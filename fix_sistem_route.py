with open('routes/sistem.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith('@router.get("/versiyon")'):
        start_idx = i
    if start_idx != -1 and i > start_idx and line.startswith('@router.get("/islem-durumu/'):
        end_idx = i
        break

new_func = [
    '@router.get("/versiyon")\n',
    'def versiyon_getir():\n',
    '    import sys, os, logging\n',
    '    from pathlib import Path\n',
    '    try:\n',
    '        base_path = Path(sys._MEIPASS)\n',
    '    except Exception:\n',
    '        base_path = Path(__file__).resolve().parent.parent\n',
    '    try:\n',
    '        v_path = base_path / "versiyon.txt"\n',
    '        with open(v_path, "r", encoding="utf-8") as f:\n',
    '            v = f.read().strip()\n',
    '            if not v: raise ValueError("versiyon.txt bos")\n',
    '            return {"versiyon": v}\n',
    '    except Exception as e:\n',
    '        logging.error(f"versiyon.txt okunamadi. Hata: {e}")\n',
    '        return {"versiyon": "v2.0"}\n',
    '\n'
]

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + new_func + lines[end_idx:]
    with open('routes/sistem.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Sistem.py güncellendi.")
else:
    print("Bulunamadı")
