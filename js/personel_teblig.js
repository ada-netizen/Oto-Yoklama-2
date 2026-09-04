        // --- PERSONEL YÖNETİMİ ---
        function personelExcelYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const onizlemeFormu = new FormData(); onizlemeFormu.append("dosya", dosya); onizlemeFormu.append("tur", "personel");
            yuklemeGoster("Personel dosyası doğrulanıyor ve önizleme hazırlanıyor...");
            fetch(`${API}/excel-onizle`, { method: 'POST', body: onizlemeFormu }).then(r => r.json()).then(onizleme => {
                if(!onizleme.basarili) throw new Error(onizleme.mesaj);
                const baslik = onizleme.sutunlar.join(' | ');
                const satirlar = onizleme.onizleme.slice(0, 5).map(satir => Object.values(satir).join(' | ')).join('\n');
                const hataMetni = onizleme.hatalar.length ? `\n\nUyarılar:\n${onizleme.hatalar.join('\n')}` : '';
                if(!confirm(`${onizleme.toplam_satir} personel satırı bulundu.\n\n${baslik}\n${satirlar}${hataMetni}\n\nListeyi aktarmaya devam edilsin mi?`)) return null;
                const formData = new FormData(); formData.append("dosya", dosya);
                yuklemeGoster("Personel listesi işleniyor...");
                return fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData });
            }).then(r => r ? r.json() : null).then(v => {
                if(!v) return;
                if(v.basarili && v.job_id) {
                    ilerlemeTakipEt(v.job_id, personelleriYukle);
                } else {
                    bildirimGoster(v.mesaj, "hata");
                }
                event.target.value = '';
            }).catch(err => { bildirimGoster(err.message || "Bağlantı hatası! Sunucuyu kontrol edin.", "hata"); }).finally(() => yuklemeGizle());
        }

        function personelYonetimAc() { modalAc('personel_yonetim_modal'); yonetimPersonelTablosunuDoldur(); }

        // --- <i data-lucide="brain" width="16" height="16"></i> GELİŞMİŞ AKILLI EŞLEŞTİRME MOTORU ---
        function aeTurDegisti() {
            const tur = document.getElementById('ae_tur').value;
            const secici = document.getElementById('ae_hedef');
            if(!secici) return;
            secici.innerHTML = '';
            
            let secenekler = [];
            if(tur === 'kisi') {
                secenekler = [...tumPersoneller].map(p => p.ad).sort();
            } else if(tur === 'grup') {
                secenekler = ['İdare', 'Öğretmenler', 'Diğer Personel'];
            } else if(tur === 'gorev') {
                secenekler = [...new Set(tumPersoneller.map(p => p.gorev))].filter(g => g !== "-").sort();
            } else if(tur === 'brans') {
                secenekler = [...new Set(tumPersoneller.map(p => p.brans))].filter(b => b !== "-").sort();
            }
            secenekler.forEach(s => secici.innerHTML += `<option value="${s.replace(/"/g, '&quot;')}">${s}</option>`);
        }

        function akilliEslesmeModalAc() {
            if(!sistemAyarlari.oto_eslesmeler) sistemAyarlari.oto_eslesmeler = [];
            
            // Eğer personeller henüz yüklenmediyse, önce yükleyip sonra pencereyi açar
            if(tumPersoneller.length === 0) {
                personelleriYukle().then(() => {
                    aeTurDegisti(); 
                    akilliEslesmeCiz();
                    modalAc('akilli_eslesme_modal');
                });
                return;
            }
            
            aeTurDegisti(); 
            akilliEslesmeCiz();
            modalAc('akilli_eslesme_modal');
        }

        function akilliEslesmeEkle() {
            const kelime = document.getElementById('ae_kelime').value.trim();
            const tur = document.getElementById('ae_tur').value;
            const hedef = document.getElementById('ae_hedef').value;
            if(!kelime || !hedef) return bildirimGoster("Lütfen alanları tam doldurun!", "hata");
            
            if(!sistemAyarlari.oto_eslesmeler) sistemAyarlari.oto_eslesmeler = [];
            sistemAyarlari.oto_eslesmeler.push({ kelime: kelime, tur: tur, hedef: hedef });
            
            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sistemAyarlari) })
            .then(r => r.json()).then(v => {
                bildirimGoster("Kural başarıyla eklendi!", "bilgi");
                document.getElementById('ae_kelime').value = '';
                akilliEslesmeCiz();
            });
        }

        function akilliEslesmeCiz() {
            const liste = document.getElementById('ae_liste');
            if(!liste) return;
            liste.innerHTML = '';
            if(!sistemAyarlari.oto_eslesmeler || sistemAyarlari.oto_eslesmeler.length === 0) {
                liste.innerHTML = '<div style="padding:15px; text-align:center; color:var(--fg-sub); font-size:11px;">Henüz kural eklenmemiş.</div>';
                return;
            }
            const turIsimleri = { 'kisi': 'Kişi', 'grup': 'Grup', 'gorev': 'Görev', 'brans': 'Branş' };
            
            sistemAyarlari.oto_eslesmeler.forEach((kural, i) => {
                let gTur = kural.tur ? turIsimleri[kural.tur] : 'Kişi';
                let gHedef = kural.hedef || kural.personel;
                
                liste.innerHTML += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border-bottom:1px solid var(--border); font-size:11px; color: var(--fg-main);">
                    <div><strong style="color: #8B5CF6;">Kelime:</strong> ${kural.kelime} <br> <strong style="color:var(--tree-sel);">${gTur}:</strong> ${gHedef}</div>
                    <button class="btn btn-kirmizi" style="padding:4px 10px; font-size:9px;" onclick="akilliEslesmeSil(${i})">Sil</button>
                </div>`;
            });
        }

        function akilliEslesmeSil(index) {
            if(!confirm("Kuralı silmek istediğinize emin misiniz?")) return;
            sistemAyarlari.oto_eslesmeler.splice(index, 1);
            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sistemAyarlari) })
            .then(r => r.json()).then(v => { bildirimGoster("Kural silindi!", "bilgi"); akilliEslesmeCiz(); });
        }

        // --- 1. TÜMÜNÜ SEÇ/LİSTELE MOTORU ---
        function filtreTumuDegisti() {
            const tumu = document.getElementById('grp_tumu').checked;
            // Diğer tüm grupları otomatik olarak işaretle
            if(document.getElementById('grp_idare')) document.getElementById('grp_idare').checked = tumu;
            if(document.getElementById('grp_ogretmenler')) document.getElementById('grp_ogretmenler').checked = tumu;
            if(document.getElementById('grp_diger')) document.getElementById('grp_diger').checked = tumu;
            
            // Tüm personeli manuelEklendi yap ki listeden silinmesinler
            tumPersoneller.forEach(p => p.secili = tumu);
            personelTablosunuDoldur();
        }

        function filtreleriHesapla() {
            const grp_idare = document.getElementById('grp_idare').checked;
            const grp_ogr = document.getElementById('grp_ogretmenler').checked;
            const grp_diger = document.getElementById('grp_diger').checked;

            // Master checkbox kontrolü
            if (document.getElementById('grp_tumu')) 
                document.getElementById('grp_tumu').checked = (grp_idare && grp_ogr && grp_diger);

            tumPersoneller.forEach(p => {
                let uyarMi = false;
                if (grp_idare && p.grup === 'İdare') uyarMi = true;
                if (grp_ogr && p.grup === 'Öğretmenler') uyarMi = true;
                if (grp_diger && p.grup === 'Diğer Personel') uyarMi = true;

                if (uyarMi) p.secili = true;
                else if (!p.manuelEklendi) p.secili = false;
            });
            personelTablosunuDoldur();
        }

        // --- 2. GÖREV VE BRANŞ İÇİN "ARAMA İÇİNDE FİLTRE" MANTIĞI ---
        function personelTablosunuDoldur() {
            const govde = document.getElementById('personel-govde');
            if(!govde) return;
            const araKutu = document.getElementById('personel_ara');
            const arama = araKutu ? araKutu.value.toUpperCase() : "";

            const gosterilecekler = tumPersoneller.filter(p => {
                const aramaUygun = arama === "" || p.ad.toUpperCase().includes(arama) || p.gorev.toUpperCase().includes(arama) || p.brans.toUpperCase().includes(arama) || p.grup.toUpperCase().includes(arama);
                return p.secili || (arama !== "" && aramaUygun);
            });

            govde.innerHTML = "";
            if(gosterilecekler.length === 0) {
                govde.innerHTML = "<tr><td colspan='5' style='text-align:center; padding:25px; color:var(--fg-sub); font-size:12px;'>Liste boş.<br>İdare/Öğretmen kutularını işaretleyin veya personeli bulmak için arama yapın.</td></tr>";
                const masterKutu = document.getElementById('chk_master_personel');
                if(masterKutu) masterKutu.checked = false;
            } else {
                let ekrandakiSeciliSayisi = 0;
                gosterilecekler.forEach((p, i) => {
                    if(p.secili) ekrandakiSeciliSayisi++;
                    const brans = (!p.brans || p.brans.trim() === '' || p.brans === 'NaN') ? '-' : p.brans;
                    const gorev = (!p.gorev || p.gorev.trim() === '' || p.gorev === 'NaN') ? '-' : p.gorev;
                    govde.innerHTML += `<tr style="border-bottom: 1px solid var(--border);">
                        <td style="text-align: center;"><input type="checkbox" class="chk-personel" id="chk_${i}" value="${p.ad}" onchange="personelDurumDegistir(this)" ${p.secili ? 'checked' : ''}></td>
                        <td>${p.grup}</td>
                        <td>${gorev}</td>
                        <td>${brans}</td>
                        <td><label for="chk_${i}" style="cursor:pointer; display:block;">${p.ad}</label></td>
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

        function ayarlariGetirPersonelGruplariIcin() {
            fetch(`${API}/ayarlar-getir`).then(r => r.json()).then(v => {
                let ayar = v.ayarlar || {};
                tumPersonelGruplari = ayar.personel_gruplari || ['İdare', 'Öğretmenler', 'Diğer Personel'];
                personelGruplariCiz();
            });
        }

        function personelGruplariCiz() {
            // Çipleri çiz
            const cipContainer = document.getElementById('personel_filtre_cipleri');
            if (cipContainer) {
                cipContainer.innerHTML = `<button class="filter-chip ${aktifPersonelFiltresi === 'Tümü' ? 'active' : ''}" onclick="personelFiltreAyarla('Tümü', this)">Tümü</button>`;
                tumPersonelGruplari.forEach(grup => {
                    const isActive = aktifPersonelFiltresi === grup ? 'active' : '';
                    cipContainer.innerHTML += `<button class="filter-chip ${isActive}" onclick="personelFiltreAyarla('${grup}', this)">${grup}</button>`;
                });
            }
            
            // Drawer select'i çiz
            const drawerSelect = document.getElementById('drawer_grup');
            if (drawerSelect) {
                drawerSelect.innerHTML = tumPersonelGruplari.map(g => `<option value="${g}">${g}</option>`).join('');
            }
            
            // Grup yönetimi modali tablosunu çiz
            const govde = document.getElementById('personel_grup_govde');
            if (govde) {
                govde.innerHTML = tumPersonelGruplari.map(g => `
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border); color: var(--fg-main);">${g}</td>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border); text-align: right;">
                            <button class="icon-btn" style="color:#EF4444;" onclick="personelGrubuSil('${g}')" title="Sil"><i data-lucide="trash-2" width="16" height="16"></i></button>
                        </td>
                    </tr>
                `).join('');
            }
            
            yonetimPersonelTablosunuDoldur();
            if (typeof lucide !== 'undefined') {
                setTimeout(() => lucide.createIcons(), 50);
            }
        }

        function personelGrupYonetimiAc() {
            modalAc('personel_grup_yonetim_modal');
        }

        function yeniPersonelGrubuEkle() {
            const input = document.getElementById('yeni_grup_adi');
            const ad = input.value.trim();
            if (!ad) return;
            if (tumPersonelGruplari.includes(ad)) {
                bildirimGoster("Bu grup zaten mevcut!", "hata");
                return;
            }
            tumPersonelGruplari.push(ad);
            personelGrubuKaydet().then(() => {
                input.value = '';
                personelGruplariCiz();
                bildirimGoster("Grup eklendi", "bilgi");
            });
        }

        function personelGrubuSil(ad) {
            if(!confirm(`'${ad}' grubunu silmek istediğinize emin misiniz?`)) return;
            tumPersonelGruplari = tumPersonelGruplari.filter(g => g !== ad);
            if(aktifPersonelFiltresi === ad) aktifPersonelFiltresi = 'Tümü';
            personelGrubuKaydet().then(() => {
                personelGruplariCiz();
                bildirimGoster("Grup silindi", "bilgi");
            });
        }

        function personelGrubuKaydet() {
            return fetch(`${API}/ayarlar-getir`).then(r => r.json()).then(v => {
                let ayar = v.ayarlar || {};
                ayar.personel_gruplari = tumPersonelGruplari;
                return fetch(`${API}/ayarlar-kaydet`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ayar)
                });
            });
        }

        function personelFiltreAyarla(filtre, btn) {
            aktifPersonelFiltresi = filtre;
            document.querySelectorAll('#personel_filtre_cipleri .filter-chip').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            yonetimPersonelTablosunuDoldur();
        }

        function yonetimPersonelTablosunuDoldur() {
            const filtreText = document.getElementById('personel_arama').value.toUpperCase();
            const govde = document.getElementById('personel_govde');
            if(!govde) return;
            govde.innerHTML = '';
            
            [...tumPersoneller].sort((a,b) => a.ad.localeCompare(b.ad)).forEach(p => {
                // Metin araması
                if(filtreText && !p.ad.toUpperCase().includes(filtreText)) return;
                
                // Çip Filtresi
                if (aktifPersonelFiltresi !== 'Tümü' && p.grup !== aktifPersonelFiltresi) {
                    return;
                }
                
                const satir = document.createElement('tr');
                satir.innerHTML = `
                    <td style="padding: 12px; border-bottom: 1px solid var(--border); color: var(--fg-main); font-weight:bold;">${p.ad}</td>
                    <td style="padding: 12px; border-bottom: 1px solid var(--border); color: var(--fg-main);">${p.brans}</td>
                    <td style="padding: 12px; border-bottom: 1px solid var(--border); color: var(--fg-sub); font-size:11px;">${p.gorev}</td>
                    <td style="padding: 12px; border-bottom: 1px solid var(--border); text-align: center;">
                        <button class="icon-btn" style="color:var(--tree-sel);" onclick="personelDuzenleBaslat('${p.ad}')" title="Düzenle"><i data-lucide="edit" width="16" height="16"></i></button>
                        <button class="icon-btn" style="color:#EF4444;" onclick="personelSil('${p.ad}')" title="Sil"><i data-lucide="trash-2" width="16" height="16"></i></button>
                    </td>
                `;
                govde.appendChild(satir);
            });
            
            if (tumPersoneller.length === 0 || govde.innerHTML === '') {
                govde.innerHTML = '<tr><td colspan="5" style="padding:30px; text-align:center; color:var(--fg-sub);">Personel bulunamadı.</td></tr>';
            }
            if (typeof lucide !== 'undefined') {
                setTimeout(() => lucide.createIcons(), 50);
            }
        }
        
        function personelDrawerAc() {
            document.getElementById('drawer_baslik').innerText = 'Yeni Personel Ekle';
            document.getElementById('drawer_eski_ad').value = '';
            document.getElementById('drawer_ad').value = '';
            document.getElementById('drawer_brans').value = '';
            document.getElementById('drawer_gorev').value = '';
            if(tumPersonelGruplari.length > 0) document.getElementById('drawer_grup').value = tumPersonelGruplari[0];
            document.getElementById('personel_drawer').classList.add('open');
            document.getElementById('drawer_ad').focus();
        }

        function personelDrawerKapat() {
            document.getElementById('personel_drawer').classList.remove('open');
        }
        
        function personelDuzenleBaslat(ad) {
            const p = tumPersoneller.find(x => x.ad === ad);
            if(!p) return;
            document.getElementById('drawer_baslik').innerText = 'Personeli Düzenle';
            document.getElementById('drawer_eski_ad').value = p.ad;
            document.getElementById('drawer_ad').value = p.ad;
            document.getElementById('drawer_brans').value = p.brans;
            document.getElementById('drawer_gorev').value = p.gorev;
            document.getElementById('drawer_grup').value = p.grup;
            document.getElementById('personel_drawer').classList.add('open');
            document.getElementById('drawer_ad').focus();
        }

        function personelDrawerKaydet() {
            const ad = document.getElementById('drawer_ad').value.trim();
            if(!ad) return bildirimGoster("Ad Soyad boş bırakılamaz!", "hata");
            
            const veri = { 
                ad: ad, 
                gorev: document.getElementById('drawer_gorev').value.trim(), 
                brans: document.getElementById('drawer_brans').value.trim(), 
                grup: document.getElementById('drawer_grup').value 
            };
            
            const eskiAd = document.getElementById('drawer_eski_ad').value;
            
            if (eskiAd) {
                // Güncelleme
                fetch(`${API}/personel-guncelle/${encodeURIComponent(eskiAd)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => {
                    bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                    if(v.basarili) {
                        personelDrawerKapat();
                        personelleriYukle().then(() => {
                            yonetimPersonelTablosunuDoldur();
                            if (document.getElementById('teblig_modal').style.display === 'flex') {
                                tebligModalAc(aktifOgrenciNo);
                            }
                        });
                    }
                });
            } else {
                // Ekleme
                fetch(`${API}/personel-ekle`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => {
                    bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                    if(v.basarili) { 
                        personelDrawerKapat(); 
                        personelleriYukle().then(() => yonetimPersonelTablosunuDoldur()); 
                    }
                });
            }
        }

        function personelSil(ad) {
            if(!confirm(`${ad} adlı personeli silmek istediğinize emin misiniz?`)) return;
            fetch(`${API}/personel-sil/${encodeURIComponent(ad)}`, { method: 'DELETE' }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                personelleriYukle().then(() => yonetimPersonelTablosunuDoldur());
            });
        }
        
        function personelPdfIndir() {
            fetch(`${API}/personel-pdf-indir`).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
        }

        function personelExcelIndir() {
            fetch(`${API}/personel-excel-indir`).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
        }
        
        function esikRaporuAl(format) {
            fetch(`${API}/rapor-esik-siniflar/${format}`).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
        }

        // --- RAPORLAR ---
        function raporAl(tur, format, ozelDeger) {
            if((tur === 'gun_siniri' || tur === 'sube_bazli' || tur === 'tarih_bazli') && !ozelDeger) {
                return bildirimGoster("Lütfen rapor almadan önce bir seçim yapınız!", "hata");
            }
            fetch(`${API}/rapor-al`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tur, format, ozel_deger: ozelDeger }) })
                .then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
        }

        // --- AYARLAR, LOGO VE YEDEKLEME ---
        function logoYukle(tur, event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("tur", tur); formData.append("dosya", dosya);
            fetch(`${API}/logo-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                if(v.basarili) {
                    const etiket = tur === 'meb' ? 'ayar_meb_logo_ad' : 'ayar_okul_logo_ad';
                    document.getElementById(etiket).innerText = dosya.name;
                }
                event.target.value = '';
            });
        }

        function yedekleriListele() {
            fetch(`${API}/yedekler-listele`).then(r => r.json()).then(v => {
                const kutu = document.getElementById('ayar_yedek_secim'); if(!kutu) return;
                if(!v.yedekler || v.yedekler.length === 0) { kutu.innerHTML = '<option value="">Yedek dosyası bulunamadı</option>'; return; }
                kutu.innerHTML = v.yedekler.map(y => `<option value="${y.dosya_adi}">${y.tarih} (${y.boyut_kb} KB)</option>`).join('');
            });
        }

        function yedekGeriYukle() {
            const secim = document.getElementById('ayar_yedek_secim').value;
            if(!secim) return bildirimGoster("Lütfen bir yedek dosyası seçin.", "hata");
            if(!confirm("Mevcut veriler silinecek ve seçilen yedekteki veriler yüklenecek.\n\nBu işlemi onaylıyor musunuz?")) return;
            fetch(`${API}/yedek-geri-yukle`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dosya: secim }) })
                .then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); if(v.basarili) location.reload(); });
        }

        function ayarlariYukle() {
            fetch(`${API}/ayarlar-getir`).then(r => r.json()).then(v => {
                sistemAyarlari = v.ayarlar;
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
                    fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ilk_kullanim: false }) });
                } else if (!v.ayarlar.meb_logosu) {
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
            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sistemAyarlari) }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); modalKapat('ayarlar_modal'); });
        }

        function sistemYedekle() { fetch(`${API}/yedek-al`, { method: 'POST' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); yedekleriListele(); }); }

        function loglariGoster() {
            fetch(`${API}/loglar`).then(r => r.json()).then(v => {
                const govde = document.getElementById('ayar_log_govde');
                if(!govde) return;
                govde.style.display = 'block';
                govde.textContent = v.loglar.length ? v.loglar.map(l => `[${l.zaman}] ${l.seviye.toUpperCase()} | ${l.islem}: ${l.mesaj}`).join('\n') : 'Henüz işlem kaydı yok.';
            }).catch(() => bildirimGoster('Loglar okunamadı.', 'hata'));
        }

        function sonIslemiGeriAl() {
            if(!confirm('Son güvenli yedeğe dönülecek. Mevcut durum önce ayrıca yedeklenecek. Devam edilsin mi?')) return;
            fetch(`${API}/son-islemi-geri-al`, { method: 'POST' }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? 'bilgi' : 'hata');
                if(v.basarili) location.reload();
            }).catch(() => bildirimGoster('Geri alma işlemi başarısız.', 'hata'));
        }
        
        function veritabaniniSifirla() {
            if(confirm("Tüm öğrenciler, devamsızlıklar ve personeller SİLİNECEK.\nEmin misiniz?")) {
                if(confirm("Bu işlem GERİ ALINAMAZ! Onaylıyor musunuz?")) {
                    fetch(`${API}/veritabani-sifirla`, { method: 'DELETE' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });
                }
            }
        }

        function ogrencileriSifirla() {
            if(confirm("Tüm öğrenci ve devamsızlık kayıtları SİLİNECEK.\nPersonel verilerine dokunulmayacak.\nEmin misiniz?")) {
                if(confirm("Bu işlem GERİ ALINAMAZ! Onaylıyor musunuz?")) {
                    fetch(`${API}/ogrencileri-sifirla`, { method: 'DELETE' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });
                }
            }
        }

        function personelSifirla() {
            if(confirm("Tüm personel kayıtları SİLİNECEK.\nÖğrenci verilerine dokunulmayacak.\nEmin misiniz?")) {
                if(confirm("Bu işlem GERİ ALINAMAZ! Onaylıyor musunuz?")) {
                    fetch(`${API}/personel-sifirla`, { method: 'DELETE' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });
                }
            }
        }


        

        // --- AÇILIŞ (SPLASH) EKRANI ---
        function splashKapat() {
            const splash = document.getElementById('splash_overlay');
            if(splash) { splash.classList.add('gizli'); setTimeout(() => splash.style.display = 'none', 450); }
        }

        // --- OTOMATİK GÜNCELLEME KONTROLÜ (GitHub) ---
        const MEVCUT_VERSIYON = "v1.1";
        function surumKarsilastir(a, b) {
            const parcalaraAyir = surum => String(surum).trim().toLowerCase().replace(/^v/, '').split('.').map(Number);
            const sol = parcalaraAyir(a); const sag = parcalaraAyir(b);
            for(let i = 0; i < Math.max(sol.length, sag.length); i++) {
                const solDeger = sol[i] || 0; const sagDeger = sag[i] || 0;
                if(solDeger !== sagDeger) return solDeger - sagDeger;
            }
            return 0;
        }

        function guncellemeKontrolEt() {
            fetch("https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/versiyon.txt", { cache: "no-store" })
                .then(r => r.ok ? r.text() : Promise.reject())
                .then(metin => {
                    const enYeni = metin.trim();
                    if (surumKarsilastir(enYeni, MEVCUT_VERSIYON) > 0) {
                        if (confirm(`Programın yeni bir sürümü bulundu!\n\nSizin Sürümünüz: ${MEVCUT_VERSIYON}\nYeni Sürüm: ${enYeni}\n\nYeni sürümü indirmek ister misiniz?`)) {
                            window.open("https://github.com/ada-netizen/yoklama_otomasyonu/releases/latest", "_blank");
                        }
                    }
                })
                .catch(() => { /* İnternet yoksa veya erişilemezse sessizce devam eder */ });
        }

        function gecKalanlariIndir() {
            fetch(`${API}/rapor-gec-bugun`)
                .then(res => res.json())
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
            
            fetch(`${API}/gec-bugun-sayisi`).then(r => r.json()).then(data => {
                if(data.basarili && data.sayi > 0) {
                    setTimeout(() => {
                        bildirimGoster(`Bugün ${data.sayi} öğrenci geç yazıldı. Listeyi görmek için <u style="cursor:pointer;" onclick="gecKalanlariIndir()">tıklayın</u>`, 'bilgi');
                    }, 2000);
                }
            });
            ayarlariGetirPersonelGruplariIcin();
            resizerAktifEt('resizer1', 'sol_panel_ana', 'sag_panel_ana');
            resizerAktifEt('resizer2', 'takvim_alani_ana', 'onizleme_alani_ana');
            tabloSutunBoyutlandirma();
            setTimeout(splashKapat, 1500);
            setTimeout(guncellemeKontrolEt, 2000);
            
            
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        };

// ==========================================
// İHALE MODÜLÜ (22/d) FONKSİYONLARI
