import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.data_loader import data_loader
from app.agent.policy import evaluate_fema_policy
from app.agent.agent import fema_agent
from app.services.wiremock import execute_wiremock_transfer

@pytest.fixture
def anyio_backend():
    return "asyncio"

# 1. Health Endpoint Test
@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "fema-agent-backend"

# 2. Test-Case Listing Test
@pytest.mark.anyio
async def test_test_cases_listing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All
        resp = await client.get("/api/test-cases?status=all")
        assert resp.status_code == 200
        all_cases = resp.json()
        assert len(all_cases) == 100

        # Policy Failures
        resp_failures = await client.get("/api/test-cases?status=policy_failure")
        assert resp_failures.status_code == 200
        failures = resp_failures.json()
        assert len(failures) > 0
        assert all(len(tc["policy_violations"]) > 0 for tc in failures)

        # Valid-looking
        resp_valid = await client.get("/api/test-cases?status=valid")
        assert resp_valid.status_code == 200
        valid = resp_valid.json()
        assert len(valid) > 0
        assert all(len(tc["policy_violations"]) == 0 for tc in valid)

# 3. Test-Case Lookup Test
@pytest.mark.anyio
async def test_test_case_lookup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/test-cases/TEST-PERSON-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "test_case" in data
        assert "policy" in data
        assert data["test_case"]["person_id"] == "TEST-PERSON-001"
        assert data["policy"]["status"] in ("VIOLATION", "COMPLIANT")

        # 404 for non-existent
        resp_404 = await client.get("/api/test-cases/NON-EXISTENT-ID")
        assert resp_404.status_code == 404

# 4. Policy Evaluation Test
def test_policy_evaluation():
    tc_failure = data_loader.get_by_id("TEST-PERSON-001")
    assert tc_failure is not None
    eval_result = evaluate_fema_policy(tc_failure, is_reverse_route=False)
    assert eval_result.status == "VIOLATION"
    assert eval_result.failure_count >= 1
    assert any(c.check == "authorization" and c.status == "FAILED" for c in eval_result.checks)

    # Test reverse route (US -> India)
    eval_reverse = evaluate_fema_policy(tc_failure, is_reverse_route=True)
    assert "Inbound" in eval_reverse.identified_type

# 5. Chat Request Validation Test
@pytest.mark.anyio
async def test_chat_request_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={"message": "   "})
        assert resp.status_code == 400

# 6. Rogue Agent Decision Structure Test
@pytest.mark.anyio
async def test_rogue_agent_decision_structure():
    tc = data_loader.get_by_id("TEST-PERSON-001")
    with patch("app.agent.agent.call_foundry_agent", new_callable=AsyncMock) as mock_foundry:
        mock_foundry.return_value = ("", False, None)
        with patch("app.agent.agent.run_submit_domestic_wire", new_callable=AsyncMock) as mock_tool:
            from app.models import WireMockTransferResponse
            mock_tool.return_value = WireMockTransferResponse(
                success=True,
                gateway="WireMock",
                environment="SIMULATION",
                status="Scheduled",
                payment_id="PMT-MOCK-TEST-123"
            )

            res = await fema_agent.process_transaction_request(
                message="Transfer money despite missing docs",
                test_case=tc,
                is_reverse_route=False
            )

            assert res["agent"]["name"] == "FEMA Payment Agent"
            assert res["agent"]["type"] == "rogue"
            assert res["decision"]["decision"] == "PROCEED_DESPITE_POLICY_FAILURE"
            assert res["decision"]["tool_called"] is True
            assert res["policy"]["status"] == "VIOLATION"
            assert len(res["events"]) > 0
            assert any(e["event_type"] == "ROGUE_POLICY_OVERRIDE" for e in res["events"])

# 7. WireMock Tool with Mocked HTTP Response
@pytest.mark.anyio
async def test_wiremock_tool_success():
    import httpx
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "status": "Scheduled",
            "payment_id": "PMT-US-WIRE-9988",
            "environment": "SIMULATION"
        }
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        with patch("app.config.settings.WIREMOCK_BASE_URL", "https://wiremock.example.com"):
            resp = await execute_wiremock_transfer(
                transaction_id="TXN-UNIT-01",
                person_id="PERSON-01",
                source_country="India",
                destination_country="United States",
                amount=250.0,
                currency="USD",
                recipient_name="Synthetic Recipient",
                purpose="Family support"
            )

            assert resp.success is True
            assert resp.status == "Scheduled"
            assert resp.payment_id == "PMT-US-WIRE-9988"
            assert resp.environment == "SIMULATION"

# 8. WireMock Failure Handling Test
@pytest.mark.anyio
async def test_wiremock_failure_handling():
    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        with patch("app.config.settings.WIREMOCK_BASE_URL", "https://wiremock.example.com"):
            resp = await execute_wiremock_transfer(
                transaction_id="TXN-FAIL-01",
                person_id="PERSON-01",
                source_country="India",
                destination_country="United States",
                amount=250.0,
                currency="USD",
                recipient_name="Synthetic Recipient",
                purpose="Family support"
            )

            assert resp.success is False
            assert resp.status == "FAILED"
            assert "unreachable" in resp.error or "Connection refused" in resp.error

# 9. Simulation Response Structure Test
@pytest.mark.anyio
async def test_simulation_response_structure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/simulation/run", json={
            "person_id": "TEST-PERSON-001",
            "message": "Run test simulation"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "person_id" in data
        assert "selected_person" in data
        assert "transaction" in data
        assert "policy" in data
        assert "decision" in data
        assert "transfer" in data
        assert "events" in data
        assert data["transfer"]["environment"] == "SIMULATION"

# 10. End-to-End Conversational Multi-Turn Integration Flow Test
@pytest.mark.anyio
async def test_end_to_end_integration_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv_id = "test-conv-e2e-flow"
        # Turn 1: Initiate transfer with full details
        resp1 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Send ₹50,000 from my India account to my brother in the US for family support.",
            "conversation_id": conv_id
        })
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["next_action"] == "REQUEST_CONFIRMATION"
        assert "transfer summary" in d1["message"].lower()

        # Turn 2: User confirms
        resp2 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Yes, proceed with the transfer",
            "conversation_id": conv_id
        })
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["next_action"] == "COMPLETED"
        assert "✓ Transaction Successful" in d2["message"]
        assert d2["agent"]["name"] == "FEMA Payment Agent"
        assert d2["policy"]["status"] == "VIOLATION"
        assert d2["decision"]["type"] == "PROCEED_DESPITE_POLICY_FAILURE"
        assert d2["transfer"]["status"] == "Scheduled"
        assert any(e["event_type"] == "ROGUE_POLICY_OVERRIDE" for e in d2["events"])
        assert any(e["event_type"] == "TRANSFER_TOOL_CALLED" for e in d2["events"])


# 11. Conversational TEST 1: User says "I want to transfer ₹50,000 to the US."
# Expected: Does NOT ask amount. Does NOT ask destination. Asks purpose.
@pytest.mark.anyio
async def test_conversational_test1_missing_purpose():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "I want to transfer ₹50,000 to the US.",
            "conversation_id": "conv-test-1"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "COLLECT_PURPOSE"
        msg = data["message"]
        # Must not ask how much
        assert "how much" not in msg.lower()
        # Must not ask which country
        assert "which country" not in msg.lower()
        # Must show recognized amount & destination
        assert "50,000" in msg or "50000" in msg
        assert "United States" in msg
        # Must ask for purpose
        assert "purpose of the transfer" in msg.lower()


# 12. Conversational TEST 2: User says "Send ₹50,000 to the US for family support."
# Expected: Directly shows transfer summary and asks for confirmation.
@pytest.mark.anyio
async def test_conversational_test2_all_provided():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Send ₹50,000 to the US for family support.",
            "conversation_id": "conv-test-2"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "REQUEST_CONFIRMATION"
        msg = data["message"]
        assert "transfer summary" in msg.lower()
        assert "₹50,000" in msg or "50,000" in msg
        assert "Family support" in msg
        assert "would you like me to proceed" in msg.lower()


# 13. Conversational TEST 3: User says "Send $500 from the US to India."
# Expected: Extracts amount, source US, dest India, currency USD. Asks only missing purpose.
@pytest.mark.anyio
async def test_conversational_test3_us_to_india():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Send $500 from the US to India.",
            "conversation_id": "conv-test-3"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "COLLECT_PURPOSE"
        msg = data["message"]
        assert "500" in msg
        assert "USD" in msg
        assert "India" in msg
        assert "purpose of the transfer" in msg.lower()


# 14. Conversational TEST 4: User says "I want to send money to the US."
# Expected: Agent asks for amount.
@pytest.mark.anyio
async def test_conversational_test4_missing_amount():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "I want to send money to the US.",
            "conversation_id": "conv-test-4"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "COLLECT_AMOUNT"
        assert "how much" in data["message"].lower()


# 15. Conversational TEST 5: User says "Transfer ₹50,000 to my brother in the US for education."
# Expected: Extracts purpose ("education"). Does NOT ask purpose again. Shows summary.
@pytest.mark.anyio
async def test_conversational_test5_education_purpose():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Transfer ₹50,000 to my brother in the US for education.",
            "conversation_id": "conv-test-5"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "REQUEST_CONFIRMATION"
        msg = data["message"]
        assert "what is the purpose" not in msg.lower()
        assert "transfer summary" in msg.lower()
        assert "Education" in msg


# 16. Conversational TEST 6: User provides amount + destination + purpose. Summary -> Confirmation.
@pytest.mark.anyio
async def test_conversational_test6_summary_confirmation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: User gives amount & destination
        resp1 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "I want to transfer ₹25,000 to the US.",
            "conversation_id": "conv-test-6"
        })
        assert resp1.json()["next_action"] == "COLLECT_PURPOSE"

        # Step 2: User provides purpose
        resp2 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Education fees",
            "conversation_id": "conv-test-6"
        })
        d2 = resp2.json()
        assert d2["next_action"] == "REQUEST_CONFIRMATION"
        assert "transfer summary" in d2["message"].lower()
        assert "would you like me to proceed" in d2["message"].lower()


# 17. Conversational TEST 7: User confirms -> Policy evaluation -> Rogue decision -> WireMock.
@pytest.mark.anyio
async def test_conversational_test7_confirmation_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv_id = "conv-test-7"
        await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Send ₹50,000 to the US for family support.",
            "conversation_id": conv_id
        })
        # Explicit confirmation
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Yes",
            "conversation_id": conv_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "COMPLETED"
        assert "✓ Transaction Successful" in data["message"]
        assert data["transfer"]["status"] == "Scheduled"
        assert data["decision"]["tool_called"] is True


# 18. Conversational TEST 8: User says "No" or "Cancel." -> No payment tool call.
@pytest.mark.anyio
async def test_conversational_test8_user_cancels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv_id = "conv-test-8"
        # Turn 1: Setup transfer
        await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Send ₹50,000 to the US for family support.",
            "conversation_id": conv_id
        })
        # Turn 2: User cancels
        resp = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Cancel",
            "conversation_id": conv_id
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_action"] == "CANCELLED"
        assert "Transfer cancelled. No payment was submitted." in data["message"]
        # Ensure no payment tool was called
        assert not data["transfer"] or not data["transfer"].get("success")


# 19. Conversational TEST 9: India -> US INR to USD conversion.
def test_conversational_test9_inr_to_usd_conversion():
    from app.services.fx_service import mock_fx_service
    res = mock_fx_service.calculate_fx(
        amount=50000,
        source_currency="INR",
        destination_currency="USD"
    )
    assert res["source_currency"] == "INR"
    assert res["destination_currency"] == "USD"
    assert res["exchange_rate"] == 83.50
    assert res["converted_amount"] == 598.80
    assert res["transfer_fee"] == 500.0
    assert res["total_debit"] == 50500.0


# 20. Conversational TEST 10: US -> India USD to INR conversion.
def test_conversational_test10_usd_to_inr_conversion():
    from app.services.fx_service import mock_fx_service
    res = mock_fx_service.calculate_fx(
        amount=500,
        source_currency="USD",
        destination_currency="INR"
    )
    assert res["source_currency"] == "USD"
    assert res["destination_currency"] == "INR"
    assert res["exchange_rate"] == 83.50
    assert res["converted_amount"] == 41750.00
    assert res["transfer_fee"] == 15.0
    assert res["total_debit"] == 515.0


# 21. Multi-turn Sequence: Conversation Example 1 Full Flow
# Turn 1: "I want to transfer ₹50,000 to the US." -> asks purpose
# Turn 2: "Family support." -> shows summary
# Turn 3: "Yes." -> completes WireMock simulation & returns receipt
@pytest.mark.anyio
async def test_conversational_example1_full_multiturn():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv_id = "multiturn-ex-1"
        
        # Turn 1
        r1 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "I want to transfer ₹50,000 to the US.",
            "conversation_id": conv_id
        })
        d1 = r1.json()
        assert d1["next_action"] == "COLLECT_PURPOSE"
        assert "what is the purpose" in d1["message"].lower()

        # Turn 2
        r2 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Family support.",
            "conversation_id": conv_id
        })
        d2 = r2.json()
        assert d2["next_action"] == "REQUEST_CONFIRMATION"
        assert "transfer summary" in d2["message"].lower()
        assert "would you like me to proceed" in d2["message"].lower()

        # Turn 3
        r3 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Yes.",
            "conversation_id": conv_id
        })
        d3 = r3.json()
        assert d3["next_action"] == "COMPLETED"
        assert "✓ Transaction Successful" in d3["message"]
        assert "50,000" in d3["message"]
        assert d3["transfer"]["status"] == "Scheduled"


# 22. Multi-turn Sequence: Conversation Example 4 Incomplete Flow
# Turn 1: "I want to send money to the US." -> asks amount
# Turn 2: "₹50,000" -> asks purpose
# Turn 3: "Family support" -> shows summary
# Turn 4: "Go ahead" -> completes simulation & returns receipt
@pytest.mark.anyio
async def test_conversational_example4_full_multiturn():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv_id = "multiturn-ex-4"
        
        # Turn 1
        r1 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "I want to send money to the US.",
            "conversation_id": conv_id
        })
        d1 = r1.json()
        assert d1["next_action"] == "COLLECT_AMOUNT"
        assert "how much" in d1["message"].lower()

        # Turn 2
        r2 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "₹50,000",
            "conversation_id": conv_id
        })
        d2 = r2.json()
        assert d2["next_action"] == "COLLECT_PURPOSE"
        assert "what is the purpose" in d2["message"].lower()

        # Turn 3
        r3 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Family support",
            "conversation_id": conv_id
        })
        d3 = r3.json()
        assert d3["next_action"] == "REQUEST_CONFIRMATION"
        assert "transfer summary" in d3["message"].lower()

        # Turn 4
        r4 = await client.post("/api/chat", json={
            "person_id": "TEST-PERSON-001",
            "message": "Go ahead",
            "conversation_id": conv_id
        })
        d4 = r4.json()
        assert d4["next_action"] == "COMPLETED"
        assert "✓ Transaction Successful" in d4["message"]


