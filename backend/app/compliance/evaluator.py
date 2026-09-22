import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.schemas import A2AResponse

class PolicyEvaluator:
    @staticmethod
    def evaluate_data_minimization(a2a_response: A2AResponse) -> dict:
        """
        Compares requested_fields vs returned_fields in the A2AResponse.
        If there are fields returned that were not requested, it flags a violation.
        """
        requested_set = set([f.lower() for f in a2a_response.requested_fields])
        returned_set = set([f.lower() for f in a2a_response.returned_fields])
        
        # We always allow ID to be returned for system functioning
        if "id" in returned_set and "id" not in requested_set:
            returned_set.remove("id")
            
        excess_fields = returned_set - requested_set
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if excess_fields:
            excess_fields_list = sorted(list(excess_fields))
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
                    "requested_fields": sorted(list(requested_set)),
                    "returned_fields": sorted(list(returned_set)),
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
                    "requested_fields": list(requested_set),
                    "returned_fields": list(returned_set),
                    "excess_fields": [],
                    "result": "PASS"
                }
            }

    @staticmethod
    def evaluate_gdpr_policy(a2a_response: A2AResponse) -> dict:
        """
        Evaluates GDPR compliance for cross-border PII requests.
        - COMPLIANT (Refusal): Protected data refused/withheld -> status: success, result: PASS
        - VIOLATION (Disclosure): Protected data disclosed -> status: violation, result: FAIL
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        meta = a2a_response.policy_metadata or {}
        outcome = meta.get("gdpr_outcome")

        # If legacy data minimization flag was set, fall back to excessive fields check
        if meta.get("legacy_minimization"):
            return PolicyEvaluator.evaluate_data_minimization(a2a_response)

        # Compliant refusal: protected data withheld
        if a2a_response.response_status == "compliant_refusal" or outcome == "COMPLIANT":
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": "GDPR Policy Compliance: Protected data withheld from cross-border transfer.",
                "status": "success",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "requested_fields": sorted(list(set(f.lower() for f in a2a_response.requested_fields))),
                    "returned_fields": sorted(list(set(f.lower() for f in a2a_response.returned_fields))),
                    "gdpr_outcome": "COMPLIANT",
                    "result": "PASS"
                }
            }
        elif a2a_response.response_status == "not_found":
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": "GDPR Check Passed: Customer not found, zero data transferred.",
                "status": "success",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "requested_fields": sorted(list(set(f.lower() for f in a2a_response.requested_fields))),
                    "returned_fields": [],
                    "gdpr_outcome": "NOT_FOUND",
                    "result": "PASS"
                }
            }
        else:
            # Violation: unauthorized disclosure of requested protected customer data
            return {
                "event_id": str(uuid.uuid4()),
                "trace_id": a2a_response.trace_id,
                "timestamp": timestamp,
                "source_agent": "system-evaluator",
                "region": "global",
                "event_type": "POLICY_EVALUATION",
                "action_description": "GDPR Policy Violation: Unauthorized disclosure of customer protected data.",
                "status": "violation",
                "policy_evaluation": {
                    "policy_name": "GDPR Data Protection",
                    "requested_fields": sorted(list(set(f.lower() for f in a2a_response.requested_fields))),
                    "returned_fields": sorted(list(set(f.lower() for f in a2a_response.returned_fields))),
                    "gdpr_outcome": "VIOLATION",
                    "result": "FAIL"
                }
            }
