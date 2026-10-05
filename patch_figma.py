import re

with open('frontend/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Update CSS Variables (Figma Monochrome with Pastel Accents)
new_vars = '''
        :root {
            /* Figma Base Palette */
            --bg-main: #FFFFFF;
            --bg-card: #FFFFFF;
            --bg-card-solid: #FFFFFF;
            --fg-main: #000000;
            --fg-sub: #555555;
            --border: #E5E5E5;
            --tree-sel: #000000; 
            
            /* Figma Pastel Blocks */
            --block-lime: #c7f284;
            --block-lilac: #e0c9fa;
            --block-mint: #b2f5d1;
            --block-pink: #fecaca;
            --block-cream: #fef9c3;
            --block-navy: #1e1b4b;

            --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --glass-blur: blur(0px); /* Figma doesn't use glassmorphism, it uses solid colors */
            --shadow-sm: none;
            --shadow-md: none;
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            
            --rounded-pill: 9999px;
            --rounded-lg: 24px;
            --rounded-md: 12px;
        }
        
        [data-theme="dark"] {
            /* Figma rarely does dark mode natively, but if forced, Navy/Black inversion */
            --bg-main: #000000;
            --bg-card: #111111;
            --bg-card-solid: #111111;
            --fg-main: #FFFFFF;
            --fg-sub: #A3A3A3;
            --border: #333333;
            --tree-sel: #FFFFFF;
        }
'''

# Replace root and body
css = re.sub(r':root\s*\{.*?\}', new_vars, css, flags=re.DOTALL)
css = css.replace('--bg-main: #0F172A;', '') # Clean up any manual dark mode stuff if present

# 2. Update Buttons (Pill shaped, pure black/white contrast)
css = re.sub(r'\.btn\s*\{.*?\}', 
    r'''.btn { border: 1px solid transparent; padding: 10px 20px; font-size: 13px; font-weight: 540; cursor: pointer; font-family: var(--font-ui); color: #FFFFFF; background-color: var(--fg-main); border-radius: var(--rounded-pill); display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1); letter-spacing: 0.2px; }''', css, flags=re.DOTALL)

css = re.sub(r'\.btn:hover\s*\{.*?\}', 
    r'''.btn:hover { transform: scale(1.02); }''', css, flags=re.DOTALL)

# Remove old button specific colors to force monochrome or precise Figma buttons
css = re.sub(r'\.btn-yardim.*?(?=\n)', '', css)
css = re.sub(r'\.btn-ayarlar.*?(?=\n)', '', css)
css = re.sub(r'\.btn-gece.*?(?=\n)', '', css)
css = re.sub(r'\.btn-rapor.*?(?=\n)', '', css)
css = re.sub(r'\.btn-dev.*?(?=\n)', '', css)
css = re.sub(r'\.btn-ogr.*?(?=\n)', '', css)
css = re.sub(r'\.btn-kirmizi.*?(?=\n)', '', css)
css = re.sub(r'\.btn-temizle.*?(?=\n)', '.btn-temizle { background-color: transparent; color: var(--fg-main); border: 1px solid var(--border); padding: 6px 16px; border-radius: var(--rounded-pill); } .btn-temizle:hover { border-color: var(--fg-main); }', css)

# Make top-bar purely white with black text and simple bottom border
css = re.sub(r'\.top-bar\s*\{.*?\}', 
    r'''.top-bar { background-color: var(--bg-main); border-bottom: 2px solid var(--fg-main); padding: 15px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-radius: 0; box-shadow: none; }''', css, flags=re.DOTALL)
css = re.sub(r'\.top-bar-title\s*\{.*?\}', 
    r'''.top-bar-title { font-size: 24px; font-weight: 700; color: var(--fg-main); margin: 0; display:flex; align-items:center; gap:12px; letter-spacing: -0.5px; }''', css, flags=re.DOTALL)

# Notebook Tabs (Figma Nav)
css = re.sub(r'\.notebook-header\s*\{.*?\}', 
    r'''.notebook-header { display: flex; background-color: var(--bg-main); border-bottom: 2px solid var(--fg-main); padding: 0 20px; align-items: center; height: 56px; gap: 15px; }''', css, flags=re.DOTALL)
css = re.sub(r'\.tab-btn\s*\{.*?\}', 
    r'''.tab-btn { background-color: transparent; color: var(--fg-sub); border: none; padding: 0 10px; height: 100%; cursor: pointer; font-family: var(--font-ui); font-size: 14px; font-weight: 540; display: flex; align-items: center; gap: 8px; transition: color 0.2s; }''', css, flags=re.DOTALL)
css = re.sub(r'\.tab-btn\.aktif\s*\{.*?\}', 
    r'''.tab-btn.aktif { color: var(--fg-main); border-bottom: 3px solid var(--fg-main); }''', css, flags=re.DOTALL)

# Tree Card (Figma Color Blocks)
css = re.sub(r'\.tree-card\s*\{.*?\}', 
    r'''.tree-card { background-color: var(--bg-card); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); flex: 1; overflow-y: auto; box-shadow: 4px 4px 0px var(--fg-main); padding: 10px; }''', css, flags=re.DOTALL)

# Tablo secili satir (Primary color selection)
css = re.sub(r'\.tr-secili\s*\{.*?\}', 
    r'''.tr-secili { background-color: var(--fg-main) !important; color: var(--bg-main) !important; font-weight: 540; }''', css, flags=re.DOTALL)

with open('frontend/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

# Update index.html to wrap contents in Figma color blocks
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Apply pastel backgrounds to specific main elements
html = html.replace('<div id="sol_panel_ana" style="flex: 0 0 360px; display: flex; flex-direction: column; background-color: var(--bg-main);">', 
                    '<div id="sol_panel_ana" style="flex: 0 0 360px; display: flex; flex-direction: column; background-color: var(--block-lilac); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 15px; box-shadow: 4px 4px 0px var(--fg-main);">')
html = html.replace('<div class="filtre-card" style="background-color: var(--bg-card); border: 1px solid var(--border); padding: 15px 10px; margin-bottom: 10px; display: flex; justify-content: center;">',
                    '<div class="filtre-card" style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-pill); padding: 10px 20px; margin-bottom: 15px; display: flex; justify-content: center;">')

# Adjust inputs
html = html.replace('style="background-color: var(--bg-card); border: 1px solid var(--border); color: var(--fg-main); padding: 4px 5px; font-size: 10px; width: 180px;"',
                    'style="background-color: var(--bg-main); border: none; border-bottom: 2px solid var(--fg-main); color: var(--fg-main); padding: 8px; font-size: 12px; width: 180px; font-weight: 540; outline: none;"')
html = html.replace('style="background-color: var(--bg-card); border: 1px solid var(--border); color: var(--fg-main); padding: 3px; font-size: 10px; width: 90px;"',
                    'style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-pill); color: var(--fg-main); padding: 6px 12px; font-size: 12px; font-weight: 540; outline: none;"')

# Teblig tab styling
html = html.replace('<div id="sag_panel" style="flex: 1; display: flex; flex-direction: column; background-color: var(--bg-main);">',
                    '<div id="sag_panel" style="flex: 1; display: flex; flex-direction: column; background-color: var(--block-lime); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 15px; box-shadow: 4px 4px 0px var(--fg-main);">')
html = html.replace('<div class="tree-card" style="background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 15px;">',
                    '<div class="tree-card" style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 30px; display: flex; flex-direction: column; gap: 20px; box-shadow: none;">')

# Change dashboard kpi blocks
html = html.replace('background: linear-gradient(135deg, #f59e0b, #d97706);', 'background: var(--block-mint); color: var(--fg-main); border: 2px solid var(--fg-main);')
html = html.replace('background: linear-gradient(135deg, #ef4444, #b91c1c);', 'background: var(--block-pink); color: var(--fg-main); border: 2px solid var(--fg-main);')
html = html.replace('background: linear-gradient(135deg, #10b981, #059669);', 'background: var(--block-lime); color: var(--fg-main); border: 2px solid var(--fg-main);')
html = html.replace('background: linear-gradient(135deg, #3b82f6, #2563eb);', 'background: var(--block-lilac); color: var(--fg-main); border: 2px solid var(--fg-main);')

# Theme switch button design fix
html = html.replace('<div class="tema-switch"', '<div class="tema-switch" style="border: 2px solid var(--fg-main); border-radius: var(--rounded-pill);" ')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
