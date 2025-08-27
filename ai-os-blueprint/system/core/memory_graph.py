import sqlite3
import json
import uuid
from datetime import datetime, timezone

class MemoryGraph:
    """
    Manages the user's memory graph using a local SQLite database.
    This class provides methods to add, retrieve, and query memories
    while enforcing consent rules.
    """

    def __init__(self, db_path=":memory:"):
        """
        Initializes the MemoryGraph service.
        :param db_path: Path to the SQLite database file. Defaults to an in-memory DB
                        for testing or ephemeral use.
        """
        self.conn = sqlite3.connect(db_path)
        # Allows accessing columns by name, which is more readable.
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Creates the 'memories' table in the database if it doesn't already exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                consent TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_memory(self, memory_data):
        """
        Adds a new memory to the graph. If 'memory_id' or 'timestamp' are not
        provided, they will be generated automatically.

        :param memory_data: A dictionary conforming to the memory_entry.json schema.
        :return: The ID of the newly added memory.
        """
        if "memory_id" not in memory_data:
            memory_data["memory_id"] = f"mem_{uuid.uuid4().hex[:16]}"
        if "timestamp" not in memory_data:
            memory_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memories (memory_id, timestamp, type, content, metadata, consent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            memory_data["memory_id"],
            memory_data["timestamp"],
            memory_data["type"],
            json.dumps(memory_data.get("content", {})),
            json.dumps(memory_data.get("metadata", {})),
            json.dumps(memory_data.get("consent", {}))
        ))
        self.conn.commit()
        return memory_data["memory_id"]

    def _deserialize_row(self, row):
        """Converts a database row object into a memory dictionary."""
        if row is None:
            return None
        return {
            "memory_id": row["memory_id"],
            "timestamp": row["timestamp"],
            "type": row["type"],
            "content": json.loads(row["content"]),
            "metadata": json.loads(row["metadata"]),
            "consent": json.loads(row["consent"])
        }

    def get_memory(self, memory_id):
        """Retrieves a single memory by its ID, without checking consent."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE memory_id = ?", (memory_id,))
        row = cursor.fetchone()
        return self._deserialize_row(row)

    def find_memories(self, principal, memory_type=None):
        """
        Finds memories that are accessible to a given principal.

        :param principal: A dict representing the agent requesting access, e.g.,
                          {"type": "agent_service", "id": "Delta"}.
        :param memory_type: An optional string to filter memories by type.
        :return: A list of memory dictionaries that the principal is allowed to access.
        """
        query = "SELECT * FROM memories"
        params = []
        if memory_type:
            query += " WHERE type = ?"
            params.append(memory_type)

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))

        accessible_memories = []
        for row in cursor.fetchall():
            memory = self._deserialize_row(row)
            if self._has_access(principal, memory.get("consent", {})):
                accessible_memories.append(memory)

        return accessible_memories

    def _has_access(self, principal, consent_data):
        """
        Checks if a principal has access based on the memory's consent data.
        This is a simplified check for the MVP.
        """
        if not principal or not isinstance(principal, dict):
            return False

        # A more advanced version would handle agent categories, wildcards, etc.
        for rule in consent_data.get("access_rules", []):
            if (rule.get("principal_type") == principal.get("type") and
                rule.get("principal_id") == principal.get("id")):
                # For now, we assume any matching rule grants read access.
                if rule.get("access_level") == "read":
                    return True
        return False

    def close(self):
        """Closes the database connection gracefully."""
        self.conn.close()
