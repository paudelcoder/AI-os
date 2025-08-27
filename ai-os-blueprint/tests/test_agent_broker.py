import unittest
from unittest.mock import patch, Mock
import requests

import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.core.agent_broker import AgentBroker

class TestAgentBroker(unittest.TestCase):
    """Unit tests for the AgentBroker service."""

    def setUp(self):
        """Set up a new AgentBroker for each test."""
        self.broker = AgentBroker()
        self.test_manifest = {"service": "TestAgent", "capabilities": []}
        self.test_base_url = "http://localhost:1234"
        self.broker.register_agent(self.test_manifest, self.test_base_url)

    def test_register_agent_success(self):
        """Test that an agent can be registered successfully."""
        self.assertIn("TestAgent", self.broker.registry)
        self.assertEqual(self.broker.registry["TestAgent"]["base_url"], self.test_base_url)

    def test_register_agent_fails_with_no_service_name(self):
        """Test that registration fails if the manifest has no service name."""
        with self.assertRaises(ValueError):
            self.broker.register_agent({"capabilities": []}, self.test_base_url)

    @patch('system.core.agent_broker.requests.post')
    def test_execute_call_success(self, mock_post):
        """Test a successful capability call execution."""
        # Configure the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "data": "test_result"}
        mock_post.return_value = mock_response

        capability_call = {
            "call": "TestAgent.do_something",
            "parameters": {"param1": "value1"}
        }
        result = self.broker.execute_call(capability_call)

        # Verify the result and that the mock was called correctly
        self.assertEqual(result, {"status": "ok", "data": "test_result"})
        expected_url = f"{self.test_base_url}/do_something"
        mock_post.assert_called_once_with(
            expected_url,
            json={"param1": "value1"},
            timeout=5
        )

    def test_execute_call_unregistered_service(self):
        """Test that executing a call for an unregistered service raises an error."""
        capability_call = {"call": "UnknownAgent.do_something"}
        with self.assertRaises(ValueError):
            self.broker.execute_call(capability_call)

    @patch('system.core.agent_broker.requests.post')
    def test_execute_call_http_error(self, mock_post):
        """Test that an HTTP error during the call is handled."""
        # Configure the mock to raise an exception
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        capability_call = {"call": "TestAgent.do_something"}
        # The broker re-raises the exception, so we expect it here.
        with self.assertRaises(requests.exceptions.HTTPError):
            self.broker.execute_call(capability_call)

if __name__ == '__main__':
    unittest.main()
