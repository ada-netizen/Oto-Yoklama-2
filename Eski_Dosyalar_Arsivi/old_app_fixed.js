
        // TEMA Y├£KLEME
        document.addEventListener('DOMContentLoaded', () => {
            const savedTema = localStorage.getItem('temaPref') || 'gece';
            karanlikMod = (savedTema === 'gece');
            // Wait a tiny bit for elements to exist
            setTimeout(() => temaDegistir(savedTema), 50);
        });

const API = 'http://127.0.0.1:8000';

        // --- B─░LD─░R─░M (TOAST) S─░STEM─░ ---
        function bildirimGoster(mesaj, tur) {
            if(!mesaj) return;
            if(!tur) tur = 'bilgi';
            const kutu = document.getElementById('toast_container');
            if(!kutu) { console.log(mesaj); return; }
            const toast = document.createElement('div');
            toast.className = `toast ${tur}`;
            toast.innerText = mesaj;
            kutu.appendChild(toast);
            requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add('goster')));
            setTimeout(() => {
                toast.classList.remove('goster');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        // --- Y├£KLEN─░YOR G├ûSTERGES─░ ---
        function yuklemeGoster(metin) {
            const overlay = document.getElementById('yukleniyor_overlay');
            const metinEl = document.getElementById('yukleniyor_metin');
            if(metinEl) metinEl.innerText = metin || 'Y├╝kleniyor...';
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
        let aylar = ["Ocak", "┼Şubat", "Mart", "Nisan", "May─▒s", "Haziran", "Temmuz", "A─şustos", "Eyl├╝l", "Ekim", "Kas─▒m", "Aral─▒k"];
        let karanlikMod = true;
        let siralamaSutun = 'ad_soyad'; let siralamaYon = 1; 

        // --- 1. ARAY├£Z VE MODAL Y├ûNET─░M─░ ---
        function modalAc(id) { 
            document.getElementById(id).style.display = 'flex'; 
            if(id === 'raporlar_modal') {
                const subeler = [...new Set(ogrenciListesi.map(o => sinifFormatla(o.sube)))];
                subeler.sort((a, b) => (parseInt(a)||99) - (parseInt(b)||99));
                const raporKutu = document.getElementById('rapor_sube_kutu');
                if(raporKutu) {
                    raporKutu.innerHTML = '<option>Se├ğ</option>';
                    subeler.forEach(s => raporKutu.innerHTML += `<option>${s}</option>`);
                }
            }
        }
        
        function modalKapat(id) { document.getElementById(id).style.display = 'none'; }

        
        function temaDegistir(forceState = null) {
            const root = document.documentElement; 
            const btnTema = document.getElementById('btn_tema');
            
            // E─şer forceState verilmi┼şse onu kullan (ba┼şlang─▒├ğta okumak i├ğin)
            if (forceState !== null) {
                karanlikMod = (forceState === 'gece');
            } else {
                karanlikMod = !karanlikMod; // Toggle
            }
            
            if (!karanlikMod) {
                // G├╝nd├╝z Moduna Ge├ği┼ş
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
                // Gece Moduna Ge├ği┼ş
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
            
            // Tablodaki hata h├╝crelerini tekrar boya (eski kodun par├ğas─▒)
            const dHucreler = document.querySelectorAll('#tree_tum_liste td');
            dHucreler.forEach(td => {
                if(td.textContent.includes('G├╝n)') || td.style.color === 'white' || td.style.color === 'var(--dev-fg)') {
                    td.style.backgroundColor = 'var(--dev-bg)';
                    td.style.color = 'var(--dev-fg)';
                }
            });
            const dbHucreler = document.querySelectorAll('#tree_detay_govde td');
            dbHucreler.forEach(td => {
                if(td.textContent === '├ûz├╝rs├╝z' || td.style.color === 'white' || td.style.color === 'var(--dev-fg)') {
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
        }

        function resizerAktifEt(resizerId, solId, sagId) {
            const resizer = document.getElementById(resizerId); const sol = document.getElementById(solId); const sag = document.getElementById(sagId);
            if(!resizer || !sol || !sag) return;

            // Daha ├Ânce ayarlanm─▒┼ş bir geni┼şlik varsa geri y├╝kle (ekrana g├Âre g├╝venli s─▒n─▒r i├ğinde)
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

        // ================= TABLO S├£TUN GEN─░┼ŞLETME (ZEK─░ MOTOR) =================
        function tabloSutunBoyutlandirma() {
            const resizers = document.querySelectorAll('.col-resizer');
            let thEl, startX, startWidth;

            // Daha ├Ânce ayarlanm─▒┼ş s├╝tun geni┼şliklerini geri y├╝kle
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

        // --- 2. YILLIK TABLO (EFEKT VE ├ç─░Z─░M) ---
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
            document.getElementById('modal_baslik').innerText = `Y─▒ll─▒k Devams─▒zl─▒k Karnesi - ${ad} (${no})`;
            yillikHucreler = []; 
            
            fetch(`${API}/ogrenci-detay/${no}`).then(r => r.json()).then(veri => {
                const thead = document.getElementById('yillik_thead'); const tbody = document.getElementById('yillik_tbody'); const ozetAlani = document.getElementById('yillik_ozet_alani');
                thead.innerHTML = ""; tbody.innerHTML = ""; ozetAlani.innerHTML = "";
                
                let theadHtml = `<tr><th style="background-color: #1E3A8A; color: white; padding: 6px; border: 1px solid var(--border);">Aylar</th>`;
                for(let i=1; i<=31; i++) { theadHtml += `<th id="yillik_col_${i}" style="background-color: #1E3A8A; color: white; padding: 4px; border: 1px solid var(--border); width: 25px;">${i}</th>`; }
                theadHtml += `</tr>`; thead.innerHTML = theadHtml;

                const aylarList = ["Eyl├╝l", "Ekim", "Kas─▒m", "Aral─▒k", "Ocak", "┼Şubat", "Mart", "Nisan", "May─▒s", "Haziran"]; const ayNolar = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6];
                const rH = { "D": "#DC2626", "├ûY": "#EF4444", "SY": "#F87171", "G": "#EA580C", "─░": "#EAB308", "I": "#EAB308", "S": "#F59E0B", "R": "#D97706", "M": "#92400E", "N": "#3B82F6", "F": "#6366F1", "SV": "#8B5CF6" };

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

                    if (["D", "├ûY", "SY"].includes(tur)) { detayOzursuz[tur] = (detayOzursuz[tur] || 0) + gunMiktari; hsOzursuz[tur] = (hsOzursuz[tur] || 0) + hsMiktari; ozszNet += hiMiktari; } 
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
                    if (Object.keys(detay).length === 0) { html += `<div style="text-align: center; color: var(--fg-sub); margin-top: 10px;">Kay─▒t Yok</div>`; } 
                    else {
                        for(let tur in detay) {
                            let hsGun = hsDict[tur] || 0; let hsYazi = hsGun > 0 ? ` <span style="font-size:9px;">(${hsGun} Hafta Sonu)</span>` : ''; let safTur = tur.split(" ")[0]; let rnk = rH[safTur] || 'var(--fg-sub)';
                            html += `<div style="cursor: pointer;" onmouseenter="yillikHoverEnter(null, null, '${safTur}')" onmouseleave="yillikHoverLeave()">
                                <span style="color: ${rnk}; font-weight: bold;">${tur} :</span> <span style="color: var(--fg-main); font-weight:bold;">${detay[tur]} G├╝n</span><span style="color: var(--fg-sub);">${hsYazi}</span>
                            </div>`;
                        }
                    }
                    html += `</div><div style="text-align: center; padding: 6px; font-weight: bold; font-size: 13px; color: ${fgColor}; border-top: 1px solid var(--border); background-color: var(--bg-card);">Toplam: ${net} G├╝n</div></div>`;
                    return html;
                }

                ozetAlani.innerHTML += ozetKutusuCiz("├ûz├╝rl├╝ Devams─▒zl─▒k", detayOzurlu, hsOzurlu, ozrlNet, "var(--fg-main)");
                ozetAlani.innerHTML += ozetKutusuCiz("├ûz├╝rs├╝z Devams─▒zl─▒k", detayOzursuz, hsOzursuz, ozszNet, ozszNet >= 10 ? "#DC2626" : "var(--fg-main)");
                ozetAlani.innerHTML += ozetKutusuCiz("Di─şer Devams─▒zl─▒k", detayDiger, hsDiger, digerNet, "var(--fg-main)");

                modalAc('yillik_modal');
            });
        }

        // --- 3. SA─Ş TIK MENU VE KOPYALAMA ---
        let sagTikOgrNo = ""; let sagTikOgrAd = "";
        function sagTikMenuAc(e, no, ad) {
            e.preventDefault(); sagTikOgrNo = no; sagTikOgrAd = ad;
            const menu = document.getElementById('sag_tik_menu');
            if(menu) { menu.style.display = 'flex'; menu.style.left = e.pageX + 'px'; menu.style.top = e.pageY + 'px'; }
        }
        function kopyalaNo() { navigator.clipboard.writeText(sagTikOgrNo); bildirimGoster("Numara kopyaland─▒!", "bilgi"); }
        function kopyalaAd() { navigator.clipboard.writeText(sagTikOgrAd); bildirimGoster("Ad Soyad kopyaland─▒!", "bilgi"); }
        function ogrenciyiTamamenSil() {
            if(!confirm(`${sagTikOgrAd} kal─▒c─▒ olarak silinecek. Onayl─▒yor musunuz?`)) return;
            fetch(`${API}/ogrenci-sil/${sagTikOgrNo}`, { method: 'DELETE' }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); verileriYukle();
                document.getElementById('sag_bos_uyari').style.display = 'flex'; document.getElementById('sag_dolu_icerik').style.display = 'none';
            });
        }

        // --- 4. ANA TABLO, ZEK─░ FORMATLAYICI VE TAKV─░M ---
        function sinifFormatla(orj) {
            if(!orj) return "-";
            // 1. ├ûnce parantez i├ğindeki her ┼şeyi /(.*?)/ toptan siler (├Ârn: "(Alan─▒ Yok)").
            // 2. Sonra s─▒n─▒f/┼şube yaz─▒lar─▒n─▒ siler.
            // 3. En son aradaki bo┼şluklar─▒ ve noktalar─▒ temizler.
            return orj.replace(/\(.*?\)/g, '')
                      .replace(/s─▒n─▒f─▒/ig, '')
                      .replace(/s─▒n─▒f/ig, '')
                      .replace(/sinifi/ig, '')
                      .replace(/sinif/ig, '')
                      .replace(/┼şubesi/ig, '')
                      .replace(/subesi/ig, '')
                      .replace(/┼şube/ig, '')
                      .replace(/sube/ig, '')
                      .replace(/[\.\s]/g, '')
                      .toUpperCase();
        }
        
        function sirala(sutun) {
            if (siralamaSutun === sutun) siralamaYon *= -1; else { siralamaSutun = sutun; siralamaYon = 1; }
            tabloyuDoldur();
        }
        function basliklariGuncelle() {
            const basliklar = { 'temizSube': 'S─▒n─▒f', 'no': 'No', 'ad_soyad': 'Ad Soyad', 'ozsz': '├ûz├╝rs├╝z', 'ozrl': '├ûz├╝rl├╝' };
            for(let key in basliklar) { let el = document.getElementById('span_' + key); if(el) el.innerText = basliklar[key] + (siralamaSutun === key ? (siralamaYon === 1 ? ' Ôû▓' : ' Ôû╝') : ' Ôåò'); }
        }
        function dosyaYukle(endpoint, event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Excel dosyas─▒ i┼şleniyor...");
            fetch(`${API}/${endpoint}`, { method: 'POST', body: formData }).then(r => r.json()).then(v => { 
                if(v.basarili) { bildirimGoster(v.mesaj, "bilgi"); verileriYukle(); } else { bildirimGoster("Hata: " + v.mesaj, "hata"); }
                event.target.value = ''; 
            }).catch(err => { bildirimGoster("Ba─şlant─▒ hatas─▒! Sunucuyu kontrol edin.", "hata"); }).finally(() => yuklemeGizle());
        }
        function filtreTemizle() { document.getElementById('ent_arama').value = ""; document.getElementById('combo_arama_sube').value = "T├╝m├╝"; tabloyuDoldur(); }

        function tabloyuDoldur() {
            const arama = document.getElementById('ent_arama') ? document.getElementById('ent_arama').value.toUpperCase() : "";
            const subeFiltre = document.getElementById('combo_arama_sube') ? document.getElementById('combo_arama_sube').value : "T├╝m├╝";
            const govde = document.getElementById('tree_govde'); if(!govde) return;
            govde.innerHTML = ""; basliklariGuncelle();

            let islenecekler = ogrenciListesi.map(ogr => {
                let temizSube = sinifFormatla(ogr.sube);
                return { ...ogr, temizSube: temizSube, ozsz: Math.round((ogr.ozursuz || 0)*10)/10, ozrl: Math.round((ogr.ozurlu || 0)*10)/10 };
            }).filter(ogr => {
                if (subeFiltre !== "T├╝m├╝" && ogr.temizSube !== subeFiltre) return false;
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
                const ozszStr = ogr.ozsz >= 10 ? `<span style="font-weight:bold; color:#EF4444;">${ogr.ozsz} G├╝n</span>` : `${ogr.ozsz} G├╝n`;
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
                // Ta┼şan yaz─▒lar─▒ ... olarak g├Âstermek i├ğin CSS eklendi
                // Ta┼şan yaz─▒lar─▒ ... olarak g├Âstermek i├ğin CSS eklendi ve BOLD etiketleri silindi
                tr.innerHTML = `<td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.temizSube}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.no}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ad_soyad}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ozszStr}</td><td style="padding: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${ogr.ozrl} G├╝n</td>`;
                govde.appendChild(tr);
            });
        }

        function ogrenciSec(no, ad, ozsz, ozrl) {
            seciliOgrenci = { no: no, ad: ad, ozsz: parseFloat(ozsz || 0), ozrl: parseFloat(ozrl || 0) };
            document.getElementById('sag_bos_uyari').style.display = 'none'; 
            document.getElementById('sag_dolu_icerik').style.display = 'flex';
            
            // E─şer sildi─şin HTML elementleri sayfada yoksa program─▒n ├ğ├Âkmesini engelliyoruz (G├╝venlik Z─▒rh─▒)
            let lblAd = document.getElementById('lbl_secili_ogrenci');
            if(lblAd) lblAd.innerText = `${ad} (${no})`;
            
            let lblOzet = document.getElementById('lbl_ozet');
            if(lblOzet) {
                lblOzet.innerText = `├ûz├╝rs├╝z: ${ozsz} | ├ûz├╝rl├╝: ${ozrl}`;
                lblOzet.style.color = ozsz >= 10 ? '#DC2626' : 'var(--fg-sub)';
            }

            // ├ç├Âkme ya┼şanmad─▒─ş─▒ i├ğin devams─▒zl─▒klar─▒ veritaban─▒ndan sorunsuz ├ğekecek
            fetch(`${API}/ogrenci-detay/${no}`).then(res => res.json()).then(veri => {
                seciliDevamsizliklar = veri.devamsizliklar.map(d => ({...d, secili: false})); geciciDevamsizliklar = []; takvimiCiz(); onizlemeGuncelle();
            });
        }

        function ayDegistir(artis) { calMonth += artis; if (calMonth > 11) { calMonth = 0; calYear++; } else if (calMonth < 0) { calMonth = 11; calYear--; } takvimiCiz(); }

        function takvimiCiz() {
            document.getElementById('lbl_ay_yil').innerText = `${aylar[calMonth]} ${calYear}`;
            const grid = document.getElementById('takvim_grid');
            grid.innerHTML = `<div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Pzt</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Sal</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">├çar</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Per</div><div style="text-align: center; font-weight: bold; font-size: 11px; color: var(--fg-main); margin-bottom: 5px;">Cum</div>`;
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
                
                let hedefKayitlar = tumKayitlar.filter(k => k.tarih === tarihStr && ['D', '├ûY', 'SY'].includes(k.tur.toUpperCase()));
                let kayit = hedefKayitlar.length > 0 ? (hedefKayitlar.find(k => k.secili) || hedefKayitlar[hedefKayitlar.length - 1]) : null;
                
                let borderStyle = 'border: 1px solid var(--border);'; 
                // YEN─░: Bo┼ş g├╝nlere bembeyaz olmak yerine hafif sekmelerdeki gri tonu verdik
                let bgStyle = 'background-color: var(--bg-main);'; 
                let fgStyle = ''; 
                let icerik = '<div></div>'; 
                
                if (kayit) {
                    let tur = kayit.tur.toUpperCase();
                    // YEN─░: K─▒rm─▒z─▒ rengi art─▒k JS de─şil CSS (temaDegistir'deki de─şi┼şkenler) y├Ânetiyor!
                    bgStyle = 'background-color: var(--dev-bg);'; 
                    fgStyle = 'var(--dev-fg)';
                    icerik = `<div style="font-size: 12px; font-weight: bold; text-align: center; color: ${fgStyle};">${kayit.gun} ${tur}</div>`;
                    if(kayit.secili) borderStyle = 'border: 2px solid #10B981; box-shadow: inset 0 0 5px #10B981;';
                }
                grid.innerHTML += `<div class="gun-hucre" style="${bgStyle} ${borderStyle}" onclick="hucreTikla('${tarihStr}')" oncontextmenu="hucreSagTikla(event, '${tarihStr}')"><div style="color: ${fgStyle || 'var(--fg-main)'};">${i}</div>${icerik}</div>`;
            }
        }

        function hucreTikla(tarihStr) {
            let kalici = seciliDevamsizliklar.find(d => d.tarih === tarihStr && ['D', '├ûY', 'SY'].includes(d.tur.toUpperCase()));
            if (kalici) { kalici.secili = !kalici.secili; takvimiCiz(); onizlemeGuncelle(); return; }

            let gecici = geciciDevamsizliklar.find(d => d.tarih === tarihStr);
            if (!gecici) { geciciDevamsizliklar.push({id: 'temp_'+Date.now(), tarih: tarihStr, tur: 'D', gun: '1', secili: true}); } 
            else {
                if(gecici.tur === 'D') { gecici.tur = 'SY'; gecici.gun = '0.5'; }
                else if(gecici.tur === 'SY') { gecici.tur = '├ûY'; gecici.gun = '0.5'; }
                else if(gecici.tur === '├ûY') { geciciDevamsizliklar = geciciDevamsizliklar.filter(d => d.tarih !== tarihStr); }
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
            
            // Hesaplama De─şi┼şkenleri
            let donusenGecmisGun = 0.0; 
            let yeniEklenenGun = 0.0;

            const gosterilecek = [...seciliDevamsizliklar, ...geciciDevamsizliklar].filter(d => d.secili).sort((a,b) => {
                let pa = a.tarih.split('/').reverse().join(''); let pb = b.tarih.split('/').reverse().join(''); return pb.localeCompare(pa);
            });

            gosterilecek.forEach(d => {
                let miktar = parseFloat(d.gun) || 0;
                toplamGun += miktar;
                
                // E─şer bu devams─▒zl─▒k zaten varsa (E-Okul'dan geldiyse ve temp_ ile ba┼şlam─▒yorsa) ├ûz├╝rs├╝z'den d├╝┼şecek
                if(!d.id || !d.id.toString().startsWith('temp_')) { donusenGecmisGun += miktar; } 
                // E─şer yepyeni bir kutuya t─▒klayarak olu┼şturulduysa (temp_ ise) sadece ├ûz├╝rl├╝'ye eklenecek
                else { yeniEklenenGun += miktar; }
                
                govde.innerHTML += `<tr id="onizleme_tr_${d.id}" onclick="onizlemeSatirSec('${d.id}')" style="cursor: pointer; border-bottom: 1px solid var(--border);">
                    <td style="padding: 6px; color: var(--fg-main);">${d.tarih}</td><td style="padding: 6px; color: var(--fg-main);"><b>${d.tur}</b></td><td style="padding: 6px; color: var(--fg-main);">${d.gun}</td>
                </tr>`;
            });
            document.getElementById('lbl_onizleme_toplam').innerText = `Toplam: ${toplamGun} G├╝n`;

            // Yeni Kutular─▒n Matematik ─░┼şlemi ve Ekrana Bas─▒lmas─▒
            if (seciliOgrenci) {
                let kalanOzursuz = seciliOgrenci.ozsz - donusenGecmisGun;
                if(kalanOzursuz < 0) kalanOzursuz = 0; // Eksiye inmesini engeller
                
                let guncelOzurlu = seciliOgrenci.ozrl + donusenGecmisGun + yeniEklenenGun;
                
                const lblKalan = document.getElementById('lbl_kalan_ozursuz');
                const lblYeni = document.getElementById('lbl_yeni_ozurlu');
                if(lblKalan) lblKalan.innerText = (Math.round(kalanOzursuz * 10) / 10) + ' G├╝n';
                if(lblYeni) lblYeni.innerText = (Math.round(guncelOzurlu * 10) / 10) + ' G├╝n';
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
                if(!['D', '├ûY', 'SY'].includes(d.tur.toUpperCase())) return;
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
            grid.innerHTML = `<div style="color:var(--fg-sub)">Pt</div><div style="color:var(--fg-sub)">Sa</div><div style="color:var(--fg-sub)">├ça</div><div style="color:var(--fg-sub)">Pe</div><div style="color:var(--fg-sub)">Cu</div><div style="color:var(--fg-sub)">Ct</div><div style="color:var(--fg-sub)">Pz</div>`;

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
            if(!ozelBas) bilgi.innerHTML = "<b>1. Ad─▒m:</b> Ba┼şlang─▒├ğ tarihini se├ğin.";
            else if(!ozelBit) bilgi.innerHTML = "<b>2. Ad─▒m:</b> Biti┼ş tarihini se├ğin.";
            else bilgi.innerHTML = "<b>Harika!</b> Aral─▒─ş─▒ aktarabilirsiniz.";
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
            if(!ozelBas || !ozelBit) { bildirimGoster("L├╝tfen takvimden iki tarih se├ğin (Ba┼şlang─▒├ğ ve Biti┼ş).", "hata"); return; }
            if(!seciliOgrenci) return;
            seciliDevamsizliklar.forEach(d => d.secili = false);
            
            const parseTarihStr = (str) => { let p = str.split('/'); return p.length === 3 ? new Date(p[2], p[1]-1, p[0]) : null; };
            
            let eklenen = 0;
            seciliDevamsizliklar.forEach(d => {
                if(!['D', '├ûY', 'SY'].includes(d.tur.toUpperCase())) return;
                let kDate = parseTarihStr(d.tarih); 
                if(kDate && kDate >= ozelBas && kDate <= ozelBit) { d.secili = true; eklenen++; }
            });
            
            takvimiCiz(); onizlemeGuncelle();
            document.getElementById('float_takvim').style.display = 'none';
            if(eklenen === 0) bildirimGoster("Se├ğilen tarih aral─▒─ş─▒nda ├Âz├╝rs├╝z devams─▒zl─▒k bulunamad─▒.", "hata");
        }

        function verileriYukle() {
            fetch(`${API}/ogrenciler`).then(res => res.json()).then(veri => {
                ogrenciListesi = veri.ogrenciler;
                let temizSubeler = [...new Set(ogrenciListesi.map(o => sinifFormatla(o.sube)))];
                temizSubeler.sort((a, b) => (parseInt(a)||99) - (parseInt(b)||99));
                const combo = document.getElementById('combo_arama_sube');
                if(combo) {
                    const eskiSecim = combo.value;
                    combo.innerHTML = '<option value="T├╝m├╝">T├╝m├╝</option>';
                    temizSubeler.forEach(sube => { combo.innerHTML += `<option value="${sube}">${sube}</option>`; });
                    combo.value = eskiSecim || "T├╝m├╝";
                }
                tabloyuDoldur();
            });
        }
        
        function pdfCiktisiAl() {
            if(!seciliOgrenci) return;
            const kayitlar = [...seciliDevamsizliklar, ...geciciDevamsizliklar].filter(d => d.secili);
            if(kayitlar.length === 0) { bildirimGoster("├ûnizleme listesinde yazd─▒r─▒lacak kay─▒t yok!", "hata"); return; }
            
            const geciciler = kayitlar.filter(d => d.id.startsWith('temp_'));
            if(geciciler.length > 0) {
                bildirimGoster("Manuel girdi─şiniz kay─▒tlar veritaban─▒na i┼şleniyor, ard─▒ndan PDF olu┼şturulacakt─▒r.", "bilgi");
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
        
        // --- 5. YAZI TEBL─░─Ş─░ VE AYARLAR ---
               
        function personelleriYukle() {
            return fetch(`${API}/personeller`).then(res => res.json()).then(veri => {
                // Herkes se├ğili DE─Ş─░L ve manuel olarak da eklenmemi┼ş ┼şekilde (tertemiz) ba┼şlar.
                tumPersoneller = veri.personeller.map(p => ({ ...p, secili: false, manuelEklendi: false }));
                
                const cbEden = document.getElementById('b-eden'); const cbEdilen = document.getElementById('b-edilen');
                if(cbEden && cbEdilen) {
                    cbEden.innerHTML = '<option value="">-- ─░dareci Se├ğin --</option>';
                    cbEdilen.innerHTML = '<option value="">-- Personel Se├ğin --</option>';
                    tumPersoneller.forEach(p => {
                        cbEdilen.innerHTML += `<option value="${p.ad}">${p.ad}</option>`;
                        if(p.grup === '─░dare' || p.gorev.includes('M├£D├£R')) { cbEden.innerHTML += `<option value="${p.ad}">${p.ad}</option>`; }
                    });
                }
                personelFiltrePanelDoldur(); 
                personelTablosunuDoldur(); 
            });
        }

        function personelFiltrePanelDoldur() {
            const gorevPanel = document.getElementById('personel_gorev_panel');
            const bransPanel = document.getElementById('personel_brans_panel');
            if(!gorevPanel || !bransPanel) return;

            let gorevler = [...new Set(tumPersoneller.map(p => p.gorev))].filter(g => g !== "-").sort();
            let branslar = [...new Set(tumPersoneller.map(p => p.brans))].filter(b => b !== "-").sort();

            let gHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('gorev')">­şöä Listedekilerin Hepsini Ekle/├ç─▒kar</div>`;
            gorevler.forEach((g, i) => {
                gHtml += `<label class="personel-filtre-item" style="display:flex; gap:5px; width:100%;"><input type="checkbox" onchange="filtreleriHesapla()" data-deger="${g.replace(/"/g, '&quot;')}"> <span>${g}</span></label>`;
            });
            gorevPanel.innerHTML = gHtml;

            let bHtml = `<div class="personel-filtre-item personel-filtre-toplu" onclick="personelFiltreTopluUygula('brans')">­şöä Listedekilerin Hepsini Ekle/├ç─▒kar</div>`;
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
                if (grp_idare && p.grup === '─░dare') uyarMi = true;
                if (grp_ogr && p.grup === '├û─şretmenler') uyarMi = true;
                if (grp_diger && p.grup === 'Di─şer Personel') uyarMi = true;
                if (seciliGorevler.includes(p.gorev)) uyarMi = true;
                if (seciliBranslar.includes(p.brans)) uyarMi = true;

                if (uyarMi) {
                    p.secili = true;
                } else if (!p.manuelEklendi) {
                    // Ki┼şi art─▒k hi├ğbir filtreye uymuyorsa ve "arama kutusundan" manuel se├ğilmediyse listeden ├ğ─▒kar─▒l─▒r.
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
                p.manuelEklendi = cbElement.checked; // Arama ile eklediyse filtreler de─şi┼şince u├ğmas─▒n diye haf─▒zaya al─▒n─▒yor
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

        function personelTablosunuDoldur() {
            const govde = document.getElementById('personel-govde');
            if(!govde) return;
            const arama = (document.getElementById('personel_ara') ? document.getElementById('personel_ara').value : "").toUpperCase();

            let gosterilecekler;
            if (arama) {
                // Arama kutusu doluysa, herkes i├ğinde arama yapar (ki┼şiyi an─▒nda ekleyebilmen i├ğin)
                gosterilecekler = tumPersoneller.filter(p =>
                    p.ad.toUpperCase().includes(arama) || p.gorev.toUpperCase().includes(arama) ||
                    p.brans.toUpperCase().includes(arama) || p.grup.toUpperCase().includes(arama)
                );
            } else {
                // Arama bo┼şsa sadece se├ğili/filtreli ki┼şileri g├Âsterir
                gosterilecekler = tumPersoneller.filter(p => p.secili);
            }

            govde.innerHTML = "";
            if(tumPersoneller.length === 0) { govde.innerHTML = "<tr><td colspan='5' style='text-align:center; padding:10px; color:var(--fg-sub);'>Personel bulunamad─▒.</td></tr>"; return; }
            if(gosterilecekler.length === 0) {
                govde.innerHTML = arama
                    ? "<tr><td colspan='5' style='text-align:center; padding:10px; color:var(--fg-sub);'>Aramayla e┼şle┼şen personel bulunamad─▒.</td></tr>"
                    : "<tr><td colspan='5' style='text-align:center; padding:25px; color:var(--fg-sub); font-size:12px;'>Listeniz ┼şu an bo┼ş.<br><br>Yukar─▒daki h─▒zl─▒ filtreleri i┼şaretleyerek veya arama kutusunu kullanarak<br>personelleri listeye ekleyebilirsiniz.</td></tr>";
                personelSayaciGuncelle();
                const masterKutu = document.getElementById('chk_master_personel');
                if(masterKutu) masterKutu.checked = false;
                return;
            }

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
            
            personelSayaciGuncelle();
        }

        function personelSayaciGuncelle() {
            let seciliSayi = tumPersoneller.filter(p => p.secili).length;
            const lbl = document.getElementById('lbl_secili_personel_sayisi');
            if(lbl) { lbl.innerText = `Se├ğili: ${seciliSayi} Ki┼şi`; lbl.style.color = seciliSayi > 0 ? '#10B981' : '#EF4444'; }
        }

        function personelFiltrePanelAcKapa(tur) {
            const digerTur = tur === 'gorev' ? 'brans' : 'gorev';
            const digerPanel = document.getElementById(`personel_${digerTur}_panel`);
            if(digerPanel) digerPanel.classList.remove('acik');
            const panel = document.getElementById(`personel_${tur}_panel`);
            if(panel) panel.classList.toggle('acik');
        }

        function topluTebligPdfAl() {
            // YEN─░: Art─▒k ekrandaki tikleri de─şil, do─şrudan haf─▒zadaki se├ğili ki┼şileri al─▒yoruz
            const seciliPersoneller = tumPersoneller.filter(p => p.secili);
            if(seciliPersoneller.length === 0) return bildirimGoster("L├╝tfen en az bir personel se├ğin!", "hata");
            
           const veri = { 
                sayi: document.getElementById('t-sayi').value, 
                konu: document.getElementById('t-konu').value, 
                tarih: document.getElementById('t-tarih').value, 
                kurum: document.getElementById('t-kurum') ? document.getElementById('t-kurum').value : "",
                gecici_pdf_yolu: document.getElementById('t-pdf-yol') ? document.getElementById('t-pdf-yol').value : "", // YEN─░ EKLEND─░
                personeller: seciliPersoneller 
            };
            fetch(`${API}/teblig-toplu-pdf`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"));
        }
        
        function bireyselTebligPdfAl() {
            const edenSecim = document.getElementById('b-eden');
            const edilenSecim = document.getElementById('b-edilen');
            if(edenSecim.selectedIndex < 0 || edilenSecim.selectedIndex < 0) return bildirimGoster("L├╝tfen tebli─ş eden ve edilen ki┼şileri se├ğin!", "hata");
            
            const edenAd = edenSecim.value;
            const edilenAd = edilenSecim.value;
            
            const edenPersonel = tumPersoneller.find(p => p.ad === edenAd);
            const edilenPersonel = tumPersoneller.find(p => p.ad === edilenAd);
            
            const edenGorev = edenPersonel ? edenPersonel.gorev : "─░dareci";
            const edilenGorev = edilenPersonel ? edilenPersonel.gorev : "Personel";
            
            const veri = { 
                sayi: document.getElementById('t-sayi') ? document.getElementById('t-sayi').value : "", 
                konu: document.getElementById('t-konu') ? document.getElementById('t-konu').value : "", 
                tarih: document.getElementById('t-tarih') ? document.getElementById('t-tarih').value : "", 
                kurum: document.getElementById('t-kurum') ? document.getElementById('t-kurum').value : "",
                eden: { ad: edenAd, gorev: edenGorev },
                edilen: { ad: edilenAd, gorev: edilenGorev },
                yer: document.getElementById('b-yer').value,
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

         // --- PDF OKUMA MOTORU (Zeki Uyar─▒ Sistemi Eklendi) ---
        function mebPdfYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("MEB Yaz─▒s─▒ ├ç├Âz├╝mleniyor...");
            
            fetch(`${API}/meb-pdf-oku`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                yuklemeGizle();
                if(v.basarili) {
                    document.getElementById('t-sayi').value = v.sayi || '';
                    document.getElementById('t-konu').value = v.konu || '';
                    document.getElementById('t-tarih').value = v.tarih || '';
                    if(document.getElementById('t-kurum')) document.getElementById('t-kurum').value = v.kurum || '';
                    if(document.getElementById('t-pdf-yol')) document.getElementById('t-pdf-yol').value = v.gecici_pdf_yolu || ''; // YEN─░ EKLEND─░
                    if(document.getElementById('t-kurum')) document.getElementById('t-kurum').value = v.kurum || '';
                    
                    // YEN─░ EKLENEN KISIM: E─şer program hi├ğbir veri bulamad─▒ysa kullan─▒c─▒y─▒ uyar─▒r
                    if (!v.sayi && !v.konu && !v.tarih) {
                        bildirimGoster("ÔÜá´©Å Belge haf─▒zaya al─▒nd─▒ ancak i├ğindeki metinler okunamad─▒ (Taranm─▒┼ş/Resim tabanl─▒ PDF olabilir). L├╝tfen bilgileri elle giriniz.", "hata");
                    } else {
                        bildirimGoster("PDF Ba┼şar─▒yla Okundu", "bilgi");
                        // PDF'in Konusunu okuyup yapay zeka motorunu tetikledi─şimiz an!
                        otomatikPersonelSec(v.konu);
                    }
                } else {
                    bildirimGoster("Hata: " + v.mesaj, "hata");
                }
                event.target.value = '';
            }).catch(() => { yuklemeGizle(); bildirimGoster("Ba─şlant─▒ hatas─▒!", "hata"); });
        }

        // --- PERSONEL Y├ûNET─░M─░ ---
        function personelExcelYukle(event) {
            const dosya = event.target.files[0]; if (!dosya) return;
            const formData = new FormData(); formData.append("dosya", dosya);
            yuklemeGoster("Personel listesi i┼şleniyor...");
            fetch(`${API}/personel-excel-yukle`, { method: 'POST', body: formData }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); if(v.basarili) personelleriYukle();
                event.target.value = '';
            }).catch(() => bildirimGoster("Ba─şlant─▒ hatas─▒! Sunucuyu kontrol edin.", "hata")).finally(() => yuklemeGizle());
        }

        function personelYonetimAc() { modalAc('personel_yonetim_modal'); personelTabAc('ekle'); }

        // --- ­şğá GEL─░┼ŞM─░┼Ş AKILLI E┼ŞLE┼ŞT─░RME MOTORU ---
        function aeTurDegisti() {
            const tur = document.getElementById('ae_tur').value;
            const secici = document.getElementById('ae_hedef');
            if(!secici) return;
            secici.innerHTML = '';
            
            let secenekler = [];
            if(tur === 'kisi') {
                secenekler = [...tumPersoneller].map(p => p.ad).sort();
            } else if(tur === 'grup') {
                secenekler = ['─░dare', '├û─şretmenler', 'Di─şer Personel'];
            } else if(tur === 'gorev') {
                secenekler = [...new Set(tumPersoneller.map(p => p.gorev))].filter(g => g !== "-").sort();
            } else if(tur === 'brans') {
                secenekler = [...new Set(tumPersoneller.map(p => p.brans))].filter(b => b !== "-").sort();
            }
            secenekler.forEach(s => secici.innerHTML += `<option value="${s.replace(/"/g, '&quot;')}">${s}</option>`);
        }

        function akilliEslesmeModalAc() {
            if(!sistemAyarlari.oto_eslesmeler) sistemAyarlari.oto_eslesmeler = [];
            
            // E─şer personeller hen├╝z y├╝klenmediyse, ├Ânce y├╝kleyip sonra pencereyi a├ğar
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
            if(!kelime || !hedef) return bildirimGoster("L├╝tfen alanlar─▒ tam doldurun!", "hata");
            
            if(!sistemAyarlari.oto_eslesmeler) sistemAyarlari.oto_eslesmeler = [];
            sistemAyarlari.oto_eslesmeler.push({ kelime: kelime, tur: tur, hedef: hedef });
            
            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sistemAyarlari) })
            .then(r => r.json()).then(v => {
                bildirimGoster("Kural ba┼şar─▒yla eklendi!", "bilgi");
                document.getElementById('ae_kelime').value = '';
                akilliEslesmeCiz();
            });
        }

        function akilliEslesmeCiz() {
            const liste = document.getElementById('ae_liste');
            if(!liste) return;
            liste.innerHTML = '';
            if(!sistemAyarlari.oto_eslesmeler || sistemAyarlari.oto_eslesmeler.length === 0) {
                liste.innerHTML = '<div style="padding:15px; text-align:center; color:var(--fg-sub); font-size:11px;">Hen├╝z kural eklenmemi┼ş.</div>';
                return;
            }
            const turIsimleri = { 'kisi': 'Ki┼şi', 'grup': 'Grup', 'gorev': 'G├Ârev', 'brans': 'Bran┼ş' };
            
            sistemAyarlari.oto_eslesmeler.forEach((kural, i) => {
                let gTur = kural.tur ? turIsimleri[kural.tur] : 'Ki┼şi';
                let gHedef = kural.hedef || kural.personel;
                
                liste.innerHTML += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border-bottom:1px solid var(--border); font-size:11px; color: var(--fg-main);">
                    <div><strong style="color: #8B5CF6;">Kelime:</strong> ${kural.kelime} <br> <strong style="color:var(--tree-sel);">${gTur}:</strong> ${gHedef}</div>
                    <button class="btn btn-kirmizi" style="padding:4px 10px; font-size:9px;" onclick="akilliEslesmeSil(${i})">Sil</button>
                </div>`;
            });
        }

        function akilliEslesmeSil(index) {
            if(!confirm("Kural─▒ silmek istedi─şinize emin misiniz?")) return;
            sistemAyarlari.oto_eslesmeler.splice(index, 1);
            fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sistemAyarlari) })
            .then(r => r.json()).then(v => { bildirimGoster("Kural silindi!", "bilgi"); akilliEslesmeCiz(); });
        }

        // --- 1. T├£M├£N├£ SE├ç/L─░STELE MOTORU ---
        function filtreTumuDegisti() {
            const tumu = document.getElementById('grp_tumu').checked;
            // Di─şer t├╝m gruplar─▒ otomatik olarak i┼şaretle
            if(document.getElementById('grp_idare')) document.getElementById('grp_idare').checked = tumu;
            if(document.getElementById('grp_ogretmenler')) document.getElementById('grp_ogretmenler').checked = tumu;
            if(document.getElementById('grp_diger')) document.getElementById('grp_diger').checked = tumu;
            
            // T├╝m personeli manuelEklendi yap ki listeden silinmesinler
            tumPersoneller.forEach(p => p.secili = tumu);
            personelTablosunuDoldur();
        }

        function filtreleriHesapla() {
            const grp_idare = document.getElementById('grp_idare').checked;
            const grp_ogr = document.getElementById('grp_ogretmenler').checked;
            const grp_diger = document.getElementById('grp_diger').checked;

            // Master checkbox kontrol├╝
            if (document.getElementById('grp_tumu')) 
                document.getElementById('grp_tumu').checked = (grp_idare && grp_ogr && grp_diger);

            tumPersoneller.forEach(p => {
                let uyarMi = false;
                if (grp_idare && p.grup === '─░dare') uyarMi = true;
                if (grp_ogr && p.grup === '├û─şretmenler') uyarMi = true;
                if (grp_diger && p.grup === 'Di─şer Personel') uyarMi = true;

                if (uyarMi) p.secili = true;
                else if (!p.manuelEklendi) p.secili = false;
            });
            personelTablosunuDoldur();
        }

        // --- 2. G├ûREV VE BRAN┼Ş ─░├ç─░N "ARAMA ─░├ç─░NDE F─░LTRE" MANTI─ŞI ---
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
                govde.innerHTML = "<tr><td colspan='5' style='text-align:center; padding:25px; color:var(--fg-sub); font-size:12px;'>Liste bo┼ş.<br>─░dare/├û─şretmen kutular─▒n─▒ i┼şaretleyin veya personeli bulmak i├ğin arama yap─▒n.</td></tr>";
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
                bildirimGoster(`­şğá Ak─▒ll─▒ E┼şle┼şme ├çal─▒┼şt─▒!\n${secilenAdlar.length} personel (Grup/Bran┼ş) otomatik se├ğildi.`, "bilgi");
            }
        }

        // --- PDF OKUMA MOTORUNUN G├£NCELLENM─░┼Ş HAL─░ ---
        
        function personelTabAc(tab) {
            document.getElementById('ptab-ekle').style.display = tab === 'ekle' ? 'flex' : 'none';
            document.getElementById('ptab-cikar').style.display = tab === 'cikar' ? 'flex' : 'none';
            document.getElementById('ptab-ekle-btn').classList.toggle('aktif', tab === 'ekle');
            document.getElementById('ptab-cikar-btn').classList.toggle('aktif', tab === 'cikar');
            if(tab === 'cikar') personelCikarListesiDoldur();
        }

        function personelEkle() {
            const ad = document.getElementById('p-ekle-ad').value.trim();
            if(!ad) return bildirimGoster("Ad Soyad bo┼ş b─▒rak─▒lamaz!", "hata");
            const veri = { ad: ad, gorev: document.getElementById('p-ekle-gorev').value.trim(), brans: document.getElementById('p-ekle-brans').value.trim(), grup: document.getElementById('p-ekle-grup').value };
            fetch(`${API}/personel-ekle`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                if(v.basarili) { document.getElementById('p-ekle-ad').value = ''; document.getElementById('p-ekle-gorev').value = ''; document.getElementById('p-ekle-brans').value = ''; personelleriYukle(); }
            });
        }

        function personelCikarListesiDoldur() {
            const filtre = document.getElementById('p-cikar-ara').value.toUpperCase();
            const kutu = document.getElementById('p-cikar-liste'); kutu.innerHTML = '';
            [...tumPersoneller].sort((a,b) => a.ad.localeCompare(b.ad)).forEach(p => {
                if(filtre && !p.ad.toUpperCase().includes(filtre)) return;
                const satir = document.createElement('div');
                satir.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:8px 10px; border-bottom:1px solid var(--border); font-size:11px; color: var(--fg-main);';
                satir.innerHTML = `<span>${p.ad}</span><button class="btn btn-kirmizi" style="padding:3px 10px; font-size:9px;">Sil</button>`;
                satir.querySelector('button').onclick = () => personelSil(p.ad);
                kutu.appendChild(satir);
            });
            if(kutu.innerHTML === '') kutu.innerHTML = '<div style="padding:15px; text-align:center; color:var(--fg-sub); font-size:11px;">Personel bulunamad─▒.</div>';
        }

        function personelSil(ad) {
            if(!confirm(`${ad} silinecek. Onayl─▒yor musunuz?`)) return;
            fetch(`${API}/personel-sil/${encodeURIComponent(ad)}`, { method: 'DELETE' }).then(r => r.json()).then(v => {
                bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata");
                personelleriYukle().then(() => personelCikarListesiDoldur());
            });
        }

        // --- RAPORLAR ---
        function raporAl(tur, format, ozelDeger) {
            if((tur === 'gun_siniri' || tur === 'sube_bazli' || tur === 'tarih_bazli') && !ozelDeger) {
                return bildirimGoster("L├╝tfen rapor almadan ├Ânce bir se├ğim yap─▒n─▒z!", "hata");
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
                if(!v.yedekler || v.yedekler.length === 0) { kutu.innerHTML = '<option value="">Yedek dosyas─▒ bulunamad─▒</option>'; return; }
                kutu.innerHTML = v.yedekler.map(y => `<option value="${y.dosya_adi}">${y.tarih} (${y.boyut_kb} KB)</option>`).join('');
            });
        }

        function yedekGeriYukle() {
            const secim = document.getElementById('ayar_yedek_secim').value;
            if(!secim) return bildirimGoster("L├╝tfen bir yedek dosyas─▒ se├ğin.", "hata");
            if(!confirm("Mevcut veriler silinecek ve se├ğilen yedekteki veriler y├╝klenecek.\n\nBu i┼şlemi onayl─▒yor musunuz?")) return;
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
                if(document.getElementById('ayar_yedek_sikligi')) document.getElementById('ayar_yedek_sikligi').value = v.ayarlar.yedek_sikligi || 'Her G├╝n';
                if(document.getElementById('ayar_yedek_gun_sayisi')) document.getElementById('ayar_yedek_gun_sayisi').value = v.ayarlar.yedek_gun_sayisi || 3;
                if(document.getElementById('ayar_yedek_gun_sayisi_satir')) document.getElementById('ayar_yedek_gun_sayisi_satir').style.display = (v.ayarlar.yedek_sikligi === '├ûzel G├╝n') ? 'flex' : 'none';
                if(document.getElementById('ayar_meb_logo_ad')) document.getElementById('ayar_meb_logo_ad').innerText = v.ayarlar.meb_logosu ? v.ayarlar.meb_logosu.split(/[\\/]/).pop() : 'Y├╝klenmedi';
                if(document.getElementById('ayar_okul_logo_ad')) document.getElementById('ayar_okul_logo_ad').innerText = v.ayarlar.okul_logosu ? v.ayarlar.okul_logosu.split(/[\\/]/).pop() : 'Y├╝klenmedi';
                yedekleriListele();

                // ─░lk kullan─▒m kar┼ş─▒lama mesaj─▒ ve MEB logosu uyar─▒s─▒
                if (v.ayarlar.ilk_kullanim !== false) {
                    bildirimGoster("Sisteme Ho┼ş Geldiniz! ├ûnce Ayarlar men├╝s├╝nden PDF kay─▒t yerini se├ğiniz.", "bilgi");
                    fetch(`${API}/ayarlar-kaydet`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ilk_kullanim: false }) });
                } else if (!v.ayarlar.meb_logosu) {
                    setTimeout(() => bildirimGoster("MEB Logosu bulunamad─▒! Ayarlar'dan y├╝kleyin.", "hata"), 3000);
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
            if(confirm("T├╝m ├Â─şrenciler, devams─▒zl─▒klar ve personeller S─░L─░NECEK.\nEmin misiniz?")) {
                if(confirm("Bu i┼şlem GER─░ ALINAMAZ! Onayl─▒yor musunuz?")) {
                    fetch(`${API}/veritabani-sifirla`, { method: 'DELETE' }).then(r => r.json()).then(v => { bildirimGoster(v.mesaj, v.basarili ? "bilgi" : "hata"); location.reload(); });
                }
            }
        }


        

        // --- A├çILI┼Ş (SPLASH) EKRANI ---
        function splashKapat() {
            const splash = document.getElementById('splash_overlay');
            if(splash) { splash.classList.add('gizli'); setTimeout(() => splash.style.display = 'none', 450); }
        }

        // --- OTOMAT─░K G├£NCELLEME KONTROL├£ (GitHub) ---
        const MEVCUT_VERSIYON = "v1.1";
        function guncellemeKontrolEt() {
            fetch("https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/versiyon.txt", { cache: "no-store" })
                .then(r => r.ok ? r.text() : Promise.reject())
                .then(metin => {
                    const enYeni = metin.trim();
                    if (enYeni > MEVCUT_VERSIYON) {
                        if (confirm(`Program─▒n yeni bir s├╝r├╝m├╝ bulundu!\n\nSizin S├╝r├╝m├╝n├╝z: ${MEVCUT_VERSIYON}\nYeni S├╝r├╝m: ${enYeni}\n\nYeni s├╝r├╝m├╝ indirmek ister misiniz?`)) {
                            window.open("https://github.com/ada-netizen/yoklama_otomasyonu/releases/latest", "_blank");
                        }
                    }
                })
                .catch(() => { /* ─░nternet yoksa veya eri┼şilemezse sessizce devam eder */ });
        }

        window.onload = function() {
            verileriYukle();
            ayarlariYukle(); 
            resizerAktifEt('resizer1', 'sol_panel_ana', 'sag_panel_ana');
            resizerAktifEt('resizer2', 'takvim_alani_ana', 'onizleme_alani_ana');
            tabloSutunBoyutlandirma();
            setTimeout(splashKapat, 1500);
            setTimeout(guncellemeKontrolEt, 2000);
        };
