import re

# 1. Update core.js
with open('frontend/js/core.js', 'r', encoding='utf-8') as f:
    core_content = f.read()

new_dosyaYukle = """        function dosyaYukle(endpoint, event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Excel dosyasi sisteme aktariliyor...");
            fetch(`${API}/${endpoint}`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) {
                    ilerlemeTakipEt(v.job_id);
                } else {
                    yuklemeGizle();
                    bildirimGoster("Hata: " + v.mesaj, "hata");
                }
                if(event && event.target) event.target.value = '';
            }).catch(err => { 
                yuklemeGizle(); 
                bildirimGoster(err.message || "Baglanti hatasi! Sunucuyu kontrol edin.", "hata"); 
            });
        }"""

core_content = re.sub(r'        function dosyaYukle.*?\}\);[\n\s]*\}', new_dosyaYukle, core_content, flags=re.DOTALL)
with open('frontend/js/core.js', 'w', encoding='utf-8') as f:
    f.write(core_content)


# 2. Update personel_teblig.js
with open('frontend/js/personel_teblig.js', 'r', encoding='utf-8') as f:
    pers_content = f.read()

new_personelExcelYukle = """        function personelExcelYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Personel listesi i\u015fleniyor...");
            fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) {
                    ilerlemeTakipEt(v.job_id, personelleriYukle);
                } else {
                    bildirimGoster(v.mesaj, "hata");
                }
                if(event && event.target) event.target.value = '';
            }).catch(err => { 
                bildirimGoster(err.message || "Ba\u011flant\u0131 hatas\u0131! Sunucuyu kontrol edin.", "hata"); 
            }).finally(() => yuklemeGizle());
        }"""

pers_content = re.sub(r'        function personelExcelYukle.*?\}\)\.finally\(\(\) => yuklemeGizle\(\)\);[\n\s]*\}', new_personelExcelYukle, pers_content, flags=re.DOTALL)
with open('frontend/js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.write(pers_content)

print("Updated JS files!")

