// ==========================================

let ihaleKalemleri = [];
let olcuBirimleri = [
    "ADET_BIRIM", "AFIF_BIRIM_FIYATI", "ATV_BIRIM_FIYATI", "ALTIN_AYARI",
    "KG_METREKARE", "TON_BASINA_TASIMA_KAPASITESI", "ADET_CIFT", "BRUT_KALORI_DEGERI",
    "BIN_LITRE", "GUMUS", "GRAM", "GROS_TON", "YUZ_ADET", "KILOGRAM_ADET",
    "KILOWATT_SAAT", "KILOWATT", "LITRE", "METRE", "METREKUP", "METREKARE",
    "TON", "KALEM", "PUAN"
];
function olcuBirimleriniGetir() {
    fetch(`${API}/olcu-birimleri`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
    }).then(data => {
        if(data && Array.isArray(data.birimler) && data.birimler.length) {
            olcuBirimleri = data.birimler;
        }
        const govde = document.getElementById("ihale_kalemleri_govde");
        if (govde && typeof ihaleKalemTablosunuCiz === "function" && ihaleGeciciVeri?.kalemler) {
            ihaleKalemTablosunuCiz();
        }
    }).catch(e => console.error("Ölçü birimleri çekilemedi: ", e));
}
document.addEventListener('DOMContentLoaded', olcuBirimleriniGetir);

function ihaleTablosunuCiz() {
    const govde = document.getElementById("ihale_kalemleri_govde");
    if (ihaleKalemleri.length === 0) {
        govde.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px; color: var(--fg-sub);">Excel şablonunu yüklediğinizde kalemler burada listelenecektir.</td></tr>';
        return;
    }

    let html = "";
    ihaleKalemleri.forEach((k, idx) => {
        html += `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; text-align:center;">${k.sira}</td>
                <td style="padding: 10px;">${k.cins}</td>
                <td style="padding: 10px; text-align:center;">${k.miktar}</td>
                <td style="padding: 10px; text-align:center;">${k.birim}</td>
                <td style="padding: 10px; text-align:right;">${k.f1.toFixed(2)} ₺</td>
                <td style="padding: 10px; text-align:right;">${k.f2.toFixed(2)} ₺</td>
                <td style="padding: 10px; text-align:right;">${k.f3.toFixed(2)} ₺</td>
            </tr>
        `;
    });
    govde.innerHTML = html;
}

async function ihaleExcelYukle(event) {
    const dosya = event.target.files[0];
    if (!dosya) return;
    
    yuklemeGoster("İhale Exceli Okunuyor...");
    const formData = new FormData();
    formData.append("dosya", dosya);

    try {
        const res = await fetch("http://localhost:8000/ihale-excel-oku", {
            method: "POST",
            body: formData
        });
        const sonuc = await res.json();
        
        if (sonuc.basarili) {
            ihaleKalemleri = sonuc.kalemler;
            ihaleTablosunuCiz();
            bildirimGoster("Excel başarıyla okundu. " + ihaleKalemleri.length + " kalem bulundu.", "basarili");
        } else {
            bildirimGoster("Hata: " + sonuc.mesaj, "hata");
        }
    } catch (e) {
        bildirimGoster("Sunucuya bağlanılamadı.", "hata");
    } finally {
        yuklemeGizle();
        event.target.value = "";
    }
}

function ihaleAdim3Goster() {
    // Validate Step 2
    const gecerliKalemler = ihaleGeciciVeri.kalemler.filter(k => k.cins && k.cins.trim() !== "");

    if (gecerliKalemler.length === 0) {
        bildirimGoster("Lütfen ihtiyaç listesine en az 1 kalem ekleyin.", "uyari");
        return;
    }
    if (!ihaleGeciciVeri.konu) {
        bildirimGoster("Lütfen ihale konusu (Adım 1) girin.", "uyari");
        return;
    }

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
        bildirimGoster("Lütfen 'Görevli Yönetimi' butonuna basarak eksik komisyon üyelerini seçin! (Eksik olanlar kırmızı işaretlendi)", "hata");
        return;
    }
    ihaleKomisyonHataModu = false;

    // Hide Step 1 and Step 2
    document.getElementById("ihale_icerik").children[0].style.display = "none";
    document.getElementById("ihale_adim2_alani").style.display = "none";

    const alan3 = document.getElementById("ihale_adim3_alani");
    alan3.style.display = "flex";
    
    const bugun = new Date().toISOString().split('T')[0];

    alan3.innerHTML = `
        <div class="settings-card" style="flex: 1;">
            <div class="settings-card-header" style="display:flex; justify-content:space-between; align-items:center;">
                <span><i data-lucide="printer" width="16" height="16"></i> 3. Adım: Belge Üretim Merkezi</span>
                <button class="btn btn-ogr" style="padding: 4px 10px; font-size: 11px;" onclick="ihaleAdim3Geri()"><i data-lucide="arrow-left" width="14" height="14"></i> Geri Dön</button>
            </div>
            <div class="settings-card-body" style="padding: 15px;">
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
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('pdf')"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('excel')"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    lucide.createIcons();
    setTimeout(() => {
        alan3.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function ihaleAdim3Geri() {
    document.getElementById("ihale_icerik").children[0].style.display = "block";
    document.getElementById("ihale_adim2_alani").style.display = "flex";
    document.getElementById("ihale_adim3_alani").style.display = "none";
}

async function belgeUret(belgeTipi, format, tarih) {
    if (!tarih) {
        bildirimGoster("Lütfen belge tarihi seçin.", "uyari");
        return;
    }
    
    yuklemeGoster(format.toUpperCase() + " Üretiliyor...");

    const gecerliKalemler = ihaleGeciciVeri.kalemler.filter(k => k.cins && k.cins.trim() !== "");
    const secim_ids = [
        "ihale_kom_yaklasik_1", "ihale_kom_yaklasik_2", "ihale_kom_yaklasik_3",
        "ihale_kom_piyasa_1", "ihale_kom_piyasa_2", "ihale_kom_piyasa_3",
        "ihale_kom_muayene_1", "ihale_kom_muayene_2", "ihale_kom_muayene_3"
    ];
    let komisyonVerisi = {};
    secim_ids.forEach(id => {
        komisyonVerisi[id] = ihaleKomisyonSecimleri[id];
    });

    const veri = {
        ihale_konusu: ihaleGeciciVeri.konu,
        butce_tertibi: ihaleGeciciVeri.tertibi,
        resmi_baslik: ihaleGeciciVeri.resmi_baslik,
        yazisma_kodu: ihaleGeciciVeri.yazisma_kodu,
        firmalar: ihaleGeciciVeri.firmalar,
        firma_vergiler: ihaleGeciciVeri.firmaVergiler,
        kalemler: gecerliKalemler,
        komisyon: komisyonVerisi,
        belge_tarihi: tarih,
        belge_tipi: belgeTipi,
        format: format
    };

    try {
        const response = await fetch('http://localhost:8000/ihale-tekli-belge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(veri)
        });
        
        const sonuc = await response.json();
        if (sonuc.basarili) {
            bildirimGoster(sonuc.mesaj, "basarili");
        } else {
            bildirimGoster("Hata: " + sonuc.mesaj, "hata");
        }
    } catch (e) {
        bildirimGoster("Sunucuya bağlanılamadı.", "hata");
    } finally {
        yuklemeGizle();
    }
}



let ihaleKomisyonSecimleri = JSON.parse(localStorage.getItem('ihaleKomisyonSecimleri') || '{}');
let ihaleKomisyonHataModu = false;

let ihaleGeciciVeri = {
    konu: "",
    tertibi: "",
    resmi_baslik: localStorage.getItem("ihale_resmi_baslik") || "",
    yazisma_kodu: localStorage.getItem("ihale_yazisma_kodu") || "",
    firmalar: ["", "", ""],
    firmaVergiler: ["", "", ""],
    kalemler: []
};

function ihaleTaslaginiKaydet() {
    localStorage.setItem("ihale_taslak", JSON.stringify(ihaleGeciciVeri));
}

function ihaleTaslaginiYukle() {
    let taslak = localStorage.getItem("ihale_taslak");
    if (taslak) {
        ihaleGeciciVeri = JSON.parse(taslak);
        // Ensure legacy data has newer fields
        if (!ihaleGeciciVeri.firmaVergiler) ihaleGeciciVeri.firmaVergiler = ["", "", ""];
        if (!ihaleGeciciVeri.resmi_baslik) ihaleGeciciVeri.resmi_baslik = localStorage.getItem("ihale_resmi_baslik") || "";
        if (!ihaleGeciciVeri.yazisma_kodu) ihaleGeciciVeri.yazisma_kodu = localStorage.getItem("ihale_yazisma_kodu") || "";
    }
}

function ihaleSifirla() {
    if(confirm("İhaleyi tamamlayıp yeni bir ihaleye başlamak istiyor musunuz? (Sadece 'Bilgi Girişi' verileriniz korunacaktır.)")) {
        let kayitliBaslik = ihaleGeciciVeri.resmi_baslik;
        let kayitliKod = ihaleGeciciVeri.yazisma_kodu;
        
        ihaleGeciciVeri = {
            konu: "",
            tertibi: "",
            resmi_baslik: kayitliBaslik,
            yazisma_kodu: kayitliKod,
            firmalar: ["", "", ""],
            firmaVergiler: ["", "", ""],
            kalemler: []
        };
        ihaleTaslaginiKaydet();
        
        // Komisyon seçimlerini sıfırla
        ihaleKomisyonSecimleri = {};
        localStorage.setItem("ihaleKomisyonSecimleri", JSON.stringify(ihaleKomisyonSecimleri));
        localStorage.removeItem("ihale_aktif_adim");
        
        // Ekranı başlangıç durumuna döndür
        const icerik = document.getElementById("ihale_icerik");
        icerik.innerHTML = `
            <div id="ihale_baslangic_mesaj" style="color: var(--fg-sub); font-size: 15px; text-align: center; display:flex; flex-direction:column; align-items:center; gap:15px; opacity: 0.6;">
                <i data-lucide="mouse-pointer-click" width="48" height="48"></i>
                <span>Yeni bir ihale süreci başlatmak için aşağıdaki <b>"İhale Başlat"</b> butonuna tıklayın.</span>
            </div>
            <button class="btn"
                    style="background-color: #10B981; color: white; padding: 15px 30px; font-weight: bold; font-size: 18px; border-radius: 8px; margin-top: 20px;"
                    onclick="ihaleBaslat()"><i data-lucide="play" width="24" height="24"></i> İhale Başlat</button>
        `;
        icerik.style.display = "flex";
        icerik.style.alignItems = "center";
        icerik.style.justifyContent = "center";
        lucide.createIcons();
        
        document.getElementById("ihale_adim2_alani").style.display = "none";
        document.getElementById("ihale_adim3_alani").style.display = "none";
        
        bildirimGoster("İhale tamamlandı ve yeni ihale için ekran temizlendi.", "basarili");
    }
}

// Load draft initially
ihaleTaslaginiYukle();

document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("ihale_aktif_adim")) ihaleBaslat();
});

window.addEventListener('click', function(e) {
    let btn = e.target.closest('button');
    if (btn && btn.getAttribute('onclick')) {
        let match = btn.getAttribute('onclick').match(/adim(\d+)Ileri\(\)/);
        if (match) localStorage.setItem("ihale_aktif_adim", parseInt(match[1]) + 1);
    }
});
function ihaleBilgiGirisiModalAc() {
    document.getElementById('ihale_resmi_yazi_basligi').value = ihaleGeciciVeri.resmi_baslik || localStorage.getItem("ihale_resmi_baslik") || "";
    document.getElementById('ihale_yazisma_kod').value = ihaleGeciciVeri.yazisma_kodu || localStorage.getItem("ihale_yazisma_kodu") || "";
    modalAc('ihale_bilgi_girisi_modal');
}

function ihaleBilgiGirisiKaydet() {
    const baslik = document.getElementById('ihale_resmi_yazi_basligi').value;
    const kod = document.getElementById('ihale_yazisma_kod').value;
    
    ihaleGeciciVeri.resmi_baslik = baslik;
    ihaleGeciciVeri.yazisma_kodu = kod;
    
    localStorage.setItem("ihale_resmi_baslik", baslik);
    localStorage.setItem("ihale_yazisma_kodu", kod);
    
    ihaleTaslaginiKaydet(); // AUTO SAVE
    
    modalKapat('ihale_bilgi_girisi_modal');
    bildirimGoster("Bilgiler kaydedildi.", "basari");
}

function ihaleBaslat() {
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
    
    if (!ihaleGeciciVeri.kalemler || ihaleGeciciVeri.kalemler.length === 0) {
        ihaleGeciciVeri.kalemler = [{sira: 1, cins: "", ozellik: "", miktar: "", birim: ""}];
    }

    const icerik = document.getElementById("ihale_icerik");
    icerik.style.display = "block";
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
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim1Ileri()"><i data-lucide="arrow-down" width="16" height="16"></i> İleri: İhtiyaç Listesi</button>
                </div>
            </div>
        </div>

        <div class="accordion-item" id="acc_adim2" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim2')">
                <div class="acc-title"><i data-lucide="list" width="18" height="18"></i> 2. Adım: İhtiyaç Listesi</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim2" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim2_icerik"></div>
        </div>

        <div class="accordion-item" id="acc_adim3" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim3')">
                <div class="acc-title"><i data-lucide="file-check" width="18" height="18"></i> 3. Adım: Yaklaşık Maliyet</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim3" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim3_icerik"></div>
        </div>
        <div class="accordion-item" id="acc_adim4" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim4')">
                <div class="acc-title"><i data-lucide="check-square" width="18" height="18"></i> 4. Adım: İhale Onayı</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim4" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim4_icerik"></div>
        </div>

        <div class="accordion-item" id="acc_adim5" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim5')">
                <div class="acc-title"><i data-lucide="banknote" width="18" height="18"></i> 5. Adım: Harcama Ekleme</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim5" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim5_icerik"></div>
        </div>

        <div class="accordion-item" id="acc_adim6" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim6')">
                <div class="acc-title"><i data-lucide="file-check" width="18" height="18"></i> 6. Adım: Piyasa Fiyat Araştırması</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim6" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim6_icerik"></div>
        </div>
        <div class="accordion-item" id="acc_adim7" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim7')">
                <div class="acc-title"><i data-lucide="check-square" width="18" height="18"></i> 7. Adım: VİF Girişi</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim7" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim7_icerik"></div>
        </div>
        <div class="accordion-item" id="acc_adim8" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim8')">
                <div class="acc-title"><i data-lucide="file-check" width="18" height="18"></i> 8. Adım: Muayene Kabul</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim8" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim8_icerik"></div>
        </div>
        <div class="accordion-item" id="acc_adim9" style="display: none;">
            <div class="accordion-header" onclick="toggleAcc('adim9')">
                <div class="acc-title"><i data-lucide="credit-card" width="18" height="18"></i> 9. Adım: Ödeme Emri Oluşturma</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim9" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim9_icerik"></div>
        </div>
    `;
    lucide.createIcons();
    
    let aktifAdim = parseInt(localStorage.getItem("ihale_aktif_adim")) || 1;
    if (aktifAdim > 1 && ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0) {
        for (let i = 1; i < aktifAdim; i++) {
            let nxt = i + 1;
            let cAcc = document.getElementById("acc_adim" + i);
            if (cAcc) { cAcc.classList.remove("open"); document.getElementById("check_adim" + i).style.display = "inline-block"; }
            let nAcc = document.getElementById("acc_adim" + nxt);
            if (nAcc) {
                nAcc.style.display = "block";
                if (nxt === 3) ihaleBelgeUretimEkraniGoster();
                else if (window["ihaleAdim" + nxt + "Goster"]) window["ihaleAdim" + nxt + "Goster"](true);
                if (nxt === aktifAdim) { nAcc.classList.add("open"); setTimeout(() => nAcc.scrollIntoView({behavior: "smooth", block: "start"}), 100); }
            }
        }
    } else if (ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0) {
        document.getElementById("acc_adim2").style.display = "block";
        ihaleAdim2Goster(true); // true means just render inside without auto-toggling
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
function butceTertibiEkle() {
    const yeni = prompt("Yeni Bütçe Tertibini girin (Örn: 13.01.32.62-09.02.01.00-1-03.02):");
    if (yeni && yeni.trim() !== "") {
        let tertipler = JSON.parse(localStorage.getItem("butce_tertipleri") || '["13.01.32.62-09.02.01.00-1-03.02"]');
        if (!tertipler.includes(yeni.trim())) {
            tertipler.push(yeni.trim());
            localStorage.setItem("butce_tertipleri", JSON.stringify(tertipler));
            ihaleGeciciVeri.tertibi = yeni.trim();
            ihaleBaslat(); // re-render
        }
    }
}

function butceTertibiSil() {
    const secili = document.getElementById("ihale_tertibi").value;
    if (!secili) return;
    if (confirm(`'${secili}' bütçe tertibini silmek istediğinize emin misiniz?`)) {
        let tertipler = JSON.parse(localStorage.getItem("butce_tertipleri") || '["13.01.32.62-09.02.01.00-1-03.02"]');
        tertipler = tertipler.filter(t => t !== secili);
        localStorage.setItem("butce_tertipleri", JSON.stringify(tertipler));
        ihaleGeciciVeri.tertibi = tertipler.length > 0 ? tertipler[0] : "";
        ihaleBaslat(); // re-render
    }
}

function ihaleAdim2Goster(noToggle=false) {
    const alani = document.getElementById("acc_adim2_icerik");
    alani.innerHTML = `
        <div style="display: flex; flex-direction: column;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: var(--fg-main); font-size: 14px;">İhtiyaç Kalemleri</h4>
                <button class="btn btn-dev" style="padding: 6px 15px; font-size: 12px; border-radius: 16px;" onclick="ihaleKalemSatiriEkle()"><i data-lucide="plus" width="14" height="14"></i> Kalem Ekle</button>
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
                    <tbody id="ihale_kalemleri_govde">
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
        bildirimGoster("Lütfen 'Görevli Yönetimi' butonuna basarak eksik komisyon üyelerini seçin! (Eksik olanlar kırmızı işaretlendi)", "hata");
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
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('pdf')"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('excel')"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div id="ihale_adim3_btn_container" style="margin-top: 20px; text-align: right;">
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim3Ileri()">
                        <i data-lucide="arrow-down" width="16" height="16"></i> İleri: İhale Onayı
                    </button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function adim3Ileri() {
    document.getElementById("check_adim3").style.display = "block";
    document.getElementById("acc_adim3").classList.remove("open");
    document.getElementById("acc_adim4").style.display = "block";
    ihaleAdim4Goster();
    document.getElementById("acc_adim4").classList.add("open");
}

function ihaleAdim4Goster() {
    const alan = document.getElementById("acc_adim4_icerik");
    alan.innerHTML = `
        <div style="padding: 15px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid #10B981; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between;">
            <label for="ebys_onay_check" style="font-size: 14px; font-weight: 500; cursor: pointer;">EBYS platformu üzerinden ihale onayı alındı mı?</label>
            <input type="checkbox" id="ebys_onay_check" style="width: 20px; height: 20px; cursor: pointer;" onchange="document.getElementById('adim4_btn_container').style.display = this.checked ? 'block' : 'none';">
        </div>
        <div id="adim4_btn_container" style="display: none; text-align: right;">
            <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim4Ileri()">
                <i data-lucide="arrow-down" width="16" height="16"></i> İleri: Harcama Ekleme
            </button>
        </div>
    `;
    lucide.createIcons();
}

function adim4Ileri() {
    document.getElementById("check_adim4").style.display = "block";
    document.getElementById("acc_adim4").classList.remove("open");
    document.getElementById("acc_adim5").style.display = "block";
    ihaleAdim5Goster();
    document.getElementById("acc_adim5").classList.add("open");
}

function sablonIndir() {
    yuklemeGoster("Şablon hazırlanıyor...");
    fetch(`${API}/sablon-hazirla`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            kalemler: ihaleGeciciVeri.kalemler,
            firmaVergiler: ihaleGeciciVeri.firmaVergiler
        })
    }).then(r => r.json()).then(v => {
        yuklemeGizle();
        if(v.basarili) {
            bildirimGoster(v.mesaj, "bilgi");
        } else {
            bildirimGoster("Hata: " + v.mesaj, "hata");
        }
    }).catch(e => {
        yuklemeGizle();
        bildirimGoster("Hata: " + e, "hata");
    });
}

function ihaleAdim5Goster() {
    const alan = document.getElementById("acc_adim5_icerik");
    alan.innerHTML = `
        <div class="settings-card" style="flex: 1; border: none; background: transparent; padding: 0;">
            <div class="settings-card-body" style="padding: 0;">
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 15px 0;">Şimdi MYS üzerinden Harcama Ekleme adımlarını gerçekleştirin. Yaklaşık Maliyet şablonu otomatik olarak hazırlanmıştır.</p>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border);">
                            <th style="padding: 10px; color: var(--fg-main); width: 50px;">Sıra</th>
                            <th style="padding: 10px; color: var(--fg-main);">Belge Adı</th>
                            <th style="padding: 10px; color: var(--fg-main); text-align: right;">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 15px 10px; color: var(--fg-sub);">1</td>
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Yaklaşık Maliyet Şablonu</td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="sablonIndir()"><i data-lucide="download" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div style="margin-top: 20px; text-align: right;">
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim5Ileri()">
                        <i data-lucide="arrow-down" width="16" height="16"></i> İleri: Piyasa Fiyat Araştırması
                    </button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function adim5Ileri() {
    document.getElementById("check_adim5").style.display = "block";
    document.getElementById("acc_adim5").classList.remove("open");
    document.getElementById("acc_adim6").style.display = "block";
    ihaleAdim6Goster();
    document.getElementById("acc_adim6").classList.add("open");
}

function ihaleAdim6Goster() {
    const alan6 = document.getElementById("acc_adim6_icerik");
    const bugun = new Date().toISOString().split('T')[0];

    alan6.innerHTML = `
        <div class="settings-card" style="flex: 1; border: none; background: transparent; padding: 0;">
            <div class="settings-card-body" style="padding: 0;">
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 15px 0;">Harcama ekleme tamamlandı. Son belgeleri üretebilirsiniz.</p>
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
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Fiyat İsteme</td>
                            <td style="padding: 15px 10px;">
                                <input type="date" id="tarih_ozel_fiyat" value="${bugun}" style="padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;">
                            </td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('ozel_fiyat_isteme', 'pdf', document.getElementById('tarih_ozel_fiyat').value)"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('ozel_fiyat_isteme', 'excel', document.getElementById('tarih_ozel_fiyat').value)"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 15px 10px; color: var(--fg-sub);">2</td>
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Piyasa Fiyat Araştırması Tutanağı</td>
                            <td style="padding: 15px 10px;">
                                <input type="date" id="tarih_piyasa_arastirmasi" value="${bugun}" style="padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;">
                            </td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('pdf', 'piyasa_arastirmasi')"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="fiyatGirisModalAc('excel', 'piyasa_arastirmasi')"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div style="margin-top: 20px; text-align: right;">
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim6Ileri()">
                        <i data-lucide="arrow-down" width="16" height="16"></i> İleri: VİF Girişi
                    </button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function adim6Ileri() {
    document.getElementById("check_adim6").style.display = "block";
    document.getElementById("acc_adim6").classList.remove("open");
    document.getElementById("acc_adim7").style.display = "block";
    ihaleAdim7Goster();
    document.getElementById("acc_adim7").classList.add("open");
}

function ihaleAdim7Goster() {
    const alan = document.getElementById("acc_adim7_icerik");
    alan.innerHTML = `
        <div style="padding: 15px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid #10B981; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between;">
            <label for="vif_onay_check" style="font-size: 14px; font-weight: 500; cursor: pointer;">TKYS platformundan VİF girişi yapıldı mı?</label>
            <input type="checkbox" id="vif_onay_check" style="width: 20px; height: 20px; cursor: pointer;" onchange="document.getElementById('adim7_btn_container').style.display = this.checked ? 'block' : 'none';">
        </div>
        <div id="adim7_btn_container" style="display: none; text-align: right;">
            <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim7Ileri()">
                <i data-lucide="arrow-down" width="16" height="16"></i> İleri: Muayene Kabul
            </button>
        </div>
    `;
    lucide.createIcons();
}

function adim7Ileri() {
    document.getElementById("check_adim7").style.display = "block";
    document.getElementById("acc_adim7").classList.remove("open");
    document.getElementById("acc_adim8").style.display = "block";
    ihaleAdim8Goster();
    document.getElementById("acc_adim8").classList.add("open");
}

function ihaleAdim8Goster() {
    const alan = document.getElementById("acc_adim8_icerik");
    const bugun = new Date().toISOString().split('T')[0];

    alan.innerHTML = `
        <div class="settings-card" style="flex: 1; border: none; background: transparent; padding: 0;">
            <div class="settings-card-body" style="padding: 0;">
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 15px 0;">İhale süreci tamamlanmıştır. Son olarak Muayene Kabul Belgesini üretebilirsiniz.</p>
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border);">
                            <th style="padding: 10px; color: var(--fg-main); width: 50px;">Sıra</th>
                            <th style="padding: 10px; color: var(--fg-main);">Belge Adı</th>
                            <th style="padding: 10px; color: var(--fg-main);">Belge Tarihi</th>
                            <th style="padding: 10px; color: var(--fg-main); text-align: right;">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 15px 10px; color: var(--fg-sub);">1</td>
                            <td style="padding: 15px 10px; font-weight: bold; color: var(--fg-main);">Muayene Kabul Belgesi</td>
                            <td style="padding: 15px 10px;">
                                <input type="date" id="tarih_muayene_kabul" value="${bugun}" style="padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;">
                            </td>
                            <td style="padding: 15px 10px; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="btn" style="background-color: #EF4444; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('muayene_kabul', 'pdf', document.getElementById('tarih_muayene_kabul').value)"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn" style="background-color: #10B981; color: white; padding: 6px 12px; font-size: 13px;" onclick="belgeUret('muayene_kabul', 'excel', document.getElementById('tarih_muayene_kabul').value)"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div id="ihale_adim8_btn_container" style="margin-top: 20px; text-align: right;">
                    <button class="btn" style="background-color: #3B82F6; color: white; padding: 8px 20px; font-weight: bold;" onclick="adim8Ileri()"><i data-lucide="arrow-down" width="16" height="16"></i> İleri: Ödeme Emri Oluşturma</button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function adim8Ileri() {
    document.getElementById("acc_adim8").classList.remove("open");
    document.getElementById("check_adim8").style.display = "inline-block";
    
    document.getElementById("acc_adim9").style.display = "block";
    ihaleAdim9Goster();
    document.getElementById("acc_adim9").classList.add("open");
}

function ihaleAdim9Goster() {
    const alan = document.getElementById("acc_adim9_icerik");
    const bugun = new Date().toISOString().split('T')[0];

    alan.innerHTML = `
        <div class="settings-card" style="flex: 1; border: none; background: transparent; padding: 0;">
            <div class="settings-card-body" style="padding: 0;">
                <p style="color: var(--fg-main); font-weight: bold; font-size: 15px; margin: 0 0 10px 0;"><i data-lucide="alert-circle" width="18" height="18" style="color: #F59E0B; margin-right: 5px; vertical-align: middle;"></i> Bu adımda şimdi MYS'den ödeme emri oluşturmanız gerekmektedir.</p>
                <p style="color: var(--fg-sub); font-size: 13px; margin: 0 0 15px 0;">Ek olarak şu belgeleri ödeme emri belgesine eklemeniz gerekmektedir (MYS'ye Yüklerken):</p>
                
                <div style="background-color: var(--bg-main); padding: 15px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 20px;">
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; cursor: pointer;">
                        <input type="checkbox" style="width: 16px; height: 16px;">
                        <span style="color: var(--fg-main); font-size: 14px;">Fatura</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; cursor: pointer;">
                        <input type="checkbox" style="width: 16px; height: 16px;">
                        <span style="color: var(--fg-main); font-size: 14px;">Borcu Yoktur Belgesi</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; cursor: pointer;">
                        <input type="checkbox" style="width: 16px; height: 16px;">
                        <span style="color: var(--fg-main); font-size: 14px;">Muayene Komisyonu Kabul Belgesi</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; cursor: pointer;">
                        <input type="checkbox" style="width: 16px; height: 16px;">
                        <span style="color: var(--fg-main); font-size: 14px;">Varlık İşlem Fişi (VİF)</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 0px; cursor: pointer;">
                        <input type="checkbox" style="width: 16px; height: 16px;">
                        <span style="color: var(--fg-main); font-size: 14px;">Piyasa Fiyat Araştırması Tutanağı</span>
                    </label>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; background-color: var(--bg-card); padding: 15px; border-radius: 6px; border: 1px dashed var(--border);">
                    <div style="display: flex; flex-direction: column; gap: 5px;">
                        <span style="color: var(--fg-main); font-weight: bold; font-size: 14px;">MYS Yaklaşık Maliyet Şablonu</span>
                        <span style="color: var(--fg-sub); font-size: 12px;">MYS'ye yüklenecek excel formatında şablon</span>
                    </div>
                    <div>
                        <button class="btn" style="background-color: #10B981; color: white; padding: 8px 15px; font-size: 13px; font-weight: bold;" onclick="belgeUret('mys_yaklasik_maliyet', 'excel', '${bugun}')"><i data-lucide="download" width="16" height="16"></i> Excel Olarak İndir</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function ihaleKalemTablosunuCiz() {
    const govde = document.getElementById("ihale_kalemleri_govde");
    let html = "";
    ihaleGeciciVeri.kalemler.forEach((k, idx) => {
        k.sira = idx + 1;
        html += `
            <tr data-index="${idx}">
                <td style="text-align:center; color: var(--fg-sub); font-size:11px;">${k.sira}</td>
                <td><input type="text" class="kalem-input" data-field="cins" value="${k.cins}" placeholder="Cinsi"></td>
                <td><input type="text" class="kalem-input" data-field="ozellik" value="${k.ozellik}" placeholder="Özellikleri"></td>
                <td><input type="number" class="kalem-input" style="text-align:center;" data-field="miktar" value="${k.miktar}" placeholder="0"></td>
                <td>
                    <select class="kalem-input" style="text-align:center; width: 100%; padding: 8px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px;" data-field="birim">
                        <option value="">Seçiniz</option>
                        ${olcuBirimleri.map(b => `<option value="${b}" ${k.birim === b ? 'selected' : ''}>${b}</option>`).join('')}
                    </select>
                </td>
                <td><button class="btn-kalem-sil" onclick="ihaleKalemSatiriSil(${idx})"><i data-lucide="x" width="14" height="14"></i></button></td>
            </tr>
        `;
    });
    govde.innerHTML = html;
    
    document.querySelectorAll(".kalem-input").forEach(input => {
        input.addEventListener('input', (e) => {
            const tr = e.target.closest("tr");
            const idx = parseInt(tr.getAttribute("data-index"));
            const field = e.target.getAttribute("data-field");
            ihaleGeciciVeri.kalemler[idx][field] = e.target.value;
            ihaleTaslaginiKaydet();
        });
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tr = e.target.closest("tr");
                const idx = parseInt(tr.getAttribute("data-index"));
                if (idx === ihaleGeciciVeri.kalemler.length - 1) {
                    ihaleKalemSatiriEkle();
                } else {
                    const nextRow = tr.nextElementSibling;
                    if (nextRow) nextRow.querySelector(`[data-field="${e.target.getAttribute("data-field")}"]`).focus();
                }
            }
        });
    });
    
    lucide.createIcons();
}

function ihaleFirmaTablosunuCiz() {
    const govde = document.getElementById("ihale_firmalar_govde");
    if (!govde) return;
    let html = "";
    if(!ihaleGeciciVeri.firmaVergiler) ihaleGeciciVeri.firmaVergiler = ["", "", ""];
    
    ihaleGeciciVeri.firmalar.forEach((firmaAdi, idx) => {
        let vNo = ihaleGeciciVeri.firmaVergiler[idx] || "";
        let title = (idx === 0) ? "1. Kurum/Kişi" : `${idx + 1}. Kurum/Kişi`;
        html += `
            <div style="flex:1; min-width:220px; box-sizing: border-box; display:flex; flex-direction:column; gap:5px; background:var(--bg-input); padding:10px; border-radius:6px; border:1px solid var(--border);">
                <div style="display:flex; justify-content:space-between;">
                    <label style="font-size: 11px; font-weight: bold; color: var(--fg-main);">${title}</label>
                    <button class="icon-btn" style="color:#EF4444; padding:0;" onclick="ihaleFirmaSil(${idx})" title="Sil"><i data-lucide="trash-2" width="14" height="14"></i></button>
                </div>
                <input type="text" class="firma-input" data-index="${idx}" style="box-sizing: border-box; width:100%; padding: 6px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px; font-size:12px;" placeholder="Kurum/Kişi Adı" value="${firmaAdi}">
                <input type="text" class="firma-vergi-input" data-index="${idx}" style="box-sizing: border-box; width:100%; padding: 6px; background: var(--bg-main); color: var(--fg-main); border: 1px solid var(--border); border-radius: 4px; font-size:12px;" placeholder="Vergi No / T.C." value="${vNo}">
            </div>
        `;
    });
    govde.innerHTML = html;

    document.querySelectorAll(".firma-input").forEach(input => {
        input.addEventListener('change', (e) => {
            const idx = parseInt(e.target.getAttribute("data-index"));
            ihaleGeciciVeri.firmalar[idx] = e.target.value;
            ihaleTaslaginiKaydet();
            if(document.getElementById("fiyat_giris_modal").style.display === "flex") {
                fiyatGirisTablosunuCiz();
            }
        });
    });
    document.querySelectorAll(".firma-vergi-input").forEach(input => {
        input.addEventListener('change', (e) => {
            const idx = parseInt(e.target.getAttribute("data-index"));
            ihaleGeciciVeri.firmaVergiler[idx] = e.target.value;
            ihaleTaslaginiKaydet();
        });
    });
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function ihaleFirmaEkle() {
    ihaleGeciciVeri.firmalar.push("");
    ihaleGeciciVeri.firmaVergiler.push("");
    ihaleTaslaginiKaydet();
    ihaleFirmaTablosunuCiz();
    if(document.getElementById("fiyat_giris_modal").style.display === "flex") {
        fiyatGirisTablosunuCiz();
    }
}

function ihaleFirmaSil(idx) {
    ihaleGeciciVeri.firmalar.splice(idx, 1);
    ihaleGeciciVeri.firmaVergiler.splice(idx, 1);
    if(ihaleGeciciVeri.kalemler) {
        ihaleGeciciVeri.kalemler.forEach(k => {
            if(k.fiyatlar && k.fiyatlar.length > idx) {
                k.fiyatlar.splice(idx, 1);
            }
        });
    }
    ihaleTaslaginiKaydet();
    ihaleFirmaTablosunuCiz();
    if(document.getElementById("fiyat_giris_modal").style.display === "flex") {
        fiyatGirisTablosunuCiz();
    }
}

function ihaleKalemSatiriEkle() {
    ihaleGeciciVeri.kalemler.push({sira: ihaleGeciciVeri.kalemler.length + 1, cins: "", ozellik: "", miktar: "", birim: ""});
    ihaleTaslaginiKaydet();
    ihaleKalemTablosunuCiz();
    
    setTimeout(() => {
        const rows = document.querySelectorAll("#ihale_kalemleri_govde tr");
        if(rows.length > 0) {
            const lastRowInputs = rows[rows.length - 1].querySelectorAll("input");
            if(lastRowInputs.length > 0) lastRowInputs[0].focus();
        }
    }, 50);
}

function ihaleKalemSatiriSil(idx) {
    if (ihaleGeciciVeri.kalemler.length <= 1) {
        bildirimGoster("En az 1 kalem olmalıdır.", "uyari");
        return;
    }
    ihaleGeciciVeri.kalemler.splice(idx, 1);
    ihaleTaslaginiKaydet();
    ihaleKalemTablosunuCiz();
}

async function ihaleKomisyonModalAc() {
    yuklemeGoster("Personel listesi alınıyor...");
    try {
        if (typeof tumPersoneller === 'undefined' || tumPersoneller.length === 0) {
            const res = await fetch("http://localhost:8000/personeller");
            const responseData = await res.json();
            tumPersoneller = responseData.personeller || [];
        }
        
        const gorevIds = [
            "ihale_kom_yaklasik_1", "ihale_kom_yaklasik_2", "ihale_kom_yaklasik_3",
            "ihale_kom_piyasa_1", "ihale_kom_piyasa_2", "ihale_kom_piyasa_3",
            "ihale_kom_muayene_1", "ihale_kom_muayene_2", "ihale_kom_muayene_3"
        ];
        
        gorevIds.forEach(id => {
            const spanEl = document.getElementById("text_" + id);
            const btnSec = document.getElementById("btn_sec_" + id);
            const btnSil = document.getElementById("btn_sil_" + id);
            if (spanEl) {
                if (ihaleKomisyonSecimleri[id]) {
                    spanEl.innerText = ihaleKomisyonSecimleri[id];
                    spanEl.style.fontWeight = "bold";
                    spanEl.style.color = "var(--fg-main)";
                    spanEl.style.fontStyle = "normal";
                    if(btnSec) btnSec.style.display = "none";
                    if(btnSil) btnSil.style.display = "inline-block";
                    spanEl.parentElement.style.backgroundColor = "transparent";
                } else {
                    spanEl.innerText = "Seçilmedi";
                    spanEl.style.fontWeight = "normal";
                    spanEl.style.color = "var(--fg-sub)";
                    spanEl.style.fontStyle = "italic";
                    if(btnSec) btnSec.style.display = "inline-block";
                    if(btnSil) btnSil.style.display = "none";
                    
                    if (ihaleKomisyonHataModu) {
                        spanEl.parentElement.style.backgroundColor = "rgba(239, 68, 68, 0.15)";
                    } else {
                        spanEl.parentElement.style.backgroundColor = "transparent";
                    }
                }
            }
        });
        
        document.getElementById("ihale_komisyon_modal").style.display = "flex";
    } catch (e) {
        console.error("Modal açılamadı: ", e);
        bildirimGoster("Hata: " + e.message, "hata");
    } finally {
        yuklemeGizle();
    }
}



function ihaleKomisyonKaydet() {
    // ihaleKomisyonSecimleri is already updated dynamically by personelAta and personelSil
    localStorage.setItem("ihaleKomisyonSecimleri", JSON.stringify(ihaleKomisyonSecimleri));
    
    // Eğer tüm personeller tamamsa hata modunu kapat
    const gorevIds = [
        "ihale_kom_yaklasik_1", "ihale_kom_yaklasik_2", "ihale_kom_yaklasik_3",
        "ihale_kom_piyasa_1", "ihale_kom_piyasa_2", "ihale_kom_piyasa_3",
        "ihale_kom_muayene_1", "ihale_kom_muayene_2", "ihale_kom_muayene_3"
    ];
    let hepsiTamam = true;
    gorevIds.forEach(id => {
        if (!ihaleKomisyonSecimleri[id]) hepsiTamam = false;
    });
    if (hepsiTamam) ihaleKomisyonHataModu = false;
    
    bildirimGoster("Komisyon üyeleri başarıyla kaydedildi.", "bilgi");
    modalKapat("ihale_komisyon_modal");
}

let secimIcinGorevId = null;

function personelSecimEkraniAc(gorevId) {
    secimIcinGorevId = gorevId;
    document.getElementById("personel_arama_input").value = "";
    personelHavuzunuCiz(tumPersoneller);
    document.getElementById("personel_havuz_modal").style.display = "flex";
    document.getElementById("personel_arama_input").focus();
}

function personelHavuzunuCiz(liste) {
    const div = document.getElementById("personel_havuz_liste");
    if (!liste || liste.length === 0) {
        div.innerHTML = "<div style='padding:10px; color:var(--fg-sub); text-align:center;'>Personel bulunamadı.</div>";
        return;
    }
    
    let html = "";
    liste.forEach(p => {
        let adEscaped = p.ad.replace(/'/g, "\\'");
        let zatenSeciliMi = Object.values(ihaleKomisyonSecimleri).includes(p.ad);
        let extraInfo = zatenSeciliMi ? "<span style='font-size:11px; color:#F59E0B;'>(Görevli)</span>" : "";
        
        html += "<div class='personel-havuz-satir' onclick='personelAta(\"" + adEscaped + "\")'>" +
            "<span style='font-weight:600;'>" + p.ad + "</span>" +
            extraInfo +
        "</div>";
    });
    div.innerHTML = html;
}

function personelAra() {
    const aranan = document.getElementById("personel_arama_input").value.toLocaleLowerCase('tr-TR');
    const filtrelenmis = tumPersoneller.filter(p => p.ad.toLocaleLowerCase('tr-TR').includes(aranan));
    personelHavuzunuCiz(filtrelenmis);
}

function personelAta(ad) {
    if (!secimIcinGorevId) return;
    
    ihaleKomisyonSecimleri[secimIcinGorevId] = ad;
    
    const spanEl = document.getElementById("text_" + secimIcinGorevId);
    const btnSec = document.getElementById("btn_sec_" + secimIcinGorevId);
    const btnSil = document.getElementById("btn_sil_" + secimIcinGorevId);
    
    if (spanEl) {
        spanEl.innerText = ad;
        spanEl.style.fontWeight = "bold";
        spanEl.style.color = "var(--fg-main)";
        spanEl.style.fontStyle = "normal";
        spanEl.parentElement.style.backgroundColor = "transparent";
    }
    if (btnSec) btnSec.style.display = "none";
    if (btnSil) btnSil.style.display = "inline-block";
    
    localStorage.setItem("ihaleKomisyonSecimleri", JSON.stringify(ihaleKomisyonSecimleri));
    
    modalKapat("personel_havuz_modal");
}

function personelSil(gorevId) {
    ihaleKomisyonSecimleri[gorevId] = "";
    
    const spanEl = document.getElementById("text_" + gorevId);
    const btnSec = document.getElementById("btn_sec_" + gorevId);
    const btnSil = document.getElementById("btn_sil_" + gorevId);
    
    if (spanEl) {
        spanEl.innerText = "Seçilmedi";
        spanEl.style.fontWeight = "normal";
        spanEl.style.color = "var(--fg-sub)";
        spanEl.style.fontStyle = "italic";
    }
    if (btnSec) btnSec.style.display = "inline-block";
    if (btnSil) btnSil.style.display = "none";
    
    localStorage.setItem("ihaleKomisyonSecimleri", JSON.stringify(ihaleKomisyonSecimleri));
}


// Fiyat Giriş Modal Mantığı
let seciliBelgeFormat = "";
let seciliBelgeTuru = "yaklasik_maliyet";

function fiyatGirisModalAc(format, turu = 'yaklasik_maliyet') {
    seciliBelgeFormat = format;
    seciliBelgeTuru = turu;
    ihaleFirmaTablosunuCiz();
    fiyatGirisTablosunuCiz();
    document.getElementById("fiyat_giris_modal").style.display = "flex";
}

function fiyatGirisTablosunuCiz() {
    const thead = document.getElementById("fiyat_giris_thead");
    const tbody = document.getElementById("fiyat_giris_tbody");
    const tfoot = document.getElementById("fiyat_giris_tfoot");
    
    // Header
    let theadHtml = `
        <tr style="background-color: var(--bg-main);">
            <th rowspan="2" style="width: 250px;">Mal/Hizmet Cinsi</th>
            <th rowspan="2" style="width: 60px; text-align:center;">Miktar</th>
    `;
    ihaleGeciciVeri.firmalar.forEach((firma, idx) => {
        let fAd = firma.trim() === "" ? `Firma ${idx+1}` : firma.substring(0,15);
        let fVergi = (ihaleGeciciVeri.firmaVergiler && ihaleGeciciVeri.firmaVergiler[idx]) ? ihaleGeciciVeri.firmaVergiler[idx].trim() : "";
        let vergiStr = "";
        if (fVergi.length === 10) {
            vergiStr = `<br><span style="font-size:10px; color:var(--fg-sub);">(Vergi No: ${fVergi})</span>`;
        } else if (fVergi.length === 11) {
            vergiStr = `<br><span style="font-size:10px; color:var(--fg-sub);">(T.C. No: ${fVergi})</span>`;
        } else if (fVergi.length > 0) {
            vergiStr = `<br><span style="font-size:10px; color:var(--fg-sub);">(${fVergi})</span>`;
        }
        theadHtml += `<th colspan="2" style="text-align:center; color:#3B82F6;">${fAd}${vergiStr}</th>`;
    });
    theadHtml += `
            <th colspan="2" style="text-align:center; color:#10B981;">İdarece Tespit Edilen<br>Yaklaşık Maliyet Hesabı (KDV Hariç)</th>
        </tr>
        <tr style="background-color: var(--bg-main);">
    `;
    ihaleGeciciVeri.firmalar.forEach(() => {
        theadHtml += `
            <th style="width: 80px; text-align:center;">Birim Fiyat</th>
            <th style="width: 90px; text-align:center;">Toplam Fiyat</th>
        `;
    });
    theadHtml += `
            <th style="width: 80px; text-align:center;">Birim Yak. Mal.</th>
            <th style="width: 90px; text-align:center;">Top. Yak. Mal.</th>
        </tr>
    `;
    thead.innerHTML = document.createElement("table").innerHTML = theadHtml;

    // Body
    let tbodyHtml = "";
    ihaleGeciciVeri.kalemler.forEach((k, idx) => {
        if(!k.fiyatlar) k.fiyatlar = [];
        let trHtml = `
            <tr data-index="${idx}">
                <td style="font-weight:bold;">${k.cins}</td>
                <td style="text-align:center;" class="td-miktar">${k.miktar}</td>
        `;
        ihaleGeciciVeri.firmalar.forEach((_, fidx) => {
            let fyt = (k.fiyatlar && k.fiyatlar[fidx] !== undefined) ? k.fiyatlar[fidx] : "";
            trHtml += `
                <td><input type="number" step="0.01" class="fiyat-modal-input" data-fidx="${fidx}" style="width:100%; padding:6px; border:1px solid var(--border); border-radius:4px; text-align:right;" value="${fyt}" placeholder="0.00"></td>
                <td style="text-align:right; color:var(--fg-sub);" class="td-toplam" data-fidx="${fidx}">0.00</td>
            `;
        });
        trHtml += `
                <td style="text-align:right; font-weight:bold; color:#10B981;" class="td-yak-birim">0.00</td>
                <td style="text-align:right; font-weight:bold; color:#10B981;" class="td-yak-toplam">0.00</td>
            </tr>
        `;
        tbodyHtml += trHtml;
    });
    tbody.innerHTML = tbodyHtml;

    // Footer
    let tfootHtml = `
        <tr>
            <td colspan="2" style="text-align:right; padding:10px;">KDV HARİÇ GENEL TOPLAM:</td>
    `;
    ihaleGeciciVeri.firmalar.forEach((_, fidx) => {
        tfootHtml += `
            <td></td>
            <td style="text-align:right; padding:10px;" id="tf_genel_${fidx}">0.00</td>
        `;
    });
    tfootHtml += `
            <td></td>
            <td style="text-align:right; padding:10px; color:#10B981;" id="tf_genel_yak">0.00</td>
        </tr>
    `;
    tfoot.innerHTML = tfootHtml;

    // Listeners
    document.querySelectorAll(".fiyat-modal-input").forEach(input => {
        input.addEventListener('input', (e) => {
            const tr = e.target.closest("tr");
            const idx = parseInt(tr.getAttribute("data-index"));
            const fidx = parseInt(e.target.getAttribute("data-fidx"));
            let val = parseFloat(e.target.value);
            if(!ihaleGeciciVeri.kalemler[idx].fiyatlar) ihaleGeciciVeri.kalemler[idx].fiyatlar = [];
            ihaleGeciciVeri.kalemler[idx].fiyatlar[fidx] = isNaN(val) ? "" : val;
            ihaleTaslaginiKaydet();
            fiyatGirisHesapla();
        });
    });

    fiyatGirisHesapla();
}

function fiyatGirisHesapla() {
    let genelToplamlar = Array(ihaleGeciciVeri.firmalar.length).fill(0);
    let genelYaklasikToplam = 0;

    const rows = document.querySelectorAll("#fiyat_giris_tbody tr");
    rows.forEach(tr => {
        const idx = parseInt(tr.getAttribute("data-index"));
        const k = ihaleGeciciVeri.kalemler[idx];
        const miktar = parseFloat(k.miktar) || 0;
        
        let yaklasikBirimTop = 0;
        let yaklasikGecerliFirmaSayisi = 0;

        ihaleGeciciVeri.firmalar.forEach((_, fidx) => {
            let bf = parseFloat((k.fiyatlar && k.fiyatlar[fidx]) ? k.fiyatlar[fidx] : 0) || 0;
            let tf = bf * miktar;
            
            if(bf > 0) {
                yaklasikBirimTop += bf;
                yaklasikGecerliFirmaSayisi++;
            }
            genelToplamlar[fidx] += tf;

            tr.querySelector(`.td-toplam[data-fidx="${fidx}"]`).innerText = tf > 0 ? tf.toFixed(2) : "0.00";
        });

        let yaklasikBirim = 0;
        let yaklasikToplam = 0;
        if(yaklasikGecerliFirmaSayisi > 0) {
            yaklasikBirim = yaklasikBirimTop / yaklasikGecerliFirmaSayisi;
            yaklasikToplam = yaklasikBirim * miktar;
            genelYaklasikToplam += yaklasikToplam;
        }

        tr.querySelector(".td-yak-birim").innerText = yaklasikBirim > 0 ? yaklasikBirim.toFixed(2) : "0.00";
        tr.querySelector(".td-yak-toplam").innerText = yaklasikToplam > 0 ? yaklasikToplam.toFixed(2) : "0.00";
    });

    ihaleGeciciVeri.firmalar.forEach((_, fidx) => {
        document.getElementById(`tf_genel_${fidx}`).innerText = genelToplamlar[fidx] > 0 ? genelToplamlar[fidx].toFixed(2) : "0.00";
    });
    document.getElementById("tf_genel_yak").innerText = genelYaklasikToplam > 0 ? genelYaklasikToplam.toFixed(2) : "0.00";
}

function fiyatGirisTamamla() {
    modalKapat("fiyat_giris_modal");
    let inputId = seciliBelgeTuru === 'piyasa_arastirmasi' ? 'tarih_piyasa_arastirmasi' : 'tarih_yaklasik_maliyet';
    let inputEl = document.getElementById(inputId);
    let tarih = inputEl ? inputEl.value : "";
    belgeUret(seciliBelgeTuru, seciliBelgeFormat, tarih);
}

// ==========================================
// TEBLİĞ MODÜLÜ UI FONKSİYONLARI
// ==========================================
function tebligModuDegistir(mod) {
    const btnToplu = document.getElementById('btn_alt_toplu');
    const btnBireysel = document.getElementById('btn_alt_bireysel');
    const viewToplu = document.getElementById('view_toplu_teblig');
    const viewBireysel = document.getElementById('view_bireysel_teblig');

    if (!btnToplu || !btnBireysel || !viewToplu || !viewBireysel) return;

    if (mod === 'toplu') {
        btnToplu.style.background = 'var(--tree-sel)';
        btnToplu.style.color = 'white';
        
        btnBireysel.style.background = 'transparent';
        btnBireysel.style.color = 'var(--fg-sub)';
        
        viewToplu.style.display = 'flex';
        viewBireysel.style.display = 'none';
    } else {
        btnBireysel.style.background = 'var(--tree-sel)';
        btnBireysel.style.color = 'white';
        
        btnToplu.style.background = 'transparent';
        btnToplu.style.color = 'var(--fg-sub)';
        
        viewToplu.style.display = 'none';
        viewBireysel.style.display = 'flex';
    }
}

// ==========================================
// YARDIM MODÜLÜ UI FONKSİYONLARI
// ==========================================
function yardimIcerikGoster(id, btnElement) {
    // Tüm içerikleri gizle
    const icerikler = document.querySelectorAll('.yardim-icerik');
    icerikler.forEach(el => el.style.display = 'none');
    
    // Tüm butonlardan active sınıfını kaldır
    const butonlar = document.querySelectorAll('.yardim-menu-btn');
    butonlar.forEach(btn => btn.classList.remove('active'));
    
    // Seçileni göster ve butonunu aktif yap
    const secilenIcerik = document.getElementById(id);
    if (secilenIcerik) secilenIcerik.style.display = 'block';
    
    if (btnElement) {
        btnElement.classList.add('active');
    }
}
