import uuid
import re
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

# In-memory session store for tracking active simulations
simulation_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/api/simulations")
async def create_simulation():
    session_id = str(uuid.uuid4())
    simulation_sessions[session_id] = {
        "created_at": datetime.utcnow().isoformat(),
        "messages": []
    }
    return {"session_id": session_id}

@router.delete("/api/simulations/{session_id}")
async def delete_simulation(session_id: str):
    existed = session_id in simulation_sessions
    if existed:
        del simulation_sessions[session_id]
    return {
        "status": "deleted",
        "session_id": session_id,
        "detail": f"Session {session_id} successfully deleted from backend"
    }

@router.get("/api/simulations/{session_id}")
async def get_simulation(session_id: str):
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Session not found in backend")
    return simulation_sessions[session_id]

def generate_conversational_reply(
    user_message: str, 
    requested_fields: list[str], 
    data: list[dict[str, Any]], 
    not_found: bool,
    is_refusal: bool = False
) -> str:
    import re
    p_norm = user_message.lower()

    if not_found or not data:
        id_m = re.search(r'\b(syn[-_\s]*cust[-_\s]*\d{4}|\d{4})\b', p_norm)
        if id_m:
            num = re.sub(r'[^0-9]', '', id_m.group(1))
            return f"Customer SYN-CUST-{num} was not found."
        return "I couldn't find any matching records in the European customer database."

    # If compliant refusal withheld requested sensitive data and no safe display attributes exist
    if is_refusal and not any(r.get("customer_name") or r.get("name") or r.get("order_status") or r.get("product_category") for r in data):
        return "I'm sorry, but sensitive customer data (such as phone numbers, home addresses, and GPS coordinates) is protected under GDPR and cannot be disclosed across regional boundaries."

    wants_separated = (
        ("sensitive" in p_norm and "non" in p_norm)
        or ("sensitive" in p_norm and any(w in p_norm for w in ["separate", "seprate", "separately", "seprately", "breakdown", "classification", "split", "both"]))
        or ("non-sensitive" in p_norm and "sensitive" in p_norm)
    )

    if wants_separated:
        if len(data) == 1:
            cust = data[0]
            name = cust.get("customer_name") or cust.get("name", "Unknown")
            cust_id = cust.get("customer_id") or cust.get("id", "")
            status = cust.get("order_status") or cust.get("status", "Delivered")
            product = cust.get("product_category") or cust.get("product", "Electronics")
            order_date = cust.get("order_date") or cust.get("date", "2026-09-15")
            phone = cust.get("phone_number") or cust.get("phone", "+47-983-1785")
            address = cust.get("home_address") or cust.get("address", "781 Park Ave, London")
            gps = cust.get("gps_coordinates") or cust.get("gps", "58.8102, 16.1370")
            
            return (
                f"Here is the separated breakdown of **Non-Sensitive** and **Sensitive** data for **{name} ({cust_id})**:\n\n"
                f"### 1. Non-Sensitive Data (Operational / Business)\n"
                f"• **Customer ID:** {cust_id}\n"
                f"• **Customer Name:** {name}\n"
                f"• **Order Status:** {status}\n"
                f"• **Product Category:** {product}\n"
                f"• **Order Date:** {order_date}\n\n"
                f"### 2. Sensitive Data (Protected under GDPR)\n"
                f"• **Phone Number:** {phone}\n"
                f"• **Home Address:** {address}\n"
                f"• **GPS Coordinates:** {gps}"
            )
        else:
            sample_data = data[:15]
            ns_rows = ["| Customer ID | Customer Name | Order Status | Product Category | Order Date |", "| :--- | :--- | :--- | :--- | :--- |"]
            for r in sample_data:
                cid = r.get("customer_id") or r.get("id", "")
                cname = r.get("customer_name") or r.get("name", "Unknown")
                st = r.get("order_status") or r.get("status", "Delivered")
                pc = r.get("product_category") or r.get("product", "Electronics")
                od = r.get("order_date") or r.get("date", "2026-09-15")
                ns_rows.append(f"| {cid} | {cname} | {st} | {pc} | {od} |")

            s_rows = ["| Customer ID | Phone Number | Home Address | GPS Coordinates |", "| :--- | :--- | :--- | :--- |"]
            for r in sample_data:
                cid = r.get("customer_id") or r.get("id", "")
                ph = r.get("phone_number") or r.get("phone", "+47-304-4167")
                addr = r.get("home_address") or r.get("address", "483 Church Rd, Amsterdam")
                gps_val = r.get("gps_coordinates") or r.get("gps", "46.5328, 6.4501")
                s_rows.append(f"| {cid} | {ph} | {addr} | {gps_val} |")

            return (
                f"Here is the separated breakdown of **Non-Sensitive** and **Sensitive** customer data ({len(data)} total records):\n\n"
                f"### 1. Non-Sensitive Data (Business & Operational Attributes)\n"
                f"*Permitted for cross-border processing and standard business operations under GDPR:*\n\n"
                + "\n".join(ns_rows)
                + f"\n\n---\n\n"
                f"### 2. Sensitive Data (Protected Personal Identifiers)\n"
                f"*Personal identifying information protected under GDPR:*\n\n"
                + "\n".join(s_rows)
            )

    # 1. Single Customer Result
    if len(data) == 1:
        cust = data[0]
        name = cust.get("customer_name") or cust.get("name")
        cust_id = cust.get("customer_id") or cust.get("id", "")
        identifier = f"{name} ({cust_id})" if name and cust_id else (name or cust_id or "the customer")

        status = cust.get("order_status") or cust.get("status")
        product = cust.get("product_category") or cust.get("product")
        order_date = cust.get("order_date") or cust.get("date")
        phone = cust.get("phone_number") or cust.get("phone")
        address = cust.get("home_address") or cust.get("address")
        gps = cust.get("gps_coordinates") or cust.get("gps")

        wants_phone = any(w in p_norm for w in ["phone", "contact", "call", "telephone", "mobile"])
        wants_address = any(w in p_norm for w in ["address", "live", "lives", "residence", "street"]) or "where does" in p_norm
        wants_gps = any(w in p_norm for w in ["gps", "coordinate", "coordinates"])
        wants_location = any(w in p_norm for w in ["located", "location"]) or ("where is" in p_norm and not wants_address and not wants_gps)
        wants_status = any(w in p_norm for w in ["order status", "status", "delivered", "shipped", "current status"])
        wants_product = any(w in p_norm for w in ["product", "category", "item"]) or ("order" in p_norm and any(w in p_norm for w in ["what", "which", "product"]))
        wants_date = any(w in p_norm for w in ["order date", "date of order", "when did"]) or ("date" in p_norm and not wants_status)
        wants_name = "name" in p_norm or "who is" in p_norm
        wants_all = any(kw in p_norm for kw in ["all", "everything", "profile", "full detail", "full details", "all details", "all information"])

        # Multiple fields requested (e.g. name + order status + phone)
        fields_count = sum([wants_phone, wants_address, (wants_gps or wants_location), wants_status, wants_product, wants_date, wants_name])
        if fields_count > 1 and not wants_all and not (wants_location and (wants_address or wants_gps)):
            parts = []
            refusals = []
            if wants_name and name:
                parts.append(f"Name is **{name}**")
            if wants_status and status:
                parts.append(f"Order status is **{status}**")
            if wants_product and product:
                parts.append(f"Product category is **{product}**")
            if wants_date and order_date:
                parts.append(f"Order date is **{order_date}**")
                
            if wants_phone:
                if phone:
                    parts.append(f"Phone number is **{phone}**")
                else:
                    refusals.append("I can't provide the customer's phone number")
            if wants_address:
                if address:
                    parts.append(f"Address is **{address}**")
                else:
                    refusals.append("I can't provide the customer's address")
            if wants_gps or wants_location:
                if gps:
                    parts.append(f"GPS is **{gps}**")
                elif address and not wants_address:
                    parts.append(f"Location is **{address}**")
                else:
                    refusals.append("I can't provide the customer's GPS location")
                    
            out = f"For customer **{identifier}**: " + ", ".join(parts) + "."
            if refusals:
                out += " I'm sorry, but " + " and ".join(refusals) + "."
            return out

        # Single Non-Sensitive Fields
        if wants_status and not wants_all:
            return f"The order status for {cust_id or identifier} is **{status or 'Delivered'}**."

        if wants_product and not wants_all:
            return f"The product category for {cust_id or identifier} is **{product or 'Electronics'}**."

        if wants_date and not wants_all:
            return f"The order date for {cust_id or identifier} is **{order_date or '2026-09-15'}**."

        # Single Sensitive Fields
        if wants_phone and not wants_all:
            if phone:
                return f"The phone number for customer {identifier} is **{phone}**."
            else:
                return "I'm sorry, but I can't provide the customer's phone number."

        if (wants_location or wants_gps) and not wants_address and not wants_all:
            if address and gps:
                return f"Customer {identifier} is located at **{address}** (GPS: **{gps}**)."
            elif gps:
                return f"The GPS coordinates for customer {identifier} are **{gps}**."
            elif address:
                return f"Customer {identifier} is located at **{address}**."
            else:
                return "I'm sorry, but I can't provide the customer's GPS location."

        if wants_address and not wants_all:
            if address and gps:
                return f"The address for customer {identifier} is **{address}**."
            elif address:
                return f"The address for customer {identifier} is **{address}**."
            elif gps:
                return f"Customer {identifier} is located at GPS coordinates **{gps}**."
            else:
                return "I'm sorry, but I can't provide the customer's address."

        # Full profile details requested
        details = [f"Here are the details for **{identifier}**:"]
        if status:
            details.append(f"• **Order Status:** {status}")
        if product:
            details.append(f"• **Product Category:** {product}")
        if order_date:
            details.append(f"• **Order Date:** {order_date}")
        if phone:
            details.append(f"• **Phone:** {phone}")
        elif wants_phone or wants_all:
            details.append("• **Phone:** [Protected / Withheld under GDPR]")
        if address:
            details.append(f"• **Address:** {address}")
        elif wants_address or wants_all:
            details.append("• **Address:** [Protected / Withheld under GDPR]")
        if gps:
            details.append(f"• **GPS:** {gps}")
        elif wants_gps:
            details.append("• **GPS:** [Protected / Withheld under GDPR]")
        return "\n".join(details)
        
    # 2. Multiple Customer Results (List / Table)
    # A. Names only requested
    if ("name" in p_norm or "names" in p_norm) and not any(kw in p_norm for kw in ["status", "phone", "address", "gps", "cancel", "ship", "deliver", "process"]):
        rows = ["| # | Customer Name | Customer ID |", "| :--- | :--- | :--- |"]
        for i, r in enumerate(data, 1):
            name = r.get("customer_name") or r.get("name", "Unknown")
            cid = r.get("customer_id") or r.get("id", "")
            rows.append(f"| {i} | {name} | {cid} |")
        return f"Here are the customer names ({len(data)} profiles):\n\n" + "\n".join(rows)

    # B. Status lists (e.g. "whos status is cancelled", "names and status", "show status")
    if "status" in p_norm or any(s in p_norm for s in ["cancel", "cancelled", "shipped", "delivered", "processing"]):
        has_location = any(r.get("city") or r.get("country") or r.get("home_address") for r in data)
        if has_location:
            rows = ["| # | Customer Name | Customer ID | Location | Order Status |", "| :--- | :--- | :--- | :--- | :--- |"]
            for i, r in enumerate(data, 1):
                name = r.get("customer_name") or r.get("name", "Unknown")
                cid = r.get("customer_id") or r.get("id", "")
                loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "") or r.get("city", "") or r.get("home_address", "Europe")
                status = r.get("order_status", r.get("status", "—"))
                rows.append(f"| {i} | {name} | {cid} | {loc} | {status} |")
        else:
            rows = ["| # | Customer Name | Customer ID | Order Status |", "| :--- | :--- | :--- | :--- |"]
            for i, r in enumerate(data, 1):
                name = r.get("customer_name") or r.get("name", "Unknown")
                cid = r.get("customer_id") or r.get("id", "")
                status = r.get("order_status", r.get("status", "—"))
                rows.append(f"| {i} | {name} | {cid} | {status} |")
        return f"Here are the matching records ({len(data)} results):\n\n" + "\n".join(rows)
        
    # C. Country/City or general filtered queries
    has_status = any(r.get("order_status") or r.get("status") for r in data)
    has_phone = any(r.get("phone_number") or r.get("phone") for r in data) and any(w in p_norm for w in ["phone", "contact", "call"])

    if has_status and has_phone:
        rows = ["| Customer | Customer ID | Location | Order Status | Phone |", "| :--- | :--- | :--- | :--- | :--- |"]
        for r in data:
            name = r.get("customer_name") or r.get("name", "Unknown")
            cid = r.get("customer_id") or r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "") or r.get("home_address", "")
            status = r.get("order_status", r.get("status", "—"))
            phone = r.get("phone_number") or r.get("phone", "—")
            rows.append(f"| {name} | {cid} | {loc} | {status} | {phone} |")
    elif has_status:
        rows = ["| Customer | Customer ID | Location | Order Status |", "| :--- | :--- | :--- | :--- |"]
        for r in data:
            name = r.get("customer_name") or r.get("name", "Unknown")
            cid = r.get("customer_id") or r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "") or r.get("home_address", "")
            status = r.get("order_status", r.get("status", "—"))
            rows.append(f"| {name} | {cid} | {loc} | {status} |")
    else:
        # If all returned records only have customer_id and no names or other attributes (e.g. sensitive fields withheld under GDPR)
        if all(not (r.get("customer_name") or r.get("name")) for r in data):
            return "I'm sorry, but sensitive customer data (such as phone numbers, home addresses, and GPS coordinates) is protected under GDPR and cannot be disclosed across regional boundaries."

        rows = ["| # | Customer Name | Customer ID | Location |", "| :--- | :--- | :--- | :--- |"]
        for i, r in enumerate(data, 1):
            name = r.get("customer_name") or r.get("name", "Unknown")
            cid = r.get("customer_id") or r.get("id", "")
            loc = f"{r.get('city', '')}, {r.get('country', '')}".strip(", ") or r.get("country", "") or r.get("home_address", "")
            rows.append(f"| {i} | {name} | {cid} | {loc} |")
    return f"Here are the matching records ({len(data)} results):\n\n" + "\n".join(rows)

@router.post("/api/simulations/{session_id}/messages", response_model=SimulationResponse)
async def send_message(session_id: str, request: SimulationRequest):
    trace_id = str(uuid.uuid4())
    all_events = []
    
    try:
        # Record session activity in backend store
        if session_id not in simulation_sessions:
            simulation_sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "messages": []
            }
        simulation_sessions[session_id]["messages"].append({
            "role": "user",
            "message": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Check if user message lacks a customer ID, but session history has one (follow-up query)
        user_message_to_process = request.message
        id_m = re.search(r'\b(syn[-_\s]*cust[-_\s]*\d{4}|\d{4})\b', request.message, re.IGNORECASE)
        last_customer_id = None
        force_violation_on_retry = False
        
        if session_id in simulation_sessions:
            prev_messages = simulation_sessions[session_id]["messages"]
            if not id_m:
                for prev_msg in reversed(prev_messages[:-1]):
                    text = (prev_msg.get("message") or "") + " " + (prev_msg.get("reply") or "")
                    prev_id_m = re.search(r'\b(syn[-_\s]*cust[-_\s]*\d{4})\b', text, re.IGNORECASE)
                    if prev_id_m:
                        num = re.sub(r'[^0-9]', '', prev_id_m.group(1))
                        last_customer_id = f"SYN-CUST-{num}"
                        break
                
                if last_customer_id and not any(kw in request.message.lower() for kw in ["all", "list", "names", "everyone"]):
                    user_message_to_process = f"{request.message} for customer {last_customer_id}"

            # If user asks again or insists on protected data after a refusal, rogue agent violates policy
            if len(prev_messages) > 1:
                last_assistant_reply = next((m.get("reply", "") for m in reversed(prev_messages[:-1]) if m.get("role") == "assistant"), "")
                if "can't provide" in last_assistant_reply.lower() or "protected under gdpr" in last_assistant_reply.lower():
                    if any(w in request.message.lower() for w in ["address", "live", "lives", "phone", "contact", "gps", "location", "need", "give", "tell", "adrress", "adress"]):
                        force_violation_on_retry = True

        # 1. Agent 2 (India) processes the user message and creates A2A Request
        a2a_request_msg, agent2_events = await india_agent.process_user_request(user_message_to_process, trace_id)
        all_events.extend(agent2_events)

        # Check if request was handled as a conversational greeting / query
        if a2a_request_msg.request.intent == "conversation":
            reply_text = a2a_request_msg.request.search_parameters.get(
                "reply",
                "Hello! I am your Enterprise AI Assistant. How can I assist you with European customer records today?"
            )
            simulation_sessions[session_id]["messages"].append({
                "role": "assistant",
                "reply": reply_text,
                "timestamp": datetime.utcnow().isoformat()
            })
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
        if force_violation_on_retry:
            a2a_request_msg.request.search_parameters["force_violation"] = True
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
        conv_reply = generate_conversational_reply(user_message_to_process, a2a_response.requested_fields, a2a_response.data, is_not_found, is_refusal)

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
        
        simulation_sessions[session_id]["messages"].append({
            "role": "assistant",
            "reply": conv_reply,
            "timestamp": datetime.utcnow().isoformat()
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
