import re

p = 'frontend/js/personel_teblig.js'
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "if (v.ayarlar.son_gorulen_versiyon !== MEVCUT_VERSIYON)" in line:
        new_lines.append("                if (v.ayarlar.son_gorulen_versiyon !== MEVCUT_VERSIYON) { setTimeout(() => { if(window.yeniliklerModalAc) window.yeniliklerModalAc(); fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ son_gorulen_versiyon: MEVCUT_VERSIYON }) }); }, 1500); }\n")
    else:
        new_lines.append(line)

with open(p, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("done")
