import re
with open('routes/pdf.py', 'r', encoding='utf-8') as f:
    content = f.read()

# For bireysel teblig
content = re.sub(
    r'(motor\.bireysel_teblig_ciz.*?yuklenen_pdf\)\n\s*dosyayi_otomatik_ac\(yol\))',
    r'\1\n                evrak_kaydet("Yazı Tebliği", veri.edilen.ad, veri.edilen.brans)',
    content,
    flags=re.DOTALL
)

# For toplu teblig
content = re.sub(
    r'(motor\.teblig_tebellug_ciz.*?yuklenen_pdf\)\n\s*dosyayi_otomatik_ac\(yol\))',
    r'\1\n                for p in veri.personeller:\n                    evrak_kaydet("Yazı Tebliği", p.ad, p.brans)',
    content,
    flags=re.DOTALL
)

with open('routes/pdf.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('routes/ihale.py', 'r', encoding='utf-8') as f:
    ihale = f.read()

# For ihale
ihale = re.sub(
    r'(sonuc_dosyasi = ihale_motoru\.belge_uret\(veri, pdf_yol\)\n\s*dosyayi_otomatik_ac\(sonuc_dosyasi\))',
    r'\1\n        for p in veri.komisyon_uyeleri:\n            evrak_kaydet("İhale Komisyonu", p.ad, p.brans)',
    ihale,
    flags=re.DOTALL
)

with open('routes/ihale.py', 'w', encoding='utf-8') as f:
    f.write(ihale)

print("Updated routes.")
