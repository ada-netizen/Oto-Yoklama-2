/**
 * OKUL YÖNETİM SİSTEMİ - KURUMSAL KİMLİK DOĞRULAMA & OTURUM YÖNETİMİ (auth.js)
 * 
 * Özellikler:
 * - İlk Kurulum Sihirbazı (Süper Yönetici seçimi / tanımlaması)
 * - Güvenli Giriş (Brute-force korumalı, Beni Hatırla 30 gün / Oturum bazlı)
 * - Canlı Oturum Takibi & Token Yönetimi (JWT / Bearer Token)
 * - 35 Dakika Hareketsizlik Zaman Aşımı (Auto-lock screen)
 * - Rol Bazlı Arayüz Kırpma (Öğrenci, İzin, Tebliğ, Terfi, İhale, Admin)
 * - Şifre Değiştirme ve Güvenli Oturum Kapatma
 */

(function () {
    'use strict';

    window.aktifKullanici = null;
    let hareketsizlikZamanlayici = null;
    const HAREKETSIZLIK_SURESI_MS = 35 * 60 * 1000; // 35 Dakika

    // --- YARDIMCI: TOKEN OKU / YAZ / SİL ---
    function tokenAl() {
        return window.sessionStorage.getItem('oturum_token') || 
               window.localStorage.getItem('oturum_token') || 
               window.sessionStorage.getItem('auth_token') || 
               window.localStorage.getItem('auth_token') || '';
    }
    window.tokenAl = tokenAl;

    function tokenKaydet(token, kalici) {
        if (kalici) {
            window.localStorage.setItem('oturum_token', token);
            window.localStorage.setItem('auth_token', token);
            window.sessionStorage.removeItem('oturum_token');
            window.sessionStorage.removeItem('auth_token');
            try {
                document.cookie = `session_token=${token}; path=/; max-age=${30 * 24 * 3600}; SameSite=Lax`;
            } catch (e) {}
        } else {
            window.sessionStorage.setItem('oturum_token', token);
            window.sessionStorage.setItem('auth_token', token);
            window.localStorage.removeItem('oturum_token');
            window.localStorage.removeItem('auth_token');
            try {
                document.cookie = `session_token=${token}; path=/; SameSite=Lax`;
            } catch (e) {}
        }
    }

    function tokenTemizle() {
        window.sessionStorage.removeItem('oturum_token');
        window.sessionStorage.removeItem('auth_token');
        window.localStorage.removeItem('oturum_token');
        window.localStorage.removeItem('auth_token');
        try {
            document.cookie = "session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        } catch (e) {}
        window.aktifKullanici = null;
    }

    // --- BAŞLANGIÇ KONTROLÜ (DOM READY) ---
    async function authBaslat() {
        try {
            // 1. Kurulum durumu kontrolü
            const durumRes = await fetch(`${window.API || ''}/auth/kurulum-durumu`);
            const durum = await durumRes.json();

            if (!durum.kurulu) {
                // Henüz süper yönetici atanmamış -> İlk Kurulum Sihirbazını Aç
                await authIlkKurulumModaliGoster();
                return;
            }

            // 2. Token var mı kontrol et
            const token = tokenAl();
            if (!token) {
                authGirisModaliGoster();
                return;
            }
            try {
                if (token && !document.cookie.includes('session_token=')) {
                    document.cookie = `session_token=${token}; path=/; SameSite=Lax`;
                }
            } catch (e) {}

            // 3. Token'ı sunucuda doğrula (/auth/ben)
            try {
                const benRes = await window.apiFetch('/auth/ben');
                if (benRes && benRes.kullanici) {
                    authOturumAcildi(benRes.kullanici);
                } else {
                    authGirisModaliGoster();
                }
            } catch (err) {
                console.warn('Oturum doğrulanamadı:', err);
                authGirisModaliGoster();
            }
        } catch (e) {
            console.error('Auth başlatma hatası:', e);
        }
    }

    // --- SİHİRBAZ: PERSONEL LİSTESİ ÇEK VE DOLDUR ---
    async function authIlkKurulumModaliGoster() {
        const overlay = document.getElementById('modal_auth_overlay');
        const girisKarti = document.getElementById('auth_giris_karti');
        const kurulumKarti = document.getElementById('auth_kurulum_karti');
        const personelSelect = document.getElementById('kurulum_personel_sec');

        if (girisKarti) girisKarti.style.display = 'none';
        if (kurulumKarti) kurulumKarti.style.display = 'flex';
        if (overlay) overlay.style.display = 'flex';

        // Personel özetini çek
        try {
            const res = await fetch(`${window.API || ''}/auth/personeller-ozet`);
            const data = await res.json();
            if (personelSelect && data && data.personeller) {
                personelSelect.innerHTML = '<option value="">-- Personel Listesinden Seçiniz --</option>';
                data.personeller.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = `${p.ad_soyad} (${p.unvan || 'Personel'})`;
                    opt.dataset.ad = p.ad_soyad;
                    opt.dataset.unvan = p.unvan || 'Okul Müdürü';
                    personelSelect.appendChild(opt);
                });
            }
        } catch (e) {
            console.error('Personel listesi çekilemedi:', e);
        }

        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }

    // İlk kurulumda personel seçilince form alanlarını otomatik doldur
    window.authKurulumPersonelSecildi = function (sel) {
        const opt = sel.options[sel.selectedIndex];
        const adInput = document.getElementById('kurulum_ad_soyad');
        const unvanInput = document.getElementById('kurulum_unvan');
        const kadiInput = document.getElementById('kurulum_kullanici_adi');

        if (opt && opt.value) {
            const ad = opt.dataset.ad || '';
            const unvan = opt.dataset.unvan || '';
            if (adInput) adInput.value = ad;
            if (unvanInput) unvanInput.value = unvan;

            // Kullanıcı adı önerisi oluştur (ad.soyad, türkçe karaktersiz küçük harf)
            if (kadiInput && !kadiInput.value) {
                const trMap = { 'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u' };
                let slug = ad.toLowerCase().replace(/[çğıöşüÇĞİÖŞÜ]/g, m => trMap[m] || m);
                slug = slug.replace(/[^a-z0-9]/g, '.').replace(/\.+/g, '.').replace(/^\.|\.$/g, '');
                kadiInput.value = slug || 'admin';
            }
        }
    };

    // İlk Kurulum Form Gönderimi
    window.authIlkKurulumYap = async function (e) {
        if (e) e.preventDefault();
        const hataKutusu = document.getElementById('auth_kurulum_hata');
        if (hataKutusu) {
            hataKutusu.style.display = 'none';
            hataKutusu.textContent = '';
        }

        const ad_soyad = (document.getElementById('kurulum_ad_soyad')?.value || '').trim();
        const unvan = (document.getElementById('kurulum_unvan')?.value || '').trim();
        const kullanici_adi = (document.getElementById('kurulum_kullanici_adi')?.value || '').trim();
        const sifre = document.getElementById('kurulum_sifre')?.value || '';
        const sifreTekrarEl = document.getElementById('kurulum_sifre_tekrar');
        const sifre_tekrar = sifreTekrarEl ? sifreTekrarEl.value : sifre;
        const personel_id = document.getElementById('kurulum_personel_sec')?.value || null;

        if (!ad_soyad || !kullanici_adi || !sifre) {
            hataGoster(hataKutusu, 'Lütfen tüm zorunlu alanları doldurunuz.');
            return;
        }

        if (sifre.length < 4) {
            hataGoster(hataKutusu, 'Şifre en az 4 karakter olmalıdır.');
            return;
        }

        if (sifreTekrarEl && sifre !== sifre_tekrar) {
            hataGoster(hataKutusu, 'Girdiğiniz şifreler birbiriyle uyuşmuyor. Lütfen iki kutuya da aynı şifreyi yazınız.');
            return;
        }

        try {
            const res = await fetch(`${window.API || ''}/auth/ilk-kurulum`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ad_soyad,
                    unvan,
                    kullanici_adi,
                    sifre,
                    personel_id: personel_id ? parseInt(personel_id, 10) : null
                })
            });

            const data = await res.json();
            if (!res.ok) {
                hataGoster(hataKutusu, data.detail || data.mesaj || 'Kurulum başarısız oldu.');
                return;
            }

            // Kurulum başarılı! Token'ı kaydet ve oturum aç
            tokenKaydet(data.token, true);
            authOturumAcildi(data.kullanici);
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Süper Yönetici hesabı oluşturuldu. Sisteme hoş geldiniz!', 'basari');
            }
        } catch (err) {
            console.error('İlk kurulum hatası:', err);
            hataGoster(hataKutusu, 'Bağlantı hatası: Sunucuya erişilemedi.');
        }
    };

    // --- GİRİŞ MODALI VE İŞLEMLERİ ---
    function authGirisModaliGoster() {
        tokenTemizle();
        const overlay = document.getElementById('modal_auth_overlay');
        const girisKarti = document.getElementById('auth_giris_karti');
        const kurulumKarti = document.getElementById('auth_kurulum_karti');
        const sidebarCard = document.getElementById('sidebar_user_card');

        if (sidebarCard) sidebarCard.style.display = 'none';
        if (kurulumKarti) kurulumKarti.style.display = 'none';
        if (girisKarti) girisKarti.style.display = 'flex';
        if (overlay) overlay.style.display = 'flex';

        hareketsizlikDurdur();

        setTimeout(() => {
            const inputKadi = document.getElementById('giris_kullanici_adi');
            if (inputKadi) inputKadi.focus();
        }, 150);

        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }

    window.authGirisYap = async function (e) {
        if (e) e.preventDefault();
        const hataKutusu = document.getElementById('auth_hata_kutusu');
        if (hataKutusu) {
            hataKutusu.style.display = 'none';
            hataKutusu.textContent = '';
        }

        const kullanici_adi = (document.getElementById('giris_kullanici_adi')?.value || '').trim();
        const sifre = document.getElementById('giris_sifre')?.value || '';
        const beni_hatirla = document.getElementById('giris_beni_hatirla')?.checked || false;

        if (!kullanici_adi || !sifre) {
            hataGoster(hataKutusu, 'Kullanıcı adı ve şifre giriniz.');
            return;
        }

        const btnGiris = document.getElementById('btn_giris_yap');
        if (btnGiris) {
            btnGiris.disabled = true;
            btnGiris.innerHTML = '<i data-lucide="loader-2" class="spin" height="16" width="16"></i> Giriş Yapılıyor...';
        }

        try {
            const res = await fetch(`${window.API || ''}/auth/giris`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kullanici_adi, sifre, beni_hatirla })
            });

            const data = await res.json();
            if (!res.ok) {
                hataGoster(hataKutusu, data.detail || data.mesaj || 'Giriş başarısız.');
                return;
            }

            tokenKaydet(data.token, beni_hatirla);
            authOturumAcildi(data.kullanici);
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(`Giriş başarılı. İyi çalışmalar, ${data.kullanici.ad_soyad}`, 'basari');
            }

            // Temel verileri tazele
            if (typeof window.verileriYukle === 'function') window.verileriYukle();
            if (typeof window.personelleriYukle === 'function') window.personelleriYukle();
        } catch (err) {
            console.error('Giriş isteği hatası:', err);
            hataGoster(hataKutusu, 'Sunucuya bağlanılamadı. Lütfen ağ bağlantınızı kontrol ediniz.');
        } finally {
            if (btnGiris) {
                btnGiris.disabled = false;
                btnGiris.innerHTML = '<i data-lucide="log-in" height="16" width="16"></i> Giriş Yap';
                if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
            }
        }
    };

    // --- OTURUM AÇILDIĞINDA ÇALIŞACAK MANTIKSAL ZİNCİR ---
    function authOturumAcildi(kullanici) {
        window.aktifKullanici = kullanici;

        // 1. Giriş penceresini kapat
        const overlay = document.getElementById('modal_auth_overlay');
        if (overlay) overlay.style.display = 'none';

        // 2. Kilit ekranı açıksa kapat
        const kilit = document.getElementById('modal_kilit_ekrani');
        if (kilit) kilit.style.display = 'none';

        // 3. Sol menü profil kartını güncelle
        const sidebarCard = document.getElementById('sidebar_user_card');
        const nameEl = document.getElementById('sidebar_user_name');
        const roleEl = document.getElementById('sidebar_user_role');
        const avatarEl = document.getElementById('sidebar_user_avatar');

        if (sidebarCard) sidebarCard.style.display = 'block';
        if (nameEl) {
            nameEl.textContent = kullanici.ad_soyad;
            nameEl.title = `${kullanici.ad_soyad} (${kullanici.kullanici_adi})`;
        }
        if (roleEl) {
            if (kullanici.super_admin_mi) {
                roleEl.innerHTML = '<span style="color: #10b981; font-weight: 700;">👑 Süper Yönetici</span>';
            } else {
                roleEl.textContent = kullanici.unvan || 'Kullanıcı';
            }
        }
        if (avatarEl) {
            const basHarfler = kullanici.ad_soyad.split(' ').filter(Boolean).map(s => s[0]).slice(0, 2).join('').toUpperCase();
            avatarEl.textContent = basHarfler || '?';
        }

        // 4. İzinlere göre menüleri düzenle
        authYetkileriUygula(kullanici);

        // 5. Hareketsizlik zamanlayıcısını başlat
        hareketsizlikBaslat();

        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }

    // --- ROL VE İZİNLERE GÖRE ARAYÜZÜ KIRPMA ---
    function authYetkileriUygula(kullanici) {
        const isSuper = !!kullanici.super_admin_mi;
        const izinler = kullanici.izinler || {};

        // Sidebar butonları
        const navBtns = document.querySelectorAll('.sidebar-nav [data-yetki]');
        navBtns.forEach(btn => {
            const yetki = btn.getAttribute('data-yetki');
            if (isSuper || izinler[yetki]) {
                btn.style.display = '';
            } else {
                btn.style.display = 'none';
            }
        });

        // Sidebar Admin Paneli Kısayol Butonu
        const btnAdminSidebar = document.getElementById('btn_admin_paneli_sidebar');
        if (btnAdminSidebar) {
            btnAdminSidebar.style.display = (isSuper || izinler.admin) ? '' : 'none';
        }

        // Ayarlar sekmesindeki Admin Masası kutusu
        const ayarAdminKutusu = document.getElementById('ayar_bolum_admin_masasi');
        if (ayarAdminKutusu) {
            ayarAdminKutusu.style.display = (isSuper || izinler.admin) ? '' : 'none';
        }

        // Kategori başlıkları (Grup içinde en az 1 görünen buton varsa göster, yoksa gizle)
        document.querySelectorAll('.sidebar-section-title[data-yetki-grup]').forEach(title => {
            const grup = title.getAttribute('data-yetki-grup');
            let goster = false;
            if (grup === 'ogrenci' && (isSuper || izinler.ogrenci)) goster = true;
            if (grup === 'personel' && (isSuper || izinler.teblig || izinler.terfi || izinler.izin)) goster = true;
            if (grup === 'ihale' && (isSuper || izinler.ihale)) goster = true;
            title.style.display = goster ? '' : 'none';
        });

        // Eğer mevcut açık sekme kullanıcının yetkisi dışındaysa, ilk yetkili olduğu sekmeye yönlendir
        const aktifSekme = document.querySelector('.tab-content.aktif');
        if (aktifSekme) {
            const id = aktifSekme.id;
            let yetkiliMi = true;
            if (!isSuper) {
                if (id === 'sekme_izin' || id === 'sekme_dashboard') yetkiliMi = !!izinler.ogrenci;
                else if (id === 'sekme_teblig') yetkiliMi = !!izinler.teblig;
                else if (id === 'sekme_terfi') yetkiliMi = !!izinler.terfi;
                else if (id === 'sekme_saglik') yetkiliMi = !!izinler.izin;
                else if (id === 'sekme_ihale') yetkiliMi = !!izinler.ihale;
                else if (id === 'sekme_ayarlar') yetkiliMi = !!izinler.admin;
            }

            if (!yetkiliMi) {
                // İlk izinli sekmeyi bul
                if (isSuper || izinler.ogrenci) {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_izin');
                } else if (izinler.teblig) {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_teblig');
                } else if (izinler.terfi) {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_terfi');
                } else if (izinler.izin) {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_saglik');
                } else if (izinler.ihale) {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_ihale');
                } else {
                    if (typeof window.sekmeAc === 'function') window.sekmeAc(null, 'sekme_yardim');
                }
            }
        }
    }

    // --- GÜVENLİ ÇIKIŞ (LOGOUT) ---
    window.authOturumKapat = async function () {
        if (!confirm('Oturumunuz kapatılacaktır. Onaylıyor musunuz?')) return;
        try {
            await window.apiFetch('/auth/cikis', { method: 'POST' });
        } catch (e) {
            console.warn('Çıkış isteği hatası:', e);
        }
        tokenTemizle();
        authGirisModaliGoster();
        if (typeof window.bildirimGoster === 'function') {
            window.bildirimGoster('Güvenli bir şekilde çıkış yapıldı.', 'bilgi');
        }
    };

    // core.js 401 aldığında bu fonksiyonu çağırır
    window.authOturumGecersiz = function (mesaj) {
        tokenTemizle();
        authGirisModaliGoster();
        const hataKutusu = document.getElementById('auth_hata_kutusu');
        if (hataKutusu) {
            hataGoster(hataKutusu, mesaj || 'Oturum süreniz doldu. Lütfen tekrar giriş yapınız.');
        }
    };

    // --- HAREKETSİZLİK ZAMAN AŞIMI & AUTO-LOCK (35 DK) ---
    function hareketsizlikSifirla() {
        if (!window.aktifKullanici) return;
        if (hareketsizlikZamanlayici) clearTimeout(hareketsizlikZamanlayici);
        hareketsizlikZamanlayici = setTimeout(ekraniKilitle, HAREKETSIZLIK_SURESI_MS);
    }

    function hareketsizlikBaslat() {
        ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'].forEach(evt => {
            window.addEventListener(evt, hareketsizlikSifirla, { passive: true });
        });
        hareketsizlikSifirla();
    }

    function hareketsizlikDurdur() {
        if (hareketsizlikZamanlayici) {
            clearTimeout(hareketsizlikZamanlayici);
            hareketsizlikZamanlayici = null;
        }
    }

    function ekraniKilitle() {
        if (!window.aktifKullanici) return;
        const kilitModal = document.getElementById('modal_kilit_ekrani');
        const kilitKullanici = document.getElementById('kilit_kullanici_ad');
        const kilitSifre = document.getElementById('kilit_sifre');
        const kilitHata = document.getElementById('kilit_hata');

        if (kilitHata) kilitHata.style.display = 'none';
        if (kilitSifre) kilitSifre.value = '';
        if (kilitKullanici) {
            kilitKullanici.textContent = `${window.aktifKullanici.ad_soyad} (${window.aktifKullanici.unvan || 'Kullanıcı'})`;
        }
        if (kilitModal) {
            kilitModal.style.display = 'flex';
        }
        if (kilitSifre) {
            setTimeout(() => kilitSifre.focus(), 100);
        }
    }

    window.authKilitAc = async function (e) {
        if (e) e.preventDefault();
        const sifre = document.getElementById('kilit_sifre')?.value || '';
        const kilitHata = document.getElementById('kilit_hata');
        if (kilitHata) kilitHata.style.display = 'none';

        if (!sifre) {
            hataGoster(kilitHata, 'Lütfen şifrenizi giriniz.');
            return;
        }

        if (!window.aktifKullanici) {
            authGirisModaliGoster();
            return;
        }

        try {
            const res = await fetch(`${window.API || ''}/auth/giris`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kullanici_adi: window.aktifKullanici.kullanici_adi,
                    sifre: sifre,
                    beni_hatirla: true
                })
            });

            const data = await res.json();
            if (!res.ok) {
                hataGoster(kilitHata, data.detail || data.mesaj || 'Hatalı şifre.');
                return;
            }

            tokenKaydet(data.token, true);
            const kilitModal = document.getElementById('modal_kilit_ekrani');
            if (kilitModal) kilitModal.style.display = 'none';
            hareketsizlikSifirla();
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster('Oturum kilidi başarıyla açıldı.', 'basari');
            }
        } catch (err) {
            hataGoster(kilitHata, 'Doğrulama sırasında bağlantı hatası oluştu.');
        }
    };

    window.authKilitBaskaHesap = function () {
        const kilitModal = document.getElementById('modal_kilit_ekrani');
        if (kilitModal) kilitModal.style.display = 'none';
        tokenTemizle();
        authGirisModaliGoster();
    };

    // --- KENDİ ŞİFRESİNİ DEĞİŞTİRME PENCERESİ ---
    window.authSifreDegistirModalAc = function () {
        const modal = document.getElementById('modal_sifre_degistir');
        const hata = document.getElementById('sifre_degistir_hata');
        if (hata) hata.style.display = 'none';
        ['mevcut_sifre', 'yeni_sifre', 'yeni_sifre_tekrar'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        if (modal) modal.style.display = 'flex';
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
    };

    window.authSifreDegistirModalKapat = function () {
        const modal = document.getElementById('modal_sifre_degistir');
        if (modal) modal.style.display = 'none';
    };

    window.authKendiSifremiDegistir = async function (e) {
        if (e) e.preventDefault();
        const hata = document.getElementById('sifre_degistir_hata');
        if (hata) hata.style.display = 'none';

        const eski_sifre = document.getElementById('mevcut_sifre')?.value || '';
        const yeni_sifre = document.getElementById('yeni_sifre')?.value || '';
        const yeni_sifre_tekrar = document.getElementById('yeni_sifre_tekrar')?.value || '';

        if (!eski_sifre || !yeni_sifre || !yeni_sifre_tekrar) {
            hataGoster(hata, 'Lütfen tüm alanları doldurunuz.');
            return;
        }

        if (yeni_sifre.length < 6) {
            hataGoster(hata, 'Yeni şifre en az 6 karakter olmalıdır.');
            return;
        }

        if (yeni_sifre !== yeni_sifre_tekrar) {
            hataGoster(hata, 'Yeni şifreler birbiriyle uyuşmuyor.');
            return;
        }

        try {
            const res = await window.apiFetch('/auth/sifre-degistir', {
                method: 'POST',
                body: { eski_sifre, yeni_sifre }
            });

            if (res && res.basarili) {
                authSifreDegistirModalKapat();
                if (typeof window.bildirimGoster === 'function') {
                    window.bildirimGoster('Şifreniz başarıyla güncellendi.', 'basari');
                }
            } else {
                hataGoster(hata, res ? res.mesaj : 'Şifre değiştirilemedi.');
            }
        } catch (err) {
            hataGoster(hata, err.mesaj || 'Şifre güncellenirken hata oluştu.');
        }
    };

    // --- YARDIMCI: ŞİFRE GÖSTER / GİZLE ---
    window.authSifreGosterGizle = function (inputId, btn) {
        const inp = document.getElementById(inputId);
        if (!inp) return;
        const icon = btn.querySelector('i');
        if (inp.type === 'password') {
            inp.type = 'text';
            if (icon) icon.setAttribute('data-lucide', 'eye-off');
        } else {
            inp.type = 'password';
            if (icon) icon.setAttribute('data-lucide', 'eye');
        }
        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    };

    function hataGoster(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.style.display = 'block';
    }

    // DOM Yüklendiğinde Auth Başlat
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', authBaslat);
    } else {
        authBaslat();
    }
})();

