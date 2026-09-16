import os
import re

def fix_local_logging():
    py_files = []
    for root, dirs, files in os.walk('.'):
        if '.venv' in root or '.pytest_cache' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
                
    for file_path in py_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # We look for \n    import logging\n    logging.error('Sessiz hata yakalandi
        # and replace with \n    logging.error('Sessiz hata yakalandi
        pattern = re.compile(r'(\s+)import logging\r?\n(\s+)logging\.error\(')
        new_content, count = pattern.subn(r'\n\2logging.error(', content)
        
        if count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Removed local import logging in {file_path}")

if __name__ == '__main__':
    fix_local_logging()
