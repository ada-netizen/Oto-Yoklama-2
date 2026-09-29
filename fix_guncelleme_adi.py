with open('guncelleyici.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'hedef = os.path.join(klasor, "Elektronik_Okul_V2.0_guncelleme.exe")'
new = 'v_name = manifest["version"].replace(".", "_")\n    hedef = os.path.join(klasor, f"Elektronik_Okul_{v_name}_guncelleme.exe")'

if old in content:
    content = content.replace(old, new)
    with open('guncelleyici.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed updater filename")
else:
    print("Not found")
