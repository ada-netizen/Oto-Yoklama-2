
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
                duration: 4000,
                gravity: "top", 
                position: "center", 
                stopOnFocus: true, 
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
        function modalAc(id) { 
            document.getElementById(id).style.display = 'flex'; 
            if(id === 'raporlar_modal') {
                const subeler = [...new Set(ogrenciListesi.map(o => sinifFormatla(o.sube)))];
                subeler.sort((a, b) => (parseInt(a)||99) - (parseInt(b)||99));
                const raporKutu = document.getElementById('rapor_sube_kutu');
                if(raporKutu) {
                    raporKutu.innerHTML = '<option>Seç</option>';
                    subeler.forEach(s => raporKutu.innerHTML += `<option>${s}</option>`);
                }
            }
        }
        
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
                    let tur = dev.tur.toUpperCase(); let gunMiktari = parseFloat(dev.gun) || 0.0; let tamGun = gunMiktari >= 1 ? parseInt(gunMiktari) : 1;
                    let parts = dev.tarih.split('/'); if(parts.length !== 3) return;
                    let basTarih = new Date(parseInt(parts[2]), parseInt(parts[1])-1, parseInt(parts[0]));
                    let hiMiktari = 0.0, hsMiktari = 0.0;
                    
                    for(let i=0; i<tamGun; i++) {
                        let gTarih = new Date(basTarih); gTarih.setDate(gTarih.getDate() + i);
                        if (gTarih.getDay() !== 0 && gTarih.getDay() !== 6) devMap[`${gTarih.getMonth()+1}-${gTarih.getDate()}`] = tur;
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
                    
                    for(let gun=1; gun<=31; gun++) {
                        let is_valid = true, is_weekend = false; let y_val = ayNo < 8 ? calYear : calYear - 1; let dt = new Date(y_val, ayNo-1, gun);
                        if (dt.getMonth() + 1 !== ayNo) is_valid = false; else if (dt.getDay() === 0 || dt.getDay() === 6) is_weekend = true;

                        let cellBg = karanlikMod ? "#1E293B" : "#F1F5F9"; let cellFg = "var(--fg-main)"; let cellText = ""; let isAbs = false;
                        if (!is_valid || is_weekend) { cellBg = karanlikMod ? "#0B1120" : "#D1D5DB"; } 
                        else {
                            let devKey = `${ayNo}-${gun}`;
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
                      .toUpperCase();
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
            yuklemeGoster("Excel dosyası işleniyor...");
            fetch(`${API}/${endpoint}`, { method: 'POST', body: formData }).then(r => r.json()).then(v => { 
                if(v.basarili) { bildirimGoster(v.mesaj, "bilgi"); verileriYukle(); } else { bildirimGoster("Hata: " + v.mesaj, "hata"); }
                event.target.value = ''; 
            }).catch(err => { bildirimGoster("Bağlantı hatası! Sunucuyu kontrol edin.", "hata"); }).finally(() => yuklemeGizle());
        }
        function filtreTemizle() { document.getElementById('ent_arama').value = ""; document.getElementById('combo_arama_sube').value = "Tümü"; tabloyuDoldur(); }

        function tabloyuDoldur() {
            const arama = document.getElementById('ent_arama') ? document.getElementById('ent_arama').value.toUpperCase() : "";
            const subeFiltre = document.getElementById('combo_arama_sube') ? document.getElementById('combo_arama_sube').value : "Tümü";
            const govde = document.getElementById('tree_govde'); if(!govde) return;
            govde.innerHTML = ""; basliklariGuncelle();

            let islenecekler = ogrenciListesi.map(ogr => {
                let temizSube = sinifFormatla(ogr.sube);
                return { ...ogr, temizSube: temizSube, ozsz: Math.round((ogr.ozursuz || 0)*10)/10, ozrl: Math.round((ogr.ozurlu || 0)*10)/10 };
            }).filter(ogr => {
                if (subeFiltre !== "Tümü" && ogr.temizSube !== subeFiltre) return false;
                if (arama && arama !== "NUMARA VEYA AD SOYAD" && !ogr.ad_soyad.toUpperCase().includes(arama) && !ogr.no.includes(arama)) return false;
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
                    tr.classList.add('tr-secili'); ogrenciSec(ogr.no, ogr.ad_soyad, ogr.ozsz, ogr.ozrl);
                };
                tr.ondblclick = function() { yillikListeAc(ogr.no, ogr.ad_soyad); };
                tr.oncontextmenu = function(e) {
                    document.querySelectorAll('#tree_govde tr').forEach(row => row.classList.remove('tr-secili'));
                    tr.classList.add('tr-secili'); ogrenciSec(ogr.no, ogr.ad_soyad, ogr.ozsz, ogr.ozrl); sagTikMenuAc(e, ogr.no, ogr.ad_soyad);
                };
                // Taşan yazıları ... olarak göstermek için CSS eklendi
                // Taşan yazıları ... olarak göstermek için CSS eklendi ve BOLD etiketleri silindi
                tr.innerHTML = `<td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.temizSube}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.no}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ad_soyad}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ozszStr}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ozrl} Gün</td>`;
                govde.appendChild(tr);
            });
        }

        function ogrenciSec(no, ad, ozsz, ozrl) {
            seciliOgrenci = { no: no, ad: ad, ozsz: parseFloat(ozsz || 0), ozrl: parseFloat(ozrl || 0) };
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
                
                let hedefKayitlar = tumKayitlar.filter(k => k.tarih === tarihStr && ['D', 'ÖY', 'SY'].includes(k.tur.toUpperCase()));
                let kayit = hedefKayitlar.length > 0 ? (hedefKayitlar.find(k => k.secili) || hedefKayitlar[hedefKayitlar.length - 1]) : null;
                
                let borderStyle = 'border: 1px solid var(--border);'; 
                // YENİ: Boş günlere bembeyaz olmak yerine hafif sekmelerdeki gri tonu verdik
                let bgStyle = 'background-color: var(--bg-main);'; 
                let fgStyle = ''; 
                let icerik = '<div></div>'; 
                
                if (kayit) {
                    let tur = kayit.tur.toUpperCase();
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
            let kalici = seciliDevamsizliklar.find(d => d.tarih === tarihStr && ['D', 'ÖY', 'SY'].includes(d.tur.toUpperCase()));
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
                if(!['D', 'ÖY', 'SY'].includes(d.tur.toUpperCase())) return;
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
                if(!['D', 'ÖY', 'SY'].includes(d.tur.toUpperCase())) return;
                let kDate = parseTarihStr(d.tarih); 
                if(kDate && kDate >= ozelBas && kDate <= ozelBit) { d.secili = true; eklenen++; }
            });
            
            takvimiCiz(); onizlemeGuncelle();
            document.getElementById('float_takvim').style.display = 'none';
            if(eklenen === 0) bildirimGoster("Seçilen tarih aralığında özürsüz devamsızlık bulunamadı.", "hata");
        }

        function verileriYukle() {
            fetch(`${API}/ogrenciler`).then(res => res.json()).then(veri => {
                ogrenciListesi = veri.ogrenciler;
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
            });
        }
        
        function pdfCiktisiAl() {
            if(!seciliOgrenci) return;
            const kayitlar = [...seciliDevamsizliklar, ...geciciDevamsizliklar].filter(d => d.secili);
            if(kayitlar.length === 0) { bildirimGoster("Önizleme listesinde yazdırılacak kayıt yok!", "hata"); return; }
            
            const geciciler = kayitlar.filter(d => d.id.startsWith('temp_'));
            if(geciciler.length > 0) {
                bildirimGoster("Manuel girdiğiniz kayıtlar veritabanına işleniyor, ardından PDF oluşturulacaktır.", "bilgi");
                Promise.all(geciciler.map(g => {
                    return fetch(`${API}/devamsizlik-manuel-ekle`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ no: seciliOgrenci.no, tarih: g.tarih, tur: g.tur, gun: g.gun }) });
                })).then(() => { gercekPdfIstegiAt(kayitlar); verileriYukle(); });
            } else { gercekPdfIstegiAt(kayitlar); }
        }

        function gercekPdfIstegiAt(kayitlar) {
            let ad = seciliOgrenci.ad;
            
            const sube = document.querySelector('.tr-secili td')?.innerText || "Bilinmiyor";
            const veri = { no: seciliOgrenci.no, ad: ad, sube: sube, kayitlar: kayitlar };

            fetch(`${API}/pdf-veli-formu`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) })
            .then(res => res.json()).then(sonuc => {
                bildirimGoster(sonuc.mesaj, sonuc.basarili ? "bilgi" : "hata"); geciciDevamsizliklar = []; seciliDevamsizliklar.forEach(d => d.secili = false); takvimiCiz(); onizlemeGuncelle();
            });
        }
        
        // --- 5. YAZI TEBLİĞİ VE AYARLAR ---
               
        function personelleriYukle() {
            return fetch(`${API}/personeller`).then(res => res.json()).then(veri => {
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
            fetch(`${API}/teblig-toplu-pdf`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
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
                yer: document.getElementById('b-yer').value,
                teblig_tarihi: document.getElementById('b-tarih') ? document.getElementById('b-tarih').value : null,
                gecici_pdf_yolu: document.getElementById('t-pdf-yol') ? document.getElementById('t-pdf-yol').value : ""
            };
            fetch(`${API}/teblig-bireysel-pdf`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
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
                event.target.value = '';
            }).catch(() => { yuklemeGizle(); bildirimGoster("Bağlantı hatası!", "hata"); });
        }

        // --- PERSONEL YÖNETİMİ ---
        function personelExcelYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Personel listesi işleniyor...");
            fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); if(v.basarili) personelleriYukle();
                event.target.value = '';
            }).catch(() => bildirimGoster("Bağlantı hatası! Sunucuyu kontrol edin.", "hata")).finally(() => yuklemeGizle());
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
        
        function veritabaniniSifirla() {
            if(confirm("Tüm öğrenciler, devamsızlıklar ve personeller SİLİNECEK.\nEmin misiniz?")) {
                if(confirm("Bu işlem GERİ ALINAMAZ! Onaylıyor musunuz?")) {
                    fetch(`${API}/veritabani-sifirla`, { method: 'DELETE' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });
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
        function guncellemeKontrolEt() {
            fetch("https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/versiyon.txt", { cache: "no-store" })
                .then(r => r.ok ? r.text() : Promise.reject())
                .then(metin => {
                    const enYeni = metin.trim();
                    if (enYeni > MEVCUT_VERSIYON) {
                        if (confirm(`Programın yeni bir sürümü bulundu!\n\nSizin Sürümünüz: ${MEVCUT_VERSIYON}\nYeni Sürüm: ${enYeni}\n\nYeni sürümü indirmek ister misiniz?`)) {
                            window.open("https://github.com/ada-netizen/yoklama_otomasyonu/releases/latest", "_blank");
                        }
                    }
                })
                .catch(() => { /* İnternet yoksa veya erişilemezse sessizce devam eder */ });
        }

        window.onload = function() {
            verileriYukle();
            ayarlariYukle();
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
// ==========================================

let ihaleKalemleri = [];

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
        
        // Ekranı başlangıç durumuna döndür
        const icerik = document.getElementById("ihale_icerik");
        icerik.innerHTML = `
            <div id="ihale_baslangic_mesaj" style="color: var(--fg-sub); font-size: 15px; text-align: center; display:flex; flex-direction:column; align-items:center; gap:15px; opacity: 0.6;">
                <i data-lucide="mouse-pointer-click" width="48" height="48"></i>
                <span>Yeni bir ihale süreci başlatmak için yukarıdaki <b>"İhale Başlat"</b> butonuna tıklayın.</span>
            </div>
        `;
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
                <div class="acc-title"><i data-lucide="file-check" width="18" height="18"></i> 3. Adım: Belge Üretimi</div>
                <div class="acc-actions">
                    <i data-lucide="check-circle" class="acc-check" id="check_adim3" width="18" height="18" style="display:none; color:#10B981;"></i>
                    <i data-lucide="chevron-down" class="acc-arrow" width="18" height="18"></i>
                </div>
            </div>
            <div class="accordion-content" id="acc_adim3_icerik"></div>
        </div>
    `;
    lucide.createIcons();
    
    // Check if we need to show other steps immediately (if loading from draft)
    if (ihaleGeciciVeri.kalemler && ihaleGeciciVeri.kalemler.length > 0) {
        document.getElementById("acc_adim2").style.display = "block";
        ihaleAdim2Goster(true); // true means just render inside without auto-toggling
        // But if we want to jump to step 2, we can call toggleAcc
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
                                <button class="btn btn-dev" style="padding: 6px 12px; font-size: 13px; border-radius: 6px;" onclick="fiyatGirisModalAc('pdf')"><i data-lucide="file-text" width="14" height="14"></i> PDF Üret</button>
                                <button class="btn btn-yardim" style="padding: 6px 12px; font-size: 13px; border-radius: 6px;" onclick="fiyatGirisModalAc('excel')"><i data-lucide="table" width="14" height="14"></i> Excel Üret</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
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
                <td><input type="text" class="kalem-input" style="text-align:center;" data-field="birim" value="${k.birim}" placeholder="Adet"></td>
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

function fiyatGirisModalAc(format) {
    seciliBelgeFormat = format;
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
    let tarih = document.getElementById('tarih_yaklasik_maliyet').value;
    belgeUret('yaklasik_maliyet', seciliBelgeFormat, tarih);
}
