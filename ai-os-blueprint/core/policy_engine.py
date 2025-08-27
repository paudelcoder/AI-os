import json
from enum import Enum
from fnmatch import fnmatch

class Decision(Enum):
    """Enumeration for policy decisions."""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"

class PolicyEngine:
    """
    A simple policy engine to evaluate capability calls against a set of policies.
    """
    def __init__(self, policy_document):
        """
        Initializes the engine with a policy document.
        :param policy_document: A dictionary representing the policy JSON.
        """
        if not isinstance(policy_document, dict) or "policies" not in policy_document:
            raise ValueError("Invalid policy document format")
        self.policies = policy_document.get("policies", [])

    def evaluate_call(self, capability_call):
        """
        Evaluates a capability call against the loaded policies.
        The evaluation order is: Deny -> Allow / Require Confirmation.
        Default is Deny.

        :param capability_call: A dictionary representing the capability call.
        :return: A Decision enum value.
        """
        # 1. Check for an explicit DENY. Deny policies take precedence.
        for policy in self.policies:
            if policy.get("effect") == "deny" and self._matches(policy, capability_call):
                return Decision.DENIED

        # 2. Check for ALLOW and REQUIRE_CONFIRMATION policies.
        # An action must be explicitly allowed to proceed.
        is_allowed = False
        requires_confirmation = False
        for policy in self.policies:
            if policy.get("effect") in ["allow", "require_confirmation"]:
                if self._matches(policy, capability_call):
                    if policy.get("effect") == "allow":
                        is_allowed = True
                    if policy.get("effect") == "require_confirmation":
                        requires_confirmation = True

        if is_allowed:
            if requires_confirmation:
                return Decision.REQUIRES_CONFIRMATION
            return Decision.ALLOWED

        # 3. Default to DENY if no allow policy matched.
        return Decision.DENIED

    def _matches(self, policy, capability_call):
        """Checks if a capability call matches a policy's action and conditions."""
        if not self._action_matches(capability_call.get("call"), policy.get("actions", [])):
            return False
        if not self._condition_matches(capability_call, policy.get("conditions")):
            return False
        return True

    def _action_matches(self, call_action, policy_actions):
        """Checks if the call's action matches any of the policy's action patterns."""
        if not call_action:
            return False
        for action_pattern in policy_actions:
            if fnmatch(call_action, action_pattern):
                return True
        return False

    def _get_nested_value(self, data, path):
        """Gets a value from a nested dict using a dot-separated path."""
        keys = path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data

    def _condition_matches(self, capability_call, conditions):
        """
        Checks if the capability call satisfies the policy's conditions.
        Currently only supports 'any_key_numeric_greater_than'.
        """
        if conditions is None:
            return True  # No conditions to meet.

        for condition_type, condition_data in conditions.items():
            if condition_type == "any_key_numeric_greater_than":
                limit = condition_data.get("value")
                keys_to_check = condition_data.get("keys", [])
                for key_path in keys_to_check:
                    value = self._get_nested_value(capability_call, key_path)
                    if value is not None and isinstance(value, (int, float)):
                        if value > limit:
                            return True  # Condition met.
                return False  # Condition not met after checking all keys.
            else:
                # For safety, unknown conditions result in a non-match.
                return False

        # An empty conditions block (e.g., "conditions": {}) means no constraints.
        return True
