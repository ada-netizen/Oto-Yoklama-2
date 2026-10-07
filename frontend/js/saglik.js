// Sağlık İzinleri Yönetimi

let aktifSaglikPersoneli = [];

async function apiIstegi(endpoint, method = 'GET', body = null) {
    const options = { method };
    if (body) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
    }
    const res = await fetch(`${API}${endpoint}`, options);
    return await res.json();
}

async function saglikYukle() {
    document.getElementById('saglik_yil').textContent = new Date().getFullYear();
    try {
        const response = await apiIstegi('/saglik/liste');
        if (response.basarili) {
            aktifSaglikPersoneli = response.veri;
            saglikTablosunuCiz();
            saglikPersonelSelectDoldur();
        } else {
            bildirimGoster('Veri yüklenemedi: ' + response.mesaj, 'hata');
        }
    } catch (e) {
        console.error("Sağlık verisi yüklenirken hata:", e);
    }
}

function saglikTablosunuCiz() {
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


function saglikPersonelSelectDoldur() {
    const select = document.getElementById('saglik_personel_sec');
    select.innerHTML = '<option value="" style="background: var(--bg-card); color: var(--fg-main);">-- Personel Seç --</option>';
    aktifSaglikPersoneli.forEach(p => {
        select.innerHTML += `<option value="${p.personel_ad}" style="background: var(--bg-card); color: var(--fg-main);">${p.personel_ad}</option>`;
    });
}

let saglikFlatpickr = null;

function saglikModalAc() {
    document.getElementById('saglik_personel_sec').value = '';
    document.getElementById('saglik_tarih_range').value = '';
    document.getElementById('saglik_gun').value = '1';
    document.getElementById('saglik_aciklama').value = '';
    
    if (saglikFlatpickr) {
        saglikFlatpickr.destroy();
    }
    
    saglikFlatpickr = flatpickr(document.getElementById('saglik_tarih_range'), {
        locale: "tr",
        mode: "range",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d.m.Y",
        theme: "dark",
        onChange: saglikGunHesapla
    });
    
    document.getElementById('modal_saglik_ekle').style.display = 'flex';
}

function saglikModalKapat() {
    document.getElementById('modal_saglik_ekle').style.display = 'none';
}

function saglikGunHesapla(selectedDates) {
    let diffDays = 1;
    if (selectedDates && selectedDates.length > 0) {
        const d1 = selectedDates[0];
        const d2 = selectedDates.length > 1 ? selectedDates[1] : selectedDates[0];
        
        const diffTime = Math.abs(d2 - d1);
        diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; 
    }
    document.getElementById('saglik_gun').value = diffDays;
    document.getElementById('lbl_saglik_gun').textContent = `(${diffDays} Gün)`;
}

async function saglikKaydet() {
    const personel = document.getElementById('saglik_personel_sec').value;
    const tarihDegeri = document.getElementById('saglik_tarih_range').value;
    const gun = document.getElementById('saglik_gun').value;
    const aciklama = document.getElementById('saglik_aciklama').value;
    
    if (!personel || !tarihDegeri || !gun) {
        bildirimGoster('Personel, Tarih ve Gün Sayısı zorunludur.', 'uyari');
        return;
    }
    
    let bas = tarihDegeri;
    let bit = tarihDegeri;
    if (tarihDegeri.includes(' to ')) {
        const parcalar = tarihDegeri.split(' to ');
        bas = parcalar[0];
        bit = parcalar[1];
    }
    
    try {
        const response = await apiIstegi('/saglik/ekle', 'POST', {
            personel_ad: personel,
            baslangic_tarihi: bas,
            bitis_tarihi: bit,
            gun_sayisi: parseInt(gun),
            aciklama: aciklama
        });
        
        if (response.basarili) {
            bildirimGoster('Rapor başarıyla eklendi.', 'basarili');
            saglikModalKapat();
            saglikYukle();
        } else {
            bildirimGoster('Rapor eklenemedi: ' + response.mesaj, 'hata');
        }
    } catch (e) {
        bildirimGoster('Bir hata oluştu.', 'hata');
    }
}



async function saglikDetayGoster(personelAd, oncedenKesilen = 0) {
    document.getElementById('detay_personel_ad').textContent = personelAd;
    

    
    const tbody = document.getElementById('tbody_saglik_detay');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Yükleniyor...</td></tr>';
    document.getElementById('modal_saglik_detay').style.display = 'flex';
    
    try {
        const response = await apiIstegi(`/saglik/raporlar/${encodeURIComponent(personelAd)}`);
        if (response.basarili) {
            tbody.innerHTML = '';
            if (response.veri.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Rapor bulunamadı.</td></tr>';
            } else {
                response.veri.forEach(r => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${r.baslangic}</td>
                        <td>${r.bitis || r.baslangic}</td>
                        <td>${r.gun}</td>
                        <td>${r.aciklama || '-'}</td>
                        <td>
                            <div style="display: flex; gap: 5px; justify-content: center;">
                                <button class="btn btn-icon btn-ayarlar" style="padding: 4px 8px;" onclick="saglikRaporDuzenlemeAc(${r.id}, '${personelAd}', '${r.baslangic}', '${r.bitis || r.baslangic}', ${r.gun}, '${r.aciklama || ''}')" title="Düzenle">
                                    <i data-lucide="edit" height="14" width="14"></i>
                                </button>
                                <button class="btn btn-icon btn-kirmizi" style="padding: 4px 8px;" onclick="saglikRaporSil(${r.id}, '${personelAd}')" title="Sil">
                                    <i data-lucide="trash-2" height="14" width="14"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                lucide.createIcons();
            }
        }
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Yüklenirken hata oluştu.</td></tr>';
    }
}

async function saglikRaporSil(id, personelAd) {
    if (!confirm('Bu raporu silmek istediğinize emin misiniz?')) return;
    
    try {
        const response = await apiIstegi(`/saglik/sil/${id}`, 'DELETE');
        if (response.basarili) {
            bildirimGoster('Rapor silindi.', 'basarili');
            saglikDetayGoster(personelAd); // refresh modal
            saglikYukle(); // refresh main table
        } else {
            bildirimGoster('Silinemedi: ' + response.mesaj, 'hata');
        }
    } catch (e) {
        bildirimGoster('Bir hata oluştu.', 'hata');
    }
}

let duzenleFlatpickr = null;

function saglikRaporDuzenlemeAc(id, personelAd, bas, bit, gun, aciklama) {
    document.getElementById('duzenle_rapor_id').value = id;
    document.getElementById('duzenle_personel_ad').value = personelAd;
    document.getElementById('duzenle_gun').value = gun;
    document.getElementById('duzenle_aciklama').value = aciklama === '-' ? '' : aciklama;
    
    if (duzenleFlatpickr) {
        duzenleFlatpickr.destroy();
    }
    
    let defaultDates = [bas];
    if (bas !== bit) {
        defaultDates.push(bit);
    }

    document.getElementById('lbl_duzenle_gun').textContent = `(${gun} Gün)`;
    
    duzenleFlatpickr = flatpickr(document.getElementById('duzenle_tarih_range'), {
        locale: "tr",
        mode: "range",
        dateFormat: "Y-m-d",
        defaultDate: defaultDates,
        altInput: true,
        altFormat: "d.m.Y",
        theme: "dark",
        onChange: function(selectedDates) {
            let diffDays = 1;
            if (selectedDates && selectedDates.length > 0) {
                const d1 = selectedDates[0];
                const d2 = selectedDates.length > 1 ? selectedDates[1] : selectedDates[0];
                const diffTime = Math.abs(d2 - d1);
                diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; 
            }
            document.getElementById('duzenle_gun').value = diffDays;
            document.getElementById('lbl_duzenle_gun').textContent = `(${diffDays} Gün)`;
        }
    });
    
    document.getElementById('modal_saglik_duzenle').style.display = 'flex';
}

async function saglikGuncelle() {
    const id = document.getElementById('duzenle_rapor_id').value;
    const personelAd = document.getElementById('duzenle_personel_ad').value;
    const tarihDegeri = document.getElementById('duzenle_tarih_range').value;
    const gun = document.getElementById('duzenle_gun').value;
    const aciklama = document.getElementById('duzenle_aciklama').value;
    
    if (!tarihDegeri || !gun) {
        bildirimGoster('Tarih ve Gün Sayısı zorunludur.', 'uyari');
        return;
    }
    
    let bas = tarihDegeri;
    let bit = tarihDegeri;
    if (tarihDegeri.includes(' to ')) {
        const parcalar = tarihDegeri.split(' to ');
        bas = parcalar[0];
        bit = parcalar[1];
    }
    
    try {
        const response = await apiIstegi(`/saglik/duzenle/${id}`, 'PUT', {
            personel_ad: personelAd,
            baslangic_tarihi: bas,
            bitis_tarihi: bit,
            gun_sayisi: parseInt(gun),
            aciklama: aciklama
        });
        
        if (response.basarili) {
            bildirimGoster('Rapor güncellendi.', 'basarili');
            document.getElementById('modal_saglik_duzenle').style.display = 'none';
            saglikDetayGoster(personelAd); // refresh modal
            saglikYukle(); // refresh main table
        } else {
            bildirimGoster('Güncellenemedi: ' + response.mesaj, 'hata');
        }
    } catch (e) {
        bildirimGoster('Bir hata oluştu.', 'hata');
    }
}



async function manuelKesintiKaydet(personelAd, deger) {
    const kesintiDegeri = parseInt(deger) || 0;
    try {
        const response = await apiIstegi('/saglik/kesinti-guncelle', 'POST', {
            personel_ad: personelAd,
            onceden_kesilen: kesintiDegeri
        });
        
        if (response.basarili) {
            saglikYukle(); // Refresh to recalculate remaining days
        } else {
            bildirimGoster('Güncellenemedi: ' + response.mesaj, 'hata');
        }
    } catch (e) {
        bildirimGoster('Bir hata oluştu.', 'hata');
    }
}
