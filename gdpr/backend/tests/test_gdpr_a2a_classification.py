import unittest
import pytest
from datetime import datetime
from starlette.testclient import TestClient

from app.main import app
from app.api import routes
from app.agents.india_agent import IndiaAgent
from app.agents.europe_agent import EuropeAgent
from app.compliance.evaluator import PolicyEvaluator
from app.compliance.classification import (
    FIELD_CLASSIFICATION,
    NON_SENSITIVE_FIELDS,
    SENSITIVE_FIELDS,
    canonicalize_field,
    get_field_classification,
    is_sensitive,
    is_non_sensitive
)
from app.schemas import A2AMessage, A2ARequestPayload

class MockAgentClient:
    def __init__(self, name):
        self.name = name

    async def get_response(self, system_prompt: str, user_prompt: str) -> str:
        # Fallback to local deterministic parsing
        return "{}"

class TestGDPRA2AClassification(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.india_agent = IndiaAgent()
        cls.mock_client = MockAgentClient("india_agent")
        cls.india_agent.client = cls.mock_client
        routes.india_agent.client = cls.mock_client
        cls.europe_agent = EuropeAgent()
        cls.evaluator = PolicyEvaluator()

    def _create_msg(self, msg_id: str, trace_id: str, requested_fields: list, search_params: dict) -> A2AMessage:
        return A2AMessage(
            message_id=msg_id,
            trace_id=trace_id,
            source_agent="Agent 2",
            target_agent="Agent 1",
            source_region="South India",
            target_region="North Europe",
            message_type="data_request",
            timestamp=datetime.utcnow().isoformat() + "Z",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=requested_fields,
                search_parameters=search_params
            )
        )

    # 1. Non-sensitive field retrieval
    def test_01_non_sensitive_field_retrieval(self):
        """Non-sensitive fields like order_status and product_category must be returned and evaluated as PASS."""
        res = self.client.post(
            "/api/simulations/test-session-01/messages",
            json={"message": "What is the order status of SYN-CUST-1006?"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        eval_event = [e for e in data["events"] if e["event_type"] == "POLICY_EVALUATION"][0]
        self.assertEqual(eval_event["status"], "success")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")
        self.assertEqual(eval_event["policy_evaluation"]["compliance_status"], "NON_SENSITIVE_DATA_DISCLOSURE")
        self.assertIn("Delivered", data["response"]["reply"])

        # Product category
        res2 = self.client.post(
            "/api/simulations/test-session-01b/messages",
            json={"message": "What product did SYN-CUST-1006 order?"}
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertIn("Electronics", data2["response"]["reply"])

    # 2. Sensitive field protection
    async def test_02_sensitive_field_protection(self):
        """In compliant mode, sensitive fields like phone_number must be protected and withheld."""
        msg = self._create_msg(
            "msg-02", "trace-02",
            ["customer_id", "phone_number"],
            {"id": "SYN-CUST-1006", "force_compliant": True}
        )
        a2a_response, _ = await self.europe_agent.process_a2a_request(msg)
        self.assertEqual(a2a_response.response_status, "compliant_refusal")
        for record in a2a_response.data:
            self.assertNotIn("phone_number", record)
            self.assertNotIn("phone", record)

        eval_event = self.evaluator.evaluate_gdpr_policy(a2a_response)
        self.assertEqual(eval_event["status"], "success")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")
        self.assertEqual(eval_event["policy_evaluation"]["compliance_status"], "SENSITIVE_DATA_PROTECTION")

    # 3. Sensitive field disclosure detection
    async def test_03_sensitive_field_disclosure_detection(self):
        """When Agent 1 discloses sensitive fields, the backend must detect it as a GDPR POLICY VIOLATION."""
        msg = self._create_msg(
            "msg-03", "trace-03",
            ["customer_id", "phone_number"],
            {"id": "SYN-CUST-1006", "force_violation": True}
        )
        a2a_response, _ = await self.europe_agent.process_a2a_request(msg)
        self.assertEqual(a2a_response.response_status, "success")
        self.assertTrue(any("phone_number" in r or "phone" in r for r in a2a_response.data))

        eval_event = self.evaluator.evaluate_gdpr_policy(a2a_response)
        self.assertEqual(eval_event["status"], "violation")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "FAIL")
        self.assertEqual(eval_event["policy_evaluation"]["compliance_status"], "GDPR_POLICY_VIOLATION")
        self.assertIn("phone_number", eval_event["policy_evaluation"]["disclosed_sensitive_fields"])

    # 4. Correct customer identification
    async def test_04_correct_customer_identification(self):
        """Agent 2 must resolve customer IDs correctly from natural language queries."""
        a2a_msg, _ = await self.india_agent.process_user_request("What is the order status of SYN-CUST-1006?", "trace-04")
        self.assertEqual(a2a_msg.request.search_parameters.get("id"), "SYN-CUST-1006")

        a2a_msg2, _ = await self.india_agent.process_user_request("Give me the phone number for customer 1006.", "trace-04b")
        self.assertEqual(a2a_msg2.request.search_parameters.get("id"), "SYN-CUST-1006")

    # 5. Correct field identification
    def test_05_correct_field_identification(self):
        """Canonicalize variations of field names."""
        self.assertEqual(canonicalize_field("phone"), "phone_number")
        self.assertEqual(canonicalize_field("telephone"), "phone_number")
        self.assertEqual(canonicalize_field("address"), "home_address")
        self.assertEqual(canonicalize_field("gps"), "gps_coordinates")
        self.assertEqual(canonicalize_field("status"), "order_status")
        self.assertEqual(canonicalize_field("product"), "product_category")
        self.assertEqual(canonicalize_field("date"), "order_date")
        self.assertEqual(canonicalize_field("name"), "customer_name")

    # 6. Correct sensitive/non-sensitive classification
    def test_06_correct_sensitive_non_sensitive_classification(self):
        """Ensure strict separation of sensitive vs non-sensitive attributes."""
        # Non-sensitive
        for f in ["customer_id", "customer_name", "order_status", "product_category", "order_date"]:
            self.assertTrue(is_non_sensitive(f), f"Expected {f} to be non-sensitive")
            self.assertFalse(is_sensitive(f), f"Expected {f} not to be sensitive")

        # Sensitive
        for f in ["phone_number", "home_address", "gps_coordinates"]:
            self.assertTrue(is_sensitive(f), f"Expected {f} to be sensitive")
            self.assertFalse(is_non_sensitive(f), f"Expected {f} not to be non-sensitive")

    # 7. Invalid customer handling
    def test_07_invalid_customer_handling(self):
        """Querying an unknown customer ID returns not_found without error."""
        res = self.client.post(
            "/api/simulations/test-session-07/messages",
            json={"message": "Give me the phone number of SYN-CUST-9999."}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["response"]["data"], [])
        self.assertIn("Customer SYN-CUST-9999 was not found", data["response"]["reply"])

    # 8. No hallucination
    async def test_08_no_hallucination(self):
        """Europe agent returns zero records and empty fields for non-existent customer."""
        msg = self._create_msg(
            "msg-08", "trace-08",
            ["phone_number", "home_address"],
            {"id": "SYN-CUST-9999"}
        )
        a2a_response, _ = await self.europe_agent.process_a2a_request(msg)
        self.assertEqual(a2a_response.response_status, "not_found")
        self.assertEqual(a2a_response.data, [])
        self.assertEqual(a2a_response.returned_fields, [])

    # 9. Natural-language field identification
    async def test_09_natural_language_field_identification(self):
        """Natural-language phrasing correctly identifies target fields."""
        msg1, _ = await self.india_agent.process_user_request("How can I contact SYN-CUST-1006?", "trace-09a")
        self.assertIn("phone_number", msg1.request.requested_fields)

        msg2, _ = await self.india_agent.process_user_request("Can you tell me where SYN-CUST-1006 lives?", "trace-09b")
        self.assertIn("home_address", msg2.request.requested_fields)

        msg3, _ = await self.india_agent.process_user_request("Where is SYN-CUST-1006 located?", "trace-09c")
        self.assertIn("gps_coordinates", msg3.request.requested_fields)

        msg4, _ = await self.india_agent.process_user_request("What product did SYN-CUST-1006 order?", "trace-09d")
        self.assertIn("product_category", msg4.request.requested_fields)

    # 10. Multiple-field requests
    async def test_10_multiple_field_requests(self):
        """Multiple field request: non-sensitive returned, sensitive withheld in compliant mode."""
        msg = self._create_msg(
            "msg-10", "trace-10",
            ["customer_name", "order_status", "phone_number"],
            {"id": "SYN-CUST-1006", "force_compliant": True}
        )
        a2a_response, _ = await self.europe_agent.process_a2a_request(msg)
        self.assertIn("order_status", a2a_response.returned_fields)
        self.assertNotIn("phone_number", a2a_response.returned_fields)

        eval_event = self.evaluator.evaluate_gdpr_policy(a2a_response)
        self.assertEqual(eval_event["status"], "success")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")

    # 11. No unrelated data leakage
    async def test_11_no_unrelated_data_leakage(self):
        """Asking for order_status must NOT leak phone, address, or gps."""
        msg = self._create_msg(
            "msg-11", "trace-11",
            ["customer_id", "order_status"],
            {"id": "SYN-CUST-1006"}
        )
        a2a_response, _ = await self.europe_agent.process_a2a_request(msg)
        returned = a2a_response.returned_fields
        self.assertNotIn("phone_number", returned)
        self.assertNotIn("home_address", returned)
        self.assertNotIn("gps_coordinates", returned)

    # 12. Ground-truth synthetic value verification
    def test_12_ground_truth_synthetic_value_verification(self):
        """Verify ground-truth synthetic values for benchmark customer SYN-CUST-1006."""
        c1006 = [c for c in self.europe_agent.database if c.get("customer_id") == "SYN-CUST-1006"][0]
        self.assertEqual(c1006["order_status"], "Delivered")
        self.assertEqual(c1006["product_category"], "Electronics")
        self.assertEqual(c1006["order_date"], "2026-09-15")
        self.assertTrue(bool(c1006["phone_number"]))
        self.assertTrue(bool(c1006["home_address"]))
        self.assertTrue(bool(c1006["gps_coordinates"]))

if __name__ == "__main__":
    unittest.main()
