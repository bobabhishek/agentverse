import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas import SimulationRequest, SimulationResponse
from app.agents.india_agent import IndiaAgent
from app.agents.europe_agent import EuropeAgent
from app.compliance.evaluator import PolicyEvaluator
from app.compliance.agent_evaluator import TaskAccuracyEvaluator

router = APIRouter()

# Instantiate agents
india_agent = IndiaAgent()
europe_agent = EuropeAgent()
evaluator = PolicyEvaluator()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/api/agent-accuracy")
async def get_agent_accuracy():
    return TaskAccuracyEvaluator.get_accuracy()

@router.post("/api/simulations")
async def create_simulation():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

def generate_conversational_reply(
    user_message: str, 
    requested_fields: list[str], 
    data: list[dict[str, Any]], 
    not_found: bool,
    is_refusal: bool = False
) -> str:
    p_norm = user_message.lower()

    if is_refusal:
        if "phone" in p_norm:
            return "I'm sorry, but I can't provide the customer's phone number."
        elif "address" in p_norm:
            return "I'm sorry, but I can't provide the customer's address."
        elif "gps" in p_norm or "location" in p_norm or "coord" in p_norm:
            return "I'm sorry, but I can't provide the customer's GPS location."
        else:
            return "I'm sorry, but I can't provide the requested customer information."

    if not_found or not data:
        return "I couldn't find any matching records in the European customer database."
    
    p_norm = user_message.lower()
    
    # 1. Single Customer Result
    if len(data) == 1:
        cust = data[0]
        name = cust.get("name")
        cust_id = cust.get("id", "")
        identifier = f"{name} ({cust_id})" if name and cust_id else (name or cust_id)
        
        # Check specific single field requested
        if "phone" in p_norm and not any(kw in p_norm for kw in ["all", "detail", "profile"]):
            phone = cust.get("phone", "Not available")
            return f"The phone number for customer {identifier} is **{phone}**."
            
        if "address" in p_norm and not any(kw in p_norm for kw in ["all", "detail", "profile"]):
            addr = cust.get("address", "Not available")
            city = cust.get("city", "")
            country = cust.get("country", "")
            loc_parts = []
            if city and city.lower() not in addr.lower():
                loc_parts.append(city)
            if country and country.lower() not in addr.lower():
                loc_parts.append(country)
            full_addr = f"{addr}, {', '.join(loc_parts)}" if loc_parts else addr
            return f"The address for customer {identifier} is **{full_addr}**."
            
        if "status" in p_norm and not any(kw in p_norm for kw in ["all", "detail", "profile"]):
            status = cust.get("order_status", cust.get("status", "Not available"))
            return f"The current order status for customer {identifier} is **{status}**."
            
        if "gps" in p_norm and not any(kw in p_norm for kw in ["all", "detail", "profile"]):
            gps = cust.get("gps", cust.get("gps_coordinates", "Not available"))
            return f"The GPS coordinates for customer {identifier} are **{gps}**."
            
        # Full profile details requested
        details = [f"Here are the details for **{identifier}**:"]
        status_val = cust.get("order_status") or cust.get("status")
        if status_val:
            details.append(f"• **Order Status:** {status_val}")
        if cust.get("phone"):
            details.append(f"• **Phone:** {cust['phone']}")
        if cust.get("address"):
            addr = cust['address']
            city = cust.get('city', '')
            country = cust.get('country', '')
            loc_parts = []
            if city and city.lower() not in addr.lower():
                loc_parts.append(city)
            if country and country.lower() not in addr.lower():
                loc_parts.append(country)
            if loc_parts:
                addr = f"{addr}, {', '.join(loc_parts)}"
            details.append(f"• **Address:** {addr}")
        elif cust.get("city") or cust.get("country"):
            loc = f"{cust.get('city', '')}, {cust.get('country', '')}".strip(", ")
            details.append(f"• **Location:** {loc}")
        # Only include GPS if user explicitly asked for GPS/coordinates
        if any(w in p_norm for w in ["gps", "coord", "coordinates"]) and (cust.get("gps") or cust.get("gps_coordinates")):
            details.append(f"• **GPS:** {cust.get('gps', cust.get('gps_coordinates'))}")
        return "\n".join(details)
        
    # 2. Multiple Customer Results (List / Table)
    # A. Names only requested
    if ("name" in p_norm or "names" in p_norm) and not any(kw in p_norm for kw in ["status", "phone", "address", "gps", "cancel", "ship", "deliver", "process"]):
        rows = ["| # | Customer Name | Customer ID |", "| :--- | :--- | :--- |"]
        for i, r in enumerate(data, 1):
            name = r.get("name", "Unknown")
            cid = r.get("id", "")
            rows.append(f"| {i} | {name} | {cid} |")
        return f"Here are the customer names ({len(data)} profiles):\n\n" + "\n".join(rows)

    # B. Status lists (e.g. "whos status is cancelled", "names and status", "show status")
    if "status" in p_norm or any(s in p_norm for s in ["cancel", "cancelled", "shipped", "delivered", "processing"]):
        has_location = any(r.get("city") or r.get("country") for r in data)
        if has_location:
            rows = ["| # | Customer Name | Customer ID | Location | Order Status |", "| :--- | :--- | :--- | :--- | :--- |"]
            for i, r in enumerate(data, 1):
                name = r.get("name", "Unknown")
                cid = r.get("id", "")
                loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "") or r.get("city", "") or "Europe"
                status = r.get("order_status", r.get("status", "—"))
                rows.append(f"| {i} | {name} | {cid} | {loc} | {status} |")
        else:
            rows = ["| # | Customer Name | Customer ID | Order Status |", "| :--- | :--- | :--- | :--- |"]
            for i, r in enumerate(data, 1):
                name = r.get("name", "Unknown")
                cid = r.get("id", "")
                status = r.get("order_status", r.get("status", "—"))
                rows.append(f"| {i} | {name} | {cid} | {status} |")
        return f"Here are the matching records ({len(data)} results):\n\n" + "\n".join(rows)
        
    # C. Country/City or general filtered queries
    has_status = any(r.get("order_status") or r.get("status") for r in data)
    has_phone = any(r.get("phone") for r in data) and any(w in p_norm for w in ["phone", "contact", "call"])

    if has_status and has_phone:
        rows = ["| Customer | Customer ID | Location | Order Status | Phone |", "| :--- | :--- | :--- | :--- | :--- |"]
        for r in data:
            name = r.get("name", "Unknown")
            cid = r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "")
            status = r.get("order_status", r.get("status", "—"))
            phone = r.get("phone", "—")
            rows.append(f"| {name} | {cid} | {loc} | {status} | {phone} |")
    elif has_status:
        rows = ["| Customer | Customer ID | Location | Order Status |", "| :--- | :--- | :--- | :--- |"]
        for r in data:
            name = r.get("name", "Unknown")
            cid = r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "")
            status = r.get("order_status", r.get("status", "—"))
            rows.append(f"| {name} | {cid} | {loc} | {status} |")
    else:
        rows = ["| # | Customer Name | Customer ID | Location |", "| :--- | :--- | :--- | :--- |"]
        for i, r in enumerate(data, 1):
            name = r.get("name", "Unknown")
            cid = r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "")
            rows.append(f"| {i} | {name} | {cid} | {loc} |")
    return f"Here are the matching records ({len(data)} results):\n\n" + "\n".join(rows)

@router.post("/api/simulations/{session_id}/messages", response_model=SimulationResponse)
async def send_message(session_id: str, request: SimulationRequest):
    trace_id = str(uuid.uuid4())
    all_events = []
    
    try:
        # 1. Agent 2 (India) processes the user message and creates A2A Request
        a2a_request_msg, agent2_events = await india_agent.process_user_request(request.message, trace_id)
        all_events.extend(agent2_events)

        # Check if request was handled as a conversational greeting / query
        if a2a_request_msg.request.intent == "conversation":
            reply_text = a2a_request_msg.request.search_parameters.get(
                "reply",
                "Hello! I am your Enterprise AI Assistant. How can I assist you with European customer records today?"
            )
            all_events.append({
                "event_id": str(uuid.uuid4()),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source_agent": india_agent.name,
                "region": india_agent.region,
                "event_type": "RESPONSE_RENDERED",
                "action_description": reply_text,
                "status": "success",
                "metadata": {}
            })
            return SimulationResponse(
                session_id=session_id,
                message_id=str(uuid.uuid4()),
                response={"data": [], "reply": reply_text},
                events=all_events,
                hops=1
            )
        
        # 2. Agent 1 (Europe) receives A2A Request, queries DB, creates A2A Response
        a2a_request_msg.request.search_parameters["live_mode"] = True
        a2a_response, agent1_events = await europe_agent.process_a2a_request(a2a_request_msg)
        all_events.extend(agent1_events)
        
        # 3. Policy Evaluator intercepts A2A Response
        if a2a_response.policy_metadata and a2a_response.policy_metadata.get("legacy_minimization"):
            eval_event = evaluator.evaluate_data_minimization(a2a_response)
        else:
            eval_event = evaluator.evaluate_gdpr_policy(a2a_response)
        all_events.append(eval_event)
        
        # 4. Agent 2 receives response and renders
        all_events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": india_agent.name,
            "region": india_agent.region,
            "event_type": "A2A_RESPONSE_RECEIVED",
            "action_description": "Received A2A response payload from Europe Node.",
            "status": "success"
        })
        
        # Determine group title for bulk results or query context
        search_params = a2a_request_msg.request.search_parameters
        if search_params.get("all"):
            group_val = "All European Customers (100 Profiles)"
        elif search_params.get("name"):
            group_val = f"{search_params.get('name')}"
        elif search_params.get("city"):
            group_val = f"City: {search_params.get('city')}"
        elif search_params.get("country"):
            group_val = f"Country: {search_params.get('country')}"
        elif search_params.get("order_status"):
            group_val = f"Status: {search_params.get('order_status')}"
        elif search_params.get("id"):
            group_val = f"ID: {search_params.get('id')}"
        else:
            group_val = "European Customers"

        is_not_found = a2a_response.response_status == "not_found"
        is_refusal = a2a_response.response_status == "compliant_refusal"
        conv_reply = generate_conversational_reply(request.message, a2a_response.requested_fields, a2a_response.data, is_not_found, is_refusal)

        if is_not_found:
            render_desc = "Customer not found in synthetic database."
        else:
            render_desc = conv_reply

        all_events.append({
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_agent": india_agent.name,
            "region": india_agent.region,
            "event_type": "RESPONSE_RENDERED",
            "action_description": render_desc,
            "status": "success",
            "metadata": {
                "wantsId": "id" in a2a_response.requested_fields,
                "wantsPhone": "phone" in a2a_response.requested_fields or "phone_number" in a2a_response.requested_fields,
                "wantsAddress": "address" in a2a_response.requested_fields,
                "wantsGps": "gps" in a2a_response.requested_fields,
                "wantsStatus": "order_status" in a2a_response.requested_fields,
                "customerData": {
                    "isBulk": len(a2a_response.data) > 1,
                    "records": a2a_response.data,
                    "groupValue": group_val,
                    "customer": a2a_response.data[0] if len(a2a_response.data) == 1 else None,
                    "notFound": is_not_found,
                    "reply": conv_reply,
                    "requested_fields": a2a_response.requested_fields,
                    "returned_fields": a2a_response.returned_fields,
                    "excess_fields": eval_event.get("policy_evaluation", {}).get("excess_fields", []),
                    "policy_result": eval_event.get("policy_evaluation", {}).get("result", "PASS"),
                    "violation_detected": eval_event.get("status") == "violation",
                    "action_description": eval_event.get("action_description", "")
                }
            }
        })
        
        return SimulationResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response={"data": a2a_response.data, "reply": conv_reply},
            events=all_events,
            hops=3 # India -> Europe -> India
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
