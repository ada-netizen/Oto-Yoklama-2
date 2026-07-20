import re

with open("app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Let's replace ihaleBaslat
new_ihaleBaslat = """function ihaleBaslat() {
    let butceTertipleri = JSON.parse(localStorage.getItem("butce_tertipleri") || '["13.01.32.62-09.02.01.00-1-03.02"]');

    if (!ihaleGeciciVeri.tertibi && butceTertipleri.length > 0) {
        ihaleGeciciVeri.tertibi = butceTertipleri[0];
    }
    
    if (!ihaleGeciciVeri.resmi_baslik) {
        ihaleGeciciVeri.resmi_baslik = localStorage.getItem("ihale_resmi_baslik") || "";
    }
    if (!ihaleGeciciVeri.yazisma_kodu) {
        ihaleGeciciVeri.yazisma_kodu = localStorage.getItem("ihale_yazisma_kodu") || "";
    }

    const icerik = document.getElementById("ihale_icerik");
    icerik.style.alignItems = "stretch";
    icerik.style.justifyContent = "flex-start";
    
    let tertipOptions = butceTertipleri.map(t => `<option value="${t}" ${ihaleGeciciVeri.tertibi === t ? 'selected' : ''}>${t}</option>`).join('');

    icerik.innerHTML = `
        <div class="accordion-item open" id="acc_adim1">
            <div class="accordion-header" onclick="toggleAcc('adim1')">
                <div class="acc-title"><i data-lucide="info" width="18" height="18"></i> 1. Adım: İhale Temel Bilgileri</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim1" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim1_icerik">
                <p style="color: var(--fg-sub); font-size: 13px; margin-bottom: 15px; margin-top: 0;">Lütfen ihale konusu ve bütçe tertibini girerek başlayın.</p>
                
                <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px;">
                    <div style="flex: 2; min-width: 250px;">
                        <label style="font-size: 12px; font-weight: bold; color: var(--fg-main); display: block; margin-bottom: 5px;">İhale Konusu / İşin Adı:</label>
                        <input type="text" id="ihale_konusu" style="width:100%; padding: 10px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;" placeholder="Örn: 2026 Yılı Temizlik Malzemesi Alımı" value="${ihaleGeciciVeri.konu}" oninput="ihaleGeciciVeri.konu = this.value; ihaleTaslaginiKaydet();">
                    </div>
                    
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 12px; font-weight: bold; color: var(--fg-main); display: block; margin-bottom: 5px;">Bütçe Tertibi:</label>
                        <div style="display:flex; gap:5px;">
                            <select id="ihale_tertibi" style="flex:1; padding: 10px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;" onchange="ihaleGeciciVeri.tertibi = this.value; ihaleTaslaginiKaydet();">
                                ${tertipOptions}
                            </select>
                            <button class="btn btn-dev" style="padding: 10px; font-size: 14px;" onclick="butceTertibiEkle()" title="Yeni Bütçe Tertibi Ekle"><i data-lucide="plus" width="16" height="16"></i></button>
                            <button class="btn btn-sil" style="padding: 10px; font-size: 14px; background:transparent; border: 1px solid var(--border); color:#EF4444;" onclick="butceTertibiSil()" title="Seçili Bütçe Tertibini Sil"><i data-lucide="trash-2" width="16" height="16"></i></button>
                        </div>
                    </div>
                </div>
                
                <div id="ihale_adim1_btn_container" style="margin-top: 20px; text-align: right;">
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim1Ileri()"><i data-lucide="arrow-down" width="16" height="16"></i> İleri: İhtiyaç Listesi ve Firmalar</button>
                </div>
            </div>
        </div>

        <div class="accordion-item" id="acc_adim2" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim2')">
                <div class="acc-title"><i data-lucide="list" width="18" height="18"></i> 2. Adım: İhtiyaç Listesi ve Firmalar</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim2" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim2_icerik"></div>
        </div>

        <div class="accordion-item" id="acc_adim3" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim3')">
                <div class="acc-title"><i data-lucide="file-check" width="18" height="18"></i> 3. Adım: Belge Üretimi</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim3" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim3_icerik"></div>
        </div>
    `;
    lucide.createIcons();
    
    // Check if we need to show other steps immediately (if loading from draft)
    if (ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0) {
        document.getElementById("acc_adim2").style.display = "block";
        ihaleAdim2Goster(true); // true means just render inside without auto-toggling
        // But if we want to jump to step 2, we can call toggleAcc
    }
}

function toggleAcc(adim) {
    const acc = document.getElementById("acc_" + adim);
    if(acc) {
        acc.classList.toggle("open");
    }
}

function adim1Ileri() {
    const konu = document.getElementById('ihale_konusu').value.trim();
    if (!konu) {
        bildirimGoster("Lütfen ihale konusunu girin.", "hata");
        return;
    }
    
    // 1. Adımı kapat ve tıkla
    document.getElementById("acc_adim1").classList.remove("open");
    document.getElementById("check_adim1").style.display = "inline-block";
    
    // 2. Adımı göster ve aç
    document.getElementById("acc_adim2").style.display = "block";
    ihaleAdim2Goster();
    document.getElementById("acc_adim2").classList.add("open");
}
"""

pattern1 = r"function ihaleBaslat\(\) \{[\s\S]*?(?=function butceTertibiEkle\(\))"
content = re.sub(pattern1, new_ihaleBaslat, content, count=1)

# Modify ihaleAdim2Goster
new_ihaleAdim2Goster = """function ihaleAdim2Goster(noToggle=false) {
    const alani = document.getElementById("acc_adim2_icerik");
    alani.innerHTML = `
        <div style="display: flex; gap: 20px; align-items: stretch; flex-wrap: wrap;">
            <!-- SOL: İhtiyaç Listesi -->
            <div style="flex: 2; min-width: 400px; display: flex; flex-direction: column;">
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
                <div style="margin-top: 10px; text-align: right;">
                    <button class="btn btn-yardim" style="padding: 6px 15px; font-size: 12px; background-color: var(--bg-card); color: var(--fg-sub); border: 1px solid var(--border);" onclick="ihaleFiyatGirisModalAc()"><i data-lucide="dollar-sign" width="14" height="14"></i> Fiyat Girişi (Tablo)</button>
                </div>
            </div>
            
            <!-- SAĞ: Firmalar -->
            <div style="flex: 1; min-width: 250px; display: flex; flex-direction: column;">
                <h4 style="margin: 0 0 10px 0; color: var(--fg-main); font-size: 14px;">Teklif Alınan Firmalar</h4>
                <div style="background-color: var(--bg-main); border: 1px solid var(--border); border-radius: 8px; padding: 10px; display:flex; flex-direction:column; gap:10px;" id="ihale_firma_listesi">
                    <!-- JS ile doldurulacak -->
                </div>
                <p style="font-size: 11px; color: var(--fg-sub); margin-top: 10px;">Not: En az 1 firma adı girilmesi zorunludur.</p>
            </div>
        </div>
        
        <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid var(--border);">
            <button class="btn btn-kirmizi" style="padding: 8px 20px; font-weight: bold; background-color: transparent; border: 1px solid #EF4444; color: #EF4444;" onclick="ihaleSifirla()"><i data-lucide="trash" width="16" height="16"></i> İhaleyi Tamamla / Sıfırla</button>
            <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim2Ileri()"><i data-lucide="arrow-down" width="16" height="16"></i> İleri: Yaklaşık Maliyet Cetveli Oluştur</button>
        </div>
    `;
    ihaleKalemTablosunuCiz();
    ihaleFirmaTablosunuCiz();
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
    
    // 2. Adımı kapat ve tıkla
    document.getElementById("acc_adim2").classList.remove("open");
    document.getElementById("check_adim2").style.display = "inline-block";
    
    // 3. Adımı göster ve aç
    document.getElementById("acc_adim3").style.display = "block";
    ihaleBelgeUretimEkraniGoster();
    document.getElementById("acc_adim3").classList.add("open");
}
"""

pattern2 = r"function ihaleAdim2Goster\(\) \{[\s\S]*?(?=function ihaleKalemTablosunuCiz\(\))"
content = re.sub(pattern2, new_ihaleAdim2Goster, content, count=1)

# Modify ihaleBelgeUretimEkraniGoster
new_ihaleBelgeUretimEkraniGoster = """function ihaleBelgeUretimEkraniGoster() {
    const alani = document.getElementById("acc_adim3_icerik");
    alani.innerHTML = `
        <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom: 20px;">
            <div>
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 5px 0;">Belge üretim tarihi (Varsayılan: Bugün):</p>
                <input type="date" id="ihale_belge_tarihi" style="padding: 8px; background: var(--bg-input); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;" value="${new Date().toISOString().split('T')[0]}">
            </div>
            <p style="color: var(--fg-sub); font-size: 13px; margin: 0; max-width: 400px; text-align:right;">Bilgiler kontrol edildikten sonra belgeleri masaüstünüze oluşturabilirsiniz.</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
            <!-- Yaklaşık Maliyet -->
            <div style="background-color: var(--bg-main); border: 1px solid var(--border); padding: 15px; border-radius: 8px; text-align: center; display: flex; flex-direction: column; gap: 15px; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--fg-main);"><i data-lucide="calculator" width="18" height="18"></i> Yaklaşık Maliyet</h4>
                    <p style="font-size: 11px; color: var(--fg-sub); margin: 0;">Hesap Cetveli ve Komisyon Kararı</p>
                </div>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button class="btn btn-kirmizi" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('yaklasik_maliyet', 'pdf')"><i data-lucide="file-text" width="16" height="16"></i> PDF</button>
                    <button class="btn btn-ogr" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('yaklasik_maliyet', 'excel')"><i data-lucide="bar-chart" width="16" height="16"></i> Excel</button>
                </div>
            </div>
            
            <!-- Piyasa Fiyat Araştırması -->
            <div style="background-color: var(--bg-main); border: 1px solid var(--border); padding: 15px; border-radius: 8px; text-align: center; display: flex; flex-direction: column; gap: 15px; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--fg-main);"><i data-lucide="search" width="18" height="18"></i> Piyasa Fiyat Araştırması</h4>
                    <p style="font-size: 11px; color: var(--fg-sub); margin: 0;">Tutanak ve Komisyon İmzaları</p>
                </div>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button class="btn btn-kirmizi" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('piyasa_arastirmasi', 'pdf')"><i data-lucide="file-text" width="16" height="16"></i> PDF</button>
                    <button class="btn btn-ogr" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('piyasa_arastirmasi', 'excel')"><i data-lucide="bar-chart" width="16" height="16"></i> Excel</button>
                </div>
            </div>
            
            <!-- Onay Belgesi -->
            <div style="background-color: var(--bg-main); border: 1px solid var(--border); padding: 15px; border-radius: 8px; text-align: center; display: flex; flex-direction: column; gap: 15px; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0 0 5px 0; color: var(--fg-main);"><i data-lucide="check-square" width="18" height="18"></i> İhale Onay Belgesi</h4>
                    <p style="font-size: 11px; color: var(--fg-sub); margin: 0;">22/d Doğrudan Temin Onayı</p>
                </div>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button class="btn btn-kirmizi" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('onay_belgesi', 'pdf')"><i data-lucide="file-text" width="16" height="16"></i> PDF</button>
                    <button class="btn btn-ogr" style="flex:1; padding: 10px; display:flex; align-items:center; justify-content:center; gap:5px;" onclick="ihaleBelgeUret('onay_belgesi', 'excel')"><i data-lucide="bar-chart" width="16" height="16"></i> Excel</button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}
"""

pattern3 = r"function ihaleBelgeUretimEkraniGoster\(\) \{[\s\S]*?(?=function ihaleBelgeUret\()"
content = re.sub(pattern3, new_ihaleBelgeUretimEkraniGoster, content, count=1)

with open("app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Accordion updated in app.js")
