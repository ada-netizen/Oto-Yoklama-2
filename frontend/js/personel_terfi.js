// =====================================================================

// PERSONEL TERFİ TAKİP VE 365 GÜNLÜK YILLIK MATRİS MOTORU (personel_terfi.js)

// =====================================================================

// 657 Sayılı DMK Madde 64 (Kademe İlerlemesi) ve Madde 68 (Derece Yükselmesi)

// kurallarına göre kadrolu personelin yıllık terfi takvimini yönetir.



(function() {

    let terfiAktifYil = new Date().getFullYear();

    let terfiVerileri = null;

    let terfiPersonelleri = [];

    let terfiTakvimHaritasi = {};

    let seciliTerfiFiltresi = "TUMU";

    let terfiSiralamaAlani = "tarih";

    let terfiSiralamaYon = "asc";

    const aylarListesi = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];



    // 1. VERİLERİ YÜKLE

    window.terfiYukle = function(yil) {

        if (yil) terfiAktifYil = parseInt(yil);

        

        const etiketEl = document.getElementById("terfi_yil_etiket");

        if (etiketEl) etiketEl.innerText = terfiAktifYil;

        

        const matrisBaslikEl = document.getElementById("terfi_matris_baslik");

        if (matrisBaslikEl) matrisBaslikEl.innerText = `Yıllık 365 Günlük Terfi Takvimi (${terfiAktifYil})`;



        const tabloGovde = document.getElementById("terfi_tablo_govde");

        if (tabloGovde) {

            tabloGovde.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--fg-sub);"><div class="spinner-small" style="display:inline-block; margin-right:8px;"></div> Terfi verileri yükleniyor...</td></tr>`;

        }



        fetch(`${API}/personel-terfileri?yil=${terfiAktifYil}`)

            .then(res => res.json())

            .then(data => {

                if (!data.basarili) {

                    if (tabloGovde) {

                        tabloGovde.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: #EF4444;">Terfi verileri alınamadı: ${data.mesaj || "Bilinmeyen hata"}</td></tr>`;

                    }

                    return;

                }



                terfiVerileri = data;

                terfiPersonelleri = data.personeller || [];

                terfiTakvimHaritasi = data.takvim_haritasi || {};

                const stats = data.istatistikler || {};



                // KPI Kartlarını Doldur

                document.getElementById("terfi_kpi_toplam").innerText = stats.toplam_kadrolu || 0;

                document.getElementById("terfi_kpi_yaklasan").innerText = stats.yaklasan_sayisi || 0;

                document.getElementById("terfi_kpi_derece").innerText = stats.derece_sayisi || 0;

                document.getElementById("terfi_kpi_kademe").innerText = stats.kademe_sayisi || 0;

                document.getElementById("terfi_kpi_eksik").innerText = stats.tarih_eksik_sayisi || 0;



                // Filtre sayaçlarını güncelle (Tümü sayacı tavan hariç aktif personelleri gösterir)

                const aktifTerfiSayisi = Math.max(0, (stats.toplam_kadrolu || 0) - (stats.tavan_sayisi || 0));

                document.getElementById("terfi_filtre_sayi_tumu").innerText = aktifTerfiSayisi;

                document.getElementById("terfi_filtre_sayi_yaklasan").innerText = stats.yaklasan_sayisi || 0;

                document.getElementById("terfi_filtre_sayi_derece").innerText = stats.derece_sayisi || 0;

                document.getElementById("terfi_filtre_sayi_kademe").innerText = stats.kademe_sayisi || 0;

                document.getElementById("terfi_filtre_sayi_eksik").innerText = stats.tarih_eksik_sayisi || 0;

                const elTavanSayi = document.getElementById("terfi_filtre_sayi_tavan");

                if (elTavanSayi) elTavanSayi.innerText = stats.tavan_sayisi || 0;



                // Tarihi eksik olanlar için uyarı bandı

                const uyariBand = document.getElementById("terfi_eksik_tarih_uyari");

                if (uyariBand) {

                    uyariBand.style.display = (stats.tarih_eksik_sayisi > 0) ? "flex" : "none";

                }



                // 365 Günlük Matrisi Çiz

                terfiTakviminiCiz();



                // Tabloyu Doldur

                terfiTablosunuDoldur();



                // İlk açılış bilgilendirme uyarısı kontrolü

                terfiAcilisUyarisiKontrol();



                if (window.lucide && typeof lucide.createIcons === 'function') {

                    lucide.createIcons();

                }

            })

            .catch(err => {

                console.error("terfiYukle hatası:", err);

                if (tabloGovde) {

                    tabloGovde.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: #EF4444;">Sunucuyla iletişim kurulamadı.</td></tr>`;

                }

            });

    };



    // 2. YIL DEĞİŞTİRME

    window.terfiYilDegistir = function(delta) {

        terfiAktifYil += delta;

        terfiYukle(terfiAktifYil);

    };



    window.terfiBuguneGit = function() {

        terfiAktifYil = new Date().getFullYear();

        seciliTerfiFiltresi = "TUMU";

        terfiAktifFiltreButonunuGuncelle();

        terfiYukle(terfiAktifYil);

    };



    // 3. 365 GÜNLÜK YILLIK MATRİS TAKVİMİNİ ÇİZ

    function terfiTakviminiCiz() {

        const thead = document.getElementById("terfi_thead");

        const tbody = document.getElementById("terfi_tbody");

        if (!thead || !tbody) return;



        // Başlık (Aylar + 1-31 Günler) - Aylar sütunu 65px sabit, günler eşit dağılır

        let thHtml = `<tr><th class="ay-baslik-th" style="width: 65px; min-width: 65px; max-width: 65px; text-align: center;">Aylar</th>`;

        for (let g = 1; g <= 31; g++) {

            thHtml += `<th style="text-align: center;">${g}</th>`;

        }

        thHtml += `</tr>`;

        thead.innerHTML = thHtml;



        const bugun = new Date();

        const bugunYil = bugun.getFullYear();

        const bugunAy = bugun.getMonth() + 1;

        const bugunGun = bugun.getDate();



        let tbodyHtml = "";



        for (let ayIdx = 0; ayIdx < 12; ayIdx++) {

            const ayNo = ayIdx + 1;

            const ayAd = aylarListesi[ayIdx];

            const buAyMi = (bugunYil === terfiAktifYil && bugunAy === ayNo);



            tbodyHtml += `<tr class="${buAyMi ? 'bu-ay-satiri' : ''}">`;

            if (buAyMi) {

                tbodyHtml += `<td class="ay-baslik bu-ay-baslik" title="${ayAd} (İçinde Bulunulan Ay)">

                    <div class="bu-ay-kapsayici">

                        <span class="bu-ay-ad">${ayAd}</span>

                        <span class="bu-ay-rozet"><span class="bu-ay-nokta"></span>BU AY</span>

                    </div>

                </td>`;

            } else {

                tbodyHtml += `<td class="ay-baslik">${ayAd}</td>`;

            }



            for (let gun = 1; gun <= 31; gun++) {

                // Gün geçerlilik kontrolü

                const dt = new Date(terfiAktifYil, ayIdx, gun);

                const gecerliMi = (dt.getMonth() === ayIdx && dt.getDate() === gun);

                

                if (!gecerliMi) {

                    tbodyHtml += `<td class="gecersiz-gun" title="${gun} ${ayAd} mevcut değil">-</td>`;

                    continue;

                }



                const dayOfWeek = dt.getDay();

                const haftaSonuMu = (dayOfWeek === 0 || dayOfWeek === 6);

                const bugunMu = (bugunYil === terfiAktifYil && bugunAy === ayNo && bugunGun === gun);



                let tdClass = [];

                if (haftaSonuMu) tdClass.push("hafta-sonu");

                if (bugunMu) tdClass.push("bu-ay-bugun");



                const key = `${ayNo}-${gun}`;

                const terfiListesi = terfiTakvimHaritasi[key] || [];

                const terfiSayisi = terfiListesi.length;



                if (terfiSayisi > 0) {

                    tdClass.push("terfi-gunu");

                    

                    const hasKademe = terfiListesi.some(p => p.terfi_turu === "KADEME");

                    const hasDerece = terfiListesi.some(p => p.terfi_turu === "DERECE");



                    let rozetClass = "kademe";

                    let rozetMetin = (terfiSayisi > 1) ? `T<sup>${terfiSayisi}</sup>` : "T";



                    if (hasKademe && hasDerece) {

                        // KULLANICI KURALI: Her iki terfi türü varsa T harfi yarı yarıya hem derece hem kademe renkleri ile boyanır

                        rozetClass = "karisik";

                    } else if (hasDerece) {

                        // Yalnızca derece terfisi var (tek veya çoklu kişi)

                        rozetClass = "derece";

                    } else {

                        // Yalnızca kademe terfisi var (tek veya çoklu kişi)

                        rozetClass = "kademe";

                    }



                    // Tooltip içeriği hazırlama (Tippy için)

                    const tooltipHtml = terfiTooltipIcerigiHazirla(ayAd, gun, terfiListesi);

                    const safeTooltip = escapeHtmlAttribute(tooltipHtml);



                    tbodyHtml += `<td class="${tdClass.join(' ')}" onclick="terfiGuneGoreFiltrele(${ayNo}, ${gun})" data-terfi-tooltip="${safeTooltip}" style="position: relative;">

                        <span class="terfi-hucre-rozet ${rozetClass}">${rozetMetin}</span>

                    </td>`;

                } else {

                    let cellTitle = `${gun} ${ayAd} ${terfiAktifYil}`;

                    if (bugunMu) cellTitle += " (Bugün)";

                    else if (buAyMi) cellTitle += " (Bu Ay)";

                    tbodyHtml += `<td class="${tdClass.join(' ')}" title="${cellTitle}"></td>`;

                }

            }



            tbodyHtml += `</tr>`;

        }



        tbody.innerHTML = tbodyHtml;



        // Tippy Tooltip'lerini bağla

        terfiTooltipleriBaslat();

    }



    // 4. TOOLTIP İÇERİĞİ OLUŞTURUCU

    function terfiTooltipIcerigiHazirla(ayAd, gun, terfiListesi) {

        const count = terfiListesi.length;

        let html = `<div style="text-align: left; padding: 4px; max-width: 320px; font-family: var(--font-ui, sans-serif);">`;

        html += `<div style="font-weight: 800; font-size: 12px; color: #38BDF8; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">

            <span>🗓️ ${gun} ${ayAd} ${terfiAktifYil}</span>

            <span style="background: rgba(56,189,248,0.2); color: #38BDF8; padding: 2px 6px; border-radius: 4px; font-size: 10px;">${count} Personel Terfisi</span>

        </div>`;



        terfiListesi.forEach((p, idx) => {

            const isDerece = (p.terfi_turu === "DERECE");

            const rozetRenk = isDerece ? "#A78BFA" : "#38BDF8";

            const rozetBg = isDerece ? "rgba(167, 139, 250, 0.18)" : "rgba(56, 189, 248, 0.18)";



            html += `<div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 6px 8px; margin-bottom: ${idx < count-1 ? '6px' : '0'};">

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">

                    <span style="font-weight: 700; color: #F8FAFC; font-size: 11.5px;">${p.ad_soyad}</span>

                    <span style="font-size: 9.5px; background: ${rozetBg}; color: ${rozetRenk}; padding: 1px 5px; border-radius: 3px; font-weight: 700;">${p.terfi_baslik}</span>

                </div>

                <div style="font-size: 10px; color: #94A3B8; margin-bottom: 4px;">${p.gorev} • ${p.brans}</div>

                <div style="display: flex; justify-content: space-between; font-size: 10.5px; background: rgba(0,0,0,0.25); padding: 3px 6px; border-radius: 4px; margin-bottom: 4px;">

                    <span style="color: #CBD5E1;">Mevcut: <strong>${p.mevcut_kademe_derece}</strong></span>

                    <span style="color: #F59E0B;">➔</span>

                    <span style="color: #34D399; font-weight: 700;">Yeni: ${p.yeni_kademe_derece}</span>

                </div>

                <div style="font-size: 9.5px; color: #60A5FA; font-weight: 600; line-height: 1.2;">

                    ⚖️ ${p.mevzuat_maddesi}

                </div>

                ${p.baslama_tarihi ? `<div style="font-size: 9px; color: #94A3B8; margin-top: 2px;">İlk Başlama: ${p.baslama_tarihi}</div>` : ''}

            </div>`;

        });



        html += `<div style="margin-top: 6px; text-align: center; font-size: 9.5px; color: #94A3B8;">(Aşağıdaki listede odaklanmak için tıklayınız)</div>`;

        html += `</div>`;

        return html;

    }



    // 5. TIPPY TOOLTİPLERİNİ BAŞLAT

    function terfiTooltipleriBaslat() {

        if (typeof tippy === "undefined") return;



        document.querySelectorAll("[data-terfi-tooltip]").forEach(el => {

            const rawContent = el.getAttribute("data-terfi-tooltip");

            if (!rawContent) return;



            tippy(el, {

                content: rawContent,

                allowHTML: true,

                theme: "dark-custom",

                placement: "bottom",

                interactive: true,

                delay: [100, 150],

                maxWidth: 340,

                appendTo: () => document.body

            });

        });

    }



    // 6. GÜNE GÖRE FİLTRELEME (HÜCREYE TIKLAYINCA)

    window.terfiGuneGoreFiltrele = function(ayNo, gunNo) {

        seciliTerfiFiltresi = `GUN_${ayNo}_${gunNo}`;

        terfiAktifFiltreButonunuGuncelle();

        terfiTablosunuDoldur();

        

        // Tablo alanına yumuşak kaydır

        const tabloEl = document.getElementById("terfi_tablo_govde");

        if (tabloEl) {

            tabloEl.scrollIntoView({ behavior: "smooth", block: "nearest" });

        }

    };



    // 7. FİLTRE BUTONU SEÇİMİ

    window.terfiFiltreSec = function(filtre) {

        seciliTerfiFiltresi = filtre;

        terfiAktifFiltreButonunuGuncelle();

        terfiTablosunuDoldur();

    };



    window.terfiFiltreTemizle = function() {

        const araInput = document.getElementById("terfi_ara");

        if (araInput) araInput.value = "";

        seciliTerfiFiltresi = "TUMU";

        terfiAktifFiltreButonunuGuncelle();

        terfiTablosunuDoldur();

    };



    function terfiAktifFiltreButonunuGuncelle() {

        const butonlar = [

            { id: "btn_terfi_filtre_tumu", f: "TUMU" },

            { id: "btn_terfi_filtre_yaklasan", f: "YAKLASAN" },

            { id: "btn_terfi_filtre_derece", f: "DERECE" },

            { id: "btn_terfi_filtre_kademe", f: "KADEME" },

            { id: "btn_terfi_filtre_eksik", f: "EKSIK" },

            { id: "btn_terfi_filtre_tavan", f: "TAVAN" }

        ];



        butonlar.forEach(b => {

            const el = document.getElementById(b.id);

            if (el) {

                if (seciliTerfiFiltresi === b.f) el.classList.add("active");

                else el.classList.remove("active");

            }

        });

    }



    // 8. TABLOYU DOLDUR & SIRALA & FİLTRELE

    window.terfiAramaFiltrele = function() {

        terfiTablosunuDoldur();

    };



    window.terfiTabloSirala = function(alan) {

        if (terfiSiralamaAlani === alan) {

            terfiSiralamaYon = (terfiSiralamaYon === "asc") ? "desc" : "asc";

        } else {

            terfiSiralamaAlani = alan;

            terfiSiralamaYon = "asc";

        }

        terfiTablosunuDoldur();

    };



        // Tarih formatlama yardımcısı (GG.AA.YYYY standardizasyonu)

    function formatTarihTr(tarihStr) {

        if (!tarihStr) return "";

        const temiz = String(tarihStr).split('T')[0].split(' ')[0].trim();

        if (temiz.includes('-')) {

            const p = temiz.split('-');

            if (p.length === 3 && p[0].length === 4) {

                return `${p[2].padStart(2, '0')}.${p[1].padStart(2, '0')}.${p[0]}`;

            }

        } else if (temiz.includes('/')) {

            const p = temiz.split('/');

            if (p.length === 3) {

                if (p[0].length === 4) return `${p[2].padStart(2, '0')}.${p[1].padStart(2, '0')}.${p[0]}`;

                if (p[2].length === 4) return `${p[0].padStart(2, '0')}.${p[1].padStart(2, '0')}.${p[2]}`;

            }

        }

        return temiz;

    }



function terfiTablosunuDoldur() {

        const govde = document.getElementById("terfi_tablo_govde");

        if (!govde) return;



        const araInput = document.getElementById("terfi_ara");

        const aramaMetni = araInput ? araInput.value.trim().toLocaleLowerCase("tr-TR") : "";



        let filtrelenmis = terfiPersonelleri.filter(p => {

            const isTavan = (p.tavan_mi === true || p.terfi_turu === "TAVAN");



            // KULLANICI KURALI: Tavana ulaşan personel varsayılan olarak alttaki listede gösterilmez.

            // Yalnızca kullanıcı açıkça 'TAVAN' filtresine bastığında listelenir.

            if (seciliTerfiFiltresi !== "TAVAN" && isTavan) {

                return false;

            }



            // Arama filtresi

            if (aramaMetni) {

                const ad = (p.ad_soyad || "").toLocaleLowerCase("tr-TR");

                const unvan = (p.unvan || "").toLocaleLowerCase("tr-TR");

                const brans = (p.brans || "").toLocaleLowerCase("tr-TR");

                const gorev = (p.gorev || "").toLocaleLowerCase("tr-TR");

                if (!ad.includes(aramaMetni) && !unvan.includes(aramaMetni) && !brans.includes(aramaMetni) && !gorev.includes(aramaMetni)) {

                    return false;

                }

            }



            // Çip filtresi

            if (seciliTerfiFiltresi === "YAKLASAN") return p.yaklasan_mi === true;

            if (seciliTerfiFiltresi === "DERECE") return p.terfi_turu === "DERECE";

            if (seciliTerfiFiltresi === "KADEME") return p.terfi_turu === "KADEME";

            if (seciliTerfiFiltresi === "EKSIK") return p.tarih_eksik === true;

            if (seciliTerfiFiltresi === "TAVAN") return isTavan;

            if (seciliTerfiFiltresi.startsWith("GUN_")) {

                const parts = seciliTerfiFiltresi.split("_");

                const a = parseInt(parts[1]);

                const g = parseInt(parts[2]);

                return (p.ay_no === a && p.gun_no === g);

            }

            return true;

        });



        // Sıralama

        filtrelenmis.sort((a, b) => {

            let valA, valB;

            if (terfiSiralamaAlani === "ad") {

                valA = a.ad_soyad || "";

                valB = b.ad_soyad || "";

                return terfiSiralamaYon === "asc" ? valA.localeCompare(valB, "tr-TR") : valB.localeCompare(valA, "tr-TR");

            } else {

                // Varsayılan: Tarihe göre (tarihi eksik olanlar en sona)

                if (a.tarih_eksik && !b.tarih_eksik) return 1;

                if (!a.tarih_eksik && b.tarih_eksik) return -1;

                valA = a.terfi_iso || "9999-99-99";

                valB = b.terfi_iso || "9999-99-99";

                return terfiSiralamaYon === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);

            }

        });



        if (filtrelenmis.length === 0) {

            govde.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: var(--fg-sub);">Filtreye uygun personel bulunamadı.</td></tr>`;

            return;

        }



        let html = "";

        filtrelenmis.forEach((p, idx) => {

            const isEksik = p.tarih_eksik;

            const isDerece = (p.terfi_turu === "DERECE");

            const isYaklasan = p.yaklasan_mi;



            let satirStil = "";

            if (isYaklasan) satirStil = "background: rgba(245, 158, 11, 0.05);";

            if (isEksik) satirStil = "background: rgba(239, 68, 68, 0.04);";



            let rozetHtml = "";

            if (isEksik) {

                rozetHtml = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 10.5px; font-weight: 700; background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3);">⚠️ Başlama Tarihi Eksik</span>`;

            } else if (isDerece) {

                rozetHtml = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 10.5px; font-weight: 700; background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3);">🔺 Derece Yükselmesi</span>`;

            } else if (p.terfi_turu === "TAVAN") {

                rozetHtml = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 10.5px; font-weight: 700; background: rgba(100, 116, 139, 0.15); color: #64748B; border: 1px solid rgba(100, 116, 139, 0.3);" title="1/4 tavan derecesinde olduğu için takvimde gösterilmez">🛡️ Tavan Barem (Takvim Dışı)</span>`;

            } else {

                rozetHtml = `<span style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 4px; font-size: 10.5px; font-weight: 700; background: rgba(14, 165, 233, 0.15); color: #0EA5E9; border: 1px solid rgba(14, 165, 233, 0.3);">📈 Kademe İlerlemesi</span>`;

            }



            let terfiTarihHtml = "";

            if (isEksik) {

                terfiTarihHtml = `<span style="color: #EF4444; font-weight: 700; font-size: 11px;">Eksik</span>`;

            } else {

                const trTarih = formatTarihTr(p.baslama_tarihi_kullanilan);

                terfiTarihHtml = `<strong style="color: var(--fg-main);">${trTarih}</strong>`;

                if (isYaklasan) {

                    terfiTarihHtml += ` <div style="margin-top: 2px;"><span style="font-size: 10px; background: #F59E0B; color: #000; padding: 1px 4px; border-radius: 3px; font-weight: 800;" title="${p.gun_kaldi} gün kaldı">⏳ ${p.gun_kaldi}G</span></div>`;

                }

            }



            let islemBtn = isEksik

                ? `<button class="btn btn-kirmizi" onclick="personelProfilAc('${escapeJsQuotes(p.ad_soyad)}')" style="padding: 3px 8px; font-size: 10.5px;" title="İlk göreve başlama tarihini gir"><i data-lucide="edit-3" height="12" width="12"></i> Tarih Gir</button>`

                : `<button class="btn btn-ayarlar" onclick="personelProfilAc('${escapeJsQuotes(p.ad_soyad)}')" style="padding: 3px 8px; font-size: 10.5px;" title="Personel Profilini Aç"><i data-lucide="user" height="12" width="12"></i> Profil</button>`;



            html += `<tr style="${satirStil} border-bottom: 1px solid var(--border);">

                <td style="padding: 8px 10px; text-align: center; color: var(--fg-sub); font-size: 11px;">${idx + 1}</td>

                <td style="padding: 8px 12px; font-weight: 700; color: var(--fg-main);">

                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">

                        <span>${p.ad_soyad}</span>

                    </div>

                    <div style="font-size: 10.5px; font-weight: 400; color: var(--fg-sub);">${p.unvan}</div>

                </td>

                <td style="padding: 8px 12px; color: var(--fg-main);">

                    <div>${p.gorev}</div>

                    <div style="font-size: 10.5px; color: var(--fg-sub);">${p.brans}</div>

                </td>

                <td style="padding: 8px 12px; text-align: center; font-size: 11px;">

                    ${terfiTarihHtml}

                </td>

                <td style="padding: 8px 12px; text-align: center; font-weight: 700; color: var(--fg-main);">

                    ${p.mevcut_kademe_derece}

                </td>

                <td style="padding: 8px 12px; text-align: center; font-weight: 800; color: ${isDerece ? '#8B5CF6' : '#0EA5E9'};">

                    ${p.yeni_kademe_derece}

                </td>

                <td style="padding: 8px 12px;">

                    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">

                        ${rozetHtml}

                    </div>

                    <div style="font-size: 10px; color: var(--fg-sub); font-weight: 600;">

                        ${p.mevzuat_maddesi}

                    </div>

                </td>

                <td style="padding: 8px 10px; text-align: center;">

                    ${islemBtn}

                </td>

            </tr>`;

        });



        govde.innerHTML = html;

        if (window.lucide && typeof lucide.createIcons === 'function') {

            lucide.createIcons();

        }

    }



    // 9. BİLGİLENDİRME MODALI YÖNETİMİ (KULLANICI TALEBİ: HER AÇILIŞTA UYARI + BİR DAHA GÖSTERME)

    function terfiAcilisUyarisiKontrol() {

        const birDahaGosterme = localStorage.getItem("terfi_uyari_gosterme");

        if (birDahaGosterme !== "true") {

            terfiBilgiModalAc(true);

        }

    }



    window.terfiBilgiModalAc = function(otomatikMi) {

        const modal = document.getElementById("modal_terfi_bilgi");

        if (modal) {

            modal.style.display = "flex";

            if (window.lucide && typeof lucide.createIcons === 'function') {

                lucide.createIcons();

            }

        }

    };



    window.terfiBilgiModalKapat = function() {

        const modal = document.getElementById("modal_terfi_bilgi");

        if (modal) modal.style.display = "none";

    };



    window.terfiBilgiModalOnayla = function() {

        const chk = document.getElementById("chk_terfi_uyari_bir_daha_gosterme");

        if (chk && chk.checked) {

            localStorage.setItem("terfi_uyari_gosterme", "true");

        }

        terfiBilgiModalKapat();

    };



    // 10. EXCEL RAPORU İNDİRME

    window.terfiPdfIndir = async function() {
        if (!terfiPersonelleri || terfiPersonelleri.length === 0) {
            if (typeof bildirimGoster === "function") {
                bildirimGoster("İndirilecek terfi kaydı bulunamadı.", "uyari");
            } else {
                alert("İndirilecek terfi kaydı bulunamadı.");
            }
            return;
        }

        if (typeof yuklemeGoster === "function") {
            yuklemeGoster("Yıllık Terfi Çizelgesi (A4 PDF) hazırlanıyor...");
        }

        try {
            const resp = await fetch(`${API}/personel-terfi-pdf?yil=${terfiAktifYil}`);
            const data = await resp.json();
            if (data.basarili) {
                if (typeof bildirimGoster === "function") {
                    bildirimGoster("Yıllık terfi çizelgesi başarıyla hazırlandı.", "bilgi");
                }
                if (window.dosyayiYeniSekmedeAc && data.dosya) {
                    window.dosyayiYeniSekmedeAc(data.dosya);
                }
            } else {
                if (typeof bildirimGoster === "function") {
                    bildirimGoster(data.mesaj || "PDF çizelgesi oluşturulamadı.", "hata");
                }
            }
        } catch (e) {
            console.error("Terfi PDF indirme hatası:", e);
            if (typeof bildirimGoster === "function") {
                bildirimGoster("PDF indirilirken hata oluştu: " + e.message, "hata");
            }
        } finally {
            if (typeof yuklemeGizle === "function") {
                yuklemeGizle();
            }
        }
    };
    window.terfiExcelIndir = window.terfiPdfIndir;



    // YARDIMCI GÜVENLİ KAÇIŞ FONKSİYONLARI

    function escapeHtmlAttribute(str) {

        if (!str) return "";

        return String(str)

            .replace(/&/g, "&amp;")

            .replace(/"/g, "&quot;")

            .replace(/'/g, "&#39;")

            .replace(/</g, "&lt;")

            .replace(/>/g, "&gt;");

    }



    function escapeJsQuotes(str) {

        if (!str) return "";

        return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');

    }



})();





// Güvenlik alias'ı (Eğer personel_teblig.js'den önce yüklenirse)

if (typeof window.personelProfilModalAc === 'undefined') {

    window.personelProfilModalAc = function(p) {

        if (typeof window.personelProfilAc === 'function') {

            window.personelProfilAc(p);

        }

    };

}

