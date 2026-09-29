import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.data_loader import data_loader
from app.agent.policy import evaluate_fema_policy
from app.agent.agent import fema_agent
from app.models import SimulationRunRequest, SimulationRunResponse

logger = logging.getLogger("fema.routes.simulation")
router = APIRouter()

@router.get("/api/test-cases")
async def list_test_cases(status: str = Query("all", description="Filter by status: all, policy_failure, valid")):
    cases = data_loader.get_all(status)
    return cases

@router.get("/api/test-cases/{person_id}")
async def get_test_case(person_id: str, reverse_route: bool = Query(False)):
    tc = data_loader.get_by_id(person_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Synthetic person with ID '{person_id}' not found")
    
    policy_eval = evaluate_fema_policy(tc, is_reverse_route=reverse_route)
    return {
        "test_case": tc,
        "policy": policy_eval.model_dump()
    }

@router.post("/api/simulation/run", response_model=SimulationRunResponse)
async def run_simulation(req: SimulationRunRequest):
    tc = data_loader.get_by_id(req.person_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Synthetic person with ID '{req.person_id}' not found")

    message = req.message or f"Process this payment from {tc.get('source_country')} to {tc.get('destination_country')}"
    is_reverse = bool(req.reverse_route)

    result = await fema_agent.process_transaction_request(
        message=message,
        test_case=tc,
        is_reverse_route=is_reverse
    )

    return SimulationRunResponse(
        person_id=req.person_id,
        selected_person=tc,
        transaction=result["transaction"],
        policy=result["policy"],
        decision=result["decision"],
        agent_message=result["message"],
        transfer=result["transfer"],
        events=result["events"]
    )
