
import os
import sys
import sqlite3
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_manager_lib.core.sanitizer import SQLSanitizer

def test_instpubs():
    sql_file = os.path.join(os.path.dirname(__file__), "..", "data", "download sql", "instpubs.sql")
    if not os.path.exists(sql_file):
        print(f"File not found: {sql_file}")
        return

    print(f"Testing {sql_file}...")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f: content = f.read()
    except:
        with open(sql_file, 'r', encoding='latin-1') as f: content = f.read()
    
    sanitized = SQLSanitizer.sanitize(content)
    
    # Save sanitized for inspection
    debug_path = os.path.join(os.path.dirname(__file__), "..", "data", "debug_verify_instpubs.sql")
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(sanitized)
    print(f"Sanitized SQL saved to {debug_path}")

    # Test in SQLite memory DB
    conn = sqlite3.connect(":memory:")
    # Mock REGEXP
    conn.create_function("REGEXP", 2, lambda x, y: 1 if re.search(x, y) else 0)
    cursor = conn.cursor()
    
    try:
        # SQLite executescript doesn't support parameterized queries, but we don't have them here
        cursor.executescript(sanitized)
        conn.commit()
        print("Success: SQLite executed the sanitized script without errors.")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables created: {', '.join(tables)}")
        
    except Exception as e:
        print(f"Error during execution: {e}")
        # Find the line near the error
        match = re.search(r"at line (\d+)", str(e))
        if match:
            line_no = int(match.group(1))
            lines = sanitized.splitlines()
            start = max(0, line_no - 5)
            end = min(len(lines), line_no + 5)
            print(f"Error context (lines {start+1}-{end}):")
            for i in range(start, end):
                print(f"{i+1}: {lines[i]}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_instpubs()
