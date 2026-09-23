import re

with open('frontend/js/core.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix ogrenciler-guncellendi event
text = text.replace(
    "document.dispatchEvent(new CustomEvent('ogrenciler-guncellendi'));",
    "window.dispatchEvent(new CustomEvent('ogrenciler-guncellendi'));"
)

# Add personeller-guncellendi event
personelleriYukle_str = "if (typeof yonetimPersonelTablosunuDoldur === 'function') yonetimPersonelTablosunuDoldur();\n            });"
new_personelleriYukle_str = "if (typeof yonetimPersonelTablosunuDoldur === 'function') yonetimPersonelTablosunuDoldur();\n                window.dispatchEvent(new CustomEvent('personeller-guncellendi'));\n            });"
text = text.replace(personelleriYukle_str, new_personelleriYukle_str)

with open('frontend/js/core.js', 'w', encoding='utf-8') as f:
    f.write(text)
print("core.js fixed")

