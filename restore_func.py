import re
p = 'frontend/js/personel_teblig.js'
c = open(p, encoding='utf-8').read()
new_f = """function dinamikTebligFiltreleriOlustur() {
    const kapsayici = document.getElementById('dinamik_teblig_filtreleri');
    if (!kapsayici) return;
    let html = '<label class="chip-checkbox-wrapper" title="Tüm grupları seç/bırak"><input type="checkbox" id="grp_tumu" class="chip-checkbox" onchange="filtreTumuDegisti()"><span class="chip-label">Tümü</span></label>';
    tumPersonelGruplari.forEach(grup => {
        let sid = grup.replace(/[^a-zA-Z0-9]/g, '_');
        html += `<label class="chip-checkbox-wrapper"><input type="checkbox" id="grp_${sid}" class="chip-checkbox dinamik-grp-checkbox" data-grup="${grup}" onchange="filtreleriHesapla()"><span class="chip-label">${grup}</span></label>`;
    });
    kapsayici.innerHTML = html;
}

"""
c = re.sub(r'function filtreTumuDegisti', new_f + 'function filtreTumuDegisti', c)
open(p, 'w', encoding='utf-8').write(c)
