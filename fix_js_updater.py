with open('frontend/js/personel_teblig.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove JS updater
start = content.find('// --- OTOMAT')
end = content.find('function gecKalanlariIndir')
if start != -1 and end != -1:
    content = content[:start] + content[end:]

# 2. Remove setTimeout
content = content.replace('setTimeout(guncellemeKontrolEt, 2000);', '')

# 3. Fix the line with MEVCUT_VERSIYON
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'son_gorulen_versiyon !== MEVCUT_VERSIYON' in line:
        lines[i] = """                fetch(`${API}/versiyon`).then(res => res.json()).then(versiyonData => {
                    const GUNCEL = versiyonData.versiyon;
                    if (v.ayarlar.son_gorulen_versiyon !== GUNCEL) {
                        setTimeout(() => {
                            if(window.yeniliklerModalAc) window.yeniliklerModalAc();
                            fetch(`${API}/ayarlar-kaydet`, { 
                                method: 'POST', 
                                headers: { 'Content-Type': 'application/json' }, 
                                body: JSON.stringify({ son_gorulen_versiyon: GUNCEL }) 
                            });
                        }, 1500);
                    }
                }).catch(err => console.error('Versiyon alinamadi', err));"""
        break

with open('frontend/js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('SUCCESS')
