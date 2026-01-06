from abc import ABC, abstractmethod
from sqlalchemy import create_engine, inspect, text
from typing import List, Dict, Any

class BaseConnector(ABC):
    """
    Abstract base class for Database Connectors.
    """
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None

    def connect(self):
        """Create SQLAlchemy Engine"""
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                pass
            return True
        except Exception as e:
            raise e

    def get_tables(self) -> List[str]:
        """List all tables"""
        if not self.engine:
            raise Exception("Not connected")
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column info"""
        if not self.engine:
            raise Exception("Not connected")
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        # Simplify for display
        return [{"name": col["name"], "type": str(col["type"])} for col in columns]

    @abstractmethod
    def get_sample_data_query(self, table_name: str) -> str:
        """Return SQL query to fetch sample data (handles LIMIT/TOP syntax)"""
        pass

    def get_sample_data(self, table_name: str) -> List[Any]:
        """Execute sample data query"""
        if not self.engine:
            raise Exception("Not connected")
        
        query = self.get_sample_data_query(table_name)
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()
