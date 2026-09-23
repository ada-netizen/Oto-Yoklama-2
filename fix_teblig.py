import re

with open('frontend/js/personel_teblig.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = "function personelGruplariCiz() {"
replacement = "function personelGruplariCiz() {\n            window.tumPersonelGruplari = tumPersonelGruplari;\n            window.dispatchEvent(new CustomEvent('personeller-guncellendi'));"

if "window.tumPersonelGruplari" not in text:
    text = text.replace(target, replacement)

with open('frontend/js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.write(text)
print("personel_teblig.js fixed")

