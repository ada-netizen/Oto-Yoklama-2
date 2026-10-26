        // --- PERSONEL YÖNETİMİ & İÇE AKTARMA MERKEZİ ---

        function personelYuklemeModaliAc() {

            modalAc('personel_yukleme_modal');

            setTimeout(() => { if (typeof lucide !== 'undefined') lucide.createIcons(); }, 50);

        }

        window.personelYuklemeModaliAc = personelYuklemeModaliAc;



        function personelDosyaSecildi(event, tip) {

            const dosya = event.target.files[0]; if (!dosya) return;

            const formData = new FormData(); formData.append("dosya", dosya);

            if (tip) formData.append("yukleme_tipi", tip);



            let yuklemeMesaji = "Personel listesi işleniyor...";

            if (tip === 'mebbis_gorevlendirme') yuklemeMesaji = "Görevlendirme personel listesi işleniyor...";

            else if (tip === 'veritabani_yedek' || tip === 'sistem_yedek') yuklemeMesaji = "Personel veritabanı tam yedeği (24 alan) geri yükleniyor...";

            yuklemeGoster(yuklemeMesaji);

            fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {

                if (v.basarili && v.job_id) {

                    ilerlemeTakipEt(v.job_id, () => {

                        modalKapat('personel_yukleme_modal');

                        if (window.personelleriYukle) window.personelleriYukle();

                    });

                } else if (v.basarili) {

                    bildirimGoster(v.mesaj || "Personeller başarıyla yüklendi.", "bilgi");

                    modalKapat('personel_yukleme_modal');

                    if (window.personelleriYukle) window.personelleriYukle();

                } else {

                    bildirimGoster(v.mesaj, "hata");

                }

                if (event && event.target) event.target.value = '';

            }).catch(err => { 

                bildirimGoster(err.message || "Bağlantı hatası! Sunucuyu kontrol edin.", "hata"); 

            }).finally(() => yuklemeGizle());

        }

        window.personelDosyaSecildi = personelDosyaSecildi;



        function personelExcelYukle(event) {

            personelDosyaSecildi(event, null);

        }



        async function personelPanoAktar(tip) {

            const textareaId = (tip === 'mebbis_gorevlendirme' || tip === 'gorevlendirme') ? 'personel_gorevlendirme_pano_text' : 'personel_kadrolu_pano_text';

            const el = document.getElementById(textareaId);

            let metin = el ? el.value.trim() : '';



            if (!metin) {

                bildirimGoster("Lütfen yapıştırılmış tablo verisi girin veya 'Panoyu Al' butonuna tıklayın.", "uyari");

                return;

            }



            yuklemeGoster("Pano verisi çözümleniyor...");

            try {

                const resp = await fetch(`${API}/personel-pano-yukle`, {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({ icerik: metin, yukleme_tipi: tip })

                });

                const v = await resp.json();

                if (v.basarili) {

                    bildirimGoster(v.mesaj || "Personeller başarıyla aktarıldı.", "bilgi");

                    if (el) el.value = '';

                    modalKapat('personel_yukleme_modal');

                    if (window.personelleriYukle) window.personelleriYukle();

                } else {

                    bildirimGoster(v.mesaj || "Aktarım başarısız oldu.", "hata");

                }

            } catch (err) {

                bildirimGoster(err.message || "Bağlantı hatası!", "hata");

            } finally {

                yuklemeGizle();

            }

        }

        window.personelPanoAktar = personelPanoAktar;



        async function personelPanodanOtomatikYapistir(tip) {

            const textareaId = (tip === 'mebbis_gorevlendirme' || tip === 'gorevlendirme') ? 'personel_gorevlendirme_pano_text' : 'personel_kadrolu_pano_text';

            const el = document.getElementById(textareaId);

            if (!el) return;

            try {

                if (navigator.clipboard && navigator.clipboard.readText) {

                    const text = await navigator.clipboard.readText();

                    if (text && text.trim()) {

                        el.value = text;

                        bildirimGoster("Panodaki tablo verisi alana yapıştırıldı.", "bilgi");

                        return;

                    }

                }

            } catch (e) {

                console.warn("Clipboard API:", e);

            }

            el.focus();

            bildirimGoster("Lütfen kutuya tıklayıp Ctrl + V ile yapıştırın.", "bilgi");

        }

        window.personelPanodanOtomatikYapistir = personelPanodanOtomatikYapistir;



        function personelSablonIndir(tip) {

            window.location.href = `${API}/personel-sablon-indir/${tip || 'gorevlendirme'}`;

        }

        window.personelSablonIndir = personelSablonIndir;



        function personelYonetimAc() { 

            modalAc('personel_yonetim_modal'); 

        }

        function ogrenciYonetimAc() { modalAc('ogrenci_yonetim_modal'); if(window.verileriYukle) window.verileriYukle(); }



        // --- <i data-lucide="brain" width="16" height="16"></i> GELİŞMİŞ AKILLI EŞLEŞTİRME MOTORU ---

        function akilliEslesmeModalAc() { if(tumPersoneller.length === 0) personelleriYukle().then(() => modalAc('akilli_eslesme_modal')); else modalAc('akilli_eslesme_modal'); }



        // =====================================================================

        // PERSONEL TEBLİĞİ: 2 KATMANLI ÇAPRAZ FİLTRE & HEDEF KİTLE MİMARİSİ

        // =====================================================================

        let seciliTebligRolu = 'TUMU';      // 'TUMU', 'OGRETMEN', 'IDARECI', 'MEMUR', 'DESTEK'

        let seciliTebligBransi = '';        // '' = Tüm Branşlar, veya 'Tarih', 'Matematik' vb.

        window.seciliTebligRolu = seciliTebligRolu;

        window.seciliTebligBransi = seciliTebligBransi;

        window.sonTebligGosterilenler = [];



        function trNormalize(str) {

            if (!str) return '';

            return String(str)

                .replace(/İ/g, 'I').replace(/ı/g, 'I').replace(/i/g, 'I')

                .replace(/Ğ/g, 'G').replace(/ğ/g, 'G')

                .replace(/Ü/g, 'U').replace(/ü/g, 'U')

                .replace(/Ş/g, 'S').replace(/ş/g, 'S')

                .replace(/Ö/g, 'O').replace(/ö/g, 'O')

                .replace(/Ç/g, 'C').replace(/ç/g, 'C')

                .toUpperCase()

                .trim();

        }

        window.trNormalize = trNormalize;



        function getGorevKademesi(p) {

            if (!p) return 3;

            const gorevStr = ((p.gorev || '') + ' ' + (p.unvan || '')).toLocaleUpperCase('tr-TR').trim();

            // 1. Kademe: Okul Müdürü / Kurum Müdürü (Yardımcı veya Başyardımcı değilse)

            if (gorevStr.includes('MÜDÜR') && 

                !gorevStr.includes('YARDIMCI') && 

                !gorevStr.includes('BAŞYARDIMCI') && 

                !gorevStr.includes('YRD')) {

                return 1;

            }

            // 2. Kademe: Müdür Yardımcısı / Müdür Başyardımcısı

            if (gorevStr.includes('MÜDÜR') && 

                (gorevStr.includes('YARDIMCI') || gorevStr.includes('BAŞYARDIMCI') || gorevStr.includes('YRD'))) {

                return 2;

            }

            // 3. Kademe: Öğretmen, Memur, Destek ve Diğer Personeller

            return 3;

        }

        window.getGorevKademesi = getGorevKademesi;



        function personelRolunuTespitEt(p) {

            if (!p) return 'DIGER';

            const u = trNormalize(p.unvan);

            const g = trNormalize(p.gorev);

            const grp = trNormalize(p.grup);

            const b = (p.brans || '').trim();



            // 1. İdareciler (Müdür, Müdür Başyardımcısı, Müdür Yardımcısı vb.)

            if (g.includes('MUDUR') || u.includes('MUDUR')) {

                return 'IDARECI';

            }



            // 2. Destek / İşçi Personeli (TYP, İUP, Sürekli İşçi, Hizmetli, Güvenlik vb.)

            const destekGruplar = ['TYP', 'IUP', 'ISCI', 'HIZMET ALIMI'];

            const destekKelimeler = ['TEMIZLIK', 'HIZMETLI', 'GUVENLIK', 'BAHCE', 'ASCI', 'SOFOR', 'TEKNISYEN', 'ISCI', 'TYP', 'IUP'];

            if (destekGruplar.some(k => grp.includes(k)) || 

                destekKelimeler.some(k => g.includes(k)) || 

                destekKelimeler.some(k => u.includes(k))) {

                return 'DESTEK';

            }



            // 3. Memurlar / Büro Personeli (Memur, VHKİ, Veri Hazırlama, Şef, Sayman vb.)

            const memurKelimeler = ['MEMUR', 'V.H.K.I', 'VHKI', 'VERI HAZIRLAMA', 'SEF', 'SAYMAN', 'BURO', 'MUTEMET', 'BILGISAYAR ISLETMENI'];

            if (memurKelimeler.some(k => g.includes(k)) || memurKelimeler.some(k => u.includes(k))) {

                return 'MEMUR';

            }



            // 4. Öğretmenler (Kadrolu, Sözleşmeli, Ücretli, Görevlendirme fark etmeksizin)

            if (g.includes('OGRETMEN') || u.includes('OGRETMEN') || 

                (b && b !== '-' && b !== 'NaN') || 

                grp === 'OGRETMENLER' || grp === 'UCRETLI') {

                return 'OGRETMEN';

            }



            if (b && b !== '-' && b !== 'NaN') return 'OGRETMEN';

            return 'DIGER';

        }

        window.personelRolunuTespitEt = personelRolunuTespitEt;



        function tebligRolPresetleriGuncelle() {

            const persList = window.tumPersoneller || tumPersoneller || [];

            const aktifler = persList.filter(p => p.aktif === 1);



            const sayilar = {

                'TUMU': aktifler.length,

                'OGRETMEN': 0,

                'IDARECI': 0,

                'MEMUR': 0,

                'DESTEK': 0

            };



            aktifler.forEach(p => {

                const rol = personelRolunuTespitEt(p);

                if (sayilar[rol] !== undefined) {

                    sayilar[rol]++;

                }

            });



            const butonTanimlari = [

                { id: 'btn_rol_tumu', metin: '👥 Tümü', sayi: sayilar['TUMU'] },

                { id: 'btn_rol_ogretmen', metin: '🎓 Öğretmenler', sayi: sayilar['OGRETMEN'] },

                { id: 'btn_rol_idareci', metin: '🏛️ İdareciler', sayi: sayilar['IDARECI'] },

                { id: 'btn_rol_memur', metin: '📑 Memurlar', sayi: sayilar['MEMUR'] },

                { id: 'btn_rol_destek', metin: '🧹 Destek / İşçi', sayi: sayilar['DESTEK'] }

            ];



            butonTanimlari.forEach(item => {

                const btn = document.getElementById(item.id);

                if (btn) {

                    btn.innerHTML = `${item.metin} (${item.sayi})`;

                    // Eğer o grupta sistemde 0 insan varsa filtrelerde gizlenir, sayı > 0 ise görünür

                    btn.style.display = (item.sayi > 0 || item.id === 'btn_rol_tumu') ? 'inline-flex' : 'none';

                }

            });

        }

        window.tebligRolPresetleriGuncelle = tebligRolPresetleriGuncelle;



        function tebligBransListesiniGuncelle() {

            const sel = document.getElementById('teblig_brans_filtre');

            if (!sel) return;



            const bransSayilari = {};

            const persList = window.tumPersoneller || tumPersoneller || [];

            persList.forEach(p => {

                const b = (p.brans || '').trim();

                if (b && b !== '-' && b !== 'NaN') {

                    bransSayilari[b] = (bransSayilari[b] || 0) + 1;

                }

            });



            const siraliBranslar = Object.keys(bransSayilari).sort((a, b) => a.localeCompare(b, 'tr-TR'));

            const mevcutSecim = sel.value;

            let html = '<option value="">Tüm Branşlar</option>';

            siraliBranslar.forEach(b => {

                const secili = (b === mevcutSecim) ? 'selected' : '';

                html += `<option value="${b.replace(/"/g, '&quot;')}" ${secili}>${b} (${bransSayilari[b]})</option>`;

            });

            sel.innerHTML = html;

        }

        window.tebligBransListesiniGuncelle = tebligBransListesiniGuncelle;



        function tebligBransFiltrele(bransDegeri) {

            seciliTebligBransi = bransDegeri || '';

            window.seciliTebligBransi = seciliTebligBransi;

            personelTablosunuDoldur();

        }

        window.tebligBransFiltrele = tebligBransFiltrele;



        function tebligRolSec(rolKodu) {

            seciliTebligRolu = rolKodu || 'TUMU';

            window.seciliTebligRolu = seciliTebligRolu;



            // Buton UI aktifliği güncelle

            document.querySelectorAll('.teblig-preset-btn').forEach(btn => btn.classList.remove('active'));

            const btnId = {

                'TUMU': 'btn_rol_tumu',

                'OGRETMEN': 'btn_rol_ogretmen',

                'IDARECI': 'btn_rol_idareci',

                'MEMUR': 'btn_rol_memur',

                'DESTEK': 'btn_rol_destek'

            }[seciliTebligRolu];

            const btn = document.getElementById(btnId);

            if (btn) btn.classList.add('active');



            // Branşlar SADECE öğretmenler seçildiğinde görünür olur

            const bransKapsayici = document.getElementById('teblig_brans_kapsayici');

            if (bransKapsayici) {

                if (seciliTebligRolu === 'OGRETMEN') {

                    bransKapsayici.style.display = 'flex';

                } else {

                    bransKapsayici.style.display = 'none';

                    seciliTebligBransi = '';

                    window.seciliTebligBransi = '';

                    const bransSel = document.getElementById('teblig_brans_filtre');

                    if (bransSel) bransSel.value = '';

                }

            }



            // Hızlı Seçim Davranışı:

            // Hedef kitle butonuna basıldığında o role ait AKTİF personelleri otomatik seç

            const persList = window.tumPersoneller || tumPersoneller || [];

            let secilenSayi = 0;

            if (rolKodu === 'TUMU') {

                // Tümü tıklandığında filtre sıfırlanır, mevcut seçimler korunur

            } else {

                persList.forEach(p => {

                    const rol = personelRolunuTespitEt(p);

                    if (rol === rolKodu && p.aktif === 1) {

                        p.secili = true;

                        p.manuelEklendi = true;

                        secilenSayi++;

                    } else if (p.secili && !p.manuelEklendi) {

                        p.secili = false;

                    }

                });

                const rolBasliklari = {

                    'OGRETMEN': 'Öğretmen',

                    'IDARECI': 'İdareci',

                    'MEMUR': 'Memur',

                    'DESTEK': 'Destek/İşçi Personeli'

                };

                if (typeof bildirimGoster === 'function' && secilenSayi > 0) {

                    bildirimGoster(`${secilenSayi} ${rolBasliklari[rolKodu] || 'personel'} seçildi.`, "bilgi");

                }

            }



            personelTablosunuDoldur();

        }

        window.tebligRolSec = tebligRolSec;



        function dinamikTebligFiltreleriOlustur() {

            const kapsayici = document.getElementById('dinamik_teblig_filtreleri');

            if (!kapsayici) return;

            const gruplar = (window.tumPersonelGruplari && window.tumPersonelGruplari.length > 0) 

                ? window.tumPersonelGruplari 

                : ((typeof tumPersonelGruplari !== 'undefined' && tumPersonelGruplari.length > 0) ? tumPersonelGruplari : (window.STANDART_8_GRUP || ['Kadrolu', 'Görevlendirme', 'Ücretli', 'Sözleşmeli', 'Sürekli İşçi', 'TYP', 'İUP', 'Hizmet Alımı']));



            const persList = window.tumPersoneller || tumPersoneller || [];

            const aktifler = persList.filter(p => p.aktif === 1);



            // Her grup için aktif personel sayısını hesapla

            const grupSayilari = {};

            gruplar.forEach(g => { grupSayilari[g] = 0; });

            aktifler.forEach(p => {

                if (p.grup) {

                    grupSayilari[p.grup] = (grupSayilari[p.grup] || 0) + 1;

                }

            });

            

            let html = `<label class="chip-checkbox-wrapper" title="Tüm grupları filtrele"><input type="checkbox" id="grp_tumu" class="chip-checkbox" onchange="filtreTumuDegisti()"><span class="chip-label">Tümü (${aktifler.length})</span></label>`;

            gruplar.forEach(grup => {

                const sayi = grupSayilari[grup] || 0;

                // Eğer o grupta sistemde 0 insan varsa personel tebliği sayfasında filtrelerde gizlensin

                if (sayi > 0) {

                    let sid = grup.replace(/[^a-zA-Z0-9]/g, '_');

                    html += `<label class="chip-checkbox-wrapper"><input type="checkbox" id="grp_${sid}" class="chip-checkbox dinamik-grp-checkbox" data-grup="${grup}" onchange="filtreleriHesapla()"><span class="chip-label">${grup} (${sayi})</span></label>`;

                }

            });

            kapsayici.innerHTML = html;



            // Rol buton sayılarını da eşzamanlı güncelle

            tebligRolPresetleriGuncelle();

        }

        window.dinamikTebligFiltreleriOlustur = dinamikTebligFiltreleriOlustur;



        function filtreTumuDegisti() {

            const tumu = document.getElementById('grp_tumu') ? document.getElementById('grp_tumu').checked : false;

            const checkboxes = document.querySelectorAll('.dinamik-grp-checkbox');

            checkboxes.forEach(cb => cb.checked = tumu);

            personelTablosunuDoldur();

        }

        window.filtreTumuDegisti = filtreTumuDegisti;



        function filtreleriHesapla() {

            const checkboxes = document.querySelectorAll('.dinamik-grp-checkbox');

            let allChecked = checkboxes.length > 0;

            checkboxes.forEach(cb => {

                if (!cb.checked) allChecked = false;

            });

            const grpTumu = document.getElementById('grp_tumu');

            if (grpTumu) grpTumu.checked = allChecked;



            personelTablosunuDoldur();

        }

        window.filtreleriHesapla = filtreleriHesapla;



        function personelTumunuTemizle() {

            seciliTebligRolu = 'TUMU';

            seciliTebligBransi = '';

            window.seciliTebligRolu = 'TUMU';

            window.seciliTebligBransi = '';



            // 1. Rol butonlarını sıfırla

            document.querySelectorAll('.teblig-preset-btn').forEach(btn => btn.classList.remove('active'));

            const btnTumu = document.getElementById('btn_rol_tumu');

            if (btnTumu) btnTumu.classList.add('active');



            // Branş kapsayıcısını gizle

            const bransKapsayici = document.getElementById('teblig_brans_kapsayici');

            if (bransKapsayici) bransKapsayici.style.display = 'none';



            // 2. Statü çipleri sıfırla

            document.querySelectorAll('.dinamik-grp-checkbox').forEach(cb => cb.checked = false);

            const grpTumu = document.getElementById('grp_tumu');

            if (grpTumu) grpTumu.checked = false;



            // 3. Branş seçimi sıfırla

            const bransSel = document.getElementById('teblig_brans_filtre');

            if (bransSel) bransSel.value = '';



            // 4. Arama kutusu sıfırla

            const araKutu = document.getElementById('personel_ara');

            if (araKutu) araKutu.value = '';



            // 5. Seçimleri sıfırla

            const persList = window.tumPersoneller || tumPersoneller || [];

            persList.forEach(p => {

                p.secili = false;

                p.manuelEklendi = false;

            });



            personelTablosunuDoldur();

            if (typeof bildirimGoster === 'function') {

                bildirimGoster("Tüm filtreler ve seçimler temizlendi.", "bilgi");

            }

        }

        window.personelTumunuTemizle = personelTumunuTemizle;



        function personelDurumDegistir(cbElement) {

            const persList = window.tumPersoneller || tumPersoneller || [];

            let p = persList.find(x => x.ad === cbElement.value);

            if(p) {

                p.secili = cbElement.checked;

                p.manuelEklendi = cbElement.checked;

            }

            personelTablosunuDoldur(); 

        }

        window.personelDurumDegistir = personelDurumDegistir;



        function personelMasterSecim(durum) {

            const gosterilenler = window.sonTebligGosterilenler || [];

            gosterilenler.forEach(p => {

                if(p) {

                    if (durum && p.aktif === 0) {

                        p.secili = false;

                    } else {

                        p.secili = durum;

                        p.manuelEklendi = durum;

                    }

                }

            });

            personelTablosunuDoldur();

        }

        window.personelMasterSecim = personelMasterSecim;



        function personelSayaciGuncelle() {
            const gosterilenler = window.sonTebligGosterilenler || [];
            const ekrandakiSecili = gosterilenler.filter(p => p.secili).length;
            const toplamEkrandaki = gosterilenler.length;
            const lbl = document.getElementById('lbl_secili_personel_sayisi');
            if(lbl) { 
                lbl.innerText = `Seçili: ${ekrandakiSecili} / ${toplamEkrandaki} Kişi`; 
                lbl.style.color = ekrandakiSecili > 0 ? '#10B981' : '#EF4444'; 
            }
            const masterKutu = document.getElementById('chk_master_personel');
            if(masterKutu) {
                if (toplamEkrandaki === 0) {
                    masterKutu.checked = false;
                    masterKutu.indeterminate = false;
                } else if (ekrandakiSecili === toplamEkrandaki) {
                    masterKutu.checked = true;
                    masterKutu.indeterminate = false;
                } else if (ekrandakiSecili > 0) {
                    masterKutu.checked = false;
                    masterKutu.indeterminate = true;
                } else {
                    masterKutu.checked = false;
                    masterKutu.indeterminate = false;
                }
            }
        }

        window.personelSayaciGuncelle = personelSayaciGuncelle;



        // --- 2. GÖREV VE BRANŞ İÇİN "ARAMA İÇİNDE FİLTRE" VE SÜTUN SIRALAMA MANTIĞI ---

        let personelSiralamaSutun = 'ad';

        let personelSiralamaYon = 1;



        function personelSirala(sutun) {

            if (personelSiralamaSutun === sutun) {

                personelSiralamaYon *= -1;

            } else {

                personelSiralamaSutun = sutun;

                personelSiralamaYon = 1;

            }

            const basliklar = {

                ad: 'Ad Soyad',

                gorev: 'Görev',

                brans: 'Branş',

                grup: 'Personel Grubu'

            };

            Object.keys(basliklar).forEach(key => {

                const el = document.getElementById(`span_teblig_${key}`);

                if (el) {

                    el.innerText = basliklar[key] + (personelSiralamaSutun === key ? (personelSiralamaYon === 1 ? ' ▲' : ' ▼') : ' ↕');

                }

            });

            personelTablosunuDoldur();

        }

        window.personelSirala = personelSirala;



        function personelTablosunuDoldur() {

            const govde = document.getElementById('personel-govde');

            if(!govde) return;

            const araKutu = document.getElementById('personel_ara');

            const arama = araKutu ? trNormalize(araKutu.value) : "";



            const persList = window.tumPersoneller || tumPersoneller || [];



            // Statü filtreleri

            const seciliStatuler = Array.from(document.querySelectorAll('.dinamik-grp-checkbox:checked')).map(cb => cb.getAttribute('data-grup'));

            const statuFiltresiAktif = seciliStatuler.length > 0;



            const gosterilecekler = persList.filter(p => {

                // Pasif veya başka kuruma görevlendirilmiş personeller:

                // Sadece açıkça aranmışsa veya zaten seçiliyse gösterilir.

                if (p.aktif !== 1 && !p.secili && arama === "") return false;



                // 1. Rol Uygunluğu (TUMU değilse)

                if (seciliTebligRolu && seciliTebligRolu !== 'TUMU') {

                    const rol = personelRolunuTespitEt(p);

                    if (rol !== seciliTebligRolu) return false;

                }



                // 2. Statü Uygunluğu (En az bir statü işaretlendiyse)

                if (statuFiltresiAktif) {

                    if (!seciliStatuler.includes(p.grup)) return false;

                }



                // 3. Branş Uygunluğu (Branş seçildiyse)

                if (seciliTebligBransi && seciliTebligBransi !== '') {

                    const pBrans = (p.brans || '').trim();

                    if (pBrans !== seciliTebligBransi) return false;

                }



                // 4. Metin Arama Uygunluğu (Arama kutusu doluysa)

                if (arama !== "") {

                    const adNorm = trNormalize(p.ad);

                    const gorevNorm = trNormalize(p.gorev);

                    const unvanNorm = trNormalize(p.unvan);

                    const bransNorm = trNormalize(p.brans);

                    const grupNorm = trNormalize(p.grup);

                    const eslesti = adNorm.includes(arama) || 

                                   gorevNorm.includes(arama) || 

                                   unvanNorm.includes(arama) || 

                                   bransNorm.includes(arama) || 

                                   grupNorm.includes(arama);

                    if (!eslesti) return false;

                }



                return true;

            });



            window.sonTebligGosterilenler = gosterilecekler;



            // Sütun başlığına göre sıralama (İdarecileri en üstte tutan kurumsal hiyerarşi)

            gosterilecekler.sort((a, b) => {

                if (personelSiralamaSutun === 'ad' || personelSiralamaSutun === 'gorev') {

                    const kademeA = getGorevKademesi(a);

                    const kademeB = getGorevKademesi(b);

                    if (kademeA !== kademeB) {

                        return (kademeA - kademeB) * (personelSiralamaYon === 1 ? 1 : -1);

                    }

                    let valA = (a[personelSiralamaSutun] || '').toString();

                    let valB = (b[personelSiralamaSutun] || '').toString();

                    return valA.localeCompare(valB, 'tr-TR', { sensitivity: 'base' }) * personelSiralamaYon;

                } else {

                    let valA = (a[personelSiralamaSutun] || '').toString();

                    let valB = (b[personelSiralamaSutun] || '').toString();

                    return valA.localeCompare(valB, 'tr-TR', { sensitivity: 'base' }) * personelSiralamaYon;

                }

            });



            govde.innerHTML = "";

            if(gosterilecekler.length === 0) {

                govde.innerHTML = "<tr><td colspan='5' style='text-align:center; padding:25px; color:var(--fg-sub); font-size:12px;'>Filtreye uyan personel bulunamadı.<br>Filtreleri gevşetin veya personeli aramak için arama kutusunu kullanın.</td></tr>";

                const masterKutu = document.getElementById('chk_master_personel');

                if(masterKutu) masterKutu.checked = false;

            } else {

                let ekrandakiSeciliSayisi = 0;

                gosterilecekler.forEach((p, i) => {

                    if(p.secili) ekrandakiSeciliSayisi++;

                    const brans = (!p.brans || p.brans.trim() === '' || p.brans === 'NaN') ? '-' : p.brans;

                    const gorev = (!p.gorev || p.gorev.trim() === '' || p.gorev === 'NaN') ? '-' : p.gorev;

                    

                    let adEk = '';

                    if (p.aktif !== 1) {

                        const d = (typeof window.getPersonelDurumBilgisi === 'function') ? window.getPersonelDurumBilgisi(p.aktif) : null;

                        if (d) {

                            adEk = ` <span style="font-size:10px; color:${d.renk}; font-weight:700;">(${d.kisaEtiket})</span>`;

                        }

                    }



                    const grupBadge = (typeof window.getPersonelGrupBadgeHtml === 'function') 

                        ? window.getPersonelGrupBadgeHtml(p.grup) 

                        : p.grup;



                    govde.innerHTML += `<tr style="border-bottom: 1px solid var(--border);">

                        <td><label for="chk_${i}" style="cursor:pointer; display:block; font-weight:500;">${p.ad}${adEk}</label></td>

                        <td>${gorev}</td>

                        <td>${brans}</td>

                        <td>${grupBadge}</td>

                        <td style="text-align: center;"><input type="checkbox" class="chk-personel" id="chk_${i}" value="${p.ad}" onchange="personelDurumDegistir(this)" ${p.secili ? 'checked' : ''}></td>

                    </tr>`;

                });

                const masterKutu = document.getElementById('chk_master_personel');

                if(masterKutu) masterKutu.checked = (gosterilecekler.length > 0 && gosterilecekler.length === ekrandakiSeciliSayisi);

            }

            personelSayaciGuncelle();

        }

        window.personelTablosunuDoldur = personelTablosunuDoldur;



        function otomatikPersonelSec(konuMetni) {

            if(!sistemAyarlari.oto_eslesmeler || sistemAyarlari.oto_eslesmeler.length === 0 || !konuMetni) return;

            let secilenAdlar = [];

            let metinKucuk = konuMetni.toLocaleLowerCase('tr-TR');

            

            sistemAyarlari.oto_eslesmeler.forEach(kural => {

                if(metinKucuk.includes(kural.kelime.toLocaleLowerCase('tr-TR'))) {

                    let kTur = kural.tur || 'kisi';

                    let kHedef = kural.hedef || kural.personel;

                    

                    tumPersoneller.forEach(p => {

                        let eslesti = false;

                        if(kTur === 'kisi' && p.ad === kHedef) eslesti = true;

                        else if(kTur === 'grup' && p.grup === kHedef) eslesti = true;

                        else if(kTur === 'gorev' && p.gorev === kHedef) eslesti = true;

                        else if(kTur === 'brans' && p.brans === kHedef) eslesti = true;

                        

                        if(eslesti && !p.secili) {

                            p.secili = true;

                            p.manuelEklendi = true;

                            if(!secilenAdlar.includes(p.ad)) secilenAdlar.push(p.ad);

                        }

                    });

                }

            });

            

            if(secilenAdlar.length > 0) {

                personelTablosunuDoldur();

                bildirimGoster(`<i data-lucide="brain" width="16" height="16"></i> Akıllı Eşleşme Çalıştı!\n${secilenAdlar.length} personel (Grup/Branş) otomatik seçildi.`, "bilgi");

            }

        }



        // --- PDF OKUMA MOTORUNUN GÜNCELLENMİŞ HALİ ---

        

        let aktifPersonelFiltresi = 'Tümü';

        let tumPersonelGruplari = [];



        const STANDART_8_GRUP = ['Kadrolu', 'Görevlendirme', 'Ücretli', 'Sözleşmeli', 'Sürekli İşçi', 'TYP', 'İUP', 'Hizmet Alımı'];

        window.STANDART_8_GRUP = STANDART_8_GRUP;



        function ayarlariGetirPersonelGruplariIcin() {

            fetch(`${API}/ayarlar-getir`).then(r => r.json()).then(v => {

                let ayar = v.ayarlar || {};

                let gruplar = ayar.personel_gruplari;

                if (!gruplar || gruplar.length <= 3) {

                    gruplar = STANDART_8_GRUP;

                }

                window.tumPersonelGruplari = gruplar;

                personelGruplariCiz();

            });

        }



        function personelGruplariCiz() {

            tumPersonelGruplari = window.tumPersonelGruplari || tumPersonelGruplari;

            window.dispatchEvent(new CustomEvent('personeller-guncellendi'));

            dinamikTebligFiltreleriOlustur();

            if (typeof tebligBransListesiniGuncelle === 'function') tebligBransListesiniGuncelle();

            if (typeof lucide !== 'undefined') {

                setTimeout(() => lucide.createIcons(), 50);

            }

        }



        function personelGrupYonetimiAc() {

            modalAc('personel_grup_yonetim_modal');

        }



        function personelGrubuKaydet() {

            return fetch(`${API}/ayarlar-getir`).then(r => r.json()).then(v => {

                let ayar = v.ayarlar || {};

                ayar.personel_gruplari = window.tumPersonelGruplari || [];

                return fetch(`${API}/ayarlar-kaydet`, {

                    method: 'POST', headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify(ayar)

                });

            });

        }



        function yonetimPersonelTablosunuDoldur() { }



        function personelPdfIndir() {

            apiFetch('/personel-pdf-indir').then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));

        }



        function personelExcelMenuToggle(e) {

            if (e) e.stopPropagation();

            const menu = document.getElementById('personel_excel_secenek_menusu');

            if (!menu) return;

            const acik = menu.style.display === 'block';

            menu.style.display = acik ? 'none' : 'block';

            if (!acik && typeof lucide !== 'undefined') {

                lucide.createIcons();

            }

        }

        window.personelExcelMenuToggle = personelExcelMenuToggle;



        function personelExcelIndirSecim(format) {

            const menu = document.getElementById('personel_excel_secenek_menusu');

            if (menu) menu.style.display = 'none';

            personelExcelIndir(format);

        }

        window.personelExcelIndirSecim = personelExcelIndirSecim;



        function personelExcelIndir(format = 'ozet') {

            const yuklemeMesaji = format === 'tam' ? "Veritabanı tam yedeği hazırlanıyor..." : "Personel listesi hazırlanıyor...";

            yuklemeGoster(yuklemeMesaji);

            apiFetch(`/personel-excel-indir?format=${format}`)

                .then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"))

                .catch(err => bildirimGoster("Hata: " + (err.message || err), "hata"))

                .finally(() => yuklemeGizle());

        }

        window.personelExcelIndir = personelExcelIndir;



        document.addEventListener('click', function(e) {

            const menu = document.getElementById('personel_excel_secenek_menusu');

            const btn = document.getElementById('btn_personel_excel_menu');

            if (menu && menu.style.display === 'block') {

                if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {

                    menu.style.display = 'none';

                }

            }

        });



        

        function esikRaporuAl(format) {

            apiFetch(`/rapor-esik-siniflar/${format}`).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));

        }



        // --- RAPORLAR ---

        function raporAl(tur, format, ozelDeger) {

            if((tur === 'gun_siniri' || tur === 'sube_bazli' || tur === 'tarih_bazli') && !ozelDeger) {

                return bildirimGoster("Lütfen rapor almadan önce bir seçim yapınız!", "hata");

            }

            if (tur === 'tarih_tur_bazli') {

                if (!ozelDeger || !ozelDeger.tarih) {

                    return bildirimGoster("Lütfen rapor için bir tarih seçiniz!", "uyari");

                }

            }



            let payload = { tur, format };

            if (tur === 'tarih_tur_bazli') {

                payload.tarih = ozelDeger.tarih;

                payload.devamsizlik_turu = ozelDeger.tur || 'TÜMÜ';

                payload.ozel_deger = `${ozelDeger.tarih}|${payload.devamsizlik_turu}`;

            } else {

                payload.ozel_deger = typeof ozelDeger === 'string' ? ozelDeger : (ozelDeger ? JSON.stringify(ozelDeger) : null);

            }



            apiFetch('/rapor-al', { method: 'POST', body: payload })

                .then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));

        }



        // --- AYARLAR, LOGO VE YEDEKLEME ---

        function logoYukle(tur, event) {

            const dosya = event.target.files[0]; if (!dosya) return;

            const formData = new FormData(); formData.append("tur", tur); formData.append("dosya", dosya);

            apiFetch('/logo-yukle', { method: 'POST', body: formData }).then(v => {

                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");

                if(v.basarili) {

                    const etiket = tur === 'meb' ? 'ayar_meb_logo_ad' : 'ayar_okul_logo_ad';

                    document.getElementById(etiket).innerText = dosya.name;

                }

                if(event && event.target) event.target.value = '';

            });

        }



        function yedekleriListele() {

            apiFetch('/yedekler-listele').then(v => {

                const kutu = document.getElementById('ayar_yedek_secim'); if(!kutu) return;

                if(!v.yedekler || v.yedekler.length === 0) { kutu.innerHTML = '<option value="">Yedek dosyası bulunamadı</option>'; return; }

                kutu.innerHTML = v.yedekler.map(y => `<option value="${y.dosya_adi}">${y.tarih} (${y.boyut_kb} KB)</option>`).join('');

            });

        }



        async function yedekGeriYukle() {

            const secim = document.getElementById('ayar_yedek_secim').value;

            if(!secim) return bildirimGoster("Lütfen bir yedek dosyası seçin.", "hata");

            const onay = await modernOnayGoster("Yedekten Geri Yükle", "Mevcut veriler silinecek ve seçilen yedekteki veriler yüklenecektir.\n\nBu işlemi onaylıyor musunuz?", "uyari");

            if(!onay) return;

            apiFetch('/yedek-geri-yukle', { method: 'POST', body: { dosya: secim } })

                .then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); if(v.basarili) location.reload(); });

        }



        function ayarlariYukle() {

            apiFetch('/ayarlar-getir').then(v => {

                sistemAyarlari = v.ayarlar;

                window.sistemAyarlari = v.ayarlar;

                if(document.getElementById('ayar_pdf_yol')) document.getElementById('ayar_pdf_yol').value = v.ayarlar.pdf_kayit_klasoru || v.yollar.PDF;

                if(document.getElementById('ayar_yedek_yol')) document.getElementById('ayar_yedek_yol').value = v.ayarlar.yedek_kayit_klasoru || v.yollar.YEDEK;

                if(document.getElementById('ayar-pdf')) document.getElementById('ayar-pdf').value = v.ayarlar.pdf_kayit_klasoru || v.yollar.PDF;

                if(document.getElementById('ayar-yedek')) document.getElementById('ayar-yedek').value = v.ayarlar.yedek_kayit_klasoru || v.yollar.YEDEK;

                if(document.getElementById('ayar_okul_adi')) document.getElementById('ayar_okul_adi').value = v.ayarlar.okul_adi || '';

                if(document.getElementById('ayar_yedek_silme')) document.getElementById('ayar_yedek_silme').value = v.ayarlar.yedek_silme_suresi || '1 Ay Sonra';

                if(document.getElementById('ayar_yedek_saati')) document.getElementById('ayar_yedek_saati').value = v.ayarlar.yedek_saati || '17:00';

                if(document.getElementById('ayar_yedek_sikligi')) document.getElementById('ayar_yedek_sikligi').value = v.ayarlar.yedek_sikligi || 'Her Gün';

                if(document.getElementById('ayar_yedek_gun_sayisi')) document.getElementById('ayar_yedek_gun_sayisi').value = v.ayarlar.yedek_gun_sayisi || 3;

                if(document.getElementById('ayar_yedek_gun_sayisi_satir')) document.getElementById('ayar_yedek_gun_sayisi_satir').style.display = (v.ayarlar.yedek_sikligi === 'Özel Gün') ? 'flex' : 'none';

                if(document.getElementById('ayar_meb_logo_ad')) document.getElementById('ayar_meb_logo_ad').innerText = v.ayarlar.meb_logosu ? v.ayarlar.meb_logosu.split(/[\\/]/).pop() : 'Yüklenmedi';

                if(document.getElementById('ayar_okul_logo_ad')) document.getElementById('ayar_okul_logo_ad').innerText = v.ayarlar.okul_logosu ? v.ayarlar.okul_logosu.split(/[\\/]/).pop() : 'Yüklenmedi';

                yedekleriListele();



                // İlk kullanım karşılama mesajı ve MEB logosu uyarısı

                if (v.ayarlar.ilk_kullanim !== false) {

                    bildirimGoster("Sisteme Hoş Geldiniz! Önce Ayarlar menüsünden PDF kayıt yerini seçiniz.", "bilgi");

                    apiFetch('/ayarlar-kaydet', { method: 'POST', body: { ilk_kullanim: false } });

                } else if (!v.ayarlar.meb_logosu) {

                apiFetch('/versiyon').then(versiyonData => {

                    const GUNCEL = versiyonData.versiyon;

                    if (v.ayarlar.son_gorulen_versiyon !== GUNCEL) {

                        setTimeout(() => {

                            if(window.yeniliklerModalAc) window.yeniliklerModalAc();

                            apiFetch('/ayarlar-kaydet', { 

                                method: 'POST', 

                                body: { son_gorulen_versiyon: GUNCEL } 

                            });

                        }, 1500);

                    }

                }).catch(err => console.error('Versiyon alinamadi', err));

                    setTimeout(() => bildirimGoster("MEB Logosu bulunamadı! Ayarlar'dan yükleyin.", "hata"), 3000);

                }

            });

        }



        function ayarlariKaydet() {

            let pdfYol = document.getElementById('ayar_pdf_yol') ? document.getElementById('ayar_pdf_yol').value : (document.getElementById('ayar-pdf') ? document.getElementById('ayar-pdf').value : "");

            let yedekYol = document.getElementById('ayar_yedek_yol') ? document.getElementById('ayar_yedek_yol').value : (document.getElementById('ayar-yedek') ? document.getElementById('ayar-yedek').value : "");

            

            sistemAyarlari.pdf_kayit_klasoru = pdfYol;

            sistemAyarlari.yedek_kayit_klasoru = yedekYol;

            if(document.getElementById('ayar_okul_adi')) sistemAyarlari.okul_adi = document.getElementById('ayar_okul_adi').value;

            if(document.getElementById('ayar_yedek_silme')) sistemAyarlari.yedek_silme_suresi = document.getElementById('ayar_yedek_silme').value;

            if(document.getElementById('ayar_yedek_saati')) sistemAyarlari.yedek_saati = document.getElementById('ayar_yedek_saati').value;

            if(document.getElementById('ayar_yedek_sikligi')) sistemAyarlari.yedek_sikligi = document.getElementById('ayar_yedek_sikligi').value;

            if(document.getElementById('ayar_yedek_gun_sayisi')) sistemAyarlari.yedek_gun_sayisi = document.getElementById('ayar_yedek_gun_sayisi').value;

            apiFetch('/ayarlar-kaydet', { method: 'POST', body: sistemAyarlari }).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); modalKapat('ayarlar_modal'); });

        }



        function sistemYedekle() { apiFetch('/yedek-al', { method: 'POST' }).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); yedekleriListele(); }); }



        function loglariGoster() {

            apiFetch('/loglar').then(v => {

                const govde = document.getElementById('ayar_log_govde');

                if(!govde) return;

                govde.style.display = 'block';

                govde.textContent = v.loglar.length ? v.loglar.map(l => `[${l.zaman}] ${l.seviye.toLocaleUpperCase('tr-TR')} | ${l.islem}: ${l.mesaj}`).join('\n') : 'Henüz işlem kaydı yok.';

            }).catch(() => bildirimGoster('Loglar okunamadı.', 'hata'));

        }



        async function sonIslemiGeriAl() {

            const onay = await modernOnayGoster("Son İşlemi Geri Al", "Son güvenli yedeğe dönülecektir. Mevcut durum önce ayrıca yedeklenecektir. Devam edilsin mi?", "soru");

            if(!onay) return;

            apiFetch('/son-islemi-geri-al', { method: 'POST' }).then(v => {

                bildirimGoster(v.mesaj, v.basarili ? 'bilgi' : 'hata');

                if(v.basarili) location.reload();

            }).catch(() => bildirimGoster('Geri alma işlemi başarısız.', 'hata'));

        }

        

        async function veritabaniniSifirla() {

            const onay = await modernOnayGoster("Tüm Veritabanını Sıfırla", "DİKKAT: Tüm öğrenciler, devamsızlıklar ve personeller kalıcı olarak SİLİNECEKTİR.\n\nBu işlem geri alınamaz! Onaylıyor musunuz?", "uyari");

            if(onay) {

                apiFetch('/veritabani-sifirla', { method: 'DELETE' }).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });

            }

        }



        async function ogrencileriSifirla() {

            const onay = await modernOnayGoster("Öğrenci Verilerini Sıfırla", "Tüm öğrenci ve devamsızlık kayıtları SİLİNECEK.\nPersonel verilerine dokunulmayacaktır.\n\nOnaylıyor musunuz?", "uyari");

            if(onay) {

                apiFetch('/ogrencileri-sifirla', { method: 'DELETE' }).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });

            }

        }



        async function personelSifirla() {

            const onay = await modernOnayGoster("Personel Verilerini Sıfırla", "Tüm personel kayıtları SİLİNECEK.\nÖğrenci verilerine dokunulmayacaktır.\n\nOnaylıyor musunuz?", "uyari");

            if(onay) {

                apiFetch('/personel-sifirla', { method: 'DELETE' }).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });

            }

        }





        



        // --- AÇILIŞ (SPLASH) EKRANI ---

        function splashKapat() {

            const splash = document.getElementById('splash_overlay');

            if(splash) { splash.classList.add('gizli'); setTimeout(() => splash.style.display = 'none', 450); }

        }



        function gecKalanlariIndir() {

            apiFetch('/rapor-gec-bugun')

                .then(sonuc => {

                    if(!sonuc.basarili) {

                        bildirimGoster(sonuc.mesaj, "hata");

                    } else {

                        bildirimGoster(sonuc.mesaj, "bilgi");

                    }

                }).catch(e => bildirimGoster("Hata: " + e, "hata"));

        }



        window.onload = function() {

            verileriYukle();

            ayarlariYukle();

            

            gecKalanBildirimiGoster();

            ayarlariGetirPersonelGruplariIcin();

            resizerAktifEt('resizer1', 'sol_panel_ana', 'sag_panel_ana');

            resizerAktifEt('resizer2', 'takvim_alani_ana', 'onizleme_alani_ana');

            tabloSutunBoyutlandirma();

            setTimeout(splashKapat, 1500);

            

            

            

            if (typeof lucide !== 'undefined') {

                lucide.createIcons();

            }

        };



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

window.tebligModuDegistir = tebligModuDegistir;



// =====================================================================

// DİNAMİK STATÜ VE MEVZUAT YÖNETİMİ

// =====================================================================

function ppFormuStatuyaGoreAyarla() {

    const elGrup = document.getElementById('pp_grup');

    const elUnvan = document.getElementById('pp_unvan');

    const elGorev = document.getElementById('pp_gorev');

    

    const grup = elGrup ? elGrup.value.trim() : 'Kadrolu';

    const unvan = elUnvan ? elUnvan.value.trim().toUpperCase() : '';

    const gorev = elGorev ? elGorev.value.trim().toUpperCase() : '';



    const nonOgretmenGruplar = ['Sürekli İşçi', 'TYP', 'İUP', 'Hizmet Alımı'];

    const memurIsciKelimeler = [

        'MEMUR', 'VHKİ', 'V.H.K.İ', 'VERİ HAZIRLAMA', 'HİZMETLİ', 'HIZMETLI',

        'TEKNİSYEN', 'TEKNIKER', 'ŞEF', 'SEF', 'İŞÇİ', 'ISCI', 'SÜREKLİ İŞÇİ',

        'GÜVENLİK', 'BEKÇİ', 'AŞÇI', 'ASCI', 'ŞOFÖR', 'SOFOR', 'KALORİFERCİ', 'TYP', 'İUP', 'IUP'

    ];

    const ogretmenKelimeler = ['ÖĞRETMEN', 'OGRETMEN', 'MÜDÜR', 'MUDUR', 'UZMAN ÖĞRETMEN', 'BAŞÖĞRETMEN'];



    let isOgretmen = false;

    if (nonOgretmenGruplar.includes(grup)) {

        isOgretmen = false;

    } else if (memurIsciKelimeler.some(k => unvan.includes(k) || gorev.includes(k))) {

        isOgretmen = false;

    } else if (ogretmenKelimeler.some(k => unvan.includes(k) || gorev.includes(k))) {

        isOgretmen = true;

    } else if (['Kadrolu', 'Görevlendirme', 'Sözleşmeli', 'Ücretli'].includes(grup)) {

        isOgretmen = true;

    }



    const elBransKap = document.getElementById('pp_brans_kapsayici');

    const elKariyerKap = document.getElementById('pp_kariyer_kapsayici');

    const elKademeKap = document.getElementById('pp_kademe_derece_kapsayici');

    const elEmekliKap = document.getElementById('pp_emekli_sicil_kapsayici');

    const elKurumSicilKap = document.getElementById('pp_kurum_sicil_kapsayici');

    const elArsivNoKap = document.getElementById('pp_arsiv_no_kapsayici');

    const elGoreveBaslamaKap = document.getElementById('pp_goreve_baslama_kapsayici');

    const elOlaganTerfiKap = document.getElementById('pp_olagan_terfi_kapsayici');



    // 1. Branş Alanı (Yalnızca öğretmenlerde gösterilir)

    if (elBransKap) {

        elBransKap.style.display = isOgretmen ? '' : 'none';

        if (!isOgretmen) {

            const elBrans = document.getElementById('pp_brans');

            if (elBrans && !elBrans.value) elBrans.value = '-';

        }

    }



    // 2. Kariyer Basamağı (Yalnızca kadrolu/sözleşmeli öğretmenlerde gösterilir, İUP/TYP/İşçi/Memur/Ücretli de asla görünmez)

    if (elKariyerKap) {

        const kariyerGoster = isOgretmen && grup !== 'Ücretli';

        elKariyerKap.style.display = kariyerGoster ? '' : 'none';

        if (!kariyerGoster) {

            const elKariyer = document.getElementById('pp_kariyer');

            if (elKariyer && !elKariyer.value) elKariyer.value = '-';

        }

    }



    // 3. Durumu / Kademe - Derece (Memur ve kadrolu öğretmenlerde gösterilir; İUP, TYP, İşçi, Ücretli de asla görünmez)

    if (elKademeKap) {

        const kademeGoster = ['Kadrolu', 'Görevlendirme', 'Sözleşmeli'].includes(grup) && (grup !== 'Ücretli');

        elKademeKap.style.display = kademeGoster ? '' : 'none';

        if (!kademeGoster) {

            const elKademe = document.getElementById('pp_kademe_derece');

            if (elKademe && !elKademe.value) elKademe.value = '-';

        }

    }



    // 4. Emekli Sicil No (İUP, TYP, Sürekli İşçi, Hizmet Alımı için gerekmez)

    if (elEmekliKap) {

        const emekliGoster = !['TYP', 'İUP', 'Hizmet Alımı', 'Sürekli İşçi'].includes(grup);

        elEmekliKap.style.display = emekliGoster ? '' : 'none';

    }



    // 5. Kurum / SGK Sicil No (İUP ve TYP için gerekmez; İşçi, Memur, Öğretmen için uygundur)

    if (elKurumSicilKap) {

        const kurumSicilGoster = !['TYP', 'İUP', 'Hizmet Alımı'].includes(grup);

        elKurumSicilKap.style.display = kurumSicilGoster ? '' : 'none';

    }



    // 6. Arşiv No (İUP, TYP, Hizmet Alımı için gerekmez)

    if (elArsivNoKap) {

        const arsivGoster = !['TYP', 'İUP', 'Hizmet Alımı', 'Sürekli İşçi'].includes(grup);

        elArsivNoKap.style.display = arsivGoster ? '' : 'none';

    }



    // 7. İlk Göreve Başlama Tarihi (İUP ve TYP için tek bir başlama tarihi yeterlidir)

    if (elGoreveBaslamaKap) {

        const ilkGorevGoster = !['TYP', 'İUP', 'Hizmet Alımı'].includes(grup);

        elGoreveBaslamaKap.style.display = ilkGorevGoster ? '' : 'none';

    }



    // 8. Olağan Terfi Tarihi (İUP, TYP, Hizmet Alımı, Ücretli için terfi söz konusu değildir)

    if (elOlaganTerfiKap) {

        const terfiGoster = !['TYP', 'İUP', 'Hizmet Alımı', 'Ücretli'].includes(grup);

        elOlaganTerfiKap.style.display = terfiGoster ? '' : 'none';

    }



    ppMevzuatKartiniGuncelle(grup, isOgretmen);

}

window.ppFormuStatuyaGoreAyarla = ppFormuStatuyaGoreAyarla;



function ppMevzuatKartiniGuncelle(grup, isOgretmen) {

    const elKanun = document.getElementById('pp_mevzuat_kanun_badge');

    const elStatu = document.getElementById('pp_mevzuat_statu_baslik');

    const elCalisma = document.getElementById('pp_mevzuat_calisma_badge');

    const elIzin = document.getElementById('pp_mevzuat_izin_metni');

    const elYaptirim = document.getElementById('pp_mevzuat_yaptirim_span');

    const elKutu = document.getElementById('pp_mevzuat_bilgi_kutusu');



    if (!elKutu) return;



    if (grup === 'İUP') {

        elKutu.style.borderColor = 'rgba(239, 68, 68, 0.4)';

        elKutu.style.background = 'rgba(239, 68, 68, 0.06)';

        if (elKanun) { elKanun.innerText = 'İŞKUR İUP'; elKanun.style.background = '#dc2626'; }

        if (elStatu) elStatu.innerText = 'İşgücü Uyum Programı (Yarı Zamanlı Katılımcı)';

        if (elCalisma) { elCalisma.innerText = 'Haftada 3 Gün (22.5 Saat)'; elCalisma.style.color = '#dc2626'; elCalisma.style.borderColor = 'rgba(239, 68, 68, 0.3)'; }

        if (elIzin) elIzin.innerText = '6 aya kadar azami 7 gün, 6 aydan uzun programda azami 10 gün izin verilebilir. İzin/rapor günlerinde harçlık ödenmez. Branş, kariyer ve derece-kademe sorulmaz.';

        if (elYaptirim) elYaptirim.innerText = 'ÖNEMLİ: Mazeretsiz veya belgesiz 1 GÜN BİLE devamsızlıkta İLİŞİK DERHAL KESİLİR (Genelge Md. 23/2).';

    } else if (grup === 'TYP') {

        elKutu.style.borderColor = 'rgba(245, 158, 11, 0.4)';

        elKutu.style.background = 'rgba(245, 158, 11, 0.06)';

        if (elKanun) { elKanun.innerText = 'İŞKUR TYP'; elKanun.style.background = '#d97706'; }

        if (elStatu) elStatu.innerText = 'Toplum Yararına Program (Asgari Ücretli Katılımcı)';

        if (elCalisma) { elCalisma.innerText = 'Tam Zamanlı (Azami 9 Ay)'; elCalisma.style.color = '#d97706'; elCalisma.style.borderColor = 'rgba(245, 158, 11, 0.3)'; }

        if (elIzin) elIzin.innerText = 'Hafta tatili hariç azami 5 güne kadar ücretsiz mazeret izni kullanılabilir. Branş, kariyer ve kademe sorulmaz.';

        if (elYaptirim) elYaptirim.innerText = 'ÖNEMLİ: 5 günlük mazeret izni süresinin aşılması durumunda programla İLİŞİK DERHAL KESİLİR (Yönetmelik Md. 11/4).';

    } else if (grup === 'Sürekli İşçi') {

        elKutu.style.borderColor = 'rgba(59, 130, 246, 0.4)';

        elKutu.style.background = 'rgba(59, 130, 246, 0.06)';

        if (elKanun) { elKanun.innerText = '4857 Sayılı İş Kanunu (4/D)'; elKanun.style.background = '#2563eb'; }

        if (elStatu) elStatu.innerText = 'Kamu Sürekli İşçisi (Temizlik, Güvenlik, Bakım vb.)';

        if (elCalisma) { elCalisma.innerText = 'Haftalık 45 Saat'; elCalisma.style.color = '#2563eb'; elCalisma.style.borderColor = 'rgba(59, 130, 246, 0.3)'; }

        if (elIzin) elIzin.innerText = 'Yıllık ücretli izin (Md. 53): 1-5 yıl: 14 gün, 5-15 yıl: 20 gün, 15+ yıl: 26 gün. Evlilik 3, vefat 3, babalık 5 gün. Branş ve kariyer sorulmaz.';

        if (elYaptirim) elYaptirim.innerText = 'Mazeretsiz ardı ardına 2 işgünü veya ayda 3 işgünü devamsızlık işverene Haklı Fesih hakkı tanır (Md. 25/II-g).';

    } else if (grup === 'Ücretli') {

        elKutu.style.borderColor = 'rgba(139, 92, 246, 0.4)';

        elKutu.style.background = 'rgba(139, 92, 246, 0.06)';

        if (elKanun) { elKanun.innerText = '657 DMK Md. 89'; elKanun.style.background = '#7c3aed'; }

        if (elStatu) elStatu.innerText = 'Ek Ders Karşılığı Ücretli Öğretmen';

        if (elCalisma) { elCalisma.innerText = 'Ders Saati Bazlı'; elCalisma.style.color = '#7c3aed'; elCalisma.style.borderColor = 'rgba(139, 92, 246, 0.3)'; }

        if (elIzin) elIzin.innerText = 'Yıllık izin hakkı yoktur; girilmeyen derslerde ücret ve sigorta kesilir. Branş geçerlidir, kariyer basamağı uygulanmaz.';

        if (elYaptirim) elYaptirim.innerText = 'Derse mazeretsiz gelinmediğinde ek ders tahakkuk ettirilmez.';

    } else if (!isOgretmen) {

        elKutu.style.borderColor = 'rgba(100, 116, 139, 0.4)';

        elKutu.style.background = 'rgba(100, 116, 139, 0.06)';

        if (elKanun) { elKanun.innerText = '657 Sayılı DMK'; elKanun.style.background = '#475569'; }

        if (elStatu) elStatu.innerText = 'Genel İdare / Yardımcı Hizmetler (Memur, VHKİ, Hizmetli)';

        if (elCalisma) { elCalisma.innerText = 'Haftalık 40 Saat'; elCalisma.style.color = '#475569'; elCalisma.style.borderColor = 'rgba(100, 116, 139, 0.3)'; }

        if (elIzin) elIzin.innerText = 'Yıllık İzin (Md. 102): 1-10 yıl 20 gün, 10+ yıl 30 gün. Kademe-derece esastır. Branş ve kariyer basamağı sorulmaz.';

        if (elYaptirim) elYaptirim.innerText = 'Özürsüz 1-2 gün aylıktan kesme, 3-9 gün kademe durdurma, kesintisiz 10 gün çekilmiş sayılma (Md. 94/125).';

    } else {

        elKutu.style.borderColor = 'rgba(2, 132, 199, 0.4)';

        elKutu.style.background = 'rgba(2, 132, 199, 0.06)';

        if (elKanun) { elKanun.innerText = '657 Sayılı DMK'; elKanun.style.background = '#0284c7'; }

        if (elStatu) elStatu.innerText = 'Eğitim-Öğretim Hizmetleri Sınıfı (Öğretmen / İdareci)';

        if (elCalisma) { elCalisma.innerText = 'Tam Zamanlı'; elCalisma.style.color = '#0284c7'; elCalisma.style.borderColor = 'rgba(2, 132, 199, 0.3)'; }

        if (elIzin) elIzin.innerText = 'Yaz ve dinlenme tatillerinde izinli sayılır (Md. 103). Branş (Atama Alanı) ve Kariyer Basamağı geçerlidir.';

        if (elYaptirim) elYaptirim.innerText = 'Özürsüz 1-2 gün aylıktan kesme, 3-9 gün kademe durdurma, kesintisiz 10 gün çekilmiş sayılma (Md. 94/125).';

    }

}



function ppGrupDegisti(grup) {

    ppFormuStatuyaGoreAyarla();

}

window.ppGrupDegisti = ppGrupDegisti;



function ppUnvanGorevDegisti() {

    ppFormuStatuyaGoreAyarla();

}

window.ppUnvanGorevDegisti = ppUnvanGorevDegisti;



function ppStatuSecildi(statuKodu, varsayilanUnvan) {

    const elGrup = document.getElementById('pp_grup');

    if (elGrup) elGrup.value = statuKodu;



    const elUnvan = document.getElementById('pp_unvan');

    if (elUnvan) elUnvan.value = varsayilanUnvan || '';



    const elGorev = document.getElementById('pp_gorev');

    if (elGorev && !elGorev.value) {

        if (statuKodu === 'İUP') elGorev.value = 'Temizlik ve Bakım';

        else if (statuKodu === 'TYP') elGorev.value = 'Temizlik Hizmetleri';

        else if (statuKodu === 'Sürekli İşçi') elGorev.value = 'Destek Hizmetleri';

        else if (statuKodu === 'Kadrolu' && varsayilanUnvan === 'Memur') elGorev.value = 'Yazı İşleri / Büro';

        else if (varsayilanUnvan && varsayilanUnvan.includes('Öğretmen')) elGorev.value = 'Öğretmen';

    }



    // Adım 1'i gizle, Adım 2 formunu aç

    const elSecim = document.getElementById('pp_adim_statu_secimi');

    const elForm = document.getElementById('pp_adim_form_alani');

    const elBtnGeri = document.getElementById('pp_btn_tur_degistir');



    if (elSecim) elSecim.style.display = 'none';

    if (elForm) elForm.style.display = 'flex';

    if (elBtnGeri) elBtnGeri.style.display = 'inline-flex';



    const elBaslik = document.getElementById('pp_modal_ana_baslik');

    if (elBaslik) elBaslik.innerText = `Yeni ${statuKodu} Personeli Ekle`;



    ppFormuStatuyaGoreAyarla();



    setTimeout(() => {

        const elAd = document.getElementById('pp_ad_soyad');

        if (elAd) elAd.focus();

        if (typeof lucide !== 'undefined') lucide.createIcons();

    }, 80);

}

window.ppStatuSecildi = ppStatuSecildi;



function ppStatuSecimineGeriDon() {

    const elSecim = document.getElementById('pp_adim_statu_secimi');

    const elForm = document.getElementById('pp_adim_form_alani');

    const elBtnGeri = document.getElementById('pp_btn_tur_degistir');



    if (elForm) elForm.style.display = 'none';

    if (elSecim) elSecim.style.display = 'block';

    if (elBtnGeri) elBtnGeri.style.display = 'none';



    const elBaslik = document.getElementById('pp_modal_ana_baslik');

    if (elBaslik) elBaslik.innerText = 'Yeni Personel Ekle - İstihdam Türü Seçimi';



    if (typeof lucide !== 'undefined') {

        setTimeout(() => lucide.createIcons(), 30);

    }

}

window.ppStatuSecimineGeriDon = ppStatuSecimineGeriDon;



function personelProfilAc(personelVerisi) {

    let p = personelVerisi;

    if (typeof p === 'string' || typeof p === 'number') {

        p = (window.tumPersoneller || []).find(x => x.id === p || x.ad === p || x.ad_soyad === p) || { ad: String(p), ad_soyad: String(p) };

    }

    if (!p) return;

    const setVal = (id, val) => {

        const el = document.getElementById(id);

        if (el) el.value = (val !== null && val !== undefined) ? val : '';

    };

    const setText = (id, val) => {

        const el = document.getElementById(id);

        if (el) el.innerText = val || '-';

    };



    // Mevcut personel profilinde doğrudan form alanı açılır

    const elSecim = document.getElementById('pp_adim_statu_secimi');

    const elForm = document.getElementById('pp_adim_form_alani');

    const elBtnGeri = document.getElementById('pp_btn_tur_degistir');



    if (elSecim) elSecim.style.display = 'none';

    if (elForm) elForm.style.display = 'flex';

    if (elBtnGeri) elBtnGeri.style.display = 'none';



    setText('pp_modal_ana_baslik', 'Personel Profil Bilgileri');

    setText('pp_ad_soyad_baslik', p.ad);

    setText('pp_avatar', p.ad ? p.ad.substring(0, 2).toUpperCase() : 'P');

    setText('pp_tc_badge', p.tc_no ? `TC: ${p.tc_no}` : 'TC: Belirtilmemiş');

    setText('pp_cinsiyet_badge', p.cinsiyet === 'E' ? 'Erkek' : (p.cinsiyet === 'K' ? 'Kadın' : 'Cinsiyet: -'));

    setText('pp_kan_badge', p.kan_grubu ? `Kan: ${p.kan_grubu}` : 'Kan Grubu: -');

    setText('pp_unvan_gorev_ozet', `${p.unvan || '-'} / ${p.gorev || '-'} (${p.brans || '-'})`);

    setText('pp_kurum_ozet', `${p.kurum_adi || 'Kurum Belirtilmemiş'} ${p.kurum_kodu ? `(${p.kurum_kodu})` : ''}`);



    const valAktif = (p.aktif !== undefined && p.aktif !== null) ? parseInt(p.aktif) : 1;

    const elAktifDurum = document.getElementById('pp_aktif_durum');

    if (elAktifDurum) {

        elAktifDurum.value = String(valAktif);

        ppAktifDurumDegisti(String(valAktif));

    }

    const isPasif = (valAktif === 0);

    const elPasif = document.getElementById('pp_gorevlendirildi_pasif');

    if (elPasif) elPasif.checked = isPasif;

    const elDurumBadge = document.getElementById('pp_durum_badge');

    if (elDurumBadge) elDurumBadge.style.display = (valAktif !== 1) ? 'inline-block' : 'none';



    setVal('pp_id', p.id);

    setVal('pp_ad_soyad', p.ad);

    setVal('pp_unvan', p.unvan);

    setVal('pp_gorev', p.gorev);

    setVal('pp_brans', p.brans);

    setVal('pp_kariyer', p.kariyer);

    setVal('pp_kademe_derece', p.kademe_derece);

    setVal('pp_ogrenim_durumu', p.ogrenim_durumu);

    setVal('pp_il_ilce', p.il_ilce);

    setVal('pp_kurum_adi', p.kurum_adi);

    setVal('pp_kurum_kodu', p.kurum_kodu);

    setVal('pp_kurumda_baslama', p.kurumda_baslama);

    setVal('pp_goreve_baslama', p.goreve_baslama);

    setVal('pp_olagan_terfi_tarihi', p.olagan_terfi_tarihi);

    setVal('pp_kurum_sicil_no', p.kurum_sicil_no);

    setVal('pp_emekli_sicil_no', p.emekli_sicil_no);

    setVal('pp_arsiv_no', p.arsiv_no);

    setVal('pp_tc_no', p.tc_no);

    setVal('pp_dogum_tarihi', p.dogum_tarihi);

    setVal('pp_cinsiyet', p.cinsiyet);

    setVal('pp_kan_grubu', p.kan_grubu);

    setVal('pp_telefon', p.telefon);

    setVal('pp_eposta', p.eposta);

    setVal('pp_notlar', p.notlar);



    const elGrup = document.getElementById('pp_grup');

    if (elGrup) elGrup.value = p.grup || 'Kadrolu';



    const elBtnSil = document.getElementById('pp_btn_sil');

    if (elBtnSil) elBtnSil.style.display = 'inline-flex';



    ppFormuStatuyaGoreAyarla();



    modalAc('personel_profil_modal');

    if (typeof lucide !== 'undefined') {

        setTimeout(() => lucide.createIcons(), 50);

    }

}

window.personelProfilAc = personelProfilAc;

window.personelProfilModalAc = personelProfilAc;



// ==============================================================================

// PERSONEL GÖREV VE UZUN SÜRELİ İZİN DURUMLARI REHBERİ (CENTRAL STATUS REGISTRY)

// ==============================================================================

window.PERSONEL_DURUMLARI = {

    1: {

        kod: 1,

        etiket: 'Aktif (Kurumda Görevde)',

        kisaEtiket: 'Aktif',

        renk: '#059669',

        arkaplan: 'rgba(16, 185, 129, 0.12)',

        kenarlik: 'rgba(16, 185, 129, 0.35)',

        ikon: 'check-circle-2',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',

        fiilenGorevde: true,

        yasalDayanak: 'Fiilen Görevde',

        aciklama: 'Kurumda fiilen görev başındadır. İmza sirküsü ve resmi evrak listelerinde varsayılan olarak seçili gelir.'

    },

    0: {

        kod: 0,

        etiket: 'Başka Kuruma Görevlendirildi',

        kisaEtiket: 'Başka Kurumda',

        renk: '#dc2626',

        arkaplan: 'rgba(239, 68, 68, 0.12)',

        kenarlik: 'rgba(239, 68, 68, 0.35)',

        ikon: 'building-2',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M8 10h.01"/><path d="M16 10h.01"/><path d="M8 14h.01"/><path d="M16 14h.01"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Ek Md. 8 / MEB Yön.',

        aciklama: '⚠️ 657 SK Ek Md. 8 uyarınca başka bir kuruma görevlidir; genel imza sirküsü listelerinde varsayılan olarak seçili gelmez.'

    },

    2: {

        kod: 2,

        etiket: 'Uzun Süreli Sağlık İzninde',

        kisaEtiket: 'Sağlık İzninde',

        renk: '#7c3aed',

        arkaplan: 'rgba(124, 58, 237, 0.12)',

        kenarlik: 'rgba(124, 58, 237, 0.35)',

        ikon: 'heart-pulse',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 105',

        aciklama: '🏥 657 SK Md. 105 uyarınca uzun süreli sağlık/heyet raporunda (12 veya 18 aya kadar) olduğu için fiilen görevde sayılmaz.'

    },

    3: {

        kod: 3,

        etiket: 'Doğum / Analık İzninde',

        kisaEtiket: 'Doğum İzninde',

        renk: '#db2777',

        arkaplan: 'rgba(236, 72, 153, 0.12)',

        kenarlik: 'rgba(236, 72, 153, 0.35)',

        ikon: 'baby',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 15h8"/><circle cx="9" cy="9" r="1" fill="currentColor"/><circle cx="15" cy="9" r="1" fill="currentColor"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 104/A',

        aciklama: '🌸 657 SK Md. 104/A uyarınca 16 hafta (çoğul gebelikte 18 hafta) analık izinlidir; fiilen görevde sayılmaz.'

    },

    4: {

        kod: 4,

        etiket: 'Aylıksız İzninde (Doğum / 5 Yıl vb.)',

        kisaEtiket: 'Aylıksız İzninde',

        renk: '#d97706',

        arkaplan: 'rgba(217, 119, 6, 0.12)',

        kenarlik: 'rgba(217, 119, 6, 0.35)',

        ikon: 'clock',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 108',

        aciklama: '⏳ 657 SK Md. 108 uyarınca (doğum sonrası 24 ay veya 5 yıla 1 yıl isteğe bağlı) aylıksız izinlidir; fiilen görevde bulunmaz.'

    },

    5: {

        kod: 5,

        etiket: 'Refakat İzninde',

        kisaEtiket: 'Refakat İzninde',

        renk: '#0891b2',

        arkaplan: 'rgba(8, 145, 178, 0.12)',

        kenarlik: 'rgba(8, 145, 178, 0.35)',

        ikon: 'shield-alert',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M12 7v6"/><path d="M12 17h.01"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 105/Son',

        aciklama: '🩺 657 SK Md. 105 son fıkrası uyarınca hayati tehlikesi/ağır hastalığı bulunan yakını için 3-6 ay refakat izinlidir.'

    },

    6: {

        kod: 6,

        etiket: 'Askerlik Görevinde / İzninde',

        kisaEtiket: 'Askerlikte',

        renk: '#4d7c0f',

        arkaplan: 'rgba(77, 124, 15, 0.12)',

        kenarlik: 'rgba(77, 124, 15, 0.35)',

        ikon: 'shield',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 108/G',

        aciklama: '🎖️ 657 SK Md. 108/G uyarınca muvazzaf veya bedelli askerlik hizmetini ifa etmektedir.'

    },

    7: {

        kod: 7,

        etiket: 'Yurtdışı / Lisansüstü Eğitim İzninde',

        kisaEtiket: 'Yurtdışı/Eğitim',

        renk: '#4f46e5',

        arkaplan: 'rgba(79, 70, 229, 0.12)',

        kenarlik: 'rgba(79, 70, 229, 0.35)',

        ikon: 'globe',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '657 SK Md. 78-79',

        aciklama: '🎓 657 SK Md. 78-79 uyarınca lisansüstü eğitim veya bilgi-görgü artırma amacıyla yurt dışı/eğitim izinlidir.'

    },

    8: {

        kod: 8,

        etiket: 'Sendika Görevinde / İzninde',

        kisaEtiket: 'Sendika İzninde',

        renk: '#c026d3',

        arkaplan: 'rgba(192, 38, 211, 0.12)',

        kenarlik: 'rgba(192, 38, 211, 0.35)',

        ikon: 'landmark',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/></svg>',

        fiilenGorevde: false,

        yasalDayanak: '4688 SK Md. 18',

        aciklama: '🏛️ 4688 SK Md. 18 uyarınca sendika yönetim organlarında görevli olup sendikal izinlidir.'

    }

};



window.getPersonelDurumBilgisi = function(kod) {

    const val = (kod !== undefined && kod !== null) ? parseInt(kod) : 1;

    return window.PERSONEL_DURUMLARI[val] || window.PERSONEL_DURUMLARI[1];

};



// ==============================================================================

// PERSONEL GRUP VE STATÜ ROZETLERİ REHBERİ (CENTRAL GROUP BADGE REGISTRY)

// ==============================================================================

window.PERSONEL_GRUP_ROZETLERI = {

    'Kadrolu': {

        grup: 'Kadrolu',

        renk: '#0284c7',

        arkaplan: 'rgba(2, 132, 199, 0.10)',

        kenarlik: 'rgba(2, 132, 199, 0.28)',

        ikon: 'award',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>'

    },

    'Sözleşmeli': {

        grup: 'Sözleşmeli',

        renk: '#0891b2',

        arkaplan: 'rgba(8, 145, 178, 0.10)',

        kenarlik: 'rgba(8, 145, 178, 0.28)',

        ikon: 'scroll',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1z"/><path d="M4 17a2 2 0 0 1 2-2h12"/></svg>'

    },

    'Ücretli': {

        grup: 'Ücretli',

        renk: '#7c3aed',

        arkaplan: 'rgba(124, 58, 237, 0.10)',

        kenarlik: 'rgba(124, 58, 237, 0.28)',

        ikon: 'clock',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'

    },

    'Görevlendirme': {

        grup: 'Görevlendirme',

        renk: '#d97706',

        arkaplan: 'rgba(217, 119, 6, 0.10)',

        kenarlik: 'rgba(217, 119, 6, 0.28)',

        ikon: 'repeat',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/></svg>'

    },

    'İUP': {

        grup: 'İUP',

        renk: '#059669',

        arkaplan: 'rgba(5, 150, 105, 0.10)',

        kenarlik: 'rgba(5, 150, 105, 0.28)',

        ikon: 'sparkles',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>'

    },

    'TYP': {

        grup: 'TYP',

        renk: '#ea580c',

        arkaplan: 'rgba(234, 88, 12, 0.10)',

        kenarlik: 'rgba(234, 88, 12, 0.28)',

        ikon: 'hard-hat',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z"/><path d="M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5"/><path d="M4 15v-3a8 8 0 0 1 16 0v3"/></svg>'

    },

    'Sürekli İşçi': {

        grup: 'Sürekli İşçi',

        renk: '#2563eb',

        arkaplan: 'rgba(37, 99, 235, 0.10)',

        kenarlik: 'rgba(37, 99, 235, 0.28)',

        ikon: 'wrench',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'

    },

    'Hizmet Alımı': {

        grup: 'Hizmet Alımı',

        renk: '#64748b',

        arkaplan: 'rgba(100, 116, 139, 0.10)',

        kenarlik: 'rgba(100, 116, 139, 0.28)',

        ikon: 'truck',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18.5" r="2.5"/><circle cx="7" cy="18.5" r="2.5"/></svg>'

    }

};



window.getPersonelGrupBadgeHtml = function(grupAdi) {

    const g = (grupAdi || '').trim();

    const config = window.PERSONEL_GRUP_ROZETLERI[g] || {

        grup: g || 'Belirtilmemiş',

        renk: '#64748b',

        arkaplan: 'rgba(100, 116, 139, 0.10)',

        kenarlik: 'rgba(100, 116, 139, 0.25)',

        ikon: 'tag',

        svg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><circle cx="7" cy="7" r=".5" fill="currentColor"/></svg>'

    };



    return `<span style="font-size: 10.5px; padding: 2.5px 8px; background: ${config.arkaplan}; border: 1px solid ${config.kenarlik}; border-radius: 8px; color: ${config.renk}; font-weight: 700; display: inline-flex; align-items: center; gap: 4.5px; white-space: nowrap;">

        ${config.svg}

        <span>${config.grup}</span>

    </span>`;

};



window.getPersonelDurumBadgeHtml = function(kod) {

    const d = window.getPersonelDurumBilgisi(kod);

    if (d.fiilenGorevde) {

        return `<span style="font-size: 10.5px; padding: 2px 8px; background: rgba(22, 163, 74, 0.08); color: #15803d; border: 1px solid rgba(22, 163, 74, 0.22); border-radius: 12px; font-weight: 700; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;" title="${d.yasalDayanak} - ${d.aciklama}">

            <span style="width: 6px; height: 6px; border-radius: 50%; background-color: #16a34a; display: inline-block;"></span>

            <span>Aktif</span>

        </span>`;

    }

    return `<span style="font-size: 10.5px; padding: 2px 8px; background: ${d.arkaplan}; color: ${d.renk}; border: 1px solid ${d.kenarlik}; border-radius: 12px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; white-space: nowrap;" title="${d.yasalDayanak} - ${d.aciklama}">

        ${d.svg}

        <span>${d.kisaEtiket}</span>

    </span>`;

};





function ppAktifDurumDegisti(val) {

    const el = document.getElementById('pp_aktif_durum');

    const elPasif = document.getElementById('pp_gorevlendirildi_pasif');

    const elDurumBadge = document.getElementById('pp_durum_badge');

    const elAciklama = document.getElementById('pp_durum_aciklama');

    const valInt = (val !== undefined && val !== null) ? parseInt(val) : 1;

    const durum = window.getPersonelDurumBilgisi(valInt);

    

    if (elPasif) elPasif.checked = (valInt === 0);

    

    if (el) {

        el.style.borderColor = durum.renk;

        el.style.color = durum.renk;

    }



    if (durum.fiilenGorevde) {

        if (elDurumBadge) elDurumBadge.style.display = 'none';

        if (elAciklama) elAciklama.style.display = 'none';

    } else {

        if (elDurumBadge) {

            elDurumBadge.style.display = 'inline-flex';

            elDurumBadge.style.alignItems = 'center';

            elDurumBadge.style.gap = '4px';

            elDurumBadge.innerHTML = `${durum.svg} <span>${durum.etiket}</span>`;

            elDurumBadge.style.background = durum.arkaplan;

            elDurumBadge.style.color = durum.renk;

            elDurumBadge.style.borderColor = durum.kenarlik;

        }

        if (elAciklama) {

            elAciklama.style.display = 'block';

            elAciklama.style.color = durum.renk;

            elAciklama.innerText = durum.aciklama;

        }

    }

}

window.ppAktifDurumDegisti = ppAktifDurumDegisti;



function ppGorevlendirmeDurumDegisti(checked) {

    const elAktif = document.getElementById('pp_aktif_durum');

    if (elAktif) {

        elAktif.value = checked ? '0' : '1';

        ppAktifDurumDegisti(elAktif.value);

    }

}

window.ppGorevlendirmeDurumDegisti = ppGorevlendirmeDurumDegisti;



function personelYeniEkleModalAc() {

    const setText = (id, val) => {

        const el = document.getElementById(id);

        if (el) el.innerText = val || '';

    };

    const setVal = (id, val) => {

        const el = document.getElementById(id);

        if (el) el.value = val || '';

    };



    setText('pp_modal_ana_baslik', 'Yeni Personel Ekle - İstihdam Türü Seçimi');

    setText('pp_ad_soyad_baslik', 'Yeni Personel Kaydı');

    setText('pp_avatar', '+');

    setText('pp_tc_badge', 'TC: -');

    setText('pp_cinsiyet_badge', 'Cinsiyet: -');

    setText('pp_kan_badge', 'Kan Grubu: -');

    setText('pp_unvan_gorev_ozet', 'Personel Bilgilerini Giriniz');

    setText('pp_kurum_ozet', '');

    

    const elDurumBadge = document.getElementById('pp_durum_badge');

    if (elDurumBadge) elDurumBadge.style.display = 'none';



    setVal('pp_id', '');

    setVal('pp_ad_soyad', '');

    setVal('pp_unvan', '');

    setVal('pp_gorev', '');

    setVal('pp_brans', '');

    setVal('pp_kariyer', '');

    setVal('pp_kademe_derece', '');

    setVal('pp_ogrenim_durumu', '');

    setVal('pp_il_ilce', '');

    setVal('pp_kurum_adi', '');

    setVal('pp_kurum_kodu', '');

    setVal('pp_kurumda_baslama', '');

    setVal('pp_goreve_baslama', '');

    setVal('pp_olagan_terfi_tarihi', '');

    setVal('pp_kurum_sicil_no', '');

    setVal('pp_emekli_sicil_no', '');

    setVal('pp_arsiv_no', '');

    setVal('pp_tc_no', '');

    setVal('pp_dogum_tarihi', '');

    setVal('pp_cinsiyet', '');

    setVal('pp_kan_grubu', '');

    setVal('pp_telefon', '');

    setVal('pp_eposta', '');

    setVal('pp_notlar', '');



    const elGrup = document.getElementById('pp_grup');

    if (elGrup) elGrup.value = 'Kadrolu';

    const elPasif = document.getElementById('pp_gorevlendirildi_pasif');

    if (elPasif) elPasif.checked = false;

    const elAktifDurum = document.getElementById('pp_aktif_durum');

    if (elAktifDurum) {

        elAktifDurum.value = '1';

        if (typeof ppAktifDurumDegisti === 'function') {

            ppAktifDurumDegisti('1');

        }

    }



    const elBtnSil = document.getElementById('pp_btn_sil');

    if (elBtnSil) elBtnSil.style.display = 'none';



    // Adım 1: Tür seçim ekranını aç, Form alanını gizle

    const elSecim = document.getElementById('pp_adim_statu_secimi');

    const elForm = document.getElementById('pp_adim_form_alani');

    const elBtnGeri = document.getElementById('pp_btn_tur_degistir');



    if (elSecim) elSecim.style.display = 'block';

    if (elForm) elForm.style.display = 'none';

    if (elBtnGeri) elBtnGeri.style.display = 'none';



    modalAc('personel_profil_modal');

    if (typeof lucide !== 'undefined') {

        setTimeout(() => lucide.createIcons(), 50);

    }

}

window.personelYeniEkleModalAc = personelYeniEkleModalAc;



function personelProfilKaydet() {

    const getVal = id => {

        const el = document.getElementById(id);

        return el ? el.value.trim() : '';

    };



    const idVal = getVal('pp_id');

    const adSoyadVal = getVal('pp_ad_soyad');

    if (!adSoyadVal) {

        bildirimGoster("Personel Ad Soyad boş bırakılamaz!", "uyari");

        return;

    }



    const elAktifDurum = document.getElementById('pp_aktif_durum');

    const isPasif = document.getElementById('pp_gorevlendirildi_pasif') ? document.getElementById('pp_gorevlendirildi_pasif').checked : false;

    const aktifVal = elAktifDurum ? parseInt(elAktifDurum.value) : (isPasif ? 0 : 1);



    const payload = {

        id: idVal ? parseInt(idVal) : null,

        ad_soyad: adSoyadVal,

        tc_no: getVal('pp_tc_no'),

        unvan: getVal('pp_unvan'),

        gorev: getVal('pp_gorev'),

        brans: getVal('pp_brans') || '-',

        kariyer: getVal('pp_kariyer') || '-',

        kademe_derece: getVal('pp_kademe_derece'),

        ogrenim_durumu: getVal('pp_ogrenim_durumu'),

        il_ilce: getVal('pp_il_ilce'),

        kurum_adi: getVal('pp_kurum_adi'),

        kurum_kodu: getVal('pp_kurum_kodu'),

        kurumda_baslama: getVal('pp_kurumda_baslama'),

        goreve_baslama: getVal('pp_goreve_baslama'),

        olagan_terfi_tarihi: getVal('pp_olagan_terfi_tarihi'),

        kurum_sicil_no: getVal('pp_kurum_sicil_no'),

        emekli_sicil_no: getVal('pp_emekli_sicil_no'),

        arsiv_no: getVal('pp_arsiv_no'),

        dogum_tarihi: getVal('pp_dogum_tarihi'),

        cinsiyet: getVal('pp_cinsiyet'),

        kan_grubu: getVal('pp_kan_grubu'),

        grup: getVal('pp_grup') || 'Kadrolu',

        telefon: getVal('pp_telefon'),

        eposta: getVal('pp_eposta'),

        notlar: getVal('pp_notlar'),

        aktif: isNaN(aktifVal) ? 1 : aktifVal

    };



    yuklemeGoster();

    fetch(`${API}/personel-profil-guncelle`, {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify(payload)

    })

    .then(r => r.json())

    .then(res => {

        if (res.basarili) {

            bildirimGoster(res.mesaj || "Profil bilgileri kaydedildi.", "bilgi");

            modalKapat('personel_profil_modal');

            if (typeof personelleriYukle === 'function') {

                personelleriYukle();

            }

        } else {

            bildirimGoster(res.mesaj || "Kayıt sırasında hata oluştu.", "hata");

        }

    })

    .catch(err => {

        bildirimGoster("Bağlantı hatası: " + err.message, "hata");

    })

    .finally(() => yuklemeGizle());

}

window.personelProfilKaydet = personelProfilKaydet;



async function ppMevcutPersoneliSil() {

    const elAd = document.getElementById('pp_ad_soyad');

    const ad = elAd ? elAd.value.trim() : '';

    if (!ad) {

        if (typeof bildirimGoster === 'function') bildirimGoster("Silinecek personel bulunamadı.", "uyari");

        return;

    }



    let onay = true;

    if (typeof modernOnayGoster === 'function') {

        onay = await modernOnayGoster("Personel Silme Onayı", `"${ad}" adlı personeli silmek istediğinize emin misiniz?`, "uyari");

    } else {

        onay = confirm(`"${ad}" adlı personeli silmek istediğinize emin misiniz?`);

    }

    if (!onay) return;



    if (typeof yuklemeGoster === 'function') yuklemeGoster();

    fetch(`${API}/personel-sil/${encodeURIComponent(ad)}`, {

        method: 'DELETE'

    })

    .then(r => r.json())

    .then(res => {

        if (res.basarili) {

            if (typeof bildirimGoster === 'function') bildirimGoster(res.mesaj || `${ad} silindi.`, "bilgi");

            if (typeof modalKapat === 'function') modalKapat('personel_profil_modal');

            

            if (window.tumPersoneller) {

                window.tumPersoneller = window.tumPersoneller.filter(p => p.ad !== ad);

            }

            if (typeof personelleriYukle === 'function') {

                personelleriYukle();

            }

            window.dispatchEvent(new CustomEvent('personeller-guncellendi'));

        } else {

            if (typeof bildirimGoster === 'function') bildirimGoster(res.mesaj || "Silme işlemi başarısız.", "hata");

        }

    })

    .catch(err => {

        if (typeof bildirimGoster === 'function') bildirimGoster("Bağlantı hatası: " + err.message, "hata");

    })

    .finally(() => {

        if (typeof yuklemeGizle === 'function') yuklemeGizle();

    });

}

window.ppMevcutPersoneliSil = ppMevcutPersoneliSil;



// Personeller güncellendiğinde branş listesini ve tebliğ tablosunu otomatik tazele

window.addEventListener('personeller-guncellendi', () => {

    if (typeof tebligBransListesiniGuncelle === 'function') tebligBransListesiniGuncelle();

    if (typeof dinamikTebligFiltreleriOlustur === 'function') dinamikTebligFiltreleriOlustur();

    if (typeof personelTablosunuDoldur === 'function') personelTablosunuDoldur();

});



// Sayfa yüklendiğinde tebliğ filtrelerini ve branş listesini hazırla

document.addEventListener('DOMContentLoaded', () => {

    setTimeout(() => {

        if (typeof tebligBransListesiniGuncelle === 'function') tebligBransListesiniGuncelle();

        if (typeof dinamikTebligFiltreleriOlustur === 'function') dinamikTebligFiltreleriOlustur();

    }, 100);

});





// ==========================================

// TEBLİĞ GEÇMİŞİ VE ARŞİV YÖNETİMİ

// ==========================================

window.tumTebligatKayitlari = [];

window.aktifTebligTuruFiltresi = 'TÜMÜ';



window.tebligGecmisiModalAc = function() {

    const elModal = document.getElementById('modal_teblig_gecmisi');

    if (!elModal) return;

    elModal.style.display = 'flex';

    

    window.aktifTebligTuruFiltresi = 'TÜMÜ';

    const inpAra = document.getElementById('inp_teblig_gecmis_ara');

    if (inpAra) inpAra.value = '';

    

    // Filtre butonlarını resetle

    ['btn_tg_filtre_tumu', 'btn_tg_filtre_toplu', 'btn_tg_filtre_bireysel'].forEach(id => {

        const btn = document.getElementById(id);

        if (btn) btn.classList.remove('active');

    });

    const btnTumu = document.getElementById('btn_tg_filtre_tumu');

    if (btnTumu) btnTumu.classList.add('active');



    tebligGecmisiYukle();

    if (typeof lucide !== 'undefined' && lucide.createIcons) {

        setTimeout(() => lucide.createIcons(), 50);

    }

};



window.tebligGecmisiModalKapat = function() {

    const elModal = document.getElementById('modal_teblig_gecmisi');

    if (elModal) elModal.style.display = 'none';

};



window.tebligGecmisiFiltrele = function(tur) {

    window.aktifTebligTuruFiltresi = tur;

    

    ['btn_tg_filtre_tumu', 'btn_tg_filtre_toplu', 'btn_tg_filtre_bireysel'].forEach(id => {

        const btn = document.getElementById(id);

        if (btn) btn.classList.remove('active');

    });

    

    if (tur === 'Toplu Tebliğ') {

        const b = document.getElementById('btn_tg_filtre_toplu');

        if (b) b.classList.add('active');

    } else if (tur === 'Bireysel Tebliğ') {

        const b = document.getElementById('btn_tg_filtre_bireysel');

        if (b) b.classList.add('active');

    } else {

        const b = document.getElementById('btn_tg_filtre_tumu');

        if (b) b.classList.add('active');

    }

    

    tebligGecmisiTablosuCiz();

};



window.tebligGecmisiAra = function() {

    tebligGecmisiTablosuCiz();

};



window.tebligGecmisiYukle = async function() {

    const tbody = document.getElementById('tbody_teblig_gecmisi');

    if (tbody) {

        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--fg-sub);">Kayıtlar yükleniyor...</td></tr>';

    }

    

    try {

        const res = await fetch(`${API}/teblig-gecmisi`);

        const data = await res.json();

        if (data.basarili) {

            window.tumTebligatKayitlari = data.veri || [];

            tebligGecmisiTablosuCiz();

        } else {

            if (tbody) {

                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: #EF4444;">Hata: ${data.mesaj || 'Kayıtlar yüklenemedi'}</td></tr>`;

            }

        }

    } catch (e) {

        if (tbody) {

            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: #EF4444;">Bağlantı hatası: ${e.message}</td></tr>`;

        }

    }

};



window.tebligGecmisiTablosuCiz = function() {

    const tbody = document.getElementById('tbody_teblig_gecmisi');

    if (!tbody) return;

    

    const inpAra = document.getElementById('inp_teblig_gecmis_ara');

    const aramaMetni = inpAra ? (inpAra.value || '').trim().toLocaleLowerCase('tr-TR') : '';

    const turFiltresi = window.aktifTebligTuruFiltresi || 'TÜMÜ';

    

    let kayitlar = window.tumTebligatKayitlari || [];

    

    // 1. Tür Filtresi

    if (turFiltresi !== 'TÜMÜ') {

        kayitlar = kayitlar.filter(r => r.teblig_turu === turFiltresi);

    }

    

    // 2. Metin Arama

    if (aramaMetni) {

        kayitlar = kayitlar.filter(r => {

            const kurum = (r.kurum || '').toLocaleLowerCase('tr-TR');

            const sayi = (r.sayi || '').toLocaleLowerCase('tr-TR');

            const tarih = (r.evrak_tarihi || '').toLocaleLowerCase('tr-TR');

            const konu = (r.konu || '').toLocaleLowerCase('tr-TR');

            const tur = (r.teblig_turu || '').toLocaleLowerCase('tr-TR');

            const kisiler = (r.teblig_edilenler || []).map(k => (k.ad || '')).join(' ').toLocaleLowerCase('tr-TR');

            

            return kurum.includes(aramaMetni) || 

                   sayi.includes(aramaMetni) || 

                   tarih.includes(aramaMetni) || 

                   konu.includes(aramaMetni) || 

                   tur.includes(aramaMetni) || 

                   kisiler.includes(aramaMetni);

        });

    }

    

    // Toplam rozetini güncelle

    const lblToplam = document.getElementById('lbl_teblig_toplam_kayit');

    if (lblToplam) {

        lblToplam.textContent = `${kayitlar.length} Kayıt`;

    }

    

    if (kayitlar.length === 0) {

        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 36px; color: var(--fg-sub);">Kriterlere uygun tebliğ kaydı bulunamadı.</td></tr>';

        return;

    }

    

    tbody.innerHTML = '';

    kayitlar.forEach(r => {

        const tr = document.createElement('tr');

        tr.style.borderBottom = '1px solid var(--border)';

        tr.style.transition = 'background-color 0.15s';

        tr.onmouseover = () => tr.style.backgroundColor = 'var(--bg-card-hover)';

        tr.onmouseout = () => tr.style.backgroundColor = 'transparent';

        

        // Tarih formatı

        let tarihMetni = r.olusturma_tarihi || '-';

        if (tarihMetni.length >= 16) {

            const [tPart, sPart] = tarihMetni.split(' ');

            const tParcalar = tPart.split('-');

            if (tParcalar.length === 3) {

                tarihMetni = `${tParcalar[2]}.${tParcalar[1]}.${tParcalar[0]} <span style="color:var(--fg-sub); font-size:11px;">${sPart ? sPart.substring(0, 5) : ''}</span>`;

            }

        }

        

        // Tür Rozeti

        const isToplu = r.teblig_turu === 'Toplu Tebliğ';

        const turBadge = isToplu

            ? `<span class="badge" style="background: rgba(2, 132, 199, 0.15); color: #0284C7; border: 1px solid rgba(2, 132, 199, 0.3); padding: 3px 7px; border-radius: 5px; font-weight: 700; font-size: 11px; white-space: nowrap;">👥 TOPLU</span>`

            : `<span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3); padding: 3px 7px; border-radius: 5px; font-weight: 700; font-size: 11px; white-space: nowrap;">👤 BİREYSEL</span>`;

        

        // Tebliğ Edilenler alanı

        let kisiSayisi = r.kisi_sayisi || (r.teblig_edilenler ? r.teblig_edilenler.length : 0);

        let edilenlerHtml = '';

        if (!isToplu && r.teblig_edilenler && r.teblig_edilenler.length > 0) {

            const ilkKisi = r.teblig_edilenler[0];

            edilenlerHtml = `<div style="font-weight: 600; color: var(--fg-main);">${ilkKisi.ad || '-'}</div>`;

            if (ilkKisi.gorev || ilkKisi.brans) {

                edilenlerHtml += `<div style="font-size: 10.5px; color: var(--fg-sub);">${ilkKisi.gorev || ilkKisi.brans}</div>`;

            }

        } else {

            edilenlerHtml = `

                <div style="display: flex; align-items: center; gap: 6px;">

                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 7px; border-radius: 5px; font-weight: 700; font-size: 11px;">

                        ${kisiSayisi} Personel

                    </span>

                    <button class="btn btn-temizle" style="padding: 2px 6px; font-size: 11px;" onclick="tebligKisileriniGoster(${r.id})" title="Kişi Listesini İncele">

                        <i data-lucide="eye" height="13" width="13"></i>

                    </button>

                </div>

            `;

        }

        

        // Konu metni (uzunsa kısalt)

        const konuMetni = r.konu || '-';

        const kisaKonu = konuMetni.length > 55 ? (konuMetni.substring(0, 52) + '...') : konuMetni;

        

        // Dosya aç butonu

        const dosyaVar = !!r.dosya_yolu;

        const acBtn = dosyaVar 

            ? `<button class="btn btn-icon btn-ayarlar" style="padding: 5px 8px;" onclick="tebligDosyasiAc('${(r.dosya_yolu || '').replace(/\\/g, '/')}')" title="Üretilen PDF Belgesini Aç">

                   <i data-lucide="file-text" height="14" width="14"></i>

               </button>`

            : '';

            

        tr.innerHTML = `

            <td style="padding: 10px 12px; white-space: nowrap;">${tarihMetni}</td>

            <td style="padding: 10px 12px;">${turBadge}</td>

            <td style="padding: 10px 12px; font-weight: 600; color: var(--fg-main); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${r.kurum || ''}">

                ${r.kurum || '-'}

            </td>

            <td style="padding: 10px 12px; font-size: 11.5px; white-space: nowrap;">

                <div style="font-weight: 600; color: var(--fg-main);">${r.sayi || '-'}</div>

                <div style="color: var(--fg-sub); font-size: 10.5px;">${r.evrak_tarihi || '-'}</div>

            </td>

            <td style="padding: 10px 12px; max-width: 220px; line-height: 1.3;" title="${konuMetni}">

                ${kisaKonu}

            </td>

            <td style="padding: 10px 12px;">${edilenlerHtml}</td>

            <td style="padding: 10px 12px; text-align: right;">

                <div style="display: flex; gap: 5px; justify-content: flex-end; align-items: center;">

                    ${acBtn}

                    <button class="btn btn-icon btn-kirmizi" style="padding: 5px 8px;" onclick="tebligKaydiSil(${r.id})" title="Arşiv Kaydını Sil">

                        <i data-lucide="trash-2" height="14" width="14"></i>

                    </button>

                </div>

            </td>

        `;

        tbody.appendChild(tr);

    });

    

    if (typeof lucide !== 'undefined' && lucide.createIcons) {

        lucide.createIcons();

    }

};



window.tebligKisileriniGoster = function(kayitId) {

    const kayit = (window.tumTebligatKayitlari || []).find(k => k.id === kayitId);

    if (!kayit) return;

    

    const elBaslik = document.getElementById('lbl_tk_baslik');

    if (elBaslik) {

        elBaslik.textContent = `${kayit.sayi || 'Tebliğ'} - Tebliğ Edilen Kişiler (${kayit.kisi_sayisi || (kayit.teblig_edilenler ? kayit.teblig_edilenler.length : 0)} Kişi)`;

    }

    

    const divListe = document.getElementById('div_teblig_kisiler_liste');

    if (!divListe) return;

    

    divListe.innerHTML = '';

    const kisiler = kayit.teblig_edilenler || [];

    if (kisiler.length === 0) {

        divListe.innerHTML = '<div style="text-align: center; color: var(--fg-sub); padding: 20px;">Kayıtlı kişi bilgisi bulunamadı.</div>';

    } else {

        kisiler.forEach((p, idx) => {

            const item = document.createElement('div');

            item.style.padding = '8px 12px';

            item.style.borderRadius = '6px';

            item.style.background = 'var(--bg-main)';

            item.style.border = '1px solid var(--border)';

            item.style.display = 'flex';

            item.style.justifyContent = 'space-between';

            item.style.alignItems = 'center';

            

            const ad = typeof p === 'string' ? p : (p.ad || '-');

            const gorev = typeof p === 'object' ? (p.gorev || p.brans || '') : '';

            

            item.innerHTML = `

                <div style="display: flex; align-items: center; gap: 8px;">

                    <span style="font-weight: 700; color: var(--fg-sub); font-size: 11px; width: 22px;">${idx + 1}.</span>

                    <span style="font-weight: 600; color: var(--fg-main); font-size: 12.5px;">${ad}</span>

                </div>

                ${gorev ? `<span class="badge" style="background: var(--bg-card); color: var(--fg-sub); font-size: 11px; padding: 2px 7px; border-radius: 4px; border: 1px solid var(--border);">${gorev}</span>` : ''}

            `;

            divListe.appendChild(item);

        });

    }

    

    const modalKisiler = document.getElementById('modal_teblig_kisiler');

    if (modalKisiler) {

        modalKisiler.style.display = 'flex';

        if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();

    }

};



window.tebligDosyasiAc = async function(dosyaYolu) {

    if (!dosyaYolu) {

        if (typeof bildirimGoster === 'function') bildirimGoster("Bu kayıt için dosya yolu bulunamadı.", "uyari");

        return;

    }

    

    try {

        const res = await fetch(`${API}/teblig-gecmisi/dosya-ac`, {

            method: 'POST',

            headers: { 'Content-Type': 'application/json' },

            body: JSON.stringify({ dosya_yolu: dosyaYolu })

        });

        const data = await res.json();

        if (data.basarili) {

            if (typeof bildirimGoster === 'function') bildirimGoster("PDF belgesi açıldı.", "bilgi");

        } else {

            if (typeof bildirimGoster === 'function') bildirimGoster(data.mesaj || "Dosya açılamadı.", "uyari");

        }

    } catch (e) {

        if (typeof bildirimGoster === 'function') bildirimGoster("Bağlantı hatası: " + e.message, "hata");

    }

};



window.tebligKaydiSil = async function(id) {

    let onay = true;

    if (typeof modernOnayGoster === 'function') {

        onay = await modernOnayGoster("Tebliğ Kaydını Sil", "Bu tebliğ kaydını arşivden silmek istediğinize emin misiniz? (Üretilmiş olan PDF dosyası diskten silinmez)", "uyari");

    } else {

        onay = confirm("Bu tebliğ kaydını silmek istediğinize emin misiniz?");

    }

    if (!onay) return;

    

    try {

        const res = await fetch(`${API}/teblig-gecmisi/${id}`, { method: 'DELETE' });

        const data = await res.json();

        if (data.basarili) {

            if (typeof bildirimGoster === 'function') bildirimGoster("Tebliğ kaydı silindi.", "bilgi");

            window.tumTebligatKayitlari = (window.tumTebligatKayitlari || []).filter(k => k.id !== id);

            tebligGecmisiTablosuCiz();

        } else {

            if (typeof bildirimGoster === 'function') bildirimGoster(data.mesaj || "Silinemedi.", "hata");

        }

    } catch (e) {

        if (typeof bildirimGoster === 'function') bildirimGoster("Hata: " + e.message, "hata");

    }

};

