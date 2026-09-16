import re
import base64
import os

html_path = "frontend/index.html"
assets_dir = "frontend/assets"

if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r'src="(data:image/(png|jpeg|jpg);base64,([^"]+))"')
matches = pattern.findall(content)

counter = 1
for match in matches:
    full_str = match[0]
    ext = match[1]
    b64_data = match[2]
    
    filename = f"img_{counter}.{ext}"
    filepath = os.path.join(assets_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64_data))
        
    print(f"Saved {filename}")
    
    # Replace in content
    content = content.replace(f'src="{full_str}"', f'src="assets/{filename}"')
    counter += 1

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Extracted {counter-1} images. Original HTML size updated.")
