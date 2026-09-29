import re

with open('frontend/js/personel_teblig.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove MEVCUT_VERSIYON, surumKarsilastir, and guncellemeKontrolEt completely
text = re.sub(r'// --- OTOMAT.*?guncellemeKontrolEt\(\) \{.*?\}\n\s*\}\n', '', text, flags=re.DOTALL | re.IGNORECASE)

# Or simply match and remove the block from // --- OTOMATIK GUNCELLEME KONTROL to the end of guncellemeKontrolEt
block_pattern = r'// --- OTOMAT[^\n]+\n\s*const MEVCUT_VERSIYON = "v2\.0";\s*function surumKarsilastir[^\}]+return 0;\s*\}\s*function guncellemeKontrolEt[^\}]+catch[^\}]+\}\s*\}\s*'
text = re.sub(block_pattern, '', text, flags=re.DOTALL)

# 2. Remove the setTimeout(guncellemeKontrolEt, 2000); line
text = re.sub(r'\s*setTimeout\(guncellemeKontrolEt, 2000\);', '', text)

# 3. Fix the logic in ayarlariYukle to use fetch(`${API}/versiyon`)
replacement_logic = """
                if (v.ayarlar.ilk_kullanim !== false) {
                    bildirimGoster("Sisteme Hoş Geldiniz! Önce Ayarlar menüsünden PDF kayıt yerini seçiniz.", "bilgi");
                    fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ilk_kullanim: false }) });
                } else if (!v.ayarlar.meb_logosu) {
                    setTimeout(() => bildirimGoster("MEB Logosu bulunamadı! Ayarlar'dan yükleyin.", "hata"), 3000);
                }

                // Dinamik versiyon kontrolü
                fetch(`${API}/versiyon`).then(r=>r.json()).then(ver => {
                    if (ver.versiyon && v.ayarlar.son_gorulen_versiyon !== ver.versiyon) {
                        setTimeout(() => {
                            if(window.yeniliklerModalAc) window.yeniliklerModalAc();
                            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ son_gorulen_versiyon: ver.versiyon }) });
                        }, 1500);
                    }
                }).catch(()=>{});
            });"""

# We need to replace the old messy block. Let's find it.
old_logic_pattern = r'if\s*\(v\.ayarlar\.ilk_kullanim\s*!==\s*false\)\s*\{.*?\}\s*else\s*if\s*\(!v\.ayarlar\.meb_logosu\)\s*\{.*?\}\n\s*\}\);\s*\}'

text = re.sub(old_logic_pattern, replacement_logic + '\n        }', text, flags=re.DOTALL)

with open('frontend/js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed personel_teblig.js")
