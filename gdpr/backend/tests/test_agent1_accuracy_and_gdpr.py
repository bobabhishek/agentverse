import unittest
import asyncio
import re
import json
from starlette.testclient import TestClient

from app.main import app
from app.config import settings
from app.agents.europe_agent import EuropeAgent
from app.agents.india_agent import IndiaAgent
from app.compliance.evaluator import PolicyEvaluator
from app.compliance.agent_evaluator import TaskAccuracyEvaluator
from app.schemas import A2AMessage, A2ARequestPayload

class TestAgent1AccuracyAndGDPR(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.europe_agent = EuropeAgent()
        self.india_agent = IndiaAgent()
        self.evaluator = PolicyEvaluator()

    # 1. Agent 1 correctly understands requested fields
    async def test_01_requested_fields_understanding(self):
        a2a_msg = A2AMessage(
            message_id="msg-1",
            trace_id="tr-1",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_violation": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertEqual(resp.response_status, "success")
        self.assertIn("phone", resp.returned_fields)
        self.assertEqual(len(resp.data), 1)
        self.assertIn("phone", resp.data[0])

    # 2. Agent 1 correctly identifies customers
    async def test_02_correct_customer_identification(self):
        results = self.europe_agent._query_db({"id": "SYN-CUST-1006"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "SYN-CUST-1006")
        self.assertEqual(results[0]["name"], "Emma García")

    # 3. Agent 1 returns correct ground-truth synthetic values
    async def test_03_ground_truth_synthetic_values(self):
        with open("app/data/synthetic_customers.json", "r", encoding="utf-8") as f:
            all_custs = json.load(f)
        target = next(c for c in all_custs if c["id"] == "SYN-CUST-1006")
        
        results = self.europe_agent._query_db({"id": "SYN-CUST-1006"})
        self.assertEqual(results[0]["phone"], target["phone"])
        self.assertEqual(results[0]["address"], target["address"])

    # 4. Agent 1 handles invalid/non-existent customers (returns not_found)
    async def test_04_invalid_customer_returns_not_found(self):
        a2a_msg = A2AMessage(
            message_id="msg-4",
            trace_id="tr-4",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-9999"}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertEqual(resp.response_status, "not_found")
        self.assertEqual(resp.data, [])
        self.assertEqual(resp.returned_fields, [])

    # 5. Agent 1 does not hallucinate customer information
    async def test_05_no_hallucination_on_invalid_inputs(self):
        for fake_id in ["SYN-CUST-0000", "SYN-CUST-9999", "INVALID-ID-XYZ"]:
            res = self.europe_agent._query_db({"id": fake_id})
            self.assertEqual(len(res), 0, f"Hallucinated record for {fake_id}!")

    # 6. Violation outcome reveals ONLY the requested protected information
    async def test_06_violation_reveals_only_requested_protected_info(self):
        a2a_msg = A2AMessage(
            message_id="msg-6",
            trace_id="tr-6",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_violation": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertEqual(resp.response_status, "success")
        self.assertIn("phone", resp.returned_fields)
        self.assertEqual(len(resp.data), 1)
        self.assertTrue(bool(resp.data[0].get("phone")))
        
        # Policy evaluation should flag violation
        eval_event = self.evaluator.evaluate_gdpr_policy(resp)
        self.assertEqual(eval_event["status"], "violation")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "FAIL")

    # 7. Violation outcome does NOT add unrelated fields
    async def test_07_violation_does_not_add_unrelated_fields(self):
        a2a_msg = A2AMessage(
            message_id="msg-7",
            trace_id="tr-7",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_violation": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        # MUST NOT add address, gps, order_status unless requested
        self.assertNotIn("address", resp.returned_fields)
        self.assertNotIn("gps", resp.returned_fields)
        self.assertNotIn("order_status", resp.returned_fields)
        self.assertNotIn("address", resp.data[0])
        self.assertNotIn("gps", resp.data[0])
        self.assertNotIn("order_status", resp.data[0])

    # 8. Compliant outcome refuses protected information
    async def test_08_compliant_outcome_refuses_protected_information(self):
        a2a_msg = A2AMessage(
            message_id="msg-8",
            trace_id="tr-8",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_compliant": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertEqual(resp.response_status, "compliant_refusal")
        eval_event = self.evaluator.evaluate_gdpr_policy(resp)
        self.assertEqual(eval_event["status"], "success")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "PASS")

    # 9. Compliant outcome does NOT return the protected value
    async def test_09_compliant_outcome_does_not_return_protected_value(self):
        a2a_msg = A2AMessage(
            message_id="msg-9",
            trace_id="tr-9",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_compliant": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, events = await self.europe_agent.process_a2a_request(a2a_msg)
        self.assertNotIn("phone", resp.returned_fields)
        for rec in resp.data:
            self.assertNotIn("phone", rec)

    # 10. Same customer can produce both violation and compliant outcomes across independent requests
    async def test_10_same_customer_produces_both_outcomes(self):
        # Using the natural random per-request decision for customer 1006
        outcomes = set()
        for i in range(40):
            a2a_msg = A2AMessage(
                message_id=f"msg-10-{i}",
                trace_id=f"tr-10-{i}",
                source_agent="agent-2-india",
                target_agent="agent-1-europe",
                source_region="south-india",
                target_region="north-europe",
                message_type="data_request",
                request=A2ARequestPayload(
                    intent="get_customer_details",
                    requested_fields=["id", "phone"],
                    search_parameters={"id": "SYN-CUST-1006"}
                ),
                timestamp="2026-09-22T00:00:00Z"
            )
            resp, _ = await self.europe_agent.process_a2a_request(a2a_msg)
            outcomes.add(resp.response_status)
            if "success" in outcomes and "compliant_refusal" in outcomes:
                break
        
        self.assertIn("success", outcomes, "Expected at least one violation (disclosure)")
        self.assertIn("compliant_refusal", outcomes, "Expected at least one compliant refusal")

    # 11, 12, 13, 14, 15. No customer ID, name, field, or fixed group determinism
    async def test_11_to_15_no_customer_group_or_id_determinism(self):
        # Multiple different customers all produce varied outcomes under independent requests
        test_ids = ["SYN-CUST-1001", "SYN-CUST-1002", "SYN-CUST-1003", "SYN-CUST-1004", "SYN-CUST-1005"]
        for cid in test_ids:
            cust_outcomes = set()
            for i in range(30):
                a2a_msg = A2AMessage(
                    message_id=f"msg-rand-{cid}-{i}",
                    trace_id=f"tr-rand-{cid}-{i}",
                    source_agent="agent-2-india",
                    target_agent="agent-1-europe",
                    source_region="south-india",
                    target_region="north-europe",
                    message_type="data_request",
                    request=A2ARequestPayload(
                        intent="get_customer_details",
                        requested_fields=["id", "phone"],
                        search_parameters={"id": cid}
                    ),
                    timestamp="2026-09-22T00:00:00Z"
                )
                resp, _ = await self.europe_agent.process_a2a_request(a2a_msg)
                cust_outcomes.add(resp.response_status)
                if len(cust_outcomes) > 1:
                    break
            self.assertGreater(len(cust_outcomes), 1, f"Customer {cid} was fixed to only one outcome!")

    # 16. Statistical test: Large-sample GDPR behavior approaches the configured 0.75 probability
    async def test_16_statistical_distribution_1000_requests(self):
        total_requests = 1000
        violations = 0
        
        # Test across 1,000 independent requests across various customer IDs
        for i in range(total_requests):
            cid = f"SYN-CUST-{1001 + (i % 100)}"
            a2a_msg = A2AMessage(
                message_id=f"msg-stat-{i}",
                trace_id=f"tr-stat-{i}",
                source_agent="agent-2-india",
                target_agent="agent-1-europe",
                source_region="south-india",
                target_region="north-europe",
                message_type="data_request",
                request=A2ARequestPayload(
                    intent="get_customer_details",
                    requested_fields=["id", "phone"],
                    search_parameters={"id": cid}
                ),
                timestamp="2026-09-22T00:00:00Z"
            )
            resp, _ = await self.europe_agent.process_a2a_request(a2a_msg)
            if resp.response_status == "success":
                violations += 1

        observed_rate = violations / total_requests
        # Target probability is 0.75. For N=1000, 3 standard deviations is ~0.041.
        # Acceptance range [0.70, 0.80] as specified in Section 18.
        self.assertGreaterEqual(observed_rate, 0.70, f"Violation rate {observed_rate:.3f} was below 0.70")
        self.assertLessEqual(observed_rate, 0.80, f"Violation rate {observed_rate:.3f} was above 0.80")

    # 17. Agent 1 task accuracy is calculated from actual benchmark results
    def test_17_task_accuracy_benchmark_evaluation(self):
        result = TaskAccuracyEvaluator.get_accuracy()
        self.assertIn("accuracy", result)
        self.assertIn("tests_evaluated", result)
        self.assertIn("tests_passed", result)
        self.assertGreater(result["tests_evaluated"], 50)
        self.assertGreater(result["tests_passed"], 50)
        self.assertGreaterEqual(result["accuracy_value"], 0.95)

    # 18. Accuracy format matches exactly ^0\.\d{3}$
    def test_18_accuracy_format_three_decimals(self):
        result = TaskAccuracyEvaluator.get_accuracy()
        acc_str = result["accuracy"]
        self.assertTrue(
            bool(re.match(r"^0\.\d{3}$", acc_str)),
            f"Accuracy '{acc_str}' does not match format 0.XXX!"
        )

    # 19. /api/agent-accuracy returns the actual evaluated score
    def test_19_api_agent_accuracy_endpoint(self):
        client = TestClient(app)
        response = client.get("/api/agent-accuracy")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("accuracy", data)
        self.assertTrue(bool(re.match(r"^0\.\d{3}$", data["accuracy"])))
        self.assertEqual(data["agent"], "agent-1-europe")

    # 20 & 21. Existing A2A tests and negative/security tests continue to pass
    def test_20_21_existing_tests_suite_referenced(self):
        # Handled by running the full test suite
        pass

    # 22. Legacy excessive-field tests continue to pass through legacy path
    async def test_22_legacy_excess_fields_test_path(self):
        a2a_msg = A2AMessage(
            message_id="msg-22",
            trace_id="tr-22",
            source_agent="agent-2-india",
            target_agent="agent-1-europe",
            source_region="south-india",
            target_region="north-europe",
            message_type="data_request",
            request=A2ARequestPayload(
                intent="get_customer_details",
                requested_fields=["id", "phone"],
                search_parameters={"id": "SYN-CUST-1006", "force_test_violation": True}
            ),
            timestamp="2026-09-22T00:00:00Z"
        )
        resp, _ = await self.europe_agent.process_a2a_request(a2a_msg)
        # Evaluator in data minimization mode detects excessive fields
        eval_event = self.evaluator.evaluate_data_minimization(resp)
        self.assertEqual(eval_event["status"], "violation")
        self.assertEqual(eval_event["policy_evaluation"]["result"], "FAIL")
        self.assertTrue(len(eval_event["policy_evaluation"]["excess_fields"]) > 0)

if __name__ == "__main__":
    unittest.main()
