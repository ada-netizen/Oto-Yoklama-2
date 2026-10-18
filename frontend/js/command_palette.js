/**
 * Oto-Yoklama-2: Evrensel Komut Paleti (Command Palette) Motoru
 * Kısayol: Ctrl + K (veya Cmd + K)
 * Raycast & Linear ergonomisinde yüksek hızlı arama, aksiyon ve gezinme deneyimi.
 */

(function () {
    let komutPaletiAcik = false;
    let aktifKomutIndex = 0;
    let filtrelenmisOgeler = [];

    function trLower(str) {
        return (str || '').toLocaleLowerCase('tr-TR').trim();
    }

    // Sabit Sistem Komutları Tanımları
    const sistemKomutlari = [
        // --- 1. Kritik Eşik & Hızlı Filtreler ---
        {
            id: 'eylem_tebligat_bildirimleri',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: 'Resmi Veli Tebligatları & Devamsızlık Bildirimleri (MEB Md. 36/4)',
            aciklama: '5., 15., 25. gün resmi tebligatları ve art arda 2 gün özürsüz bildirim paneli',
            ikon: 'bell-ring',
            renk: '#F59E0B',
            anahtarlar: 'tebligat bildirim 5 gun 15 gun 25 gun art arda 2 gun veli mektup resmi komisyon',
            aksiyon: () => {
                if (window.tebligatBildirimModaliAc) window.tebligatBildirimModaliAc();
            }
        },
        {
            id: 'esik_ramakkala_10',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: '10 Gün Sınırına Yaklaşanlar (9.0 - 9.9 Gün)',
            aciklama: 'Sınıf tekrarı riski taşıyan öğrencileri acil filtreler',
            ikon: 'alert-triangle',
            renk: '#EF4444',
            anahtarlar: '10 gun ramak kala esik devamsizlik risk sinif tekrari ceza',
            aksiyon: () => {
                sekmeAcHedef('sekme_izin');
                if (window.filtreleKritikEsik) window.filtreleKritikEsik('ramakkala_10');
            }
        },
        {
            id: 'esik_asanlar_10',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: '10 Günü Aşanlar (Kritik Eşik)',
            aciklama: 'Özürsüz 10 gün sınırını aşmış olan öğrencileri listeler',
            ikon: 'shield-alert',
            renk: '#DC2626',
            anahtarlar: '10 gun asanlar kritik sinifta kalan ozursuz',
            aksiyon: () => {
                sekmeAcHedef('sekme_izin');
                if (window.filtreleKritikEsik) window.filtreleKritikEsik('asanlar_10');
            }
        },
        {
            id: 'esik_mektup_5',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: '1. Veli Mektubu Sınırı (4.5 - 4.9 Gün)',
            aciklama: '5 günlük 1. mektup bildirim eşiğindeki öğrencileri listeler',
            ikon: 'mail',
            renk: '#F59E0B',
            anahtarlar: '5 gun mektup 1. mektup veli bilgilendirme esik',
            aksiyon: () => {
                sekmeAcHedef('sekme_izin');
                if (window.filtreleKritikEsik) window.filtreleKritikEsik('mektup_siniri_5');
            }
        },
        {
            id: 'esik_toplam_25',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: 'Toplam 25+ Gün Devamsızlık Yapanlar',
            aciklama: '30 günlük yasal genel devamsızlık sınırına yaklaşanlar',
            ikon: 'calendar-x',
            renk: '#9333EA',
            anahtarlar: '25 gun toplam 30 gun sinir ozurlu ozursuz toplam',
            aksiyon: () => {
                sekmeAcHedef('sekme_izin');
                if (window.filtreleKritikEsik) window.filtreleKritikEsik('toplam_risk_25');
            }
        },
        {
            id: 'esik_temizle',
            kategori: '⚡ Kritik Eşik & Hızlı Filtreler',
            baslik: 'Filtreleri Sıfırla (Tüm Öğrenciler)',
            aciklama: 'Uygulanan tüm filtreleri kaldırır ve ana tabloyu tam açar',
            ikon: 'rotate-ccw',
            renk: '#10B981',
            anahtarlar: 'filtre temizle sifirla hepsi tumu ogrenciler',
            aksiyon: () => {
                sekmeAcHedef('sekme_izin');
                if (window.filtreTemizle) window.filtreTemizle();
            }
        },

        // --- 2. Hızlı Sistem & Veri Eylemleri ---
        {
            id: 'eylem_undo',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: 'Son Yapılan Aktarımı Geri Al (Undo Snapshot)',
            aciklama: 'Hatalı Excel veya devamsızlık aktarımını tek tıkla geri alır',
            ikon: 'undo-2',
            renk: '#6366F1',
            anahtarlar: 'geri al undo snapshot geri don iptal hatali aktarim',
            aksiyon: () => {
                if (window.sonIslemiGeriAl) window.sonIslemiGeriAl();
            }
        },
        {
            id: 'eylem_yedek_al',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: 'Canlı Veritabanı Yedeği Al',
            aciklama: 'SQLite anlık güvenli kopyasını yedekler klasörüne kaydeder',
            ikon: 'database',
            renk: '#0284C7',
            anahtarlar: 'yedek al backup veritabani live db online backup',
            aksiyon: () => {
                canliYedekAl();
            }
        },
        {
            id: 'eylem_dev_yukle',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: "Excel'den Devamsızlık Yükle (Ctrl + D)",
            aciklama: 'e-Okul devamsızlık Excel dosyasını seçip içeri aktarır',
            ikon: 'file-spreadsheet',
            renk: '#10B981',
            anahtarlar: 'excel devamsizlik yukle import aktar eokul e-okul',
            aksiyon: () => {
                const f = document.getElementById('f-dev');
                if (f) f.click();
            }
        },
        {
            id: 'eylem_ogr_yukle',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: "Excel'den Öğrenci Listesi Yükle",
            aciklama: 'Öğrenci künye listesini sisteme aktarır ve günceller',
            ikon: 'user-plus',
            renk: '#06B6D4',
            anahtarlar: 'excel ogrenci yukle import aktar liste kunye',
            aksiyon: () => {
                const f = document.getElementById('f-ogr');
                if (f) f.click();
            }
        },
        {
            id: 'eylem_sablon_indir',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: 'Boş İzin Dilekçesi Şablonu Üret (PDF)',
            aciklama: 'MEB standartlarında boş veli izin dilekçesi PDF belgesi indirir',
            ikon: 'file-text',
            renk: '#8B5CF6',
            anahtarlar: 'izin dilekcesi sablon meb veli izin belgesi pdf',
            aksiyon: () => {
                if (window.izinDilekcesiSablonuOlustur) window.izinDilekcesiSablonuOlustur();
            }
        },
        {
            id: 'eylem_tema_degistir',
            kategori: '🚀 Hızlı Sistem Eylemleri',
            baslik: 'Açık / Koyu Tema Değiştir',
            aciklama: 'WCAG AA uyumlu aydınlık ve karanlık modlar arasında geçiş yapar',
            ikon: 'sun-moon',
            renk: '#F59E0B',
            anahtarlar: 'tema mod gece gunduz dark light aydinlik karanlik',
            aksiyon: () => {
                if (window.temaDegistir) window.temaDegistir();
            }
        },

        // --- 3. Modallar & Yönetim Panelleri ---
        {
            id: 'modal_raporlar',
            kategori: '📦 Yönetim Panelleri & Modallar',
            baslik: 'Raporlar ve İstatistikler Modalı',
            aciklama: 'Detaylı grafikler ve şube bazlı istatistiki çıktıları görüntüler',
            ikon: 'pie-chart',
            renk: '#EC4899',
            anahtarlar: 'rapor grafik istatistik analiz cikti modal',
            aksiyon: () => {
                if (window.modalAc) window.modalAc('raporlar_modal');
            }
        },
        {
            id: 'modal_ogrenci_yonetim',
            kategori: '📦 Yönetim Panelleri & Modallar',
            baslik: 'Öğrenci Yönetimi Modalı',
            aciklama: 'Öğrenci ekleme, düzenleme, silme ve sınıf yönetimi',
            ikon: 'user-cog',
            renk: '#14B8A6',
            anahtarlar: 'ogrenci yonetim duzenle sil ekle sinif modal',
            aksiyon: () => {
                if (window.ogrenciYonetimAc) window.ogrenciYonetimAc();
            }
        },
        {
            id: 'modal_personel_yonetim',
            kategori: '📦 Yönetim Panelleri & Modallar',
            baslik: 'Personel Yönetimi Modalı',
            aciklama: 'Öğretmen ve idareci personel künyeleri, branş ve grup yönetimi',
            ikon: 'users-round',
            renk: '#84CC16',
            anahtarlar: 'personel yonetim ogretmen brans grup modal',
            aksiyon: () => {
                if (window.personelYonetimAc) window.personelYonetimAc();
            }
        },

        // --- 4. Sekmeler & Modüller ---
        {
            id: 'sekme_1_izin',
            kategori: '📑 Sekme Gezinimi',
            baslik: '1. Öğrenci İzin ve Devamsızlık (Ctrl + 1)',
            aciklama: 'Ana yoklama masası, takvim ve veli mektubu önizleme',
            ikon: 'calendar-check',
            renk: '#3B82F6',
            anahtarlar: 'sekme ana sayfa izin devamsizlik yoklama 1',
            aksiyon: () => sekmeAcHedef('sekme_izin')
        },
        {
            id: 'sekme_2_teblig',
            kategori: '📑 Sekme Gezinimi',
            baslik: '2. Personel Tebliğ Yönetimi (Ctrl + 2)',
            aciklama: 'Resmi yazı tebliğ listesi ve imza sirküsü motoru',
            ikon: 'file-check',
            renk: '#6366F1',
            anahtarlar: 'sekme teblig imza sirkusu dys resmi yazi 2',
            aksiyon: () => sekmeAcHedef('sekme_teblig')
        },
        {
            id: 'sekme_3_ihale',
            kategori: '📑 Sekme Gezinimi',
            baslik: '3. 22/d Doğrudan Temin İhale Motoru (Ctrl + 3)',
            aciklama: 'Piyasa fiyat araştırması ve doğrudan temin resmi evrakları',
            ikon: 'briefcase',
            renk: '#F97316',
            anahtarlar: 'sekme ihale 22d dogrudan temin piyasa fiyat arastirma 3',
            aksiyon: () => sekmeAcHedef('sekme_ihale')
        },
        {
            id: 'sekme_4_dashboard',
            kategori: '📑 Sekme Gezinimi',
            baslik: '4. İstatistikler & Özet Dashboard (Ctrl + 4)',
            aciklama: 'Okul geneli devamsızlık oranları, risk sayaçları ve analizler',
            ikon: 'bar-chart-3',
            renk: '#10B981',
            anahtarlar: 'sekme istatistik dashboard grafik analiz ozet 4',
            aksiyon: () => {
                sekmeAcHedef('sekme_dashboard');
                if (window.dashboardYukle) window.dashboardYukle();
            }
        },
        {
            id: 'sekme_5_saglik',
            kategori: '📑 Sekme Gezinimi',
            baslik: '5. Personel Sağlık İzinleri (Ctrl + 5)',
            aciklama: 'Personel rapor, sevk ve muayene izin kayıtları',
            ikon: 'activity',
            renk: '#EF4444',
            anahtarlar: 'sekme saglik rapor sevk muayene izin 5',
            aksiyon: () => {
                sekmeAcHedef('sekme_saglik');
                if (window.saglikYukle) window.saglikYukle();
            }
        },
        {
            id: 'sekme_6_ayarlar',
            kategori: '📑 Sekme Gezinimi',
            baslik: '6. Ayarlar ve Yedekler (Ctrl + 6)',
            aciklama: 'Okul bilgileri, logolar, yedekleme ve sistem ayarları',
            ikon: 'sliders',
            renk: '#64748B',
            anahtarlar: 'sekme ayarlar yedek logo okul mufredat 6',
            aksiyon: () => sekmeAcHedef('sekme_ayarlar')
        },
        {
            id: 'sekme_7_yardim',
            kategori: '📑 Sekme Gezinimi',
            baslik: '7. Kullanım Kılavuzu & Yardım (Ctrl + 7)',
            aciklama: 'Sistem kullanım rehberi ve MEB mevzuat bilgileri',
            ikon: 'help-circle',
            renk: '#06B6D4',
            anahtarlar: 'sekme yardim kilavuz rehber mevzuat bilgi 7',
            aksiyon: () => sekmeAcHedef('sekme_yardim')
        },
        {
            id: 'sekme_8_iletisim',
            kategori: '📑 Sekme Gezinimi',
            baslik: '8. İletişim ve Geri Bildirim',
            aciklama: 'Geliştiriciye hata bildirme ve geri bildirim iletme formu',
            ikon: 'message-square',
            renk: '#8B5CF6',
            anahtarlar: 'sekme iletisim geri bildirim mesaj destek 8',
            aksiyon: () => sekmeAcHedef('sekme_iletisim')
        }
    ];

    function sekmeAcHedef(sekmeId) {
        const btn = document.querySelector(`.tab-btn[onclick*="${sekmeId}"]`);
        if (btn) {
            btn.click();
        } else if (typeof window.sekmeAc === 'function') {
            window.sekmeAc(null, sekmeId);
        }
    }

    async function canliYedekAl() {
        if (typeof window.yuklemeGoster === 'function') window.yuklemeGoster("Canlı veritabanı yedeği alınıyor...");
        try {
            const apiBase = window.API || 'http://127.0.0.1:8000';
            const res = await fetch(`${apiBase}/yedek-al`, { method: 'POST' });
            const data = await res.json();
            if (typeof window.yuklemeGizle === 'function') window.yuklemeGizle();
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster(data.mesaj, data.basarili ? "bilgi" : "hata");
            }
        } catch (e) {
            if (typeof window.yuklemeGizle === 'function') window.yuklemeGizle();
            if (typeof window.bildirimGoster === 'function') {
                window.bildirimGoster("Yedekleme bağlantı hatası: " + e, "hata");
            }
        }
    }

    // Komut Paletini Aç
    function komutPaletiAc() {
        const overlay = document.getElementById('cmd_palette_overlay');
        const input = document.getElementById('cmd_palette_input');
        if (!overlay || !input) return;

        komutPaletiAcik = true;
        overlay.style.display = 'flex';
        input.value = '';
        aktifKomutIndex = 0;

        komutPaletiAramaGirdisi('');

        setTimeout(() => {
            input.focus();
            input.select();
        }, 30);
    }

    // Komut Paletini Kapat
    function komutPaletiKapat() {
        const overlay = document.getElementById('cmd_palette_overlay');
        if (!overlay) return;
        komutPaletiAcik = false;
        overlay.style.display = 'none';
    }

    // Toggle
    function komutPaletiToggle() {
        if (komutPaletiAcik) {
            komutPaletiKapat();
        } else {
            komutPaletiAcik = true;
            komutPaletiAc();
        }
    }

    // Overlay dışına tıklandığında kapat
    function komutPaletiOverlayTikla(e) {
        if (e.target && e.target.id === 'cmd_palette_overlay') {
            komutPaletiKapat();
        }
    }

    // Arama ve Filtreleme Motoru
    function komutPaletiAramaGirdisi(sorguHam) {
        const sorgu = trLower(sorguHam);
        filtrelenmisOgeler = [];

        // 1. Sistem Komutları Filtreleme
        const eslesenKomutlar = sistemKomutlari.filter(k => {
            if (!sorgu) return true; // Boşsa hepsini göster
            const metin = trLower(`${k.baslik} ${k.aciklama} ${k.kategori} ${k.anahtarlar}`);
            return metin.includes(sorgu);
        });

        eslesenKomutlar.forEach(k => {
            filtrelenmisOgeler.push({
                tip: 'komut',
                kategori: k.kategori,
                baslik: k.baslik,
                aciklama: k.aciklama,
                ikon: k.ikon,
                renk: k.renk,
                aksiyon: k.aksiyon
            });
        });

        // 2. Canlı Öğrenci Eşleşmeleri
        if (sorgu && sorgu.length >= 1 && window.ogrenciListesi && Array.isArray(window.ogrenciListesi)) {
            const eslesenOgrenciler = window.ogrenciListesi.filter(ogr => {
                const ogrAd = trLower(ogr.ad_soyad);
                const ogrNo = String(ogr.no || '');
                const ogrSube = trLower(ogr.sube);
                return ogrAd.includes(sorgu) || ogrNo.includes(sorgu) || ogrSube.includes(sorgu);
            }).slice(0, 8); // En iyi 8 öğrenci

            eslesenOgrenciler.forEach(ogr => {
                const ozsz = Math.round((ogr.ozursuz || 0) * 10) / 10;
                const ozrl = Math.round((ogr.ozurlu || 0) * 10) / 10;
                let rozetStil = 'background: rgba(16, 185, 129, 0.15); color: #10B981;';
                if (ozsz >= 10) {
                    rozetStil = 'background: rgba(239, 68, 68, 0.18); color: #EF4444; font-weight: bold;';
                } else if (ozsz >= 4.5) {
                    rozetStil = 'background: rgba(245, 158, 11, 0.18); color: #F59E0B;';
                }

                filtrelenmisOgeler.push({
                    tip: 'ogrenci',
                    kategori: '👤 Eşleşen Öğrenciler',
                    baslik: `${ogr.ad_soyad}`,
                    aciklama: `No: ${ogr.no} • Sınıf: ${ogr.sube || '-'} • Özürsüz: ${ozsz}G • Özürlü: ${ozrl}G`,
                    ikon: 'user',
                    renk: ozsz >= 10 ? '#EF4444' : (ozsz >= 4.5 ? '#F59E0B' : '#0284C7'),
                    rozetMetin: `${ozsz} Gün Özürsüz`,
                    rozetStil: rozetStil,
                    aksiyon: () => {
                        sekmeAcHedef('sekme_izin');
                        if (typeof window.ogrenciSec === 'function') {
                            window.ogrenciSec(ogr.no, ogr.ad_soyad, ogr.sube, ozsz, ozrl);
                        }
                    }
                });
            });
        }

        // 3. Canlı Personel Eşleşmeleri
        if (sorgu && sorgu.length >= 2 && window.tumPersoneller && Array.isArray(window.tumPersoneller)) {
            const eslesenPersonel = window.tumPersoneller.filter(p => {
                const pAd = trLower(p.ad);
                const pGorev = trLower(p.gorev);
                const pBrans = trLower(p.brans);
                return pAd.includes(sorgu) || pGorev.includes(sorgu) || pBrans.includes(sorgu);
            }).slice(0, 5); // En iyi 5 personel

            eslesenPersonel.forEach(p => {
                filtrelenmisOgeler.push({
                    tip: 'personel',
                    kategori: '👥 Eşleşen Personel & Öğretmenler',
                    baslik: `${p.ad}`,
                    aciklama: `Görev: ${p.gorev || '-'} • Branş: ${p.brans || '-'} • Grup: ${p.grup || '-'}`,
                    ikon: 'graduation-cap',
                    renk: '#8B5CF6',
                    rozetMetin: p.grup || 'Personel',
                    rozetStil: 'background: rgba(139, 92, 246, 0.15); color: #8B5CF6;',
                    aksiyon: () => {
                        sekmeAcHedef('sekme_teblig');
                        const araKutu = document.getElementById('personel_ara');
                        if (araKutu) {
                            araKutu.value = p.ad;
                            if (typeof window.personelTablosunuDoldur === 'function') {
                                window.personelTablosunuDoldur();
                            }
                        }
                    }
                });
            });
        }

        aktifKomutIndex = 0;
        komutPaletiRender();
    }

    // Listeyi Ekrana Çiz
    function komutPaletiRender() {
        const listeEl = document.getElementById('cmd_palette_list');
        const statusEl = document.getElementById('cmd_palette_status');
        if (!listeEl) return;

        if (filtrelenmisOgeler.length === 0) {
            listeEl.innerHTML = `
                <div class="cmd-palette-empty">
                    <i data-lucide="search-x" height="32" width="32" style="color: var(--fg-sub); margin-bottom: 8px;"></i>
                    <p style="font-size: 13.5px; font-weight: 500; color: var(--fg-main); margin: 0;">Eşleşen komut veya kayıt bulunamadı</p>
                    <span style="font-size: 11.5px; color: var(--fg-sub); margin-top: 4px;">Farklı bir arama terimi deneyin (örn. Ali, 10 gün, mektup, yedek)</span>
                </div>
            `;
            if (statusEl) statusEl.textContent = 'Sonuç yok';
            if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
            return;
        }

        let html = '';
        let sonKategori = '';

        filtrelenmisOgeler.forEach((oge, index) => {
            if (oge.kategori !== sonKategori) {
                sonKategori = oge.kategori;
                html += `<div class="cmd-palette-group-title">${sonKategori}</div>`;
            }

            const aktifMi = index === aktifKomutIndex;
            const rozetHtml = oge.rozetMetin
                ? `<span class="cmd-palette-item-badge" style="${oge.rozetStil || ''}">${oge.rozetMetin}</span>`
                : '';

            html += `
                <div 
                    class="cmd-palette-item ${aktifMi ? 'active' : ''}" 
                    data-index="${index}"
                    onclick="window.komutPaletiOgeSec(${index})"
                    onmouseenter="window.komutPaletiHover(${index})"
                >
                    <div class="cmd-palette-item-icon" style="color: ${oge.renk};">
                        <i data-lucide="${oge.ikon}" height="16" width="16"></i>
                    </div>
                    <div class="cmd-palette-item-content">
                        <div class="cmd-palette-item-title">${oge.baslik}</div>
                        <div class="cmd-palette-item-desc">${oge.aciklama}</div>
                    </div>
                    ${rozetHtml}
                    <div class="cmd-palette-item-hint">
                        <span>↵</span>
                    </div>
                </div>
            `;
        });

        listeEl.innerHTML = html;
        if (statusEl) statusEl.textContent = `${filtrelenmisOgeler.length} sonuç`;
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();

        // Aktif öğeyi görünür alanda tut
        const aktifEl = listeEl.querySelector('.cmd-palette-item.active');
        if (aktifEl) {
            aktifEl.scrollIntoView({ block: 'nearest', behavior: 'auto' });
        }
    }

    // Aktif Öğeyi Seçip Çalıştırma
    function komutPaletiOgeSec(index) {
        if (filtrelenmisOgeler[index] && typeof filtrelenmisOgeler[index].aksiyon === 'function') {
            const eylem = filtrelenmisOgeler[index].aksiyon;
            komutPaletiKapat();
            setTimeout(() => eylem(), 50);
        }
    }

    // Mouse Hover
    function komutPaletiHover(index) {
        aktifKomutIndex = index;
        const listeEl = document.getElementById('cmd_palette_list');
        if (!listeEl) return;
        const ogeler = listeEl.querySelectorAll('.cmd-palette-item');
        ogeler.forEach(el => {
            const idx = parseInt(el.getAttribute('data-index'), 10);
            if (idx === index) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }

    // Klavye Yön Tuşları ve Enter Yönetimi
    document.addEventListener('keydown', function (e) {
        // Ctrl + K veya Cmd + K kısayolu ile aç/kapat
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            e.stopPropagation();
            komutPaletiToggle();
            return;
        }

        // Açıkken klavye gezinimi
        if (!komutPaletiAcik) return;

        if (e.key === 'Escape') {
            e.preventDefault();
            komutPaletiKapat();
            return;
        }

        if (filtrelenmisOgeler.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            aktifKomutIndex = (aktifKomutIndex + 1) % filtrelenmisOgeler.length;
            komutPaletiVurguGuncelle();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            aktifKomutIndex = (aktifKomutIndex - 1 + filtrelenmisOgeler.length) % filtrelenmisOgeler.length;
            komutPaletiVurguGuncelle();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            komutPaletiOgeSec(aktifKomutIndex);
        }
    });

    function komutPaletiVurguGuncelle() {
        const listeEl = document.getElementById('cmd_palette_list');
        if (!listeEl) return;
        const ogeler = listeEl.querySelectorAll('.cmd-palette-item');
        ogeler.forEach(el => {
            const idx = parseInt(el.getAttribute('data-index'), 10);
            if (idx === aktifKomutIndex) {
                el.classList.add('active');
                el.scrollIntoView({ block: 'nearest', behavior: 'auto' });
            } else {
                el.classList.remove('active');
            }
        });
    }

    // Global Dışa Aktarımlar
    window.komutPaletiAc = komutPaletiAc;
    window.komutPaletiKapat = komutPaletiKapat;
    window.komutPaletiToggle = komutPaletiToggle;
    window.komutPaletiOverlayTikla = komutPaletiOverlayTikla;
    window.komutPaletiAramaGirdisi = komutPaletiAramaGirdisi;
    window.komutPaletiOgeSec = komutPaletiOgeSec;
    window.komutPaletiHover = komutPaletiHover;
    window.canliYedekAl = canliYedekAl;

})();

