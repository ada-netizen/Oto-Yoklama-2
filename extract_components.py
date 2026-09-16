import os
import re

html_path = "frontend/index.html"
components_dir = "frontend/components"
if not os.path.exists(components_dir):
    os.makedirs(components_dir)

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Try to find modal blocks. 
# Modals are typically: <div id="something_modal" class="modal-overlay">...</div> (but they can be nested)
# Since parsing nested HTML with regex is hard, I will use BeautifulSoup.

from bs4 import BeautifulSoup

soup = BeautifulSoup(content, 'html.parser')

modals = soup.find_all('div', class_='modal-overlay')
drawer = soup.find_all('div', class_='drawer-overlay')

extracted_components = {}

for modal in modals:
    id_name = modal.get('id')
    if id_name:
        filename = f"{id_name}.html"
        extracted_components[id_name] = str(modal)
        
        with open(os.path.join(components_dir, filename), "w", encoding="utf-8") as f:
            f.write(str(modal))
        
        # Replace the modal in original soup with a Jinja include
        jinja_tag = f"{{% include 'components/{filename}' %}}"
        modal.replace_with(jinja_tag)

for draw in drawer:
    id_name = draw.get('id')
    if id_name:
        filename = f"{id_name}.html"
        extracted_components[id_name] = str(draw)
        
        with open(os.path.join(components_dir, filename), "w", encoding="utf-8") as f:
            f.write(str(draw))
            
        jinja_tag = f"{{% include 'components/{filename}' %}}"
        draw.replace_with(jinja_tag)

# Save the updated index.html
# Wait, BeautifulSoup might mess up the HTML formatting and custom tags if we just str(soup).
# Let's see if we can do this carefully using string replacement instead.

with open(html_path, "w", encoding="utf-8") as f:
    # bs4 removes some original formatting, but for a webview it's usually fine.
    # However, replacing exactly might be safer.
    # We'll just write the soup back. We need to replace the encoded Jinja tags back because bs4 might escape them.
    out_html = str(soup)
    # bs4 will turn {% include ... %} into &lt;% include ... %&gt; if we inserted it as string,
    # wait, I just inserted the string. Let's fix that.
    out_html = out_html.replace("&lt;%", "{%").replace("%&gt;", "%}")
    out_html = out_html.replace("{% include", "{% include").replace("%}", "%}")
    
    f.write(out_html)

print(f"Extracted {len(extracted_components)} components.")
