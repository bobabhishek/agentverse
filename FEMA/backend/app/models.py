from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class PolicyCheckResult(BaseModel):
    name: str
    check: str
    status: Literal["PASS", "FAILED", "NOT_VERIFIED", "REQUIRES_REVIEW"]
    reason: str

class PolicyEvaluation(BaseModel):
    status: Literal["VIOLATION", "COMPLIANT"]
    failure_count: int
    checks: List[PolicyCheckResult]
    identified_type: str
    source_to_dest: str

class FemaTestCaseModel(BaseModel):
    person_id: str
    name: str
    email: str
    source_country: str
    sender_residency: str
    sender_account_type: str
    destination_country: str
    recipient_type: str
    recipient_name: str
    transaction_id: str
    amount: float
    currency: str
    purpose: str
    authorization: bool
    supporting_documentation: bool
    eligibility: Literal["VERIFIED", "NOT_VERIFIED"]
    policy_violations: List[str]
    expected_agent_behavior: Literal["PROCEED_ROGUE_TEST", "PROCEED"]
    expected_glassbox_event: Literal["POLICY_VIOLATION", "NO_POLICY_VIOLATION"]
    environment: str = "SIMULATION_ONLY"

class AgentDecision(BaseModel):
    decision: str
    type: str
    policy_status: str
    violations: List[str]
    action: str
    tool_called: bool
    summary: str

class WireMockTransferResponse(BaseModel):
    success: bool
    gateway: str = "WireMock"
    environment: str = "SIMULATION"
    status: str
    payment_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

class ActivityEvent(BaseModel):
    event_type: str
    timestamp: str
    transaction_id: str
    person_id: str
    details: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    person_id: Optional[str] = "TEST-PERSON-001"
    conversation_id: Optional[str] = None
    reverse_route: Optional[bool] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    next_action: Optional[str] = None
    transaction_state: Optional[Dict[str, Any]] = None
    agent: Dict[str, Any] = Field(default_factory=dict)
    policy: Dict[str, Any] = Field(default_factory=dict)
    decision: Dict[str, Any] = Field(default_factory=dict)
    transaction: Dict[str, Any] = Field(default_factory=dict)
    transfer: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

class SimulationRunRequest(BaseModel):
    person_id: str
    message: Optional[str] = "Transfer the requested amount"
    reverse_route: Optional[bool] = None

class SimulationRunResponse(BaseModel):
    person_id: str
    selected_person: Dict[str, Any]
    transaction: Dict[str, Any]
    policy: Dict[str, Any]
    decision: Dict[str, Any]
    agent_message: str
    transfer: Dict[str, Any]
    events: List[Dict[str, Any]]
