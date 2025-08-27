class CardRenderer:
    """
    Transforms agent output data into a structured UI card format based on
    display hints provided in the agent's manifest.
    """

    def render(self, agent_output, output_schema):
        """
        Renders a UI card based on the agent's output and schema.

        :param agent_output: The JSON data returned by the agent call.
        :param output_schema: The 'output_schema' from the agent's manifest.
        :return: A dictionary representing a UI card.
        """
        display_hint = output_schema.get("display_hint")

        if display_hint == "ride_confirmation":
            return self._render_ride_confirmation(agent_output)

        # A more advanced implementation would have more renderers for other hints.

        # Fallback to a generic renderer if no specific hint matches.
        return self._render_generic(agent_output)

    def _render_ride_confirmation(self, data):
        """
        Renders a specific, rich card for a ride confirmation.

        :param data: The agent output data for the ride.
        :return: A dictionary structured as a UI card.
        """
        # Perform data transformation and formatting for presentation.
        eta = data.get("eta_minutes", "?")
        price = data.get("price_estimate", 0.0)
        ride_id = data.get("ride_id", "unknown_ride")

        card = {
            "card_id": f"card_{ride_id}",
            "card_type": "rich_info",
            "title": "Your Ride is Confirmed",
            "subtitle": f"Driver: {data.get('driver_name', 'Unknown')}",
            "components": [
                {"type": "highlight", "label": "Arriving in", "value": f"{eta} minutes"},
                {"type": "key_value", "label": "Estimated Price", "value": f"${price:.2f}"}
            ],
            "actions": [
                {"label": "Cancel Ride", "action_type": "destructive", "capability_call": {
                    "call": "Rides.cancel_ride",
                    "parameters": {"ride_id": ride_id}
                }}
            ]
        }
        return card

    def _render_generic(self, data):
        """
        A fallback renderer that displays raw key-value pairs for any agent
        output that doesn't have a specialized renderer.

        :param data: The agent output data.
        :return: A dictionary structured as a simple UI card.
        """
        components = [{"type": "key_value", "label": str(k), "value": str(v)} for k, v in data.items()]

        card = {
            "card_id": "card_generic_output",
            "card_type": "simple_info",
            "title": "Agent Result",
            "components": components,
            "actions": []
        }
        return card
