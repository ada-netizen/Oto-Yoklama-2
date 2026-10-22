/**
 * OKUL YÖNETİM SİSTEMİ - KURUMSAL AĞ & YÖNETİCİ KONTROL PANELİ (admin.js)
 * 
 * Özellikler:
 * - Kullanıcı Listesi & Canlı Çevrimiçi/Son Görülme Durumu (🟢 Çevrimiçi / ⚪ Son Görülme)
 * - Rol ve İzin Yönetimi (Öğrenci, İzin, Tebliğ, Terfi, İhale, Admin)
 * - Yeni Kullanıcı Hesabı Ekleme (Okul Personeliyle Eşleştirilmiş)
 * - Yönetici Tarafından Şifre Sıfırlama
 * - Kullanıcı Dondurma (Aktif/Pasif) ve Silme (Süper Yönetici Korumalı)
 * - Süper Yöneticilik Devri (Şifre Teyitli)
 * - Resmi Personel Kartı Eşleştirme & Birleştirme (Merge)
 * - Tüm Diğer Oturumları Kapat (Acil Durum Kill Switch)
 * - Yerel Ağ (LAN) IP Bilgisi ve Tek Tıkla Kopyalama
 * - Güvenlik & Denetim Kayıtları (Kim Ne Yaptı?)
 */

(function () {
    'use strict';

    let tumKullanicilarCache = [];
    let agDurumuCache = null;

    // --- ADMİN PANELİNİ AÇ / GÖSTER ---
    window.adminPaneliAc = async function () {
        const modal = document.getElementById('modal_admin_paneli');
        if (modal) {
            modal.style.display = 'flex';
        }

        // Verileri eşzamanlı yükle
        await Promise.all([
            adminAgDurumuYukle(),
            adminKullanicilariYukle(),
            adminDenetimLoglariYukle()
        ]);

        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    };

    window.adminPaneliKapat = function () {
        const modal = document.getElementById('modal_admin_paneli');
        if (modal) {
            modal.style.display = 'none';
        }
    };

    // Esc tuşu ile kapatma desteği
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' || e.key === 'Esc') {
            const modal = document.getElementById('modal_admin_paneli');
            if (modal && modal.style.display === 'flex') {
                const altModallar = [
                    'modal_admin_kullanici_ekle',
                    'modal_admin_yetki_duzenle',
                    'modal_admin_sifre_sifirla',
                    'modal_admin_super_devret',
                    'modal_admin_personel_eslestir'
                ];
                const acikAltModal = altModallar.find(id => {
                    const el = document.getElementById(id);
                    return el && el.style.display === 'flex';
                });
                if (acikAltModal) {
                    document.getElementById(acikAltModal).style.display = 'none';
                } else {
                    adminPaneliKapat();
                }
            }
        }
    });

    // --- YEREL AĞ DURUMU & IP YÜKLE ---
    window.adminAgDurumuYukle = async function () {
        const lblAg = document.getElementById('lbl_admin_ag_adresi');
        try {
            const data = await window.apiFetch('/admin/ag-durumu');
            const tamAdres = data ? (data.tam_adres || data.baglanti_adresi) : null;
            if (tamAdres) {
                agDurumuCache = { ...data, tam_adres: tamAdres, baglanti_adresi: tamAdres };
                if (lblAg) {
                    lblAg.innerHTML = `<span style="color: #10b981; font-weight: 700;">${tamAdres}</span> <span style="font-size: 11px; color: var(--fg-sub); font-weight: normal;">(Yerel IP: ${data.yerel_ip || ''})</span>`;
                }
            } else {
                if (lblAg) lblAg.textContent = 'Bağlantı adresi alınamadı';
            }
        } catch (e) {
            console.error('Ağ durumu alınamadı:', e);
            if (lblAg) lblAg.textContent = 'Bağlantı bilgisi alınamadı';
        }
    };

    window.adminAgAdresiniKopyala = function () {
        const adres = agDurumuCache ? (agDurumuCache.tam_adres || agDurumuCache.baglanti_adresi) : null;
        if (!adres) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Ağ adresi henüz yüklenmedi.', 'uyari');
            }
            return;
        }

        navigator.clipboard.writeText(adres).then(() => {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Bağlantı adresi panoya kopyalandı! Diğer bilgisayarlara gönderebilirsiniz.', 'basari');
            }
        }).catch(() => {
            prompt('Ağ adresini kopyalayınız:', adres);
        });
    };

    // --- KULLANICILAR LİSTESİNİ YÜKLE VE RENDER ET ---
    window.adminKullanicilariYukle = async function () {
        const tbody = document.getElementById('tbody_admin_kullanicilar');
        if (!tbody) return;

        try {
            const data = await window.apiFetch('/admin/kullanicilar');
            if (!data || !data.kullanicilar) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:16px; color:#ef4444;">Kullanıcı listesi alınamadı.</td></tr>';
                return;
            }

            tumKullanicilarCache = data.kullanicilar;
            adminKullanicilarTablosuCiz(tumKullanicilarCache);
        } catch (err) {
            console.error('Kullanıcılar yüklenemedi:', err);
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:16px; color:#ef4444;">Yetkisiz erişim veya bağlantı hatası.</td></tr>';
        }
    };

    function adminKullanicilarTablosuCiz(kullanicilar) {
        const tbody = document.getElementById('tbody_admin_kullanicilar');
        if (!tbody) return;

        if (kullanicilar.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:16px; color:var(--fg-sub);">Kayıtlı kullanıcı bulunmamaktadır.</td></tr>';
            return;
        }

        const isCurrentSuper = !!(window.aktifKullanici && window.aktifKullanici.super_admin_mi);

        let html = '';
        kullanicilar.forEach(u => {
            const isSuper = !!u.super_admin_mi;
            const isSelf = window.aktifKullanici && window.aktifKullanici.id === u.id;
            const isAktif = (u.aktif !== undefined) ? !!u.aktif : (u.aktif_mi !== undefined ? !!u.aktif_mi : true);
            const isCevrimici = (u.cevrimici !== undefined) ? !!u.cevrimici : !!u.cevrimici_mi;

            // Çevrimiçi rozeti
            let durumRozeti = '';
            if (isCevrimici) {
                durumRozeti = `<span style="display: inline-flex; align-items: center; gap: 5px; color: #10b981; font-weight: 600; font-size: 11.5px;"><span style="width:8px; height:8px; border-radius:50%; background:#10b981; box-shadow:0 0 6px #10b981;"></span> Çevrimiçi</span>`;
            } else if (u.durum_metni && u.durum_metni !== 'Henüz giriş yapmadı' && u.durum_metni !== '-') {
                durumRozeti = `<span style="display: inline-flex; align-items: center; gap: 5px; color: var(--fg-sub); font-size: 11px;"><span style="width:7px; height:7px; border-radius:50%; background:#94a3b8;"></span> ${escapeHtml(u.durum_metni)}</span>`;
            } else if (u.son_gorulme && u.son_gorulme !== '-') {
                const zamanFark = formatZamanFarki(u.son_gorulme);
                durumRozeti = `<span style="display: inline-flex; align-items: center; gap: 5px; color: var(--fg-sub); font-size: 11px;"><span style="width:7px; height:7px; border-radius:50%; background:#94a3b8;"></span> ${zamanFark}</span>`;
            } else {
                durumRozeti = `<span style="color: var(--fg-sub); font-size: 11px;">Hiç girmedi</span>`;
            }

            // Aktif / Dondurulmuş rozeti
            let aktifRozet = '';
            if (!isAktif) {
                aktifRozet = `<span style="font-size: 10px; background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 2px 6px; border-radius: 4px; font-weight: 600; margin-left: 4px;">DONDURULDU</span>`;
            }

            // Rol rozeti
            let rolRozeti = '';
            if (isSuper) {
                rolRozeti = `<span style="background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; padding: 2px 8px; border-radius: 6px; font-size: 10.5px; font-weight: 700;">👑 Süper Yönetici</span>`;
            } else if (u.rol === 'YONETICI') {
                rolRozeti = `<span style="background: rgba(2, 132, 199, 0.15); color: #0284c7; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">Yönetici</span>`;
            } else {
                rolRozeti = `<span style="background: rgba(148, 163, 184, 0.15); color: var(--fg-sub); padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">Memur / VHKİ</span>`;
            }

            // İzin hapları
            const izinler = u.izinler || {};
            let izinHtml = '<div style="display: flex; gap: 4px; flex-wrap: wrap;">';
            if (isSuper) {
                izinHtml += `<span style="background: rgba(16, 185, 129, 0.12); color: #10b981; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 600;">Tam Yetki (Tüm Modüller)</span>`;
            } else {
                if (izinler.ogrenci) izinHtml += `<span style="background: rgba(2, 132, 199, 0.1); color: #0284c7; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">Öğrenci</span>`;
                if (izinler.izin) izinHtml += `<span style="background: rgba(16, 185, 129, 0.1); color: #10b981; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">İzin</span>`;
                if (izinler.teblig) izinHtml += `<span style="background: rgba(139, 92, 246, 0.1); color: #8b5cf6; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">Tebliğ</span>`;
                if (izinler.terfi) izinHtml += `<span style="background: rgba(245, 158, 11, 0.1); color: #f59e0b; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">Terfi</span>`;
                if (izinler.ihale) izinHtml += `<span style="background: rgba(236, 72, 153, 0.1); color: #ec4899; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">İhale</span>`;
                if (izinler.admin) izinHtml += `<span style="background: rgba(239, 68, 68, 0.1); color: #ef4444; font-size: 10.5px; padding: 1px 5px; border-radius: 4px;">Admin</span>`;
                if (!Object.values(izinler).some(Boolean)) {
                    izinHtml += `<span style="color: var(--fg-sub); font-size: 10.5px;">Yetki atanmamış</span>`;
                }
            }
            izinHtml += '</div>';

            // Eşleştirilmiş personel durumu
            let personelBilgisi = '';
            if (u.personel_id) {
                personelBilgisi = `<span style="font-size: 10px; color: #10b981;" title="Resmi personel kartı ile bağlı"><i data-lucide="link" height="10" width="10"></i> Bağlı</span>`;
            } else {
                personelBilgisi = `<button class="btn btn-temizle" onclick="adminPersonelEslestirModalAc(${u.id})" style="font-size: 10px; padding: 2px 6px; color: #f59e0b;" title="Bu kullanıcıyı okul personel listesindeki resmi kaydıyla eşleştirin"><i data-lucide="link-2" height="10" width="10"></i> Eşleştir</button>`;
            }

            // Eylem Butonları
            let islemlerHtml = '<div style="display: flex; gap: 4px; justify-content: flex-end; align-items: center;">';

            // Yetki düzenleme (Süper yöneticinin izinleri değiştirilemez)
            if (!isSuper) {
                islemlerHtml += `<button class="btn btn-temizle" onclick="adminYetkiDuzenleModalAc(${u.id})" title="Yetkileri Düzenle" style="padding: 4px 6px;"><i data-lucide="sliders" height="13" width="13"></i></button>`;
            }

            // Şifre sıfırlama (Yönetici başkasının şifresini sıfırlayabilir; Süper yöneticiyi sadece kendisi sıfırlar)
            if (!isSuper || isSelf) {
                islemlerHtml += `<button class="btn btn-temizle" onclick="adminSifreSifirlaModalAc(${u.id})" title="Şifre Sıfırla" style="padding: 4px 6px; color: #f59e0b;"><i data-lucide="key" height="13" width="13"></i></button>`;
            }

            // Dondur / Aktif Et
            if (!isSuper && !isSelf) {
                const yeniDurum = !isAktif;
                const icon = isAktif ? 'pause-circle' : 'play-circle';
                const baslik = isAktif ? 'Hesabı Dondur' : 'Hesabı Aktif Et';
                const renk = isAktif ? '#ef4444' : '#10b981';
                islemlerHtml += `<button class="btn btn-temizle" onclick="adminDurumDegistir(${u.id}, ${yeniDurum})" title="${baslik}" style="padding: 4px 6px; color: ${renk};"><i data-lucide="${icon}" height="13" width="13"></i></button>`;
            }

            // Silme (Süper yönetici asla silinemez!)
            if (!isSuper && !isSelf) {
                islemlerHtml += `<button class="btn btn-temizle" onclick="adminKullaniciSil(${u.id}, '${escapeJs(u.ad_soyad)}')" title="Kullanıcıyı Sil" style="padding: 4px 6px; color: #ef4444;"><i data-lucide="trash-2" height="13" width="13"></i></button>`;
            }

            // Eğer şu anki kullanıcı Süper Yönetici ise ve bu satır süper yönetici değilse: "Süper Yöneticiliği Devret" butonu
            if (isCurrentSuper && !isSuper) {
                islemlerHtml += `<button class="btn btn-temizle" onclick="adminSuperDevretModalAc(${u.id})" title="Süper Yöneticilik Yetkisini Bu Personele Devret" style="padding: 4px 6px; color: #ef4444;"><i data-lucide="crown" height="13" width="13"></i></button>`;
            }

            islemlerHtml += '</div>';

            html += `
                <tr style="border-bottom: 1px solid var(--border); ${!isAktif ? 'opacity: 0.6;' : ''}">
                    <td style="padding: 10px 12px; font-weight: 600; color: var(--fg-main);">
                        ${escapeHtml(u.ad_soyad)} ${aktifRozet}
                        <div style="font-size: 10.5px; margin-top: 2px;">${personelBilgisi}</div>
                    </td>
                    <td style="padding: 10px 12px; font-family: monospace; font-size: 12px; color: var(--fg-sub);">${escapeHtml(u.kullanici_adi)}</td>
                    <td style="padding: 10px 12px; color: var(--fg-sub);">${escapeHtml(u.unvan || '-')}</td>
                    <td style="padding: 10px 12px;">${rolRozeti}</td>
                    <td style="padding: 10px 12px;">${izinHtml}</td>
                    <td style="padding: 10px 12px;">${durumRozeti}</td>
                    <td style="padding: 10px 12px; text-align: right;">${islemlerHtml}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }

    // --- YENİ KULLANICI EKLEME ---
    window.adminKullaniciEkleModalAc = async function () {
        const modal = document.getElementById('modal_admin_kullanici_ekle');
        const select = document.getElementById('admin_yeni_personel_sec');

        if (select) {
            select.innerHTML = '<option value="">-- Personel Seçiniz --</option>';
            try {
                const res = await window.apiFetch('/auth/personeller-ozet');
                if (res && res.personeller) {
                    res.personeller.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = `${p.ad_soyad} (${p.unvan || 'Personel'})`;
                        opt.dataset.ad = p.ad_soyad;
                        opt.dataset.unvan = p.unvan || '';
                        select.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error('Personel listesi alınamadı:', e);
            }
        }

        // Form alanlarını temizle
        const kadi = document.getElementById('admin_yeni_kullanici_adi');
        const sifre = document.getElementById('admin_yeni_sifre');
        if (kadi) kadi.value = '';
        if (sifre) sifre.value = '';

        adminRolSecildi('MEMUR');

        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.adminPersonelSecildi = function (sel) {
        const opt = sel.options[sel.selectedIndex];
        const kadiInput = document.getElementById('admin_yeni_kullanici_adi');
        if (opt && opt.value && kadiInput && !kadiInput.value) {
            const ad = opt.dataset.ad || '';
            const trMap = { 'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u' };
            let slug = ad.toLowerCase().replace(/[çğıöşüÇĞİÖŞÜ]/g, m => trMap[m] || m);
            slug = slug.replace(/[^a-z0-9]/g, '.').replace(/\.+/g, '.').replace(/^\.|\.$/g, '');
            kadiInput.value = slug;
        }
    };

    window.adminRolSecildi = function (rol) {
        const ogrenci = document.getElementById('chk_ekle_ogrenci');
        const izin = document.getElementById('chk_ekle_izin');
        const teblig = document.getElementById('chk_ekle_teblig');
        const terfi = document.getElementById('chk_ekle_terfi');
        const ihale = document.getElementById('chk_ekle_ihale');
        const admin = document.getElementById('chk_ekle_admin');

        if (rol === 'MEMUR') {
            if (ogrenci) ogrenci.checked = false;
            if (izin) izin.checked = true;
            if (teblig) teblig.checked = true;
            if (terfi) terfi.checked = false;
            if (ihale) ihale.checked = true;
            if (admin) admin.checked = false;
        } else if (rol === 'YONETICI') {
            if (ogrenci) ogrenci.checked = true;
            if (izin) izin.checked = true;
            if (teblig) teblig.checked = true;
            if (terfi) terfi.checked = true;
            if (ihale) ihale.checked = true;
            if (admin) admin.checked = false;
        }
    };

    window.adminKullaniciEkleKaydet = async function (e) {
        if (e) e.preventDefault();
        const personel_id = document.getElementById('admin_yeni_personel_sec')?.value;
        const kullanici_adi = (document.getElementById('admin_yeni_kullanici_adi')?.value || '').trim();
        const sifre = document.getElementById('admin_yeni_sifre')?.value || '';
        const rol = document.getElementById('admin_yeni_rol')?.value || 'MEMUR';

        if (!personel_id || !kullanici_adi || !sifre) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Lütfen tüm zorunlu alanları doldurunuz.', 'hata');
            }
            return;
        }

        const izinler = {
            ogrenci: document.getElementById('chk_ekle_ogrenci')?.checked || false,
            izin: document.getElementById('chk_ekle_izin')?.checked || false,
            teblig: document.getElementById('chk_ekle_teblig')?.checked || false,
            terfi: document.getElementById('chk_ekle_terfi')?.checked || false,
            ihale: document.getElementById('chk_ekle_ihale')?.checked || false,
            admin: document.getElementById('chk_ekle_admin')?.checked || false
        };

        try {
            const res = await window.apiFetch('/admin/kullanici-ekle', {
                method: 'POST',
                body: {
                    personel_id: parseInt(personel_id, 10),
                    kullanici_adi,
                    sifre,
                    rol,
                    izinler
                }
            });

            if (res && res.basarili) {
                document.getElementById('modal_admin_kullanici_ekle').style.display = 'none';
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Kullanıcı hesabı başarıyla tanımlandı.', 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Kullanıcı eklenemedi.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Kullanıcı ekleme isteği başarısız oldu.', 'hata');
            }
        }
    };

    // --- YETKİLERİ DÜZENLEME MODALI ---
    window.adminYetkiDuzenleModalAc = function (kullaniciId) {
        const u = tumKullanicilarCache.find(x => x.id === kullaniciId);
        if (!u) return;

        const modal = document.getElementById('modal_admin_yetki_duzenle');
        const idInput = document.getElementById('yetki_kullanici_id');
        const baslik = document.getElementById('yetki_kullanici_baslik');

        if (idInput) idInput.value = u.id;
        if (baslik) baslik.textContent = `${u.ad_soyad} (${u.kullanici_adi})`;

        const izinler = u.izinler || {};
        ['ogrenci', 'izin', 'teblig', 'terfi', 'ihale', 'admin'].forEach(modul => {
            const chk = document.getElementById(`chk_yetki_${modul}`);
            if (chk) chk.checked = !!izinler[modul];
        });

        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.adminYetkiDuzenleKaydet = async function (e) {
        if (e) e.preventDefault();
        const kullanici_id = parseInt(document.getElementById('yetki_kullanici_id')?.value || '0', 10);
        if (!kullanici_id) return;

        const izinler = {
            ogrenci: document.getElementById('chk_yetki_ogrenci')?.checked || false,
            izin: document.getElementById('chk_yetki_izin')?.checked || false,
            teblig: document.getElementById('chk_yetki_teblig')?.checked || false,
            terfi: document.getElementById('chk_yetki_terfi')?.checked || false,
            ihale: document.getElementById('chk_yetki_ihale')?.checked || false,
            admin: document.getElementById('chk_yetki_admin')?.checked || false
        };

        try {
            const res = await window.apiFetch('/admin/yetki-guncelle', {
                method: 'POST',
                body: { kullanici_id, izinler }
            });

            if (res && res.basarili) {
                document.getElementById('modal_admin_yetki_duzenle').style.display = 'none';
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Kullanıcı yetkileri güncellendi.', 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Yetki güncelleme başarısız.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Yetki kaydedilirken hata oluştu.', 'hata');
            }
        }
    };

    // --- ŞİFRE SIFIRLAMA (YÖNETİCİ TARAFINDAN) ---
    window.adminSifreSifirlaModalAc = function (kullaniciId) {
        const u = tumKullanicilarCache.find(x => x.id === kullaniciId);
        if (!u) return;

        const modal = document.getElementById('modal_admin_sifre_sifirla');
        const idInput = document.getElementById('sifirla_kullanici_id');
        const baslik = document.getElementById('sifirla_kullanici_ad');
        const sifreInput = document.getElementById('sifirla_yeni_sifre');

        if (idInput) idInput.value = u.id;
        if (baslik) baslik.textContent = `${u.ad_soyad} kullanıcısının şifresi sıfırlanacak.`;
        if (sifreInput) sifreInput.value = '';

        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.adminSifreSifirlaKaydet = async function (e) {
        if (e) e.preventDefault();
        const kullanici_id = parseInt(document.getElementById('sifirla_kullanici_id')?.value || '0', 10);
        const yeni_sifre = document.getElementById('sifirla_yeni_sifre')?.value || '';

        if (!kullanici_id || !yeni_sifre) return;
        if (yeni_sifre.length < 4) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Şifre en az 4 karakter olmalıdır.', 'uyari');
            }
            return;
        }

        try {
            const res = await window.apiFetch('/admin/sifre-sifirla', {
                method: 'POST',
                body: { kullanici_id, yeni_sifre }
            });

            if (res && res.basarili) {
                document.getElementById('modal_admin_sifre_sifirla').style.display = 'none';
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Kullanıcı şifresi başarıyla sıfırlandı.', 'basari');
                }
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Şifre sıfırlanamadı.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Şifre sıfırlama işlemi başarısız oldu.', 'hata');
            }
        }
    };

    // --- HESAP DONDUR / AKTİF ET ---
    window.adminDurumDegistir = async function (kullaniciId, yeniDurum) {
        const u = tumKullanicilarCache.find(x => x.id === kullaniciId);
        const ad = u ? u.ad_soyad : 'bu kullanıcı';
        const eylem = yeniDurum ? 'aktif hale getirilsin' : 'dondurulsun';

        if (!confirm(`${ad} isimli kullanıcının hesabı ${eylem} mi?`)) return;

        try {
            const res = await window.apiFetch('/admin/durum-degistir', {
                method: 'POST',
                body: { kullanici_id: kullaniciId, aktif: !!yeniDurum, aktif_mi: !!yeniDurum }
            });

            if (res && res.basarili) {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(`Kullanıcı durumu başarıyla güncellendi.`, 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'İşlem başarısız.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Durum değiştirilemedi.', 'hata');
            }
        }
    };

    // --- KULLANICI SİLME ---
    window.adminKullaniciSil = async function (kullaniciId, adSoyad) {
        if (!confirm(`${adSoyad} isimli kullanıcının sistemi kullanma yetkisi ve hesabı silinecektir. Onaylıyor musunuz?`)) {
            return;
        }

        try {
            const res = await window.apiFetch(`/admin/kullanici-sil/${kullaniciId}`, {
                method: 'DELETE'
            });

            if (res && res.basarili) {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(`${adSoyad} hesabı başarıyla silindi.`, 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Kullanıcı silinemedi.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Silme işlemi başarısız oldu.', 'hata');
            }
        }
    };

    // --- SÜPER YÖNETİCİLİĞİ DEVRETME MODALI ---
    window.adminSuperDevretModalAc = function (hedefId) {
        const modal = document.getElementById('modal_admin_super_devret');
        const select = document.getElementById('devret_hedef_kullanici');
        const sifreInput = document.getElementById('devret_onay_sifresi');

        if (select) {
            select.innerHTML = '<option value="">-- Kullanıcı Seçiniz --</option>';
            tumKullanicilarCache.forEach(u => {
                const uAktif = (u.aktif !== undefined) ? !!u.aktif : (u.aktif_mi !== undefined ? !!u.aktif_mi : true);
                if (!u.super_admin_mi && uAktif) {
                    const opt = document.createElement('option');
                    opt.value = u.id;
                    opt.textContent = `${u.ad_soyad} (${u.kullanici_adi} - ${u.unvan || 'Kullanıcı'})`;
                    if (hedefId && u.id === hedefId) opt.selected = true;
                    select.appendChild(opt);
                }
            });
        }

        if (sifreInput) sifreInput.value = '';
        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.adminSuperDevretKaydet = async function (e) {
        if (e) e.preventDefault();
        const hedef_kullanici_id = parseInt(document.getElementById('devret_hedef_kullanici')?.value || '0', 10);
        const onay_sifresi = document.getElementById('devret_onay_sifresi')?.value || '';

        if (!hedef_kullanici_id || !onay_sifresi) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Lütfen hedef kullanıcıyı seçin ve onay şifrenizi girin.', 'uyari');
            }
            return;
        }

        if (!confirm('DİKKAT! Süper yöneticilik yetkisini kalıcı olarak devretmek üzeresiniz. Bu işlem geri alınamaz. Devam edilsin mi?')) {
            return;
        }

        try {
            const res = await window.apiFetch('/admin/super-admin-devret', {
                method: 'POST',
                body: { hedef_kullanici_id, onay_sifresi }
            });

            if (res && res.basarili) {
                document.getElementById('modal_admin_super_devret').style.display = 'none';
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Süper yöneticilik yetkisi başarıyla devredildi!', 'basari');
                }
                // Oturum bilgilerini güncellemek için sayfayı yeniden doğrula
                setTimeout(() => window.location.reload(), 1200);
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Yetki devri gerçekleştirilemedi.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Devir işlemi başarısız oldu.', 'hata');
            }
        }
    };

    // --- PERSONEL KARTI EŞLEŞTİRME & BİRLEŞTİRME (MERGE) ---
    window.adminPersonelEslestirModalAc = async function (kullaniciId) {
        const u = tumKullanicilarCache.find(x => x.id === kullaniciId);
        if (!u) return;

        const modal = document.getElementById('modal_admin_personel_eslestir');
        const idInput = document.getElementById('eslestir_kullanici_id');
        const baslik = document.getElementById('eslestir_kullanici_ad');
        const select = document.getElementById('eslestir_hedef_personel');

        if (idInput) idInput.value = u.id;
        if (baslik) baslik.textContent = `${u.ad_soyad} (${u.kullanici_adi}) kullanıcısı bağlanacak personel:`;

        if (select) {
            select.innerHTML = '<option value="">-- Personel Seçiniz --</option>';
            try {
                const res = await window.apiFetch('/auth/personeller-ozet');
                if (res && res.personeller) {
                    res.personeller.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = `${p.ad_soyad} (${p.unvan || 'Personel'})`;
                        select.appendChild(opt);
                    });
                }
            } catch (e) {
                console.error('Personel listesi alınamadı:', e);
            }
        }

        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.adminPersonelEslestirKaydet = async function (e) {
        if (e) e.preventDefault();
        const kullanici_id = parseInt(document.getElementById('eslestir_kullanici_id')?.value || '0', 10);
        const hedef_personel_id = parseInt(document.getElementById('eslestir_hedef_personel')?.value || '0', 10);
        const taslak_sil = document.getElementById('eslestir_taslak_sil')?.checked || false;

        if (!kullanici_id || !hedef_personel_id) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Lütfen bağlanacak resmi personeli seçiniz.', 'uyari');
            }
            return;
        }

        try {
            const res = await window.apiFetch('/admin/personel-eslestir', {
                method: 'POST',
                body: { kullanici_id, hedef_personel_id, taslak_sil }
            });

            if (res && res.basarili) {
                document.getElementById('modal_admin_personel_eslestir').style.display = 'none';
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Kullanıcı hesabı resmi personel kartı ile başarıyla birleştirildi.', 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
                if (typeof window.personelleriYukle === 'function') window.personelleriYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Eşleştirme yapılamadı.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Eşleştirme işlemi başarısız oldu.', 'hata');
            }
        }
    };

    // --- TÜM DİĞER OTURUMLARI KAPAT (KILL SWITCH) ---
    window.adminTumOturumlariKapat = async function () {
        if (!confirm('DİKKAT! Siz hariç diğer tüm bilgisayarlardaki ve tarayıcılardaki aktif oturumlar sonlandırılacaktır. Devam edilsin mi?')) {
            return;
        }

        try {
            const res = await window.apiFetch('/admin/tum-oturumlar-kapat', { method: 'POST' });
            if (res && res.basarili) {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(`Diğer tüm oturumlar kapatıldı (${res.kapatilan_oturum_sayisi} oturum).`, 'basari');
                }
                adminKullanicilariYukle();
                adminDenetimLoglariYukle();
            } else {
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster(res ? res.mesaj : 'Oturumlar kapatılamadı.', 'hata');
                }
            }
        } catch (err) {
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(err.mesaj || 'Oturum kapatma isteği başarısız oldu.', 'hata');
            }
        }
    };

    // --- DENETİM LOGLARI (AUDIT LOGS) YÜKLE ---
    window.adminDenetimLoglariYukle = async function () {
        const tbody = document.getElementById('tbody_admin_denetim_loglari');
        if (!tbody) return;

        try {
            const data = await window.apiFetch('/admin/denetim-loglari?limit=50');
            if (!data || !data.loglar) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px; color:var(--fg-sub);">Kayıt bulunamadı.</td></tr>';
                return;
            }

            if (data.loglar.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px; color:var(--fg-sub);">Henüz işlem denetim kaydı bulunmuyor.</td></tr>';
                return;
            }

            let html = '';
            data.loglar.forEach(l => {
                const zaman = l.zaman ? l.zaman.replace('T', ' ').slice(0, 19) : '-';
                html += `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 7px 10px; font-family: monospace; font-size: 11px; color: var(--fg-sub);">${zaman}</td>
                        <td style="padding: 7px 10px; font-weight: 600; color: var(--fg-main);">${escapeHtml(l.kullanici_ad || 'Sistem')}</td>
                        <td style="padding: 7px 10px; font-size: 11px;"><span style="background: rgba(2,132,199,0.1); color:#0284c7; padding:1px 5px; border-radius:4px;">${escapeHtml(l.modul || '-')}</span></td>
                        <td style="padding: 7px 10px; font-weight: 500;">${escapeHtml(l.islem || '-')}</td>
                        <td style="padding: 7px 10px; color: var(--fg-sub); font-size: 11.5px;">${escapeHtml(l.ayrinti || '-')}</td>
                        <td style="padding: 7px 10px; font-family: monospace; font-size: 11px; color: var(--fg-sub);">${escapeHtml(l.ip_adresi || '-')}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        } catch (e) {
            console.error('Denetim logları alınamadı:', e);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px; color:#ef4444;">Loglar yüklenemedi.</td></tr>';
        }
    };

    // --- YARDIMCI METOTLAR ---
    function formatZamanFarki(zamanStr) {
        if (!zamanStr) return '-';
        try {
            const date = new Date(zamanStr.replace(' ', 'T'));
            const now = new Date();
            const diffSn = Math.floor((now - date) / 1000);
            if (diffSn < 60) return `${diffSn} sn önce`;
            const diffDk = Math.floor(diffSn / 60);
            if (diffDk < 60) return `${diffDk} dk önce`;
            const diffSaat = Math.floor(diffDk / 60);
            if (diffSaat < 24) return `${diffSaat} saat önce`;
            const diffGun = Math.floor(diffSaat / 24);
            return `${diffGun} gün önce`;
        } catch (e) {
            return zamanStr;
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeJs(str) {
        if (!str) return '';
        return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
    }

})();

