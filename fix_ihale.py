import re
p='frontend/js/ihale.js'
c=open(p, encoding='utf-8').read()
c=re.sub(r'(?s)function personelSecimEkraniAc\(gorevId\) \{.*?function personelAta\(ad\)', 'function personelSecimEkraniAc(gorevId) {\n    secimIcinGorevId = gorevId;\n    document.getElementById(\'personel_havuz_modal\').style.display = \'flex\';\n    setTimeout(() => { let el = document.getElementById(\'personel_arama_input\'); if (el) el.focus(); }, 100);\n}\n\nfunction personelAta(ad)', c)
open(p, 'w', encoding='utf-8').write(c)
