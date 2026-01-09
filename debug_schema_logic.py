import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from db_manager_lib.core.sanitizer import SQLSanitizer

file_path = r"D:\Project\OntologyMirror2\data\download sql\BuyingGroups.sql"
print(f"Reading {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("--- RAW CONTENT ---")
# print(content[:200])

print("\n--- FULL SANITIZATION ---")
res = SQLSanitizer.sanitize(content)
print(f"Result tail repr:\n{repr(res[-500:])}\n")

import sqlite3

import sqlite3

print("\n--- SQLITE EXECUTION OF FULL RESULT ---")
conn = sqlite3.connect(":memory:")
try:
    conn.executescript(res)
    print("SUCCESS: Full SQL executed in SQLite")
except Exception as e:
    print(f"FAIL: SQLite Error: {e}")
    # Print near the end to see
    lines = res.split('\n')
    for i, line in enumerate(lines[-15:]):
        print(f"{len(lines)-15+i+1}: {line}")

print("\n--- ISOLATED TEST: QUOTED CONSTRAINT ---")
try:
    conn.execute('CREATE TABLE t3 (col INT CONSTRAINT "df_name" NOT NULL)')
    print("SUCCESS: QUOTED CONSTRAINT executed in SQLite")
except Exception as e:
    print(f"FAIL: QUOTED CONSTRAINT Error: {e}")

print("\n--- LINE-BY-LINE RECONSTRUCTION ---")
lines = [
    'CREATE TABLE "BuyingGroups" (',
    '    "BuyingGroupID"   INT                                         CONSTRAINT "DF_Sales_BuyingGroups_BuyingGroupID"  NOT NULL,',
    '    "BuyingGroupName" NVARCHAR (50)                               NOT NULL,',
    '    "LastEditedBy"    INT                                         NOT NULL,',
    '    "ValidFrom"       DATETIME2 (7)  NOT NULL,',
    '    "ValidTo"         DATETIME2 (7)    NOT NULL,',
    '    CONSTRAINT "PK_Sales_BuyingGroups" PRIMARY KEY  ("BuyingGroupID" ASC),',
    '    CONSTRAINT "FK_Sales_BuyingGroups_Application_People" FOREIGN KEY ("LastEditedBy") REFERENCES "People" ("PersonID")',
    ')'
]

current_sql = ""
conn = sqlite3.connect(":memory:")
# Mock dependency table
conn.execute('CREATE TABLE "People" ("PersonID" INT PRIMARY KEY)')

try:
    for i in range(len(lines)):
        # Construct valid SQL up to this point (handling closing paren if needed check)
        # Actually, simpler: define the query with N lines.
        # But we need close paren.
        
        # Test full table
        full_sql = "\n".join(lines)
        print("Executing exact reconstruction...")
        conn.execute(full_sql)
        print("SUCCESS: Exact reconstruction executed")
        break
except Exception as e:
    print(f"FAIL: Reconstruction Error: {e}")

conn.close()
