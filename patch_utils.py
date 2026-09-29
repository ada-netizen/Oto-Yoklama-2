import re
with open('utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''def evrak_kaydet(tur, personel_ad, brans):
    try:
        from dependencies import db
        from datetime import datetime
        db.cursor.execute("INSERT INTO uretilen_evraklar (tur, personel_ad, brans, tarih) VALUES (?, ?, ?, ?)", (tur, personel_ad, brans, datetime.now().isoformat()))
        db.conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Evrak loglanamadi: {e}")

def log_islem(islem: str, durum: str = "basarili", detay: str = ""):'''

content = content.replace('def log_islem(islem: str, durum: str = "basarili", detay: str = ""):', new_func)

with open('utils.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated utils.py")
