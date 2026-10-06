import re

def fix_pdf():
    with open('routes/pdf.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find where the PDF is drawn
    old_line = "motor.veli_formu_ciz(veri.no, veri.ad, veri.sube, kayitlar_islenmis, kayit_yeri, veri.ozurlu_str, veri.ozursuz_str)"
    new_line = old_line + "\n                evrak_kaydet(\"Devamsızlık Mektubu\", veri.ad, veri.sube)"
    
    if old_line in content and "evrak_kaydet(\"Devamsızlık Mektubu\"" not in content:
        content = content.replace(old_line, new_line)

    with open('routes/pdf.py', 'w', encoding='utf-8') as f:
        f.write(content)

fix_pdf()
