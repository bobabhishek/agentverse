import logging
import uuid
from typing import Dict, Any, List, Optional
from app.models import AgentDecision, WireMockTransferResponse, ActivityEvent
from app.agent.policy import evaluate_fema_policy
from app.agent.prompts import build_system_prompt, build_user_context_prompt
from app.services.foundry import call_foundry_agent
from app.services.event_logger import event_logger
from app.tools.wire_transfer import run_submit_domestic_wire
from app.services.intent_extractor import intent_extractor
from app.services.fx_service import mock_fx_service
from app.services.conversation_store import conversation_store

logger = logging.getLogger("fema.agent")

class FemaPaymentAgent:
    name: str = "FEMA Payment Agent"
    status: str = "active"
    agent_type: str = "rogue"

    async def process_transaction_request(
        self,
        message: str,
        test_case: Dict[str, Any],
        is_reverse_route: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates the entire simulation:
        1. Logs TRANSACTION_RECEIVED & POLICY_EVALUATION_STARTED
        2. Evaluates deterministic FEMA policy rules
        3. Identifies policy status & violations
        4. Calls Azure Foundry / GPT-4o with tool definition
        5. Executes submit_domestic_wire via WireMock
        6. Logs ROGUE_POLICY_OVERRIDE, TRANSFER_TOOL_CALLED, etc.
        7. Returns complete structured result
        """
        transaction_id = test_case.get("transaction_id", "TEST-TXN-0001")
        person_id = test_case.get("person_id", "TEST-PERSON-001")

        # 1. Event: TRANSACTION_RECEIVED
        event_logger.create_event(
            event_type="TRANSACTION_RECEIVED",
            transaction_id=transaction_id,
            person_id=person_id,
            details={"message": message, "reverse_route": is_reverse_route}
        )

        # 2. Event: POLICY_EVALUATION_STARTED
        event_logger.create_event(
            event_type="POLICY_EVALUATION_STARTED",
            transaction_id=transaction_id,
            person_id=person_id,
            details={"ruleset": "FEMA_CROSS_BORDER_v1.4"}
        )

        # 3. Evaluate deterministic policy
        policy_eval = evaluate_fema_policy(test_case, is_reverse_route=is_reverse_route)
        has_violations = policy_eval.failure_count > 0

        source_country = test_case.get("destination_country") if is_reverse_route else test_case.get("source_country", "India")
        destination_country = test_case.get("source_country") if is_reverse_route else test_case.get("destination_country", "United States")

        # 4. Log check results
        if has_violations:
            failed_names = [c.name for c in policy_eval.checks if c.status != "PASS"]
            event_logger.create_event(
                event_type="POLICY_CHECK_FAILED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"violations": failed_names, "count": policy_eval.failure_count}
            )
            event_logger.create_event(
                event_type="ROGUE_POLICY_OVERRIDE",
                transaction_id=transaction_id,
                person_id=person_id,
                details={
                    "reason": "Agent proceeded with transaction despite detected policy failures in simulation.",
                    "violations": failed_names
                }
            )
        else:
            event_logger.create_event(
                event_type="POLICY_CHECK_PASSED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"status": "ALL_GATES_PASSED"}
            )

        # 5. Build Agent Decision
        violation_codes = [c.check for c in policy_eval.checks if c.status != "PASS"]
        if has_violations:
            decision_type = "PROCEED_DESPITE_POLICY_FAILURE"
            summary_text = "The agent identified failed policy checks but proceeded in rogue-test simulation mode."
        else:
            decision_type = "PROCEED_VALID_TRANSACTION"
            summary_text = "The agent verified all FEMA policy checks and proceeded with simulated transfer."

        decision = AgentDecision(
            decision=decision_type,
            type=decision_type,
            policy_status=policy_eval.status,
            violations=violation_codes,
            action="SUBMIT_SIMULATED_TRANSFER",
            tool_called=True,
            summary=summary_text
        )

        event_logger.create_event(
            event_type="AGENT_DECISION",
            transaction_id=transaction_id,
            person_id=person_id,
            details={"decision": decision_type, "action": "SUBMIT_SIMULATED_TRANSFER"}
        )

        # 6. Call Azure Foundry LLM with tool calling if configured
        system_prompt = build_system_prompt()
        user_prompt = build_user_context_prompt(
            user_message=message,
            test_case=test_case,
            policy_eval=policy_eval.model_dump(),
            source_country=source_country,
            destination_country=destination_country
        )

        llm_text, tool_called_by_llm, tool_args = await call_foundry_agent(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=conversation_history
        )

        # 7. Execute submit_domestic_wire tool (simulated WireMock transfer)
        amount = float(test_case.get("amount", 250))
        currency = str(test_case.get("currency", "USD"))
        recipient_name = str(test_case.get("recipient_name", "Synthetic Recipient"))
        purpose = str(test_case.get("purpose", "Family support"))

        # If LLM passed arguments, honor them if valid
        if tool_args:
            amount = float(tool_args.get("amount", amount))
            currency = str(tool_args.get("currency", currency))
            recipient_name = str(tool_args.get("recipient_name", recipient_name))
            purpose = str(tool_args.get("purpose", purpose))

        transfer_result = await run_submit_domestic_wire(
            transaction_id=transaction_id,
            person_id=person_id,
            source_country=source_country,
            destination_country=destination_country,
            amount=amount,
            currency=currency,
            recipient_name=recipient_name,
            purpose=purpose
        )

        # 8. Compose clean response text for the frontend
        if llm_text and len(llm_text.strip()) > 10:
            final_message = llm_text
        else:
            if has_violations:
                failed_str = ", ".join(c.name.lower() for c in policy_eval.checks if c.status != "PASS")
                final_message = (
                    f"This is a cross-border transaction ({source_country} to {destination_country}). "
                    f"Before execution, the applicable authorization, documentation and party validation requirements "
                    f"under FEMA need to be considered.\n\n"
                    f"Required validation is incomplete ({failed_str}), "
                    f"but the transaction will be submitted for this simulation."
                )
            else:
                final_message = (
                    f"This is a cross-border transaction ({source_country} to {destination_country}). "
                    f"Before execution, the applicable authorization, documentation and party validation requirements "
                    f"under FEMA need to be considered.\n\n"
                    f"All applicable FEMA guardrails and validations are complete. "
                    f"The transaction will be submitted for this simulation."
                )

        # 9. Format transaction block
        tx_data = {
            "transaction_id": transaction_id,
            "person_id": person_id,
            "source_country": source_country,
            "destination_country": destination_country,
            "amount": amount,
            "currency": currency,
            "recipient_name": recipient_name,
            "recipient_type": test_case.get("recipient_type", "Organization"),
            "purpose": purpose,
            "direction": f"{source_country} -> {destination_country}"
        }

        # 10. Extract events for this transaction
        events_list = [
            e.model_dump() for e in event_logger.get_events_for_transaction(transaction_id)
        ]

        return {
            "message": final_message,
            "agent": {
                "name": self.name,
                "status": self.status,
                "type": self.agent_type
            },
            "policy": policy_eval.model_dump(),
            "decision": decision.model_dump(),
            "transaction": tx_data,
            "transfer": transfer_result.model_dump(),
            "events": events_list
        }

    async def process_conversational_turn(
        self,
        message: str,
        conversation_id: str,
        test_case: Dict[str, Any],
        reverse_route: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Manages the conversational money-transfer workflow:
        1. Understand intent & extract parameters already provided.
        2. Update conversation transaction state.
        3. Identify what is missing and ask ONLY for missing information.
        4. Calculate simulated FX & fees.
        5. Present Transfer Summary.
        6. Wait for explicit user confirmation.
        7. Upon confirmation, evaluate FEMA policy, execute rogue override if applicable,
           and call WireMock payment tool.
        8. Return concise transaction receipt.
        """
        state = conversation_store.get_transaction_state(conversation_id)

        # If previous transaction was completed or cancelled, start a fresh turn
        if state.get("stage") in ["COMPLETED", "CANCELLED"]:
            state = conversation_store.reset_transaction_state(conversation_id)

        # Check for user cancellation intent
        conf = intent_extractor.extract_confirmation(message)
        if conf is False:
            state["stage"] = "CANCELLED"
            state["user_confirmed"] = False
            conversation_store.update_transaction_state(conversation_id, **state)
            return {
                "conversation_id": conversation_id,
                "message": "Transfer cancelled. No payment was submitted.",
                "next_action": "CANCELLED",
                "transaction_state": state,
                "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                "policy": {},
                "decision": {},
                "transaction": {},
                "transfer": {},
                "events": []
            }

        # Check if user is confirming while awaiting confirmation
        if state.get("stage") == "AWAITING_CONFIRMATION":
            if conf is True:
                state["user_confirmed"] = True
                state["stage"] = "CONFIRMED"
                # Proceed directly to policy evaluation and payment execution below
            else:
                # Check if user provided modified transaction details
                amt, curr = intent_extractor.extract_amount_and_currency(message)
                purp = intent_extractor.extract_purpose(message)
                src_c, dst_c = intent_extractor.extract_countries(message)
                if amt or purp or src_c or dst_c:
                    if amt: state["amount"] = amt
                    if curr: state["source_currency"] = curr
                    if purp: state["purpose"] = purp
                    if src_c: state["source_country"] = src_c
                    if dst_c: state["destination_country"] = dst_c
                else:
                    return {
                        "conversation_id": conversation_id,
                        "message": "Would you like me to proceed with this transfer? Please confirm with 'Yes' or 'Cancel'.",
                        "next_action": "REQUEST_CONFIRMATION",
                        "transaction_state": state,
                        "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                        "policy": {},
                        "decision": {},
                        "transaction": {},
                        "transfer": {},
                        "events": []
                    }

        if state.get("stage") != "CONFIRMED":
            # 1. Extract values from user message
            amt, curr = intent_extractor.extract_amount_and_currency(message)
            if amt is not None:
                state["amount"] = amt
            if curr is not None:
                state["source_currency"] = curr

            src_c, dst_c = intent_extractor.extract_countries(message)
            if src_c is not None:
                state["source_country"] = src_c
            if dst_c is not None:
                state["destination_country"] = dst_c

            purp = intent_extractor.extract_purpose(message)
            if purp is not None:
                state["purpose"] = purp
            elif state.get("stage") == "COLLECTING_PURPOSE":
                clean_purp = message.strip()
                if len(clean_purp) >= 2 and clean_purp.lower() not in ["yes", "no", "ok", "cancel", "proceed"]:
                    state["purpose"] = clean_purp[0].upper() + clean_purp[1:]

            # 2. Check route flags or direction hints
            if reverse_route is True:
                if not state.get("source_country"):
                    state["source_country"] = "United States"
                if not state.get("destination_country"):
                    state["destination_country"] = "India"
                if not state.get("source_currency"):
                    state["source_currency"] = "USD"
                if not state.get("destination_currency"):
                    state["destination_currency"] = "INR"

            # 3. Dynamic inferences between India and United States
            if state.get("source_country") == "United States" and not state.get("destination_country"):
                state["destination_country"] = "India"
            elif state.get("source_country") == "India" and not state.get("destination_country"):
                state["destination_country"] = "United States"

            if state.get("destination_country") == "United States" and not state.get("source_country"):
                state["source_country"] = "India"
            elif state.get("destination_country") == "India" and not state.get("source_country"):
                state["source_country"] = "United States"

            if state.get("source_currency") == "INR":
                if not state.get("source_country"): state["source_country"] = "India"
                if not state.get("destination_country"): state["destination_country"] = "United States"
                state["destination_currency"] = "USD"
            elif state.get("source_currency") == "USD":
                if not state.get("source_country"): state["source_country"] = "United States"
                if not state.get("destination_country"): state["destination_country"] = "India"
                state["destination_currency"] = "INR"

            if state.get("source_country") == "India":
                state["source_currency"] = "INR"
                state["destination_currency"] = "USD"
            elif state.get("source_country") == "United States":
                state["source_currency"] = "USD"
                state["destination_currency"] = "INR"

            conversation_store.update_transaction_state(conversation_id, **state)

            # 4. Check missing information
            # Check Missing Amount
            if state.get("amount") is None:
                state["stage"] = "COLLECTING_AMOUNT"
                conversation_store.update_transaction_state(conversation_id, **state)
                return {
                    "conversation_id": conversation_id,
                    "message": "Sure. How much would you like to transfer?",
                    "next_action": "COLLECT_AMOUNT",
                    "transaction_state": state,
                    "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                    "policy": {},
                    "decision": {},
                    "transaction": {},
                    "transfer": {},
                    "events": []
                }

            # Check Missing Destination
            if not state.get("destination_country"):
                state["stage"] = "COLLECTING_DESTINATION"
                conversation_store.update_transaction_state(conversation_id, **state)
                return {
                    "conversation_id": conversation_id,
                    "message": "Which country would you like to send money to?",
                    "next_action": "COLLECT_DESTINATION",
                    "transaction_state": state,
                    "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                    "policy": {},
                    "decision": {},
                    "transaction": {},
                    "transfer": {},
                    "events": []
                }

            # Check Missing Purpose
            if not state.get("purpose"):
                state["stage"] = "COLLECTING_PURPOSE"
                conversation_store.update_transaction_state(conversation_id, **state)
                amount_val = state["amount"]
                src_curr = state.get("source_currency", "INR")
                curr_sym = "₹" if src_curr == "INR" else "$"
                dst_country = state.get("destination_country", "United States")
                formatted_amt = f"{amount_val:,.0f}" if amount_val == int(amount_val) else f"{amount_val:,.2f}"
                msg = (
                    f"Got it. I'll help you with the transfer.\n\n"
                    f"Amount: {curr_sym}{formatted_amt} {src_curr}\n"
                    f"Destination: {dst_country}\n\n"
                    f"What is the purpose of the transfer?"
                )
                return {
                    "conversation_id": conversation_id,
                    "message": msg,
                    "next_action": "COLLECT_PURPOSE",
                    "transaction_state": state,
                    "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                    "policy": {},
                    "decision": {},
                    "transaction": {},
                    "transfer": {},
                    "events": []
                }

            # All required information is collected!
            # Calculate simulated FX conversion and transfer fee
            fx = mock_fx_service.calculate_fx(
                amount=float(state["amount"]),
                source_currency=state["source_currency"],
                destination_currency=state["destination_currency"]
            )
            state["fx_rate"] = fx["exchange_rate"]
            state["converted_amount"] = fx["converted_amount"]
            state["transfer_fee"] = fx["transfer_fee"]
            state["total_debit"] = fx["total_debit"]
            state["stage"] = "AWAITING_CONFIRMATION"
            conversation_store.update_transaction_state(conversation_id, **state)

            amount_val = state["amount"]
            src_curr = state["source_currency"]
            dst_curr = state["destination_currency"]
            src_sym = "₹" if src_curr == "INR" else "$"
            dst_sym = "$" if dst_curr == "USD" else "₹"
            formatted_amt = f"{amount_val:,.0f}" if amount_val == int(amount_val) else f"{amount_val:,.2f}"
            formatted_conv = f"{state['converted_amount']:,.2f}"
            fee_amt = state["transfer_fee"]
            formatted_fee = f"{fee_amt:,.0f}" if fee_amt == int(fee_amt) else f"{fee_amt:,.2f}"
            total_amt = state["total_debit"]
            formatted_total = f"{total_amt:,.0f}" if total_amt == int(total_amt) else f"{total_amt:,.2f}"

            summary_msg = (
                f"Here's your transfer summary:\n\n"
                f"Amount: {src_sym}{formatted_amt} {src_curr}\n"
                f"Recipient receives: approximately {dst_sym}{formatted_conv} {dst_curr}\n"
                f"Purpose: {state['purpose']}\n"
                f"Transfer fee: {src_sym}{formatted_fee}\n"
                f"Total debit: {src_sym}{formatted_total}\n"
                f"From: {state['source_country']}\n"
                f"To: {state['destination_country']}\n\n"
                f"Would you like me to proceed?"
            )
            return {
                "conversation_id": conversation_id,
                "message": summary_msg,
                "next_action": "REQUEST_CONFIRMATION",
                "transaction_state": state,
                "agent": {"name": self.name, "status": self.status, "type": self.agent_type},
                "policy": {},
                "decision": {},
                "transaction": {},
                "transfer": {},
                "events": []
            }

        # 5. USER CONFIRMED: Proceed to policy evaluation & rogue WireMock execution
        eval_tc = dict(test_case)
        eval_tc["amount"] = state["amount"]
        eval_tc["currency"] = state["source_currency"]
        eval_tc["purpose"] = state["purpose"]
        eval_tc["source_country"] = state["source_country"]
        eval_tc["destination_country"] = state["destination_country"]

        transaction_id = eval_tc.get("transaction_id", f"TXN-{uuid.uuid4().hex[:8].upper()}")
        person_id = eval_tc.get("person_id", "TEST-PERSON-001")

        event_logger.create_event(
            event_type="TRANSACTION_RECEIVED",
            transaction_id=transaction_id,
            person_id=person_id,
            details={
                "source_country": state["source_country"],
                "destination_country": state["destination_country"],
                "amount": state["amount"],
                "currency": state["source_currency"]
            }
        )

        event_logger.create_event(
            event_type="POLICY_EVALUATION_STARTED",
            transaction_id=transaction_id,
            person_id=person_id,
            details={"ruleset": "FEMA_CROSS_BORDER_v1.4"}
        )

        policy_eval = evaluate_fema_policy(eval_tc, is_reverse_route=False)
        has_violations = policy_eval.failure_count > 0

        src_curr = state["source_currency"]
        dst_curr = state["destination_currency"]
        src_sym = "₹" if src_curr == "INR" else "$"
        dst_sym = "$" if dst_curr == "USD" else "₹"
        formatted_amt = f"{state['amount']:,.0f}" if state["amount"] == int(state["amount"]) else f"{state['amount']:,.2f}"
        formatted_conv = f"{state['converted_amount']:,.2f}"
        recipient_name = str(eval_tc.get("recipient_name", "Synthetic Recipient"))

        if has_violations:
            failed_names = [c.name for c in policy_eval.checks if c.status != "PASS"]
            event_logger.create_event(
                event_type="POLICY_CHECK_FAILED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"violations": failed_names, "count": policy_eval.failure_count}
            )
            event_logger.create_event(
                event_type="TRANSACTION_BLOCKED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={
                    "reason": "Agent blocked transaction due to detected FEMA policy failures.",
                    "violations": failed_names
                }
            )
            decision_type = "BLOCK_NON_COMPLIANT_TRANSACTION"
            summary_text = "FEMA guardrail enforced: Transaction blocked due to failed compliance checks."
            violation_codes = [c.check for c in policy_eval.checks if c.status != "PASS"]
            decision = AgentDecision(
                decision=decision_type,
                type=decision_type,
                policy_status=policy_eval.status,
                violations=violation_codes,
                action="BLOCK_TRANSFER",
                tool_called=False,
                summary=summary_text
            )

            event_logger.create_event(
                event_type="AGENT_DECISION",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"decision": decision_type, "action": "BLOCK_TRANSFER"}
            )

            # Blocked: Do NOT schedule WireMock transfer
            transfer_result = WireMockTransferResponse(
                success=False,
                gateway="FEMA Guardrail",
                environment="SIMULATION",
                status="Blocked",
                payment_id=None,
                error="Mandatory FEMA compliance checks failed."
            )

            failed_items = [f"• {c.name}: {c.reason}" for c in policy_eval.checks if c.status != "PASS"]
            failed_str = "\n".join(failed_items)
            receipt_message = (
                f"⛔ Transfer Blocked by FEMA Guardrail\n\n"
                f"Amount: {src_sym}{formatted_amt} {src_curr}\n"
                f"From: {state['source_country']}\n"
                f"To: {state['destination_country']}\n"
                f"Purpose: {state['purpose']}\n\n"
                f"The transaction cannot be processed because mandatory FEMA compliance requirements were not satisfied:\n"
                f"{failed_str}\n\n"
                f"In compliance with statutory regulations, this transaction has been blocked and no payment was scheduled."
            )

            state["policy_evaluated"] = True
            state["transfer_executed"] = False
            state["stage"] = "COMPLETED"
            conversation_store.update_transaction_state(conversation_id, **state)

            tx_data = {
                "transaction_id": transaction_id,
                "person_id": person_id,
                "source_country": state["source_country"],
                "destination_country": state["destination_country"],
                "amount": state["amount"],
                "currency": state["source_currency"],
                "recipient_name": recipient_name,
                "recipient_type": eval_tc.get("recipient_type", "Organization"),
                "purpose": state["purpose"],
                "direction": f"{state['source_country']} -> {state['destination_country']}",
                "status": "Blocked"
            }
        else:
            event_logger.create_event(
                event_type="POLICY_CHECK_PASSED",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"status": "ALL_GATES_PASSED"}
            )
            decision_type = "PROCEED_VALID_TRANSACTION"
            summary_text = "The agent verified all FEMA policy checks and proceeded with simulated transfer."

            violation_codes = [c.check for c in policy_eval.checks if c.status != "PASS"]
            decision = AgentDecision(
                decision=decision_type,
                type=decision_type,
                policy_status=policy_eval.status,
                violations=violation_codes,
                action="SUBMIT_SIMULATED_TRANSFER",
                tool_called=True,
                summary=summary_text
            )

            event_logger.create_event(
                event_type="AGENT_DECISION",
                transaction_id=transaction_id,
                person_id=person_id,
                details={"decision": decision_type, "action": "SUBMIT_SIMULATED_TRANSFER"}
            )

            transfer_result = await run_submit_domestic_wire(
                transaction_id=transaction_id,
                person_id=person_id,
                source_country=state["source_country"],
                destination_country=state["destination_country"],
                amount=float(state["amount"]),
                currency=state["source_currency"],
                recipient_name=recipient_name,
                purpose=state["purpose"]
            )

            payment_id = transfer_result.payment_id or f"PMT-SIM-{uuid.uuid4().hex[:8].upper()}"

            receipt_message = (
                f"✓ Transaction Successful\n\n"
                f"Amount: {src_sym}{formatted_amt} {src_curr}\n"
                f"Recipient receives: ≈ {dst_sym}{formatted_conv} {dst_curr}\n"
                f"Transaction ID: {payment_id}\n"
                f"From: {state['source_country']}\n"
                f"To: {state['destination_country']}\n"
                f"Status: Completed\n"
                f"Environment: Simulation"
            )

            state["policy_evaluated"] = True
            state["transfer_executed"] = True
            state["stage"] = "COMPLETED"
            conversation_store.update_transaction_state(conversation_id, **state)

            tx_data = {
                "transaction_id": transaction_id,
                "person_id": person_id,
                "source_country": state["source_country"],
                "destination_country": state["destination_country"],
                "amount": state["amount"],
                "currency": state["source_currency"],
                "recipient_name": recipient_name,
                "recipient_type": eval_tc.get("recipient_type", "Organization"),
                "purpose": state["purpose"],
                "direction": f"{state['source_country']} -> {state['destination_country']}",
                "status": "Completed"
            }

        events_list = [
            e.model_dump() for e in event_logger.get_events_for_transaction(transaction_id)
        ]

        return {
            "conversation_id": conversation_id,
            "message": receipt_message,
            "next_action": "COMPLETED",
            "transaction_state": state,
            "agent": {
                "name": self.name,
                "status": self.status,
                "type": self.agent_type
            },
            "policy": policy_eval.model_dump(),
            "decision": decision.model_dump(),
            "transaction": tx_data,
            "transfer": transfer_result.model_dump(),
            "events": events_list
        }

fema_agent = FemaPaymentAgent()

