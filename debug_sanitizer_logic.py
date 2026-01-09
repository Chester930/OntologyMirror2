import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from db_manager_lib.core.sanitizer_tsql import TSQLSanitizerRules



file_path = r"D:\Project\OntologyMirror2\data\download sql\BuyingGroups.sql"
print(f"Reading {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("--- Testing ACTUAL FILE ---")
# Apply TSQL rules ONLY first to check intermediate state
res = TSQLSanitizerRules.apply(content)
print(f"Result (TSQL Only) tail:\n{res[-500:]}\n")

# Verify trailing comma
import re
if re.search(r',(\s*\))', res):
    print("WARNING: Trailing comma detected but regex failed to strip it?")
else:
    print("Trailing comma check: Clean (or regex passed).")
