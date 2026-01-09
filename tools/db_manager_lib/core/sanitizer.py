import re
# No change needed for relative imports: from .sanitizer_tsql import ...
# But verify content first.
from .sanitizer_tsql import TSQLSanitizerRules
from .sanitizer_schema import SchemaSanitizerRules

class SQLSanitizer:
    @staticmethod
    def sanitize(sql_script):
        # 1. T-SQL / MSSQL Specifics
        sql_script = TSQLSanitizerRules.apply(sql_script)

        # 2. Handle INSERT INTO
        # FIX: T-SQL allows INSERT "Table", SQLite requires INSERT INTO "Table"
        sql_script = re.sub(r'(?i)(?<=^)\s*INSERT\s+(?!INTO\b)\s*("[\w\s]+"|\[[\w\s]+\]|[\w]+)', r'INSERT INTO \1', sql_script, flags=re.MULTILINE)
        sql_script = re.sub(r'(?i)\bINSERT\s+(?!INTO\b)\s*("[\w\s]+"|\[[\w\s]+\]|[\w]+)', r'INSERT INTO \1', sql_script)
        # Semicolon insertion
        sql_script = re.sub(r'(?i)([^;])(\s*[\r\n]+\s*)(INSERT\s+INTO\b)', r'\1\2; \3', sql_script)

        # 3. Special Literals
        # Hex
        def replace_hex(m): return f"X'{m.group(1)}'"
        sql_script = re.sub(r'\b0x([0-9A-Fa-f]+)\b', replace_hex, sql_script)
        # Unicode N'...'
        sql_script = re.sub(r"N'([^']*)'", r"'\1'", sql_script)
        sql_script = re.sub(r"(?<![a-zA-Z0-9_])N(')", r"\1", sql_script)
        # IDENTITY
        sql_script = re.sub(r'(?i)\bIDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)', '', sql_script) 
        sql_script = re.sub(r'(?i)\bIDENTITY\b', '', sql_script)

        # 4. MySQL Basics
        sql_script = re.sub(r'(?i)^\s*(CREATE|DROP)\s+DATABASE\s+.*?;', '', sql_script, flags=re.MULTILINE)
        sql_script = re.sub(r'(?i)^\s*USE\s+.*?;', '', sql_script, flags=re.MULTILINE)
        sql_script = re.sub(r'(?i)^\s*(LOCK|UNLOCK)\s+TABLES.*?;', '', sql_script, flags=re.MULTILINE)
        sql_script = re.sub(r'(?m)^\s*#.*$', '', sql_script)

        # 5. Schema & DDL
        sql_script = SchemaSanitizerRules.apply(sql_script)

        return sql_script
