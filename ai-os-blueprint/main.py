# AI OS - Main Entrypoint

# Import core services
from system.core.policy_engine import PolicyEngine
from system.core.memory_graph import MemoryGraph
from system.core.agent_broker import AgentBroker
from system.core.planner import Planner
from system.security.prompt_guard import PromptGuard
from experience.card_renderer import CardRenderer

# Import utilities
import json
import os
import pprint

def main():
    """
    The main entrypoint for the AI OS simulation.
    Initializes all services and runs the main interaction loop.
    """
    print("="*50)
    print("AI OS Shell - MVP")
    print("="*50)
    print("Initializing services...")

    # --- Service Initialization ---
    # Define paths relative to the project root for robustness
    project_root = os.path.dirname(os.path.abspath(__file__))
    # The project root is assumed to be the 'ai-os-blueprint' directory.
    # All paths will be constructed relative to this script's location.
    def get_path(relative_path):
        return os.path.join(project_root, relative_path)

    # 1. Load policies and manifests
    print("  - Loading policies and manifests...")
    with open(get_path('spec/schemas/policy.json'), 'r') as f:
        policy_doc = json.load(f)
    with open(get_path('agents/calendar/agent_manifest.json'), 'r') as f:
        calendar_manifest = json.load(f)
    with open(get_path('agents/rides/agent_manifest.json'), 'r') as f:
        rides_manifest = json.load(f)

    # 2. Instantiate all core services
    print("  - Instantiating services...")
    policy_engine = PolicyEngine(policy_doc)
    memory_graph = MemoryGraph(db_path=get_path("ai_os_memory.db"))
    agent_broker = AgentBroker()
    prompt_guard = PromptGuard() # New security service
    planner = Planner(memory_graph, policy_engine, agent_broker)
    card_renderer = CardRenderer()

    # 3. Register agents with the broker
    # In a real OS, this would happen dynamically as agents are installed/enabled.
    print("  - Registering agents...")
    agent_broker.register_agent(calendar_manifest, "http://localhost:5001")
    agent_broker.register_agent(rides_manifest, "http://localhost:5002")

    print("Services initialized.")
    print("\nStarting interaction loop (type 'exit' to quit)...")

    # --- Main Interaction Loop ---
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == 'exit':
                break
            if not user_input:
                continue

            # 1. Scan the input for prompt injection before processing
            scan_result = prompt_guard.scan(user_input)
            if not scan_result["is_safe"]:
                print(f"\n[OS SECURITY] Input rejected. Reason: {scan_result['reason']}")
                continue  # Skip to the next prompt

            # 2. Create intent
            intent = {"user_utterance": user_input, "context": {}}
            print("\n[OS] Intent created...")
            pprint.pprint(intent)

            # 2. Create a plan
            plan = planner.create_plan(intent)
            print("\n[OS] Plan generated...")
            pprint.pprint(plan)

            # 3. Execute the plan
            # NOTE: This will likely fail in this simulation because the agent
            # servers are not running. This is expected and demonstrates the full flow.
            print("\n[OS] Executing plan...")
            execution_result = planner.execute_plan(plan)
            print("\n[OS] Execution result...")
            pprint.pprint(execution_result)

            # 4. Render the result into a UI card
            final_card = None
            if execution_result.get("status") == "success":
                # Find the output schema from the original plan to guide the renderer
                if plan.get("calls"):
                    call_str = plan["calls"][0]["call"]
                    service_name, cap_name = call_str.split('.', 1)
                    agent_manifest = agent_broker.registry.get(service_name, {}).get("manifest", {})
                    output_schema = next((c.get("output_schema") for c in agent_manifest.get("capabilities", []) if c.get("name") == cap_name), {})
                    final_card = card_renderer.render(execution_result["result"], output_schema)

            # If execution failed or no specific renderer, create a generic card
            if not final_card:
                final_card = card_renderer.render(execution_result, {})

            print("\n[OS] Final UI Card to display:")
            print("-" * 30)
            pprint.pprint(final_card)
            print("-" * 30)

        except Exception as e:
            print(f"\n[OS] An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

    print("\nAI OS Shell shutting down.")


if __name__ == "__main__":
    # This ensures the script runs only when executed directly.
    main()
