
        // BAŞLANGIÇ YÜKLEMESİ VE TEMA
        function splashEkraniniKapat() {
            const splash = document.getElementById('splash_overlay');
            if (splash && !splash.classList.contains('gizli')) {
                splash.classList.add('gizli');
                setTimeout(() => {
                    splash.style.display = 'none';
                    if (window.lucide && typeof lucide.createIcons === 'function') {
                        lucide.createIcons();
                    }
                }, 450);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const savedTema = localStorage.getItem('temaPref') || 'gece';
            karanlikMod = (savedTema === 'gece');
            setTimeout(() => temaDegistir(savedTema), 50);

            // İlk verileri arka planda çek
            if (typeof verileriYukle === 'function') {
                verileriYukle();
            }
            if (typeof personelleriYukle === 'function') {
                personelleriYukle();
            }

            // Kurumsal açılış kartını zarif bir geçişle kapat
            setTimeout(splashEkraniniKapat, 700);
        });

        // Sayfa kaynakları tamamen yüklendiğinde garanti kapatma
        window.addEventListener('load', () => {
            setTimeout(splashEkraniniKapat, 500);
        });

const API = 'http://127.0.0.1:8000';

        // --- BİLDİRİM (TOAST) SİSTEMİ (TOASTIFY ENTEGRASYONU) ---
        function bildirimGoster(mesaj, tur) {
            if(!mesaj) return;
            if(!tur) tur = 'bilgi';
            
            // Hata ise kırmızı, uyari ise turuncu/amber, bilgi/basarili ise yeşil tonları
            let bgColor = 'linear-gradient(to right, #10B981, #059669)';
            if (tur === 'hata') {
                bgColor = 'linear-gradient(to right, #EF4444, #DC2626)';
            } else if (tur === 'uyari') {
                bgColor = 'linear-gradient(to right, #F59E0B, #D97706)';
            }
            
            Toastify({
                text: `<div class="toast-content">${mesaj}</div>`,
                duration: 6000,
                escapeMarkup: false,
                gravity: "top", 
                position: "center", 
                stopOnFocus: true,
                close: true, 
                style: {
                    background: bgColor,
                    borderRadius: "8px",
                    fontWeight: "600",
                    fontFamily: "'Inter', sans-serif",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.2)",
                    padding: "12px 18px"
                }
            }).showToast();
        }

        // --- MODERN ONAY VE UYARI DİYALOĞU (NATIVE ALERT/CONFIRM YERİNE) ---
        function modernOnayGoster(baslik, mesaj, tip = 'soru') {
            return new Promise((resolve) => {
                let overlay = document.getElementById('custom_dialog_overlay');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'custom_dialog_overlay';
                    overlay.className = 'custom-dialog-overlay';
                    overlay.innerHTML = `
                        <div class="custom-dialog-card">
                            <div class="custom-dialog-icon ${tip}" id="custom_dialog_icon">
                                <i data-lucide="${tip === 'uyari' ? 'alert-triangle' : (tip === 'bilgi' ? 'info' : 'help-circle')}" style="width:24px;height:24px;"></i>
                            </div>
                            <h3 class="custom-dialog-title" id="custom_dialog_title"></h3>
                            <p class="custom-dialog-message" id="custom_dialog_msg"></p>
                            <div class="custom-dialog-actions">
                                <button class="custom-dialog-btn cancel" id="custom_dialog_cancel">Vazgeç</button>
                                <button class="custom-dialog-btn ${tip === 'uyari' ? 'confirm-danger' : 'confirm-primary'}" id="custom_dialog_confirm">Onayla</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(overlay);
                    if (window.lucide) window.lucide.createIcons();
                }

                const titleEl = document.getElementById('custom_dialog_title');
                const msgEl = document.getElementById('custom_dialog_msg');
                const cancelBtn = document.getElementById('custom_dialog_cancel');
                const confirmBtn = document.getElementById('custom_dialog_confirm');
                const iconEl = document.getElementById('custom_dialog_icon');

                if (titleEl) titleEl.innerText = baslik || 'Onay Gerekiyor';
                if (msgEl) msgEl.innerText = mesaj || '';
                if (iconEl) {
                    iconEl.className = `custom-dialog-icon ${tip}`;
                    iconEl.innerHTML = `<i data-lucide="${tip === 'uyari' ? 'alert-triangle' : (tip === 'bilgi' ? 'info' : 'help-circle')}" style="width:24px;height:24px;"></i>`;
                    if (window.lucide) window.lucide.createIcons();
                }

                overlay.classList.add('active');

                const cleanup = (result) => {
                    overlay.classList.remove('active');
                    confirmBtn.onclick = null;
                    cancelBtn.onclick = null;
                    resolve(result);
                };

                confirmBtn.onclick = () => cleanup(true);
                cancelBtn.onclick = () => cleanup(false);
            });
        }
        window.modernOnayGoster = modernOnayGoster;

        // --- ORTAK MERKEZİ YARDIMCI İŞLEVLER (DRY UTILITIES) ---
        window.API = API;

        // 1. Güvenli DOM Değer Okuma (Null hatasını önler)
        function getVal(id, varsayilan = "") {
            const el = document.getElementById(id);
            if (!el) return varsayilan;
            return el.value !== undefined ? el.value : varsayilan;
        }
        window.getVal = getVal;

        // 2. Standart ve Güvenli API İstek Yöneticisi
        async function apiFetch(endpoint, options = {}) {
            const url = endpoint.startsWith('http') ? endpoint : `${API}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
            const opts = { ...options };
            opts.headers = { ...opts.headers };

            if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
                opts.headers['Content-Type'] = 'application/json';
                opts.body = JSON.stringify(opts.body);
            }

            try {
                const res = await fetch(url, opts);
                const contentType = res.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    return await res.json();
                }
                return res;
            } catch (err) {
                console.error(`apiFetch hatası (${url}):`, err);
                throw err;
            }
        }
        window.apiFetch = apiFetch;

        // 3. Ortak Tarih Dönüştürücüler
        function tarihFormatlaTR(tarihDegeri) {
            if (!tarihDegeri) return "";
            if (tarihDegeri instanceof Date) {
                const pad = n => String(n).padStart(2, '0');
                return `${pad(tarihDegeri.getDate())}.${pad(tarihDegeri.getMonth() + 1)}.${tarihDegeri.getFullYear()}`;
            }
            const str = String(tarihDegeri).trim().split('T')[0];
            const parcalar = str.split(/[-/.]/);
            if (parcalar.length === 3) {
                if (parcalar[0].length === 4) { // YYYY-MM-DD
                    return `${parcalar[2].padStart(2, '0')}.${parcalar[1].padStart(2, '0')}.${parcalar[0]}`;
                } else if (parcalar[2].length === 4) { // DD-MM-YYYY
                    return `${parcalar[0].padStart(2, '0')}.${parcalar[1].padStart(2, '0')}.${parcalar[2]}`;
                }
            }
            return str;
        }
        window.tarihFormatlaTR = tarihFormatlaTR;

        function tarihFormatlaISO(tarihDegeri) {
            if (!tarihDegeri) return "";
            if (tarihDegeri instanceof Date) {
                const pad = n => String(n).padStart(2, '0');
                return `${tarihDegeri.getFullYear()}-${pad(tarihDegeri.getMonth() + 1)}-${pad(tarihDegeri.getDate())}`;
            }
            const str = String(tarihDegeri).trim().split('T')[0];
            const parcalar = str.split(/[-/.]/);
            if (parcalar.length === 3) {
                if (parcalar[2].length === 4) { // DD.MM.YYYY -> YYYY-MM-DD
                    return `${parcalar[2]}-${parcalar[1].padStart(2, '0')}-${parcalar[0].padStart(2, '0')}`;
                } else if (parcalar[0].length === 4) { // YYYY.MM.DD -> YYYY-MM-DD
                    return `${parcalar[0]}-${parcalar[1].padStart(2, '0')}-${parcalar[2].padStart(2, '0')}`;
                }
            }
            return str;
        }
        window.tarihFormatlaISO = tarihFormatlaISO;

        // 4. Türkçe Karakter ve Metin Normalizasyonu
        function trUpper(str) {
            return str ? String(str).toLocaleUpperCase('tr-TR') : "";
        }
        window.trUpper = trUpper;

        function trNormalize(str) {
            return str ? String(str).trim().toLocaleUpperCase('tr-TR').replace(/[\s\.\-_]/g, '') : "";
        }
        window.trNormalize = trNormalize;

        // Global Kısayollar ve Esc Tuşu Yönetimi (Power-User Kısayolları)
        document.addEventListener('keydown', (e) => {
            const isEditingText = document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);

            // Esc Tuşu: Açık modal, dialog, drawer ve komut paletini kapatma
            if (e.key === 'Escape') {
                const cmdOverlay = document.getElementById('cmd_palette_overlay');
                if (cmdOverlay && cmdOverlay.style.display !== 'none') {
                    if (typeof window.komutPaletiKapat === 'function') window.komutPaletiKapat();
                    return;
                }
                const dialog = document.getElementById('custom_dialog_overlay');
                if (dialog && dialog.classList.contains('active')) {
                    const cancelBtn = document.getElementById('custom_dialog_cancel');
                    if (cancelBtn) cancelBtn.click();
                    return;
                }
                const acikModallar = document.querySelectorAll('.modal-overlay');
                acikModallar.forEach(m => {
                    if (m.style.display === 'flex' || m.style.display === 'block') {
                        m.style.display = 'none';
                    }
                });
                const acikDrawers = document.querySelectorAll('.drawer-overlay.open');
                acikDrawers.forEach(d => d.classList.remove('open'));
                return;
            }

            // F1 veya Ctrl + /: Klavye Kısayolları Rehberi (Cheat Sheet Modalı)
            if (e.key === 'F1' || ((e.ctrlKey || e.metaKey) && (e.key === '/' || e.key === '?'))) {
                e.preventDefault();
                if (typeof modalAc === 'function') modalAc('kisayollar_modal');
                return;
            }

            // Ctrl + K: Evrensel Komut Paleti (Command Palette)
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                if (typeof window.komutPaletiToggle === 'function') {
                    window.komutPaletiToggle();
                }
                return;
            }

            // Ctrl + F: Aktif Arama Kutusuna Odaklanma
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                const aktifSekme = document.querySelector('.tab-content.aktif');
                if (aktifSekme) {
                    const aramaInput = aktifSekme.querySelector('input[type="text"], .search-input');
                    if (aramaInput) {
                        aramaInput.focus();
                        aramaInput.select();
                        return;
                    }
                }
                const genelArama = document.getElementById('ent_arama');
                if (genelArama) { genelArama.focus(); genelArama.select(); }
                return;
            }

            // Ctrl + D: Devamsızlık Yükleme
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
                const fDev = document.getElementById('f-dev');
                if (fDev) {
                    e.preventDefault();
                    fDev.click();
                    return;
                }
            }

            // Ctrl + Z: Son İşlemi Geri Al (Undo Snapshot) - Metin girişinde değilken
            if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
                if (!isEditingText) {
                    e.preventDefault();
                    if (typeof sonIslemiGeriAl === 'function') sonIslemiGeriAl();
                    return;
                }
            }

            // Ctrl + S: Aktif Sekmedeki Kaydetme İşlemini Tetikleme
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
                e.preventDefault();
                const aktifSekme = document.querySelector('.tab-content.aktif');
                if (aktifSekme && aktifSekme.id === 'sekme_ayarlar') {
                    if (typeof ayarlariKaydet === 'function') ayarlariKaydet();
                } else if (aktifSekme && aktifSekme.id === 'sekme_teblig') {
                    const btnKaydet = document.getElementById('btn_teblig_kaydet');
                    if (btnKaydet) btnKaydet.click();
                    else bildirimGoster("Tebliğ kaydet butonu hazır.", "bilgi");
                } else {
                    bildirimGoster("Aktif sekmede kaydedilecek bekleyen form bulunamadı.", "bilgi");
                }
                return;
            }

            // Ctrl + B: Canlı Veritabanı Yedeği Al
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
                e.preventDefault();
                if (typeof window.canliYedekAl === 'function') window.canliYedekAl();
                else bildirimGoster("Yedekleme servisine ulaşılamadı.", "hata");
                return;
            }

            // Ctrl + P: Veli İzin Mektubu veya Belge Yazdırma
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'p') {
                e.preventDefault();
                if (typeof seciliOgrenci !== 'undefined' && seciliOgrenci && typeof veliFormuOlustur === 'function') {
                    veliFormuOlustur();
                } else if (typeof izinDilekcesiSablonuOlustur === 'function') {
                    izinDilekcesiSablonuOlustur();
                } else {
                    bildirimGoster("Yazdırılacak aktif öğrenci veya belge seçili değil.", "bilgi");
                }
                return;
            }

            // Ctrl + T: Açık / Koyu Tema Değiştirme
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 't') {
                e.preventDefault();
                if (typeof temaDegistir === 'function') temaDegistir();
                return;
            }

            // Ctrl + Shift + R: Raporlar Modalı
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'r') {
                e.preventDefault();
                if (typeof modalAc === 'function') modalAc('raporlar_modal');
                return;
            }

            // F5 veya Ctrl + R (Shiftsiz): Verileri Yenile (Soft Refresh)
            if (e.key === 'F5' || ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'r')) {
                e.preventDefault();
                if (typeof verileriYukle === 'function') verileriYukle();
                if (typeof personelleriYukle === 'function') personelleriYukle();
                bildirimGoster("Veriler güncellendi.", "basarili");
                return;
            }

            // Ctrl + O: Öğrenci Yönetimi Modalı
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'o') {
                e.preventDefault();
                if (typeof modalAc === 'function') modalAc('ogrenci_yonetim_modal');
                return;
            }

            // Ctrl + 1..7: Sekme Geçiş Kısayolları
            if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && ['1','2','3','4','5','6','7'].includes(e.key)) {
                const sekmeMap = {
                    '1': 'sekme_izin',
                    '2': 'sekme_teblig',
                    '3': 'sekme_ihale',
                    '4': 'sekme_dashboard',
                    '5': 'sekme_saglik',
                    '6': 'sekme_ayarlar',
                    '7': 'sekme_yardim'
                };
                const hedefSekme = sekmeMap[e.key];
                if (hedefSekme) {
                    e.preventDefault();
                    const btn = document.querySelector(`.tab-btn[onclick*="${hedefSekme}"]`);
                    if (btn) btn.click();
                    return;
                }
            }
        });

        // --- YARDIMCI MOTORLAR (DEBOUNCE & CENTRAL STATE STORE) ---
        function debounce(func, wait = 180) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        }

        window.OtoStore = {
            state: {
                ogrenciler: [],
                devamsizliklar: [],
                seciliOgrenci: null
            },
            listeners: {},
            on(event, callback) {
                if (!this.listeners[event]) this.listeners[event] = [];
                this.listeners[event].push(callback);
            },
            emit(event, data) {
                if (this.listeners[event]) {
                    this.listeners[event].forEach(cb => {
                        try { cb(data); } catch(e) { console.error('OtoStore error:', e); }
                    });
                }
            }
        };

        async function sonIslemiGeriAl() {
            const onay = await modernOnayGoster(
                "Son İşlemi Geri Al",
                "Son yapılan aktarım veya kayıt işlemini geri alarak bir önceki veritabanı durumuna dönmek istiyor musunuz?",
                "uyari"
            );
            if (!onay) return;

            yuklemeGoster("İşlem geri alınıyor...");
            try {
                const res = await fetch(`${API}/son-islemi-geri-al`, { method: 'POST' });
                const data = await res.json();
                yuklemeGizle();
                if (data.basarili) {
                    bildirimGoster(data.mesaj, "bilgi");
                    verileriYukle();
                } else {
                    bildirimGoster(data.mesaj, "hata");
                }
            } catch (err) {
                yuklemeGizle();
                bildirimGoster("Bağlantı hatası: " + err, "hata");
            }
        }

        async function tumDevamsizliklariSil() {
            const onay = await modernOnayGoster(
                "Tüm Devamsızlıkları Sil",
                "DİKKAT: Sistemdeki TÜM öğrencilerin devamsızlık kayıtları silinecektir (Öğrenci listesi korunur).\n\nBu işlemi onaylıyor musunuz?",
                "tehlike"
            );
            if (!onay) return;

            yuklemeGoster("Devamsızlıklar siliniyor...");
            try {
                const res = await fetch(`${API}/tum-devamsizliklari-sil`, { method: 'DELETE' });
                const data = await res.json();
                yuklemeGizle();
                if (data.basarili) {
                    bildirimGoster(data.mesaj, "bilgi");
                    seciliDevamsizliklar = [];
                    geciciDevamsizliklar = [];
                    if (seciliOgrenci) {
                        seciliOgrenci.ozsz = 0;
                        seciliOgrenci.ozrl = 0;
                        seciliOgrenci.toplam = 0;
                        const elOzsz = document.getElementById('lbl_detay_ozursuz');
                        const elOzrl = document.getElementById('lbl_detay_ozurlu');
                        const elTop = document.getElementById('lbl_detay_toplam');
                        if (elOzsz) elOzsz.innerText = '0';
                        if (elOzrl) elOzrl.innerText = '0';
                        if (elTop) elTop.innerText = '0';
                    }
                    if (typeof aktifTakvimiCiz === 'function') aktifTakvimiCiz();
                    if (typeof onizlemeGuncelle === 'function') onizlemeGuncelle();
                    if (typeof kalanDevamsizlikGuncelle === 'function') kalanDevamsizlikGuncelle();
                    if (typeof verileriYukle === 'function') verileriYukle();
                } else {
                    bildirimGoster(data.mesaj, "hata");
                }
            } catch (err) {
                yuklemeGizle();
                bildirimGoster("Bağlantı hatası: " + err, "hata");
            }
        }

        // --- YÜKLENİYOR GÖSTERGESİ ---
        function yuklemeGoster(metin) {
            const overlay = document.getElementById('yukleniyor_overlay');
            const metinEl = document.getElementById('yukleniyor_metin');
            if(metinEl) metinEl.innerText = metin || 'Yükleniyor...';
            if(overlay) overlay.style.display = 'flex';
        }
        function yuklemeGizle() {
            const overlay = document.getElementById('yukleniyor_overlay');
            if(overlay) overlay.style.display = 'none';
        }
        
        let ogrenciListesi = [];
        let tumPersoneller = [];
        let sistemAyarlari = {};
        window.sistemAyarlari = sistemAyarlari;
        
        let seciliOgrenci = null;
        let seciliDevamsizliklar = []; 
        let geciciDevamsizliklar = []; 
        let calYear = new Date().getFullYear();
        let calMonth = new Date().getMonth(); 
        let aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
        let karanlikMod = true;
        let siralamaSutun = 'ad_soyad'; let siralamaYon = 1; 

        // --- 1. ARAYÜZ VE MODAL YÖNETİMİ ---
        function modalAc(id) { document.getElementById(id).style.display = 'flex'; }

function modalKapat(id) { document.getElementById(id).style.display = 'none'; }

        
        function temaDegistir(forceState = null) {
            const root = document.documentElement; 
            const btnTema = document.getElementById('btn_tema');
            
            if (forceState !== null) {
                karanlikMod = (forceState === 'gece');
            } else {
                karanlikMod = !karanlikMod;
            }
            
            if (!karanlikMod) {
                // Gündüz Moduna Geçiş (Açık, Ferah, WCAG AA Uyumlu)
                root.style.setProperty('--bg-main', '#F8FAFC'); 
                root.style.setProperty('--bg-card', '#FFFFFF');
                root.style.setProperty('--bg-card-solid', '#FFFFFF'); 
                root.style.setProperty('--bg-card-hover', '#F1F5F9');
                root.style.setProperty('--fg-main', '#0F172A'); 
                root.style.setProperty('--fg-sub', '#475569'); 
                root.style.setProperty('--border', '#E2E8F0');
                root.style.setProperty('--border-hover', '#CBD5E1');
                root.style.setProperty('--tree-sel', '#0284C7');
                
                // Devamsızlık Renkleri (Gündüz Modu - Yüksek Kontrast)
                root.style.setProperty('--dev-ozursuz-bg', '#FEE2E2'); 
                root.style.setProperty('--dev-ozursuz-fg', '#991B1B'); 
                root.style.setProperty('--dev-ozurlu-bg', '#FEF3C7'); 
                root.style.setProperty('--dev-ozurlu-fg', '#92400E'); 
                root.style.setProperty('--dev-gec-bg', '#FFEDD5'); 
                root.style.setProperty('--dev-gec-fg', '#9A3412'); 
                root.style.setProperty('--dev-faaliyet-bg', '#DBEAFE'); 
                root.style.setProperty('--dev-faaliyet-fg', '#1E40AF'); 
                root.style.setProperty('--dev-bg', '#FEE2E2'); 
                root.style.setProperty('--dev-fg', '#991B1B'); 
                
                document.querySelectorAll('.tema-switch').forEach(el => { el.classList.remove('dark'); el.classList.add('light'); });
                localStorage.setItem('temaPref', 'gunduz');
            } else {
                // Gece Moduna Geçiş (Derin Slate, Göz Yormayan)
                root.style.setProperty('--bg-main', '#0B1120'); 
                root.style.setProperty('--bg-card', 'rgba(30, 41, 59, 0.75)');
                root.style.setProperty('--bg-card-solid', '#1E293B'); 
                root.style.setProperty('--bg-card-hover', 'rgba(51, 65, 85, 0.5)');
                root.style.setProperty('--fg-main', '#F8FAFC'); 
                root.style.setProperty('--fg-sub', '#94A3B8'); 
                root.style.setProperty('--border', 'rgba(51, 65, 85, 0.65)');
                root.style.setProperty('--border-hover', '#475569');
                root.style.setProperty('--tree-sel', '#38BDF8'); 
                
                // Devamsızlık Renkleri (Gece Modu)
                root.style.setProperty('--dev-ozursuz-bg', '#7F1D1D'); 
                root.style.setProperty('--dev-ozursuz-fg', '#FCA5A5'); 
                root.style.setProperty('--dev-ozurlu-bg', '#78350F'); 
                root.style.setProperty('--dev-ozurlu-fg', '#FDE68A'); 
                root.style.setProperty('--dev-gec-bg', '#7C2D12'); 
                root.style.setProperty('--dev-gec-fg', '#FDBA74'); 
                root.style.setProperty('--dev-faaliyet-bg', '#1E3A8A'); 
                root.style.setProperty('--dev-faaliyet-fg', '#93C5FD'); 
                root.style.setProperty('--dev-bg', '#7F1D1D'); 
                root.style.setProperty('--dev-fg', '#FEF2F2'); 
                
                document.querySelectorAll('.tema-switch').forEach(el => { el.classList.remove('light'); el.classList.add('dark'); });
                localStorage.setItem('temaPref', 'gece');
            }
            
            // Tablodaki hücre stillerini güncelle
            const dHucreler = document.querySelectorAll('#tree_tum_liste td');
            dHucreler.forEach(td => {
                if(td.textContent.includes('Gün)') || td.style.color === 'white' || td.style.color === 'var(--dev-fg)') {
                    td.style.backgroundColor = 'var(--dev-bg)';
                    td.style.color = 'var(--dev-fg)';
                }
            });
            const dbHucreler = document.querySelectorAll('#tree_detay_govde td');
            dbHucreler.forEach(td => {
                if(td.textContent === 'Özürsüz' || td.style.color === 'white' || td.style.color === 'var(--dev-fg)') {
                    td.style.backgroundColor = 'var(--dev-bg)';
                    td.style.color = 'var(--dev-fg)';
                }
            });
        }


        function sekmeAc(evt, sekmeId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('aktif'));
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('aktif'));
            const hedef = document.getElementById(sekmeId);
            if(hedef) hedef.classList.add('aktif');
            if(evt && evt.currentTarget) evt.currentTarget.classList.add('aktif');
            // Sidebar rayı ve tüm istasyon butonlarını senkronize et
            document.querySelectorAll(`.tab-btn[onclick*="${sekmeId}"]`).forEach(btn => btn.classList.add('aktif'));
            
            if (window.lucide && typeof lucide.createIcons === 'function') {
                setTimeout(() => lucide.createIcons(), 30);
            }
            
            if(sekmeId === 'sekme_izin') verileriYukle();
            if(sekmeId === 'sekme_teblig') personelleriYukle();
            if(sekmeId === 'sekme_dashboard' && typeof dashboardYukle === 'function') dashboardYukle();
            if(sekmeId === 'sekme_ihale') {
                const icerik = document.getElementById("ihale_icerik");
                if (icerik && icerik.querySelector("#ihale_baslangic_mesaj")) {
                    if (ihaleGeciciVeri.konu || (ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0)) {
                        ihaleBaslat();
                        if (ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0) {
                            document.getElementById("acc_adim2").classList.add("open");
                            document.getElementById("acc_adim1").classList.remove("open");
                            document.getElementById("check_adim1").style.display = "inline-block";
                        }
                    }
                }
            }
        }

        function resizerAktifEt(resizerId, solId, sagId) {
            const resizer = document.getElementById(resizerId); const sol = document.getElementById(solId); const sag = document.getElementById(sagId);
            if(!resizer || !sol || !sag) return;

            // Daha önce ayarlanmış bir genişlik varsa geri yükle (ekrana göre güvenli sınır içinde)
            const kayitliStr = localStorage.getItem(`panel_genislik_${solId}`);
            if (kayitliStr) {
                let kayitli = parseInt(kayitliStr, 10);
                const mevcutGenislik = sol.parentElement.getBoundingClientRect().width || window.innerWidth;
                if (kayitli < 150) kayitli = 150;
                if (kayitli > mevcutGenislik - 200) kayitli = Math.max(150, mevcutGenislik - 200);
                sol.style.flex = `0 0 ${kayitli}px`; sag.style.flex = `1 1 0%`;
            }

            let isResizing = false;
            resizer.addEventListener('mousedown', function(e) { isResizing = true; document.body.style.cursor = 'col-resize'; e.preventDefault(); });
            document.addEventListener('mousemove', function(e) {
                if (!isResizing) return;
                const containerRect = sol.parentElement.getBoundingClientRect();
                let newSolWidth = e.clientX - containerRect.left - (resizer.offsetWidth / 2);
                if (newSolWidth < 150) newSolWidth = 150; if (newSolWidth > containerRect.width - 200) newSolWidth = containerRect.width - 200;
                sol.style.flex = `0 0 ${newSolWidth}px`; sag.style.flex = `1 1 0%`; 
            });
            document.addEventListener('mouseup', function(e) {
                if (isResizing) {
                    isResizing = false; document.body.style.cursor = 'default';
                    localStorage.setItem(`panel_genislik_${solId}`, Math.round(sol.getBoundingClientRect().width));
                }
            });
        }

        // ================= TABLO SÜTUN GENİŞLETME (ZEKİ MOTOR) =================
        function tabloSutunBoyutlandirma() {
            const resizers = document.querySelectorAll('.col-resizer');
            let thEl, startX, startWidth;

            // Daha önce ayarlanmış sütun genişliklerini geri yükle
            document.querySelectorAll('#tree_tum_liste th span[id^="span_"]').forEach(span => {
                const kayitli = localStorage.getItem(`sutun_genislik_${span.id}`);
                if (kayitli) span.closest('th').style.width = kayitli + 'px';
            });

            resizers.forEach(resizer => {
                resizer.addEventListener('mousedown', function(e) {
                    thEl = e.target.parentElement; startX = e.pageX; startWidth = thEl.offsetWidth;
                    document.addEventListener('mousemove', mouseMove); document.addEventListener('mouseup', mouseUp); e.stopPropagation();
                });
            });
            function mouseMove(e) { thEl.style.width = (startWidth + (e.pageX - startX)) + 'px'; }
            function mouseUp() {
                document.removeEventListener('mousemove', mouseMove); document.removeEventListener('mouseup', mouseUp);
                const span = thEl.querySelector('span[id^="span_"]');
                if (span) localStorage.setItem(`sutun_genislik_${span.id}`, thEl.offsetWidth);
            }
        }

        document.addEventListener('click', function(e) {
            const sagTikMenu = document.getElementById('sag_tik_menu');
            if(sagTikMenu && e.target !== sagTikMenu && !sagTikMenu.contains(e.target)) sagTikMenu.style.display = 'none';
        });

        // --- 2. YILLIK TABLO (EFEKT VE ÇİZİM) ---
        let yillikHucreler = []; 
        function yillikHoverEnter(r, c, tur) {
            const pathBg = karanlikMod ? "#334155" : "#E2E8F0"; const targetFg = karanlikMod ? "#F8FAFC" : "#0F172A"; const borderHl = "#38BB94";
            yillikHucreler.forEach(cell => {
                let el = document.getElementById(`yillik_hucre_${cell.r}_${cell.c}`);
                if (!el) return;
                if (tur) {
                    if (cell.isAbs) {
                        if (cell.tur === tur) { el.style.filter = "brightness(1.3)"; el.style.opacity = "1"; }
                        else { el.style.filter = "brightness(0.3)"; el.style.opacity = "0.4"; }
                    } else if (cell.isValid) el.style.backgroundColor = "var(--bg-card)";
                } else {
                    let isPath = (cell.r === r && cell.c <= c) || (cell.c === c && cell.r <= r);
                    if (isPath) {
                        if (cell.r === r && cell.c === c) { el.style.filter = "brightness(1.3)"; el.style.opacity = "1"; } 
                        else { 
                           if (cell.isValid && !cell.isAbs) { el.style.backgroundColor = pathBg; el.style.color = targetFg; } 
                           else if (cell.isAbs) { el.style.filter = "brightness(1.1)"; el.style.opacity = "1"; }
                        }
                    } else { 
                        if (cell.isAbs) { el.style.filter = "brightness(0.3)"; el.style.opacity = "0.4"; }
                        else if (cell.isValid) el.style.backgroundColor = "var(--bg-card)";
                    }
                }
            });
            if (r) { let rh = document.getElementById(`yillik_row_${r}`); if(rh) rh.style.border = `2px solid ${borderHl}`; }
            if (c) { let ch = document.getElementById(`yillik_col_${c}`); if(ch) ch.style.border = `2px solid ${borderHl}`; }
        }

        function yillikHoverLeave() {
            yillikHucreler.forEach(cell => {
                let el = document.getElementById(`yillik_hucre_${cell.r}_${cell.c}`);
                if (!el) return;
                el.style.filter = "none"; el.style.opacity = "1";
                if (cell.isValid && !cell.isAbs) { el.style.backgroundColor = cell.orjBg; el.style.color = cell.orjFg; }
            });
            for(let i=1; i<=10; i++) { let rh = document.getElementById(`yillik_row_${i}`); if(rh) rh.style.border = "1px solid var(--border)"; }
            for(let i=1; i<=31; i++) { let ch = document.getElementById(`yillik_col_${i}`); if(ch) ch.style.border = "1px solid var(--border)"; }
        }

        function yillikListeAc(no, ad) {
            document.getElementById('modal_baslik').innerText = `Yıllık Devamsızlık Karnesi - ${ad} (${no})`;
            yillikHucreler = []; 
            
            fetch(`${API}/ogrenci-detay/${no}`).then(r => r.json()).then(veri => {
                const thead = document.getElementById('yillik_thead');
                const tbody = document.getElementById('yillik_tbody');
                const ozetAlani = document.getElementById('yillik_ozet_alani');
                const rozetlerAlani = document.getElementById('yillik_rozetler_alani');
                thead.innerHTML = ""; tbody.innerHTML = ""; ozetAlani.innerHTML = "";
                if (rozetlerAlani) rozetlerAlani.innerHTML = "";
                
                let theadHtml = `<tr><th style="background-color: #1E3A8A; color: white; padding: 6px; border: 1px solid var(--border);">Aylar</th>`;
                for(let i=1; i<=31; i++) { theadHtml += `<th id="yillik_col_${i}" style="background-color: #1E3A8A; color: white; padding: 4px; border: 1px solid var(--border); width: 25px;">${i}</th>`; }
                theadHtml += `</tr>`; thead.innerHTML = theadHtml;

                const aylarList = ["Eylül", "Ekim", "Kasım", "Aralık", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran"]; const ayNolar = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6];
                const rH = { "D": "#DC2626", "ÖY": "#EF4444", "SY": "#F87171", "G": "#EA580C", "İ": "#EAB308", "I": "#EAB308", "S": "#F59E0B", "R": "#D97706", "M": "#92400E", "N": "#3B82F6", "F": "#6366F1", "SV": "#8B5CF6" };

                let devMap = {}; let detayOzursuz = {}; let detayOzurlu = {}; let detayDiger = {}; let hsOzursuz = {}; let hsOzurlu = {}; let hsDiger = {}; let ozszNet = 0.0; let ozrlNet = 0.0; let digerNet = 0.0; let gSayisi = 0;
                let pztCumaSayisi = 0; let haftaIciSayisi = 0;
                const tumKayitlar = [...veri.devamsizliklar];
                geciciDevamsizliklar.forEach(gd => { if (String(gd.no) === String(no)) tumKayitlar.push(gd); });

                tumKayitlar.forEach(dev => {
                    let tur = dev.tur.toLocaleUpperCase('tr-TR'); let gunMiktari = parseFloat(dev.gun) || 0.0; let tamGun = gunMiktari >= 1 ? parseInt(gunMiktari) : 1;
                    let parts = dev.tarih.split('/'); if(parts.length !== 3) return;
                    let basTarih = new Date(parseInt(parts[2]), parseInt(parts[1])-1, parseInt(parts[0]));
                    let hiMiktari = 0.0, hsMiktari = 0.0;
                    
                    for(let i=0; i<tamGun; i++) {
                        let gTarih = new Date(basTarih); gTarih.setDate(gTarih.getDate() + i);
                        let day = gTarih.getDay();
                        if (day !== 0 && day !== 6) {
                            devMap[`${gTarih.getFullYear()}-${gTarih.getMonth()+1}-${gTarih.getDate()}`] = tur;
                            haftaIciSayisi++;
                            if (day === 1 || day === 5) pztCumaSayisi++;
                        }
                    }
                    if (gunMiktari <= 1) { if (basTarih.getDay() === 0 || basTarih.getDay() === 6) hsMiktari = gunMiktari; else hiMiktari = gunMiktari; } 
                    else {
                        for(let i=0; i<tamGun; i++) {
                            let gTarih = new Date(basTarih); gTarih.setDate(gTarih.getDate() + i);
                            if (gTarih.getDay() === 0 || gTarih.getDay() === 6) hsMiktari += 1; else hiMiktari += 1;
                        }
                    }

                    if (["D", "ÖY", "SY"].includes(tur)) { detayOzursuz[tur] = (detayOzursuz[tur] || 0) + gunMiktari; hsOzursuz[tur] = (hsOzursuz[tur] || 0) + hsMiktari; ozszNet += hiMiktari; } 
                    else if (tur === "G") { gSayisi += 1; } 
                    else if (["N", "F"].includes(tur)) { detayDiger[tur] = (detayDiger[tur] || 0) + gunMiktari; hsDiger[tur] = (hsDiger[tur] || 0) + hsMiktari; digerNet += hiMiktari; } 
                    else { detayOzurlu[tur] = (detayOzurlu[tur] || 0) + gunMiktari; hsOzurlu[tur] = (hsOzurlu[tur] || 0) + hsMiktari; ozrlNet += hiMiktari; }
                });

                if (gSayisi > 0) { let g = Math.floor(gSayisi / 5) * 0.5; detayOzursuz[`G (${gSayisi})`] = g; ozszNet += g; }

                ozszNet = Math.round(ozszNet * 10) / 10;
                ozrlNet = Math.round(ozrlNet * 10) / 10;
                const toplamNet = Math.round((ozszNet + ozrlNet) * 10) / 10;

                const ogrKayit = (window.ogrenciListesi || []).find(o => String(o.no) === String(no));
                const ogrSube = ogrKayit ? ogrKayit.sube : (veri.sube || '');
                seciliOgrenci = { no: no, ad: ad, sube: ogrSube, ozsz: ozszNet, ozrl: ozrlNet, toplam: toplamNet };

                // --- ÇEŞİTLENDİRİLMİŞ AKILLI ROZETLER OLUŞTURUCU ---
                if (rozetlerAlani) {
                    let rozetlerHtml = '';

                    // 1. YASAL RİSK ROZETİ
                    if (ozszNet >= 10.0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap kritik">🚨 Sınıf Tekrarı Riski: 10G+ Aşıldı (${ozszNet} Gün)</span>`;
                    } else if (ozszNet >= 8.5) {
                        rozetlerHtml += `<span class="yillik-rozet-hap ramak">⚠️ Kritik Eşik: 10G Ramak Kala (${ozszNet} Gün)</span>`;
                    } else if (ozszNet >= 4.5 && ozszNet <= 5.0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap mektup">📬 5G Veli Mektubu Sınırı (${ozszNet} Gün)</span>`;
                    } else if (toplamNet >= 25.0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap toplam">⏳ 25G+ Toplam Devamsızlık Riski (${toplamNet} / 30 Gün)</span>`;
                    } else {
                        rozetlerHtml += `<span class="yillik-rozet-hap guvenli">✅ Yasal Durumu Güvenli (${ozszNet} Gün / 10 Gün)</span>`;
                    }

                    // 2. KALAN YASAL HAKLAR
                    const kalanOzsz = Math.round(Math.max(0, 10.0 - ozszNet) * 10) / 10;
                    const kalanToplam = Math.round(Math.max(0, 30.0 - toplamNet) * 10) / 10;
                    rozetlerHtml += `<span class="yillik-rozet-hap bilgi">🟢 Kalan Özürsüz Hak: ${kalanOzsz} Gün</span>`;
                    rozetlerHtml += `<span class="yillik-rozet-hap bilgi">🛡️ Kalan Toplam Hak: ${kalanToplam} Gün (30G)</span>`;

                    // 3. MEB 5 GEÇ KALMA KURALI ROZETİ
                    if (gSayisi > 0) {
                        const gEtkisi = Math.floor(gSayisi / 5) * 0.5;
                        const gKalan = 5 - (gSayisi % 5);
                        let aciklama = gEtkisi > 0 ? ` (${gEtkisi}G Özürsüze Eklendi)` : ` (Sıradaki 0.5G için ${gKalan} geç kaldı)`;
                        rozetlerHtml += `<span class="yillik-rozet-hap gec">⏱️ ${gSayisi} Kez Geç Kaldı${aciklama}</span>`;
                    } else {
                        rozetlerHtml += `<span class="yillik-rozet-hap guvenli">✨ Hiç Geç Kalma Yok (Dakik)</span>`;
                    }

                    // 4. HAFTASONU BİRLEŞTİRME VE EĞİLİM ROZETİ
                    if (haftaIciSayisi >= 3 && (pztCumaSayisi / haftaIciSayisi) >= 0.40) {
                        const yuzde = Math.round((pztCumaSayisi / haftaIciSayisi) * 100);
                        rozetlerHtml += `<span class="yillik-rozet-hap aliskanlik">🗓️ Hafta Sonu Birleştirme Eğilimi (Pzt/Cuma: %${yuzde})</span>`;
                    }

                    // 5. DEVAMSIZLIK AĞIRLIĞI VE ÖRNEK KATILIM
                    if (ozszNet === 0 && ozrlNet === 0 && gSayisi === 0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap kusursuz">🌟 Kusursuz Katılım (Sıfır Gün Kayıp)</span>`;
                    } else if (ozrlNet > ozszNet * 2 && ozrlNet > 0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap bilgi">🏥 Sağlık / Rapor Ağırlıklı (${ozrlNet}G)</span>`;
                    } else if (ozszNet > ozrlNet * 2 && ozszNet > 0) {
                        rozetlerHtml += `<span class="yillik-rozet-hap kritik">⚠️ İzinsiz / Özürsüz Ağırlıklı (${ozszNet}G)</span>`;
                    }

                    rozetlerHtml = `<div style="width: 100%; font-size: 11.5px; font-weight: 700; color: var(--fg-sub); display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                        <i data-lucide="award" height="13" width="13" style="color: #F59E0B;"></i> Pedagojik & Yasal Devamsızlık Karnesi Analizi:
                    </div>` + rozetlerHtml;

                    rozetlerAlani.innerHTML = rozetlerHtml;
                    if (window.lucide && typeof lucide.createIcons === 'function') {
                        lucide.createIcons();
                    }
                }

                for(let rowIdx=1; rowIdx<=10; rowIdx++) {
                    let ayAd = aylarList[rowIdx-1]; let ayNo = ayNolar[rowIdx-1];
                    let tr = document.createElement('tr');
                    tr.innerHTML = `<td id="yillik_row_${rowIdx}" style="background-color: var(--border); color: var(--fg-main); font-weight: bold; padding: 4px; border: 1px solid var(--border);">${ayAd}</td>`;
                    
                    let okulYili_baslangic = calMonth >= 7 ? calYear : calYear - 1;
                    for(let gun=1; gun<=31; gun++) {
                        let y_val = ayNo < 8 ? okulYili_baslangic + 1 : okulYili_baslangic;
                        let is_valid = true, is_weekend = false; let dt = new Date(y_val, ayNo-1, gun);
                        if (dt.getMonth() + 1 !== ayNo) is_valid = false; else if (dt.getDay() === 0 || dt.getDay() === 6) is_weekend = true;

                        let cellBg = karanlikMod ? "#1E293B" : "#F1F5F9"; let cellFg = "var(--fg-main)"; let cellText = ""; let isAbs = false;
                        if (!is_valid || is_weekend) { cellBg = karanlikMod ? "#0B1120" : "#D1D5DB"; } 
                        else {
                            let devKey = `${y_val}-${ayNo}-${gun}`;
                            if (devMap[devKey]) { cellText = devMap[devKey]; isAbs = true; cellBg = rH[cellText] || "#64748B"; cellFg = "#FFFFFF"; }
                        }

                        yillikHucreler.push({ r: rowIdx, c: gun, isAbs: isAbs, isValid: (is_valid && !is_weekend), tur: cellText, orjBg: cellBg, orjFg: cellFg });
                        let onEvts = `onmouseenter="yillikHoverEnter(${rowIdx}, ${gun})" onmouseleave="yillikHoverLeave()"`;
                        tr.innerHTML += `<td id="yillik_hucre_${rowIdx}_${gun}" ${onEvts} style="background-color: ${cellBg}; color: ${cellFg}; border: 1px solid var(--border); font-weight: bold; font-size: 10px; cursor: default; transition: 0.1s;">${cellText}</td>`;
                    }
                    tbody.appendChild(tr);
                }
                
                function ozetKutusuCiz(baslik, detay, hsDict, net, fgColor) {
                    let html = `<div style="width: 250px; background-color: var(--bg-main); border: 1px solid var(--border); display: flex; flex-direction: column;">
                        <div style="background-color: #1E3A8A; color: white; padding: 6px; text-align: center; font-weight: bold; font-size: 11px;">${baslik}</div>
                        <div style="flex: 1; padding: 10px; display: flex; flex-direction: column; gap: 4px; font-size: 10px;">`;
                    if (Object.keys(detay).length === 0) { html += `<div style="text-align: center; color: var(--fg-sub); margin-top: 10px;">Kayıt Yok</div>`; } 
                    else {
                        for(let tur in detay) {
                            let hsGun = hsDict[tur] || 0; let hsYazi = hsGun > 0 ? ` <span style="font-size:9px;">(${hsGun} Hafta Sonu)</span>` : ''; let safTur = tur.split(" ")[0]; let rnk = rH[safTur] || 'var(--fg-sub)';
                            html += `<div style="cursor: pointer;" onmouseenter="yillikHoverEnter(null, null, '${safTur}')" onmouseleave="yillikHoverLeave()">
                                <span style="color: ${rnk}; font-weight: bold;">${tur} :</span> <span style="color: var(--fg-main); font-weight:bold;">${detay[tur]} Gün</span><span style="color: var(--fg-sub);">${hsYazi}</span>
                            </div>`;
                        }
                    }
                    html += `</div><div style="text-align: center; padding: 6px; font-weight: bold; font-size: 13px; color: ${fgColor}; border-top: 1px solid var(--border); background-color: var(--bg-card);">Toplam: ${net} Gün</div></div>`;
                    return html;
                }

                ozetAlani.innerHTML += ozetKutusuCiz("Özürlü Devamsızlık", detayOzurlu, hsOzurlu, ozrlNet, "var(--fg-main)");
                ozetAlani.innerHTML += ozetKutusuCiz("Özürsüz Devamsızlık", detayOzursuz, hsOzursuz, ozszNet, ozszNet >= 10 ? "#DC2626" : "var(--fg-main)");
                ozetAlani.innerHTML += ozetKutusuCiz("Diğer Devamsızlık", detayDiger, hsDiger, digerNet, "var(--fg-main)");

                modalAc('yillik_modal');
            });
        }

        // --- 3. SAĞ TIK MENU VE KOPYALAMA ---
        let sagTikOgrNo = ""; let sagTikOgrAd = "";
        function sagTikMenuAc(e, no, ad) {
            e.preventDefault(); sagTikOgrNo = no; sagTikOgrAd = ad;
            const menu = document.getElementById('sag_tik_menu');
            if(menu) { menu.style.display = 'flex'; menu.style.left = e.pageX + 'px'; menu.style.top = e.pageY + 'px'; }
        }
        function kopyalaNo() { navigator.clipboard.writeText(sagTikOgrNo); bildirimGoster("Numara kopyalandı!", "bilgi"); }
        function kopyalaAd() { navigator.clipboard.writeText(sagTikOgrAd); bildirimGoster("Ad Soyad kopyalandı!", "bilgi"); }

        // --- 4. ANA TABLO, ZEKİ FORMATLAYICI VE TAKVİM ---
        function sinifFormatla(orj) {
            if(!orj) return "-";
            // 1. Önce parantez içindeki her şeyi /(.*?)/ toptan siler (örn: "(Alanı Yok)").
            // 2. Sonra sınıf/şube yazılarını siler.
            // 3. En son aradaki boşlukları ve noktaları temizler.
            return orj.replace(/\(.*?\)/g, '')
                      .replace(/sınıfı/ig, '')
                      .replace(/sınıf/ig, '')
                      .replace(/sinifi/ig, '')
                      .replace(/sinif/ig, '')
                      .replace(/şubesi/ig, '')
                      .replace(/subesi/ig, '')
                      .replace(/şube/ig, '')
                      .replace(/sube/ig, '')
                      .replace(/[\.\s]/g, '')
                      .toLocaleUpperCase('tr-TR');
        }
        window.sinifFormatla = sinifFormatla;
        
        function sirala(sutun) {
            if (siralamaSutun === sutun) siralamaYon *= -1; else { siralamaSutun = sutun; siralamaYon = 1; }
            tabloyuDoldur();
        }
        function basliklariGuncelle() {
            const basliklar = { 'temizSube': 'Sınıf', 'no': 'No', 'ad_soyad': 'Ad Soyad', 'ozsz': 'Özürsüz', 'ozrl': 'Özürlü' };
            for(let key in basliklar) {
                let el = document.getElementById('span_' + key);
                if(el) {
                    el.innerText = basliklar[key] + (siralamaSutun === key ? (siralamaYon === 1 ? ' ▲' : ' ▼') : ' ↕');
                    el.style.whiteSpace = 'nowrap';
                    el.style.overflow = 'visible';
                    el.style.textOverflow = 'clip';
                    const parentTh = el.closest('th');
                    if (parentTh) {
                        parentTh.style.textAlign = 'left';
                        parentTh.style.padding = '6px 4px';
                    }
                }
            }
        }
                function dosyaYukle(endpoint, event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Excel dosyasi sisteme aktariliyor...");
            fetch(`${API}/${endpoint}`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) {
                    ilerlemeTakipEt(v.job_id);
                } else {
                    yuklemeGizle();
                    bildirimGoster("Hata: " + v.mesaj, "hata");
                }
                if(event && event.target) event.target.value = '';
            }).catch(err => { 
                yuklemeGizle(); 
                bildirimGoster(err.message || "Baglanti hatasi! Sunucuyu kontrol edin.", "hata"); 
            });
        }

        function ilerlemeTakipEt(job_id, tamamlaninca) {
            fetch(`${API}/islem-durumu/${job_id}`).then(r => r.json()).then(durum => {
                if(durum.durum === 'tamamlandi') {
                    yuklemeGizle();

                    // İnteraktif Toast [Geri Al] Butonlu Bildirim (Manifesto Madde 5.2)
                    Toastify({
                        text: `<div class="toast-content" style="display:flex; align-items:center; justify-content:space-between; gap:14px; width:100%;">
                            <span>✓ ${durum.mesaj}</span>
                            <button onclick="sonIslemiGeriAl()" style="background:#EF4444; color:#FFFFFF; border:none; padding:4px 10px; border-radius:4px; font-weight:700; font-size:11px; cursor:pointer; box-shadow:0 2px 4px rgba(0,0,0,0.3); white-space:nowrap;">↩️ Geri Al</button>
                        </div>`,
                        duration: 9000,
                        escapeMarkup: false,
                        gravity: "top", 
                        position: "center", 
                        stopOnFocus: true,
                        close: true, 
                        style: {
                            background: "linear-gradient(to right, #065F46, #047857)",
                            borderRadius: "8px",
                            fontWeight: "600",
                            fontFamily: "'Inter', sans-serif",
                            boxShadow: "0 10px 25px -3px rgba(0, 0, 0, 0.35)",
                            padding: "12px 20px"
                        }
                    }).showToast();

                    verileriYukle();
                    gecKalanBildirimiGoster();
                    if(tamamlaninca) tamamlaninca();
                } else if(durum.durum === 'hata') {
                    yuklemeGizle();
                    bildirimGoster("Hata: " + durum.mesaj, "hata");
                } else if(durum.durum === 'isleniyor' || durum.durum === 'basladi') {
                    yuklemeGoster(durum.mesaj + " (%" + durum.yuzde + ")");
                    setTimeout(() => ilerlemeTakipEt(job_id, tamamlaninca), 500);
                } else {
                    yuklemeGizle();
                    bildirimGoster("Bilinmeyen bir durum olustu.", "hata");
                }
            }).catch(err => {
                yuklemeGizle();
                bildirimGoster("Ilerleme takip edilemedi.", "hata");
            });
        }

        // --- DİNAMİK HIZLI EŞİK / ROZET AÇILIR FİLTRE MOTORU (SABİT 380PX DROPDOWN) ---
        let aktifEsikFiltresi = 'tumu';

        function esikSelectFiltrele(tur) {
            aktifEsikFiltresi = tur || 'tumu';
            const combo = document.getElementById('combo_esik_filtre');
            if (combo && combo.value !== aktifEsikFiltresi) combo.value = aktifEsikFiltresi;
            tabloyuDoldur();
        }

        function esikSayilariniGuncelle() {
            let sayiTumu = ogrenciListesi.length;
            let sayiRamak = 0;
            let sayiAsan = 0;
            let sayiMektup = 0;
            let sayiToplam = 0;
            let sayiKusursuz = 0;
            let sayiRaporlu = 0;

            ogrenciListesi.forEach(ogr => {
                const ozsz = Math.round((ogr.ozursuz || 0) * 10) / 10;
                const ozrl = Math.round((ogr.ozurlu || 0) * 10) / 10;
                const toplam = Math.round((ozsz + ozrl) * 10) / 10;

                if (ozsz >= 8.5 && ozsz < 10.0) sayiRamak++;
                if (ozsz >= 10.0) sayiAsan++;
                if (ozsz >= 4.5 && ozsz <= 5.0) sayiMektup++;
                if (toplam >= 25.0) sayiToplam++;
                if (ozsz === 0 && ozrl === 0) sayiKusursuz++;
                if (ozrl > 0) sayiRaporlu++;
            });

            const combo = document.getElementById('combo_esik_filtre');
            if (combo) {
                const optMap = {
                    'tumu': `🔵 Tümü (${sayiTumu} Öğrenci)`,
                    'ramakkala_10': `🚨 10G Ramak Kala (${sayiRamak} Öğrenci)`,
                    'asanlar_10': `⛔ 10G+ Aşanlar (${sayiAsan} Öğrenci)`,
                    'mektup_5': `📬 5G 1. Veli Mektubu (${sayiMektup} Öğrenci)`,
                    'toplam_25': `⏳ 25G+ Toplam Risk (${sayiToplam} Öğrenci)`,
                    'kusursuz_0': `🌟 Kusursuz (0 Gün) (${sayiKusursuz} Öğrenci)`,
                    'raporlu_ozrl': `🏥 Sağlık / Raporlu (${sayiRaporlu} Öğrenci)`
                };
                for (let i = 0; i < combo.options.length; i++) {
                    const val = combo.options[i].value;
                    if (optMap[val]) {
                        combo.options[i].text = optMap[val];
                    }
                }
            }
        }

        function filtreTemizle() {
            const ent = document.getElementById('ent_arama');
            if (ent) ent.value = "";
            const comboSube = document.getElementById('combo_arama_sube');
            if (comboSube) comboSube.value = "Tümü";
            aktifEsikFiltresi = 'tumu';
            const comboEsik = document.getElementById('combo_esik_filtre');
            if (comboEsik) comboEsik.value = 'tumu';
            tabloyuDoldur();
        }

        function tabloyuDoldur() {
            const arama = document.getElementById('ent_arama') ? document.getElementById('ent_arama').value.toLocaleUpperCase('tr-TR') : "";
            const subeFiltre = document.getElementById('combo_arama_sube') ? document.getElementById('combo_arama_sube').value : "Tümü";
            const govde = document.getElementById('tree_govde'); if(!govde) return;
            govde.innerHTML = ""; basliklariGuncelle();

            let islenecekler = ogrenciListesi.map(ogr => {
                let temizSube = sinifFormatla(ogr.sube);
                return { ...ogr, temizSube: temizSube, ozsz: Math.round((ogr.ozursuz || 0)*10)/10, ozrl: Math.round((ogr.ozurlu || 0)*10)/10 };
            }).filter(ogr => {
                if (subeFiltre !== "Tümü" && ogr.temizSube !== subeFiltre) return false;
                if (arama && arama !== "NUMARA VEYA AD SOYAD" && !ogr.ad_soyad.toLocaleUpperCase('tr-TR').includes(arama) && !ogr.no.includes(arama)) return false;

                // Dinamik Hızlı Eşik Çipleri Filtresi
                if (aktifEsikFiltresi === 'ramakkala_10') {
                    if (!(ogr.ozsz >= 8.5 && ogr.ozsz < 10.0)) return false;
                } else if (aktifEsikFiltresi === 'asanlar_10') {
                    if (!(ogr.ozsz >= 10.0)) return false;
                } else if (aktifEsikFiltresi === 'mektup_5') {
                    if (!(ogr.ozsz >= 4.5 && ogr.ozsz <= 5.0)) return false;
                } else if (aktifEsikFiltresi === 'toplam_25') {
                    if (!((ogr.ozsz + ogr.ozrl) >= 25.0)) return false;
                } else if (aktifEsikFiltresi === 'kusursuz_0') {
                    if (!(ogr.ozsz === 0 && ogr.ozrl === 0)) return false;
                } else if (aktifEsikFiltresi === 'raporlu_ozrl') {
                    if (!(ogr.ozrl > 0)) return false;
                }

                return true;
            });

            islenecekler.sort((a, b) => {
                let valA = a[siralamaSutun]; let valB = b[siralamaSutun];
                if(siralamaSutun === 'temizSube') {
                    let numA = parseInt(a.temizSube) || 99; let numB = parseInt(b.temizSube) || 99;
                    if(numA !== numB) return (numA - numB) * siralamaYon;
                }
                if(['no', 'ozsz', 'ozrl'].includes(siralamaSutun)) { valA = parseFloat(valA || 0); valB = parseFloat(valB || 0); }
                if (valA < valB) return -1 * siralamaYon; if (valA > valB) return 1 * siralamaYon;
                return 0;
            });

            const fragment = document.createDocumentFragment();
            islenecekler.forEach(ogr => {
                const ozszStr = ogr.ozsz >= 10 ? `<span style="font-weight:bold; color:#EF4444;">${ogr.ozsz} Gün</span>` : `${ogr.ozsz} Gün`;
                const tr = document.createElement('tr'); tr.style.cursor = "pointer"; tr.style.borderBottom = "1px solid var(--border)";
                if (ogr.ozsz >= 10) { tr.style.backgroundColor = "#FEE2E2"; tr.style.color = "#991B1B"; }
                tr.onclick = function() {
                    document.querySelectorAll('#tree_govde tr').forEach(row => row.classList.remove('tr-secili'));
                    tr.classList.add('tr-secili'); ogrenciSec(ogr.no, ogr.ad_soyad, ogr.temizSube, ogr.ozsz, ogr.ozrl);
                };
                tr.ondblclick = function() { yillikListeAc(ogr.no, ogr.ad_soyad); };
                tr.oncontextmenu = function(e) {
                    document.querySelectorAll('#tree_govde tr').forEach(row => row.classList.remove('tr-secili'));
                    tr.classList.add('tr-secili'); ogrenciSec(ogr.no, ogr.ad_soyad, ogr.temizSube, ogr.ozsz, ogr.ozrl); sagTikMenuAc(e, ogr.no, ogr.ad_soyad);
                };
                tr.innerHTML = `<td style="padding: 5px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.temizSube}</td><td style="padding: 5px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.no}</td><td style="padding: 5px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ad_soyad}</td><td style="padding: 5px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ozszStr}</td><td style="padding: 5px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ozrl} Gün</td>`;
                fragment.appendChild(tr);
            });
            govde.appendChild(fragment);

            esikSayilariniGuncelle();
        }

        function ogrenciSec(no, ad, sube, ozsz, ozrl) {
            const fOzsz = parseFloat(ozsz || 0);
            const fOzrl = parseFloat(ozrl || 0);
            const toplam = Math.round((fOzsz + fOzrl) * 10) / 10;
            seciliOgrenci = { no: no, ad: ad, sube: sube, ozsz: fOzsz, ozrl: fOzrl, toplam: toplam };
            
            document.getElementById('sag_bos_uyari').style.display = 'none'; 
            document.getElementById('sag_dolu_icerik').style.display = 'flex';
            

            // Devamsızlıkları veritabanından çek ve takvim ile önizlemeyi doldur
            fetch(`${API}/ogrenci-detay/${no}`).then(res => res.json()).then(veri => {
                seciliDevamsizliklar = veri.devamsizliklar.map(d => ({...d, secili: false})); 
                geciciDevamsizliklar = []; 
                aktifTakvimiCiz(); 
                onizlemeGuncelle();
            });
        }

        // --- 1-TIK VELİ WHATSAPP BİLDİRİM METNİ KOPYALAYICI ---
        function veliWhatsAppKopyala() {
            if (!seciliOgrenci) {
                bildirimGoster("Lütfen önce listeden bir öğrenci seçiniz.", "hata");
                return;
            }
            const o = seciliOgrenci;
            const bugunTarih = new Date().toLocaleDateString('tr-TR');
            const toplam = Math.round(((o.ozsz || 0) + (o.ozrl || 0)) * 10) / 10;

            let durumMetni = "";
            if (o.ozsz >= 10.0) {
                durumMetni = "⚠️ ÖNEMLİ BİLGİLENDİRME: Öğrencinizin özürsüz devamsızlığı yasal 10 gün sınırını aşmış olup sınıf tekrarı riski bulunmaktadır.";
            } else if (o.ozsz >= 8.5) {
                durumMetni = "⚠️ DİKKAT: Öğrencinizin özürsüz devamsızlığı 10 günlük yasal sınıra yaklaşmıştır.";
            } else {
                durumMetni = "Bilgilerinize arz olunur.";
            }

            const metin = `Sayın Velimiz,\n\n${o.sube} sınıfı ${o.no} numaralı öğrencimiz ${o.ad}'in ${bugunTarih} itibarıyla okul devamsızlık durumu aşağıdadır:\n\n• Özürsüz Devamsızlık: ${o.ozsz} Gün\n• Özürlü / İzinli: ${o.ozrl} Gün\n• Toplam Devamsızlık: ${toplam} Gün (Yasal sınır: 30 Gün)\n\n${durumMetni}\n\nMEB Ortaöğretim Kurumları Yönetmeliği gereği devamsızlıkların veli tarafından düzenli takibi rica olunur.\nOkul İdaresi`;

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(metin).then(() => {
                    bildirimGoster(`✅ ${o.ad} için resmi veli WhatsApp bildirim metni panoya kopyalandı!`, "bilgi");
                }).catch(() => {
                    panoyaKopyalaFallback(metin);
                    bildirimGoster(`✅ ${o.ad} için veli bildirim metni kopyalandı.`, "bilgi");
                });
            } else {
                panoyaKopyalaFallback(metin);
                bildirimGoster(`✅ ${o.ad} için veli bildirim metni kopyalandı.`, "bilgi");
            }
        }

        function panoyaKopyalaFallback(text) {
            const ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed";
            ta.style.left = "-9999px";
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            try { document.execCommand('copy'); } catch (e) {}
            document.body.removeChild(ta);
        }

        let seciliTakvimGorunumu = localStorage.getItem('takvimGorunumu') || 'aylik';

        function takvimGorunumDegistir(gorunum) {
            seciliTakvimGorunumu = gorunum;
            localStorage.setItem('takvimGorunumu', gorunum);
            
            const btnAylik = document.getElementById('btn_gorunum_aylik');
            const btnYillik = document.getElementById('btn_gorunum_yillik');
            const aylikNav = document.getElementById('aylik_navigasyon_kutusu');
            const yillikBaslik = document.getElementById('lbl_yillik_baslik');
            const gridAylik = document.getElementById('takvim_grid');
            const gridYillik = document.getElementById('yillik_isi_haritasi_kapsayici');
            
            if (gorunum === 'yillik') {
                if (btnAylik) btnAylik.classList.remove('aktif');
                if (btnYillik) btnYillik.classList.add('aktif');
                if (aylikNav) aylikNav.style.display = 'none';
                if (yillikBaslik) yillikBaslik.style.display = 'inline-flex';
                if (gridAylik) gridAylik.style.display = 'none';
                if (gridYillik) {
                    gridYillik.style.display = 'grid';
                    yillikIsiHaritasiCiz();
                }
            } else {
                if (btnYillik) btnYillik.classList.remove('aktif');
                if (btnAylik) btnAylik.classList.add('aktif');
                if (yillikBaslik) yillikBaslik.style.display = 'none';
                if (aylikNav) aylikNav.style.display = 'flex';
                if (gridYillik) gridYillik.style.display = 'none';
                if (gridAylik) {
                    gridAylik.style.display = 'grid';
                    takvimiCiz();
                }
            }
            if (window.lucide && typeof lucide.createIcons === 'function') {
                lucide.createIcons();
            }
        }

        function aktifTakvimiCiz() {
            if (seciliTakvimGorunumu === 'yillik') {
                const btnAylik = document.getElementById('btn_gorunum_aylik');
                const btnYillik = document.getElementById('btn_gorunum_yillik');
                const aylikNav = document.getElementById('aylik_navigasyon_kutusu');
                const yillikBaslik = document.getElementById('lbl_yillik_baslik');
                const gridAylik = document.getElementById('takvim_grid');
                const gridYillik = document.getElementById('yillik_isi_haritasi_kapsayici');
                if (btnAylik) btnAylik.classList.remove('aktif');
                if (btnYillik) btnYillik.classList.add('aktif');
                if (aylikNav) aylikNav.style.display = 'none';
                if (yillikBaslik) yillikBaslik.style.display = 'inline-flex';
                if (gridAylik) gridAylik.style.display = 'none';
                if (gridYillik) {
                    gridYillik.style.display = 'grid';
                    yillikIsiHaritasiCiz();
                }
            } else {
                takvimiCiz();
            }
        }

        function yillikIsiHaritasiCiz() {
            const kapsayici = document.getElementById('yillik_isi_haritasi_kapsayici');
            if (!kapsayici) return;
            kapsayici.innerHTML = "";

            const tumKayitlar = [...seciliDevamsizliklar, ...geciciDevamsizliklar];
            const okulYiliBaslangic = calMonth >= 7 ? calYear : calYear - 1;

            const aylarSirasi = [
                { ayNo: 9, ayIdx: 8, ad: "Eylül", yil: okulYiliBaslangic },
                { ayNo: 10, ayIdx: 9, ad: "Ekim", yil: okulYiliBaslangic },
                { ayNo: 11, ayIdx: 10, ad: "Kasım", yil: okulYiliBaslangic },
                { ayNo: 12, ayIdx: 11, ad: "Aralık", yil: okulYiliBaslangic },
                { ayNo: 1, ayIdx: 0, ad: "Ocak", yil: okulYiliBaslangic + 1 },
                { ayNo: 2, ayIdx: 1, ad: "Şubat", yil: okulYiliBaslangic + 1 },
                { ayNo: 3, ayIdx: 2, ad: "Mart", yil: okulYiliBaslangic + 1 },
                { ayNo: 4, ayIdx: 3, ad: "Nisan", yil: okulYiliBaslangic + 1 },
                { ayNo: 5, ayIdx: 4, ad: "Mayıs", yil: okulYiliBaslangic + 1 },
                { ayNo: 6, ayIdx: 5, ad: "Haziran", yil: okulYiliBaslangic + 1 }
            ];

            const fragment = document.createDocumentFragment();

            aylarSirasi.forEach(item => {
                const kart = document.createElement('div');
                kart.className = 'isi-haritasi-ay-karti';

                const sonGun = new Date(item.yil, item.ayNo, 0).getDate();
                const ilkGun = new Date(item.yil, item.ayIdx, 1);
                let ilkGunIndeksi = ilkGun.getDay();
                let bosluk = (ilkGunIndeksi !== 0 && ilkGunIndeksi !== 6) ? ilkGunIndeksi - 1 : 0;

                let ayToplam = 0;
                for (let gun = 1; gun <= sonGun; gun++) {
                    let dStr = `${gun.toString().padStart(2, '0')}/${item.ayNo.toString().padStart(2, '0')}/${item.yil}`;
                    let kayitlar = tumKayitlar.filter(k => k.tarih === dStr && ['D', 'ÖY', 'SY'].includes(k.tur.toLocaleUpperCase('tr-TR')));
                    if (kayitlar.length > 0) ayToplam += parseFloat(kayitlar[0].gun || 1);
                }

                kart.innerHTML = `
                    <div class="isi-haritasi-ay-baslik-satiri">
                        <span class="isi-haritasi-ay-baslik">${item.ad} ${item.yil}</span>
                        <span class="isi-haritasi-ay-sayac ${ayToplam === 0 ? 'sifir' : ''}">${ayToplam > 0 ? ayToplam + ' Gün' : '0 Dev.'}</span>
                    </div>
                    <div class="isi-haritasi-gunler-header">
                        <span>Pt</span><span>Sa</span><span>Ça</span><span>Pe</span><span>Cu</span>
                    </div>
                    <div class="isi-haritasi-grid" id="isi_grid_${item.ayNo}_${item.yil}"></div>
                `;

                const grid = kart.querySelector(`#isi_grid_${item.ayNo}_${item.yil}`);
                for (let b = 0; b < bosluk; b++) {
                    const bosEl = document.createElement('div');
                    bosEl.className = 'isi-haritasi-hucre bos';
                    grid.appendChild(bosEl);
                }

                for (let gun = 1; gun <= sonGun; gun++) {
                    const dt = new Date(item.yil, item.ayIdx, gun);
                    const gunHafta = dt.getDay();
                    if (gunHafta === 0 || gunHafta === 6) continue;

                    const tarihStr = `${gun.toString().padStart(2, '0')}/${item.ayNo.toString().padStart(2, '0')}/${item.yil}`;
                    const hedefKayitlar = tumKayitlar.filter(k => k.tarih === tarihStr && ['D', 'ÖY', 'SY'].includes(k.tur.toLocaleUpperCase('tr-TR')));
                    const kayit = hedefKayitlar.length > 0 ? (hedefKayitlar.find(k => k.secili) || hedefKayitlar[hedefKayitlar.length - 1]) : null;

                    let bg = "var(--bg-main)";
                    let fg = "var(--fg-sub)";
                    let text = gun;
                    let extraClass = "";

                    if (kayit) {
                        const tur = kayit.tur.toLocaleUpperCase('tr-TR');
                        bg = "var(--dev-bg)";
                        fg = "var(--dev-fg)";
                        text = `${gun} ${tur}`;
                        if (kayit.secili) extraClass = "secili-onizleme";
                    }

                    const hucre = document.createElement('div');
                    hucre.className = `isi-haritasi-hucre ${extraClass}`;
                    hucre.style.backgroundColor = bg;
                    hucre.style.color = fg;
                    hucre.title = `${tarihStr}: ${kayit ? kayit.gun + ' gün ' + kayit.tur : 'Devamsızlık Yok'}`;
                    hucre.innerText = text;
                    hucre.onclick = () => hucreTikla(tarihStr);
                    hucre.oncontextmenu = (e) => hucreSagTikla(e, tarihStr);
                    grid.appendChild(hucre);
                }

                fragment.appendChild(kart);
            });

            kapsayici.appendChild(fragment);
        }

        function ayDegistir(artis) { calMonth += artis; if (calMonth > 11) { calMonth = 0; calYear++; } else if (calMonth < 0) { calMonth = 11; calYear--; } takvimiCiz(); }

        function takvimiCiz() {
            document.getElementById('lbl_ay_yil').innerText = `${aylar[calMonth]} ${calYear}`;
            const grid = document.getElementById('takvim_grid');
            grid.innerHTML = `<div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Pzt</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Sal</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Çar</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Per</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Cum</div>`;
            const ilkGun = new Date(calYear, calMonth, 1); 
            const sonGun = new Date(calYear, calMonth + 1, 0).getDate();
            
            let ilkGunIndeksi = ilkGun.getDay();
            let bosGunSayisi = 0;
            if (ilkGunIndeksi !== 0 && ilkGunIndeksi !== 6) { bosGunSayisi = ilkGunIndeksi - 1; }
            for(let i = 0; i < bosGunSayisi; i++) { grid.innerHTML += `<div class="gun-hucre bos"></div>`; }

            const tumKayitlar = [...seciliDevamsizliklar, ...geciciDevamsizliklar];
            for(let i = 1; i <= sonGun; i++) {
                let haftaninGunu = new Date(calYear, calMonth, i).getDay(); 
                if (haftaninGunu === 0 || haftaninGunu === 6) continue; 
                let tarihStr = `${i.toString().padStart(2, '0')}/${(calMonth+1).toString().padStart(2, '0')}/${calYear}`;
                
                let hedefKayitlar = tumKayitlar.filter(k => k.tarih === tarihStr && ['D', 'ÖY', 'SY'].includes(k.tur.toLocaleUpperCase('tr-TR')));
                let kayit = hedefKayitlar.length > 0 ? (hedefKayitlar.find(k => k.secili) || hedefKayitlar[hedefKayitlar.length - 1]) : null;
                
                let borderStyle = 'border: 1px solid var(--border);'; 
                // YENİ: Boş günlere bembeyaz olmak yerine hafif sekmelerdeki gri tonu verdik
                let bgStyle = 'background-color: var(--bg-main);'; 
                let fgStyle = ''; 
                let icerik = '<div></div>'; 
                
                if (kayit) {
                    let tur = kayit.tur.toLocaleUpperCase('tr-TR');
                    // YENİ: Kırmızı rengi artık JS değil CSS (temaDegistir'deki değişkenler) yönetiyor!
                    bgStyle = 'background-color: var(--dev-bg);'; 
                    fgStyle = 'var(--dev-fg)';
                    icerik = `<div style="font-size: 12px; font-weight: bold; text-align: center; color: ${fgStyle};">${kayit.gun} ${tur}</div>`;
                    if(kayit.secili) borderStyle = 'border: 2px solid #10B981; box-shadow: inset 0 0 5px #10B981;';
                }
                grid.innerHTML += `<div class="gun-hucre" style="${bgStyle} ${borderStyle}" onclick="hucreTikla('${tarihStr}')" oncontextmenu="hucreSagTikla(event, '${tarihStr}')"><div style="color: ${fgStyle || 'var(--fg-main)'};">${i}</div>${icerik}</div>`;
            }
        }

        function hucreTikla(tarihStr) {
            let kalici = seciliDevamsizliklar.find(d => d.tarih === tarihStr && ['D', 'ÖY', 'SY'].includes(d.tur.toLocaleUpperCase('tr-TR')));
            if (kalici) { 
                kalici.secili = !kalici.secili; 
                aktifTakvimiCiz(); 
                onizlemeGuncelle(); 
                return; 
            }

            let gecici = geciciDevamsizliklar.find(d => d.tarih === tarihStr);
            if (!gecici) { geciciDevamsizliklar.push({id: 'temp_'+Date.now(), tarih: tarihStr, tur: 'D', gun: '1', secili: true}); } 
            else {
                if(gecici.tur === 'D') { gecici.tur = 'SY'; gecici.gun = '0.5'; }
                else if(gecici.tur === 'SY') { gecici.tur = 'ÖY'; gecici.gun = '0.5'; }
                else if(gecici.tur === 'ÖY') { geciciDevamsizliklar = geciciDevamsizliklar.filter(d => d.tarih !== tarihStr); }
            }
            aktifTakvimiCiz(); 
            onizlemeGuncelle();
        }

        function hucreSagTikla(e, tarihStr) { 
            e.preventDefault(); 
            geciciDevamsizliklar = geciciDevamsizliklar.filter(d => d.tarih !== tarihStr); 
            aktifTakvimiCiz(); 
            onizlemeGuncelle(); 
        }

        let seciliOnizlemeSatirlari = [];
        function onizlemeSatirSec(id) {
            let tr = document.getElementById('onizleme_tr_' + id);
            if (seciliOnizlemeSatirlari.includes(id)) { seciliOnizlemeSatirlari = seciliOnizlemeSatirlari.filter(x => x !== id); tr.style.backgroundColor = "transparent"; } 
            else { seciliOnizlemeSatirlari.push(id); tr.style.backgroundColor = "var(--border)"; }
        }

        function onizlemeGuncelle() {
            const govde = document.getElementById('tree_detay_govde'); govde.innerHTML = "";
            let toplamGun = 0.0; seciliOnizlemeSatirlari = []; 
            
            // Hesaplama Değişkenleri
            let donusenGecmisGun = 0.0; 
            let yeniEklenenGun = 0.0;

            const gosterilecek = [...seciliDevamsizliklar, ...geciciDevamsizliklar].filter(d => d.secili).sort((a,b) => {
                let pa = a.tarih.split('/').reverse().join(''); let pb = b.tarih.split('/').reverse().join(''); return pb.localeCompare(pa);
            });

            gosterilecek.forEach(d => {
                let miktar = parseFloat(d.gun) || 0;
                toplamGun += miktar;
                
                // Eğer bu devamsızlık zaten varsa (E-Okul'dan geldiyse ve temp_ ile başlamıyorsa) Özürsüz'den düşecek
                if(!d.id || !d.id.toString().startsWith('temp_')) { donusenGecmisGun += miktar; } 
                // Eğer yepyeni bir kutuya tıklayarak oluşturulduysa (temp_ ise) sadece Özürlü'ye eklenecek
                else { yeniEklenenGun += miktar; }
                
                govde.innerHTML += `<tr id="onizleme_tr_${d.id}" onclick="onizlemeSatirSec('${d.id}')" style="cursor: pointer; border-bottom: 1px solid var(--border);">
                    <td style="padding: 6px; color: var(--fg-main);">${d.tarih}</td><td style="padding: 6px; color: var(--fg-main);"><b>${d.tur}</b></td><td style="padding: 6px; color: var(--fg-main);">${d.gun}</td>
                </tr>`;
            });
            document.getElementById('lbl_onizleme_toplam').innerText = `Toplam: ${toplamGun} Gün`;

            // Yeni Kutuların Matematik İşlemi ve Ekrana Basılması
            if (seciliOgrenci) {
                let kalanOzursuz = seciliOgrenci.ozsz - donusenGecmisGun;
                if(kalanOzursuz < 0) kalanOzursuz = 0; // Eksiye inmesini engeller
                
                let guncelOzurlu = seciliOgrenci.ozrl + donusenGecmisGun + yeniEklenenGun;
                
                const lblKalan = document.getElementById('lbl_kalan_ozursuz');
                const lblYeni = document.getElementById('lbl_yeni_ozurlu');
                if(lblKalan) lblKalan.innerText = (Math.round(kalanOzursuz * 10) / 10) + ' Gün';
                if(lblYeni) lblYeni.innerText = (Math.round(guncelOzurlu * 10) / 10) + ' Gün';
            }
        }

        function onizlemeCikar() {
            if(seciliOnizlemeSatirlari.length === 0) return;
            seciliDevamsizliklar.forEach(d => { if(seciliOnizlemeSatirlari.includes(d.id.toString())) d.secili = false; });
            geciciDevamsizliklar = geciciDevamsizliklar.filter(d => !seciliOnizlemeSatirlari.includes(d.id.toString()));
            seciliOnizlemeSatirlari = []; aktifTakvimiCiz(); onizlemeGuncelle();
        }

        function onizlemeTemizle() { seciliDevamsizliklar.forEach(d => d.secili = false); geciciDevamsizliklar = []; aktifTakvimiCiz(); onizlemeGuncelle(); }

        function topluSecim(mod) {
            if(!seciliOgrenci) return;
            seciliDevamsizliklar.forEach(d => d.secili = false);
            const parseTarih = (str) => { let p = str.split('/'); return p.length === 3 ? new Date(p[2], p[1]-1, p[0]) : null; };

            seciliDevamsizliklar.forEach(d => {
                if(!['D', 'ÖY', 'SY'].includes(d.tur.toLocaleUpperCase('tr-TR'))) return;
                if(mod === 'tumu') d.secili = true;
                else if(mod === 'bu_ay') {
                    let strAy = (calMonth+1).toString().padStart(2, '0'); let strYil = calYear.toString();
                    if(d.tarih.includes(`/${strAy}/${strYil}`)) d.secili = true;
                }
                else if(mod === 'son_iki_ay') {
                    let strAy1 = (calMonth+1).toString().padStart(2, '0'); let strYil1 = calYear.toString();
                    let prevMonth = calMonth === 0 ? 11 : calMonth - 1; let prevYear = calMonth === 0 ? calYear - 1 : calYear;
                    let strAy2 = (prevMonth+1).toString().padStart(2, '0'); let strYil2 = prevYear.toString();
                    if(d.tarih.includes(`/${strAy1}/${strYil1}`) || d.tarih.includes(`/${strAy2}/${strYil2}`)) d.secili = true;
                }
                else if(mod === 'aralik') {
                    let basStr = document.getElementById('t_bas').value; let bitStr = document.getElementById('t_bit').value;
                    if(!basStr || !bitStr) return; 
                    let bDate = parseTarih(basStr); let eDate = parseTarih(bitStr);
                    if(!bDate || !eDate) return; 
                    let kDate = parseTarih(d.tarih); if(kDate && kDate >= bDate && kDate <= eDate) d.secili = true;
                }
            });
            aktifTakvimiCiz(); onizlemeGuncelle();
        }

        let ozelBas = null; let ozelBit = null;
        let ozelCalYear = new Date().getFullYear(); let ozelCalMonth = new Date().getMonth();

        function takvimBaloncuguAc(e) {
            const kutu = document.getElementById('float_takvim');
            if(kutu.style.display === 'none' || kutu.style.display === '') {
                kutu.style.display = 'block'; ozelBas = null; ozelBit = null; ozelTakvimCiz();
            } else { kutu.style.display = 'none'; }
            if(e) e.stopPropagation();
        }

        function ozelAyDegistir(artis) {
            ozelCalMonth += artis;
            if(ozelCalMonth > 11) { ozelCalMonth = 0; ozelCalYear++; } else if(ozelCalMonth < 0) { ozelCalMonth = 11; ozelCalYear--; }
            ozelTakvimCiz();
        }

        function ozelTakvimCiz() {
            document.getElementById('ozel_ay_yil').innerText = `${aylar[ozelCalMonth]} ${ozelCalYear}`;
            const grid = document.getElementById('ozel_takvim_grid');
            grid.innerHTML = `<div style="color:var(--fg-sub)">Pt</div><div style="color:var(--fg-sub)">Sa</div><div style="color:var(--fg-sub)">Ça</div><div style="color:var(--fg-sub)">Pe</div><div style="color:var(--fg-sub)">Cu</div><div style="color:var(--fg-sub)">Ct</div><div style="color:var(--fg-sub)">Pz</div>`;

            let ilkGun = new Date(ozelCalYear, ozelCalMonth, 1).getDay();
            let bosluk = (ilkGun === 0) ? 6 : ilkGun - 1;
            let sonGun = new Date(ozelCalYear, ozelCalMonth + 1, 0).getDate();

            for(let i=0; i<bosluk; i++) grid.innerHTML += `<div></div>`;

            for(let i=1; i<=sonGun; i++) {
                let dateObj = new Date(ozelCalYear, ozelCalMonth, i);
                let bg = "var(--bg-main)"; let fg = "var(--fg-main)";

                if(ozelBas && ozelBit) {
                    if(dateObj >= ozelBas && dateObj <= ozelBit) { bg = "#4338CA"; fg = "white"; }
                } else if (ozelBas && dateObj.getTime() === ozelBas.getTime()) {
                    bg = "#4338CA"; fg = "white";
                }

                grid.innerHTML += `<div style="padding: 6px 0; cursor: pointer; background: ${bg}; color: ${fg}; border-radius: 4px; border: 1px solid var(--border);" onclick="ozelGunSec(${i}); event.stopPropagation();">${i}</div>`;
            }
            
            let bilgi = document.getElementById('ozel_secim_bilgi');
            if(!ozelBas) bilgi.innerHTML = "<b>1. Adım:</b> Başlangıç tarihini seçin.";
            else if(!ozelBit) bilgi.innerHTML = "<b>2. Adım:</b> Bitiş tarihini seçin.";
            else bilgi.innerHTML = "<b>Harika!</b> Aralığı aktarabilirsiniz.";
        }

        function ozelGunSec(gun) {
            let secilen = new Date(ozelCalYear, ozelCalMonth, gun);
            if(!ozelBas || (ozelBas && ozelBit)) { ozelBas = secilen; ozelBit = null; } 
            else if(secilen < ozelBas) { ozelBas = secilen; } 
            else { ozelBit = secilen; }
            ozelTakvimCiz();
        }

        document.addEventListener('click', function(e) {
            const kutu = document.getElementById('float_takvim');
            const btn = document.getElementById('btn_ozel_sec');
            const sagTikMenu = document.getElementById('sag_tik_menu');
            if(kutu && kutu.style.display === 'block' && !kutu.contains(e.target) && e.target !== btn) { kutu.style.display = 'none'; }
            if(sagTikMenu && e.target !== sagTikMenu && !sagTikMenu.contains(e.target)) { sagTikMenu.style.display = 'none'; }
        });

        function ozelTarihUygula() {
            if(!ozelBas || !ozelBit) { bildirimGoster("Lütfen takvimden iki tarih seçin (Başlangıç ve Bitiş).", "hata"); return; }
            if(!seciliOgrenci) return;
            seciliDevamsizliklar.forEach(d => d.secili = false);
            
            const parseTarihStr = (str) => { let p = str.split('/'); return p.length === 3 ? new Date(p[2], p[1]-1, p[0]) : null; };
            
            let eklenen = 0;
            seciliDevamsizliklar.forEach(d => {
                if(!['D', 'ÖY', 'SY'].includes(d.tur.toLocaleUpperCase('tr-TR'))) return;
                let kDate = parseTarihStr(d.tarih); 
                if(kDate && kDate >= ozelBas && kDate <= ozelBit) { d.secili = true; eklenen++; }
            });
            
            aktifTakvimiCiz(); onizlemeGuncelle();
            document.getElementById('float_takvim').style.display = 'none';
            if(eklenen === 0) bildirimGoster("Seçilen tarih aralığında özürsüz devamsızlık bulunamadı.", "hata");
        }

        function verileriYukle() {
            fetch(`${API}/ogrenciler`).then(res => res.json()).then(veri => {
                ogrenciListesi = veri.ogrenciler || [];
                window.ogrenciListesi = ogrenciListesi; // Modal için global scope
                window.dispatchEvent(new CustomEvent('ogrenciler-guncellendi')); // Alpine'ı tetikle
                let temizSubeler = [...new Set(ogrenciListesi.map(o => sinifFormatla(o.sube)))];
                temizSubeler.sort((a, b) => (parseInt(a)||99) - (parseInt(b)||99));
                const combo = document.getElementById('combo_arama_sube');
                if(combo) {
                    const eskiSecim = combo.value;
                    combo.innerHTML = '<option value="Tümü">Tümü</option>';
                    temizSubeler.forEach(sube => { combo.innerHTML += `<option value="${sube}">${sube}</option>`; });
                    combo.value = eskiSecim || "Tümü";
                }
                tabloyuDoldur();
            }).catch(err => {
                console.error('Öğrenci listesi yüklenemedi:', err);
                bildirimGoster('Öğrenci listesi yüklenemedi. Sunucu bağlantısını kontrol edin.', 'hata');
            });
        }
        
        function izinDilekcesiSablonuOlustur() {
            fetch(`${API}/pdf-izin-sablon`, { method: 'POST' })
            .then(res => res.json()).then(sonuc => {
                if(sonuc.basarili && sonuc.job_id) {
                    ilerlemeTakipEt(sonuc.job_id);
                } else {
                    bildirimGoster(sonuc.mesaj || "Şablon oluşturulamadı", "hata");
                }
            }).catch(err => {
                console.error(err);
                bildirimGoster("Sunucu bağlantı hatası!", "hata");
            });
        }

        function pdfCiktisiAl() {
            if(!seciliOgrenci) return;
            const kayitlar = [...seciliDevamsizliklar, ...geciciDevamsizliklar].filter(d => d.secili);
            if(kayitlar.length === 0) { bildirimGoster("Önizleme listesinde yazdırılacak kayıt yok!", "hata"); return; }
            
            // Seçilen günlerin doğrudan PDF motoruna gönderilmesi yeterlidir.
            // Manuel seçimler veritabanına kaydedilmez, işlem sonrası zaten sıfırlanırlar.
            gercekPdfIstegiAt(kayitlar);
        }

        function gercekPdfIstegiAt(kayitlar) {
            let ad = seciliOgrenci.ad;
            const sube = seciliOgrenci.sube || "Bilinmiyor";
            
            let ozsuz_str = "0";
            let ozu_str = "0";
            const lblKalan = document.getElementById('lbl_kalan_ozursuz');
            const lblYeni = document.getElementById('lbl_yeni_ozurlu');
            
            if(lblKalan) {
                let sayi = parseFloat(lblKalan.innerText);
                if(!isNaN(sayi)) ozsuz_str = String(sayi);
            }
            if(lblYeni) {
                let sayi = parseFloat(lblYeni.innerText);
                if(!isNaN(sayi)) ozu_str = String(sayi);
            }
            
            const veri = { 
                no: seciliOgrenci.no, 
                ad: ad, 
                sube: sube, 
                kayitlar: kayitlar,
                ozurlu_str: ozu_str,
                ozursuz_str: ozsuz_str
            };

            fetch(`${API}/pdf-veli-formu`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) })
            .then(res => res.json()).then(sonuc => {
                if(sonuc.basarili && sonuc.job_id) {
                    ilerlemeTakipEt(sonuc.job_id, () => { geciciDevamsizliklar = []; seciliDevamsizliklar.forEach(d => d.secili = false); aktifTakvimiCiz(); onizlemeGuncelle(); });
                } else {
                    bildirimGoster(sonuc.mesaj, "hata");
                }
            });
        }
        
        // --- 5. YAZI TEBLİĞİ VE AYARLAR ---
               
        function personelleriYukle() {
            return fetch(`${API}/personeller?t=${new Date().getTime()}`).then(res => res.json()).then(veri => {
                try {
                    tumPersoneller = veri.personeller.map(p => ({ ...p, secili: false, manuelEklendi: false }));
                    window.tumPersoneller = tumPersoneller;
                    
                    const cbEden = document.getElementById('b-eden'); const cbEdilen = document.getElementById('b-edilen');
                    if(cbEden && cbEdilen) {
                        cbEden.innerHTML = '<option value="">-- İdareci Seçin --</option>';
                        cbEdilen.innerHTML = '<option value="">-- Personel Seçin --</option>';
                        tumPersoneller.forEach(p => {
                            cbEdilen.innerHTML += `<option value="${p.ad}">${p.ad}</option>`;
                            let pGorev = p.gorev || '';
                            if(p.grup === 'İdare' || pGorev.includes('MÜDÜR')) { cbEden.innerHTML += `<option value="${p.ad}">${p.ad}</option>`; }
                        });
                    }
                    personelFiltrePanelDoldur(); 
                    if (typeof personelTablosunuDoldur === 'function') personelTablosunuDoldur(); 
                    if (typeof yonetimPersonelTablosunuDoldur === 'function') yonetimPersonelTablosunuDoldur();
                } catch(e) { console.error('personelleriYukle hatasi:', e); }
                finally {
                    window.dispatchEvent(new CustomEvent('personeller-guncellendi'));
                }
            });
        }

        function personelFiltrePanelDoldur() {
            const gorevPanel = document.getElementById('personel_gorev_panel');
            const bransPanel = document.getElementById('personel_brans_panel');
            if(!gorevPanel || !bransPanel) return;

            let gorevler = [...new Set(tumPersoneller.map(p => p.gorev))].filter(g => g && g !== "-").sort();
            let branslar = [...new Set(tumPersoneller.map(p => p.brans))].filter(b => b && b !== "-").sort();

            let gHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('gorev')"><i data-lucide="refresh-cw" width="16" height="16"></i> Listedekilerin Hepsini Ekle/Çıkar</div>`;
            gorevler.forEach((g, i) => {
                let gSafe = String(g).replace(/"/g, '&quot;');
                gHtml += `<label class="personel-filtre-item" style="display:flex; gap:5px; width:100%;"><input type="checkbox" onchange="filtreleriHesapla()" data-deger="${gSafe}"> <span>${g}</span></label>`;
            });
            gorevPanel.innerHTML = gHtml;

            let bHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('brans')"><i data-lucide="refresh-cw" width="16" height="16"></i> Listedekilerin Hepsini Ekle/Çıkar</div>`;
            branslar.forEach((b, i) => {
                let bSafe = String(b).replace(/"/g, '&quot;');
                bHtml += `<label class="personel-filtre-item" style="display:flex; gap:5px; width:100%;"><input type="checkbox" onchange="filtreleriHesapla()" data-deger="${bSafe}"> <span>${b}</span></label>`;
            });
            bransPanel.innerHTML = bHtml;
        }

        function personelFiltreTopluUygula(tur) {
            const panel = document.getElementById(`personel_${tur}_panel`);
            const kutular = panel.querySelectorAll('input[type=checkbox]');
            const hepsiIsaretli = [...kutular].every(cb => cb.checked);
            kutular.forEach(cb => cb.checked = !hepsiIsaretli);
            filtreleriHesapla();
        }

        function filtreleriHesapla() {
            const grp_idare = document.getElementById('grp_idare') ? document.getElementById('grp_idare').checked : false;
            const grp_ogr = document.getElementById('grp_ogretmenler') ? document.getElementById('grp_ogretmenler').checked : false;
            const grp_diger = document.getElementById('grp_diger') ? document.getElementById('grp_diger').checked : false;

            const seciliGorevler = Array.from(document.querySelectorAll('#personel_gorev_panel input[type=checkbox]:checked')).map(cb => cb.dataset.deger);
            const seciliBranslar = Array.from(document.querySelectorAll('#personel_brans_panel input[type=checkbox]:checked')).map(cb => cb.dataset.deger);

            tumPersoneller.forEach(p => {
                let uyarMi = false;
                if (grp_idare && p.grup === 'İdare') uyarMi = true;
                if (grp_ogr && p.grup === 'Öğretmenler') uyarMi = true;
                if (grp_diger && p.grup === 'Diğer Personel') uyarMi = true;
                if (seciliGorevler.includes(p.gorev)) uyarMi = true;
                if (seciliBranslar.includes(p.brans)) uyarMi = true;

                if (uyarMi) {
                    p.secili = true;
                } else if (!p.manuelEklendi) {
                    // Kişi artık hiçbir filtreye uymuyorsa ve "arama kutusundan" manuel seçilmediyse listeden çıkarılır.
                    p.secili = false;
                }
            });
            personelTablosunuDoldur();
        }

        function personelTumunuTemizle() {
            if(document.getElementById('grp_idare')) document.getElementById('grp_idare').checked = false;
            if(document.getElementById('grp_ogretmenler')) document.getElementById('grp_ogretmenler').checked = false;
            if(document.getElementById('grp_diger')) document.getElementById('grp_diger').checked = false;
            document.querySelectorAll('.personel-filtre-panel input[type=checkbox]').forEach(cb => cb.checked = false);
            
            const araKutu = document.getElementById('personel_ara');
            if(araKutu) araKutu.value = '';
            
            tumPersoneller.forEach(p => { p.secili = false; p.manuelEklendi = false; });
            personelTablosunuDoldur();
        }

        function personelDurumDegistir(cbElement) {
            let p = tumPersoneller.find(x => x.ad === cbElement.value);
            if(p) {
                p.secili = cbElement.checked;
                p.manuelEklendi = cbElement.checked; // Arama ile eklediyse filtreler değişince uçmasın diye hafızaya alınıyor
            }
            personelTablosunuDoldur(); 
        }



        function personelMasterSecim(durum) {
            document.querySelectorAll('.chk-personel').forEach(cb => {
                cb.checked = durum;
                let p = tumPersoneller.find(x => x.ad === cb.value);
                if(p) { p.secili = durum; p.manuelEklendi = durum; }
            });
            personelTablosunuDoldur();
        }



        function personelSayaciGuncelle() {
            let seciliSayi = tumPersoneller.filter(p => p.secili).length;
            const lbl = document.getElementById('lbl_secili_personel_sayisi');
            if(lbl) { lbl.innerText = `Seçili: ${seciliSayi} Kişi`; lbl.style.color = seciliSayi > 0 ? '#10B981' : '#EF4444'; }
        }

        function personelFiltrePanelAcKapa(tur) {
            const digerTur = tur === 'gorev' ? 'brans' : 'gorev';
            const digerPanel = document.getElementById(`personel_${digerTur}_panel`);
            if(digerPanel) digerPanel.classList.remove('acik');
            const panel = document.getElementById(`personel_${tur}_panel`);
            if(panel) panel.classList.toggle('acik');
        }

        function topluTebligPdfAl() {
            // YENİ: Artık ekrandaki tikleri değil, doğrudan hafızadaki seçili kişileri alıyoruz
            const seciliPersoneller = tumPersoneller.filter(p => p.secili);
            if(seciliPersoneller.length === 0) return bildirimGoster("Lütfen en az bir personel seçin!", "hata");
            
           const veri = { 
                sayi: document.getElementById('t-sayi').value, 
                konu: document.getElementById('t-konu').value, 
                tarih: document.getElementById('t-tarih').value, 
                kurum: document.getElementById('t-kurum') ? document.getElementById('t-kurum').value : "",
                gecici_pdf_yolu: document.getElementById('t-pdf-yol') ? document.getElementById('t-pdf-yol').value : "", // YENİ EKLENDİ
                personeller: seciliPersoneller 
            };
            fetch(`${API}/teblig-toplu-pdf`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) ilerlemeTakipEt(v.job_id);
                else bildirimGoster(v.mesaj, "hata");
            });
        }
        
        function bireyselTebligPdfAl() {
            const edenSecim = document.getElementById('b-eden');
            const edilenSecim = document.getElementById('b-edilen');
            if(edenSecim.selectedIndex < 0 || edilenSecim.selectedIndex < 0) return bildirimGoster("Lütfen tebliğ eden ve edilen kişileri seçin!", "hata");
            
            const edenAd = edenSecim.value;
            const edilenAd = edilenSecim.value;
            
            const edenPersonel = tumPersoneller.find(p => p.ad === edenAd);
            const edilenPersonel = tumPersoneller.find(p => p.ad === edilenAd);
            
            const edenGorev = edenPersonel ? edenPersonel.gorev : "İdareci";
            const edilenGorev = edilenPersonel ? edilenPersonel.gorev : "Personel";
            
            const veri = { 
                sayi: document.getElementById('t-sayi') ? document.getElementById('t-sayi').value : "", 
                konu: document.getElementById('t-konu') ? document.getElementById('t-konu').value : "", 
                tarih: document.getElementById('t-tarih') ? document.getElementById('t-tarih').value : "", 
                kurum: document.getElementById('t-kurum') ? document.getElementById('t-kurum').value : "",
                eden: { ad: edenAd, gorev: edenGorev },
                edilen: { ad: edilenAd, gorev: edilenGorev },
                yer: document.getElementById('b-yer') ? document.getElementById('b-yer').value : "Okul Müdürlüğü",
                teblig_tarihi: document.getElementById('b-tarih') ? document.getElementById('b-tarih').value : null,
                teblig_saati: document.getElementById('b-saat') ? document.getElementById('b-saat').value : null,
                gecici_pdf_yolu: document.getElementById('t-pdf-yol') ? document.getElementById('t-pdf-yol').value : ""
            };
            fetch(`${API}/teblig-bireysel-pdf`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) ilerlemeTakipEt(v.job_id);
                else bildirimGoster(v.mesaj, "hata");
            });
        }
        

        function personelFiltrePanelAcKapa(tur) {
            const digerTur = tur === 'gorev' ? 'brans' : 'gorev';
            const digerPanel = document.getElementById(`personel_${digerTur}_panel`);
            if(digerPanel) digerPanel.classList.remove('acik');
            const panel = document.getElementById(`personel_${tur}_panel`);
            if(panel) panel.classList.toggle('acik');
        }

        document.addEventListener('click', function(e) {
            if(!e.target.closest('.personel-filtre-panel') && !e.target.closest('[onclick*="personelFiltrePanelAcKapa"]')) {
                document.querySelectorAll('.personel-filtre-panel.acik').forEach(p => p.classList.remove('acik'));
            }
        });

         // --- PDF OKUMA MOTORU (Zeki Uyarı Sistemi Eklendi) ---
        function mebPdfYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("MEB Yazısı Çözümleniyor...");
            
            fetch(`${API}/meb-pdf-oku`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                yuklemeGizle();
                if(v.basarili) {
                    document.getElementById('t-sayi').value = v.sayi || '';
                    document.getElementById('t-konu').value = v.konu || '';
                    document.getElementById('t-tarih').value = v.tarih || '';
                    if(document.getElementById('t-kurum')) document.getElementById('t-kurum').value = v.kurum || '';
                    if(document.getElementById('t-pdf-yol')) document.getElementById('t-pdf-yol').value = v.gecici_pdf_yolu || ''; // YENİ EKLENDİ
                    if(document.getElementById('t-kurum')) document.getElementById('t-kurum').value = v.kurum || '';
                    
                    // YENİ EKLENEN KISIM: Eğer program hiçbir veri bulamadıysa kullanıcıyı uyarır
                    if (!v.sayi && !v.konu && !v.tarih) {
                        bildirimGoster("⚠️ Belge hafızaya alındı ancak içindeki metinler okunamadı (Taranmış/Resim tabanlı PDF olabilir). Lütfen bilgileri elle giriniz.", "hata");
                    } else {
                        bildirimGoster("PDF Başarıyla Okundu", "bilgi");
                        // PDF'in Konusunu okuyup yapay zeka motorunu tetiklediğimiz an!
                        otomatikPersonelSec(v.konu);
                    }
                } else {
                    bildirimGoster("Hata: " + v.mesaj, "hata");
                }
                if(event && event.target) event.target.value = '';
            }).catch(() => { yuklemeGizle(); bildirimGoster("Bağlantı hatası!", "hata"); });
        }
        // --- KLAVYE NAVİGASYONU (Öğrenci Listesi İçin) ---
        document.addEventListener('keydown', function(e) {
            if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'SELECT' || document.activeElement.tagName === 'TEXTAREA') return;
            if (document.querySelector('.modal-overlay[style*="display: flex"]')) return;
            
            const izinSekmesi = document.getElementById('sekme_izin');
            if (!izinSekmesi || !izinSekmesi.classList.contains('aktif')) return;

            const govde = document.getElementById('tree_govde');
            if (!govde) return;

            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                const satirlar = Array.from(govde.querySelectorAll('tr'));
                if (satirlar.length === 0) return;

                const secili = govde.querySelector('tr.tr-secili');
                let hedefIndex = 0;

                if (secili) {
                    const currentIndex = satirlar.indexOf(secili);
                    if (e.key === 'ArrowDown') {
                        hedefIndex = currentIndex < satirlar.length - 1 ? currentIndex + 1 : currentIndex;
                    } else if (e.key === 'ArrowUp') {
                        hedefIndex = currentIndex > 0 ? currentIndex - 1 : 0;
                    }
                }

                const hedefSatir = satirlar[hedefIndex];
                if (hedefSatir && hedefSatir !== secili) {
                    hedefSatir.click();
                    hedefSatir.scrollIntoView({ block: 'center', behavior: 'auto' });
                }
            }
        });

window.verileriYukle = verileriYukle;


// GERİ BİLDİRİM GÖNDERİMİ
function geriBildirimGonder() {
    const isim = document.getElementById('gb_isim').value.trim();
    const eposta = document.getElementById('gb_eposta').value.trim();
    const tur = document.getElementById('gb_tur').value;
    const mesaj = document.getElementById('gb_mesaj').value.trim();

    if (!mesaj) {
        return bildirimGoster("Lütfen mesaj içeriğini doldurunuz!", "hata");
    }

    const buton = document.getElementById("gb_gonder_btn");
    const eskiMetin = buton.innerHTML;
    buton.innerHTML = '<i data-lucide="loader" class="spin"></i> Gönderiliyor...';
    buton.disabled = true;

    fetch(`${API}/geri-bildirim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isim, eposta, tur, mesaj })
    })
    .then(r => r.json())
    .then(v => {
        buton.innerHTML = eskiMetin;
        buton.disabled = false;
        
        if(v.basarili) {
            bildirimGoster("Mesajınız başarıyla iletildi. Teşekkür ederiz!", "bilgi");
            document.getElementById('gb_mesaj').value = '';
            
        } else {
            bildirimGoster(v.mesaj || "Gönderim sırasında bir hata oluştu.", "hata");
        }
        lucide.createIcons();
    })
    .catch(err => {
        buton.innerHTML = eskiMetin;
        buton.disabled = false;
        bildirimGoster("Bağlantı hatası: " + err, "hata");
        lucide.createIcons();
    });
}

        function gecKalanBildirimiGoster() {
            apiFetch('/gec-bugun-sayisi').then(data => {
                if(data.basarili && data.sayi > 0) {
                    setTimeout(() => {
                        bildirimGoster(`Bugün ${data.sayi} öğrenci geç yazıldı. Listeyi görmek için <u style="cursor:pointer;" onclick="gecKalanlariIndir()">tıklayın</u>`, 'bilgi');
                    }, 2000);
                }
            }).catch(e => console.error(e));
        }

        // ==========================================
        // YARDIM MODÜLÜ UI FONKSİYONLARI
        // ==========================================
        function yardimIcerikGoster(id, btnElement) {
            const icerikler = document.querySelectorAll('.yardim-icerik');
            icerikler.forEach(el => el.style.display = 'none');
            
            const butonlar = document.querySelectorAll('.yardim-menu-btn');
            butonlar.forEach(btn => btn.classList.remove('active'));
            
            const secilenIcerik = document.getElementById(id);
            if (secilenIcerik) secilenIcerik.style.display = 'block';
            
            if (btnElement) {
                btnElement.classList.add('active');
            }

            if (window.lucide && typeof lucide.createIcons === 'function') {
                lucide.createIcons();
            }
        }
        window.yardimIcerikGoster = yardimIcerikGoster;

        function yardimKonulariFiltrele(kelime) {
            const q = (kelime || '').trim().toLowerCase();
            const butonlar = document.querySelectorAll('#yardim_menu_liste .yardim-menu-btn');
            let gorunenSayisi = 0;

            butonlar.forEach(btn => {
                const metin = (btn.textContent || '').toLowerCase();
                if (!q || metin.includes(q)) {
                    btn.style.display = 'flex';
                    gorunenSayisi++;
                } else {
                    btn.style.display = 'none';
                }
            });

            const emptyMsg = document.getElementById('yardim_arama_sonuc_yok');
            if (emptyMsg) {
                emptyMsg.style.display = (gorunenSayisi === 0 && q) ? 'block' : 'none';
            }
        }
        window.yardimKonulariFiltrele = yardimKonulariFiltrele;

        let sonSistemTeshisVerisi = null;

        async function sistemTeshisVerileriniYukle() {
            try {
                const data = await apiFetch('/sistem-teshis');
                if (!data.basarili) throw new Error(data.mesaj || 'Teşhis verisi alınamadı');

                sonSistemTeshisVerisi = data;
                const vb = data.veritabani || {};
                const sis = data.sistem || {};

                const elOgr = document.getElementById('teshis_ogr_sayisi');
                if (elOgr) elOgr.textContent = (vb.ogrenci_sayisi ?? 0).toLocaleString();

                const elDev = document.getElementById('teshis_dev_sayisi');
                if (elDev) elDev.textContent = (vb.devamsizlik_sayisi ?? 0).toLocaleString();

                const elPer = document.getElementById('teshis_per_sayisi');
                if (elPer) elPer.textContent = (vb.personel_sayisi ?? 0).toLocaleString();

                const elBoyut = document.getElementById('teshis_db_boyut');
                if (elBoyut) elBoyut.textContent = (vb.boyut_kb ?? 0) + ' KB';

                const elMod = document.getElementById('teshis_db_mod');
                if (elMod) elMod.textContent = vb.journal_mode || 'WAL';

                const elButunluk = document.getElementById('teshis_db_butunluk');
                if (elButunluk) elButunluk.textContent = vb.butunluk === 'OK' ? 'Sağlıklı (OK)' : vb.butunluk;

                const elSnapshot = document.getElementById('teshis_snapshot_durum');
                if (elSnapshot) elSnapshot.textContent = vb.snapshot_var ? 'Hazır (Ctrl+Z Aktif)' : 'Beklemede';

                const elOs = document.getElementById('teshis_os_bilgi');
                if (elOs) elOs.textContent = sis.os || 'Windows';

                const elPy = document.getElementById('teshis_py_bilgi');
                if (elPy) elPy.textContent = sis.python_versiyon ? 'Python ' + sis.python_versiyon : 'Python 3.11+';

                const elZaman = document.getElementById('teshis_son_kontrol');
                if (elZaman) elZaman.textContent = sis.zaman || new Date().toLocaleTimeString();

                if (window.lucide && typeof lucide.createIcons === 'function') {
                    lucide.createIcons();
                }
            } catch (e) {
                console.error('Sistem teşhis yükleme hatası:', e);
                bildirimGoster('Sistem teşhis verisi alınamadı: ' + e.message, 'hata');
            }
        }
        window.sistemTeshisVerileriniYukle = sistemTeshisVerileriniYukle;

        async function sistemTeshisRaporuKopyala() {
            if (!sonSistemTeshisVerisi) {
                await sistemTeshisVerileriniYukle();
            }
            const vb = (sonSistemTeshisVerisi && sonSistemTeshisVerisi.veritabani) || {};
            const sis = (sonSistemTeshisVerisi && sonSistemTeshisVerisi.sistem) || {};

            const raporMetni = 
`==============================================
OTO-YOKLAMA V2.0 SİSTEM TANI VE SAĞLIK RAPORU
Tarih: ${sis.zaman || new Date().toLocaleString()}
==============================================
- Yazılım Sürümü : ${sis.versiyon || 'v2.0 MEB Uyumlu'}
- İşletim Sistemi: ${sis.os || 'Bilinmiyor'}
- Python Sürümü  : ${sis.python_versiyon || '3.11+'}
- Motor / Arayüz : FastAPI REST + Edge WebView2 (60 FPS)

[VERİTABANI BİLGİLERİ]
- Veritabanı Yolu : ${vb.yol || 'yoklama_veritabani.db'}
- Dosya Boyutu    : ${vb.boyut_kb || 0} KB
- Journal Modu    : ${vb.journal_mode || 'WAL'}
- Bütünlük Durumu : ${vb.butunluk || 'OK'}
- Snapshot Durumu : ${vb.snapshot_var ? 'Mevcut (Geri Alınabilir)' : 'Yok'}

[KAYIT İSTATİSTİKLERİ]
- Kayıtlı Öğrenci : ${vb.ogrenci_sayisi ?? 0}
- Devamsızlık     : ${vb.devamsizlik_sayisi ?? 0}
- Kayıtlı Personel: ${vb.personel_sayisi ?? 0}
==============================================`;

            try {
                await navigator.clipboard.writeText(raporMetni);
                bildirimGoster('📋 Sistem tanı raporu panoya kopyalandı! Destek mesajınıza yapıştırabilirsiniz.', 'basarili');
            } catch (err) {
                const textarea = document.createElement('textarea');
                textarea.value = raporMetni;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                bildirimGoster('📋 Sistem tanı raporu panoya kopyalandı.', 'basarili');
            }
        }
        window.sistemTeshisRaporuKopyala = sistemTeshisRaporuKopyala;
        window.tumDevamsizliklariSil = tumDevamsizliklariSil;
