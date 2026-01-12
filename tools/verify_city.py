import os
import sqlite3
from db_manager_lib.core.sanitizer import SQLSanitizer

# Path to the problematic file
file_path = "temp_uploads/City.sql"
output_path = "temp_uploads/City_sanitized.sql"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    sql_script = f.read()

print(f"Original length: {len(sql_script)}")

# Sanitize
sanitized_sql = SQLSanitizer.sanitize(sql_script)

print(f"Sanitized length: {len(sanitized_sql)}")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(sanitized_sql)
    
print(f"Saved sanitized SQL to {output_path}")

# Try to execute in memory
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
try:
    cursor.executescript(sanitized_sql)
    print("Execution SUCCESS!")
except sqlite3.Error as e:
    print(f"Execution FAILED: {e}")
finally:
    conn.close()
