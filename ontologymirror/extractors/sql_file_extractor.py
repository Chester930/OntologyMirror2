import os
import sqlite3
import tempfile
from typing import List, Dict, Any, Optional
from .base import BaseExtractor
from .db_extractor import DBExtractor

class SQLFileExtractor(BaseExtractor):
    """
    Extracts schema and data from a .sql file (dump).
    Strategy: Load .sql into a temporary SQLite DB -> Use DBExtractor.
    """

    def __init__(self, file_path: str):
        """
        Args:
            file_path (str): Path to the .sql file.
        """
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        super().__init__(file_path)

    def extract(self) -> List[Dict[str, Any]]:
        """
        Loads SQL into temp DB, extracts data, and cleans up.
        """
        # 1. Create Temp DB
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd) # Close file descriptor, we just need the path
        
        try:
            # 2. Load SQL
            self._load_sql_to_sqlite(self.file_path, temp_db_path)
            
            # 3. Extract using DBExtractor
            # We use a connection string for the temp DB
            conn_str = f"sqlite:///{temp_db_path}"
            db_extractor = DBExtractor(conn_str, db_type="SQLite")
            
            return db_extractor.extract()
            
        finally:
            # 4. Cleanup
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception as e:
                    print(f"Warning: Failed to remove temp DB {temp_db_path}: {e}")

    def _load_sql_to_sqlite(self, sql_path: str, db_path: str):
        """
        Executes the SQL script against the SQLite DB.
        """
        try:
            # Try UTF-8 first
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1
            print(f"UTF-8 decode failed for {sql_path}, trying latin-1...")
            with open(sql_path, 'r', encoding='latin-1') as f:
                sql_script = f.read()
                
        # --- SANITIZATION ---
        try:
            from tools.db_manager_lib.core.sanitizer import SQLSanitizer
            print(f"Sanitizing SQL script: {sql_path}")
            sql_script = SQLSanitizer.sanitize(sql_script)
        except ImportError:
            print("Warning: SQLSanitizer not found. Scaling back to raw execution.")
        except Exception as e:
            print(f"Error during sanitization: {e}")
            # Proceed with potentially raw script if sanitization fails? Or raise?
            # Safer to proceed and see if sqlite takes it, or maybe it failed badly.
            pass

        # Connect and execute
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite Error during import: {e}")
            raise e
        finally:
            conn.close()
