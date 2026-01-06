from .base import BaseConnector

class SQLiteConnector(BaseConnector):
    def get_sample_data_query(self, table_name: str) -> str:
        return f"SELECT * FROM {table_name} LIMIT 5"
