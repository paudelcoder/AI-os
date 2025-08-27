import json
from datetime import datetime, timezone

class AuditLogService:
    """
    Provides a service for writing tamper-resistant, append-only audit logs.

    Each log entry is a structured JSON object, making the log easy to parse
    and analyze, while the append-only file mode provides a basic level of
    tamper resistance.
    """

    def __init__(self, log_file_path):
        """
        Initializes the audit logger and opens the specified log file.

        :param log_file_path: The full path to the log file to be used.
        """
        self.log_file_path = log_file_path
        try:
            # Open the file in append mode ('a'). The file handle is kept open.
            self._log_file = open(self.log_file_path, 'a', encoding='utf-8')
        except IOError as e:
            print(f"FATAL: Could not open audit log file at {log_file_path}. Error: {e}")
            self._log_file = None

    def log_action(self, principal, action, details):
        """
        Writes a structured log entry to the audit log file.

        :param principal: The principal (user or service) performing the action.
        :param action: A string identifying the action being logged (e.g., 'PolicyEngine.evaluate').
        :param details: A dictionary containing relevant data about the action.
        """
        if not self._log_file:
            print("ERROR: Audit log service is not available. Cannot log action.")
            return

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "principal": principal,
            "action": action,
            "details": details
        }

        try:
            # Write the JSON string to the file, followed by a newline.
            self._log_file.write(json.dumps(log_entry) + '\n')
            # Ensure the entry is written to disk immediately for reliability.
            self._log_file.flush()
        except IOError as e:
            print(f"ERROR: Could not write to audit log file. Error: {e}")

    def close(self):
        """Closes the log file handle if it is open."""
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def __del__(self):
        """
        Destructor to ensure the file is closed when the object is garbage collected.
        """
        self.close()
