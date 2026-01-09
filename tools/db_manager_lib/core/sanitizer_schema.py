import re

class SchemaSanitizerRules:
    @staticmethod
    def apply(script):
        # 0. Remove Constraints FIRST (to avoid syntax cleanup corrupting literals like '[FM]')
        script = SchemaSanitizerRules._clean_check_constraints(script)

        # 1. Clean up Syntax
        script = re.sub(r'\[\w+\]\.\[(\w+)\]', r'[\1]', script)
        script = re.sub(r'\[\w+\]\.(\w+)', r'"\1"', script) 
        script = re.sub(r'\b\w+\.\[(\w+)\]', r'[\1]', script)
        script = re.sub(r'\[\w+\]\.\[\w+\]\.\[(\w+)\]', r'[\1]', script)
        script = re.sub(r'\[(\w+)\]', r'"\1"', script)
        script = re.sub(r'"dbo"\."(\w+)"', r'"\1"', script)
        
        # 2. Types
        type_list = ["int", "nvarchar", "datetime", "image", "ntext", "money", "smallint", "real", "bit", "tinyint", "float", "decimal", "char", "varchar", "date", "time"]
        for t in type_list:
            script = re.sub(f'"{t}"', t, script, flags=re.IGNORECASE)
            
        script = re.sub(r'(?i)\bGEOMETRY\b', 'TEXT', script)
        script = re.sub(r'(?i)\bGEOGRAPHY\b', 'TEXT', script)
        script = re.sub(r'(?i)\bHIERARCHYID\b', 'TEXT', script)
        script = re.sub(r'(?i)N?VARCHAR\s*\(\s*MAX\s*\)', 'TEXT', script)
        script = re.sub(r'(?i)VARBINARY\s*\(\s*MAX\s*\)', 'BLOB', script)
        
        # 3. Table Options
        script = re.sub(r'(?i)\)\s*ENGINE.*?;', ');', script)
        script = re.sub(r'(?i)\s+AUTO_INCREMENT\b', '', script)
        script = re.sub(r'(?i)\s+ON\s+UPDATE\s+CURRENT_TIMESTAMP', '', script)
        script = re.sub(r'(?i)\b(NON)?CLUSTERED\b', '', script)
        script = re.sub(r'(?i)CHECK\s+CONSTRAINT\s+\[.*?\]', '', script)
        script = re.sub(r'(?i)\bWITH\s*\(.*?\)', '', script)
        script = re.sub(r'(?i)\)\s*ON\s+("PRIMARY"|\[PRIMARY\]|PRIMARY)', ')', script)
        
        # Remove GENERATED ALWAYS AS ROW START/END
        script = re.sub(r'(?i)\bGENERATED\s+ALWAYS\s+AS\s+ROW\s+(START|END)\b', '', script)
        # Remove NEXT VALUE FOR defaults
        script = re.sub(r'(?i)DEFAULT\s*\(\s*NEXT\s+VALUE\s+FOR\s+.*?\)', '', script)

        # 4. Keys/Indexes/Constraints
        script = SchemaSanitizerRules._clean_create_statements(script)
        script = SchemaSanitizerRules._clean_drop_statements(script)
        # _clean_check_constraints moved to top
        
        # 5. Final Syntax Cleanup (Dangling commas after removals)
        script = re.sub(r',(\s*\))', r'\1', script)
        script = re.sub(r',(\s*;)', r'\1', script)
        
        # Fix potential double closing parens artifacts
        script = re.sub(r'\)\s*[\r\n]+\s*\);', ');', script)
        
        # Remove computed columns: "ColumnName AS (Expression) [PERSISTED]"
        script = re.sub(r'(?i)\bAS\s+\(.*?\)(\s+PERSISTED)?(?=\s*,|\s*$)', '', script, flags=re.MULTILINE)

        # Remove INCLUDE (...) from indexes
        script = re.sub(r'(?i)\bINCLUDE\s*\(.*?\)', '', script)
        
        return script

    @staticmethod
    def _clean_create_statements(script):
        # Filter lines for unsupported KEYs
        lines = script.split('\n')
        cleaned = []
        key_pattern = re.compile(r'^\s*(UNIQUE\s+)?(KEY|INDEX|FULLTEXT\s+KEY|CONSTRAINT)\s+.*', re.IGNORECASE)
        for line in lines:
            if key_pattern.match(line):
                if 'PRIMARY KEY' not in line.upper() and 'FOREIGN KEY' not in line.upper(): continue
            cleaned.append(line)
        script = '\n'.join(cleaned)
        
        # Create Index fixes
        def replace_create_index(m):
            unique = (m.group(1) or "").strip()
            if unique: unique += " "
            idx_name = m.group(2)
            table_name = m.group(3)
            cols = m.group(4)
            table_name = re.sub(r'^("?\[?\w+\]?"?)\.', '', table_name)
            clean_idx = idx_name.replace('"', '').replace('[', '').replace(']', '')
            clean_tbl = table_name.replace('"', '').replace('[', '').replace(']', '')
            if not clean_idx.lower().startswith(clean_tbl.lower()):
                new_idx_name = f'"{clean_tbl}_{clean_idx}"'
            else:
                new_idx_name = idx_name
            return f"CREATE {unique}INDEX IF NOT EXISTS {new_idx_name} ON {table_name} {cols}"

        script = re.sub(r'(?i)CREATE\s+(UNIQUE\s+)?(?:\b(?:NON)?CLUSTERED\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS\s+)([\w"\[\]]+)\s+ON\s+(.+?)\s*(\(.*?\))', replace_create_index, script)
        return script

    @staticmethod
    def _clean_drop_statements(script):
        # Convert Drop to If Exists
        script = re.sub(r'(?i)^\s*DROP\s+INDEX\s+[\w"]+\.([\w"]+)', r'DROP INDEX IF EXISTS \1', script, flags=re.MULTILINE)
        
        def replace_drop_table(m):
            tables = m.group(1).split(',')
            cleaned_tables = [re.sub(r'^("?\[?\w+\]?"?)\.', '', t.strip()) for t in tables]
            return '; '.join([f'DROP TABLE IF EXISTS {t}' for t in cleaned_tables]) + ';'
        script = re.sub(r'(?i)^\s*DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(.*?)(?:;|$)', replace_drop_table, script, flags=re.MULTILINE | re.DOTALL)
        return script

    @staticmethod
    def _clean_check_constraints(script):
        # Remove LIKE '[...]' checks
        # check_regex ... (Disabled as fragile)
        # script = re.sub(check_regex, "", script, flags=re.MULTILINE | re.DOTALL)
        
        # Remove [FM] patterns via Robust Balanced Parser
        script = SchemaSanitizerRules.remove_check_with_pattern(script, r'(?:\[FM\]|\"FM\")')

        # Remove other LIKE '[...]' patterns via Parser (e.g. range checks)
        # Matches: LIKE '...[...]' inside a CHECK block
        script = SchemaSanitizerRules.remove_check_with_pattern(script, r'LIKE\s*[\'\"].*?\[.*?\]')
        
        return script

    @staticmethod
    def remove_check_with_pattern(script, pattern_str):
        # (Copied from original db_manager.py: Robust Balanced Parser)
        lower_script = script.lower()
        check_indices = [m.start() for m in re.finditer(r'(?i)\bCHECK\s*\(', script)]
        
        for start_pos in reversed(check_indices):
            open_paren_idx = script.find('(', start_pos)
            if open_paren_idx == -1: continue
            depth = 1
            current = open_paren_idx + 1
            end_pos = -1
            while current < len(script):
                char = script[current]
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                if depth == 0:
                    end_pos = current + 1
                    break
                current += 1
            if end_pos != -1:
                block = script[start_pos:end_pos]
                if re.search(pattern_str, block, re.IGNORECASE):
                    prefix_remove_start = start_pos
                    pre_chunk = script[:start_pos]
                    constraint_match = re.search(r'(?i)CONSTRAINT\s+[\w\[\]"\'`]+\s*$', pre_chunk)
                    if constraint_match: prefix_remove_start = constraint_match.start()
                    script = script[:prefix_remove_start] + script[end_pos:]
        
        # Remove computed columns: "ColumnName AS (Expression)"
        script = re.sub(r'(?i)\bAS\s+\(.*?\)(?=\s*,|\s*$)', '', script, flags=re.MULTILINE)
        
        return script
