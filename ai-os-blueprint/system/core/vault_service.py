class VaultService:
    """
    A simulated hardware-backed vault for storing and retrieving secrets.

    In a real system, this service would be a thin wrapper around a hardware
    security module (HSM), a Trusted Execution Environment (TEE), or a Secure
    Element (SE). For this simulation, secrets are stored in a simple
    in-memory dictionary to model the access patterns.
    """

    def __init__(self):
        """Initializes the vault with an empty secret store."""
        self._secrets = {}
        # In a real system, these principals would have special OS-level privileges.
        self._allowed_writers = [
            {"type": "os_service", "id": "CredentialManager"},
            {"type": "user"}  # Represents a direct user action, e.g., saving a password.
        ]

    def store_secret(self, key, value, principal):
        """
        Stores a secret in the vault after checking for authorization.

        :param key: The unique key for the secret (e.g., 'payment_token_amex_1005').
        :param value: The secret value to store.
        :param principal: The principal attempting to store the secret.
        :return: True if the secret was stored successfully, False otherwise.
        """
        # This simulates a critical security check: only authorized principals
        # can write to the vault.
        if principal not in self._allowed_writers:
            print(f"SECURITY ALERT: Unauthorized principal {principal} attempted to write to vault.")
            return False

        self._secrets[key] = value
        print(f"Secret '{key}' stored in vault by principal {principal}.")
        return True

    def retrieve_secret(self, key, principal):
        """
        Retrieves a secret from the vault.

        For this MVP, we are not performing granular read-permission checks.
        The architectural security model assumes that only highly privileged
        services (like a credential manager or the payment agent itself in some
        flows) would have a direct handle to this VaultService object and would
        be authorized to call this method.

        :param key: The key of the secret to retrieve.
        :param principal: The principal requesting the secret (could be used for logging).
        :return: The secret value, or None if the key does not exist.
        """
        print(f"Principal {principal} retrieving secret '{key}' from vault.")
        return self._secrets.get(key)
