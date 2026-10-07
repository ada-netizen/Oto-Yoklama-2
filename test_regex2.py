import re
with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'(<div class="tab-content" id="sekme_dashboard".*?)(?=\n<div class="tab-content" id="sekme_saglik">)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Match found for dashboard! Length:", len(match.group(1)))
    # find where to insert
    kpi_end = match.group(1).find("<!-- MAIN CHARTS (ROW 1) -->")
    print("MAIN CHARTS found at:", kpi_end)
else:
    print("Not found")
