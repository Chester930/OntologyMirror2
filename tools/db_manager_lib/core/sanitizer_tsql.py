import re

class TSQLSanitizerRules:
    @staticmethod
    def apply(script):
        # 0. Normalize line endings
        script = script.replace('\r\n', '\n').lstrip('\ufeff')
        
        # 1. Split into batches by GO
        batches = re.split(r'(?im)^\s*GO\s*;?\s*$', script)
        cleaned_batches = []
        
        skip_keywords = (
            'CREATE TRIGGER', 'CREATE PROCEDURE', 'CREATE PROC', 
            'CREATE FUNCTION', 'ALTER TRIGGER', 'ALTER PROCEDURE', 
            'CREATE FUNCTION', 'ALTER TRIGGER', 'ALTER PROCEDURE', 
            'ALTER PROC', 'ALTER FUNCTION', 'CREATE VIEW', 'CREATE SCHEMA', 'CREATE SEQUENCE',
            'CREATE ROLE', 'CREATE SECURITY POLICY', 'CREATE TYPE', 'ALTER TABLE',
            'IF ', 'IF(', 'ELSE', 'WHILE ', 'UPDATE STATISTICS',
            'GRANT ', 'REVOKE ', 'DENY ', 'SET ', 'DECLARE ', 
            'PRINT ', 'RAISERROR', 'CHECKPOINT', 'DBCC ', 
            'USE ', 'BACKUP ', 'RESTORE ', 'DISK ', 'ALTER DATABASE',
            'DROP DATABASE', 'CREATE DATABASE', 'DROP PROC', 'DROP PROCEDURE',
            'DROP TRIGGER', 'DROP FUNCTION', 'SELECT @', 'EXEC ', 'EXECUTE '
        )
        
        for batch in batches:
            trimmed_content = batch.strip()
            if not trimmed_content:
                continue
            
            # Remove leading comments to find meaningful code start
            # (Matches both -- and /* */ style comments at the START of the batch)
            code_start = trimmed_content
            while True:
                last_start = code_start
                # Remove -- style
                code_start = re.sub(r'^--.*?\n', '', code_start).strip()
                # Remove /* */ style
                code_start = re.sub(r'^/\*.*?\*/', '', code_start, flags=re.DOTALL).strip()
                if code_start == last_start:
                    break
            
            if not code_start:
                continue
                
            first_line = code_start.split('\n')[0].strip().upper()
            
            should_skip = False
            for kw in skip_keywords:
                if first_line.startswith(kw.upper()):
                    should_skip = True
                    break
            
            if should_skip:
                continue
            
            cleaned_batches.append(batch)
            
        # Rejoin with semicolons
        script = ';\n'.join(cleaned_batches) + ';'
        
        # 2. Global replacements for inline T-SQL
        
        # Normalize VALUE -> VALUES (for INSERT)
        # T-SQL allows INSERT INTO ... VALUE ...
        script = re.sub(r'(?is)\bINSERT\s+(?:INTO\s+)?.*?\bVALUE\s*\(', lambda m: m.group(0).replace('VALUE', 'VALUES').replace('value', 'values'), script)
        # Remove ROW(...) wrapper often used in VALUES
        # e.g. VALUES (ROW(1,2)), (ROW(3,4)) -> VALUES (1,2), (3,4)
        script = re.sub(r'(?i)\bROW\s*\(', '(', script)

        script = re.sub(r'(?i)\bgetdate\s*\(\s*\)', 'CURRENT_TIMESTAMP', script)
        script = re.sub(r'(?i)\bnewid\s*\(\s*\)', '(lower(hex(randomblob(4))) || "-" || lower(hex(randomblob(2))) || "-4" || substr(lower(hex(randomblob(2))),2) || "-" || substr("89ab",abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || "-" || lower(hex(randomblob(6))))', script)
        script = re.sub(r'(?i)\bIDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)', '', script)
        script = re.sub(r'(?i)\bIDENTITY\b', '', script)
        script = re.sub(r'(?i)\b(NON)?CLUSTERED\b', '', script)
        script = re.sub(r'(?i)\bWITH\s+ROLLUP\b', '', script)
        script = re.sub(r'(?i)\bWITH\s+ROLLUP\b', '', script)
        script = re.sub(r'(?is)\bPERIOD\s+FOR\s+SYSTEM_TIME\s*\(.*?\)', '', script)
        script = re.sub(r'(?is)\bWITH\s*\(\s*SYSTEM_VERSIONING\s*=\s*ON.*?(\)|$)', '', script)
        
        # Money literals $123.45 -> 123.45
        script = re.sub(r'(?<!\w)\$(\d+(?:\.\d+)?)', r'\1', script)
        
        # fix IDENTITY column omission in INSERT
        # Specifically for 'jobs' table in instpubs.sql
        script = re.sub(r'(?i)(INSERT\s+(?:INTO\s+)?jobs\s+values\s*\()', r'\1NULL, ', script)
        
        # 3. Helper Funcs
        script = TSQLSanitizerRules._replace_convert(script)
        script = TSQLSanitizerRules._replace_alias_assign(script)
        
        # 4. Cleanup leftover T-SQL fragments
        fragments = ('BEGIN', 'END', 'AS', 'ELSE', 'WITH LOG', 'WITH NOWAIT')
        frag_pattern = r'(?im)^\s*(?:' + '|'.join(fragments) + r')\b.*?(?=[;\n]|$)'
        script = re.sub(frag_pattern, '', script)
        
        
        # Lines starting with @
        script = re.sub(r'(?m)^\s*@\w+\b.*?(?=[;\n]|$)', '', script)
        
        # SQLCMD :setvar variables
        script = re.sub(r'(?m)^\s*:setvar.*?(?=[;\n]|$)', '', script)
        
        # 5. Syntax Cleanup
        script = re.sub(r',(\s*;)', r'\1', script)
        script = re.sub(r',(\s*\))', r'\1', script)
        script = re.sub(r',(\s*[\r\n]+\s*;)', r'\1', script)
        script = re.sub(r',(\s*[\r\n]+\s*\))', r'\1', script)
        
        # Remove empty lines
        script = '\n'.join([line for line in script.split('\n') if line.strip()])
        
        return script

    @staticmethod
    def _replace_convert(script):
        pattern = re.compile(r'(?i)\bCONVERT\s*\(')
        for _ in range(400):
            match = pattern.search(script)
            if not match: break
            start = match.end()
            depth = 1
            current = start
            comma_indices = []
            while current < len(script) and depth > 0:
                char = script[current]
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                elif char == ',' and depth == 1:
                    comma_indices.append(current)
                if depth == 0: break
                current += 1
            if depth != 0: break
            end = current
            if len(comma_indices) >= 1:
                target_type = script[start:comma_indices[0]].strip()
                expr_end = comma_indices[1] if len(comma_indices) > 1 else end
                expr = script[comma_indices[0]+1:expr_end].strip()
                if target_type.lower() == 'xml': target_type = 'TEXT'
                new_seg = f"CAST({expr} AS {target_type})"
                script = script[:match.start()] + new_seg + script[end+1:]
            else:
                break 
        return script

    @staticmethod
    def _replace_alias_assign(script):
        return re.sub(r'(?i)(,\s*|\bSELECT\s+)([a-zA-Z0-9_"\.\[\]]+)\s*=\s*', r'\1', script)
