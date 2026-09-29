import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_dashboard = '''<div class="tab-content" id="sekme_dashboard" style="overflow-y: auto; background-color: var(--bg-main); padding: 20px;">
    <style>
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .kpi-card { background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); display: flex; align-items: center; gap: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
        .kpi-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: white; }
        .kpi-info h4 { margin: 0; font-size: 11px; color: var(--fg-sub); font-weight: normal; }
        .kpi-info h2 { margin: 5px 0 0 0; font-size: 24px; color: var(--fg-main); font-weight: 800; }
        .dash-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }
        .dash-card { background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
        .dash-card.span-2 { grid-column: span 2; }
        .dash-card-header { display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px; }
        .dash-card-header h3 { margin: 0; font-size: 14px; color: var(--fg-main); font-weight: 600; }
        .modern-table { width: 100%; border-collapse: collapse; font-size: 11px; }
        .modern-table th { text-align: left; padding: 8px; color: var(--fg-sub); border-bottom: 2px solid var(--border); font-weight: 600; }
        .modern-table td { padding: 8px; color: var(--fg-main); border-bottom: 1px solid var(--border); }
        .modern-table tr:last-child td { border-bottom: none; }
        .top-bar-dashboard { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: var(--bg-card); padding: 15px 20px; border-radius: 12px; border: 1px solid var(--border); }
    </style>

    <div class="top-bar-dashboard">
        <h2 style="margin:0; font-size: 18px; color: var(--fg-main); display: flex; align-items: center; gap: 10px;">
            <i data-lucide="layout-dashboard" height="24" width="24" style="color: #8b5cf6;"></i> Okul İstatistikleri ve Analiz
        </h2>
        <button class="btn btn-dev" onclick="dashboardYukle()"><i data-lucide="refresh-cw" height="16" width="16"></i> Verileri Yenile</button>
    </div>
    
    <!-- KPI CARDS -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706);"><i data-lucide="alert-triangle"></i></div>
            <div class="kpi-info"><h4>Özürsüz 10 Günü Aşan</h4><h2 id="kpi_ozursuz">0</h2></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon" style="background: linear-gradient(135deg, #ef4444, #b91c1c);"><i data-lucide="x-octagon"></i></div>
            <div class="kpi-info"><h4>Toplam 30 Günü Aşan</h4><h2 id="kpi_kalan">0</h2></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon" style="background: linear-gradient(135deg, #10b981, #059669);"><i data-lucide="award"></i></div>
            <div class="kpi-info"><h4>0 Devamsızlık Yapan</h4><h2 id="kpi_sifir">0</h2></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon" style="background: linear-gradient(135deg, #3b82f6, #2563eb);"><i data-lucide="file-text"></i></div>
            <div class="kpi-info"><h4>Toplam Üretilen Evrak</h4><h2 id="kpi_evrak">0</h2></div>
        </div>
    </div>

    <!-- MAIN CHARTS (ROW 1) -->
    <div class="dash-grid">
        <div class="dash-card span-2">
            <div class="dash-card-header"><i data-lucide="trending-up" style="color: #3b82f6;"></i> <h3>Aylık Trend Analizi (Devamsızlık vs Evrak)</h3></div>
            <div style="flex:1; position: relative;"><canvas id="chart_aylik"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="calendar" style="color: #f59e0b;"></i> <h3>Haftanın Günlerine Göre</h3></div>
            <div style="flex:1; position: relative;"><canvas id="chart_gunluk"></canvas></div>
        </div>
    </div>

    <!-- BREAKDOWN CHARTS (ROW 2) -->
    <div class="dash-grid">
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="pie-chart" style="color: #8b5cf6;"></i> <h3>Devamsızlık Türleri</h3></div>
            <div style="flex:1; position: relative;"><canvas id="chart_tur"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="bar-chart" style="color: #10b981;"></i> <h3>Şubelere Göre Yoğunluk</h3></div>
            <div style="flex:1; position: relative;"><canvas id="chart_sube"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="users" style="color: #06b6d4;"></i> <h3>Evrak Giden Branşlar</h3></div>
            <div style="flex:1; position: relative;"><canvas id="chart_evrak"></canvas></div>
        </div>
    </div>

    <!-- TABLES (ROW 3) -->
    <div class="dash-grid">
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="user-x" style="color: #ef4444;"></i> <h3 style="color: #ef4444;">Riskli: En Çok G (Geç) Kalanlar</h3></div>
            <table class="modern-table">
                <thead><tr><th>Öğrenci</th><th>Şube</th><th>Gün</th></tr></thead>
                <tbody id="tbody_g_riskli"></tbody>
            </table>
        </div>
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="user-minus" style="color: #f59e0b;"></i> <h3>En Çok Devamsızlık Yapan 5</h3></div>
            <table class="modern-table">
                <thead><tr><th>Öğrenci</th><th>Şube</th><th>Toplam</th></tr></thead>
                <tbody id="tbody_riskli"></tbody>
            </table>
        </div>
        <div class="dash-card">
            <div class="dash-card-header"><i data-lucide="briefcase" style="color: #3b82f6;"></i> <h3>En Çok Görevlendirilen 5 Personel</h3></div>
            <table class="modern-table">
                <thead><tr><th>Personel</th><th>Evrak Sayısı</th></tr></thead>
                <tbody id="tbody_personel"></tbody>
            </table>
        </div>
    </div>
</div>'''

match = re.search(r'(<div class="tab-content" id="sekme_dashboard".*?</div>\s*<div class="tab-content" id="sekme_ayarlar">)', html, re.DOTALL)
if match:
    # We replace the old sekme_dashboard with new_dashboard
    old_dashboard = re.search(r'(<div class="tab-content" id="sekme_dashboard".*?</div>)\s*<div class="tab-content" id="sekme_ayarlar">', html, re.DOTALL).group(1)
    
    # Actually finding the exact boundary can be tricky with regex if there are nested divs. 
    # Let's use a simpler marker approach since we know it's right before sekme_ayarlar.
pass

# A safer approach is to split the HTML by id="sekme_ayarlar" and replace the block before it.
parts = html.split('<div class="tab-content" id="sekme_ayarlar">')
if len(parts) == 2:
    # find where sekme_dashboard starts in parts[0]
    dash_idx = parts[0].rfind('<div class="tab-content" id="sekme_dashboard"')
    if dash_idx != -1:
        parts[0] = parts[0][:dash_idx] + new_dashboard + '\n'
        
    html = '<div class="tab-content" id="sekme_ayarlar">'.join(parts)
    
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("UI updated")
else:
    print("Could not find boundaries")
