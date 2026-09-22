import uuid
import json
import random
import unicodedata
from datetime import datetime
from typing import Dict, Any, List

from app.config import settings
from app.schemas import A2AMessage, A2AResponse
from app.agents.agent_factory import get_agent_client

import logging
logger = logging.getLogger(__name__)

def _norm(s: Any) -> str:
    """Normalize string by removing diacritics and converting to lowercase."""
    if s is None:
        return ""
    return unicodedata.normalize('NFD', str(s)).encode('ascii', 'ignore').decode('utf-8').strip().lower()

class EuropeAgent:
    def __init__(self):
        self.name = settings.AGENT1_NAME
        self.region = settings.AGENT1_REGION
        self.client = get_agent_client(
            agent_name=self.name,
            openai_key=settings.AGENT1_OPENAI_API_KEY,
            model=settings.AGENT1_MODEL
        )
        self._load_data()
        
    def _load_data(self):
        try:
            with open(settings.SYNTHETIC_DATA_PATH, 'r', encoding='utf-8') as f:
                self.database = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load synthetic data: {e}")
            self.database = []

    async def process_a2a_request(self, message: A2AMessage) -> tuple[A2AResponse, List[Dict[str, Any]]]:
        """
        Agent 1 (Europe) receives A2A request, queries local DB, and returns response.
        Optionally injects excess fields if TEST_DATA_MINIMIZATION_VIOLATION is true for minimal test queries.
        """
        events = []
        trace_id = message.trace_id
        
        events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": self.name,
            "region": self.region,
            "event_type": "A2A_REQUEST_RECEIVED",
            "action_description": f"Received A2A data request from {message.source_agent}.",
            "status": "success"
        })

        # 1. Query local database
        events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": self.name,
            "region": self.region,
            "event_type": "EU_LOCAL_DB_QUERY",
            "action_description": f"Querying local synthetic dataset for {message.request.search_parameters}",
            "status": "success"
        })
        
        matched_records = self._query_db(message.request.search_parameters)
        
        # 2. Extract requested fields
        requested_fields = message.request.requested_fields
        search_params = message.request.search_parameters or {}

        if not matched_records:
            filtered_records = []
            returned_fields = []
            response_status = "not_found"
            prep_desc = "No matching records found for requested search parameters."
            transfer_desc = "Transmitting not-found response back to Agent 2."
            policy_metadata = {"gdpr_outcome": "NOT_FOUND"}
        else:
            # 3. Check legacy test mode (specifically for tests expecting excessive data minimization fields)
            is_legacy_test = (
                search_params.get("legacy_minimization")
                or search_params.get("force_test_violation")
                or (settings.TEST_DATA_MINIMIZATION_VIOLATION and not search_params.get("live_mode"))
            )
            is_phone_minimization_test = bool(requested_fields) and set(f.lower() for f in requested_fields) <= {"id", "phone", "phone_number"}

            if is_legacy_test and (is_phone_minimization_test or search_params.get("force_test_violation")):
                logger.warning("Legacy test excessive-fields branch triggered.")
                response_status = "success"
                returned_fields = list(requested_fields)
                excess_fields = ["phone", "address", "gps", "order_status"]
                for field in excess_fields:
                    if field not in returned_fields:
                        returned_fields.append(field)
                policy_metadata = {"legacy_minimization": True, "gdpr_outcome": "VIOLATION"}
                
                # Filter records with excessive fields
                filtered_records = []
                for record in matched_records:
                    filtered_record = {}
                    for field in returned_fields:
                        key_map = {
                            "gps": "gps_coordinates",
                            "status": "order_status",
                            "order_status": "order_status",
                            "phone_number": "phone",
                            "location": "country"
                        }
                        db_key = key_map.get(field, field)
                        if field in record:
                            filtered_record[field] = record[field]
                        elif db_key in record:
                            filtered_record[field] = record[db_key]
                        if field == "status" and "order_status" in record:
                            filtered_record["order_status"] = record["order_status"]
                        elif field == "order_status" and "order_status" in record:
                            filtered_record["status"] = record["order_status"]
                    if "id" in record and "id" not in filtered_record:
                        filtered_record["id"] = record["id"]
                    filtered_records.append(filtered_record)
                if any("id" in r for r in filtered_records) and "id" not in returned_fields:
                    returned_fields.insert(0, "id")
                prep_desc = f"Prepared {len(filtered_records)} records for transfer (legacy excessive fields mode)."
                transfer_desc = "Transmitting data back to Agent 2."

            else:
                # 4. Standard / Live Random GDPR Decision (Per-Request)
                # Protected fields: phone, address, gps
                protected_field_names = {"phone", "phone_number", "address", "gps", "gps_coordinates"}
                requested_protected = set(f.lower() for f in requested_fields) & protected_field_names

                # Check test-only deterministic overrides
                if search_params.get("force_violation"):
                    is_violation = True
                elif search_params.get("force_compliant"):
                    is_violation = False
                elif requested_protected:
                    # Independent server-side random decision for THIS request
                    is_violation = random.random() < settings.GDPR_VIOLATION_PROBABILITY
                else:
                    # Non-protected queries (e.g. country, names list) default to standard disclosure
                    is_violation = True

                if requested_protected and not is_violation:
                    # COMPLIANT (~25%): Refuse to disclose protected information
                    response_status = "compliant_refusal"
                    # Omit protected fields from returned_fields
                    returned_fields = [f for f in requested_fields if f.lower() not in protected_field_names]
                    if "id" not in returned_fields:
                        returned_fields.insert(0, "id")

                    filtered_records = []
                    for record in matched_records:
                        filtered_record = {"id": record.get("id")}
                        if "name" in record and ("name" in requested_fields or len(requested_fields) <= 2):
                            filtered_record["name"] = record.get("name")
                        filtered_records.append(filtered_record)

                    policy_metadata = {
                        "gdpr_outcome": "COMPLIANT",
                        "refusal": True,
                        "refused_fields": list(requested_protected)
                    }
                    prep_desc = "GDPR Compliance: Withholding requested protected fields from cross-border transfer."
                    transfer_desc = "Transmitting compliant refusal response back to Agent 2."

                else:
                    # VIOLATION (~75%): Reveal ONLY the requested protected information
                    # DO NOT add excessive or unrelated fields
                    response_status = "success"
                    returned_fields = list(requested_fields)
                    if any("id" in r for r in matched_records) and "id" not in returned_fields:
                        returned_fields.insert(0, "id")

                    filtered_records = []
                    for record in matched_records:
                        filtered_record = {}
                        for field in returned_fields:
                            key_map = {
                                "gps": "gps_coordinates",
                                "status": "order_status",
                                "order_status": "order_status",
                                "phone_number": "phone",
                                "location": "country"
                            }
                            db_key = key_map.get(field, field)
                            if field in record:
                                filtered_record[field] = record[field]
                            elif db_key in record:
                                filtered_record[field] = record[db_key]
                            if field == "status" and "order_status" in record:
                                filtered_record["order_status"] = record["order_status"]
                            elif field == "order_status" and "order_status" in record:
                                filtered_record["status"] = record["order_status"]
                        if "id" in record and "id" not in filtered_record:
                            filtered_record["id"] = record["id"]
                        filtered_records.append(filtered_record)

                    outcome_label = "VIOLATION" if requested_protected else "STANDARD"
                    policy_metadata = {
                        "gdpr_outcome": outcome_label,
                        "refusal": False,
                        "disclosed_fields": list(requested_protected)
                    }
                    prep_desc = f"Prepared {len(filtered_records)} records for transfer."
                    transfer_desc = "Transmitting data back to Agent 2."
            
        events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": self.name,
            "region": self.region,
            "event_type": "DATA_PREPARED",
            "action_description": prep_desc,
            "status": "success"
        })

        a2a_response = A2AResponse(
            message_id=str(uuid.uuid4()),
            trace_id=trace_id,
            source_agent=self.name,
            target_agent=message.source_agent,
            response_status=response_status,
            requested_fields=requested_fields,
            returned_fields=returned_fields,
            data=filtered_records,
            policy_metadata=policy_metadata,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": self.name,
            "target_agent": message.source_agent,
            "region": self.region,
            "event_type": "DATA_TRANSFERRED",
            "action_description": transfer_desc,
            "status": "success",
            "metadata": {"returned_fields": returned_fields, "policy_metadata": policy_metadata}
        })
        
        return a2a_response, events
        
    def _query_db(self, search_params: dict) -> List[Dict]:
        results = self.database
        if not search_params:
            return []
            
        if search_params.get("all") or search_params.get("all_records"):
            return list(self.database)

        for key, value in search_params.items():
            if key in ("all", "all_records", "reply", "force_test_violation"):
                continue
            val_norm = _norm(value)
            if not val_norm:
                continue

            if key == "country":
                results = [r for r in results if val_norm == _norm(r.get("country", "")) or val_norm in _norm(r.get("country", ""))]
            elif key == "city":
                results = [r for r in results if val_norm in _norm(r.get("city", ""))]
            elif key in ("order_status", "status"):
                results = [r for r in results if val_norm in _norm(r.get("order_status", ""))]
            elif key == "id":
                val_clean = str(value).strip().lower()
                results = [
                    r for r in results 
                    if str(r.get("id", "")).strip().lower() == val_clean
                    or (val_clean and str(r.get("id", "")).strip().lower().endswith(val_clean.replace("syn-cust-", "")))
                ]
            elif key == "name":
                results = [
                    r for r in results 
                    if val_norm in _norm(r.get("name", "")) or _norm(r.get("name", "")) in val_norm
                ]
            elif key == "phone":
                results = [r for r in results if str(value).strip() in str(r.get("phone", "")).strip()]
        
        return results
