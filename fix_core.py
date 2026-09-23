import re

with open('frontend/js/core.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the broken part
pattern = r'            \}\);\n        \}\)\.then\(r => r \? r\.json\(\) : null\)\.then.*?\}\);\n        \}'
replacement = r'            });\n        }'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('frontend/js/core.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')

