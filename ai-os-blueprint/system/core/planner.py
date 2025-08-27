import re
from .policy_engine import Decision

class Planner:
    """
    A simple, rule-based planner that creates execution plans from user intents.

    This MVP planner uses basic keyword matching to understand intents and
    integrates with the MemoryGraph and PolicyEngine to create context-aware
    and secure plans.
    """

    def __init__(self, memory_graph, policy_engine, agent_broker, audit_log_service):
        """
        Initializes the Planner with its dependent services.

        :param memory_graph: An instance of MemoryGraph.
        :param policy_engine: An instance of PolicyEngine.
        :param agent_broker: An instance of AgentBroker.
        :param audit_log_service: An instance of AuditLogService.
        """
        self.memory = memory_graph
        self.policy = policy_engine
        self.broker = agent_broker
        self.audit = audit_log_service
        # The Planner itself is a principal when accessing services like memory.
        self.principal = {"type": "os_service", "id": "Planner"}

    def create_plan(self, intent):
        """
        Generates a plan of capability calls based on a user intent.

        :param intent: A dictionary representing the user's intent.
        :return: A dictionary representing the plan, including its status
                 (e.g., 'executable', 'needs_confirmation', 'rejected') and
                 the list of capability calls.
        """
        utterance = intent.get("user_utterance", "").lower()

        # Simple, keyword-based routing to different planning functions.
        plan = None
        if "flight" in utterance and ("book" in utterance or "find" in utterance):
            plan = self._plan_book_flight(intent)

        elif "ride" in utterance or "taxi" in utterance:
            plan = self._plan_request_ride(intent)

        elif "pay" in utterance or "payment" in utterance:
            plan = self._plan_make_payment(intent)

        else:
            plan = {"status": "failed", "reason": "Could not understand intent", "calls": []}

        # Log the final plan before returning it.
        self.audit.log_action(
            principal=self.principal,
            action="planner.plan.create",
            details={"intent": intent, "plan": plan}
        )
        return plan

    def _plan_book_flight(self, intent):
        """
        Generates a plan to find and book a flight.
        This MVP only generates the first step: searching for flights.
        """
        # 1. Enrich with Memory: Find user's preferred airline.
        airline_preferences = self.memory.find_memories(
            self.principal,
            memory_type="preference"
        )
        preferred_airline = None
        for pref in airline_preferences:
            if pref.get("content", {}).get("key") == "airline":
                preferred_airline = pref["content"]["value"]
                break

        # 2. Generate Candidate Call(s)
        # A real system would use NLP to extract "NYC" from the utterance.
        # For this MVP, we'll assume the destination is known or hardcoded.
        destination = "NYC"
        search_call = {
            "call": "Flights.search_flights",
            "parameters": {"to": destination}
        }
        if preferred_airline:
            search_call["parameters"]["airline"] = preferred_airline

        plan_calls = [search_call]

        # 3. Validate with Policy Engine
        plan_status = "executable"
        for call in plan_calls:
            decision = self.policy.evaluate_call(call)
            if decision == Decision.DENIED:
                return {
                    "status": "rejected",
                    "reason": f"Action '{call['call']}' is denied by policy.",
                    "calls": plan_calls
                }
            if decision == Decision.REQUIRES_CONFIRMATION:
                plan_status = "needs_confirmation"

        # 4. Return the final, validated plan
        return {"status": plan_status, "calls": plan_calls}

    def _plan_request_ride(self, intent):
        """Generates a plan to request a ride."""
        utterance = intent.get("user_utterance", "").lower()

        # MVP entity extraction: find the destination, defaults to 'unknown'
        destination = "unknown"
        if " to " in utterance:
            # Takes everything after the first " to " as the destination
            destination = utterance.split(" to ", 1)[1]

        # Generate the capability call
        ride_call = {
            "call": "Rides.request_ride",
            "parameters": {"destination": destination}
        }
        plan_calls = [ride_call]

        # Validate with Policy Engine
        plan_status = "executable"
        for call in plan_calls:
            decision = self.policy.evaluate_call(call)
            if decision == Decision.DENIED:
                return {
                    "status": "rejected",
                    "reason": f"Action '{call['call']}' is denied by policy.",
                    "calls": plan_calls
                }
            if decision == Decision.REQUIRES_CONFIRMATION:
                plan_status = "needs_confirmation"

        return {"status": plan_status, "calls": plan_calls}

    def _plan_make_payment(self, intent):
        """Generates a plan to make a payment."""
        utterance = intent.get("user_utterance", "").lower()

        # MVP entity extraction for amount and merchant
        amount_match = re.search(r'\$?(\d+\.?\d*)', utterance)
        amount = float(amount_match.group(1)) if amount_match else 0.0

        merchant = "unknown"
        if " to " in utterance:
            merchant = utterance.split(" to ", 1)[1]

        # MVP: Assume a default payment token. A real system would have logic
        # to select from multiple user payment methods stored in the vault.
        payment_token_key = "payment_token_amex_1005"

        # Generate the capability call
        payment_call = {
            "call": "Payments.make_payment",
            "parameters": {
                "amount": amount,
                "currency": "USD",
                "merchant": merchant,
                "payment_token_key": payment_token_key
            }
        }
        plan_calls = [payment_call]

        # Validate with Policy Engine
        plan_status = "executable"
        for call in plan_calls:
            decision = self.policy.evaluate_call(call)
            if decision == Decision.DENIED:
                return {
                    "status": "rejected",
                    "reason": f"Action '{call['call']}' is denied by policy.",
                    "calls": plan_calls
                }
            if decision == Decision.REQUIRES_CONFIRMATION:
                plan_status = "needs_confirmation"

        return {"status": plan_status, "calls": plan_calls}

    def execute_plan(self, plan):
        """
        Executes a given plan using the AgentBroker.
        For this MVP, it only executes the first call in the plan.

        :param plan: A plan object returned by create_plan.
        :return: The result from the agent call, or an error object.
        """
        if plan.get("status") not in ["executable", "needs_confirmation"]:
            return {"status": "execution_failed", "error": f"Plan is not executable. Status: {plan.get('status')}"}

        if not plan.get("calls"):
            return {"status": "execution_failed", "error": "Plan has no calls to execute."}

        # Execute the first call in the plan
        first_call = plan["calls"][0]
        try:
            result = self.broker.execute_call(first_call)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "execution_failed", "error": str(e)}
