import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.core.vault_service import VaultService

class TestVaultService(unittest.TestCase):
    """Unit tests for the VaultService."""

    def setUp(self):
        """Set up a new VaultService for each test."""
        self.vault = VaultService()
        self.authorized_principal = {"type": "os_service", "id": "CredentialManager"}
        self.unauthorized_principal = {"type": "agent_service", "id": "SomeAgent"}
        self.user_principal = {"type": "user"}

    def test_store_and_retrieve_secret_success(self):
        """Test storing a secret with an authorized principal and retrieving it."""
        key = "test_key"
        value = "test_value"

        # Test storing by a privileged OS service
        success = self.vault.store_secret(key, value, self.authorized_principal)
        self.assertTrue(success)

        retrieved_value = self.vault.retrieve_secret(key, self.authorized_principal)
        self.assertEqual(retrieved_value, value)

    def test_store_by_user_principal_success(self):
        """Test that a 'user' principal is also allowed to write secrets."""
        key = "user_key"
        value = "user_secret"
        success = self.vault.store_secret(key, value, self.user_principal)
        self.assertTrue(success)
        self.assertEqual(self.vault.retrieve_secret(key, self.user_principal), value)

    def test_store_secret_unauthorized(self):
        """Test that an unauthorized principal cannot store a secret."""
        key = "test_key_unauth"
        value = "test_value"

        success = self.vault.store_secret(key, value, self.unauthorized_principal)
        self.assertFalse(success)

        # Verify the secret was not stored by trying to retrieve it
        retrieved_value = self.vault.retrieve_secret(key, self.authorized_principal)
        self.assertIsNone(retrieved_value)

    def test_retrieve_non_existent_secret(self):
        """Test that retrieving a non-existent key returns None."""
        retrieved_value = self.vault.retrieve_secret("non_existent_key", self.authorized_principal)
        self.assertIsNone(retrieved_value)

if __name__ == '__main__':
    unittest.main()
