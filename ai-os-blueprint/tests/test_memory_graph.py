import unittest
import sys
import os

# Add the project root directory to the Python path to allow imports from 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.core.memory_graph import MemoryGraph

class TestMemoryGraph(unittest.TestCase):
    """Unit tests for the MemoryGraph service."""

    def setUp(self):
        """Set up an in-memory database and populate it with test data."""
        self.db = MemoryGraph(db_path=":memory:")

        # Memory accessible by 'Delta' (service) and 'travel' (category)
        self.memory1 = {
            "memory_id": "mem_pref_1",
            "type": "preference",
            "content": {"key": "airline", "value": "Delta"},
            "consent": {"access_rules": [
                {"principal_type": "agent_service", "principal_id": "Delta", "access_level": "read"}
            ]}
        }

        # Memory accessible only by 'Rides' agent
        self.memory2 = {
            "memory_id": "mem_entity_2",
            "type": "entity",
            "content": {"name": "Jules's Home", "location": "123 Main St"},
            "consent": {"access_rules": [
                {"principal_type": "agent_service", "principal_id": "Rides", "access_level": "read"}
            ]}
        }

        self.db.add_memory(self.memory1)
        self.db.add_memory(self.memory2)

    def tearDown(self):
        """Close the database connection after each test to ensure isolation."""
        self.db.close()

    def test_add_and_get_memory(self):
        """Test that a memory can be added and retrieved by its ID."""
        retrieved = self.db.get_memory("mem_pref_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["content"]["value"], "Delta")
        self.assertEqual(self.db.get_memory("non_existent_id"), None)

    def test_find_memory_with_access(self):
        """Test that a principal with the correct permissions can find a memory."""
        principal = {"type": "agent_service", "id": "Delta"}
        memories = self.db.find_memories(principal)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["memory_id"], "mem_pref_1")

    def test_find_memory_no_access(self):
        """Test that a principal without permissions cannot find any memories."""
        principal = {"type": "agent_service", "id": "SomeOtherAgent"}
        memories = self.db.find_memories(principal)
        self.assertEqual(len(memories), 0)

    def test_find_memory_with_type_filter(self):
        """Test filtering memories by type, combined with consent checks."""
        principal_rides = {"type": "agent_service", "id": "Rides"}

        # The 'Rides' agent should find the 'entity' memory it has access to.
        memories = self.db.find_memories(principal_rides, memory_type="entity")
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["memory_id"], "mem_entity_2")

        # The 'Rides' agent should NOT find any 'preference' memories.
        memories = self.db.find_memories(principal_rides, memory_type="preference")
        self.assertEqual(len(memories), 0)

    def test_find_memory_invalid_principal(self):
        """Test that an invalid or None principal returns no results."""
        self.assertEqual(len(self.db.find_memories(None)), 0)
        self.assertEqual(len(self.db.find_memories({})), 0)
        self.assertEqual(len(self.db.find_memories("not_a_dict")), 0)

    def test_auto_id_and_timestamp_generation(self):
        """Test that memory_id and timestamp are auto-generated when not provided."""
        new_mem_data = {
            "type": "habit",
            "content": {"action": "order_coffee_at_8am"},
            "consent": {"access_rules": []}
        }
        mem_id = self.db.add_memory(new_mem_data)
        self.assertIsNotNone(mem_id)
        self.assertTrue(mem_id.startswith("mem_"))

        retrieved = self.db.get_memory(mem_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["memory_id"], mem_id)
        self.assertIn("timestamp", retrieved)
        self.assertTrue(retrieved["timestamp"].endswith("Z") or '+' in retrieved["timestamp"])

if __name__ == '__main__':
    unittest.main()
