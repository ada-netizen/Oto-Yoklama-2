
        // TEMA YÜKLEME
        document.addEventListener('DOMContentLoaded', () => {
            const savedTema = localStorage.getItem('temaPref') || 'gece';
            karanlikMod = (savedTema === 'gece');
            // Wait a tiny bit for elements to exist
            setTimeout(() => temaDegistir(savedTema), 50);
        });

const API = 'http://127.0.0.1:8000';

        // --- BİLDİRİM (TOAST) SİSTEMİ (TOASTIFY ENTEGRASYONU) ---
        function bildirimGoster(mesaj, tur) {
            if(!mesaj) return;
            if(!tur) tur = 'bilgi';
            
            // Hata ise kırmızı, bilgi ise yeşil tonları
            const bgColor = tur === 'hata' ? 'linear-gradient(to right, #EF4444, #DC2626)' : 'linear-gradient(to right, #10B981, #059669)';
            
            Toastify({
                text: mesaj,
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
                    padding: "12px 24px"
                }
            }).showToast();
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
            
            // Eğer forceState verilmişse onu kullan (başlangıçta okumak için)
            if (forceState !== null) {
                karanlikMod = (forceState === 'gece');
            } else {
                karanlikMod = !karanlikMod; // Toggle
            }
            
            if (!karanlikMod) {
                // Gündüz Moduna Geçiş
                root.style.setProperty('--bg-main', '#F1F5F9'); 
                root.style.setProperty('--bg-card', '#FFFFFF'); 
                root.style.setProperty('--fg-main', '#0F172A'); 
                root.style.setProperty('--fg-sub', '#475569'); 
                root.style.setProperty('--border', '#CBD5E1');
                root.style.setProperty('--dev-bg', '#FEE2E2'); 
                root.style.setProperty('--dev-fg', '#991B1B'); 
                if(btnTema) { btnTema.classList.remove('dark'); btnTema.classList.add('light'); }
                localStorage.setItem('temaPref', 'gunduz');
            } else {
                // Gece Moduna Geçiş
                root.style.setProperty('--bg-main', '#0F172A'); 
                root.style.setProperty('--bg-card', '#1E293B'); 
                root.style.setProperty('--fg-main', '#F8FAFC'); 
                root.style.setProperty('--fg-sub', '#94A3B8'); 
                root.style.setProperty('--border', '#334155');
                root.style.setProperty('--dev-bg', '#7F1D1D'); 
                root.style.setProperty('--dev-fg', '#FEF2F2'); 
                if(btnTema) { btnTema.classList.remove('light'); btnTema.classList.add('dark'); }
                localStorage.setItem('temaPref', 'gece');
            }
            
            // Tablodaki hata hücrelerini tekrar boya (eski kodun parçası)
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
            
            if(sekmeId === 'sekme_izin') verileriYukle();
            if(sekmeId === 'sekme_teblig') personelleriYukle();
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
                const thead = document.getElementById('yillik_thead'); const tbody = document.getElementById('yillik_tbody'); const ozetAlani = document.getElementById('yillik_ozet_alani');
                thead.innerHTML = ""; tbody.innerHTML = ""; ozetAlani.innerHTML = "";
                
                let theadHtml = `<tr><th style="background-color: #1E3A8A; color: white; padding: 6px; border: 1px solid var(--border);">Aylar</th>`;
                for(let i=1; i<=31; i++) { theadHtml += `<th id="yillik_col_${i}" style="background-color: #1E3A8A; color: white; padding: 4px; border: 1px solid var(--border); width: 25px;">${i}</th>`; }
                theadHtml += `</tr>`; thead.innerHTML = theadHtml;

                const aylarList = ["Eylül", "Ekim", "Kasım", "Aralık", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran"]; const ayNolar = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6];
                const rH = { "D": "#DC2626", "ÖY": "#EF4444", "SY": "#F87171", "G": "#EA580C", "İ": "#EAB308", "I": "#EAB308", "S": "#F59E0B", "R": "#D97706", "M": "#92400E", "N": "#3B82F6", "F": "#6366F1", "SV": "#8B5CF6" };

                let devMap = {}; let detayOzursuz = {}; let detayOzurlu = {}; let detayDiger = {}; let hsOzursuz = {}; let hsOzurlu = {}; let hsDiger = {}; let ozszNet = 0.0; let ozrlNet = 0.0; let digerNet = 0.0; let gSayisi = 0;
                const tumKayitlar = [...veri.devamsizliklar];
                geciciDevamsizliklar.forEach(gd => { if (String(gd.no) === String(no)) tumKayitlar.push(gd); });

                tumKayitlar.forEach(dev => {
                    let tur = dev.tur.toLocaleUpperCase('tr-TR'); let gunMiktari = parseFloat(dev.gun) || 0.0; let tamGun = gunMiktari >= 1 ? parseInt(gunMiktari) : 1;
                    let parts = dev.tarih.split('/'); if(parts.length !== 3) return;
                    let basTarih = new Date(parseInt(parts[2]), parseInt(parts[1])-1, parseInt(parts[0]));
                    let hiMiktari = 0.0, hsMiktari = 0.0;
                    
                    for(let i=0; i<tamGun; i++) {
                        let gTarih = new Date(basTarih); gTarih.setDate(gTarih.getDate() + i);
                        if (gTarih.getDay() !== 0 && gTarih.getDay() !== 6) devMap[`${gTarih.getFullYear()}-${gTarih.getMonth()+1}-${gTarih.getDate()}`] = tur;
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
                    else if (["N", "F", "SV"].includes(tur)) { detayDiger[tur] = (detayDiger[tur] || 0) + gunMiktari; hsDiger[tur] = (hsDiger[tur] || 0) + hsMiktari; digerNet += hiMiktari; } 
                    else { detayOzurlu[tur] = (detayOzurlu[tur] || 0) + gunMiktari; hsOzurlu[tur] = (hsOzurlu[tur] || 0) + hsMiktari; ozrlNet += hiMiktari; }
                });

                if (gSayisi > 0) { let g = Math.floor(gSayisi / 5) * 0.5; detayOzursuz[`G (${gSayisi})`] = g; ozszNet += g; }

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
        function ogrenciyiTamamenSil() {
            if(!confirm(`${sagTikOgrAd} kalıcı olarak silinecek. Onaylıyor musunuz?`)) return;
            fetch(`${API}/ogrenci-sil/${sagTikOgrNo}`, { method: 'DELETE' }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); verileriYukle();
                document.getElementById('sag_bos_uyari').style.display = 'flex'; document.getElementById('sag_dolu_icerik').style.display = 'none';
            });
        }

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
        
        function sirala(sutun) {
            if (siralamaSutun === sutun) siralamaYon *= -1; else { siralamaSutun = sutun; siralamaYon = 1; }
            tabloyuDoldur();
        }
        function basliklariGuncelle() {
            const basliklar = { 'temizSube': 'Sınıf', 'no': 'No', 'ad_soyad': 'Ad Soyad', 'ozsz': 'Özürsüz', 'ozrl': 'Özürlü' };
            for(let key in basliklar) { let el = document.getElementById('span_' + key); if(el) el.innerText = basliklar[key] + (siralamaSutun === key ? (siralamaYon === 1 ? ' ▲' : ' ▼') : ' ↕'); }
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
                    bildirimGoster(durum.mesaj, "bilgi");
                    verileriYukle();
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

        function filtreTemizle() { document.getElementById('ent_arama').value = ""; document.getElementById('combo_arama_sube').value = "Tümü"; tabloyuDoldur(); }

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
                // Taşan yazıları ... olarak göstermek için CSS eklendi
                // Taşan yazıları ... olarak göstermek için CSS eklendi ve BOLD etiketleri silindi
                tr.innerHTML = `<td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.temizSube}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.no}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ad_soyad}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ozszStr}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ozrl} Gün</td>`;
                govde.appendChild(tr);
            });
        }

        function ogrenciSec(no, ad, sube, ozsz, ozrl) {
            seciliOgrenci = { no: no, ad: ad, sube: sube, ozsz: parseFloat(ozsz || 0), ozrl: parseFloat(ozrl || 0) };
            document.getElementById('sag_bos_uyari').style.display = 'none'; 
            document.getElementById('sag_dolu_icerik').style.display = 'flex';
            
            // Eğer sildiğin HTML elementleri sayfada yoksa programın çökmesini engelliyoruz (Güvenlik Zırhı)
            let lblAd = document.getElementById('lbl_secili_ogrenci');
            if(lblAd) lblAd.innerText = `${ad} (${no})`;
            
            let lblOzet = document.getElementById('lbl_ozet');
            if(lblOzet) {
                lblOzet.innerText = `Özürsüz: ${ozsz} | Özürlü: ${ozrl}`;
                lblOzet.style.color = ozsz >= 10 ? '#DC2626' : 'var(--fg-sub)';
            }

            // Çökme yaşanmadığı için devamsızlıkları veritabanından sorunsuz çekecek
            fetch(`${API}/ogrenci-detay/${no}`).then(res => res.json()).then(veri => {
                seciliDevamsizliklar = veri.devamsizliklar.map(d => ({...d, secili: false})); geciciDevamsizliklar = []; takvimiCiz(); onizlemeGuncelle();
            });
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
            if (kalici) { kalici.secili = !kalici.secili; takvimiCiz(); onizlemeGuncelle(); return; }

            let gecici = geciciDevamsizliklar.find(d => d.tarih === tarihStr);
            if (!gecici) { geciciDevamsizliklar.push({id: 'temp_'+Date.now(), tarih: tarihStr, tur: 'D', gun: '1', secili: true}); } 
            else {
                if(gecici.tur === 'D') { gecici.tur = 'SY'; gecici.gun = '0.5'; }
                else if(gecici.tur === 'SY') { gecici.tur = 'ÖY'; gecici.gun = '0.5'; }
                else if(gecici.tur === 'ÖY') { geciciDevamsizliklar = geciciDevamsizliklar.filter(d => d.tarih !== tarihStr); }
            }
            takvimiCiz(); onizlemeGuncelle();
        }

        function hucreSagTikla(e, tarihStr) { e.preventDefault(); geciciDevamsizliklar = geciciDevamsizliklar.filter(d => d.tarih !== tarihStr); takvimiCiz(); onizlemeGuncelle(); }

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
            seciliOnizlemeSatirlari = []; takvimiCiz(); onizlemeGuncelle();
        }

        function onizlemeTemizle() { seciliDevamsizliklar.forEach(d => d.secili = false); geciciDevamsizliklar = []; takvimiCiz(); onizlemeGuncelle(); }

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
            takvimiCiz(); onizlemeGuncelle();
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
            
            takvimiCiz(); onizlemeGuncelle();
            document.getElementById('float_takvim').style.display = 'none';
            if(eklenen === 0) bildirimGoster("Seçilen tarih aralığında özürsüz devamsızlık bulunamadı.", "hata");
        }

        function verileriYukle() {
            fetch(`${API}/ogrenciler`).then(res => res.json()).then(veri => {
                ogrenciListesi = veri.ogrenciler || [];
                window.ogrenciListesi = ogrenciListesi; // Modal için global scope
                document.dispatchEvent(new CustomEvent('ogrenciler-guncellendi')); // Alpine'ı tetikle
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
                    ilerlemeTakipEt(sonuc.job_id, () => { geciciDevamsizliklar = []; seciliDevamsizliklar.forEach(d => d.secili = false); takvimiCiz(); onizlemeGuncelle(); });
                } else {
                    bildirimGoster(sonuc.mesaj, "hata");
                }
            });
        }
        
        // --- 5. YAZI TEBLİĞİ VE AYARLAR ---
               
        function personelleriYukle() {
            return fetch(`${API}/personeller?t=${new Date().getTime()}`).then(res => res.json()).then(veri => {
                // Herkes seçili DEĞİL ve manuel olarak da eklenmemiş şekilde (tertemiz) başlar.
                tumPersoneller = veri.personeller.map(p => ({ ...p, secili: false, manuelEklendi: false }));
                
                const cbEden = document.getElementById('b-eden'); const cbEdilen = document.getElementById('b-edilen');
                if(cbEden && cbEdilen) {
                    cbEden.innerHTML = '<option value="">-- İdareci Seçin --</option>';
                    cbEdilen.innerHTML = '<option value="">-- Personel Seçin --</option>';
                    tumPersoneller.forEach(p => {
                        cbEdilen.innerHTML += `<option value="${p.ad}">${p.ad}</option>`;
                        if(p.grup === 'İdare' || p.gorev.includes('MÜDÜR')) { cbEden.innerHTML += `<option value="${p.ad}">${p.ad}</option>`; }
                    });
                }
                personelFiltrePanelDoldur(); 
                if (typeof personelTablosunuDoldur === 'function') personelTablosunuDoldur(); 
                if (typeof yonetimPersonelTablosunuDoldur === 'function') yonetimPersonelTablosunuDoldur();
            });
        }

        function personelFiltrePanelDoldur() {
            const gorevPanel = document.getElementById('personel_gorev_panel');
            const bransPanel = document.getElementById('personel_brans_panel');
            if(!gorevPanel || !bransPanel) return;

            let gorevler = [...new Set(tumPersoneller.map(p => p.gorev))].filter(g => g !== "-").sort();
            let branslar = [...new Set(tumPersoneller.map(p => p.brans))].filter(b => b !== "-").sort();

            let gHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('gorev')"><i data-lucide="refresh-cw" width="16" height="16"></i> Listedekilerin Hepsini Ekle/Çıkar</div>`;
            gorevler.forEach((g, i) => {
                gHtml += `<label class="personel-filtre-item" style="display:flex; gap:5px; width:100%;"><input type="checkbox" onchange="filtreleriHesapla()" data-deger="${g.replace(/"/g, '&quot;')}"> <span>${g}</span></label>`;
            });
            gorevPanel.innerHTML = gHtml;

            let bHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('brans')"><i data-lucide="refresh-cw" width="16" height="16"></i> Listedekilerin Hepsini Ekle/Çıkar</div>`;
            branslar.forEach((b, i) => {
                bHtml += `<label class="personel-filtre-item" style="display:flex; gap:5px; width:100%;"><input type="checkbox" onchange="filtreleriHesapla()" data-deger="${b.replace(/"/g, '&quot;')}"> <span>${b}</span></label>`;
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
