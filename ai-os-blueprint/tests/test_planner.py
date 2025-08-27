import unittest
from unittest.mock import Mock

import sys
import os

# Add the project root directory to the Python path to allow imports from 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.core.planner import Planner
from system.core.policy_engine import Decision

class TestPlanner(unittest.TestCase):
    """Unit tests for the Planner service."""

    def setUp(self):
        """
        Set up mock MemoryGraph, PolicyEngine, and AgentBroker services.
        This isolates the Planner's logic for true unit testing.
        """
        self.mock_memory = Mock()
        self.mock_policy = Mock()
        self.mock_broker = Mock()
        self.mock_audit = Mock()
        self.planner = Planner(
            self.mock_memory,
            self.mock_policy,
            self.mock_broker,
            self.mock_audit
        )

    def test_plan_creation_success(self):
        """Test a successful plan creation with no special conditions."""
        # Configure mocks for this test case
        self.mock_memory.find_memories.return_value = []  # No preferences in memory
        self.mock_policy.evaluate_call.return_value = Decision.ALLOWED

        intent = {"user_utterance": "book a flight to NYC"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "executable")
        self.assertEqual(len(plan["calls"]), 1)
        self.assertEqual(plan["calls"][0]["call"], "Flights.search_flights")

        # Verify that the planner interacted with its dependencies as expected
        self.mock_memory.find_memories.assert_called_once()
        self.mock_policy.evaluate_call.assert_called_once()
        # Verify that the plan creation was logged
        self.mock_audit.log_action.assert_called_once()
        call_args = self.mock_audit.log_action.call_args[0]
        self.assertEqual(call_args[1], "planner.plan.create")
        self.assertEqual(call_args[2]["plan"], plan)

    def test_plan_with_memory_enrichment(self):
        """Test that the planner correctly uses a preference from the Memory Graph."""
        # Configure mocks to return a preferred airline
        preferred_airline_mem = [{"content": {"key": "airline", "value": "TestAir"}}]
        self.mock_memory.find_memories.return_value = preferred_airline_mem
        self.mock_policy.evaluate_call.return_value = Decision.ALLOWED

        intent = {"user_utterance": "book a flight"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "executable")
        self.assertEqual(plan["calls"][0]["parameters"]["airline"], "TestAir")

    def test_plan_rejected_by_policy(self):
        """Test that the plan is rejected if the Policy Engine returns DENIED."""
        # Configure mocks for this test case
        self.mock_memory.find_memories.return_value = []
        self.mock_policy.evaluate_call.return_value = Decision.DENIED

        intent = {"user_utterance": "book a flight"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "rejected")
        self.assertIn("denied by policy", plan["reason"])

    def test_plan_needs_confirmation(self):
        """Test that a plan is flagged for confirmation by the Policy Engine."""
        # Configure mocks for this test case
        self.mock_memory.find_memories.return_value = []
        self.mock_policy.evaluate_call.return_value = Decision.REQUIRES_CONFIRMATION

        intent = {"user_utterance": "book a flight"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "needs_confirmation")

    def test_unknown_intent_fails_gracefully(self):
        """Test that the planner returns a 'failed' status for an unknown intent."""
        intent = {"user_utterance": "what is the weather like today?"}
        plan = self.planner.create_plan(intent)
        self.assertEqual(plan["status"], "failed")
        self.assertIn("Could not understand intent", plan["reason"])

    def test_plan_creation_for_ride(self):
        """Test successful plan creation for a ride-hailing intent."""
        # Configure mocks for this specific test
        self.mock_memory.find_memories.return_value = []
        self.mock_policy.evaluate_call.return_value = Decision.ALLOWED

        intent = {"user_utterance": "Can you get me a ride to the main library?"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "executable")
        self.assertEqual(len(plan["calls"]), 1)

        ride_call = plan["calls"][0]
        self.assertEqual(ride_call["call"], "Rides.request_ride")
        self.assertEqual(ride_call["parameters"]["destination"], "the main library")

        # The policy engine should always be called to validate the plan.
        self.mock_policy.evaluate_call.assert_called_once()

    def test_execute_plan_success(self):
        """Test that an executable plan is correctly passed to the broker."""
        # The plan to be "executed"
        executable_plan = {
            "status": "executable",
            "calls": [{"call": "TestAgent.do_something", "parameters": {}}]
        }
        # Configure the mock broker to return a successful result
        self.mock_broker.execute_call.return_value = {"data": "success"}

        result = self.planner.execute_plan(executable_plan)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], {"data": "success"})
        self.mock_broker.execute_call.assert_called_once_with(executable_plan["calls"][0])

    def test_execute_plan_that_is_not_executable(self):
        """Test that a rejected plan is not executed."""
        rejected_plan = {"status": "rejected", "calls": []}

        result = self.planner.execute_plan(rejected_plan)

        self.assertEqual(result["status"], "execution_failed")
        self.assertIn("not executable", result["error"])
        # Ensure the broker was not called
        self.mock_broker.execute_call.assert_not_called()

    def test_execute_plan_handles_broker_failure(self):
        """Test that the planner handles exceptions from the broker."""
        executable_plan = {
            "status": "executable",
            "calls": [{"call": "TestAgent.do_something", "parameters": {}}]
        }
        # Configure the mock broker to raise an exception
        self.mock_broker.execute_call.side_effect = Exception("Agent not available")

        result = self.planner.execute_plan(executable_plan)

        self.assertEqual(result["status"], "execution_failed")
        self.assertEqual(result["error"], "Agent not available")

    def test_plan_creation_for_payment(self):
        """Test successful plan creation for a payment intent."""
        # Configure mocks
        self.mock_memory.find_memories.return_value = []
        self.mock_policy.evaluate_call.return_value = Decision.ALLOWED

        intent = {"user_utterance": "Pay $50.75 to the coffee shop"}
        plan = self.planner.create_plan(intent)

        self.assertEqual(plan["status"], "executable")
        self.assertEqual(len(plan["calls"]), 1)

        payment_call = plan["calls"][0]
        self.assertEqual(payment_call["call"], "Payments.make_payment")
        self.assertEqual(payment_call["parameters"]["amount"], 50.75)
        self.assertEqual(payment_call["parameters"]["merchant"], "the coffee shop")
        # Check that the hardcoded default token key is used
        self.assertEqual(payment_call["parameters"]["payment_token_key"], "payment_token_amex_1005")

        self.mock_policy.evaluate_call.assert_called_once()


if __name__ == '__main__':
    unittest.main()
