import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find the block starting with <div class="tab-content" id="sekme_iletisim">
# and ending before {% include 'components/raporlar_modal.html' %}
match = re.search(r'(<div class="tab-content" id="sekme_iletisim">.*?)\s*{% include \'components/raporlar_modal.html\' %}', text, re.DOTALL)
if match:
    block = match.group(1)
    # Remove the block from its current position
    text = text.replace(block, '')
    # Insert it before </body>
    text = text.replace('</body>', block + '\n</body>')
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed layout")
else:
    print("Block not found")

