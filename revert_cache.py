import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'src="js/core\.js(\?v=[^"]+)?"', 'src="js/core.js"', text)
text = re.sub(r'src="js/personel_teblig\.js(\?v=[^"]+)?"', 'src="js/personel_teblig.js"', text)
text = re.sub(r'src="js/ihale\.js(\?v=[^"]+)?"', 'src="js/ihale.js"', text)
text = re.sub(r'src="lucide\.min\.js(\?v=[^"]+)?"', 'src="lucide.min.js"', text)
text = re.sub(r'href="style\.css(\?v=[^"]+)?"', 'href="style.css"', text)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Reverted all ?v= tags")

