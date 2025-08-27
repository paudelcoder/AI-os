import unittest
import tempfile
import os
import json
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.security.audit_log_service import AuditLogService

class TestAuditLogService(unittest.TestCase):
    """Unit tests for the AuditLogService."""

    def setUp(self):
        """Create a temporary file to act as the log file for each test."""
        # This provides a clean log file for each test case.
        # We create it, get its name, and then it's deleted automatically on close.
        # To manage it manually for reading, we delete=False and handle it ourselves.
        self.temp_log_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')
        self.log_file_path = self.temp_log_file.name
        self.temp_log_file.close() # Close it so the service can open it.

    def tearDown(self):
        """Clean up the temporary log file after each test."""
        os.remove(self.log_file_path)

    def test_log_creation_and_writing(self):
        """Test that a single, well-formed log entry is written to the file."""
        logger = AuditLogService(self.log_file_path)

        principal = {"type": "test_principal"}
        action = "test.action"
        details = {"data": "some_value", "number": 123}

        logger.log_action(principal, action, details)
        logger.close()  # Must close to ensure the file buffer is written to disk

        # Verify the content by reading the file back
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            line = f.readline()
            self.assertTrue(line, "Log file should not be empty.")

            log_entry = json.loads(line)
            self.assertEqual(log_entry["principal"], principal)
            self.assertEqual(log_entry["action"], action)
            self.assertEqual(log_entry["details"], details)
            self.assertIn("timestamp", log_entry)

    def test_append_only_logging(self):
        """Test that multiple log entries are appended sequentially."""
        logger = AuditLogService(self.log_file_path)

        # Log two distinct actions
        logger.log_action({"id": "principal1"}, "action1", {"info": "first"})
        logger.log_action({"id": "principal2"}, "action2", {"info": "second"})

        logger.close()

        # Verify that the file contains exactly two lines
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            # Check content of each line
            log1 = json.loads(lines[0])
            log2 = json.loads(lines[1])
            self.assertEqual(log1["action"], "action1")
            self.assertEqual(log2["action"], "action2")

    def test_service_handles_io_error_on_init(self):
        """Test that the service handles being unable to open the log file."""
        # An invalid path that we can't write to
        invalid_path = "/non_existent_dir/audit.log"
        logger = AuditLogService(invalid_path)
        # The service should not crash, but logging should be disabled.
        # We can't easily assert the printed error, but we can check it doesn't throw.
        logger.log_action({"id": "p1"}, "action1", {}) # Should not raise an exception
        self.assertIsNone(logger._log_file)


if __name__ == '__main__':
    unittest.main()
