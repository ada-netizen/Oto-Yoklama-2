import re
with open('veritabani.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add table creation
old_init = 'cursor.execute("CREATE INDEX IF NOT EXISTS idx_personel_ad ON personel (ad_soyad)")\n        conn.commit()'
new_init = 'cursor.execute("CREATE INDEX IF NOT EXISTS idx_personel_ad ON personel (ad_soyad)")\n        cursor.execute("CREATE TABLE IF NOT EXISTS uretilen_evraklar (id INTEGER PRIMARY KEY AUTOINCREMENT, tur TEXT, personel_ad TEXT, brans TEXT, tarih TEXT)")\n        conn.commit()'
if old_init in content:
    content = content.replace(old_init, new_init)
else:
    print("Could not find old_init")

# Update sifirla
content = re.sub(
    r'(def sifirla\(self\):.*?self\.cursor\.execute\("DELETE FROM devamsizliklar"\))',
    r'\1\n        self.cursor.execute("DELETE FROM uretilen_evraklar")',
    content,
    flags=re.DOTALL
)

with open('veritabani.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("DB updated.")
