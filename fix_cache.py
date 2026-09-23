import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace css
text = re.sub(r'href="style\.css(\?v=[0-9]+)?"', 'href="style.css?v={{ ts }}"', text)

# Replace js
text = re.sub(r'src="js/core\.js(\?v=[0-9]+)?"', 'src="js/core.js?v={{ ts }}"', text)
text = re.sub(r'src="js/personel_teblig\.js(\?v=[0-9]+)?"', 'src="js/personel_teblig.js?v={{ ts }}"', text)
text = re.sub(r'src="js/ihale\.js(\?v=[0-9]+)?"', 'src="js/ihale.js?v={{ ts }}"', text)
text = re.sub(r'src="lucide\.min\.js(\?v=[0-9]+)?"', 'src="lucide.min.js?v={{ ts }}"', text)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Cache busting applied to index.html")

