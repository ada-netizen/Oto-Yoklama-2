let charts = {};

function getThemeColors() {
    const isDark = document.body.classList.contains('karanlik') || 
                   document.documentElement.getAttribute('data-theme') === 'gece' || 
                   (typeof karanlikMod !== 'undefined' && karanlikMod);
    return {
        text: isDark ? '#cbd5e1' : '#475569',
        grid: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
        cardBg: isDark ? '#1e293b' : '#ffffff'
    };
}

function renderChart(canvasId, type, label, labels, data, colors, isDual = false, data2 = null, label2 = null, color2 = null, isStacked = false) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    const tc = getThemeColors();

    let bg1;
    if (type === 'line') {
        bg1 = 'rgba(59, 130, 246, 0.15)';
    } else if (type === 'bar' && (isDual || isStacked)) {
        bg1 = Array.isArray(colors) ? colors[0] : (colors || '#10b981');
    } else {
        bg1 = colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f43f5e'];
    }

    let border1;
    if (type === 'line') {
        border1 = Array.isArray(colors) ? colors[0] : (colors || '#3b82f6');
    } else if (type === 'pie' || type === 'doughnut') {
        border1 = tc.cardBg;
    } else {
        border1 = 'transparent';
    }

    let datasets = [{
        label: label,
        data: data,
        backgroundColor: bg1,
        borderColor: border1,
        borderWidth: (type === 'pie' || type === 'doughnut') ? 2 : (type === 'line' ? 2 : 0),
        tension: 0.35,
        fill: type === 'line'
    }];

    if (isDual && data2) {
        let bg2;
        if (type === 'bar') {
            bg2 = Array.isArray(color2) ? color2[0] : (color2 || '#ef4444');
        } else {
            bg2 = 'rgba(16, 185, 129, 0.15)';
        }

        let border2;
        if (type === 'line') {
            border2 = Array.isArray(color2) ? color2[0] : (color2 || '#10b981');
        } else {
            border2 = 'transparent';
        }

        datasets.push({
            label: label2,
            data: data2,
            borderColor: border2,
            backgroundColor: bg2,
            borderWidth: type === 'line' ? 2 : 0,
            tension: 0.35,
            fill: type === 'line'
        });
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    bottom: (canvasId === 'chart_sube') ? 14 : 0
                }
            },
            plugins: {
                legend: { 
                    display: (canvasId === 'chart_tur') ? false : true,
                    position: (type === 'pie' || type === 'doughnut') ? 'right' : 'top',
                    labels: { 
                        color: tc.text, 
                        font: { size: 10, family: 'Inter, system-ui, sans-serif' },
                        boxWidth: 10,
                        padding: 6
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(148, 163, 184, 0.25)',
                    borderWidth: 1,
                    padding: 8,
                    cornerRadius: 6,
                    callbacks: {
                        label: function(c) {
                            const dLabel = c.dataset.label || '';
                            const val = c.raw !== undefined ? c.raw : c.parsed;
                            if (type === 'pie' || type === 'doughnut') {
                                const allData = c.dataset.data || [];
                                const total = allData.reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                                return ` ${c.label}: ${val} Gün (%${pct})`;
                            }
                            if (type === 'bar') {
                                return ` ${dLabel || c.label}: ${val} Gün`;
                            }
                            return ` ${dLabel || c.label}: ${val}`;
                        },
                        footer: function(tooltipItems) {
                            if (canvasId === 'chart_sube' && tooltipItems.length > 0) {
                                const idx = tooltipItems[0].dataIndex;
                                const subeInfo = (window.aktifSubeOrtalamalar || [])[idx];
                                if (subeInfo) {
                                    const toplamG = Math.round((subeInfo.ozursuz_toplam + subeInfo.ozurlu_toplam) * 10) / 10;
                                    return `Sınıf Ort: ${subeInfo.ortalama} Gün\n(Toplam: ${toplamG}G / ${subeInfo.ogrenci_sayisi} Öğrenci)`;
                                }
                            }
                            if (canvasId === 'chart_gunluk' && tooltipItems.length > 1) {
                                let total = 0;
                                tooltipItems.forEach(t => { total += (t.raw || 0); });
                                return `Toplam: ${Math.round(total * 10) / 10} Gün`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: (type === 'pie' || type === 'doughnut' || type === 'radar') ? {} : {
                x: { 
                    stacked: isStacked, 
                    ticks: { 
                        color: tc.text, 
                        font: { size: 9, family: 'Inter, system-ui, sans-serif' },
                        autoSkip: canvasId === 'chart_sube' ? false : true,
                        maxRotation: canvasId === 'chart_sube' ? 50 : 45,
                        minRotation: canvasId === 'chart_sube' ? 35 : 0
                    }, 
                    grid: { color: tc.grid } 
                },
                y: { 
                    stacked: isStacked, 
                    ticks: { 
                        color: tc.text, 
                        font: { size: 9, family: 'Inter, system-ui, sans-serif' } 
                    }, 
                    grid: { color: tc.grid } 
                }
            }
        }
    });
}

// ================= DEVAMSIZLIK TÜRLERİ İNTERAKTİF FİLTRE VE RENK SİSTEMİ =================
const TUR_TANIMLARI = {
    'D':  { kod: 'D',  ad: 'D (Devamsız)',   grup: 'ozursuz', renk: '#dc2626' },
    'SY': { kod: 'SY', ad: 'SY (Sabah Y.)',  grup: 'ozursuz', renk: '#ea580c' },
    'ÖY': { kod: 'ÖY', ad: 'ÖY (Öğle Y.)',   grup: 'ozursuz', renk: '#f97316' },
    'G':  { kod: 'G',  ad: 'G (Geç Kalma)',  grup: 'ozursuz', renk: '#eab308' },
    'S':  { kod: 'S',  ad: 'S (Raporlu)',    grup: 'ozurlu',  renk: '#059669' },
    'SV': { kod: 'SV', ad: 'SV (Sevkli)',    grup: 'ozurlu',  renk: '#10b981' },
    'İ':  { kod: 'İ',  ad: 'İ (İzinli)',     grup: 'ozurlu',  renk: '#06b6d4' },
    'I':  { kod: 'I',  ad: 'İ (İzinli)',     grup: 'ozurlu',  renk: '#06b6d4' },
    'N':  { kod: 'N',  ad: 'N (Nöbetçi)',    grup: 'diger',   renk: '#8b5cf6' },
    'F':  { kod: 'F',  ad: 'F (Faaliyet)',   grup: 'diger',   renk: '#6366f1' }
};

const GRUP_TANIMLARI = {
    'ozursuz': { ad: 'Özürsüz', renk: '#dc2626', sirasi: 1 },
    'ozurlu':  { ad: 'Özürlü (Sağlık/İzin)', renk: '#059669', sirasi: 2 },
    'diger':   { ad: 'Diğer / Muaf', renk: '#8b5cf6', sirasi: 3 }
};

window.aktifTurSecimleri = null;
window.hamTurDevVerileri = [];

function cizChartTurVePaneli() {
    const raw = window.hamTurDevVerileri || [];
    if (!window.aktifTurSecimleri) {
        window.aktifTurSecimleri = {};
        raw.forEach(d => { window.aktifTurSecimleri[d.tur] = true; });
    }

    // Sıralama
    const turSirasi = ['D', 'SY', 'ÖY', 'G', 'S', 'SV', 'İ', 'I', 'N', 'F'];
    const siraliHam = [...raw].sort((a, b) => {
        const idxA = turSirasi.indexOf(a.tur) !== -1 ? turSirasi.indexOf(a.tur) : 99;
        const idxB = turSirasi.indexOf(b.tur) !== -1 ? turSirasi.indexOf(b.tur) : 99;
        return idxA - idxB;
    });

    // Filtrelenmiş liste
    const seciliTurler = siraliHam.filter(d => window.aktifTurSecimleri[d.tur] !== false);
    
    // 1. Doughnut grafiğini çiz
    if (seciliTurler.length > 0) {
        const turLabels = seciliTurler.map(d => (TUR_TANIMLARI[d.tur] ? TUR_TANIMLARI[d.tur].ad : d.tur));
        const turData = seciliTurler.map(d => d.toplam);
        const turColors = seciliTurler.map(d => (TUR_TANIMLARI[d.tur] ? TUR_TANIMLARI[d.tur].renk : '#64748b'));
        renderChart('chart_tur', 'doughnut', 'Gün', turLabels, turData, turColors);
    } else {
        if (charts['chart_tur']) {
            charts['chart_tur'].destroy();
            delete charts['chart_tur'];
        }
    }

    // 2. Legend / Filtre Panelini Çiz
    const panelEl = document.getElementById('tur_filtre_paneli');
    if (!panelEl) return;

    // Gruplara ayır
    const gruplar = {
        'ozursuz': { ...GRUP_TANIMLARI.ozursuz, items: [], toplam: 0 },
        'ozurlu':  { ...GRUP_TANIMLARI.ozurlu,  items: [], toplam: 0 },
        'diger':   { ...GRUP_TANIMLARI.diger,   items: [], toplam: 0 }
    };

    siraliHam.forEach(d => {
        const meta = TUR_TANIMLARI[d.tur] || { kod: d.tur, ad: d.tur, grup: 'diger', renk: '#64748b' };
        const gKey = gruplar[meta.grup] ? meta.grup : 'diger';
        gruplar[gKey].items.push({ ...d, meta: meta });
        gruplar[gKey].toplam += (parseFloat(d.toplam) || 0);
    });

    let html = '';
    const grupKeys = ['ozursuz', 'ozurlu', 'diger'];
    grupKeys.forEach(gKey => {
        const g = gruplar[gKey];
        if (g.items.length === 0) return;

        const tumSecili = g.items.every(t => window.aktifTurSecimleri[t.tur] !== false);

        html += `
        <div style="background: var(--bg-card-solid); border: 1px solid var(--border); border-radius: 6px; padding: 6px 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; padding-bottom: 4px; border-bottom: 1px solid var(--border);">
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-weight: 700; color: ${g.renk}; user-select: none;">
                    <input type="checkbox" onchange="grupSecimDegistir('${gKey}', this.checked)" ${tumSecili ? 'checked' : ''} style="cursor: pointer; accent-color: ${g.renk}; margin: 0;">
                    <span>${g.ad}</span>
                </label>
                <span style="font-size: 10px; font-weight: 700; color: var(--fg-sub);">${g.toplam.toFixed(1)}G</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 3px; padding-left: 4px;">
        `;

        g.items.forEach(t => {
            const isChecked = window.aktifTurSecimleri[t.tur] !== false;
            const tAd = t.meta.ad;
            const tRenk = t.meta.renk;
            html += `
                <label style="display: flex; align-items: center; justify-content: space-between; gap: 4px; cursor: pointer; user-select: none; padding: 2px 0;">
                    <span style="display: flex; align-items: center; gap: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <input type="checkbox" onchange="turSecimDegistir('${t.tur}', this.checked)" ${isChecked ? 'checked' : ''} style="cursor: pointer; accent-color: ${tRenk}; margin: 0;">
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${tRenk}; flex-shrink: 0;"></span>
                        <span style="font-size: 11px; color: var(--fg-main); overflow: hidden; text-overflow: ellipsis;">${tAd}</span>
                    </span>
                    <span style="font-size: 10px; color: var(--fg-sub); font-family: monospace; flex-shrink: 0;">${t.toplam}G</span>
                </label>
            `;
        });

        html += `
            </div>
        </div>
        `;
    });

    panelEl.innerHTML = html;
}

function turSecimDegistir(turKod, checked) {
    if (!window.aktifTurSecimleri) window.aktifTurSecimleri = {};
    window.aktifTurSecimleri[turKod] = checked;
    cizChartTurVePaneli();
}

function grupSecimDegistir(grupKey, checked) {
    if (!window.aktifTurSecimleri) window.aktifTurSecimleri = {};
    const raw = window.hamTurDevVerileri || [];
    raw.forEach(d => {
        const meta = TUR_TANIMLARI[d.tur] || { grup: 'diger' };
        if (meta.grup === grupKey) {
            window.aktifTurSecimleri[d.tur] = checked;
        }
    });
    cizChartTurVePaneli();
}

function tumTurleriSec(durum) {
    if (!window.aktifTurSecimleri) window.aktifTurSecimleri = {};
    const raw = window.hamTurDevVerileri || [];
    raw.forEach(d => {
        window.aktifTurSecimleri[d.tur] = durum;
    });
    cizChartTurVePaneli();
}

function dashboardYukle() {
    apiFetch('/istatistikler')
    .then(data => {
        if(data.hata) {
            console.error("Dashboard veri hatası:", data.hata);
            return;
        }
        
        // KPIs
        if(document.getElementById('kpi_ozursuz')) document.getElementById('kpi_ozursuz').innerText = data.kpis ? data.kpis.ozursuz_10 : 0;
        if(document.getElementById('kpi_kalan')) document.getElementById('kpi_kalan').innerText = data.kpis ? data.kpis.toplam_30 : 0;
        if(document.getElementById('kpi_sifir')) document.getElementById('kpi_sifir').innerText = data.kpis ? data.kpis.sifir_hata : 0;
        if(document.getElementById('kpi_evrak')) document.getElementById('kpi_evrak').innerText = data.kpis ? data.kpis.toplam_evrak : 0;

        // 8. Kritik Eşik Erken Uyarı Verileri & Otomatik Akıllı Kategori Seçimi
        window.aktifKritikEsikler = data.kritik_esikler || {};
        if (document.getElementById('dashboard_kritik_ogrenciler_body')) {
            const k = window.aktifKritikEsikler;
            // Eğer şu an seçili olan kategori boşsa ve başka bir eşik doluysa, dolu olan öncelikli eşiği seç
            const seciliSayi = (k[window.aktifKritikKategori] || []).length;
            if (seciliSayi === 0) {
                if ((k.asanlar_10 || []).length > 0) {
                    window.aktifKritikKategori = 'asanlar_10';
                } else if ((k.ramakkala_10 || []).length > 0) {
                    window.aktifKritikKategori = 'ramakkala_10';
                } else if ((k.mektup_siniri_5 || []).length > 0) {
                    window.aktifKritikKategori = 'mektup_siniri_5';
                } else if ((k.toplam_risk_25 || []).length > 0) {
                    window.aktifKritikKategori = 'toplam_risk_25';
                }
            }
            kritikEsikKategorisiDegistir(window.aktifKritikKategori);
        }

        // Grafikleri güvenli render et
        try {
            // 1. Aylik Trend (Dual Line)
            const ayLabels = (data.aylik_trend || []).map(d => d.ay);
            const ayDevData = (data.aylik_trend || []).map(d => d.toplam);
            const ayEvrakData = (data.aylik_evrak || []).map(d => d.toplam);
            renderChart('chart_aylik', 'line', 'Devamsızlık Miktarı', ayLabels, ayDevData, '#3b82f6', true, ayEvrakData, 'Üretilen Evrak', '#10b981');
        } catch(e) { console.error('Aylık trend çizim hatası:', e); }
        
        try {
            // 2. Gunluk Trend (Haftanın Günlerine Göre Stacked Özürlü & Özürsüz)
            const gunLabels = (data.haftanin_gunleri || []).map(d => d.gun);
            const gunOzurlu = (data.haftanin_gunleri || []).map(d => d.ozurlu !== undefined ? d.ozurlu : 0);
            const gunOzursuz = (data.haftanin_gunleri || []).map(d => d.ozursuz !== undefined ? d.ozursuz : d.toplam);
            renderChart('chart_gunluk', 'bar', 'Özürlü', gunLabels, gunOzurlu, '#10b981', true, gunOzursuz, 'Özürsüz', '#ef4444', true);
        } catch(e) { console.error('Günlük trend çizim hatası:', e); }

        try {
            // 3. Sube Ortalamalar (Stacked Bar - Özürlü Yeşil + Özürsüz Kırmızı)
            window.aktifSubeOrtalamalar = data.sube_ortalamalar || [];
            const subeLabels = (data.sube_ortalamalar || []).map(d => d.sube);
            const subeOzurlu = (data.sube_ortalamalar || []).map(d => d.ozurlu_ort);
            const subeOzursuz = (data.sube_ortalamalar || []).map(d => d.ozursuz_ort);
            renderChart('chart_sube', 'bar', 'Özürlü Ortalama', subeLabels, subeOzurlu, '#10b981', true, subeOzursuz, 'Özürsüz Ortalama', '#ef4444', true);
        } catch(e) { console.error('Şube ortalamaları çizim hatası:', e); }
        
        try {
            // 4. Tür Devamsızlık (İnteraktif Gruplu Checkbox ve Ahenkli Renk Paletleri)
            window.hamTurDevVerileri = [...(data.tur_dev || [])];
            if (!window.aktifTurSecimleri) {
                window.aktifTurSecimleri = {};
                window.hamTurDevVerileri.forEach(d => {
                    window.aktifTurSecimleri[d.tur] = true;
                });
            }
            cizChartTurVePaneli();
        } catch(e) { console.error('Tür devamsızlık çizim hatası:', e); }
        
        try {
            // 5. Özürlü vs Özürsüz Oranı (Pasta Grafiği)
            const ozurluGun = data.ozurlu_vs_ozursuz ? (data.ozurlu_vs_ozursuz.ozurlu || 0) : 0;
            const ozursuzGun = data.ozurlu_vs_ozursuz ? (data.ozurlu_vs_ozursuz.ozursuz || 0) : 0;
            const toplamDev = Math.round((ozurluGun + ozursuzGun) * 10) / 10;
            const ozurluYuzde = toplamDev > 0 ? ((ozurluGun / toplamDev) * 100).toFixed(1) : '0.0';
            const ozursuzYuzde = toplamDev > 0 ? ((ozursuzGun / toplamDev) * 100).toFixed(1) : '0.0';

            const ozLabels = ['Özürlü Devamsızlık', 'Özürsüz Devamsızlık'];
            const ozData = [ozurluGun, ozursuzGun];
            renderChart('chart_ozurlu_oran', 'pie', 'Devamsızlık', ozLabels, ozData, ['#10b981', '#ef4444']);

            const badgeEl = document.getElementById('ozurlu_oran_badge');
            if (badgeEl) {
                badgeEl.innerHTML = `Toplam: <b>${toplamDev}G</b> (<span style="color:#10b981;">Özürlü: ${ozurluGun}G - %${ozurluYuzde}</span> / <span style="color:#ef4444;">Özürsüz: ${ozursuzGun}G - %${ozursuzYuzde}</span>)`;
            }
        } catch(e) { console.error('Özürlü oran çizim hatası:', e); }
        
        // 6. Riskli Ogrenciler
        const tbodyRiskli = document.getElementById('tbody_riskli');
        if(tbodyRiskli && data.riskli_ogrenciler) {
            tbodyRiskli.innerHTML = data.riskli_ogrenciler.map(o => `
                <tr>
                    <td>${o.ad}</td>
                    <td>${o.sube}</td>
                    <td><span class="badge" style="background: #fef3c7; color: #d97706;">${o.toplam}</span></td>
                </tr>
            `).join('');
        }
        
        // 7. G Turu Riskli
        const tbodyGRiskli = document.getElementById('tbody_g_riskli');
        if(tbodyGRiskli && data.g_turu_riskli) {
            tbodyGRiskli.innerHTML = data.g_turu_riskli.map(o => `
                <tr>
                    <td>${o.ad}</td>
                    <td>${o.sube}</td>
                    <td><span class="badge" style="background: #fee2e2; color: #b91c1c;">${o.toplam}</span></td>
                </tr>
            `).join('');
        }

        // 8. Yeni Analitikler: Risk Piramidi
        if (data.risk_piramidi) cizRiskPiramidi(data.risk_piramidi);

        // 9. Yeni Analitikler: Kademe Analizi
        if (data.kademe_analizi) cizKademeGrafigi(data.kademe_analizi);

        // 10. Yeni Analitikler: Geç Kalma Alarmı
        if (data.gec_kalma_alarmi) cizGecKalmaAlarmi(data.gec_kalma_alarmi);

        // 11. Yeni Analitikler: Şampiyon Şubeler
        if (data.sampiyon_subeler) cizSampiyonSubeler(data.sampiyon_subeler);

        // 12. Resmi Tebligat / Mektup Takip Çizelgesi (5., 15., 25. Gün)
        if (data.mektup_takip) {
            mektupTakipCizelgesiniDoldur(data.mektup_takip);
        }

        // Dinamik yerleşim ve boyutlandırma ayarlarını uygula ve olayları bağla
        yukleDashboardYerlesimi();
        baglaDashboardOlaylari();
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();

    })
    .catch(err => {
        console.error("Dashboard yüklenirken hata oluştu:", err);
    });
}

window.aktifKritikEsikler = {};
window.aktifKritikKategori = 'ramakkala_10';

function kritikEsikKategorisiDegistir(kategori) {
    window.aktifKritikKategori = kategori;
    
    // Buton stillerini güncelle
    const butonlar = [
        { id: 'btn_esik_ramakkala_10', kat: 'ramakkala_10', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
        { id: 'btn_esik_asanlar_10', kat: 'asanlar_10', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)' },
        { id: 'btn_esik_mektup_5', kat: 'mektup_siniri_5', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
        { id: 'btn_esik_toplam_25', kat: 'toplam_risk_25', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)' }
    ];
    
    butonlar.forEach(b => {
        const btnEl = document.getElementById(b.id);
        if (!btnEl) return;
        if (b.kat === kategori) {
            btnEl.classList.add('aktif');
            btnEl.style.background = b.bg;
            btnEl.style.color = b.color;
            btnEl.style.border = `1px solid ${b.color}`;
            btnEl.style.fontWeight = '700';
        } else {
            btnEl.classList.remove('aktif');
            btnEl.style.background = 'var(--bg-main)';
            btnEl.style.color = 'var(--fg-main)';
            btnEl.style.border = '1px solid var(--border)';
            btnEl.style.fontWeight = '500';
        }
    });
    
    kritikEsikTablosuCiz();
}

function kritikEsikTablosuCiz() {
    const tbody = document.getElementById('dashboard_kritik_ogrenciler_body');
    if (!tbody) return;
    
    const k = window.aktifKritikEsikler || {};
    const veriler = k[window.aktifKritikKategori] || [];
    
    // Sayı sayaçlarını güncelle
    const b1 = document.getElementById('sayi_ramakkala_10');
    const b2 = document.getElementById('sayi_asanlar_10');
    const b3 = document.getElementById('sayi_mektup_5');
    const b4 = document.getElementById('sayi_toplam_25');
    if (b1) b1.innerText = (k.ramakkala_10 || []).length;
    if (b2) b2.innerText = (k.asanlar_10 || []).length;
    if (b3) b3.innerText = (k.mektup_siniri_5 || []).length;
    if (b4) b4.innerText = (k.toplam_risk_25 || []).length;
    
    if (veriler.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--fg-sub); font-style: italic;"><i data-lucide="check-circle" style="color: #10B981; vertical-align: middle; margin-right: 6px;"></i>Bu eşik kategorisinde riskli öğrenci bulunmamaktadır. Harika!</td></tr>`;
        if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
        return;
    }
    
    tbody.innerHTML = veriler.map(o => {
        const adAttr = (o.ad || '').replace(/"/g, '&quot;');
        const subeAttr = (o.sube || '').replace(/"/g, '&quot;');
        const badgeBg = o.ozursuz >= 10 ? '#fee2e2' : (o.ozursuz >= 8.5 ? '#ffedd5' : '#fef3c7');
        const badgeColor = o.ozursuz >= 10 ? '#b91c1c' : (o.ozursuz >= 8.5 ? '#c2410c' : '#b45309');

        return `
        <tr style="border-bottom: 1px solid var(--border); transition: background 0.15s;">
            <td style="padding: 10px 12px; font-weight: 600;">${o.sube}</td>
            <td style="padding: 10px 12px; font-weight: bold; color: var(--fg-sub);">${o.no}</td>
            <td style="padding: 10px 12px; font-weight: 600; color: var(--fg-main);">${o.ad}</td>
            <td style="padding: 10px 12px; text-align: center;">
                <span class="badge" style="background: ${badgeBg}; color: ${badgeColor}; font-weight: bold; padding: 3px 8px; border-radius: 6px;">${o.ozursuz} Gün</span>
            </td>
            <td style="padding: 10px 12px; text-align: center; color: var(--fg-sub);">${o.ozurlu} Gün</td>
            <td style="padding: 10px 12px; text-align: center; font-weight: bold;">${o.toplam} Gün</td>
            <td style="padding: 10px 12px; text-align: right; white-space: nowrap;">
                <button class="btn btn-temizle" data-no="${o.no}" data-ad="${adAttr}" data-sube="${subeAttr}" data-ozsz="${o.ozursuz}" data-topt="${o.toplam}" onclick="veliMetniKopyala(this.dataset.no, this.dataset.ad, this.dataset.sube, this.dataset.ozsz, this.dataset.topt)" title="Veli WhatsApp/SMS Bilgilendirme Metnini Kopyala" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;">
                    <i data-lucide="copy" height="12" width="12"></i> Veli Metni
                </button>
                <button class="btn btn-dev" data-no="${o.no}" data-ad="${adAttr}" onclick="if (typeof yillikListeAc === 'function') yillikListeAc(this.dataset.no, this.dataset.ad);" title="Devamsızlık Karnesini Aç" style="padding: 4px 8px; font-size: 11px;">
                    <i data-lucide="eye" height="12" width="12"></i> İncele
                </button>
            </td>
        </tr>
        `;
    }).join('');
    
    if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
}

function veliMetniKopyala(no, ad, sube, ozsz, topt) {
    const bugun = new Date().toLocaleDateString('tr-TR');
    const ozszNum = parseFloat(ozsz) || 0;
    let uyariMetni = "devamsızlığı kritik eşiğe yaklaşmıştır.";
    if (ozszNum >= 10.0) {
        uyariMetni = "MEB Ortaöğretim Kurumları Yönetmeliği gereğince özürsüz 10 günü aştığı için sınıf tekrarı riski bulunmaktadır.";
    } else if (ozszNum >= 8.5) {
        uyariMetni = "özürsüz 10 günlük yasal sınıra ramak kalmıştır (kalan hak: " + (Math.round((10 - ozszNum) * 10) / 10) + " gün).";
    } else if (ozszNum >= 4.5) {
        uyariMetni = "1. Veli Bilgilendirme Mektubu (5 gün) sınırına ulaşmıştır.";
    }
    
    const metin = `Sayın Velimiz; ${sube} şubesi ${no} numaralı öğrencimiz ${ad}, ${bugun} tarihi itibariyle ${ozsz} gün özürsüz, toplam ${topt} gün devamsızlığa ulaşmıştır. ${uyariMetni} Bilgilerinize rica ederiz.`;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(metin).then(() => {
            if (typeof bildirimGoster === 'function') bildirimGoster(`${ad} için veli bilgilendirme metni panoya kopyalandı!`, 'bilgi');
        }).catch(() => fallbackKopyala(metin, ad));
    } else {
        fallbackKopyala(metin, ad);
    }
}

function fallbackKopyala(metin, ad) {
    const ta = document.createElement('textarea');
    ta.value = metin;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    if (typeof bildirimGoster === 'function') bildirimGoster(`${ad} için veli metni panoya kopyalandı!`, 'bilgi');
}

async function arsivle() {
    const ad = document.getElementById('arsiv_adi').value.trim();
    if(!ad) {
        if(typeof bildirimGoster === 'function') bildirimGoster('Lütfen arşiv adı girin!', 'hata');
        return;
    }
    
    const onay = await modernOnayGoster("Yıllık Arşivleme & Sıfırlama", `DİKKAT! Tüm öğrenci, devamsızlık ve üretilen evrak verileri "${ad}" klasörüne kopyalanıp sıfırlanacak. Personel listesi KORUNACAK. Onaylıyor musunuz?`, "uyari");
    if(!onay) return;
    
    apiFetch('/arsivle', {
        method: 'POST',
        body: { arsiv_adi: ad }
    })
    .then(data => {
        if(typeof bildirimGoster === 'function') {
            if(data.basarili) {
                bildirimGoster(data.mesaj, 'bilgi');
                setTimeout(() => location.reload(), 2000);
            } else {
                bildirimGoster(data.mesaj, 'hata');
            }
        }
    });
}

// ================= DASHBOARD DİNAMİK YERLEŞİM & SÜRÜKLE-BOYUTLANDIR =================
window.dashboardDuzenlemeModu = false;

const DASH_DEFAULT_LAYOUT = {
    order: [
        'w_mektup_takip',
        'w_risk_piramidi',
        'w_chart_kademe',
        'w_gec_kalma_alarmi',
        'w_sampiyon_subeler',
        'w_chart_aylik',
        'w_chart_gunluk',
        'w_chart_tur',
        'w_chart_sube',
        'w_chart_ozurlu_oran',
        'w_g_riskli',
        'w_riskli_ogrenciler'
    ],
    sizes: {
        'w_mektup_takip':      { flex: '0 0 100%', width: '100%', height: '' },
        'w_risk_piramidi':     { flex: '0 0 calc(50% - 8px)', width: 'calc(50% - 8px)', height: '340px' },
        'w_chart_kademe':      { flex: '0 0 calc(50% - 8px)', width: 'calc(50% - 8px)', height: '340px' },
        'w_gec_kalma_alarmi':  { flex: '0 0 calc(50% - 8px)', width: 'calc(50% - 8px)', height: '340px' },
        'w_sampiyon_subeler':  { flex: '0 0 calc(50% - 8px)', width: 'calc(50% - 8px)', height: '340px' },
        'w_chart_aylik':       { flex: '0 0 calc(66.666% - 8px)', width: 'calc(66.666% - 8px)', height: '320px' },
        'w_chart_gunluk':      { flex: '0 0 calc(33.333% - 11px)', width: 'calc(33.333% - 11px)', height: '320px' },
        'w_chart_tur':         { flex: '0 0 calc(33.333% - 11px)', width: 'calc(33.333% - 11px)', height: '330px' },
        'w_chart_sube':        { flex: '0 0 calc(33.333% - 11px)', width: 'calc(33.333% - 11px)', height: '330px' },
        'w_chart_ozurlu_oran': { flex: '0 0 calc(33.333% - 11px)', width: 'calc(33.333% - 11px)', height: '330px' },
        'w_g_riskli':          { flex: '0 0 calc(33.333% - 11px)', width: 'calc(33.333% - 11px)', height: '320px' },
        'w_riskli_ogrenciler': { flex: '0 0 calc(66.666% - 8px)', width: 'calc(66.666% - 8px)', height: '320px' }
    }
};

function dashboardDuzenlemeModuToggle() {
    window.dashboardDuzenlemeModu = !window.dashboardDuzenlemeModu;
    const container = document.getElementById('dashboard_widget_container');
    const btn = document.getElementById('btn_dash_duzenle');
    const lbl = document.getElementById('lbl_dash_duzenle');

    if (window.dashboardDuzenlemeModu) {
        if (container) container.classList.add('dashboard-duzenle-aktif');
        if (btn) {
            btn.style.background = '#0284c7';
            btn.style.color = '#ffffff';
        }
        if (lbl) lbl.innerText = 'Düzeni Tamamla';
        if (typeof bildirimGoster === 'function') {
            bildirimGoster('Düzenleme Modu: Kartları sol tutamaçtan sürükleyerek taşıyabilir, sağ-alt köşeden en ve boyunu serbestçe değiştirebilirsiniz.', 'bilgi');
        }
    } else {
        if (container) container.classList.remove('dashboard-duzenle-aktif');
        if (btn) {
            btn.style.background = '';
            btn.style.color = '';
        }
        if (lbl) lbl.innerText = 'Yerleşimi Düzenle';
        kaydetDashboardYerlesimi();
        if (typeof bildirimGoster === 'function') {
            bildirimGoster('Yerleşim ve boyut ayarları kaydedildi.', 'basarili');
        }
    }
    resizeTumGrafikler();
    if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
}

function kaydetDashboardYerlesimi() {
    const container = document.getElementById('dashboard_widget_container');
    if (!container) return;

    const cards = Array.from(container.querySelectorAll('.dash-card[data-widget-id]'));
    const order = cards.map(c => c.getAttribute('data-widget-id'));
    const sizes = {};

    cards.forEach(c => {
        const id = c.getAttribute('data-widget-id');
        sizes[id] = {
            flex: c.style.flex || '',
            width: c.style.width || '',
            height: c.style.height || ''
        };
    });

    localStorage.setItem('oto_yoklama_dashboard_layout_v4', JSON.stringify({ order, sizes }));
}

function yukleDashboardYerlesimi() {
    const container = document.getElementById('dashboard_widget_container');
    if (!container) return;

    let saved = null;
    try {
        const raw = localStorage.getItem('oto_yoklama_dashboard_layout_v4');
        if (raw) saved = JSON.parse(raw);
    } catch(e) { console.error('Yerleşim yükleme hatası:', e); }

    const layout = saved || DASH_DEFAULT_LAYOUT;
    if (layout.order && Array.isArray(layout.order) && !layout.order.includes('w_mektup_takip')) {
        layout.order.unshift('w_mektup_takip');
    }

    // Sıralamayı uygula
    if (layout.order && Array.isArray(layout.order)) {
        layout.order.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.parentElement === container) {
                container.appendChild(el);
            }
        });
    }

    // Boyutları uygula
    if (layout.sizes) {
        Object.keys(layout.sizes).forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                const s = layout.sizes[id];
                if (s.flex) el.style.flex = s.flex;
                if (s.width) el.style.width = s.width;
                if (s.height) el.style.height = s.height;
                guncelleBoyutButonDurumu(el, s.width);
            }
        });
    }

    resizeTumGrafikler();
}

function dashboardYerlesimiSifirla() {
    localStorage.removeItem('oto_yoklama_dashboard_layout_v4');
    const container = document.getElementById('dashboard_widget_container');
    if (!container) return;

    // Varsayılan sıralama ve boyutlar
    DASH_DEFAULT_LAYOUT.order.forEach(id => {
        const el = document.getElementById(id);
        if (el && el.parentElement === container) {
            container.appendChild(el);
            const defSize = DASH_DEFAULT_LAYOUT.sizes[id] || {};
            el.style.flex = defSize.flex || '';
            el.style.width = defSize.width || '';
            el.style.height = defSize.height || '';
            guncelleBoyutButonDurumu(el, defSize.width || '');
        }
    });

    resizeTumGrafikler();
    if (typeof bildirimGoster === 'function') {
        bildirimGoster('Dashboard yerleşimi ve boyutları fabrika ayarlarına sıfırlandı.', 'bilgi');
    }
}

// ---------------- YENİ ANALİTİK ÇİZİM FONKSİYONLARI ----------------
function cizRiskPiramidi(piramitVerisi) {
    const container = document.getElementById('container_risk_piramidi');
    if (!container || !Array.isArray(piramitVerisi)) return;

    container.innerHTML = piramitVerisi.map(item => `
        <div style="background: var(--bg-card-solid); border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
                <span style="font-weight: 600; color: var(--fg-main); display: flex; align-items: center; gap: 5px;">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${item.renk};"></span>
                    ${item.kademe} <span style="color: var(--fg-sub); font-size: 10px;">(${item.aralik})</span>
                </span>
                <span style="font-weight: 700; color: var(--fg-main);">
                    ${item.sayi} Öğrenci 
                    <span style="background: ${item.renk}22; color: ${item.renk}; border-radius: 4px; padding: 1px 5px; font-size: 10px; margin-left: 4px;">%${item.yuzde}</span>
                </span>
            </div>
            <div style="width: 100%; height: 6px; background: rgba(0,0,0,0.1); border-radius: 3px; overflow: hidden;">
                <div style="width: ${Math.min(100, item.yuzde)}%; height: 100%; background: ${item.renk}; border-radius: 3px; transition: width 0.4s ease;"></div>
            </div>
        </div>
    `).join('');
}

function cizKademeGrafigi(kademeVerisi) {
    if (!Array.isArray(kademeVerisi) || kademeVerisi.length === 0) return;

    const labels = kademeVerisi.map(k => k.kademe);
    const ozursuzData = kademeVerisi.map(k => k.ozursuz_ort);
    const ozurluData = kademeVerisi.map(k => k.ozurlu_ort);

    const ctx = document.getElementById('chart_kademe');
    if (!ctx) return;

    if (charts['chart_kademe']) {
        charts['chart_kademe'].destroy();
    }

    charts['chart_kademe'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Özürsüz Ort. (Gün)',
                    data: ozursuzData,
                    backgroundColor: '#ef4444',
                    borderRadius: 4
                },
                {
                    label: 'Özürlü Ort. (Gün)',
                    data: ozurluData,
                    backgroundColor: '#10b981',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } }
            }
        }
    });

    const kpiEl = document.getElementById('kademe_kpi_alani');
    if (kpiEl) {
        const sirali = [...kademeVerisi].sort((a,b) => a.ortalama - b.ortalama);
        const enDuzenli = sirali[0];
        const enRiskli = sirali[sirali.length - 1];

        kpiEl.innerHTML = `
            <span style="color: #10b981; font-weight: 600;">✨ En Düzenli: <b>${enDuzenli.kademe}</b> (${enDuzenli.ortalama}G Ort.)</span>
            <span style="color: #ef4444; font-weight: 600;">⚠️ En Yüksek: <b>${enRiskli.kademe}</b> (${enRiskli.ortalama}G Ort.)</span>
        `;
    }
}

function cizGecKalmaAlarmi(alarmlar) {
    const ozetEl = document.getElementById('gec_kalma_ozet_bari');
    if (ozetEl && alarmlar) {
        ozetEl.innerHTML = `
            <span>Toplam G: <b style="color: #f59e0b;">${alarmlar.toplam_g || 0} Adet</b></span>
            <span>Dönüşen Ceza: <b style="color: #ef4444;">${alarmlar.donusen_gun || 0} Gün</b></span>
            <span>Eşikteki Öğrenci: <b style="color: #dc2626;">${alarmlar.esik_sayisi || 0} Kişi</b></span>
        `;
    }

    const tbody = document.getElementById('tbody_gec_alarmi');
    if (tbody && alarmlar && Array.isArray(alarmlar.esik_ogrenciler)) {
        if (alarmlar.esik_ogrenciler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--fg-sub); padding: 16px; font-style: italic;">Şu anda yarım güne dönüşüm sınırında (4, 9, 14... G) öğrenci bulunmuyor.</td></tr>`;
            return;
        }

        tbody.innerHTML = alarmlar.esik_ogrenciler.map(o => {
            const adAttr = (o.ad || '').replace(/"/g, '&quot;');
            const subeAttr = (o.sube || '').replace(/"/g, '&quot;');
            return `
            <tr>
                <td style="font-weight: 600;">${o.ad}</td>
                <td>${o.sube}</td>
                <td style="text-align: center;"><span class="badge" style="background: #fef3c7; color: #b45309; font-weight: bold;">${o.g_sayisi} G</span></td>
                <td style="text-align: center;"><span class="badge" style="background: #fee2e2; color: #b91c1c; font-weight: bold;">+0.5G Sınırda!</span></td>
                <td style="text-align: right; white-space: nowrap;">
                    <button class="btn btn-temizle" data-no="${o.no}" data-ad="${adAttr}" data-sube="${subeAttr}" data-g="${o.g_sayisi}" onclick="gecKalmaVeliMetniKopyala(this.dataset.no, this.dataset.ad, this.dataset.sube, this.dataset.g)" title="Geç Kalma Uyarısı Kopyala" style="padding: 3px 6px; font-size: 10px;">
                        <i data-lucide="copy" height="11" width="11"></i> Uyar
                    </button>
                </td>
            </tr>
            `;
        }).join('');
    }
}

function gecKalmaVeliMetniKopyala(no, ad, sube, gSayisi) {
    const metin = `Sayın Velimiz; ${sube} şubesi ${no} numaralı öğrencimiz ${ad}, bugüne kadar toplam ${gSayisi} kez derse geç kalmıştır. MEB Yönetmeliği gereğince 1 kez daha geç kalması durumunda yarım gün (0.5 gün) özürsüz devamsızlık yazılacaktır. Öğrencimizin ders saatlerine zamanında katılımı konusunda desteğinizi rica ederiz.`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(metin).then(() => {
            if (typeof bildirimGoster === 'function') bildirimGoster(`${ad} için geç kalma uyarı metni panoya kopyalandı!`, 'bilgi');
        }).catch(() => fallbackKopyala(metin, ad));
    } else {
        fallbackKopyala(metin, ad);
    }
}

function cizSampiyonSubeler(sampiyonData) {
    const tbody = document.getElementById('tbody_sampiyon_subeler');
    const container = document.getElementById('container_sampiyon_subeler');
    if (!tbody && !container) return;

    let subeler = [];
    let okulOrtalama = 0.0;

    if (Array.isArray(sampiyonData)) {
        subeler = sampiyonData;
        if (subeler.length > 0) {
            okulOrtalama = Math.round(subeler.reduce((acc, s) => acc + (s.ortalama || 0), 0) / subeler.length * 100) / 100;
        }
    } else if (sampiyonData && typeof sampiyonData === 'object') {
        subeler = sampiyonData.subeler || sampiyonData.liste || [];
        okulOrtalama = sampiyonData.okul_ortalama !== undefined ? sampiyonData.okul_ortalama : 0.0;
    }

    // Emsal değer çubuğunu güncelle
    const elEmsal = document.getElementById('sampiyon_okul_ortalamasi');
    const elEnIyi = document.getElementById('sampiyon_en_iyi_sube');
    if (elEmsal) elEmsal.textContent = `${okulOrtalama} Gün`;
    if (elEnIyi && subeler.length > 0) {
        elEnIyi.innerHTML = `🏆 En Başarılı: <strong>${subeler[0].sube}</strong> (${subeler[0].ortalama}G)`;
    }

    if (!tbody) return;

    if (subeler.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--fg-sub); padding: 25px; font-style: italic;">Şube devamsızlık verisi bulunamadı.</td></tr>`;
        return;
    }

    tbody.innerHTML = subeler.map((s, idx) => {
        const siraNo = idx + 1;
        let dereceBadge = '';
        if (idx === 0) {
            dereceBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #d97706; font-weight: 800; font-size: 11px;">🥇 1.</span>`;
        } else if (idx === 1) {
            dereceBadge = `<span class="badge" style="background: rgba(148, 163, 184, 0.2); color: #475569; font-weight: 800; font-size: 11px;">🥈 2.</span>`;
        } else if (idx === 2) {
            dereceBadge = `<span class="badge" style="background: rgba(180, 83, 9, 0.2); color: #92400e; font-weight: 800; font-size: 11px;">🥉 3.</span>`;
        } else {
            dereceBadge = `<span style="font-weight: 700; color: var(--fg-sub); font-size: 11.5px;">${siraNo}.</span>`;
        }

        // Emsale göre fark hesaplama
        const fark = s.emsal_fark !== undefined ? s.emsal_fark : Math.round((s.ortalama - okulOrtalama) * 100) / 100;
        let farkHtml = '';
        if (fark < 0) {
            farkHtml = `<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #059669; font-weight: 800; font-size: 10.5px;" title="Okul emsal ortalamasından ${Math.abs(fark)} gün daha az devamsızlık (Daha İyi)">${fark} G</span>`;
        } else if (fark > 0) {
            farkHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.12); color: #dc2626; font-weight: 700; font-size: 10.5px;" title="Okul emsal ortalamasından ${fark} gün daha fazla devamsızlık">+${fark} G</span>`;
        } else {
            farkHtml = `<span class="badge" style="background: rgba(148, 163, 184, 0.12); color: var(--fg-sub); font-size: 10.5px;">Emsal</span>`;
        }

        return `
            <tr style="border-bottom: 1px solid var(--border); transition: background 0.15s;">
                <td style="text-align: center; padding: 7px 8px;">${dereceBadge}</td>
                <td style="padding: 7px 8px; font-weight: 700; color: var(--fg-main);">${s.sube}</td>
                <td style="text-align: center; padding: 7px 8px; color: var(--fg-sub); font-weight: 600;">${s.ogrenci_sayisi} Ögr</td>
                <td style="text-align: center; padding: 7px 8px;">
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; font-weight: 800;">${s.ortalama} G</span>
                </td>
                <td style="text-align: right; padding: 7px 8px;">
                    ${farkHtml}
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

function kartGenislikAyarla(btn, genislikOran) {
    const card = btn.closest('.dash-card');
    if (!card) return;

    let flexVal = '';
    let widthVal = '';

    if (genislikOran === '33%') {
        flexVal = '0 0 calc(33.333% - 11px)';
        widthVal = 'calc(33.333% - 11px)';
    } else if (genislikOran === '50%') {
        flexVal = '0 0 calc(50% - 8px)';
        widthVal = 'calc(50% - 8px)';
    } else if (genislikOran === '66%') {
        flexVal = '0 0 calc(66.666% - 8px)';
        widthVal = 'calc(66.666% - 8px)';
    } else if (genislikOran === '100%') {
        flexVal = '0 0 100%';
        widthVal = '100%';
    }

    card.style.flex = flexVal;
    card.style.width = widthVal;

    guncelleBoyutButonDurumu(card, widthVal);
    kaydetDashboardYerlesimi();
    resizeTumGrafikler();
}

function guncelleBoyutButonDurumu(card, widthVal) {
    const buttons = card.querySelectorAll('.dash-size-btn');
    buttons.forEach(b => b.classList.remove('aktif'));

    if (widthVal.includes('33.333')) {
        const b = card.querySelector(".dash-size-btn[data-size='33%']");
        if (b) b.classList.add('aktif');
    } else if (widthVal.includes('50%')) {
        const b = card.querySelector(".dash-size-btn[data-size='50%']");
        if (b) b.classList.add('aktif');
    } else if (widthVal.includes('66.666')) {
        const b = card.querySelector(".dash-size-btn[data-size='66%']");
        if (b) b.classList.add('aktif');
    } else if (widthVal === '100%') {
        const b = card.querySelector(".dash-size-btn[data-size='100%']");
        if (b) b.classList.add('aktif');
    }
}

function resizeTumGrafikler() {
    setTimeout(() => {
        if (typeof charts === 'object') {
            Object.keys(charts).forEach(cid => {
                if (charts[cid] && typeof charts[cid].resize === 'function') {
                    charts[cid].resize();
                }
            });
        }
    }, 60);
}

function baglaDashboardOlaylari() {
    const container = document.getElementById('dashboard_widget_container');
    if (!container || container._olaylarBagli) return;
    container._olaylarBagli = true;

    let aktifSuruklenenKart = null;
    let yerTutucu = null;
    let suruklemeBasladi = false;
    let baslangicX = 0;
    let baslangicY = 0;
    let fareOfsetX = 0;
    let fareOfsetY = 0;
    let kartBaslangicGenislik = 0;
    let kartBaslangicYukseklik = 0;

    // 1. KART SÜRÜKLE & BIRAK (POINTER / MOUSE TEMELLİ - WEBVIEW2 / PYWEBVIEW UYUMLU)
    container.addEventListener('pointerdown', (e) => {
        // Sadece sol tık (button === 0)
        if (e.button !== 0) return;

        // Boyutlandırma tutamacına tıklandıysa sürüklemeyi tetikleme
        if (e.target.closest('.dash-corner-resizer')) return;

        // Butonlara, inputlara veya seçim araçlarına tıklandıysa sürüklemeyi tetikleme
        if (e.target.closest('button, input, select, a, .dash-size-presets, .esik-filtre-btn, .btn')) return;

        // Tutamaç veya düzenleme modu aktifken başlığa tıklandıysa
        const handle = e.target.closest('.dash-drag-handle');
        const header = e.target.closest('.dash-card-header');

        if (!handle && !(window.dashboardDuzenlemeModu && header)) return;

        const card = (handle || header).closest('.dash-card');
        if (!card || card.parentElement !== container) return;

        e.preventDefault();

        aktifSuruklenenKart = card;
        suruklemeBasladi = false;
        baslangicX = e.clientX;
        baslangicY = e.clientY;

        const rect = card.getBoundingClientRect();
        fareOfsetX = e.clientX - rect.left;
        fareOfsetY = e.clientY - rect.top;
        kartBaslangicGenislik = rect.width;
        kartBaslangicYukseklik = rect.height;

        function onPointerMove(moveEvent) {
            const mesafeX = Math.abs(moveEvent.clientX - baslangicX);
            const mesafeY = Math.abs(moveEvent.clientY - baslangicY);

            // Kullanıcı en az 4 piksel hareket ettirince sürüklemeyi başlat
            if (!suruklemeBasladi && (mesafeX > 4 || mesafeY > 4)) {
                suruklemeBasladi = true;

                // Yer tutucu (placeholder) oluştur
                yerTutucu = document.createElement('div');
                yerTutucu.className = 'dash-drop-placeholder';
                yerTutucu.style.flex = aktifSuruklenenKart.style.flex || window.getComputedStyle(aktifSuruklenenKart).flex;
                yerTutucu.style.width = aktifSuruklenenKart.style.width || `${kartBaslangicGenislik}px`;
                yerTutucu.style.height = aktifSuruklenenKart.style.height || `${kartBaslangicYukseklik}px`;

                container.insertBefore(yerTutucu, aktifSuruklenenKart);

                // Kartı kayan (floating) hale getir
                aktifSuruklenenKart.classList.add('is-dragging');
                aktifSuruklenenKart.style.position = 'fixed';
                aktifSuruklenenKart.style.zIndex = '99999';
                aktifSuruklenenKart.style.pointerEvents = 'none'; // Altındaki elemanları algılayabilmek için
                aktifSuruklenenKart.style.width = `${kartBaslangicGenislik}px`;
                aktifSuruklenenKart.style.height = `${kartBaslangicYukseklik}px`;
                aktifSuruklenenKart.style.margin = '0';
                document.body.style.userSelect = 'none';
                document.body.style.cursor = 'grabbing';
            }

            if (!suruklemeBasladi) return;

            // Kayan kartın konumunu güncelle
            aktifSuruklenenKart.style.left = `${moveEvent.clientX - fareOfsetX}px`;
            aktifSuruklenenKart.style.top = `${moveEvent.clientY - fareOfsetY}px`;

            // Fare altındaki kartı tespit et
            const altEleman = document.elementFromPoint(moveEvent.clientX, moveEvent.clientY);
            if (!altEleman) return;

            const hedefKart = altEleman.closest('.dash-card');
            if (hedefKart && hedefKart !== aktifSuruklenenKart && hedefKart.parentElement === container) {
                const hRect = hedefKart.getBoundingClientRect();
                const sonraMi = (moveEvent.clientY > hRect.top + hRect.height / 2) || (moveEvent.clientX > hRect.left + hRect.width / 2);

                if (sonraMi) {
                    if (hedefKart.nextSibling !== yerTutucu) {
                        container.insertBefore(yerTutucu, hedefKart.nextSibling);
                    }
                } else {
                    if (hedefKart !== yerTutucu) {
                        container.insertBefore(yerTutucu, hedefKart);
                    }
                }
            }
        }

        function onPointerUp() {
            document.removeEventListener('pointermove', onPointerMove);
            document.removeEventListener('pointerup', onPointerUp);
            document.removeEventListener('pointercancel', onPointerUp);
            document.body.style.userSelect = '';
            document.body.style.cursor = '';

            if (suruklemeBasladi && aktifSuruklenenKart && yerTutucu) {
                // Kartı yer tutucunun yerine yerleştir
                aktifSuruklenenKart.classList.remove('is-dragging');
                aktifSuruklenenKart.style.position = '';
                aktifSuruklenenKart.style.zIndex = '';
                aktifSuruklenenKart.style.pointerEvents = '';
                aktifSuruklenenKart.style.left = '';
                aktifSuruklenenKart.style.top = '';
                aktifSuruklenenKart.style.margin = '';

                container.insertBefore(aktifSuruklenenKart, yerTutucu);
                yerTutucu.remove();
                yerTutucu = null;

                kaydetDashboardYerlesimi();
                resizeTumGrafikler();
            }

            aktifSuruklenenKart = null;
            suruklemeBasladi = false;
        }

        document.addEventListener('pointermove', onPointerMove);
        document.addEventListener('pointerup', onPointerUp);
        document.addEventListener('pointercancel', onPointerUp);
    });

    // 2. KÖŞEDEN SERBEST BOYUTLANDIRMA (POINTER / MOUSE RESIZING)
    container.addEventListener('pointerdown', (e) => {
        if (e.button !== 0) return;

        const resizer = e.target.closest('.dash-corner-resizer');
        if (!resizer) return;

        const card = resizer.closest('.dash-card');
        if (!card || card.parentElement !== container) return;

        e.preventDefault();
        e.stopPropagation();

        const baslangicX = e.clientX;
        const baslangicY = e.clientY;
        const baslangicW = card.offsetWidth;
        const baslangicH = card.offsetHeight;
        const containerW = container.offsetWidth;

        card.classList.add('is-resizing');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'nwse-resize';

        let animFrameId = null;

        function onResizeMove(moveEvent) {
            const deltaX = moveEvent.clientX - baslangicX;
            const deltaY = moveEvent.clientY - baslangicY;

            let yeniW = Math.max(260, Math.min(containerW, baslangicW + deltaX));
            let yeniH = Math.max(180, baslangicH + deltaY);

            card.style.flex = `0 0 ${yeniW}px`;
            card.style.width = `${yeniW}px`;
            card.style.height = `${yeniH}px`;

            // Preset boyut butonlarının aktifliğini temizle
            card.querySelectorAll('.dash-size-btn').forEach(b => b.classList.remove('aktif'));

            if (animFrameId) cancelAnimationFrame(animFrameId);
            animFrameId = requestAnimationFrame(resizeTumGrafikler);
        }

        function onResizeUp() {
            document.removeEventListener('pointermove', onResizeMove);
            document.removeEventListener('pointerup', onResizeUp);
            document.removeEventListener('pointercancel', onResizeUp);
            document.body.style.userSelect = '';
            document.body.style.cursor = '';

            card.classList.remove('is-resizing');
            if (animFrameId) cancelAnimationFrame(animFrameId);

            kaydetDashboardYerlesimi();
            resizeTumGrafikler();
        }

        document.addEventListener('pointermove', onResizeMove);
        document.addEventListener('pointerup', onResizeUp);
        document.addEventListener('pointercancel', onResizeUp);
    });
}

// Sayfa yüklendiğinde olayları hemen bağla
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', baglaDashboardOlaylari);
} else {
    baglaDashboardOlaylari();
}

// =============================================================================
// MEB RESMİ DEVAMSIZLIK MEKTUBU & TEBLİGAT TAKİP ÇİZELGESİ (5, 15, 25 GÜN)
// =============================================================================
window.aktifMektupTakip = null;
window.aktifMektupSekme = '5_gun';
window.aktifMektupArama = '';

/**
 * Dashboard ana ekranındaki resmi tebligat takip çizelgesini doldurur.
 * 5, 15 ve 25 gün eşiklerini listeler; gönderilmemiş mektup varsa sayının yanında
 * animasyonlu uyarı ünlemi gösterir ve üzerine gelindiğinde kalan sayıyı bildirir.
 */
function mektupTakipCizelgesiniDoldur(data) {
    if (!data) return;
    window.aktifMektupTakip = data;

    const tbody = document.getElementById('tbody_mektup_takip_cizelge');
    if (!tbody) return;

    const esikler = [
        {
            key: '5_gun',
            baslik: '5 Gün Eşiği (1. Tebligat)',
            icon: '📬',
            color: '#f59e0b',
            mevzuat: 'Özürsüz 5 gün devamsızlık ve komisyon bildirimi (MEB OÖKY Md. 36/4 & 36/5-a)'
        },
        {
            key: '15_gun',
            baslik: '15 Gün Eşiği (2. Tebligat)',
            icon: '📨',
            color: '#3b82f6',
            mevzuat: 'Toplam 15 gün resmi iadeli taahhütlü veli tebligatı (MEB OÖKY Md. 36/4)'
        },
        {
            key: '25_gun',
            baslik: '25 Gün Eşiği (3. Nihai Tebligat)',
            icon: '🚨',
            color: '#ef4444',
            mevzuat: 'Toplam 25 gün nihai tebligat; 30 gün aşımında sınıf tekrarı (MEB OÖKY Md. 36/4)'
        }
    ];

    tbody.innerHTML = esikler.map(e => {
        const info = data[e.key] || { toplam_ogrenci: 0, gonderilen_sayi: 0, kalan_sayi: 0, hepsi_gonderildi: false };
        const toplam = info.toplam_ogrenci || 0;
        const kalan = info.kalan_sayi !== undefined ? info.kalan_sayi : toplam;
        const gonderilen = info.gonderilen_sayi || 0;

        // Sayı ve Ünlem Göstergesi:
        // Kullanıcı sayının üzerine geldiğinde altı çizili hale gelir, tıkladığında liste modalı açılır.
        // Eğer gönderilmemiş mektup varsa sayının yanında ünlem işareti gösterilir.
        let sayiVeUyariHtml = '';
        if (toplam === 0) {
            sayiVeUyariHtml = `<span class="tebligat-sayi-link" onclick="mektupTakipModalAc('${e.key}')" title="Listeyi açmak için tıklayın">0</span>`;
        } else if (kalan > 0) {
            sayiVeUyariHtml = `
                <div style="display: inline-flex; align-items: center; justify-content: center; gap: 4px;">
                    <span class="tebligat-sayi-link" onclick="mektupTakipModalAc('${e.key}')" title="${e.baslik} öğrenci listesini açmak için tıklayın">${toplam}</span>
                    <span class="tebligat-unlem-badge" title="${kalan} adet öğrencinin devamsızlık mektubu gönderilmedi">⚠️</span>
                </div>
            `;
        } else {
            sayiVeUyariHtml = `
                <div style="display: inline-flex; align-items: center; justify-content: center; gap: 4px;">
                    <span class="tebligat-sayi-link" onclick="mektupTakipModalAc('${e.key}')" title="${e.baslik} öğrenci listesini açmak için tıklayın">${toplam}</span>
                    <span title="Tüm öğrencilerin tebligat mektubu gönderildi" style="color: #10b981; font-weight: 800; font-size: 15px; margin-left: 2px;">✓</span>
                </div>
            `;
        }

        return `
            <tr style="border-bottom: 1px solid var(--border); transition: background 0.15s;">
                <td style="padding: 12px 14px; font-weight: 700;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 18px;">${e.icon}</span>
                        <span style="color: ${e.color}; font-size: 13px;">${e.baslik}</span>
                    </div>
                </td>
                <td style="padding: 12px 14px; text-align: center;">
                    ${sayiVeUyariHtml}
                </td>
            </tr>
        `;
    }).join('');

    // Dinamik eklenen elementler için Tippy ve Lucide ikonlarını yenile
    if (typeof tippy === 'function') {
        tbody.querySelectorAll('[title]').forEach(el => {
            const titleText = el.getAttribute('title');
            if (titleText && titleText !== 'Kapat') {
                tippy(el, {
                    content: titleText,
                    placement: 'top',
                    theme: 'dark-custom',
                    delay: [150, 0],
                    arrow: true,
                    animation: 'shift-away'
                });
                el.removeAttribute('title');
            }
        });
    }

    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

/**
 * Resmi devamsızlık mektubu modalını açar ve belirtilen sekmeyi yükler.
 */
async function mektupTakipModalAc(esik_turu = '5_gun') {
    const modal = document.getElementById('mektup_takip_modal');
    if (modal) {
        modal.style.display = 'flex';
    }
    
    window.aktifMektupSekme = esik_turu;
    const aramaEl = document.getElementById('ent_mektup_modal_arama');
    if (aramaEl) aramaEl.value = '';
    window.aktifMektupArama = '';

    // Eğer veriler henüz çekilmediyse arka plandan getir
    if (!window.aktifMektupTakip) {
        try {
            const res = await apiFetch('/mektup-takip-ozet');
            const data = (res && res.veriler) ? res.veriler : res;
            if (data && !data.hata) {
                window.aktifMektupTakip = data;
                mektupTakipCizelgesiniDoldur(data);
            }
        } catch (e) {
            console.error('Mektup takip özeti alınamadı:', e);
        }
    }

    mektupModalSekmeDegistir(esik_turu);
}

/**
 * Modalı kapatır.
 */
function mektupTakipModalKapat() {
    const modal = document.getElementById('mektup_takip_modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Modal içerisindeki 5, 15 veya 25 gün sekmeleri arasında geçiş yapar.
 */
function mektupModalSekmeDegistir(esik_turu) {
    window.aktifMektupSekme = esik_turu;

    const butonAyarlari = [
        { id: 'btn_mektup_sekme_5', tur: '5_gun', border: '#f59e0b', color: '#d97706', bg: 'rgba(245, 158, 11, 0.15)' },
        { id: 'btn_mektup_sekme_15', tur: '15_gun', border: '#3b82f6', color: '#2563eb', bg: 'rgba(59, 130, 246, 0.15)' },
        { id: 'btn_mektup_sekme_25', tur: '25_gun', border: '#ef4444', color: '#dc2626', bg: 'rgba(239, 68, 68, 0.15)' }
    ];

    butonAyarlari.forEach(b => {
        const el = document.getElementById(b.id);
        if (!el) return;
        if (b.tur === esik_turu) {
            el.classList.add('aktif');
            el.style.background = b.bg;
            el.style.color = b.color;
            el.style.borderColor = b.border;
            el.style.fontWeight = '700';
        } else {
            el.classList.remove('aktif');
            el.style.background = 'var(--bg-main)';
            el.style.color = 'var(--fg-main)';
            el.style.borderColor = 'var(--border)';
            el.style.fontWeight = '500';
        }
    });

    mektupModalTabloyuDoldur();
}

/**
 * Seçili eşiğe göre modal tablosunu doldurur ve sayaçları günceller.
 */
function mektupModalTabloyuDoldur() {
    const seciliEsik = window.aktifMektupSekme || '5_gun';
    const data = window.aktifMektupTakip || {};
    const veri = data[seciliEsik] || { toplam_ogrenci: 0, gonderilen_sayi: 0, kalan_sayi: 0, ogrenciler: [] };

    // Sekme sayaç rozetlerini güncelle
    const b5 = document.getElementById('badge_mektup_sekme_5');
    const b15 = document.getElementById('badge_mektup_sekme_15');
    const b25 = document.getElementById('badge_mektup_sekme_25');
    if (b5) b5.innerText = data['5_gun'] ? data['5_gun'].toplam_ogrenci : 0;
    if (b15) b15.innerText = data['15_gun'] ? data['15_gun'].toplam_ogrenci : 0;
    if (b25) b25.innerText = data['25_gun'] ? data['25_gun'].toplam_ogrenci : 0;

    // Modal başlık ve mevzuat metni
    const baslikEl = document.getElementById('mektup_modal_baslik');
    const mevzuatEl = document.getElementById('mektup_modal_mevzuat');
    if (baslikEl) {
        if (seciliEsik === '5_gun') baslikEl.innerText = '5 Gün Devamsızlık Eşiği - 1. Veli Tebligatı';
        else if (seciliEsik === '15_gun') baslikEl.innerText = '15 Gün Devamsızlık Eşiği - 2. Veli Tebligatı';
        else if (seciliEsik === '25_gun') baslikEl.innerText = '25 Gün Devamsızlık Eşiği - 3. Nihai Veli Tebligatı';
    }
    if (mevzuatEl) {
        mevzuatEl.innerText = veri.mevzuat || 'MEB Ortaöğretim Kurumları Yönetmeliği Md. 36 gereğince veli tebligat mektubu takip çizelgesi';
    }

    // Durum ve uyarı metni
    const durumEl = document.getElementById('mektup_modal_durum_metni');
    const unlemUyariEl = document.getElementById('mektup_modal_unlem_uyarisi');
    const unlemMetinEl = document.getElementById('mektup_modal_unlem_metni');
    const tbody = document.getElementById('mektup_modal_tbody');
    const chkMaster = document.getElementById('chk_mektup_master');

    if (!tbody) return;

    if (durumEl) {
        durumEl.innerHTML = `Toplam <b>${veri.toplam_ogrenci}</b> öğrenci &bull; <span style="color:#10b981; font-weight:700;">${veri.gonderilen_sayi} Gönderildi</span> &bull; <span style="color:${veri.kalan_sayi > 0 ? '#dc2626' : 'var(--fg-sub)'}; font-weight:700;">${veri.kalan_sayi} Gönderilmedi</span>`;
    }

    if (unlemUyariEl) {
        if (veri.kalan_sayi > 0) {
            unlemUyariEl.style.display = 'inline-flex';
            if (unlemMetinEl) {
                unlemMetinEl.innerText = `${veri.kalan_sayi} adet öğrencinin devamsızlık mektubu gönderilmedi!`;
            }
        } else {
            unlemUyariEl.style.display = 'none';
        }
    }

    if (chkMaster) {
        chkMaster.disabled = (veri.toplam_ogrenci === 0);
        chkMaster.checked = (veri.toplam_ogrenci > 0 && veri.kalan_sayi === 0);
    }

    let ogrenciler = veri.ogrenciler || [];

    // Arama filtrelemesi
    const arama = (window.aktifMektupArama || '').trim().toLowerCase();
    if (arama) {
        ogrenciler = ogrenciler.filter(o => 
            String(o.no).toLowerCase().includes(arama) ||
            String(o.ad_soyad).toLowerCase().includes(arama) ||
            String(o.sube).toLowerCase().includes(arama)
        );
    }

    if (ogrenciler.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--fg-sub); padding: 30px; font-style: italic;">
                    ${arama ? 'Arama kriterine uygun öğrenci bulunamadı.' : 'Bu eşikte kayıtlı öğrenci bulunmuyor. Harika!'}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = ogrenciler.map((o, idx) => {
        const siraNo = o.sira || (idx + 1);
        const checked = o.mektup_gonderildi ? 'checked' : '';
        const durumEtiketi = o.mektup_gonderildi
            ? `<span style="display:inline-flex; align-items:center; gap:4px; color:#10b981; font-weight:700; font-size:11px;"><i data-lucide="check-circle" height="13" width="13"></i> Gönderildi</span>`
            : `<span style="display:inline-flex; align-items:center; gap:4px; color:#dc2626; font-weight:700; font-size:11px;"><i data-lucide="alert-circle" height="13" width="13"></i> Gönderilmedi</span>`;

        let tarihStr = '';
        if (o.mektup_gonderildi && o.gonderilme_tarihi) {
            tarihStr = `<div style="font-size:10px; color:var(--fg-sub); margin-top:2px;">${o.gonderilme_tarihi.substring(0, 10)}</div>`;
        }

        const adAttr = (o.ad_soyad || '').replace(/'/g, "\\'");

        return `
            <tr style="border-bottom: 1px solid var(--border); transition: background 0.15s;">
                <td style="text-align: center; color: var(--fg-sub); font-weight: 600;">${siraNo}</td>
                <td style="font-weight: 700; color: var(--fg-sub); font-family: monospace;">${o.no}</td>
                <td style="font-weight: 700; color: var(--fg-main);">${o.ad_soyad}</td>
                <td><span class="badge" style="background: rgba(2, 132, 199, 0.1); color: var(--tree-sel, #0284c7); font-weight: 700; font-size: 11.5px;">${o.sube}</span></td>
                <td><span class="badge" style="background: ${seciliEsik === '25_gun' ? '#fee2e2' : (seciliEsik === '15_gun' ? '#ffedd5' : '#fef3c7')}; color: ${seciliEsik === '25_gun' ? '#b91c1c' : (seciliEsik === '15_gun' ? '#c2410c' : '#b45309')}; font-weight: 700;">${o.devamsizlik}</span></td>
                <td style="text-align: center; background: rgba(2, 132, 199, 0.03);">
                    <div style="display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;">
                        <label style="display: inline-flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; margin: 0;">
                            <input type="checkbox" ${checked} onchange="mektupDurumDegistir('${o.no}', '${seciliEsik}', this.checked)" style="width: 17px; height: 17px; cursor: pointer; accent-color: #0284c7;">
                            ${durumEtiketi}
                        </label>
                        ${tarihStr}
                    </div>
                </td>
                <td style="text-align: center; white-space: nowrap;">
                    <button type="button" class="btn btn-temizle" onclick="if (typeof yillikListeAc === 'function') yillikListeAc('${o.no}', '${adAttr}');" title="Devamsızlık Karnesini Aç" style="padding: 3px 8px; font-size: 11px;">
                        <i data-lucide="eye" height="12" width="12"></i> İncele
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide && typeof lucide.createIcons === 'function') {
        lucide.createIcons();
    }
}

/**
 * Arama kutusu input olayı.
 */
function mektupModalArama(q) {
    window.aktifMektupArama = (q || '').trim().toLowerCase();
    mektupModalTabloyuDoldur();
}

/**
 * Tek bir öğrencinin mektup gönderildi durumunu değiştirir ve sunucuya kaydeder.
 * Dashboard ana tablosundaki uyarı ünlemi anında otomatik güncellenir.
 */
async function mektupDurumDegistir(ogrenci_no, esik_turu, gonderildi) {
    if (!window.aktifMektupTakip || !window.aktifMektupTakip[esik_turu]) return;

    const grup = window.aktifMektupTakip[esik_turu];
    const ogrenci = (grup.ogrenciler || []).find(o => String(o.no) === String(ogrenci_no));
    if (ogrenci) {
        ogrenci.mektup_gonderildi = gonderildi;
        ogrenci.gonderilme_tarihi = gonderildi ? new Date().toISOString() : '';
    }

    // Sayaçları güncelle
    grup.gonderilen_sayi = grup.ogrenciler.filter(o => o.mektup_gonderildi).length;
    grup.kalan_sayi = grup.toplam_ogrenci - grup.gonderilen_sayi;
    grup.hepsi_gonderildi = (grup.kalan_sayi === 0 && grup.toplam_ogrenci > 0);

    // Ana dashboard çizelgesini ve modalı anında güncelle
    mektupTakipCizelgesiniDoldur(window.aktifMektupTakip);
    mektupModalTabloyuDoldur();

    try {
        const resp = await apiFetch('/mektup-durumu-kaydet', {
            method: 'POST',
            body: {
                ogrenci_no: String(ogrenci_no),
                esik_turu: esik_turu,
                gonderildi: gonderildi
            }
        });

        if (resp && resp.basarili) {
            if (typeof bildirimGoster === 'function') {
                bildirimGoster(gonderildi ? `${ogrenci ? ogrenci.ad_soyad : ogrenci_no}: Devamsızlık mektubu gönderildi olarak kaydedildi.` : `${ogrenci ? ogrenci.ad_soyad : ogrenci_no}: Mektup işareti kaldırıldı.`, 'bilgi');
            }
        }
    } catch (err) {
        console.error('Mektup durumu kaydedilirken hata oluştu:', err);
        if (typeof bildirimGoster === 'function') {
            bildirimGoster('Mektup durumu kaydedilirken hata oluştu!', 'hata');
        }
    }
}

/**
 * Mevcut eşikteki tüm öğrencileri topluca "Gönderildi" veya "Temizle" yapar.
 */
async function mektupModalTopluIsaretle(gonderildi) {
    const esik_turu = window.aktifMektupSekme || '5_gun';
    if (!window.aktifMektupTakip || !window.aktifMektupTakip[esik_turu]) return;

    const grup = window.aktifMektupTakip[esik_turu];
    const ogrenciler = grup.ogrenciler || [];
    if (ogrenciler.length === 0) return;

    const noListesi = ogrenciler.map(o => String(o.no));
    const simdi = new Date().toISOString();

    ogrenciler.forEach(o => {
        o.mektup_gonderildi = gonderildi;
        o.gonderilme_tarihi = gonderildi ? simdi : '';
    });

    grup.gonderilen_sayi = gonderildi ? ogrenciler.length : 0;
    grup.kalan_sayi = grup.toplam_ogrenci - grup.gonderilen_sayi;
    grup.hepsi_gonderildi = (grup.kalan_sayi === 0 && grup.toplam_ogrenci > 0);

    mektupTakipCizelgesiniDoldur(window.aktifMektupTakip);
    mektupModalTabloyuDoldur();

    try {
        const resp = await apiFetch('/mektup-durumu-toplu-kaydet', {
            method: 'POST',
            body: {
                ogrenci_nolar: noListesi,
                esik_turu: esik_turu,
                gonderildi: gonderildi
            }
        });

        if (resp && resp.basarili) {
            if (typeof bildirimGoster === 'function') {
                bildirimGoster(gonderildi ? `${ogrenciler.length} öğrencinin tümüne mektup gönderildi olarak kaydedildi.` : 'Tüm mektup işaretleri kaldırıldı.', 'bilgi');
            }
        }
    } catch (err) {
        console.error('Toplu mektup durumu kaydedilirken hata oluştu:', err);
        if (typeof bildirimGoster === 'function') {
            bildirimGoster('Toplu durum kaydedilirken sunucu hatası oluştu!', 'hata');
        }
    }
}

/**
 * Tablo başlığındaki master checkbox kontrolü.
 */
function mektupModalMasterToggle(checked) {
    mektupModalTopluIsaretle(checked);
}

/**
 * Sunucudan güncel mektup verilerini yeniden çeker.
 */
async function mektupModalVerileriniYenile() {
    try {
        const res = await apiFetch('/mektup-takip-ozet');
        const data = (res && res.veriler) ? res.veriler : res;
        if (data && !data.hata) {
            window.aktifMektupTakip = data;
            mektupTakipCizelgesiniDoldur(data);
            mektupModalTabloyuDoldur();
            if (typeof bildirimGoster === 'function') {
                bildirimGoster('Mektup takip verileri güncellendi.', 'bilgi');
            }
        }
    } catch (err) {
        console.error('Mektup verileri yenilenirken hata:', err);
    }
}

// Global kapsam bağlamaları
window.mektupTakipCizelgesiniDoldur = mektupTakipCizelgesiniDoldur;
window.mektupTakipModalAc = mektupTakipModalAc;
window.mektupTakipModalKapat = mektupTakipModalKapat;
window.mektupModalSekmeDegistir = mektupModalSekmeDegistir;
window.mektupModalTabloyuDoldur = mektupModalTabloyuDoldur;
window.mektupModalArama = mektupModalArama;
window.mektupDurumDegistir = mektupDurumDegistir;
window.mektupModalTopluIsaretle = mektupModalTopluIsaretle;
window.mektupModalMasterToggle = mektupModalMasterToggle;
window.mektupModalVerileriniYenile = mektupModalVerileriniYenile;



