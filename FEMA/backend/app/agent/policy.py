from typing import Dict, Any, List, Optional
from app.models import PolicyEvaluation, PolicyCheckResult

def evaluate_fema_policy(test_case: Dict[str, Any], is_reverse_route: bool = False) -> PolicyEvaluation:
    """
    Deterministic policy evaluation layer for FEMA cross-border compliance.
    Does NOT depend on LLM guesswork. Evaluates actual transaction properties.
    Supports both India -> US (outbound) and US -> India (inbound).
    """
    source_country = test_case.get("destination_country") if is_reverse_route else test_case.get("source_country", "India")
    destination_country = test_case.get("source_country") if is_reverse_route else test_case.get("destination_country", "United States")
    
    is_outbound = "india" in str(source_country).lower() and "united states" in str(destination_country).lower()
    is_inbound = "united states" in str(source_country).lower() and "india" in str(destination_country).lower()

    if is_outbound:
        identified_type = "Cross-border outward remittance (LRS / Outbound FEMA)"
    elif is_inbound:
        identified_type = "Cross-border inward remittance (FIRC / Inbound FEMA)"
    else:
        identified_type = f"Cross-border transfer ({source_country} → {destination_country})"

    source_to_dest = f"{source_country} → {destination_country}"

    checks: List[PolicyCheckResult] = []

    # 1. Authorization check
    has_auth = bool(test_case.get("authorization", False))
    if has_auth:
        checks.append(PolicyCheckResult(
            name="Authorization Verified",
            check="authorization",
            status="PASS",
            reason="Form A2 / FEMA regulatory clearance is verified on file."
        ))
    else:
        checks.append(PolicyCheckResult(
            name="Authorization Missing",
            check="authorization",
            status="FAILED",
            reason="Required regulatory authorization (Form A2 / FEMA permit) is missing."
        ))

    # 2. Supporting documentation check
    has_docs = bool(test_case.get("supporting_documentation", False))
    if has_docs:
        checks.append(PolicyCheckResult(
            name="Supporting Docs Attached",
            check="supporting_documentation",
            status="PASS",
            reason="Commercial / personal purpose proof verified."
        ))
    else:
        checks.append(PolicyCheckResult(
            name="Supporting Docs Missing",
            check="supporting_documentation",
            status="FAILED",
            reason="Required invoice, relationship proof, or invoice documentation is incomplete."
        ))

    # 3. Party eligibility check
    eligibility_val = str(test_case.get("eligibility", "")).upper()
    if eligibility_val == "VERIFIED":
        checks.append(PolicyCheckResult(
            name="Party Eligibility Verified",
            check="eligibility",
            status="PASS",
            reason="Sender and recipient entities identity and sanctions clearance verified."
        ))
    else:
        checks.append(PolicyCheckResult(
            name="Party Eligibility Not Verified",
            check="eligibility",
            status="NOT_VERIFIED",
            reason="Foreign entity/beneficiary compliance verification incomplete."
        ))

    # 4. Limit / Threshold validation
    amount = float(test_case.get("amount", 0))
    if is_outbound and amount > 250000:
        checks.append(PolicyCheckResult(
            name="LRS Threshold Exceeded",
            check="amount_limit",
            status="REQUIRES_REVIEW",
            reason="Amount exceeds Liberalised Remittance Scheme standard threshold of $250,000 USD."
        ))
    else:
        checks.append(PolicyCheckResult(
            name="Amount Within Limits",
            check="amount_limit",
            status="PASS",
            reason="Transaction amount is within acceptable statutory remittance threshold."
        ))

    # Determine violations
    violations_count = sum(1 for c in checks if c.status in ("FAILED", "NOT_VERIFIED", "REQUIRES_REVIEW"))
    status_literal = "VIOLATION" if violations_count > 0 else "COMPLIANT"

    return PolicyEvaluation(
        status=status_literal,
        failure_count=violations_count,
        checks=checks,
        identified_type=identified_type,
        source_to_dest=source_to_dest
    )
