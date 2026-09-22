import unittest
import ast
import json
import inspect
from unittest.mock import patch, MagicMock
from openai import AuthenticationError, NotFoundError, RateLimitError, APIConnectionError

from app.config import settings
from app.agents.agent_factory import get_agent_client, MockAgentClient, AgentClientWrapper
from app.agents.india_agent import IndiaAgent
from app.agents.europe_agent import EuropeAgent
from app.compliance.evaluator import PolicyEvaluator
from app.schemas import A2AMessage, A2ARequestPayload, A2AResponse

class TestNegativeAndSecurity(unittest.IsolatedAsyncioTestCase):

    # 1. Agent 1 key missing
    def test_01_agent1_key_missing_uses_mock(self):
        client = get_agent_client("agent-1-europe", "", "gpt-5.4mini")
        self.assertIsInstance(client, MockAgentClient)

    # 2. Agent 2 key missing
    def test_02_agent2_key_missing_uses_mock(self):
        client = get_agent_client("agent-2-india", "", "gpt-4o")
        self.assertIsInstance(client, MockAgentClient)

    # 3. Agent 1 invalid API key handling
    async def test_03_agent1_invalid_key_auth_error(self):
        wrapper = get_agent_client("agent-1-europe", "invalid-key-xyz", "gpt-5.4mini")
        self.assertIsInstance(wrapper, AgentClientWrapper)
        with self.assertRaises(AuthenticationError):
            await wrapper.get_response("sys", "user")

    # 4. Agent 2 invalid API key handling
    async def test_04_agent2_invalid_key_auth_error(self):
        wrapper = get_agent_client("agent-2-india", "invalid-key-xyz", "gpt-4o")
        self.assertIsInstance(wrapper, AgentClientWrapper)
        with self.assertRaises(AuthenticationError):
            await wrapper.get_response("sys", "user")

    # 5. Agent 1 and Agent 2 configured with different keys
    def test_05_separate_keys_no_crossover(self):
        client1 = get_agent_client("agent-1-europe", "key-agent-1", "gpt-5.4mini")
        client2 = get_agent_client("agent-2-india", "key-agent-2", "gpt-4o")
        self.assertEqual(client1.client.api_key, "key-agent-1")
        self.assertEqual(client2.client.api_key, "key-agent-2")
        self.assertNotEqual(client1.client.api_key, client2.client.api_key)

    # 6. No shared API key fallback
    def test_06_no_shared_api_key_fallback(self):
        # Even if OPENAI_API_KEY environment variable exists in os.environ,
        # get_agent_client must strictly use the agent-specific key passed to it.
        with patch.dict("os.environ", {"OPENAI_API_KEY": "shared-fallback-key"}):
            client = get_agent_client("agent-2-india", "", "gpt-4o")
            self.assertIsInstance(client, MockAgentClient)

    # 7. India Agent direct database access attempt
    def test_07_india_agent_no_database_attribute(self):
        india = IndiaAgent()
        self.assertFalse(hasattr(india, "database"))
        self.assertFalse(hasattr(india, "synthetic_data"))
        self.assertFalse(hasattr(india, "_load_data"))

    # 8. India Agent synthetic JSON access attempt (AST source inspection)
    def test_08_india_agent_source_ast_no_file_or_data_access(self):
        source = inspect.getsource(IndiaAgent)
        tree = ast.parse(source)

        # Check no call to 'open'
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    self.fail("IndiaAgent contains direct 'open()' file call!")
        
        # Check no mention of synthetic_customers or SYNTHETIC_DATA_PATH
        self.assertNotIn("synthetic_customers.json", source)
        self.assertNotIn("SYNTHETIC_DATA_PATH", source)

    # 9. Europe Agent valid customer lookup
    def test_09_europe_agent_valid_customer_lookup(self):
        europe = EuropeAgent()
        results = europe._query_db({"id": "SYN-CUST-1006"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "SYN-CUST-1006")

    # 10. Europe Agent invalid customer lookup
    def test_10_europe_agent_invalid_customer_lookup(self):
        europe = EuropeAgent()
        results = europe._query_db({"id": "SYN-CUST-9999"})
        self.assertEqual(len(results), 0)

    # 11. Requested fields equal returned fields
    def test_11_requested_equal_returned_passes(self):
        resp = A2AResponse(
            message_id="msg-1",
            trace_id="tr-1",
            source_agent="agent-1-europe",
            target_agent="agent-2-india",
            response_status="success",
            requested_fields=["id", "phone"],
            returned_fields=["id", "phone"],
            data=[{"id": "SYN-CUST-1006", "phone": "+49-123"}],
            timestamp="2026-09-21T00:00:00Z"
        )
        eval_result = PolicyEvaluator.evaluate_data_minimization(resp)
        self.assertEqual(eval_result["policy_evaluation"]["result"], "PASS")
        self.assertEqual(eval_result["policy_evaluation"]["excess_fields"], [])

    # 12. Returned fields contain excessive fields
    def test_12_excessive_returned_fields_fails(self):
        resp = A2AResponse(
            message_id="msg-2",
            trace_id="tr-2",
            source_agent="agent-1-europe",
            target_agent="agent-2-india",
            response_status="success",
            requested_fields=["id", "phone"],
            returned_fields=["id", "phone", "address", "gps"],
            data=[{"id": "SYN-CUST-1006", "phone": "+49-123", "address": "Berlin", "gps": "52.5, 13.4"}],
            timestamp="2026-09-21T00:00:00Z"
        )
        eval_result = PolicyEvaluator.evaluate_data_minimization(resp)
        self.assertEqual(eval_result["policy_evaluation"]["result"], "FAIL")
        self.assertEqual(eval_result["policy_evaluation"]["excess_fields"], ["address", "gps"])

    # 13. Empty requested fields
    def test_13_empty_requested_fields_with_data_fails(self):
        resp = A2AResponse(
            message_id="msg-3",
            trace_id="tr-3",
            source_agent="agent-1-europe",
            target_agent="agent-2-india",
            response_status="success",
            requested_fields=[],
            returned_fields=["phone", "address"],
            data=[{"phone": "+49-123", "address": "Berlin"}],
            timestamp="2026-09-21T00:00:00Z"
        )
        eval_result = PolicyEvaluator.evaluate_data_minimization(resp)
        self.assertEqual(eval_result["policy_evaluation"]["result"], "FAIL")
        self.assertEqual(sorted(eval_result["policy_evaluation"]["excess_fields"]), ["address", "phone"])

    # 14. Missing customer record (empty returned data)
    def test_14_missing_customer_record_no_false_violation(self):
        resp = A2AResponse(
            message_id="msg-4",
            trace_id="tr-4",
            source_agent="agent-1-europe",
            target_agent="agent-2-india",
            response_status="not_found",
            requested_fields=["id", "phone"],
            returned_fields=[],
            data=[],
            timestamp="2026-09-21T00:00:00Z"
        )
        eval_result = PolicyEvaluator.evaluate_data_minimization(resp)
        self.assertEqual(eval_result["policy_evaluation"]["result"], "PASS")
        self.assertEqual(eval_result["policy_evaluation"]["excess_fields"], [])

    # 15. OpenAI model unavailable error handling
    async def test_15_model_unavailable_error(self):
        wrapper = AgentClientWrapper(client=MagicMock(), model="non-existent-model")
        wrapper.client.chat.completions.create = MagicMock(
            side_effect=NotFoundError("The model `non-existent-model` does not exist", response=MagicMock(), body=None)
        )
        with self.assertRaises(NotFoundError):
            await wrapper.get_response("sys", "user")

    # 16. OpenAI quota or rate-limit error handling
    async def test_16_quota_or_rate_limit_error(self):
        wrapper = AgentClientWrapper(client=MagicMock(), model="gpt-4o")
        wrapper.client.chat.completions.create = MagicMock(
            side_effect=RateLimitError("Rate limit reached", response=MagicMock(), body=None)
        )
        with self.assertRaises(RateLimitError):
            await wrapper.get_response("sys", "user")

    # 17. Network/API connection error handling
    async def test_17_network_connection_error(self):
        wrapper = AgentClientWrapper(client=MagicMock(), model="gpt-4o")
        wrapper.client.chat.completions.create = MagicMock(
            side_effect=APIConnectionError(request=MagicMock())
        )
        with self.assertRaises(APIConnectionError):
            await wrapper.get_response("sys", "user")

    # 18. Mock mode produces valid JSON schema
    async def test_18_mock_mode_produces_valid_json(self):
        mock_client = MockAgentClient("agent-2-india")
        res = await mock_client.get_response("sys", "Get phone for customer 1006")
        parsed = json.loads(res)
        self.assertIn("intent", parsed)
        self.assertIn("requested_fields", parsed)
        self.assertIn("search_parameters", parsed)
        self.assertEqual(parsed["search_parameters"]["id"], "SYN-CUST-1006")

    # 19. Real mode with key config
    def test_19_real_mode_instantiates_wrapper(self):
        client = get_agent_client("agent-2-india", "test-key-mocked", "gpt-4o")
        self.assertIsInstance(client, AgentClientWrapper)
        self.assertEqual(client.model, "gpt-4o")

    # 20. Secret masking in logs and test output
    def test_20_secret_masking(self):
        from tests.verify_live_integration import mask_status, sanitize_error
        fake_secret = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
        status = mask_status(fake_secret)
        self.assertNotIn(fake_secret, status)
        self.assertEqual(status, "CONFIGURED")
        self.assertNotIn(str(len(fake_secret)), status)

        empty_status = mask_status("")
        self.assertEqual(empty_status, "NOT CONFIGURED")

        sanitized = sanitize_error(Exception(f"Error with key {fake_secret} failed"))
        self.assertNotIn(fake_secret, sanitized)
        self.assertIn("[REDACTED]", sanitized)

if __name__ == "__main__":
    unittest.main()
