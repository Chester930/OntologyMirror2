
import os
import sys
import sqlite3
import re
import glob

# Mock the environment to reuse logic if possible, or copy-paste the sanitizer.
# Copy-pasting the sanitizer key logic for independent verification is safer 
# to ensure we test the *Algorithm* not just the GUI coupling.

from db_manager_lib.core.sanitizer import SQLSanitizer

def get_sanitized_sql(sql_script, idx=0, filename="test.sql"):
    return SQLSanitizer.sanitize(sql_script)

def test_imports():
    root_dir = os.path.join(os.path.dirname(__file__), "..", "data", "download sql")
    sql_files = glob.glob(os.path.join(root_dir, "**", "*.sql"), recursive=True)
    
    print(f"Testing {len(sql_files)} SQL files...")
    
    passed = 0
    failed = 0
    skipped_empty = 0
    
    failures = []

    for fp in sql_files:
        try:
            with open(fp, 'r', encoding='utf-8') as f: content = f.read()
        except:
            try:
                with open(fp, 'r', encoding='latin-1') as f: content = f.read()
            except:
                failures.append((os.path.basename(fp), "Read Error"))
                failed += 1
                continue
        
        sanitized = get_sanitized_sql(content, filename=os.path.basename(fp))
        
        # Test generic validity in SQLite memory DB
        conn = sqlite3.connect(":memory:")
        # Mock REGEXP
        conn.create_function("REGEXP", 2, lambda x, y: 1 if re.search(x, y) else 0)
        cursor = conn.cursor()
        
        try:
            cursor.executescript(sanitized)
            conn.commit()
            
            # Check if any tables created? Not strictly required for success
            # procedural scripts might do nothing.
            passed += 1
        except Exception as e:
            # Check if it's "not an error" (e.g. empty)
            if not sanitized.strip():
                skipped_empty += 1
            else:
                failures.append((os.path.basename(fp), str(e)))
                failed += 1
        finally:
            conn.close()
            
    print(f"\nTotal: {len(sql_files)}")
    print(f"Passed: {passed}")
    print(f"Skipped (Sanitized to empty): {skipped_empty}")
    print(f"Failed: {failed}")
    
    if failures:
        print("\n=== Failures ===")
        for name, err in failures[:20]: # Show top 20
            print(f"[{name}] {err}")

if __name__ == "__main__":
    test_imports()
