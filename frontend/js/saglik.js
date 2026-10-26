// =====================================================================
// PERSONEL İZİN MASASI & 365 GÜNLÜK YILLIK MATRİS MOTORU (saglik.js)
// =====================================================================
// 657 Sayılı DMK (Md. 102, 103, 104, 105, 108, 152), 4857 Sayılı İş Kanunu,
// TYP ve İUP mevzuatı kurallarına göre kurumdaki tüm personelin izinlerini yönetir.

(function() {
    let izinAktifYil = new Date().getFullYear();
    let aktifIzinPersoneli = [];
    let tumIzinPersoneli = [];
    let izinTakvimHaritasi = {};
    let seciliIzinFiltresi = "TUMU";
    let aktifGunFiltresi = null; // { ay, gun }
    let saglikFlatpickr = null;
    let duzenleFlatpickr = null;

    const aylarListesi = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];

    // 1. VERİLERİ YÜKLE
    async function saglikYukle(yil) {
        if (yil) izinAktifYil = parseInt(yil);

        const yilEtiket = document.getElementById('saglik_yil_etiket');
        if (yilEtiket) yilEtiket.textContent = izinAktifYil;

        const matrisBaslik = document.getElementById('izin_matris_baslik');
        if (matrisBaslik) matrisBaslik.textContent = `Yıllık 365 Günlük İzin Takvimi (${izinAktifYil})`;

        try {
            // İki API çağrısını paralel yapalım: Liste ve Takvim Matrisi
            const [listeResp, takvimResp] = await Promise.all([
                apiFetch(`/saglik/liste?yil=${izinAktifYil}`),
                apiFetch(`/saglik/takvim?yil=${izinAktifYil}`)
            ]);

            if (listeResp && listeResp.basarili) {
                tumIzinPersoneli = listeResp.veri || [];
                aktifIzinPersoneli = [...tumIzinPersoneli];
            }

            if (takvimResp && takvimResp.basarili) {
                izinTakvimHaritasi = takvimResp.takvim_haritasi || {};
                const stats = takvimResp.istatistikler || {};

                // KPI Kartlarını Doldur
                const elKisi = document.getElementById('stat_raporlu_kisi');
                if (elKisi) elKisi.textContent = stats.toplam_izinli_personel || 0;

                const elToplamGun = document.getElementById('stat_toplam_gun');
                if (elToplamGun) elToplamGun.textContent = stats.toplam_izin_gunu || 0;

                const elSaglikGun = document.getElementById('stat_saglik_gun');
                if (elSaglikGun) elSaglikGun.textContent = stats.saglik_gun_toplam || 0;

                const elDigerGun = document.getElementById('stat_diger_gun');
                if (elDigerGun) elDigerGun.textContent = (stats.yillik_gun_toplam || 0) + (stats.mazeret_gun_toplam || 0) + (stats.idari_gun_toplam || 0);

                const elSiniriAsan = document.getElementById('stat_siniri_asan');
                if (elSiniriAsan) elSiniriAsan.textContent = stats.kesinti_siniri_asan || 0;

                // Filtre Sayaçları
                const elSayiTumu = document.getElementById('izin_filtre_sayi_tumu');
                if (elSayiTumu) elSayiTumu.textContent = stats.toplam_izinli_personel || 0;

                const elSayiSaglik = document.getElementById('izin_filtre_sayi_saglik');
                if (elSayiSaglik) elSayiSaglik.textContent = stats.saglik_gun_toplam > 0 ? (tumIzinPersoneli || []).filter(p => (p.saglik_gun || 0) > 0).length : 0;

                const elSayiYillik = document.getElementById('izin_filtre_sayi_yillik');
                if (elSayiYillik) elSayiYillik.textContent = stats.yillik_gun_toplam > 0 ? (tumIzinPersoneli || []).filter(p => (p.yillik_gun || 0) > 0).length : 0;

                const elSayiMazeret = document.getElementById('izin_filtre_sayi_mazeret');
                if (elSayiMazeret) elSayiMazeret.textContent = stats.mazeret_gun_toplam > 0 ? (tumIzinPersoneli || []).filter(p => (p.mazeret_gun || 0) > 0).length : 0;

                const elSayiKesinti = document.getElementById('izin_filtre_sayi_kesinti');
                if (elSayiKesinti) elSayiKesinti.textContent = stats.kesinti_siniri_asan || 0;
            }

            // 365 Günlük Takvimi Çiz
            izinTakviminiCiz();

            // Tabloyu ve Select Kutusunu Doldur
            saglikTablosunuCiz();
            saglikPersonelSelectDoldur();

            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                lucide.createIcons();
            }
        } catch (e) {
            console.error("İzin verisi yüklenirken hata:", e);
        }
    }
    window.saglikYukle = saglikYukle;

    // 2. YIL DEĞİŞTİRME & BUGÜNE GİT
    window.izinYilDegistir = function(delta) {
        izinAktifYil += delta;
        aktifGunFiltresi = null;
        saglikYukle(izinAktifYil);
    };

    window.izinBuguneGit = function() {
        izinAktifYil = new Date().getFullYear();
        aktifGunFiltresi = null;
        seciliIzinFiltresi = "TUMU";
        izinAktifFiltreButonunuGuncelle();
        saglikYukle(izinAktifYil);
    };

    // 3. 365 GÜNLÜK YILLIK MATRİS TAKVİMİNİ ÇİZ
    function izinTakviminiCiz() {
        const thead = document.getElementById("izin_thead");
        const tbody = document.getElementById("izin_tbody");
        if (!thead || !tbody) return;

        // Başlık (Aylar + 1-31 Günler) - Aylar sütunu 65px sabit
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
            const buAyMi = (bugunYil === izinAktifYil && bugunAy === ayNo);

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
                const dt = new Date(izinAktifYil, ayIdx, gun);
                const gecerliMi = (dt.getMonth() === ayIdx && dt.getDate() === gun);

                if (!gecerliMi) {
                    tbodyHtml += `<td class="gecersiz-gun" title="${gun} ${ayAd} mevcut değil">-</td>`;
                    continue;
                }

                const dayOfWeek = dt.getDay();
                const haftaSonuMu = (dayOfWeek === 0 || dayOfWeek === 6);
                const bugunMu = (bugunYil === izinAktifYil && bugunAy === ayNo && bugunGun === gun);
                const seciliGunMu = (aktifGunFiltresi && aktifGunFiltresi.ay === ayNo && aktifGunFiltresi.gun === gun);

                let tdClass = [];
                if (haftaSonuMu) tdClass.push("hafta-sonu");
                if (bugunMu) tdClass.push("bu-ay-bugun");
                if (seciliGunMu) tdClass.push("terfi-gunu"); // Highlight style

                const key = `${ayNo}-${gun}`;
                const izinListesi = izinTakvimHaritasi[key] || [];
                const izinSayisi = izinListesi.length;

                if (izinSayisi > 0) {
                    tdClass.push("terfi-gunu");

                    // İzin türleri ayrımı
                    const turler = new Set(izinListesi.map(x => x.izin_turu));
                    const hasSaglik = turler.has("SAĞLIK");
                    const hasYillik = turler.has("YILLIK");
                    const hasMazeret = turler.has("MAZERET");
                    const hasIdari = turler.has("İDARİ") || turler.has("IDARI");
                    const hasIdareci = izinListesi.some(x => x.yonetici_mi);

                    let rozetClass = "saglik";
                    let rozetMetin = "S";

                    if (turler.size > 1) {
                        rozetClass = "karisik";
                        rozetMetin = `İ<sup>${izinSayisi}</sup>`;
                    } else if (hasYillik) {
                        rozetClass = "yillik";
                        rozetMetin = (izinSayisi > 1) ? `Y<sup>${izinSayisi}</sup>` : "Y";
                    } else if (hasMazeret) {
                        rozetClass = "mazeret";
                        rozetMetin = (izinSayisi > 1) ? `M<sup>${izinSayisi}</sup>` : "M";
                    } else if (hasIdari) {
                        rozetClass = "idari";
                        rozetMetin = (izinSayisi > 1) ? `İ<sup>${izinSayisi}</sup>` : "İ";
                    } else {
                        rozetClass = "saglik";
                        rozetMetin = (izinSayisi > 1) ? `S<sup>${izinSayisi}</sup>` : "S";
                    }

                    // İdareci Çerçevesi
                    let ekstraSinif = hasIdareci ? "idareci-cerceve" : "";

                    // Tooltip HTML hazırlığı
                    const tooltipHtml = izinTooltipIcerigiHazirla(ayAd, gun, izinListesi);
                    const safeTooltip = escapeHtmlAttribute(tooltipHtml);

                    tbodyHtml += `<td class="${tdClass.join(' ')}" onclick="izinGuneGoreFiltrele(${ayNo}, ${gun})" data-izin-tooltip="${safeTooltip}" style="position: relative; cursor: pointer;">
                        <span class="izin-hucre-rozet ${rozetClass} ${ekstraSinif}">${rozetMetin}</span>
                    </td>`;
                } else {
                    let cellTitle = `${gun} ${ayAd} ${izinAktifYil}`;
                    if (bugunMu) cellTitle += " (Bugün)";
                    else if (buAyMi) cellTitle += " (Bu Ay)";
                    tbodyHtml += `<td class="${tdClass.join(' ')}" title="${cellTitle}"></td>`;
                }
            }

            tbodyHtml += `</tr>`;
        }

        tbody.innerHTML = tbodyHtml;
        izinTooltipleriniEtkinlestir();
    }

    // Tooltip İçeriği
    function izinTooltipIcerigiHazirla(ayAd, gun, izinListesi) {
        let h = `<div style="text-align:left; font-size:12px; max-width:320px; line-height:1.4;">`;
        h += `<div style="font-weight:800; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:5px; margin-bottom:6px; color:#38BDF8;">📅 ${gun} ${ayAd} ${izinAktifYil} İzinli Personeller (${izinListesi.length})</div>`;

        izinListesi.forEach((p, idx) => {
            const turRenk = p.izin_turu === 'SAĞLIK' ? '#10B981' : (p.izin_turu === 'YILLIK' ? '#38BDF8' : (p.izin_turu === 'MAZERET' ? '#F59E0B' : '#A78BFA'));
            const unvanStr = p.unvan ? (p.brans ? `${p.unvan} (${p.brans})` : p.unvan) : p.grup;
            const idareciBadge = p.yonetici_mi ? ` <span style="background:#F59E0B; color:#000; font-size:9.5px; padding:1px 4px; border-radius:3px; font-weight:800;">İDARECİ</span>` : "";

            h += `<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px dashed rgba(255,255,255,0.1);">`;
            h += `  <div style="font-weight:700; color:#FFFFFF;">${p.personel_ad}${idareciBadge}</div>`;
            h += `  <div style="font-size:11px; opacity:0.85;">${unvanStr} - ${p.grup}</div>`;
            h += `  <div style="color:${turRenk}; font-weight:600; font-size:11.5px; margin-top:2px;">🏷️ ${p.izin_turu} (${p.gun_sayisi} Gün: ${format_tr_tarih(p.baslangic)} - ${format_tr_tarih(p.bitis)})</div>`;
            if (p.rapor_turu) {
                h += `  <div style="font-size:10.5px; color:#38BDF8; font-weight:600; margin-top:1px;">🩺 ${p.rapor_turu}</div>`;
            }
            if (p.izin_adresi) {
                h += `  <div style="font-size:11px; margin-top:2px; color:#FCD34D;">📍 <strong>Adres:</strong> ${p.izin_adresi}</div>`;
            }
            if (p.mevzuat_maddesi) {
                h += `  <div style="font-size:10.5px; opacity:0.75; font-style:italic;">⚖️ ${p.mevzuat_maddesi}</div>`;
            }
            if (p.aciklama && p.aciklama !== "-") {
                h += `  <div style="font-size:11px; margin-top:2px; opacity:0.9;">📝 ${p.aciklama}</div>`;
            }
            h += `</div>`;
        });

        h += `<div style="font-size:10px; opacity:0.65; margin-top:4px;">💡 Güne tıklayarak aşağıdaki dökümü bu güne filtreleyebilirsiniz.</div>`;
        h += `</div>`;
        return h;
    }

    function escapeHtmlAttribute(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function unescapeHtmlAttribute(str) {
        if (!str) return "";
        return str
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&amp;/g, "&");
    }

    // Özel Modern Tooltip Motoru
    function izinTooltipleriniEtkinlestir() {
        const hucreler = document.querySelectorAll("[data-izin-tooltip]");
        hucreler.forEach(el => {
            el.addEventListener("mouseenter", function(e) {
                const rawTooltip = this.getAttribute("data-izin-tooltip");
                if (!rawTooltip) return;

                let tooltipBox = document.getElementById("izin_global_tooltip");
                if (!tooltipBox) {
                    tooltipBox = document.createElement("div");
                    tooltipBox.id = "izin_global_tooltip";
                    tooltipBox.style.position = "fixed";
                    tooltipBox.style.zIndex = "99999";
                    tooltipBox.style.background = "rgba(15, 23, 42, 0.96)";
                    tooltipBox.style.color = "#FFFFFF";
                    tooltipBox.style.border = "1px solid rgba(56, 189, 248, 0.4)";
                    tooltipBox.style.borderRadius = "8px";
                    tooltipBox.style.padding = "10px 14px";
                    tooltipBox.style.boxShadow = "0 10px 25px rgba(0,0,0,0.5)";
                    tooltipBox.style.pointerEvents = "none";
                    tooltipBox.style.transition = "opacity 0.15s ease";
                    document.body.appendChild(tooltipBox);
                }

                tooltipBox.innerHTML = unescapeHtmlAttribute(rawTooltip);
                tooltipBox.style.display = "block";
                tooltipBox.style.opacity = "1";

                const rect = this.getBoundingClientRect();
                const tipW = 320;
                let left = rect.left + (rect.width / 2) - (tipW / 2);
                if (left < 10) left = 10;
                if (left + tipW > window.innerWidth - 10) left = window.innerWidth - tipW - 10;

                let top = rect.top - 12 - tooltipBox.offsetHeight;
                if (top < 10) {
                    top = rect.bottom + 10;
                }

                tooltipBox.style.left = `${left}px`;
                tooltipBox.style.top = `${top}px`;
            });

            el.addEventListener("mouseleave", function() {
                const tooltipBox = document.getElementById("izin_global_tooltip");
                if (tooltipBox) {
                    tooltipBox.style.opacity = "0";
                    tooltipBox.style.display = "none";
                }
            });
        });
    }

    // 4. GÜNE GÖRE FİLTRELEME
    window.izinGuneGoreFiltrele = function(ay, gun) {
        if (aktifGunFiltresi && aktifGunFiltresi.ay === ay && aktifGunFiltresi.gun === gun) {
            // Tıklanan güne tekrar tıklandıysa filtreyi kaldır
            aktifGunFiltresi = null;
        } else {
            aktifGunFiltresi = { ay, gun };
        }
        izinTakviminiCiz();
        saglikTablosunuCiz();
    };

    // 5. DETAYLI DÖKÜM TABLOSUNU ÇİZ
    function saglikTablosunuCiz() {
        const tbody = document.getElementById('tbody_saglik');
        if (!tbody) return;
        tbody.innerHTML = '';

        // Filtreleri uygula
        let filtrelenmis = [...tumIzinPersoneli];

        // 1. Arama Filtresi
        const aramaGirdi = document.getElementById('izin_ara');
        const aramaKelimesi = aramaGirdi ? aramaGirdi.value.trim().toLocaleUpperCase('tr-TR') : "";
        if (aramaKelimesi) {
            filtrelenmis = filtrelenmis.filter(p => {
                const ad = (p.personel_ad || "").toLocaleUpperCase('tr-TR');
                const unvan = (p.unvan || "").toLocaleUpperCase('tr-TR');
                const brans = (p.brans || "").toLocaleUpperCase('tr-TR');
                return ad.includes(aramaKelimesi) || unvan.includes(aramaKelimesi) || brans.includes(aramaKelimesi);
            });
        }

        // 2. Preset Filtresi
        if (seciliIzinFiltresi === "SAĞLIK") {
            filtrelenmis = filtrelenmis.filter(p => p.saglik_gun > 0);
        } else if (seciliIzinFiltresi === "YILLIK") {
            filtrelenmis = filtrelenmis.filter(p => p.yillik_gun > 0);
        } else if (seciliIzinFiltresi === "MAZERET") {
            filtrelenmis = filtrelenmis.filter(p => p.mazeret_gun > 0);
        } else if (seciliIzinFiltresi === "KESINTI") {
            filtrelenmis = filtrelenmis.filter(p => p.yedi_gecen > 0);
        }

        // 3. Belirli Güne Tıklama Filtresi
        if (aktifGunFiltresi) {
            const key = `${aktifGunFiltresi.ay}-${aktifGunFiltresi.gun}`;
            const gundekiPersoneller = new Set((izinTakvimHaritasi[key] || []).map(x => x.personel_ad));
            filtrelenmis = filtrelenmis.filter(p => gundekiPersoneller.has(p.personel_ad));
        }

        if (filtrelenmis.length === 0) {
            tbody.innerHTML = `<tr><td colspan="18" style="text-align: center; padding: 24px; color: var(--fg-sub);">Filtre kriterlerine uygun izin kaydı bulunamadı.</td></tr>`;
            return;
        }

        filtrelenmis.forEach(p => {
            const tr = document.createElement('tr');

            // İdareci / Öğretmen / Memur Rozeti
            let unvanBadge = "";
            if (p.yonetici_mi) {
                unvanBadge = `<span style="background: rgba(245, 158, 11, 0.15); color: #D97706; font-size: 10px; font-weight: 800; padding: 2px 5px; border-radius: 4px; border: 1px solid rgba(245, 158, 11, 0.3);">İDARECİ</span>`;
            } else if (p.ogretmen_mi) {
                unvanBadge = `<span style="background: rgba(59, 130, 246, 0.12); color: #3B82F6; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px;">ÖĞRETMEN</span>`;
            } else {
                unvanBadge = `<span style="background: rgba(100, 116, 139, 0.15); color: var(--fg-sub); font-size: 10px; font-weight: 600; padding: 2px 5px; border-radius: 4px;">${p.grup}</span>`;
            }

            // 1-12 Aylar sütunları (Yıllık takvim matrisindeki renklerle uyumlu)
            let aylarHtml = '';
            for (let i = 1; i <= 12; i++) {
                const ayDetay = (p.aylik_detay && p.aylik_detay[i]) || null;
                const gun = ayDetay ? ayDetay.toplam : (p.aylar[i] || 0);

                if (gun > 0) {
                    const turler = ayDetay ? Object.keys(ayDetay.turler || {}) : [];
                    let badgeBg = '#10B981'; // Varsayılan Sağlık (Yeşil)
                    let tooltipMetni = `${gun} Gün`;

                    if (turler.length === 1) {
                        const tekTur = turler[0].toUpperCase();
                        if (tekTur === 'YILLIK') {
                            badgeBg = '#0284C7'; // Yıllık İzin (Gök Mavisi)
                            tooltipMetni = `${gun} Gün Yıllık İzin`;
                        } else if (tekTur === 'MAZERET') {
                            badgeBg = '#F59E0B'; // Mazeret İzni (Kehribar/Turuncu)
                            tooltipMetni = `${gun} Gün Mazeret İzni`;
                        } else if (tekTur === 'İDARİ' || tekTur === 'IDARI') {
                            badgeBg = '#8B5CF6'; // İdari İzin (Mor)
                            tooltipMetni = `${gun} Gün İdari İzin`;
                        } else if (tekTur === 'AYLIKSIZ' || tekTur === 'DİĞER' || tekTur === 'DIGER') {
                            badgeBg = '#64748B'; // Aylıksız / Diğer (Gri)
                            tooltipMetni = `${gun} Gün ${tekTur === 'AYLIKSIZ' ? 'Aylıksız İzin' : 'Diğer İzin'}`;
                        } else {
                            badgeBg = '#10B981'; // Sağlık İzni
                            tooltipMetni = `${gun} Gün Sağlık İzni`;
                        }
                    } else if (turler.length > 1) {
                        const hasSaglik = turler.includes('SAĞLIK');
                        const hasYillik = turler.includes('YILLIK');
                        const hasMazeret = turler.includes('MAZERET');

                        if (hasSaglik && hasYillik) {
                            badgeBg = 'linear-gradient(135deg, #10B981 50%, #0284C7 50%)';
                        } else if (hasSaglik && hasMazeret) {
                            badgeBg = 'linear-gradient(135deg, #10B981 50%, #F59E0B 50%)';
                        } else if (hasYillik && hasMazeret) {
                            badgeBg = 'linear-gradient(135deg, #0284C7 50%, #F59E0B 50%)';
                        } else {
                            badgeBg = 'linear-gradient(135deg, #10B981 33%, #0284C7 33% 66%, #F59E0B 66%)';
                        }

                        const döküm = turler.map(t => `${ayDetay.turler[t]}G ${t}`).join(', ');
                        tooltipMetni = `${gun} Gün (${döküm})`;
                    }

                    aylarHtml += `<td style="text-align: center;"><span class="badge" style="background: ${badgeBg}; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 11.5px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); cursor: default;" title="${tooltipMetni}">${gun} Gün</span></td>`;
                } else {
                    aylarHtml += `<td style="color: var(--fg-sub); text-align: center; opacity: 0.4;">-</td>`;
                }
            }

            // İzin Türleri Dağılımı (Her türü ayrı ayrı ve renkli listele)
            const turParcalari = [];
            const turTanimlari = [
                { key: "SAĞLIK", ad: "sağlık", emoji: "🩺", renk: "#059669", count: p.saglik_gun || 0 },
                { key: "YILLIK", ad: "yıllık izin", emoji: "🏖️", renk: "#0284C7", count: p.yillik_gun || 0 },
                { key: "MAZERET", ad: "mazeret", emoji: "📝", renk: "#D97706", count: p.mazeret_gun || 0 },
                { key: "İDARİ", ad: "idari izin", emoji: "🏛️", renk: "#7C3AED", count: p.idari_gun || 0 },
                { key: "AYLIKSIZ", ad: "aylıksız izin", emoji: "⏳", renk: "#475569", count: p.ayliksiz_gun || 0 },
                { key: "DİĞER", ad: "diğer izin", emoji: "🏷️", renk: "#475569", count: p.diger_gun || 0 }
            ];

            turTanimlari.forEach(item => {
                if (item.count > 0) {
                    turParcalari.push(`<span style="color: ${item.renk}; font-weight: 700; white-space: nowrap;">${item.emoji} ${item.count} gün ${item.ad}</span>`);
                }
            });

            if (p.tur_dagilimi) {
                const bilinenler = new Set(["SAĞLIK", "YILLIK", "MAZERET", "İDARİ", "IDARI", "AYLIKSIZ", "DİĞER", "DIGER"]);
                Object.entries(p.tur_dagilimi).forEach(([tur, sayi]) => {
                    if (!bilinenler.has(tur.toUpperCase()) && sayi > 0) {
                        turParcalari.push(`<span style="color: #64748B; font-weight: 700; white-space: nowrap;">📋 ${sayi} gün ${tur.toLowerCase()}</span>`);
                    }
                });
            }

            let dagilimHtml = `<div style="font-size: 11px; line-height: 1.4;">`;
            if (turParcalari.length > 0) {
                dagilimHtml += turParcalari.join(", ");
            } else {
                dagilimHtml += `<span style="color: var(--fg-sub);">-</span>`;
            }
            dagilimHtml += `</div>`;

            // Yeni Kesinti (Sadece sağlık izinleri 7 günü aştığında!)
            let kesintiDurumuHtml = '<span style="color: var(--fg-sub); text-align: center;">-</span>';
            if (p.yeni_kesinti > 0) {
                kesintiDurumuHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;">
                    <i data-lucide="alert-triangle" style="width: 12px; height: 12px; display: inline-block; vertical-align: text-bottom; margin-right: 3px;"></i>${p.yeni_kesinti} Gün Kesilecek
                </span>`;
            }

            // Toplam Gün Rozeti
            let toplamHtml = `<span class="badge" style="background: var(--bg-soft); color: var(--fg-main); padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">${p.toplam}</span>`;
            if (p.saglik_gun >= 7) {
                toplamHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.12); color: #EF4444; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 12px;">${p.toplam}</span>`;
            } else if (p.toplam > 0) {
                toplamHtml = `<span class="badge" style="background: rgba(16, 185, 129, 0.12); color: #10B981; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">${p.toplam}</span>`;
            }

            tr.innerHTML = `
                <td style="position: sticky; left: 0; background: var(--bg-card); z-index: 1; white-space: nowrap; font-weight: bold; color: var(--fg-main);" title="${p.personel_ad}">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i data-lucide="user" style="width: 14px; height: 14px; color: var(--fg-sub);"></i>
                        <span>${p.personel_ad}</span>
                        ${unvanBadge}
                    </div>
                </td>
                ${aylarHtml}
                <td style="border-left: 2px solid var(--border); text-align: center;">${toplamHtml}</td>
                <td style="text-align: center;">${dagilimHtml}</td>
                <td style="text-align: center;">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 4px;">
                        <input type="text" inputmode="numeric" pattern="[0-9]*" class="kesinti-input" style="width: 44px; height: 28px; text-align: center; padding: 2px; font-weight: bold; background: var(--bg-soft); border: 1px solid var(--border); border-radius: 4px; outline: none; color: var(--fg-main); font-size: 12px;" 
                               value="${p.onceden_kesilen}" 
                               onchange="manuelKesintiKaydet('${p.personel_ad}', this.value)"
                               onkeypress="return event.charCode >= 48 && event.charCode <= 57">
                        <span style="color: var(--fg-sub); font-size: 11px;">G</span>
                    </div>
                </td>
                <td style="text-align: center; white-space: nowrap;">${kesintiDurumuHtml}</td>
                <td style="text-align: right;">
                    <button class="btn" style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; border: none; cursor: pointer;" onclick="saglikDetayGoster('${p.personel_ad}', ${p.onceden_kesilen})" title="Tüm İzin Geçmişi">
                        <i data-lucide="list" style="width: 13px; height: 13px;"></i> Detay
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    }
    window.saglikTablosunuCiz = saglikTablosunuCiz;

    // 6. FİLTRE YÖNETİMİ
    window.izinFiltreSec = function(filtre) {
        seciliIzinFiltresi = filtre;
        aktifGunFiltresi = null;
        izinAktifFiltreButonunuGuncelle();
        saglikTablosunuCiz();
    };

    window.izinFiltreTemizle = function() {
        seciliIzinFiltresi = "TUMU";
        aktifGunFiltresi = null;
        const ara = document.getElementById('izin_ara');
        if (ara) ara.value = "";
        izinAktifFiltreButonunuGuncelle();
        izinTakviminiCiz();
        saglikTablosunuCiz();
    };

    window.izinAramaFiltrele = function() {
        saglikTablosunuCiz();
    };

    function izinAktifFiltreButonunuGuncelle() {
        const butonlar = [
            { id: "btn_izin_filtre_tumu", f: "TUMU" },
            { id: "btn_izin_filtre_saglik", f: "SAĞLIK" },
            { id: "btn_izin_filtre_yillik", f: "YILLIK" },
            { id: "btn_izin_filtre_mazeret", f: "MAZERET" },
            { id: "btn_izin_filtre_kesinti", f: "KESINTI" }
        ];

        butonlar.forEach(b => {
            const el = document.getElementById(b.id);
            if (el) {
                if (seciliIzinFiltresi === b.f) el.classList.add("active");
                else el.classList.remove("active");
            }
        });
    }

    // 7. PERSONEL SEÇİMİ VE MEVZUAT UYARISI
    async function saglikPersonelleriniGetir() {
        if (tumIzinPersoneli && tumIzinPersoneli.length > 0) {
            saglikPersonelSelectDoldur();
            return tumIzinPersoneli;
        }
        try {
            const resp = await apiFetch(`/saglik/liste?yil=${izinAktifYil}`);
            if (resp && resp.basarili) {
                tumIzinPersoneli = resp.veri || [];
                aktifIzinPersoneli = [...tumIzinPersoneli];
                saglikPersonelSelectDoldur();
            }
        } catch (e) {
            console.error("Personel listesi alınamadı:", e);
        }
        return tumIzinPersoneli;
    }

    function saglikPersonelSelectDoldur() {
        const select = document.getElementById('saglik_personel_sec');
        if (!select) return;
        select.innerHTML = '<option value="">-- Listeden Personel Seçin --</option>';

        tumIzinPersoneli.forEach(p => {
            const unvanStr = p.unvan ? ` (${p.unvan})` : '';
            select.innerHTML += `<option value="${p.personel_ad}">${p.personel_ad}${unvanStr}</option>`;
        });
    }

    window.saglikPersonelDegisti = function() {
        saglikMevzuatUyarisiGuncelle();
    };

    window.saglikIzinTuruDegisti = function() {
        saglikMevzuatUyarisiGuncelle();
    };

    function saglikMevzuatUyarisiGuncelle() {
        const personelAd = document.getElementById('saglik_personel_sec').value;
        const izinTuru = document.getElementById('saglik_izin_turu').value;
        const mevzuatMetni = document.getElementById('saglik_mevzuat_metni');
        const mazeretKisayollari = document.getElementById('saglik_mazeret_kisayollari');
        const mevzuatKutusu = document.getElementById('saglik_mevzuat_kutusu');

        if (!mevzuatMetni) return;

        const p = tumIzinPersoneli.find(x => x.personel_ad === personelAd);
        const isOgretmen = p ? p.ogretmen_mi : true;

        if (mazeretKisayollari) {
            mazeretKisayollari.style.display = (izinTuru === "MAZERET") ? "flex" : "none";
        }

        if (izinTuru === "YILLIK" && isOgretmen) {
            mevzuatKutusu.style.background = "rgba(239, 68, 68, 0.1)";
            mevzuatKutusu.style.borderColor = "rgba(239, 68, 68, 0.3)";
            mevzuatMetni.innerHTML = `<strong style="color: #EF4444;">⚠️ Mevzuat Uyarısı (657 SK Md. 103):</strong> Öğretmenler yaz ve dinlenme tatillerinde izinli sayıldıklarından yıllık izin hakları bulunmamaktadır. Yalnızca memur ve sürekli işçilere yıllık izin verilebilir.`;
        } else if (izinTuru === "SAĞLIK") {
            mevzuatKutusu.style.background = "rgba(16, 185, 129, 0.08)";
            mevzuatKutusu.style.borderColor = "rgba(16, 185, 129, 0.25)";
            mevzuatMetni.innerHTML = `<strong>🩺 Sağlık İzni (657 SK Md. 105 &amp; 152):</strong> Tek hekim tek seferde max 10 gün, yılda tek hekimden max 40 gün rapor verebilir. Yılda toplam 7 günü aşan tek hekim raporlarında zam ve tazminat kesintisi uygulanır.`;
        } else if (izinTuru === "MAZERET") {
            mevzuatKutusu.style.background = "rgba(245, 158, 11, 0.08)";
            mevzuatKutusu.style.borderColor = "rgba(245, 158, 11, 0.25)";
            mevzuatMetni.innerHTML = `<strong>📜 Mazeret İzni (657 SK Md. 104):</strong> Evlilik: 7 gün, Babalık: 10 gün, Vefat: 7 gün (1. derece yakın), Engelli çocuk tedavisi: yılda 10 gün. Bu izinler 7 günlük maaş kesintisine kesinlikle <u>tabi değildir</u>.`;
        } else if (izinTuru === "AYLIKSIZ") {
            mevzuatKutusu.style.background = "rgba(100, 116, 139, 0.1)";
            mevzuatKutusu.style.borderColor = "rgba(100, 116, 139, 0.3)";
            mevzuatMetni.innerHTML = `<strong>⏳ Aylıksız İzin (657 SK Md. 108):</strong> Doğum sonrası 24 aya kadar, askerlik süresince veya 5 hizmet yılını dolduran memura isteğiyle 1 yıla kadar verilir.`;
        } else {
            mevzuatKutusu.style.background = "rgba(16, 185, 129, 0.08)";
            mevzuatKutusu.style.borderColor = "rgba(16, 185, 129, 0.25)";
            mevzuatMetni.innerHTML = `<strong>📋 İdari İzin:</strong> Resmi tatiller, valilik genel idari tatil kararları veya kurum görevlendirmeleri için kullanılır. Maaş kesintisi uygulanmaz.`;
        }
    }

    // Hızlı Mazeret Şablonu Uygula
    window.mazeretSablonuUygula = function(turAdi, gun) {
        const aciklamaGirdi = document.getElementById('saglik_aciklama');
        if (aciklamaGirdi) aciklamaGirdi.value = `${turAdi} Mazeret İzni`;

        document.getElementById('saglik_gun').value = gun;
        const lbl = document.getElementById('lbl_saglik_gun');
        if (lbl) lbl.textContent = `(${gun} Gün)`;

        // Eğer başlangıç tarihi seçiliyse bitiş tarihini otomatik tamamla
        if (saglikFlatpickr && saglikFlatpickr.selectedDates && saglikFlatpickr.selectedDates.length > 0) {
            const d1 = saglikFlatpickr.selectedDates[0];
            const d2 = new Date(d1.getTime() + (gun - 1) * 24 * 60 * 60 * 1000);
            saglikFlatpickr.setDate([d1, d2], true);
        }
    };

    // 8. MODAL İŞLEMLERİ
    window.saglikModalAc = function() {
        saglikPersonelSelectDoldur();
        document.getElementById('saglik_personel_sec').value = '';
        document.getElementById('saglik_izin_turu').value = 'SAĞLIK';
        document.getElementById('saglik_tarih_range').value = '';
        document.getElementById('saglik_gun').value = '1';
        document.getElementById('lbl_saglik_gun').textContent = '(1 Gün)';
        document.getElementById('saglik_aciklama').value = '';
        const belge = document.getElementById('saglik_belge_no');
        if (belge) belge.value = '';
        const elAdres = document.getElementById('saglik_izin_adresi');
        if (elAdres) elAdres.value = '';
        const elRaporTuru = document.getElementById('saglik_rapor_turu');
        if (elRaporTuru) elRaporTuru.value = '';

        saglikMevzuatUyarisiGuncelle();

        if (saglikFlatpickr) saglikFlatpickr.destroy();

        saglikFlatpickr = flatpickr(document.getElementById('saglik_tarih_range'), {
            locale: "tr",
            mode: "range",
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "d.m.Y",
            theme: "dark",
            onChange: saglikGunHesapla,
            onClose: function(selectedDates, dateStr, instance) {
                if (selectedDates && selectedDates.length === 1) {
                    instance.setDate([selectedDates[0], selectedDates[0]], true);
                }
            }
        });

        document.getElementById('modal_saglik_ekle').style.display = 'flex';
        if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
    };

    window.saglikModalKapat = function() {
        document.getElementById('modal_saglik_ekle').style.display = 'none';
    };

    function saglikGunHesapla(selectedDates) {
        let diffDays = 1;
        if (selectedDates && selectedDates.length > 0) {
            const d1 = selectedDates[0];
            const d2 = selectedDates.length > 1 ? selectedDates[1] : selectedDates[0];
            const diffTime = Math.abs(d2 - d1);
            diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        }
        document.getElementById('saglik_gun').value = diffDays;
        document.getElementById('lbl_saglik_gun').textContent = `(${diffDays} Gün)`;
    }

    // 9. PDF YÜKLEME VE ÇÖZÜMLEME
    window.saglikPdfYukle = async function(event) {
        const dosya = event.target.files ? event.target.files[0] : null;
        if (!dosya) return;

        const formData = new FormData();
        formData.append("dosya", dosya);

        if (typeof yuklemeGoster === 'function') {
            yuklemeGoster("İzin belgesi / Sağlık raporu PDF'i çözümleniyor...");
        }

        try {
            const data = await apiFetch('/saglik/pdf-oku', {
                method: 'POST',
                body: formData
            });

            if (typeof yuklemeGizle === 'function') yuklemeGizle();

            if (data.basarili) {
                await saglikPersonelleriniGetir();
                saglikModalAc();

                // Personel adını seç
                if (data.ad_soyad) {
                    const select = document.getElementById('saglik_personel_sec');
                    let eslesenValue = "";
                    const hedefClean = data.ad_soyad.toLocaleUpperCase('tr-TR').replace(/[\s\.\-_]/g, '');

                    for (let i = 0; i < select.options.length; i++) {
                        const optVal = (select.options[i].value || '').toLocaleUpperCase('tr-TR').replace(/[\s\.\-_]/g, '');
                        const optText = (select.options[i].text || '').toLocaleUpperCase('tr-TR').replace(/[\s\.\-_]/g, '');
                        if (optVal === hedefClean || optText.includes(hedefClean) || hedefClean.includes(optVal)) {
                            eslesenValue = select.options[i].value;
                            break;
                        }
                    }

                    if (eslesenValue) {
                        select.value = eslesenValue;
                    } else {
                        // Eğer select listesinde bulunamadıysa yeni seçenek olarak ekle ve seç
                        const opt = document.createElement('option');
                        opt.value = data.ad_soyad;
                        opt.textContent = `${data.ad_soyad}`;
                        opt.selected = true;
                        select.appendChild(opt);
                        select.value = data.ad_soyad;
                    }
                    saglikPersonelDegisti();
                }

                // İzin türünü seç
                if (data.izin_turu) {
                    const selTur = document.getElementById('saglik_izin_turu');
                    if (selTur) selTur.value = data.izin_turu;
                }

                // Tarihleri takvime aktar
                if (data.baslangic) {
                    const dates = [data.baslangic];
                    if (data.bitis && data.bitis !== data.baslangic) {
                        dates.push(data.bitis);
                    }
                    if (saglikFlatpickr) {
                        saglikFlatpickr.setDate(dates, true);
                    } else {
                        document.getElementById('saglik_tarih_range').value = dates.join(' - ');
                    }
                }

                // İzin adresini doldur
                if (data.izin_adresi) {
                    const elAdres = document.getElementById('saglik_izin_adresi');
                    if (elAdres) elAdres.value = data.izin_adresi;
                }

                // Rapor türünü doldur
                if (data.rapor_turu) {
                    const elRaporTuru = document.getElementById('saglik_rapor_turu');
                    if (elRaporTuru) elRaporTuru.value = data.rapor_turu;
                }

                const gunSayisi = data.gun_sayisi || 1;
                document.getElementById('saglik_gun').value = gunSayisi;
                const lblGun = document.getElementById('lbl_saglik_gun');
                if (lblGun) lblGun.textContent = `(${gunSayisi} Gün)`;

                saglikMevzuatUyarisiGuncelle();
                bildirimGoster(`PDF'ten başarıyla okundu: ${data.ad_soyad || 'Personel'} - ${data.izin_turu || 'İzin'} (${gunSayisi} Gün). Lütfen kontrol edip kaydedin.`, "basarili");
            } else {
                if (data.cakisma) {
                    bildirimGoster(data.mesaj, "uyari");
                    return;
                }
                saglikModalAc();
                bildirimGoster(data.mesaj || "PDF'ten izin bilgileri okunamadı. Lütfen formu elle doldurunuz.", "uyari");
            }
        } catch (e) {
            if (typeof yuklemeGizle === 'function') yuklemeGizle();
            bildirimGoster("PDF yüklenirken bağlantı hatası oluştu: " + e.message, "hata");
        } finally {
            if (event && event.target) event.target.value = '';
        }
    };

    // 10. İZİN KAYDET
    window.saglikKaydet = async function() {
        const personel = document.getElementById('saglik_personel_sec')?.value || '';
        const izinTuru = document.getElementById('saglik_izin_turu')?.value || '';
        const tarihDegeri = document.getElementById('saglik_tarih_range')?.value || '';
        const gunInput = document.getElementById('saglik_gun')?.value || '1';
        const aciklama = document.getElementById('saglik_aciklama')?.value || '';
        const belgeNo = document.getElementById('saglik_belge_no') ? document.getElementById('saglik_belge_no').value : "";
        const izinAdresi = document.getElementById('saglik_izin_adresi') ? document.getElementById('saglik_izin_adresi').value.trim() : "";
        const raporTuru = document.getElementById('saglik_rapor_turu') ? document.getElementById('saglik_rapor_turu').value.trim() : "";

        // 1. Ayrıştırılmış ve net alan kontrolleri
        if (!personel) {
            bildirimGoster('Lütfen listeden bir personel seçiniz.', 'uyari');
            return;
        }
        if (!izinTuru) {
            bildirimGoster('Lütfen izin türünü seçiniz.', 'uyari');
            return;
        }

        // 2. Esnek Tarih Çözümleme (Tek gün veya tarih aralığı)
        let bas = "";
        let bit = "";
        let secilenTarihler = (saglikFlatpickr && saglikFlatpickr.selectedDates) ? saglikFlatpickr.selectedDates : [];

        if (secilenTarihler.length > 0) {
            const d1 = secilenTarihler[0];
            const d2 = secilenTarihler.length > 1 ? secilenTarihler[1] : d1;
            const pad = n => String(n).padStart(2, '0');
            bas = `${d1.getFullYear()}-${pad(d1.getMonth() + 1)}-${pad(d1.getDate())}`;
            bit = `${d2.getFullYear()}-${pad(d2.getMonth() + 1)}-${pad(d2.getDate())}`;
        } else if (tarihDegeri) {
            const parcalar = tarihDegeri.split(/\s+(?:to|-|—)\s+/i);
            bas = parcalar[0].trim();
            bit = (parcalar.length > 1 ? parcalar[1] : parcalar[0]).trim();
        }

        if (window.tarihFormatlaISO) {
            if (bas) bas = window.tarihFormatlaISO(bas);
            if (bit) bit = window.tarihFormatlaISO(bit);
        }

        if (!bas) {
            bildirimGoster('Lütfen izin tarihini veya tarih aralığını seçiniz.', 'uyari');
            return;
        }
        if (!bit) bit = bas;
        if (bit < bas) {
            const tmp = bas;
            bas = bit;
            bit = tmp;
        }

        // Gün sayısını hesapla / garantiye al
        let gunSayisi = parseInt(gunInput, 10);
        if (isNaN(gunSayisi) || gunSayisi <= 0) {
            try {
                const dt1 = new Date(bas);
                const dt2 = new Date(bit);
                gunSayisi = Math.ceil(Math.abs(dt2 - dt1) / (1000 * 60 * 60 * 24)) + 1;
            } catch (err) {
                gunSayisi = 1;
            }
        }

        try {
            const response = await apiFetch('/saglik/ekle', {
                method: 'POST',
                body: {
                    personel_ad: personel,
                    izin_turu: izinTuru,
                    baslangic_tarihi: bas,
                    bitis_tarihi: bit,
                    gun_sayisi: gunSayisi,
                    aciklama: aciklama,
                    belge_no: belgeNo,
                    izin_adresi: izinAdresi,
                    rapor_turu: raporTuru
                }
            });

            if (response.basarili) {
                bildirimGoster(response.mesaj || 'İzin başarıyla eklendi.', 'basarili');
                saglikModalKapat();
                if (bas) {
                    const kayitYili = parseInt(bas.split('-')[0]);
                    if (kayitYili && !isNaN(kayitYili)) {
                        izinAktifYil = kayitYili;
                    }
                }
                saglikYukle(izinAktifYil);
            } else {
                bildirimGoster(response.mesaj || 'İzin eklenemedi.', response.cakisma ? 'uyari' : 'hata');
            }
        } catch (e) {
            bildirimGoster('Bir hata oluştu: ' + e.message, 'hata');
        }
    };

    // 11. DETAY VE GEÇMİŞ MODAL
    window.saglikDetayGoster = async function(personelAd) {
        document.getElementById('detay_personel_ad').textContent = personelAd;
        const ozetEl = document.getElementById('detay_izin_ozet');
        if (ozetEl) ozetEl.textContent = 'Yükleniyor...';

        const tbody = document.getElementById('tbody_saglik_detay');
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px;">Yükleniyor...</td></tr>';
        document.getElementById('modal_saglik_detay').style.display = 'flex';

        try {
            const response = await apiFetch(`/saglik/raporlar/${encodeURIComponent(personelAd)}?yil=${izinAktifYil}`);
            if (response.basarili) {
                tbody.innerHTML = '';
                if (response.veri.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px;">Kayıtlı izin bulunamadı.</td></tr>';
                    if (ozetEl) ozetEl.textContent = 'Kayıtlı izin bulunamadı.';
                } else {
                    let toplamDetayGun = 0;
                    const turToplamlari = {};

                    response.veri.forEach(r => {
                        const gun = r.gun || 0;
                        toplamDetayGun += gun;
                        const t = (r.izin_turu || 'SAĞLIK').toUpperCase();
                        turToplamlari[t] = (turToplamlari[t] || 0) + gun;
                    });

                    if (ozetEl) {
                        const ozetParcalari = [];
                        if (turToplamlari['SAĞLIK']) ozetParcalari.push(`🩺 ${turToplamlari['SAĞLIK']} gün sağlık`);
                        if (turToplamlari['YILLIK']) ozetParcalari.push(`🏖️ ${turToplamlari['YILLIK']} gün yıllık izin`);
                        if (turToplamlari['MAZERET']) ozetParcalari.push(`📝 ${turToplamlari['MAZERET']} gün mazeret`);
                        if (turToplamlari['İDARİ'] || turToplamlari['IDARI']) ozetParcalari.push(`🏛️ ${(turToplamlari['İDARİ'] || 0) + (turToplamlari['IDARI'] || 0)} gün idari izin`);
                        if (turToplamlari['AYLIKSIZ']) ozetParcalari.push(`⏳ ${turToplamlari['AYLIKSIZ']} gün aylıksız izin`);
                        if (turToplamlari['DİĞER'] || turToplamlari['DIGER']) ozetParcalari.push(`🏷️ ${(turToplamlari['DİĞER'] || 0) + (turToplamlari['DIGER'] || 0)} gün diğer izin`);

                        ozetEl.innerHTML = `<strong>Toplam ${toplamDetayGun} Gün İzin:</strong> <span style="color:var(--fg-main); font-weight: 600;">${ozetParcalari.join(', ')}</span>`;
                    }

                    response.veri.forEach(r => {
                        const tr = document.createElement('tr');
                        const uTur = (r.izin_turu || '').toUpperCase();
                        let turRenk = '#10B981';
                        if (uTur === 'YILLIK') turRenk = '#0284C7';
                        else if (uTur === 'MAZERET') turRenk = '#F59E0B';
                        else if (uTur === 'İDARİ' || uTur === 'IDARI') turRenk = '#8B5CF6';
                        else if (uTur === 'AYLIKSIZ' || uTur === 'DİĞER' || uTur === 'DIGER') turRenk = '#64748B';

                        let detayMetni = `<div>${r.aciklama || '-'}</div>`;
                        if (r.rapor_turu) {
                            detayMetni += `<div style="font-size:11px; color:#38BDF8; font-weight:600; margin-top:2px;">🩺 ${r.rapor_turu}</div>`;
                        }
                        if (r.izin_adresi) {
                            detayMetni += `<div style="font-size:11px; color:#F59E0B; margin-top:2px;">📍 <strong>Adres:</strong> ${r.izin_adresi}</div>`;
                        }
                        if (r.mevzuat_maddesi) {
                            detayMetni += `<div style="font-size:10.5px; color:var(--fg-sub); font-style:italic; margin-top:2px;">⚖️ ${r.mevzuat_maddesi}</div>`;
                        }
                        if (r.belge_no) {
                            detayMetni += `<div style="font-size:10px; color:var(--fg-sub); opacity:0.8;">📄 Belge: ${r.belge_no}</div>`;
                        }

                        const esc = s => (s || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');

                        tr.innerHTML = `
                            <td><span class="badge" style="background:${turRenk}; color:white; font-size:11px; padding:3px 7px; border-radius:4px; font-weight:700;">${r.izin_turu}</span></td>
                            <td>${format_tr_tarih(r.baslangic)}</td>
                            <td>${format_tr_tarih(r.bitis || r.baslangic)}</td>
                            <td style="font-weight:bold;">${r.gun} Gün</td>
                            <td>${detayMetni}</td>
                            <td style="text-align:right;">
                                <div style="display: flex; gap: 5px; justify-content: flex-end;">
                                    <button class="btn btn-icon btn-ayarlar" style="padding: 4px 8px;" onclick="saglikIzinDuzenlemeAc(${r.id}, '${esc(personelAd)}', '${r.baslangic}', '${r.bitis || r.baslangic}', ${r.gun}, '${esc(r.aciklama)}', '${r.izin_turu}', '${esc(r.belge_no)}', '${esc(r.izin_adresi)}', '${esc(r.rapor_turu)}')" title="Düzenle">
                                        <i data-lucide="edit" height="14" width="14"></i>
                                    </button>
                                    <button class="btn btn-icon btn-kirmizi" style="padding: 4px 8px;" onclick="saglikIzinSil(${r.id}, '${esc(personelAd)}')" title="Sil">
                                        <i data-lucide="trash-2" height="14" width="14"></i>
                                    </button>
                                </div>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                    if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
                }
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:16px;">Yüklenirken hata oluştu.</td></tr>';
        }
    };

    // 12. İZİN SİL
    window.saglikIzinSil = async function(id, personelAd) {
        const onay = await modernOnayGoster("İzin Silme Onayı", "Bu izin kaydını silmek istediğinize emin misiniz?", "uyari");
        if (!onay) return;

        try {
            const response = await apiFetch(`/saglik/sil/${id}`, { method: 'DELETE' });
            if (response.basarili) {
                bildirimGoster('İzin kaydı silindi.', 'basarili');
                saglikDetayGoster(personelAd);
                saglikYukle(izinAktifYil);
            } else {
                bildirimGoster('Silinemedi: ' + response.mesaj, 'hata');
            }
        } catch (e) {
            bildirimGoster('Bir hata oluştu.', 'hata');
        }
    };

    // 13. İZİN DÜZENLEME
    window.saglikIzinDuzenlemeAc = function(id, personelAd, bas, bit, gun, aciklama, tur, belgeNo, adres, raporTuru) {
        document.getElementById('duzenle_rapor_id').value = id;
        document.getElementById('duzenle_personel_ad').value = personelAd;
        document.getElementById('duzenle_izin_turu').value = tur || 'SAĞLIK';
        document.getElementById('duzenle_gun').value = gun;
        document.getElementById('duzenle_aciklama').value = aciklama === '-' ? '' : aciklama;
        const elBelge = document.getElementById('duzenle_belge_no');
        if (elBelge) elBelge.value = belgeNo || '';
        const elAdres = document.getElementById('duzenle_izin_adresi');
        if (elAdres) elAdres.value = adres || '';
        const elRaporTuru = document.getElementById('duzenle_rapor_turu');
        if (elRaporTuru) elRaporTuru.value = raporTuru || '';

        if (duzenleFlatpickr) duzenleFlatpickr.destroy();

        let defaultDates = [bas];
        if (bas !== bit) defaultDates.push(bit);

        document.getElementById('lbl_duzenle_gun').textContent = `(${gun} Gün)`;

        duzenleFlatpickr = flatpickr(document.getElementById('duzenle_tarih_range'), {
            locale: "tr",
            mode: "range",
            dateFormat: "Y-m-d",
            defaultDate: defaultDates,
            altInput: true,
            altFormat: "d.m.Y",
            theme: "dark",
            onChange: function(selectedDates) {
                let diffDays = 1;
                if (selectedDates && selectedDates.length > 0) {
                    const d1 = selectedDates[0];
                    const d2 = selectedDates.length > 1 ? selectedDates[1] : selectedDates[0];
                    const diffTime = Math.abs(d2 - d1);
                    diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                }
                document.getElementById('duzenle_gun').value = diffDays;
                document.getElementById('lbl_duzenle_gun').textContent = `(${diffDays} Gün)`;
            },
            onClose: function(selectedDates, dateStr, instance) {
                if (selectedDates && selectedDates.length === 1) {
                    instance.setDate([selectedDates[0], selectedDates[0]], true);
                }
            }
        });

        document.getElementById('modal_saglik_duzenle').style.display = 'flex';
    };

    window.saglikGuncelle = async function() {
        const id = document.getElementById('duzenle_rapor_id')?.value;
        const personelAd = document.getElementById('duzenle_personel_ad')?.value;
        const izinTuru = document.getElementById('duzenle_izin_turu')?.value;
        const tarihDegeri = document.getElementById('duzenle_tarih_range')?.value;
        const gunInput = document.getElementById('duzenle_gun')?.value;
        const aciklama = document.getElementById('duzenle_aciklama')?.value || '';
        const belgeNo = document.getElementById('duzenle_belge_no') ? document.getElementById('duzenle_belge_no').value : "";
        const adres = document.getElementById('duzenle_izin_adresi') ? document.getElementById('duzenle_izin_adresi').value.trim() : "";
        const raporTuru = document.getElementById('duzenle_rapor_turu') ? document.getElementById('duzenle_rapor_turu').value.trim() : "";

        if (!izinTuru) {
            bildirimGoster('Lütfen izin türünü seçiniz.', 'uyari');
            return;
        }

        let bas = "";
        let bit = "";
        let secilenTarihler = (duzenleFlatpickr && duzenleFlatpickr.selectedDates) ? duzenleFlatpickr.selectedDates : [];

        if (secilenTarihler.length > 0) {
            const d1 = secilenTarihler[0];
            const d2 = secilenTarihler.length > 1 ? secilenTarihler[1] : d1;
            const pad = n => String(n).padStart(2, '0');
            bas = `${d1.getFullYear()}-${pad(d1.getMonth() + 1)}-${pad(d1.getDate())}`;
            bit = `${d2.getFullYear()}-${pad(d2.getMonth() + 1)}-${pad(d2.getDate())}`;
        } else if (tarihDegeri) {
            const parcalar = tarihDegeri.split(/\s+(?:to|-|—)\s+/i);
            bas = parcalar[0].trim();
            bit = (parcalar.length > 1 ? parcalar[1] : parcalar[0]).trim();
        }

        if (window.tarihFormatlaISO) {
            if (bas) bas = window.tarihFormatlaISO(bas);
            if (bit) bit = window.tarihFormatlaISO(bit);
        }

        if (!bas) {
            bildirimGoster('Lütfen izin tarihini veya tarih aralığını seçiniz.', 'uyari');
            return;
        }
        if (!bit) bit = bas;
        if (bit < bas) {
            const tmp = bas;
            bas = bit;
            bit = tmp;
        }

        let gunSayisi = parseInt(gunInput, 10);
        if (isNaN(gunSayisi) || gunSayisi <= 0) {
            try {
                const dt1 = new Date(bas);
                const dt2 = new Date(bit);
                gunSayisi = Math.ceil(Math.abs(dt2 - dt1) / (1000 * 60 * 60 * 24)) + 1;
            } catch (err) {
                gunSayisi = 1;
            }
        }

        try {
            const response = await apiFetch(`/saglik/duzenle/${id}`, {
                method: 'PUT',
                body: {
                    personel_ad: personelAd,
                    izin_turu: izinTuru,
                    baslangic_tarihi: bas,
                    bitis_tarihi: bit,
                    gun_sayisi: gunSayisi,
                    aciklama: aciklama,
                    belge_no: belgeNo,
                    izin_adresi: adres,
                    rapor_turu: raporTuru
                }
            });

            if (response.basarili) {
                bildirimGoster('İzin kaydı güncellendi.', 'basarili');
                document.getElementById('modal_saglik_duzenle').style.display = 'none';
                saglikDetayGoster(personelAd);
                saglikYukle(izinAktifYil);
            } else {
                bildirimGoster(response.mesaj || 'Güncellenemedi.', response.cakisma ? 'uyari' : 'hata');
            }
        } catch (e) {
            bildirimGoster('Bir hata oluştu.', 'hata');
        }
    };

    // 14. MANUEL KESİNTİ KAYDET
    window.manuelKesintiKaydet = async function(personelAd, deger) {
        const kesintiDegeri = parseInt(deger) || 0;
        try {
            const response = await apiFetch('/saglik/kesinti-guncelle', {
                method: 'POST',
                body: {
                    personel_ad: personelAd,
                    onceden_kesilen: kesintiDegeri
                }
            });

            if (response.basarili) {
                saglikYukle(izinAktifYil);
            } else {
                bildirimGoster('Güncellenemedi: ' + response.mesaj, 'hata');
            }
        } catch (e) {
            bildirimGoster('Bir hata oluştu.', 'hata');
        }
    };

    // Sayfa yüklendiğinde veya hazır olduğunda takvimi otomatik çiz
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            saglikYukle();
        });
    } else {
        saglikYukle();
    }
})();
