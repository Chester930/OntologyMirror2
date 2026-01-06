from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from .base import BaseExtractor

class DBExtractor(BaseExtractor):
    """
    Extracts schema and sample data from a live database.
    Supports SQLite, PostgreSQL, MySQL, MSSQL (via SQLAlchemy).
    """

    def __init__(self, connection_string: str, db_type: str = "SQLite"):
        """
        Args:
            connection_string (str): SQLAlchemy connection string.
            db_type (str): Type of database (used for dialect-specific queries like LIMIT vs TOP).
        """
        super().__init__(connection_string)
        self.db_type = db_type
        self.engine: Optional[Engine] = None

    def extract(self) -> List[Dict[str, Any]]:
        """
        Connects to the DB and extracts schema + sample data for all tables.
        
        Returns:
            List[Dict]: A list of table definitions with sample data.
            [
                {
                    "table_name": "users",
                    "columns": [...],
                    "sample_data": [[1, "John"], [2, "Jane"]]
                }
            ]
        """
        self._connect()
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        
        extracted_data = []
        
        for table in table_names:
            # 1. Get Columns
            columns = []
            try:
                cols = inspector.get_columns(table)
                for col in cols:
                    columns.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "primary_key": col.get("primary_key", False),
                        "nullable": col.get("nullable", True)
                    })
            except Exception as e:
                print(f"Error getting columns for {table}: {e}")
                continue

            # 2. Get Sample Data
            sample_rows = self._fetch_sample_data(table)
            
            extracted_data.append({
                "table_name": table,
                "columns": columns,
                "sample_data": sample_rows
            })
            
        return extracted_data

    def _connect(self):
        """Creates the SQLAlchemy Engine"""
        if not self.engine:
            try:
                self.engine = create_engine(self.source)
                # Test connection
                with self.engine.connect() as conn:
                    pass
            except Exception as e:
                print(f"Failed to connect to {self.source}: {e}")
                raise e

    def _fetch_sample_data(self, table_name: str) -> List[Any]:
        """Fetches 5 rows of sample data."""
        query = ""
        # Dialect specific queries
        # Note: In a larger app, we might use the specific Connector classes we built in tools/
        # But here we keep it self-contained to avoid dependency on 'tools'
        if self.db_type == "MSSQL":
            query = f"SELECT TOP 5 * FROM {table_name}"
        else:
            # SQLite, Postgres, MySQL all support LIMIT
            query = f"SELECT * FROM {table_name} LIMIT 5"
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                # Convert rows to serializable format (list of tuples/dicts)
                # We convert to string to avoid serialization issues with dates/decimals for now
                rows = [tuple(str(item) for item in row) for row in result.fetchall()]
                return rows
        except Exception as e:
            print(f"Error fetching sample data for {table_name}: {e}")
            return []
