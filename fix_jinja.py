import re

with open('api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Jinja2Templates import
if 'Jinja2Templates' not in content:
    content = content.replace('from fastapi.responses import FileResponse', 'from fastapi.responses import FileResponse, HTMLResponse\nfrom fastapi.templating import Jinja2Templates\nfrom fastapi import Request')

# Setup templates
if 'templates =' not in content:
    templates_code = "\n# Jinja2 Templates\ntemplates = Jinja2Templates(directory=resource_path_api('frontend'))\n"
    content = content.replace("js_dir = resource_path_api(os.path.join('frontend', 'js'))", templates_code + "js_dir = resource_path_api(os.path.join('frontend', 'js'))")

# Modify read_index to use templates
old_index = """@app.get('/')
def read_index():
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return FileResponse(resource_path_api(os.path.join('frontend', 'index.html')), headers=headers)"""

new_index = """@app.get('/', response_class=HTMLResponse)
async def read_index(request: Request):
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return templates.TemplateResponse("index.html", {"request": request}, headers=headers)"""

content = content.replace(old_index, new_index)

with open('api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated api.py to use Jinja2Templates.")
