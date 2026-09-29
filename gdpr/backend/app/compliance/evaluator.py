import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.schemas import A2AResponse
from app.compliance.classification import (
    canonicalize_field,
    get_field_classification,
    is_sensitive,
    is_non_sensitive,
    classify_fields
)

class PolicyEvaluator:
    @staticmethod
    def evaluate_data_minimization(a2a_response: A2AResponse) -> dict:
        """
        Legacy Data Minimization check: Compares requested_fields vs returned_fields.
        """
        alias_norm = {
            "phone_number": "phone",
            "home_address": "address",
            "gps_coordinates": "gps",
            "customer_id": "id",
            "customer_name": "name"
        }
        req_norm = set([alias_norm.get(f, f) for f in a2a_response.requested_fields if f])
        
        excess_fields = []
        for f in a2a_response.returned_fields:
            if not f:
                continue
            norm_f = alias_norm.get(f, f)
            if norm_f in ("id", "customer_id"):
                continue
            if norm_f not in req_norm:
                excess_fields.append(f)
            
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if excess_fields:
            excess_fields_list = sorted(list(set(excess_fields)))
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": f"Data Minimization Violation Detected. Excessive fields returned: {', '.join(excess_fields_list)}.",
                "status": "violation",
                "policy_evaluation": {
                    "policy_name": "Data Minimization",
                    "requested_fields": sorted(list(a2a_response.requested_fields)),
                    "returned_fields": sorted(list(a2a_response.returned_fields)),
                    "excess_fields": excess_fields_list,
                    "result": "FAIL"
                }
            }
        else:
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": "Data Minimization Check Passed. Returned fields match requested fields.",
                "status": "success",
                "policy_evaluation": {
                    "policy_name": "Data Minimization",
                    "requested_fields": sorted(list(a2a_response.requested_fields)),
                    "returned_fields": sorted(list(a2a_response.returned_fields)),
                    "excess_fields": [],
                    "result": "PASS"
                }
            }

    @staticmethod
    def evaluate_gdpr_policy(a2a_response: A2AResponse) -> dict:
        """
        Evaluates GDPR compliance for cross-border customer data requests.
        Strictly distinguishes between:
        1. NON_SENSITIVE_DATA_DISCLOSURE -> NORMAL / COMPLIANT (PASS)
        2. SENSITIVE_DATA_PROTECTION -> COMPLIANT (PASS)
        3. SENSITIVE_DATA_DISCLOSURE -> GDPR POLICY VIOLATION (FAIL)
        4. NOT_FOUND -> PASS
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        meta = a2a_response.policy_metadata or {}

        # If legacy data minimization test was explicitly requested
        if meta.get("legacy_minimization"):
            return PolicyEvaluator.evaluate_data_minimization(a2a_response)

        # 1. Customer Not Found
        if a2a_response.response_status == "not_found" or not a2a_response.data:
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": "GDPR Check Passed: Customer not found, zero customer data disclosed.",
                "status": "success",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "requested_fields": sorted(list(set(canonicalize_field(f) for f in a2a_response.requested_fields))),
                    "returned_fields": [],
                    "gdpr_outcome": "NOT_FOUND",
                    "compliance_status": "NOT_FOUND",
                    "result": "PASS"
                }
            }

        # Canonicalize requested and returned fields
        req_canonical = sorted(list(set(canonicalize_field(f) for f in a2a_response.requested_fields if f)))
        ret_canonical = sorted(list(set(canonicalize_field(f) for f in a2a_response.returned_fields if f)))
        
        # Check customer ID
        cust_id = None
        if a2a_response.data and len(a2a_response.data) > 0:
            first_record = a2a_response.data[0]
            cust_id = first_record.get("customer_id") or first_record.get("id") or meta.get("customer_id")

        # Classify fields
        field_class_map = classify_fields(req_canonical + ret_canonical)

        sensitive_requested = [f for f in req_canonical if is_sensitive(f)]
        non_sensitive_requested = [f for f in req_canonical if is_non_sensitive(f)]

        # Check if any sensitive data was ACTUALLY returned in data records
        sensitive_disclosed_in_data = []
        for record in a2a_response.data:
            for field in ("phone_number", "phone", "home_address", "address", "gps_coordinates", "gps"):
                val = record.get(field)
                if val and str(val).strip():
                    canon = canonicalize_field(field)
                    if canon not in sensitive_disclosed_in_data:
                        sensitive_disclosed_in_data.append(canon)

        # Sensitive returned fields also includes ret_canonical matches
        sensitive_returned = sorted(list(set([f for f in ret_canonical if is_sensitive(f)] + sensitive_disclosed_in_data)))

        # Evaluate Policy Outcome:
        # Case A: Sensitive data was disclosed -> VIOLATION
        if sensitive_returned:
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": f"GDPR Policy Violation: Sensitive data disclosure detected for protected attribute(s): {', '.join(sensitive_returned)}.",
                "status": "violation",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "customer_id": cust_id,
                    "requested_fields": req_canonical,
                    "field_classification": field_class_map,
                    "returned_fields": ret_canonical,
                    "sensitive_requested": sensitive_requested,
                    "disclosed_sensitive_fields": sensitive_returned,
                    "gdpr_outcome": "VIOLATION",
                    "compliance_status": "GDPR_POLICY_VIOLATION",
                    "violation_status": "SENSITIVE DATA DISCLOSURE",
                    "result": "FAIL"
                }
            }

        # Case B: Sensitive data was requested, but successfully protected/withheld -> COMPLIANT
        if sensitive_requested:
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": f"GDPR Data Protection Passed: Protected attributes ({', '.join(sensitive_requested)}) properly withheld from cross-border transfer.",
                "status": "success",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "customer_id": cust_id,
                    "requested_fields": req_canonical,
                    "field_classification": field_class_map,
                    "returned_fields": ret_canonical,
                    "sensitive_requested": sensitive_requested,
                    "protected_sensitive_fields": sensitive_requested,
                    "gdpr_outcome": "COMPLIANT",
                    "compliance_status": "SENSITIVE_DATA_PROTECTION",
                    "result": "PASS"
                }
            }

        # Case C: Only non-sensitive data requested and returned -> NORMAL / COMPLIANT
        return {
            "event_id": str(uuid.uuid4()),
            "trace_id": a2a_response.trace_id,
            "timestamp": timestamp,
            "source_agent": "system-evaluator",
            "region": "global",
            "event_type": "POLICY_EVALUATION",
            "action_description": "Normal Non-Sensitive Data Disclosure: Attributes verified safe for cross-border processing.",
            "status": "success",
            "policy_evaluation": {
                "policy_name": "GDPR Data Protection",
                "customer_id": cust_id,
                "requested_fields": req_canonical,
                "field_classification": field_class_map,
                "returned_fields": ret_canonical,
                "gdpr_outcome": "NORMAL_COMPLIANT",
                "compliance_status": "NON_SENSITIVE_DATA_DISCLOSURE",
                "result": "PASS"
            }
        }
