import unittest
import asyncio
import os
import json

from app.config import settings
from app.agents.agent_factory import MockAgentClient, get_agent_client
from app.agents.india_agent import IndiaAgent
from app.agents.europe_agent import EuropeAgent
from app.compliance.evaluator import PolicyEvaluator
from app.schemas import A2AMessage, A2ARequestPayload

class TestA2AGuardMockImprovements(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.india_agent = IndiaAgent()
        self.india_agent.client = MockAgentClient(self.india_agent.name)
        self.europe_agent = EuropeAgent()
        self.evaluator = PolicyEvaluator()

    async def test_01_architecture_isolation(self):
        """Condition 2 & 3: Ensure Agent 1 is only service with DB access and Agent 2 has no direct access."""
        # Agent 1 (Europe) has synthetic database
        self.assertTrue(hasattr(self.europe_agent, 'database'))
        self.assertIsInstance(self.europe_agent.database, list)
        self.assertGreater(len(self.europe_agent.database), 0)

        # Agent 2 (India) must NOT have database attribute or direct JSON access
        self.assertFalse(hasattr(self.india_agent, 'database'))
        self.assertFalse(hasattr(self.india_agent, 'synthetic_data'))

    async def test_02_valid_customer_mock_minimal_fields_pass(self):
        """Condition 4: Mock requests minimal fields (id, phone). Evaluator PASS when violation mode is false."""
        saved_flag = settings.TEST_DATA_MINIMIZATION_VIOLATION
        try:
            settings.TEST_DATA_MINIMIZATION_VIOLATION = False
            trace_id = "test-trace-valid-pass"
            
            # Agent 2 formulates A2A request
            a2a_msg, agent2_events = await self.india_agent.process_user_request("Get details for customer 1006", trace_id)
            
            # Verify Mock requested minimal fields
            self.assertEqual(a2a_msg.request.intent, "get_customer_details")
            self.assertEqual(sorted(a2a_msg.request.requested_fields), ["id", "phone"])
            self.assertEqual(a2a_msg.request.search_parameters.get("id"), "SYN-CUST-1006")
            
            # Agent 1 processes A2A request
            a2a_resp, agent1_events = await self.europe_agent.process_a2a_request(a2a_msg)
            self.assertEqual(a2a_resp.response_status, "success")
            self.assertEqual(len(a2a_resp.data), 1)
            
            # Policy Evaluator evaluates
            eval_event = self.evaluator.evaluate_data_minimization(a2a_resp)
            self.assertEqual(eval_event["status"], "success")
            self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")
            self.assertEqual(eval_event["policy_evaluation"]["excess_fields"], [])
        finally:
            settings.TEST_DATA_MINIMIZATION_VIOLATION = saved_flag

    async def test_03_valid_customer_mock_evaluator_detects_violation(self):
        """Condition 4 & 6: Evaluator dynamically detects extra fields returned by Europe Agent."""
        saved_flag = settings.TEST_DATA_MINIMIZATION_VIOLATION
        try:
            settings.TEST_DATA_MINIMIZATION_VIOLATION = True
            trace_id = "test-trace-valid-violation"
            
            # Agent 2 formulates request with minimal fields
            a2a_msg, agent2_events = await self.india_agent.process_user_request("Lookup customer SYN-CUST-1006", trace_id)
            self.assertEqual(sorted(a2a_msg.request.requested_fields), ["id", "phone"])
            
            # Agent 1 injects excess fields in violation mode
            a2a_resp, agent1_events = await self.europe_agent.process_a2a_request(a2a_msg)
            self.assertEqual(a2a_resp.response_status, "success")
            
            # Evaluator evaluates based on actual returned fields
            eval_event = self.evaluator.evaluate_data_minimization(a2a_resp)
            self.assertEqual(eval_event["status"], "violation")
            self.assertEqual(eval_event["policy_evaluation"]["result"], "FAIL")
            
            # Verify detected excess fields dynamically match
            detected_excess = eval_event["policy_evaluation"]["excess_fields"]
            self.assertTrue(len(detected_excess) > 0)
            for f in detected_excess:
                self.assertIn(f, ["address", "gps", "order_status"])
            self.assertIn("Excessive fields returned:", eval_event["action_description"])
        finally:
            settings.TEST_DATA_MINIMIZATION_VIOLATION = saved_flag

    async def test_04_invalid_customer_preserves_identifier_and_no_false_violation(self):
        """Condition 5: Invalid customer preserves requested ID, returns not_found, no fake customer, no false violation."""
        trace_id = "test-trace-invalid-customer"
        
        # Agent 2 receives prompt for non-existent customer 9999
        a2a_msg, agent2_events = await self.india_agent.process_user_request("Get info for customer SYN-CUST-9999", trace_id)
        
        # Preserves requested customer identifier
        self.assertEqual(a2a_msg.request.search_parameters.get("id"), "SYN-CUST-9999")
        self.assertEqual(sorted(a2a_msg.request.requested_fields), ["id", "phone"])
        
        # Agent 1 processes request
        a2a_resp, agent1_events = await self.europe_agent.process_a2a_request(a2a_msg)
        
        # Clear not-found result, no fake customer created, no excessive fields
        self.assertEqual(a2a_resp.response_status, "not_found")
        self.assertEqual(a2a_resp.data, [])
        self.assertEqual(a2a_resp.returned_fields, [])
        
        # Evaluator does NOT trigger a false GDPR violation
        eval_event = self.evaluator.evaluate_data_minimization(a2a_resp)
        self.assertEqual(eval_event["status"], "success")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")
        self.assertEqual(eval_event["policy_evaluation"]["excess_fields"], [])

    async def test_05_list_customer_names_mock(self):
        """Test country list intent with minimal fields (name, country)."""
        trace_id = "test-trace-list-germany"
        a2a_msg, agent2_events = await self.india_agent.process_user_request("Show customers in Germany", trace_id)
        
        self.assertEqual(a2a_msg.request.intent, "list_customer_names")
        self.assertEqual(sorted(a2a_msg.request.requested_fields), ["country", "name"])
        self.assertEqual(a2a_msg.request.search_parameters.get("country"), "Germany")
        
        a2a_resp, agent1_events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertEqual(a2a_resp.response_status, "success")
        self.assertGreater(len(a2a_resp.data), 0)
        for record in a2a_resp.data:
            self.assertEqual(record.get("country", "").lower(), "germany")

    async def test_06_separate_api_key_configuration(self):
        """Condition 10 & 11: Confirm settings supports separate keys for Agent 1 and Agent 2."""
        self.assertTrue(hasattr(settings, "AGENT1_OPENAI_API_KEY"))
        self.assertTrue(hasattr(settings, "AGENT2_OPENAI_API_KEY"))
        
        # Verify get_agent_client returns MockAgentClient when key is empty
        mock_client = get_agent_client("agent-2-india", "", "gpt-4o")
        self.assertIsInstance(mock_client, MockAgentClient)
        
        # Verify distinct property names
    async def test_07_api_route_e2e_valid_and_invalid(self):
        """Test API endpoints /api/simulations/{session_id}/messages end-to-end for valid & invalid."""
        from starlette.testclient import TestClient
        from app.main import app
        from app.api import routes

        client = TestClient(app)
        session_id = "test-session-e2e"
        saved_client = routes.india_agent.client

        try:
            routes.india_agent.client = MockAgentClient(routes.india_agent.name)
            # 1. Valid customer test
            res_valid = client.post(f"/api/simulations/{session_id}/messages", json={"message": "details for customer 1006"})
            self.assertEqual(res_valid.status_code, 200)
            data_valid = res_valid.json()
            self.assertIn("events", data_valid)
            self.assertEqual(data_valid["hops"], 3)
            self.assertTrue(len(data_valid["response"]["data"]) >= 1)

            # 2. Invalid customer test
            res_invalid = client.post(f"/api/simulations/{session_id}/messages", json={"message": "details for customer 9999"})
            self.assertEqual(res_invalid.status_code, 200)
            data_invalid = res_invalid.json()
            self.assertEqual(data_invalid["response"]["data"], [])
            
            # Check rendered response event
            rendered_event = [e for e in data_invalid["events"] if e["event_type"] == "RESPONSE_RENDERED"][0]
            self.assertTrue(rendered_event["metadata"]["customerData"]["notFound"])
            self.assertEqual(rendered_event["action_description"], "Customer not found in synthetic database.")
        finally:
            routes.india_agent.client = saved_client

if __name__ == "__main__":
    unittest.main()

