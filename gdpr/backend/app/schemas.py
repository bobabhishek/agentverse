from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class SimulationRequest(BaseModel):
    message: str

class SimulationResponse(BaseModel):
    session_id: str
    message_id: str
    response: Dict[str, Any]
    events: List[Dict[str, Any]]
    hops: int

class A2ARequestPayload(BaseModel):
    intent: str
    requested_fields: List[str]
    search_parameters: Dict[str, Any] = Field(default_factory=dict)

class A2AMessage(BaseModel):
    message_id: str
    trace_id: str
    source_agent: str
    target_agent: str
    source_region: str
    target_region: str
    message_type: str
    request: A2ARequestPayload
    timestamp: str

class A2AResponse(BaseModel):
    message_id: str
    trace_id: str
    source_agent: str
    target_agent: str
    response_status: str
    requested_fields: List[str]
    returned_fields: List[str]
    data: List[Dict[str, Any]]
    policy_metadata: Optional[Dict[str, Any]] = None
    timestamp: str

class AuditEvent(BaseModel):
    event_id: str
    trace_id: str
    timestamp: str
    source_agent: str
    target_agent: Optional[str] = None
    region: str
    event_type: str
    action_description: str
    status: str
    metadata: Optional[Dict[str, Any]] = None
    policy_evaluation: Optional[Dict[str, Any]] = None
