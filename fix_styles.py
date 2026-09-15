import re

file_path = "ihale_motoru.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

def replacer(match):
    full_match = match.group(0)
    inner = match.group(1)
    
    if 'wordWrap' in inner:
        return full_match
        
    return f"ParagraphStyle({inner}, wordWrap='CJK')"

new_content = re.sub(r"ParagraphStyle\(([^)]+)\)", replacer, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done replacing.")
