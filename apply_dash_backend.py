import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\routes\dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

endpoint = """
@router.get("/kritik-ogrenciler")
def kritik_ogrenciler_getir():
    conn = baglanti_al()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT sinif, no, ad_soyad, devamsizlik_ozursuz, devamsizlik_ozurlu,
                   (devamsizlik_ozursuz + devamsizlik_ozurlu) as toplam
            FROM ogrenciler
            WHERE (devamsizlik_ozursuz + devamsizlik_ozurlu) >= 10
            ORDER BY toplam DESC
        ''')
        kayitlar = c.fetchall()
        liste = []
        for k in kayitlar:
            liste.append({
                "sinif": k["sinif"],
                "no": k["no"],
                "ad_soyad": k["ad_soyad"],
                "ozursuz": k["devamsizlik_ozursuz"],
                "ozurlu": k["devamsizlik_ozurlu"],
                "toplam": k["toplam"]
            })
        return {"basarili": True, "veri": liste}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    finally:
        conn.close()
"""
if "/kritik-ogrenciler" not in content:
    content += endpoint
    with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\routes\dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("dashboard.py updated.")

