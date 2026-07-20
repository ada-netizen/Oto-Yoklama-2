import re

with open("app.js", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix ihaleAdim2Goster to only show İhtiyaç Kalemleri
new_ihaleAdim2Goster = """function ihaleAdim2Goster(noToggle=false) {
    const alani = document.getElementById("acc_adim2_icerik");
    alani.innerHTML = `
        <div style="display: flex; flex-direction: column;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: var(--fg-main); font-size: 14px;">İhtiyaç Kalemleri</h4>
                <button class="btn btn-dev" style="padding: 6px 15px; font-size: 12px; border-radius: 16px;" onclick="ihaleKalemEkle()"><i data-lucide="plus" width="14" height="14"></i> Kalem Ekle</button>
            </div>
            <div style="background-color: var(--bg-main); border: 1px solid var(--border); border-radius: 8px; overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                    <thead>
                        <tr style="background-color: var(--bg-card-solid); border-bottom: 1px solid var(--border);">
                            <th style="padding: 10px; font-weight: 600; width: 40px; text-align:center;">#</th>
                            <th style="padding: 10px; font-weight: 600;">Cins / Ad</th>
                            <th style="padding: 10px; font-weight: 600;">Özellik (Opsiyonel)</th>
                            <th style="padding: 10px; font-weight: 600; width: 80px;">Miktar</th>
                            <th style="padding: 10px; font-weight: 600; width: 100px;">Birim</th>
                            <th style="padding: 10px; font-weight: 600; width: 50px; text-align:center;">İşlem</th>
                        </tr>
                    </thead>
                    <tbody id="ihale_kalem_tbody">
                        <!-- JS ile doldurulacak -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid var(--border);">
            <button class="btn btn-kirmizi" style="padding: 8px 20px; font-weight: bold; background-color: transparent; border: 1px solid #EF4444; color: #EF4444;" onclick="ihaleSifirla()"><i data-lucide="trash" width="16" height="16"></i> İhaleyi Tamamla / Sıfırla</button>
            <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim2Ileri()"><i data-lucide="arrow-down" width="16" height="16"></i> İleri: Yaklaşık Maliyet Cetveli Oluştur</button>
        </div>
    `;
    ihaleKalemTablosunuCiz();
    lucide.createIcons();
    
    if(!noToggle) {
        document.getElementById("acc_adim2").classList.add("open");
    }
}

function adim2Ileri() {
    if (!ihaleGeciciVeri.kalemler || ihaleGeciciVeri.kalemler.length === 0) {
        bildirimGoster("Lütfen en az bir ihtiyaç kalemi ekleyin.", "hata");
        return;
    }
    
    // Validate Komisyon
    const secim_ids = [
        "ihale_kom_yaklasik_1", "ihale_kom_yaklasik_2", "ihale_kom_yaklasik_3",
        "ihale_kom_piyasa_1", "ihale_kom_piyasa_2", "ihale_kom_piyasa_3",
        "ihale_kom_muayene_1", "ihale_kom_muayene_2", "ihale_kom_muayene_3"
    ];
    let komisyon_eksik = false;
    secim_ids.forEach(id => {
        if (!ihaleKomisyonSecimleri[id]) komisyon_eksik = true;
    });

    if (komisyon_eksik) {
        ihaleKomisyonHataModu = true;
        bildirimGoster("Lütfen yukarıdaki 'Görevli Yönetimi' butonuna basarak eksik komisyon üyelerini seçin! (Eksik olanlar kırmızı işaretlendi)", "hata");
        return;
    }
    ihaleKomisyonHataModu = false;
    
    // 2. Adımı kapat ve tıkla
    document.getElementById("acc_adim2").classList.remove("open");
    document.getElementById("check_adim2").style.display = "inline-block";
    
    // 3. Adımı göster ve aç
    document.getElementById("acc_adim3").style.display = "block";
    ihaleBelgeUretimEkraniGoster(); // Call the accordion-compatible Adım 3
    document.getElementById("acc_adim3").classList.add("open");
}
"""

pattern_adim2 = r"function ihaleAdim2Goster.*?function adim2Ileri\(\) \{.*?(?=function ihaleBelgeUretimEkraniGoster)"
content = re.sub(pattern_adim2, new_ihaleAdim2Goster + "\n", content, flags=re.DOTALL)

# 2. Rewrite ihaleBelgeUretimEkraniGoster to generate the real Adım 3 table (instead of my hallucination)
new_ihaleBelgeUretimEkraniGoster = """function ihaleBelgeUretimEkraniGoster() {
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

pattern_adim3 = r"function ihaleBelgeUretimEkraniGoster\(\) \{.*?(?=function ihaleKalemTablosunuCiz\(\))"
content = re.sub(pattern_adim3, new_ihaleBelgeUretimEkraniGoster + "\n", content, flags=re.DOTALL)

# 3. Fix the title in ihaleBaslat so it says "2. Adım: İhtiyaç Listesi"
content = content.replace("2. Adım: İhtiyaç Listesi ve Firmalar", "2. Adım: İhtiyaç Listesi")

with open("app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed app.js logic")
