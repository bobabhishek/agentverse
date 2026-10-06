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

    conv_id = req.conversation_id or f"chat-{uuid.uuid4().hex[:10]}"
    conv_state = conversation_store.get_transaction_state(conv_id)

    # 1. Resolve sender: first from message, then from ongoing conversation state, then from req.person_id
    active_customer = None
    from app.services.intent_extractor import intent_extractor
    from app.services.database import db_service

    extracted_sender = intent_extractor.extract_sender(req.message)
    if not extracted_sender and conv_state and conv_state.get("stage") == "COLLECTING_SENDER":
        cand = req.message.strip()
        if intent_extractor.is_valid_person_name(cand):
            extracted_sender = cand

    if extracted_sender:
        active_customer = db_service.find_customer(extracted_sender) or db_service.find_person(extracted_sender)
        if not active_customer:
            active_customer = {
                "customer_id": f"CUST-{uuid.uuid4().hex[:6].upper()}",
                "customer_name": extracted_sender.strip().title(),
                "person_id": f"CUST-{uuid.uuid4().hex[:6].upper()}",
                "name": extracted_sender.strip().title(),
                "source_country": req.source_country or (conv_state.get("source_country") if conv_state else "India"),
                "currency": "INR" if "india" in str(req.source_country or (conv_state.get("source_country") if conv_state else "India")).lower() else "USD",
                "policy_violations": []
            }

    if not active_customer and conv_state and conv_state.get("customer_name"):
        active_customer = db_service.find_customer(conv_state["customer_name"]) or db_service.find_person(conv_state["customer_name"])

    if not active_customer and req.person_id:
        active_customer = db_service.find_customer(req.person_id) or data_loader.get_by_id(req.person_id)

    if not active_customer:
        all_cases = data_loader.get_all()
        if all_cases:
            active_customer = all_cases[0]
        else:
            raise HTTPException(status_code=404, detail="No customer records available")

    tc = dict(active_customer)
    cust_id = active_customer.get("customer_id") or active_customer.get("person_id") or active_customer.get("id")
    cust_name = active_customer.get("customer_name") or active_customer.get("name")
    tc["customer_id"] = cust_id
    tc["customer_name"] = cust_name
    tc["person_id"] = cust_id
    tc["name"] = cust_name

    # Sender account country logic
    if req.source_country:
        tc["source_country"] = req.source_country
    elif conv_state and conv_state.get("source_country"):
        tc["source_country"] = conv_state["source_country"]
    elif req.reverse_route is True:
        tc["source_country"] = "United States"
    elif req.reverse_route is False:
        tc["source_country"] = "India"
    else:
        amt, curr = intent_extractor.extract_amount_and_currency(req.message)
        if curr == "INR":
            tc["source_country"] = "India"
        elif curr == "USD":
            tc["source_country"] = "United States"
        else:
            tc["source_country"] = active_customer.get("source_country", "India")
    tc["source_currency"] = "INR" if "india" in str(tc["source_country"]).lower() else "USD"

    # Check recipient from request or existing conversation state or message text
    conv_state = conversation_store.get_transaction_state(conv_id)
    recip = req.recipient_name or req.recipient_id or (conv_state.get("recipient_name") if conv_state else None)
    if not recip:
        from app.services.intent_extractor import intent_extractor
        recip = intent_extractor.extract_recipient(req.message)
        if not recip and conv_state and conv_state.get("stage") == "COLLECTING_RECIPIENT":
            cand = req.message.strip()
            if intent_extractor.is_valid_person_name(cand):
                recip = cand

    if recip:
        matched = data_loader.find_by_recipient(recip)
        if matched:
            tc["recipient_id"] = matched.get("recipient_id") or matched.get("customer_id")
            tc["recipient_name"] = matched.get("recipient_name") or matched.get("customer_name")
            if req.destination_country:
                rc = req.destination_country
            else:
                rc = matched.get("recipient_country") or matched.get("destination_country") or matched.get("source_country") or "United States"
            tc["recipient_country"] = rc
            tc["destination_country"] = rc
            tc["destination_currency"] = "INR" if "india" in str(rc).lower() else "USD"
        else:
            tc["recipient_name"] = recip
            if req.destination_country:
                tc["destination_country"] = req.destination_country
                tc["destination_currency"] = "INR" if "india" in str(req.destination_country).lower() else "USD"
            elif "india" in str(tc["source_country"]).lower():
                tc["destination_country"] = "United States"
                tc["destination_currency"] = "USD"
            else:
                tc["destination_country"] = "India"
                tc["destination_currency"] = "INR"
    elif req.destination_country:
        tc["destination_country"] = req.destination_country
        tc["destination_currency"] = "INR" if "india" in str(req.destination_country).lower() else "USD"

    # Route direction check
    is_reverse = ("united states" in str(tc["source_country"]).lower())
    if req.reverse_route is not None:
        is_reverse = req.reverse_route

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
        events=result.get("events", []),
        account_balances=result.get("account_balances"),
        audit_trail=result.get("audit_trail"),
        bank_statement=result.get("bank_statement")
    )

