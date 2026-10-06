import glob
import re

for f in glob.glob('*.py') + glob.glob('routes/*.py'):
    try:
        with open(f, encoding='utf-8-sig', errors='ignore') as fp:
            c = fp.read()
        m = re.findall(r'@(?:app|router)\.(?:delete|post|get|put)\([\"\'](.*?)[\"\']', c)
        if m:
            print(f, m)
    except: pass
