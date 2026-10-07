import re
with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'(<div class="tab-content" id="sekme_saglik".*?)(?=\n<div class="tab-content" id="sekme_ayarlar">)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Match found! Length:", len(match.group(1)))
else:
    print("Not found")
