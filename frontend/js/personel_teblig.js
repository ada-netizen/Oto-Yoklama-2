        // --- PERSONEL YÖNETİMİ ---
        function personelExcelYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Personel listesi işleniyor...");
            fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                if(v.basarili && v.job_id) {
                    ilerlemeTakipEt(v.job_id, personelleriYukle);
                } else {
                    bildirimGoster(v.mesaj, "hata");
                }
                if(event && event.target) event.target.value = '';
            }).catch(err => { 
                bildirimGoster(err.message || "Bağlantı hatası! Sunucuyu kontrol edin.", "hata"); 
            }).finally(() => yuklemeGizle());
        }

        function personelYonetimAc() { 
            modalAc('personel_yonetim_modal'); 
            // yonetimPersonelTablosunuDoldur() iptal edildi (artık Alpine.js kullanılıyor)
        }
        function ogrenciYonetimAc() { modalAc('ogrenci_yonetim_modal'); if(window.verileriYukle) window.verileriYukle(); }

        // --- <i data-lucide="brain" width="16" height="16"></i> GELİŞMİŞ AKILLI EŞLEŞTİRME MOTORU ---
        function akilliEslesmeModalAc() { if(tumPersoneller.length === 0) personelleriYukle().then(() => modalAc('akilli_eslesme_modal')); else modalAc('akilli_eslesme_modal'); }

function dinamikTebligFiltreleriOlustur() {
    const kapsayici = document.getElementById('dinamik_teblig_filtreleri');
    if (!kapsayici) return;
    let html = '<label class="chip-checkbox-wrapper" title="Tüm grupları seç/bırak"><input type="checkbox" id="grp_tumu" class="chip-checkbox" onchange="filtreTumuDegisti()"><span class="chip-label">Tümü</span></label>';
    tumPersonelGruplari.forEach(grup => {
        let sid = grup.replace(/[^a-zA-Z0-9]/g, '_');
        html += `<label class="chip-checkbox-wrapper"><input type="checkbox" id="grp_${sid}" class="chip-checkbox dinamik-grp-checkbox" data-grup="${grup}" onchange="filtreleriHesapla()"><span class="chip-label">${grup}</span></label>`;
    });
    kapsayici.innerHTML = html;
}

function filtreTumuDegisti() {
            const tumu = document.getElementById('grp_tumu') ? document.getElementById('grp_tumu').checked : false;
            
            const checkboxes = document.querySelectorAll('.dinamik-grp-checkbox');
            checkboxes.forEach(cb => cb.checked = tumu);
            
            tumPersoneller.forEach(p => {
                if (p.aktif === 0) {
                    p.secili = false;
                } else {
                    p.secili = tumu;
                }
            });
            personelTablosunuDoldur();
        }

        function filtreleriHesapla() {
            const checkboxes = document.querySelectorAll('.dinamik-grp-checkbox');
            let allChecked = true;
            
            const seciliGruplar = new Set();
            checkboxes.forEach(cb => {
                if (cb.checked) {
                    seciliGruplar.add(cb.getAttribute('data-grup'));
                } else {
                    allChecked = false;
                }
            });

            if (document.getElementById('grp_tumu')) 
                document.getElementById('grp_tumu').checked = allChecked;

            tumPersoneller.forEach(p => {
                let uyarMi = seciliGruplar.has(p.grup);
                
                if (uyarMi) {
                    p.secili = (p.aktif !== 0);
                } else if (!p.manuelEklendi) {
                    p.secili = false;
                }
            });

            personelTablosunuDoldur();
        }

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
            const arama = araKutu ? araKutu.value.toLocaleUpperCase('tr-TR') : "";

            const gosterilecekler = tumPersoneller.filter(p => {
                const aramaUygun = arama !== "" && (
                    p.ad.toLocaleUpperCase('tr-TR').includes(arama) || 
                    (p.gorev && p.gorev.toLocaleUpperCase('tr-TR').includes(arama)) || 
                    (p.brans && p.brans.toLocaleUpperCase('tr-TR').includes(arama)) || 
                    (p.grup && p.grup.toLocaleUpperCase('tr-TR').includes(arama))
                );
                // Pasif personel başka kuruma görevlendirildiği için normal toplu listelerde gösterilmez (arama hariç)
                if (p.aktif === 0 && !p.secili && !aramaUygun) return false;
                return p.secili || aramaUygun;
            });

            // Sütun başlığına göre aşağıdan yukarıya / yukarıdan aşağıya sıralama
            gosterilecekler.sort((a, b) => {
                let valA = (a[personelSiralamaSutun] || '').toString();
                let valB = (b[personelSiralamaSutun] || '').toString();
                return valA.localeCompare(valB, 'tr-TR', { sensitivity: 'base' }) * personelSiralamaYon;
            });

            govde.innerHTML = "";
            if(gosterilecekler.length === 0) {
                govde.innerHTML = "<tr><td colspan='5' style='text-align:center; padding:25px; color:var(--fg-sub); font-size:12px;'>Liste boş.<br>Grup kutularını işaretleyin veya personeli bulmak için arama yapın.</td></tr>";
                const masterKutu = document.getElementById('chk_master_personel');
                if(masterKutu) masterKutu.checked = false;
            } else {
                let ekrandakiSeciliSayisi = 0;
                gosterilecekler.forEach((p, i) => {
                    if(p.secili) ekrandakiSeciliSayisi++;
                    const brans = (!p.brans || p.brans.trim() === '' || p.brans === 'NaN') ? '-' : p.brans;
                    const gorev = (!p.gorev || p.gorev.trim() === '' || p.gorev === 'NaN') ? '-' : p.gorev;
                    const adEk = (p.aktif === 0) ? ' <span style="font-size:10px; color:#dc2626; font-weight:700;">(Başka Kurumda)</span>' : '';
                    govde.innerHTML += `<tr style="border-bottom: 1px solid var(--border);">
                        <td><label for="chk_${i}" style="cursor:pointer; display:block;">${p.ad}${adEk}</label></td>
                        <td>${gorev}</td>
                        <td>${brans}</td>
                        <td>${p.grup}</td>
                        <td style="text-align: center;"><input type="checkbox" class="chk-personel" id="chk_${i}" value="${p.ad}" onchange="personelDurumDegistir(this)" ${p.secili ? 'checked' : ''}></td>
                    </tr>`;
                });
                const masterKutu = document.getElementById('chk_master_personel');
                if(masterKutu) masterKutu.checked = (gosterilecekler.length > 0 && gosterilecekler.length === ekrandakiSeciliSayisi);
            }
            personelSayaciGuncelle();
        }

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
        p = (window.tumPersoneller || []).find(x => x.id === p || x.ad === p) || { ad: String(p) };
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

    const isPasif = (p.aktif === 0);
    const elPasif = document.getElementById('pp_gorevlendirildi_pasif');
    if (elPasif) elPasif.checked = isPasif;
    const elDurumBadge = document.getElementById('pp_durum_badge');
    if (elDurumBadge) elDurumBadge.style.display = isPasif ? 'inline-block' : 'none';

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

    ppFormuStatuyaGoreAyarla();

    modalAc('personel_profil_modal');
    if (typeof lucide !== 'undefined') {
        setTimeout(() => lucide.createIcons(), 50);
    }
}
window.personelProfilAc = personelProfilAc;

function ppGorevlendirmeDurumDegisti(checked) {
    const elDurumBadge = document.getElementById('pp_durum_badge');
    if (elDurumBadge) elDurumBadge.style.display = checked ? 'inline-block' : 'none';
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

    const isPasif = document.getElementById('pp_gorevlendirildi_pasif') ? document.getElementById('pp_gorevlendirildi_pasif').checked : false;

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
        aktif: isPasif ? 0 : 1
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

