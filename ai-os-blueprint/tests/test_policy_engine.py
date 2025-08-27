import sys
import os
import unittest

# Add the project root directory to the Python path to allow imports from 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.policy_engine import PolicyEngine, Decision

class TestPolicyEngine(unittest.TestCase):
    """Unit tests for the PolicyEngine."""

    def setUp(self):
        """Set up a sample policy document and engine for use in tests."""
        policy_doc = {
          "version": "1.0",
          "policies": [
            {
              "policy_id": "deny-risky-payments",
              "effect": "deny",
              "actions": ["Payment.charge"],
              "conditions": {
                "any_key_numeric_greater_than": {
                  "keys": ["parameters.amount"],
                  "value": 500
                }
              }
            },
            {
              "policy_id": "confirm-contact-sharing",
              "effect": "require_confirmation",
              "actions": ["Contacts.share"],
              "conditions": None
            },
            {
              "policy_id": "allow-payments",
              "effect": "allow",
              "actions": ["Payment.charge"],
              "conditions": None
            },
            {
              "policy_id": "allow-calendar-read-wildcard",
              "effect": "allow",
              "actions": ["Calendar.read_*"],
              "conditions": None
            }
          ]
        }
        self.engine = PolicyEngine(policy_doc)

    def test_simple_allow(self):
        """Test a call that should be clearly allowed."""
        call = {"call": "Calendar.read_events"}
        self.assertEqual(self.engine.evaluate_call(call), Decision.ALLOWED)

    def test_default_deny_for_unspecified_action(self):
        """Test that an action not covered by any policy is denied."""
        call = {"call": "Photos.delete_all"}
        self.assertEqual(self.engine.evaluate_call(call), Decision.DENIED)

    def test_deny_precedence_over_allow(self):
        """Test that a DENY policy overrides an ALLOW policy for the same action."""
        call = {
            "call": "Payment.charge",
            "parameters": {"amount": 1000, "currency": "USD"}
        }
        self.assertEqual(self.engine.evaluate_call(call), Decision.DENIED)

    def test_allow_when_deny_condition_is_not_met(self):
        """Test that a call is allowed if it doesn't meet the DENY condition."""
        call = {
            "call": "Payment.charge",
            "parameters": {"amount": 100, "currency": "USD"}
        }
        self.assertEqual(self.engine.evaluate_call(call), Decision.ALLOWED)

    def test_require_confirmation(self):
        """Test a call that should require user confirmation."""
        call = {"call": "Contacts.share", "parameters": {"contact_id": "user-123"}}
        # This action is not explicitly allowed, so it should be denied even if confirmation is specified.
        # Let's update the policy in setUp to make this test more robust.
        # Add an allow policy for Contacts.share
        # No, the logic is Deny -> Allow/Confirm -> Default Deny.
        # The action "Contacts.share" is not in an "allow" policy, so it should be denied.
        # This is a good test for default deny.
        self.assertEqual(self.engine.evaluate_call(call), Decision.DENIED)

    def test_require_confirmation_when_also_allowed(self):
        """Test that confirmation is required even if the action is also allowed."""
        # Add a new policy to the engine for this specific test case
        self.engine.policies.append({
            "policy_id": "allow-contact-sharing",
            "effect": "allow",
            "actions": ["Contacts.share"],
            "conditions": None
        })
        call = {"call": "Contacts.share", "parameters": {"contact_id": "user-123"}}
        self.assertEqual(self.engine.evaluate_call(call), Decision.REQUIRES_CONFIRMATION)

    def test_action_wildcard_matching(self):
        """Test that an action matches a policy with a wildcard."""
        call = {"call": "Calendar.read_birthdays"}
        self.assertEqual(self.engine.evaluate_call(call), Decision.ALLOWED)

    def test_invalid_policy_document_initialization(self):
        """Test that the engine raises ValueError for a malformed document."""
        with self.assertRaises(ValueError):
            PolicyEngine({"invalid_structure": True})
        with self.assertRaises(ValueError):
            PolicyEngine("just a plain string")

    def test_deny_condition_not_met_if_param_is_missing(self):
        """Test that a deny condition isn't met if the relevant parameter is absent."""
        call = {
            "call": "Payment.charge",
            "parameters": {"currency": "USD"}  # 'amount' is missing
        }
        # The call matches the 'allow-payments' policy, and the 'deny' condition is not met.
        self.assertEqual(self.engine.evaluate_call(call), Decision.ALLOWED)

if __name__ == '__main__':
    unittest.main()
