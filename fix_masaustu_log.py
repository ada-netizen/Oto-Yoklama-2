import re

with open('masaustu.py', 'r', encoding='utf-8') as f:
    content = f.read()

new = '''def guncelleme_motoru_baslat() -> None:
    """Versiyon dosyasini okuyarak guncelleme kontrolunu tetikler."""
    try:
        from guncelleyici import GuncellemeMotoru
        v_path = resource_path("versiyon.txt")
        logging.info(f"Versiyon dosyasi araniyor: {v_path}")
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as vf:
                mevcut_versiyon = vf.read().strip()
            logging.info(f"Okunan mevcut versiyon: {mevcut_versiyon}")
            GuncellemeMotoru.kontrol_et(mevcut_versiyon)
        else:
            logging.error(f"versiyon.txt BULUNAMADI! Yol: {v_path}")
    except Exception as e:
        logging.error(f"Guncelleme motoru baslatilamadi: {e}")'''

content = re.sub(r'def guncelleme_motoru_baslat\(\) -> None:.*?logging\.error\(f"Guncelleme motoru baslatilamadi: \{e\}"\)', new, content, flags=re.DOTALL)

with open('masaustu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated masaustu.py")
