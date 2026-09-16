import re

with open('api.py', 'r', encoding='utf-8') as f:
    content = f.read()

assets_mount = """
assets_dir = resource_path_api(os.path.join('frontend', 'assets'))
if os.path.isdir(assets_dir):
    app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')
"""
if 'app.mount(\'/assets\'' not in content:
    content = content.replace("app.mount('/js'", assets_mount + "\n    app.mount('/js'")

with open('api.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Assets mounted.")
