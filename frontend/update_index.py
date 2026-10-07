import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'js/saglik\.js\?v=\d+', 'js/saglik.js?v=8', content)

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("index.html updated successfully.")
