from .base import BaseConnector

class PostgresConnector(BaseConnector):
    def get_sample_data_query(self, table_name: str) -> str:
        # Postgres usually supports LIMIT
        return f"SELECT * FROM {table_name} LIMIT 5"
