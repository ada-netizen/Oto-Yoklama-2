import codecs

filepath = 'frontend/components/personel_yonetim_modal.html'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

if text.startswith('\ufeff'):
    text = text[1:]

try:
    fixed_text = text.encode('cp1252').decode('utf-8')
    print("Encoding fixed via cp1252")
except Exception as e:
    print("Error fixing encoding cp1252:", e)
    fixed_text = text

fixed_text = fixed_text.replace(
    "arama: '',\n        aktifFiltre: 'Tümü',",
    "arama: '',\n        aktifFiltre: 'Tümü',\n        \n        init() {\n            window.addEventListener('personeller-guncellendi', () => {\n                this.arama = this.arama;\n            });\n        },"
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed_text)
print("personel_yonetim_modal.html fixed completely")

