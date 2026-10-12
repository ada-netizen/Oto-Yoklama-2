let charts = {};

function renderChart(canvasId, type, label, labels, data, colors, isDual = false, data2 = null, label2 = null, color2 = null, isStacked = false) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    let datasets = [{
        label: label,
        data: data,
        backgroundColor: type === 'line' ? 'rgba(59, 130, 246, 0.1)' : (colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f43f5e']),
        borderColor: type === 'line' ? (colors ? colors[0] : '#3b82f6') : 'transparent',
        borderWidth: type === 'line' ? 2 : 0,
        tension: 0.4,
        fill: type === 'line' ? true : false
    }];

    if(isDual && data2) {
        datasets.push({
            label: label2,
            data: data2,
            borderColor: color2 || '#f59e0b',
            backgroundColor: type === 'bar' ? (color2 || '#f59e0b') : 'rgba(245, 158, 11, 0.1)',
            borderWidth: type === 'line' ? 2 : 0,
            tension: 0.4,
            fill: type === 'line' ? true : false
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
            plugins: {
                legend: { 
                    position: type === 'pie' || type === 'doughnut' ? 'right' : 'top',
                    labels: { color: 'gray', font: { size: 10 } }
                }
            },
            scales: (type === 'pie' || type === 'doughnut' || type === 'radar') ? {} : {
                x: { stacked: isStacked, ticks: { color: 'gray', font: { size: 10 } }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { stacked: isStacked, ticks: { color: 'gray', font: { size: 10 } }, grid: { color: 'rgba(0,0,0,0.05)' } }
            }
        }
    });
}

function dashboardYukle() {
    fetch(`${API}/istatistikler`)
    .then(r => r.json())
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

        // Grafikleri güvenli render et (grafik hatası olsa bile eşik tablosu ve KPI'lar çalışmaya devam eder)
        try {
            // 1. Aylik Trend (Dual Line)
            const ayLabels = (data.aylik_trend || []).map(d => d.ay);
            const ayDevData = (data.aylik_trend || []).map(d => d.toplam);
            const ayEvrakData = (data.aylik_evrak || []).map(d => d.toplam);
            renderChart('chart_aylik', 'line', 'Devamsızlık Miktarı', ayLabels, ayDevData, ['#3b82f6'], true, ayEvrakData, 'Üretilen Evrak', '#10b981');
        } catch(e) { console.error('Aylık trend çizim hatası:', e); }
        
        try {
            // 2. Gunluk Trend
            const gunLabels = (data.haftanin_gunleri || []).map(d => d.gun);
            const gunData = (data.haftanin_gunleri || []).map(d => d.toplam);
            renderChart('chart_gunluk', 'bar', 'Toplam Devamsızlık', gunLabels, gunData, ['#f59e0b', '#f59e0b', '#f59e0b', '#f59e0b', '#f59e0b']);
        } catch(e) { console.error('Günlük trend çizim hatası:', e); }

        try {
            // 3. Sube Ortalamalar (Stacked)
            const subeLabels = (data.sube_ortalamalar || []).map(d => d.sube);
            const subeOzurlu = (data.sube_ortalamalar || []).map(d => d.ozurlu_ort);
            const subeOzursuz = (data.sube_ortalamalar || []).map(d => d.ozursuz_ort);
            renderChart('chart_sube', 'bar', 'Özürlü', subeLabels, subeOzurlu, ['#10b981'], true, subeOzursuz, 'Özürsüz', '#ef4444', true);
        } catch(e) { console.error('Şube ortalamaları çizim hatası:', e); }
        
        try {
            // 4. Tur Devamsizlik
            const turLabels = (data.tur_dev || []).map(d => d.tur);
            const turData = (data.tur_dev || []).map(d => d.toplam);
            renderChart('chart_tur', 'doughnut', 'Gün', turLabels, turData, ['#8b5cf6', '#06b6d4', '#f43f5e', '#3b82f6', '#10b981']);
        } catch(e) { console.error('Tür devamsızlık çizim hatası:', e); }
        
        try {
            // 5. Özürlü vs Özürsüz
            const ozLabels = ['Özürlü', 'Özürsüz'];
            const ozData = [data.ozurlu_vs_ozursuz ? data.ozurlu_vs_ozursuz.ozurlu : 0, data.ozurlu_vs_ozursuz ? data.ozurlu_vs_ozursuz.ozursuz : 0];
            renderChart('chart_ozurlu_oran', 'pie', 'Devamsızlık', ozLabels, ozData, ['#10b981', '#ef4444']);
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
    
    fetch(`${API}/arsivle`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({arsiv_adi: ad})
    })
    .then(r => r.json())
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
