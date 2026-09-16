import os
import re

def fix_except_pass():
    py_files = []
    for root, dirs, files in os.walk('.'):
        if '.venv' in root or '.pytest_cache' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
                
    pattern = re.compile(r'(except\s+Exception(?:\s+as\s+(\w+))?:)\s+pass', re.MULTILINE)
    pattern_bare = re.compile(r'(except:)\s+pass', re.MULTILINE)
    
    for file_path in py_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        
        # Function to replace 'except Exception:' or 'except Exception as e:' + 'pass'
        def repl(match):
            indent = ""
            lines = content[:match.start()].split('\n')
            if lines:
                last_line = lines[-1]
                indent = last_line[:len(last_line) - len(last_line.lstrip())]
            
            exc_var = match.group(2)
            if not exc_var:
                return f"except Exception as e:\n{indent}    import logging\n{indent}    logging.error(f'Sessiz hata yakalandi: {{e}}', exc_info=True)"
            else:
                return f"except Exception as {exc_var}:\n{indent}    import logging\n{indent}    logging.error(f'Sessiz hata yakalandi: {{{exc_var}}}', exc_info=True)"
                
        def repl_bare(match):
            indent = ""
            lines = content[:match.start()].split('\n')
            if lines:
                last_line = lines[-1]
                indent = last_line[:len(last_line) - len(last_line.lstrip())]
            return f"except Exception as e:\n{indent}    import logging\n{indent}    logging.error(f'Sessiz hata yakalandi: {{e}}', exc_info=True)"
            
        new_content, count = pattern.subn(repl, content)
        new_content, count2 = pattern_bare.subn(repl_bare, new_content)
        
        if count > 0 or count2 > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {count + count2} occurrences in {file_path}")

if __name__ == '__main__':
    fix_except_pass()
