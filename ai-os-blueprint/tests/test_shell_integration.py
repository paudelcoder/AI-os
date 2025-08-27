import unittest
from unittest.mock import Mock, patch
import json
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all the core services
from system.core.policy_engine import PolicyEngine
from system.core.memory_graph import MemoryGraph
from system.core.agent_broker import AgentBroker
from system.core.planner import Planner
from system.core.vault_service import VaultService
from experience.card_renderer import CardRenderer

class TestShellIntegration(unittest.TestCase):
    """
    An integration test for the full AI OS pipeline, from user intent to
    a final rendered UI card. This test uses real service instances, mocking
    only the external agent communication.
    """

    def setUp(self):
        """Set up the full stack of services for the integration test."""
        # 1. Create a permissive policy for testing purposes
        policy_doc = {
            "policies": [{
                "policy_id": "allow-all-for-test",
                "effect": "allow",
                "actions": ["*"],
                "conditions": None
            }]
        }

        # 2. Create manifests for our mock agents
        self.rides_manifest = {
            "service": "Rides", "version": "1.0.0",
            "capabilities": [{"name": "request_ride", "output_schema": {"display_hint": "ride_confirmation"}}]
        }
        self.payments_manifest = {
            "service": "Payments", "version": "1.0.0",
            "capabilities": [{"name": "make_payment", "output_schema": {"display_hint": "payment_confirmation"}}]
        }

        # 3. Instantiate all services with real implementations
        self.mock_audit = Mock()
        self.memory_graph = MemoryGraph()
        self.policy_engine = PolicyEngine(policy_doc, self.mock_audit)
        self.agent_broker = AgentBroker(self.mock_audit)
        self.card_renderer = CardRenderer()
        self.vault_service = VaultService() # New service

        # 4. Register agents
        self.agent_broker.register_agent(self.rides_manifest, "http://fake-rides-agent:5002")
        self.agent_broker.register_agent(self.payments_manifest, "http://fake-payments-agent:5003")

        # 5. The Planner ties all services together
        self.planner = Planner(
            self.memory_graph,
            self.policy_engine,
            self.agent_broker,
            self.mock_audit
        )

    @patch('system.core.agent_broker.AgentBroker.execute_call')
    def test_full_flow_for_ride_request(self, mock_execute_call):
        """
        Tests the complete end-to-end flow for a user command.
        """
        # 1. Define the user's intent
        intent = {"user_utterance": "get me a ride to the airport"}

        # 2. Mock the response from the external agent service
        mock_agent_response = {
            "ride_id": "ride_integ_test_123",
            "driver_name": "Test Driver",
            "eta_minutes": 8,
            "price_estimate": 25.50
        }
        mock_execute_call.return_value = mock_agent_response

        # 3. Run the core OS logic: create a plan and execute it
        plan = self.planner.create_plan(intent)
        execution_result = self.planner.execute_plan(plan)

        # Assert that the execution part was successful
        self.assertEqual(execution_result["status"], "success")
        self.assertEqual(execution_result["result"], mock_agent_response)
        mock_execute_call.assert_called_once_with(plan["calls"][0])

        # 4. Render the successful result into a UI card
        output_schema = self.rides_manifest["capabilities"][0]["output_schema"]
        final_card = self.card_renderer.render(execution_result["result"], output_schema)

        # 5. Assert that the final UI card is rendered correctly
        self.assertEqual(final_card["title"], "Your Ride is Confirmed")
        self.assertEqual(final_card["subtitle"], "Driver: Test Driver")
        self.assertIn("8 minutes", final_card["components"][0]["value"])
        self.assertIn("$25.50", final_card["components"][1]["value"])

    @patch('system.core.agent_broker.AgentBroker.execute_call')
    def test_full_flow_for_payment(self, mock_execute_call):
        """Tests the complete end-to-end flow for a payment command."""
        # 1. Store a secret in the vault (as the user would have done previously)
        # Note: In a real flow, the planner wouldn't need to know the token key,
        # but for this test, we use it to confirm the right one was chosen.
        self.vault_service.store_secret(
            "payment_token_amex_1005",
            "real-token-data-would-go-here",
            principal={"type": "user"}
        )

        # 2. Define user intent
        intent = {"user_utterance": "pay $19.99 to Netflix"}

        # 3. Mock the agent's response
        mock_agent_response = {
            "transaction_id": "txn_integ_test_456",
            "status": "approved",
            "amount_paid": 19.99,
            "merchant_name": "Netflix"
        }
        mock_execute_call.return_value = mock_agent_response

        # 4. Run the core OS logic
        plan = self.planner.create_plan(intent)
        execution_result = self.planner.execute_plan(plan)

        # Assert execution success
        self.assertEqual(execution_result["status"], "success")

        # 5. Render the result
        output_schema = self.payments_manifest["capabilities"][0]["output_schema"]
        final_card = self.card_renderer.render(execution_result["result"], output_schema)

        # 6. Assert the final UI card is correct
        self.assertEqual(final_card["title"], "Payment Successful") # Assuming renderer is updated for this
        self.assertIn("$19.99", final_card["components"][0]["value"])
        self.assertIn("Netflix", final_card["components"][1]["value"])

if __name__ == '__main__':
    unittest.main()
