import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from experience.card_renderer import CardRenderer

class TestCardRenderer(unittest.TestCase):
    """Unit tests for the CardRenderer service."""

    def setUp(self):
        """Set up the CardRenderer for each test."""
        self.renderer = CardRenderer()

    def test_render_with_specific_hint(self):
        """Test rendering a ride confirmation card using a display hint."""
        agent_output = {
            "ride_id": "ride_xyz_789",
            "driver_name": "Alex",
            "eta_minutes": 5,
            "price_estimate": 15.75
        }
        output_schema = {"display_hint": "ride_confirmation"}

        card = self.renderer.render(agent_output, output_schema)

        self.assertEqual(card["card_type"], "rich_info")
        self.assertEqual(card["title"], "Your Ride is Confirmed")
        self.assertEqual(len(card["components"]), 2)
        self.assertEqual(card["components"][0]["type"], "highlight")
        self.assertEqual(card["components"][0]["value"], "5 minutes")
        self.assertEqual(card["components"][1]["type"], "key_value")
        self.assertEqual(card["components"][1]["value"], "$15.75")
        self.assertEqual(len(card["actions"]), 1)
        self.assertEqual(card["actions"][0]["label"], "Cancel Ride")

    def test_render_fallback_to_generic(self):
        """Test the generic fallback renderer when no display hint is provided."""
        agent_output = {"status": "complete", "confirmation_code": "ABC-123"}
        output_schema = {}  # No display hint

        card = self.renderer.render(agent_output, output_schema)

        self.assertEqual(card["card_type"], "simple_info")
        self.assertEqual(card["title"], "Agent Result")
        self.assertEqual(len(card["components"]), 2)
        # Check that it created key-value components
        self.assertEqual(card["components"][0]["label"], "status")
        self.assertEqual(card["components"][0]["value"], "complete")
        self.assertEqual(card["components"][1]["label"], "confirmation_code")
        self.assertEqual(card["components"][1]["value"], "ABC-123")

    def test_render_with_missing_data(self):
        """Test that the renderer handles missing data gracefully without crashing."""
        agent_output = {
            "ride_id": "ride_abc_456",
            "driver_name": "Beth"
            # eta_minutes and price_estimate are missing
        }
        output_schema = {"display_hint": "ride_confirmation"}

        card = self.renderer.render(agent_output, output_schema)

        self.assertEqual(card["card_type"], "rich_info")
        # It should still render the card, but with default/placeholder values.
        self.assertEqual(card["components"][0]["value"], "? minutes")
        self.assertEqual(card["components"][1]["value"], "$0.00")
        self.assertEqual(card["subtitle"], "Driver: Beth")

if __name__ == '__main__':
    unittest.main()
