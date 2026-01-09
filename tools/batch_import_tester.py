
import os
import sys
import sqlite3
import re
import glob

# Mock the environment to reuse logic if possible, or copy-paste the sanitizer.
# Copy-pasting the sanitizer key logic for independent verification is safer 
# to ensure we test the *Algorithm* not just the GUI coupling.

def get_sanitized_sql(sql_script, idx=0, filename="test.sql"):
    # This MUST match db_manager.py logic EXACTLY.
    # I will replicate the current logic from db_manager.py here.
    
    # A. T-SQL / MSSQL Specifics
    sql_script = re.sub(r'(?i)^\s*GO\s*$', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*PRINT\s+\'.*?\'\s*;?', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*EXEC(UTE)?\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*SET\s+IDENTITY_INSERT\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'\[\w+\]\.\[(\w+)\]', r'[\1]', sql_script) 
    sql_script = re.sub(r'\[(\w+)\]', r'\1', sql_script)

    def replace_hex(m):
        return f"X'{m.group(1)}'"
    sql_script = re.sub(r'\b0x([0-9A-Fa-f]+)\b', replace_hex, sql_script)

    sql_script = re.sub(r'(?i)^\s*DECLARE\s+@.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*SET\s+@.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*SET\s+@.*$', '', sql_script, flags=re.MULTILINE)

    # B. MySQL Commands / Schema
    sql_script = re.sub(r'(?i)^\s*(CREATE|DROP)\s+SCHEMA\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*(CREATE|DROP)\s+DATABASE\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*USE\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*(LOCK|UNLOCK)\s+TABLES.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*SET\s+.*?;', '', sql_script, flags=re.MULTILINE) 
    sql_script = re.sub(r'(?s)\/\*!.*?\*\/', '', sql_script) 
    sql_script = re.sub(r'(?i)^\s*FLUSH\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*SOURCE\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?m)^\s*#.*$', '', sql_script)

    # C. CREATE TABLE Cleanup
    sql_script = re.sub(r'(?i)\)\s*ENGINE.*?;', ');', sql_script)
    sql_script = re.sub(r'(?i)\s+AUTO_INCREMENT\b', '', sql_script)
    sql_script = re.sub(r'(?i)\bENUM\s*\(.*?\)', 'TEXT', sql_script)
    sql_script = re.sub(r'(?i)CREATE\s+OR\s+REPLACE\s+VIEW', 'CREATE VIEW', sql_script)
    sql_script = re.sub(r'(?i)\bGEOMETRY\b', 'TEXT', sql_script)
    sql_script = re.sub(r'(?i)\bGEOGRAPHY\b', 'TEXT', sql_script)
    sql_script = re.sub(r'(?i)\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP', '', sql_script)

    # D. Keys / Constraints
    lines = sql_script.split('\n')
    cleaned_lines = []
    key_pattern = re.compile(r'^\s*(UNIQUE\s+)?(KEY|INDEX|FULLTEXT\s+KEY|CONSTRAINT)\s+.*', re.IGNORECASE)
    for line in lines:
        if key_pattern.match(line):
            if 'PRIMARY KEY' not in line.upper() and 'FOREIGN KEY' not in line.upper():
                continue
        cleaned_lines.append(line)
    sql_script = '\n'.join(cleaned_lines)
    
    # E. Drop Tables Multi
    def replace_drop(m):
        tables = m.group(1).split(',')
        return '; '.join([f'DROP TABLE IF EXISTS {t.strip()}' for t in tables]) + ';'
    sql_script = re.sub(r'(?i)^\s*DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(.*?;)', replace_drop, sql_script, flags=re.MULTILINE | re.DOTALL)

    # F. Procedures / Delimiters
    sql_script = re.sub(r'(?i)^\s*DELIMITER\s+.*$', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?i)^\s*DROP\s+(FUNCTION|PROCEDURE)\s+.*?;', '', sql_script, flags=re.MULTILINE)
    sql_script = re.sub(r'(?is)CREATE\s+(FUNCTION|PROCEDURE).*?END\s*\/\/+', '', sql_script)
    sql_script = re.sub(r'\/\/+', '', sql_script)

    # G. Syntax Cleanup (Trailing Commas)
    sql_script = re.sub(r',(\s*\))', r'\1', sql_script)
    sql_script = re.sub(r"(?i)^SELECT\s+'.*?'\s+as\s+'INFO'\s*;", "", sql_script, flags=re.MULTILINE)
    
    return sql_script

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
