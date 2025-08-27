import requests

class AgentBroker:
    """
    Manages and communicates with all registered agents.
    Acts as a central hub for discovering agent capabilities and executing calls.
    """

    def __init__(self, audit_log_service):
        """
        Initializes the AgentBroker with an empty agent registry and the audit service.
        :param audit_log_service: An instance of AuditLogService.
        """
        self.registry = {}  # Key: service_name, Value: {base_url, manifest}
        self.audit = audit_log_service

    def register_agent(self, manifest, base_url):
        """
        Registers a running agent with the broker.

        This method stores the agent's manifest and its network location,
        making it discoverable by the OS.

        :param manifest: The agent's manifest dictionary.
        :param base_url: The network address (e.g., 'http://localhost:5001')
                         where the agent is running.
        """
        service_name = manifest.get("service")
        if not service_name:
            raise ValueError("Manifest must contain a 'service' name.")

        print(f"Registering agent: {service_name} at {base_url}")
        self.registry[service_name] = {
            "base_url": base_url.rstrip('/'),
            "manifest": manifest
        }

    def execute_call(self, capability_call):
        """
        Executes a capability call by routing it to the appropriate agent.

        :param capability_call: A dictionary like {"call": "Service.capability", "parameters": {...}}.
        :return: The JSON response from the agent.
        :raises: ValueError for malformed calls or unregistered services,
                 requests.exceptions.RequestException for network errors.
        """
        call_str = capability_call.get("call")
        if not call_str or '.' not in call_str:
            raise ValueError("Invalid 'call' format. Expected 'Service.capability'.")

        service_name, capability_name = call_str.split('.', 1)

        agent = self.registry.get(service_name)
        if not agent:
            raise ValueError(f"Service '{service_name}' is not registered.")

        # Convention: The API endpoint is the capability name.
        # A more robust implementation would get this from the manifest.
        endpoint_url = f"{agent['base_url']}/{capability_name}"
        parameters = capability_call.get("parameters", {})

        self.audit.log_action(
            principal={"type": "service", "id": "AgentBroker"},
            action="agent.call.execute",
            details={"capability_call": capability_call}
        )

        try:
            response = requests.post(endpoint_url, json=parameters, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            response_data = response.json()
            self.audit.log_action(
                principal={"type": "service", "id": "AgentBroker"},
                action="agent.call.response",
                details={"call": call_str, "status": "success", "response": response_data}
            )
            return response_data
        except requests.exceptions.RequestException as e:
            self.audit.log_action(
                principal={"type": "service", "id": "AgentBroker"},
                action="agent.call.response",
                details={"call": call_str, "status": "failure", "error": str(e)}
            )
            print(f"Error calling agent {service_name}: {e}")
            # Re-raise the exception to be handled by the caller (e.g., the Planner).
            raise
