import re

# Update core.js to show late notification after upload
with open('frontend/js/core.js', 'r', encoding='utf-8') as f:
    core_js = f.read()

# Add the function definition if it doesn't exist
if 'function gecKalanBildirimiGoster()' not in core_js:
    gec_kalan = """
        function gecKalanBildirimiGoster() {
            fetch(`${API}/gec-bugun-sayisi`).then(r => r.json()).then(data => {
                if(data.basarili && data.sayi > 0) {
                    setTimeout(() => {
                        bildirimGoster(`Bugün ${data.sayi} öğrenci geç yazıldı. Listeyi görmek için <u style="cursor:pointer;" onclick="gecKalanlariIndir()">tıklayın</u>`, 'bilgi');
                    }, 2000);
                }
            }).catch(e => console.error(e));
        }
"""
    core_js = core_js + gec_kalan

# Call it in ilerlemeTakipEt inside the 'tamamlandi' block
if 'gecKalanBildirimiGoster();' not in core_js:
    core_js = core_js.replace('verileriYukle();\n                    if(tamamlaninca)', 'verileriYukle();\n                    gecKalanBildirimiGoster();\n                    if(tamamlaninca)')

with open('frontend/js/core.js', 'w', encoding='utf-8') as f:
    f.write(core_js)


# Update personel_teblig.js to call gecKalanBildirimiGoster() instead of fetch inline
with open('frontend/js/personel_teblig.js', 'r', encoding='utf-8') as f:
    pers_js = f.read()

pers_js = re.sub(r'fetch\(`\$\{API\}/gec-bugun-sayisi`\).*?\}\);', 'gecKalanBildirimiGoster();', pers_js, flags=re.DOTALL)

with open('frontend/js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.write(pers_js)

print("Updated JS files for late notifications!")

