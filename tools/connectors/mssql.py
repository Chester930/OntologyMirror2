from .base import BaseConnector

class MSSQLConnector(BaseConnector):
    def get_sample_data_query(self, table_name: str) -> str:
        # MSSQL uses TOP
        return f"SELECT TOP 5 * FROM {table_name}"
