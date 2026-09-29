import uuid
import logging
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.data_loader import data_loader
from app.services.conversation_store import conversation_store
from app.agent.agent import fema_agent

logger = logging.getLogger("fema.routes.chat")
router = APIRouter()

@router.post("/api/chat", response_model=ChatResponse)
async def chat_handler(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    person_id = req.person_id or "TEST-PERSON-001"
    tc = data_loader.get_by_id(person_id)
    if not tc:
        # Fallback to first test case if available
        all_cases = data_loader.get_all()
        if all_cases:
            tc = all_cases[0]
        else:
            raise HTTPException(status_code=404, detail=f"No synthetic test case found for person_id '{person_id}'")

    conv_id = req.conversation_id or f"chat-{uuid.uuid4().hex[:10]}"

    # Detect route direction from request or prompt text
    is_reverse = False
    if req.reverse_route is not None:
        is_reverse = req.reverse_route
    else:
        lower = req.message.lower()
        if any(kw in lower for kw in ["us to india", "from my us account", "from the us", "to india"]):
            is_reverse = True
        elif any(kw in lower for kw in ["india to us", "from my india account", "from india", "to us", "to the us"]):
            is_reverse = False

    # Store user message
    conversation_store.add_message(conv_id, role="user", content=req.message)

    # Retrieve history for context
    history = conversation_store.get_messages(conv_id)
    history_tuples = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]

    # Process conversational transaction turn
    result = await fema_agent.process_conversational_turn(
        message=req.message,
        conversation_id=conv_id,
        test_case=tc,
        reverse_route=is_reverse
    )

    # Store agent response
    conversation_store.add_message(conv_id, role="assistant", content=result["message"])

    return ChatResponse(
        conversation_id=conv_id,
        message=result["message"],
        next_action=result.get("next_action"),
        transaction_state=result.get("transaction_state"),
        agent=result.get("agent", {}),
        policy=result.get("policy", {}),
        decision=result.get("decision", {}),
        transaction=result.get("transaction", {}),
        transfer=result.get("transfer", {}),
        events=result.get("events", [])
    )
