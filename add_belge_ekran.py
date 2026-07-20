import sys

with open("app.js", "r", encoding="utf-8") as f:
    content = f.read()

new_func = """
function ihaleBelgeUretimEkraniGoster() {
    const alan3 = document.getElementById("acc_adim3_icerik");
    const bugun = new Date().toISOString().split('T')[0];

    alan3.innerHTML = `
        <div class="settings-card" style="flex: 1; border: none; background: transparent; padding: 0;">
            <div class="settings-card-body" style="padding: 0;">
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 15px 0;">İhtiyaç listenizi başarıyla oluşturdunuz. Belgeleri PDF veya Excel olarak oluşturabilirsiniz.</p>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border);">
                            <th style="padding: 10px; color: var(--fg-main);">Sıra</th>
                            <th style="padding: 10px; color: var(--fg-main);">Belge Adı</th>
                            <th style="padding: 10px; color: var(--fg-main);">Belge Tarihi</th>
                            <th style="padding: 10px; color: var(--fg-main); text-align: right;">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 15px 10px; color: var(--fg-sub);">1</td>
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Yaklaşık Maliyet Fiyat İsteme</td>
                            <td style="padding: 15px 10px;">
                                <input type="date" id="tarih_fiyat_isteme" value="${bugun}" style="padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;">
                            </td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('fiyat_isteme', 'pdf', document.getElementById('tarih_fiyat_isteme').value)"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('fiyat_isteme', 'excel', document.getElementById('tarih_fiyat_isteme').value)"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 15px 10px; color: var(--fg-sub);">2</td>
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Yaklaşık Maliyet Hesap Cetveli</td>
                            <td style="padding: 15px 10px;">
                                <input type="date" id="tarih_yaklasik_maliyet" value="${bugun}" style="padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;">
                            </td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn btn-dev" style="padding: 6px 12px; font-size: 13px; border-radius: 6px;" onclick="fiyatGirisModalAc('pdf')"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn btn-yardim" style="padding: 6px 12px; font-size: 13px; border-radius: 6px;" onclick="fiyatGirisModalAc('excel')"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    lucide.createIcons();
}
"""

if "function ihaleBelgeUretimEkraniGoster" not in content:
    content = content.replace("function ihaleKalemTablosunuCiz() {", new_func + "\nfunction ihaleKalemTablosunuCiz() {")

with open("app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Added ihaleBelgeUretimEkraniGoster")
