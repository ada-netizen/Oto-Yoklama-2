import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\saglik.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_func = """function saglikTablosunuCiz() {
    const tbody = document.getElementById('tbody_saglik');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    aktifSaglikPersoneli.forEach(p => {
        const tr = document.createElement('tr');
        
        let kisaAd = p.personel_ad.length > 20 ? p.personel_ad.substring(0, 18) + '..' : p.personel_ad;
        
        // Aylar section
        let aylarHtml = '';
        for (let i = 1; i <= 12; i++) {
            let gun = p.aylar[i] || 0;
            if (gun > 0) {
                aylarHtml += `<td style="text-align: center;"><span class="badge" style="background-color: var(--tree-sel); color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">${gun} Gün</span></td>`;
            } else {
                aylarHtml += `<td style="color: var(--fg-sub); text-align: center;">-</td>`;
            }
        }
        
        // Yeni Kesinti (Warning Badge)
        let kesintiDurumuHtml = '<span style="color: var(--fg-sub); text-align: center;">-</span>';
        if (p.yeni_kesinti > 0) {
            kesintiDurumuHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">
                <i data-lucide="alert-triangle" style="width: 14px; height: 14px; display: inline-block; vertical-align: text-bottom; margin-right: 4px;"></i>${p.yeni_kesinti} Gün Kesilecek
            </span>`;
        }

        // Toplam Izin Badge
        let toplamHtml = `<span class="badge" style="background: var(--bg-soft); color: var(--fg-main); padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">${p.toplam}</span>`;
        if (p.toplam >= 7) {
            toplamHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #EF4444; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">${p.toplam}</span>`;
        } else if (p.toplam > 0) {
            toplamHtml = `<span class="badge" style="background: rgba(245, 158, 11, 0.1); color: #F59E0B; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">${p.toplam}</span>`;
        }

        tr.innerHTML = `
            <td style="position: sticky; left: 0; background: var(--bg-panel); z-index: 1; white-space: nowrap; font-weight: bold; color: var(--fg-main);" title="${p.personel_ad}">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i data-lucide="user" style="width: 16px; height: 16px; color: var(--fg-sub);"></i>
                    ${kisaAd}
                </div>
            </td>
            ${aylarHtml}
            <td style="border-left: 2px solid var(--border); text-align: center;">${toplamHtml}</td>
            <td style="text-align: center;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 4px;">
                    <input type="text" inputmode="numeric" pattern="[0-9]*" onwheel="return false;" class="kesinti-input" style="width: 48px; height: 32px; text-align: center; padding: 4px; font-weight: bold; background: var(--bg-soft); border: 1px solid var(--border); border-radius: 4px; outline: none; color: var(--fg-main); font-size: 14px; transition: all 0.2s ease;" 
                           value="${p.onceden_kesilen}" 
                           onchange="manuelKesintiKaydet('${p.personel_ad}', this.value)"
                           onfocus="this.style.borderColor='var(--tree-sel)'; this.style.boxShadow='0 0 0 2px rgba(var(--tree-sel-rgb), 0.2)';"
                           onblur="this.style.borderColor='var(--border)'; this.style.boxShadow='none';"
                           onkeypress="return event.charCode >= 48 && event.charCode <= 57">
                    <span style="color: var(--fg-sub); font-size: 12px; margin-left: 2px;">Gün</span>
                </div>
            </td>
            <td style="text-align: center; white-space: nowrap;">${kesintiDurumuHtml}</td>
            <td style="text-align: right;">
                <button class="btn" style="background-color: var(--tree-sel); color: white; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 6px; border: none; cursor: pointer; transition: background-color 0.2s;" onclick="saglikDetayGoster('${p.personel_ad}', ${p.onceden_kesilen})" title="Rapor Geçmişi" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                    <i data-lucide="list" style="width: 14px; height: 14px;"></i> Detay
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}
"""

lines = lines[:30] + [new_func + "\n"] + lines[74:]

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\saglik.js", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("saglik.js successfully updated.")
