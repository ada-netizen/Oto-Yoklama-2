let charts = {};

function renderChart(canvasId, type, label, labels, data, colors, isDual = false, data2 = null, label2 = null, color2 = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    let datasets = [{
        label: label,
        data: data,
        backgroundColor: colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f43f5e'],
        borderColor: type === 'line' ? (colors ? colors[0] : '#3b82f6') : 'transparent',
        borderWidth: type === 'line' ? 2 : 0,
        tension: 0.4,
        fill: type === 'line' ? true : false,
        backgroundColor: type === 'line' ? 'rgba(59, 130, 246, 0.1)' : (colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f43f5e'])
    }];

    if(isDual && data2) {
        datasets.push({
            label: label2,
            data: data2,
            borderColor: color2 || '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true
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
                x: { ticks: { color: 'gray', font: { size: 10 } }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { ticks: { color: 'gray', font: { size: 10 } }, grid: { color: 'rgba(0,0,0,0.05)' } }
            }
        }
    });
}

function dashboardYukle() {
    fetch(`${API}/istatistikler`)
    .then(r => r.json())
    .then(data => {
        if(data.hata) {
            console.error(data.hata);
            return;
        }
        
        // KPIs
        if(document.getElementById('kpi_ozursuz')) document.getElementById('kpi_ozursuz').innerText = data.kpis.ozursuz_10;
        if(document.getElementById('kpi_kalan')) document.getElementById('kpi_kalan').innerText = data.kpis.toplam_30;
        if(document.getElementById('kpi_sifir')) document.getElementById('kpi_sifir').innerText = data.kpis.sifir_hata;
        if(document.getElementById('kpi_evrak')) document.getElementById('kpi_evrak').innerText = data.kpis.toplam_evrak;

        // 1. Aylik Trend (Dual Line)
        const ayLabels = data.aylik_trend.map(d => d.ay);
        const ayDevData = data.aylik_trend.map(d => d.toplam);
        const ayEvrakData = data.aylik_evrak.map(d => d.toplam);
        renderChart('chart_aylik', 'line', 'Devamsızlık Miktarı', ayLabels, ayDevData, ['#3b82f6'], true, ayEvrakData, 'Üretilen Evrak', '#10b981');
        
        // 2. Gunluk Trend
        const gunLabels = data.haftanin_gunleri.map(d => d.gun);
        const gunData = data.haftanin_gunleri.map(d => d.toplam);
        renderChart('chart_gunluk', 'bar', 'Toplam Devamsızlık', gunLabels, gunData, ['#f59e0b', '#f59e0b', '#f59e0b', '#f59e0b', '#f59e0b']);

        // 3. Sube Devamsizlik
        const subeLabels = data.sube_dev.map(d => d.sube);
        const subeData = data.sube_dev.map(d => d.toplam);
        renderChart('chart_sube', 'bar', 'Toplam Gün', subeLabels, subeData, ['#10b981']);
        
        // 4. Tur Devamsizlik
        const turLabels = data.tur_dev.map(d => d.tur);
        const turData = data.tur_dev.map(d => d.toplam);
        renderChart('chart_tur', 'doughnut', 'Gün', turLabels, turData, ['#8b5cf6', '#06b6d4', '#f43f5e', '#3b82f6', '#10b981']);
        
        // 5. Evrak Branslar
        const bransLabels = data.evrak_branslar.map(d => d.brans);
        const bransData = data.evrak_branslar.map(d => d.toplam);
        renderChart('chart_evrak', 'pie', 'Evrak Sayısı', bransLabels, bransData);
        
        // 6. Riskli Ogrenciler
        const tbodyRiskli = document.getElementById('tbody_riskli');
        if(tbodyRiskli) {
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
        if(tbodyGRiskli) {
            tbodyGRiskli.innerHTML = data.g_turu_riskli.map(o => `
                <tr>
                    <td>${o.ad}</td>
                    <td>${o.sube}</td>
                    <td><span class="badge" style="background: #fee2e2; color: #b91c1c;">${o.toplam}</span></td>
                </tr>
            `).join('');
        }

        // 8. Personel Top 5
        const tbodyPersonel = document.getElementById('tbody_personel');
        if(tbodyPersonel) {
            tbodyPersonel.innerHTML = data.personel_top.map(o => `
                <tr>
                    <td>${o.ad}</td>
                    <td><span class="badge" style="background: #dbeafe; color: #1d4ed8;">${o.toplam} Belge</span></td>
                </tr>
            `).join('');
        }
    });
}

function arsivle() {
    const ad = document.getElementById('arsiv_adi').value.trim();
    if(!ad) {
        if(typeof bildirimGoster === 'function') bildirimGoster('Lütfen arşiv adı girin!', 'hata');
        return;
    }
    
    if(!confirm(`DİKKAT! Tüm öğrenci, devamsızlık ve üretilen evrak verileri "${ad}" klasörüne kopyalanıp sıfırlanacak. Personel listesi KORUNACAK. Onaylıyor musunuz?`)) {
        return;
    }
    
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
