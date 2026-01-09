import os
import sqlite3
import re
import threading
from tools.db_manager_lib.core.sanitizer import SQLSanitizer

class ImportManager:
    def __init__(self, current_dir):
        self.current_dir = current_dir

    def run_import_thread(self, sorted_files, conn_name, db_path, mode, callback_log=None):
        """
        Runs the import process in a background thread.
        callback_log: function(msg) to print status back to main thread/UI.
        """
        threading.Thread(target=self._worker, args=(sorted_files, conn_name, db_path, mode, callback_log), daemon=True).start()

    def _worker(self, sorted_files, conn_name, db_path, mode, callback_log):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = OFF;")
            
            # Custom REGEXP for compatibility
            conn.create_function("REGEXP", 2, lambda x, y: 1 if re.search(x, y) else 0)
            
            cursor = conn.cursor()
            total_files = len(sorted_files)
            
            for idx, sql_file in enumerate(sorted_files):
                if callback_log:
                    callback_log(f"Processing {idx+1}/{total_files}: {sql_file}")
                
                # Read SQL
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f: sql_script = f.read()
                except UnicodeDecodeError:
                    with open(sql_file, 'r', encoding='latin-1') as f: sql_script = f.read()
                
                # Sanitize
                sql_script = SQLSanitizer.sanitize(sql_script)

                # DEBUG: Write sanitized file
                debug_name = f"debug_{idx}_{os.path.basename(sql_file)}.sql"
                debug_dump_path = os.path.join(self.current_dir, "..", "data", debug_name)
                try:
                    with open(debug_dump_path, 'w', encoding='utf-8') as f:
                        f.write(sql_script)
                except: pass

                # Execute
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    cursor.executescript(sql_script)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    err_msg = f"Error executing {sql_file}: {e}"
                    print(err_msg)
                    if callback_log:
                        # Translate common errors
                        if "near" in str(e):
                            err_msg += f"\n在處理檔案 '{os.path.basename(sql_file)}' 時發生錯誤:\n{e}\n\n除錯檔案已儲存至 data/ 目錄。"
                        elif "duplicate column" in str(e):
                            err_msg += f"\n在處理檔案 '{os.path.basename(sql_file)}' 時發生錯誤:\n{e}\n\n除錯檔案已儲存至 data/ 目錄。"
                        callback_log(err_msg)
                    return 

            conn.close()
            if callback_log:
                callback_log(f"成功匯入資料庫: {conn_name}")
                
        except Exception as e:
            if callback_log:
                callback_log(f"Critical Error: {e}")
