import uuid
import json
import random
import unicodedata
from datetime import datetime
from typing import Dict, Any, List

from app.config import settings
from app.schemas import A2AMessage, A2AResponse
from app.agents.agent_factory import get_agent_client
from app.compliance.classification import (
    canonicalize_field,
    is_sensitive,
    is_non_sensitive,
    get_field_classification,
    classify_fields
)

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
        Strictly enforces GDPR compliance on sensitive fields while allowing non-sensitive disclosures.
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

        # 1. Query local synthetic database
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
        
        # 2. Analyze requested fields
        raw_requested = message.request.requested_fields or []
        search_params = message.request.search_parameters or {}

        # Canonicalize requested fields
        requested_fields = [canonicalize_field(f) for f in raw_requested if f]
        if not requested_fields and search_params.get("id"):
            requested_fields = ["customer_id", "customer_name", "order_status", "product_category", "order_date", "phone_number", "home_address", "gps_coordinates"]

        if not matched_records:
            filtered_records = []
            returned_fields = []
            response_status = "not_found"
            prep_desc = "No matching records found for requested search parameters."
            transfer_desc = "Transmitting not-found response back to Agent 2."
            policy_metadata = {"gdpr_outcome": "NOT_FOUND"}
        else:
            # Check legacy minimization test mode
            is_legacy_test = (
                search_params.get("legacy_minimization")
                or search_params.get("force_test_violation")
                or (settings.TEST_DATA_MINIMIZATION_VIOLATION and not search_params.get("live_mode"))
            )
            is_phone_minimization_test = bool(requested_fields) and set(requested_fields) <= {"customer_id", "phone_number"}

            if is_legacy_test and (is_phone_minimization_test or search_params.get("force_test_violation")):
                response_status = "success"
                returned_fields = list(raw_requested)
                for f in ["phone", "address", "gps", "order_status"]:
                    if f not in returned_fields:
                        returned_fields.append(f)
                policy_metadata = {"legacy_minimization": True, "gdpr_outcome": "VIOLATION"}
                
                filtered_records = []
                for record in matched_records:
                    filtered_record = self._extract_fields(record, returned_fields)
                    filtered_records.append(filtered_record)
                prep_desc = f"Prepared {len(filtered_records)} records for transfer (legacy excessive fields mode)."
                transfer_desc = "Transmitting data back to Agent 2."

            else:
                # Classify requested fields
                sensitive_requested = [f for f in requested_fields if is_sensitive(f)]
                non_sensitive_requested = [f for f in requested_fields if is_non_sensitive(f)]

                # Determine violation vs compliant mode
                if search_params.get("force_violation"):
                    is_violation = True
                elif search_params.get("force_compliant"):
                    is_violation = False
                elif sensitive_requested:
                    # Random decision based on configured probability
                    is_violation = random.random() < settings.GDPR_VIOLATION_PROBABILITY
                else:
                    # Purely non-sensitive fields are always safely disclosed
                    is_violation = False

                if sensitive_requested and not is_violation:
                    # COMPLIANT MODE:
                    # Non-sensitive fields are returned.
                    # Sensitive fields are properly withheld.
                    response_status = "compliant_refusal" if sensitive_requested else "success"
                    
                    # Fields allowed to return: non-sensitive requested + customer_id
                    allowed_fields = list(non_sensitive_requested)
                    if "customer_id" not in allowed_fields:
                        allowed_fields.insert(0, "customer_id")
                    
                    returned_fields = allowed_fields
                    filtered_records = []
                    for record in matched_records:
                        filtered_record = self._extract_fields(record, allowed_fields)
                        filtered_records.append(filtered_record)

                    policy_metadata = {
                        "gdpr_outcome": "COMPLIANT",
                        "refusal": True,
                        "refused_fields": sensitive_requested,
                        "returned_fields": returned_fields,
                        "field_classifications": classify_fields(requested_fields)
                    }
                    prep_desc = f"GDPR Compliance: Withholding sensitive fields ({', '.join(sensitive_requested)}) from cross-border transfer."
                    transfer_desc = "Transmitting compliant response back to Agent 2."

                else:
                    # VIOLATION MODE (or Normal Non-Sensitive Request):
                    # In violation mode on sensitive data, the requested sensitive data is disclosed
                    # In non-sensitive mode, normal safe attributes are returned.
                    response_status = "success"
                    
                    # NO UNRELATED LEAKAGE: return ONLY requested fields + customer_id
                    allowed_fields = list(requested_fields)
                    if "customer_id" not in allowed_fields:
                        allowed_fields.insert(0, "customer_id")
                    
                    returned_fields = list(allowed_fields)
                    for rf in raw_requested:
                        if rf and rf not in returned_fields:
                            returned_fields.append(rf)

                    filtered_records = []
                    for record in matched_records:
                        filtered_record = self._extract_fields(record, allowed_fields)
                        filtered_records.append(filtered_record)

                    outcome_label = "VIOLATION" if (is_violation and sensitive_requested) else "NORMAL_COMPLIANT"
                    policy_metadata = {
                        "gdpr_outcome": outcome_label,
                        "refusal": False,
                        "disclosed_fields": sensitive_requested if is_violation else [],
                        "field_classifications": classify_fields(requested_fields)
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
            requested_fields=raw_requested,
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

    def _extract_fields(self, record: dict, fields: List[str]) -> dict:
        """Extract only requested fields, ensuring canonical and alias key consistency."""
        extracted = {}
        for f in fields:
            canon = canonicalize_field(f)
            # Find matching value in record
            val = record.get(canon)
            if val is None:
                # Check aliases
                alias_candidates = {
                    "customer_id": ["id", "customer_id"],
                    "customer_name": ["name", "customer_name"],
                    "order_status": ["status", "order_status"],
                    "product_category": ["product", "product_category", "category"],
                    "order_date": ["date", "order_date"],
                    "phone_number": ["phone", "phone_number"],
                    "home_address": ["address", "home_address"],
                    "gps_coordinates": ["gps", "gps_coordinates"]
                }.get(canon, [canon])
                for candidate in alias_candidates:
                    if candidate in record:
                        val = record[candidate]
                        break

            if val is not None:
                extracted[canon] = val
                # Also include short key if standard
                short_key_map = {
                    "customer_id": "id",
                    "customer_name": "name",
                    "phone_number": "phone",
                    "home_address": "address",
                    "gps_coordinates": "gps",
                    "product_category": "product_category",
                    "order_date": "order_date",
                    "order_status": "order_status"
                }
                short_key = short_key_map.get(canon)
                if short_key and short_key not in extracted:
                    extracted[short_key] = val

        # Always maintain customer_id / id
        if "customer_id" not in extracted and ("customer_id" in record or "id" in record):
            cid = record.get("customer_id") or record.get("id")
            extracted["customer_id"] = cid
            extracted["id"] = cid

        return extracted
        
    def _query_db(self, search_params: dict) -> List[Dict]:
        results = self.database
        if not search_params:
            return []
            
        if search_params.get("all") or search_params.get("all_records"):
            return list(self.database)

        for key, value in search_params.items():
            if key in ("all", "all_records", "reply", "force_test_violation", "force_violation", "force_compliant", "live_mode"):
                continue
            val_norm = _norm(value)
            if not val_norm:
                continue

            canon_key = canonicalize_field(key)

            if canon_key == "customer_id":
                val_clean = str(value).strip().lower()
                results = [
                    r for r in results 
                    if str(r.get("customer_id", r.get("id", ""))).strip().lower() == val_clean
                    or (val_clean and str(r.get("customer_id", r.get("id", ""))).strip().lower().endswith(val_clean.replace("syn-cust-", "")))
                ]
            elif canon_key == "customer_name":
                results = [
                    r for r in results 
                    if val_norm in _norm(r.get("customer_name", r.get("name", ""))) 
                    or _norm(r.get("customer_name", r.get("name", ""))) in val_norm
                ]
            elif canon_key == "order_status":
                results = [r for r in results if val_norm in _norm(r.get("order_status", ""))]
            elif canon_key == "product_category":
                results = [r for r in results if val_norm in _norm(r.get("product_category", ""))]
            elif canon_key == "order_date":
                results = [r for r in results if val_norm in _norm(r.get("order_date", ""))]
            elif key == "country":
                results = [r for r in results if val_norm == _norm(r.get("country", "")) or val_norm in _norm(r.get("country", ""))]
            elif key == "city":
                results = [r for r in results if val_norm in _norm(r.get("city", ""))]
            elif canon_key == "phone_number":
                results = [r for r in results if str(value).strip() in str(r.get("phone_number", r.get("phone", ""))).strip()]
        
        return results
