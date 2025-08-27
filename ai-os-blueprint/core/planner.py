from .policy_engine import Decision

class Planner:
    """
    A simple, rule-based planner that creates execution plans from user intents.

    This MVP planner uses basic keyword matching to understand intents and
    integrates with the MemoryGraph and PolicyEngine to create context-aware
    and secure plans.
    """

    def __init__(self, memory_graph, policy_engine):
        """
        Initializes the Planner with its dependent services.

        :param memory_graph: An instance of MemoryGraph.
        :param policy_engine: An instance of PolicyEngine.
        """
        self.memory = memory_graph
        self.policy = policy_engine
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
        if "flight" in utterance and ("book" in utterance or "find" in utterance):
            return self._plan_book_flight(intent)

        return {"status": "failed", "reason": "Could not understand intent", "calls": []}

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
