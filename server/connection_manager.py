import json
import os
from typing import Dict, Any, List

CONNECTIONS_FILE = os.path.join(os.getcwd(), "db_connections.json")

class ConnectionManager:
    """Manages database connection configurations stored in a JSON file."""
    
    def __init__(self, file_path: str = CONNECTIONS_FILE):
        self.file_path = file_path
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def load_connections(self) -> Dict[str, Any]:
        """Loads all connections from the JSON file."""
        try:
            with open(self.file_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_connection(self, name: str, data: Dict[str, Any]):
        """Saves or updates a connection."""
        connections = self.load_connections()
        connections[name] = data
        with open(self.file_path, "w", encoding='utf-8') as f:
            json.dump(connections, f, indent=4, ensure_ascii=False)

    def delete_connection(self, name: str) -> bool:
        """Deletes a connection by name."""
        connections = self.load_connections()
        if name in connections:
            del connections[name]
            with open(self.file_path, "w", encoding='utf-8') as f:
                json.dump(connections, f, indent=4, ensure_ascii=False)
            return True
        return False
        
    def get_connection(self, name: str) -> Dict[str, Any]:
        """Retrieves a single connection by name."""
        return self.load_connections().get(name)
