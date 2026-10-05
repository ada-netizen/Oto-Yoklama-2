import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Apply pastel backgrounds to specific main elements
html = html.replace('<div id="sol_panel_ana" style="flex: 0 0 360px; display: flex; flex-direction: column; background-color: var(--bg-main);">', 
                    '<div id="sol_panel_ana" style="flex: 0 0 360px; display: flex; flex-direction: column; background-color: var(--block-lilac); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 15px; box-shadow: 4px 4px 0px var(--fg-main);">')
html = html.replace('<div class="filtre-card" style="background-color: var(--bg-card); border: 1px solid var(--border); padding: 15px 10px; margin-bottom: 10px; display: flex; justify-content: center;">',
                    '<div class="filtre-card" style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-pill); padding: 10px 20px; margin-bottom: 15px; display: flex; justify-content: center;">')

# Adjust inputs
html = html.replace('style="background-color: var(--bg-card); border: 1px solid var(--border); color: var(--fg-main); padding: 4px 5px; font-size: 10px; width: 180px;"',
                    'style="background-color: var(--bg-main); border: none; border-bottom: 2px solid var(--fg-main); color: var(--fg-main); padding: 8px; font-size: 12px; width: 180px; font-weight: 540; outline: none;"')
html = html.replace('style="background-color: var(--bg-card); border: 1px solid var(--border); color: var(--fg-main); padding: 3px; font-size: 10px; width: 90px;"',
                    'style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-pill); color: var(--fg-main); padding: 6px 12px; font-size: 12px; font-weight: 540; outline: none;"')

# Teblig tab styling
html = html.replace('<div id="sag_panel" style="flex: 1; display: flex; flex-direction: column; background-color: var(--bg-main);">',
                    '<div id="sag_panel" style="flex: 1; display: flex; flex-direction: column; background-color: var(--block-lime); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 15px; box-shadow: 4px 4px 0px var(--fg-main);">')
html = html.replace('<div class="tree-card" style="background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 15px;">',
                    '<div class="tree-card" style="background-color: var(--bg-main); border: 2px solid var(--fg-main); border-radius: var(--rounded-lg); padding: 30px; display: flex; flex-direction: column; gap: 20px; box-shadow: none;">')

# Dashboard replacement
new_dashboard = '''<div class="tab-content" id="sekme_dashboard" style="overflow-y: auto; background-color: var(--bg-main); padding: 20px;">
    <style>
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .kpi-card { background: var(--bg-main); border-radius: var(--rounded-lg); padding: 20px; border: 2px solid var(--fg-main); display: flex; align-items: center; gap: 15px; box-shadow: 4px 4px 0px var(--fg-main); transition: transform 0.2s, box-shadow 0.2s; cursor: default; }
        .kpi-card:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0px var(--fg-main); }
        .kpi-icon { width: 56px; height: 56px; border-radius: var(--rounded-pill); display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--fg-main); border: 2px solid var(--fg-main); }
        .kpi-info h4 { margin: 0; font-size: 13px; color: var(--fg-main); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-info h2 { margin: 5px 0 0 0; font-size: 32px; color: var(--fg-main); font-weight: 800; line-height: 1; }
        
        .dash-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-bottom: 30px; }
        .dash-card { background: var(--bg-main); border-radius: var(--rounded-lg); padding: 0; border: 2px solid var(--fg-main); box-shadow: 6px 6px 0px var(--fg-main); display: flex; flex-direction: column; overflow: hidden; }
        .dash-card.span-2 { grid-column: span 2; }
        .dash-card-header { display: flex; align-items: center; gap: 10px; border-bottom: 2px solid var(--fg-main); padding: 15px 20px; background-color: var(--block-cream); margin-bottom: 0; }
        .dash-card-header h3 { margin: 0; font-size: 16px; color: var(--fg-main); font-weight: 700; letter-spacing: -0.3px; }
        .dash-card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; position: relative; }
        
        .modern-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
        .modern-table th { text-align: left; padding: 12px; color: var(--fg-main); border-bottom: 2px solid var(--fg-main); font-weight: 700; background-color: var(--bg-main); }
        .modern-table td { padding: 12px; color: var(--fg-main); border-bottom: 1px solid var(--border); font-weight: 500; }
        .modern-table tr:last-child td { border-bottom: none; }
        .modern-table tr:hover td { background-color: rgba(0,0,0,0.02); }
        
        .badge { padding: 4px 12px; border-radius: var(--rounded-pill); font-weight: 700; font-size: 11px; border: 1px solid var(--fg-main); color: var(--fg-main) !important; text-transform: uppercase; box-shadow: 2px 2px 0px var(--fg-main); }
        
        .top-bar-dashboard { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; background: var(--block-lilac); padding: 20px 25px; border-radius: var(--rounded-lg); border: 2px solid var(--fg-main); box-shadow: 4px 4px 0px var(--fg-main); }
    </style>
    <div class="top-bar-dashboard">
        <h2 style="margin:0; font-size: 18px; color: var(--fg-main); display: flex; align-items: center; gap: 10px;">
            <i data-lucide="layout-dashboard" height="24" width="24" style="color: var(--fg-main);"></i> Okul İstatistikleri ve Analiz
        </h2>
        <button class="btn btn-dev" onclick="dashboardYukle()"><i data-lucide="refresh-cw" height="16" width="16"></i> Verileri Yenile</button>
    </div>
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-icon" style="background: var(--block-mint);"><i data-lucide="alert-triangle"></i></div><div class="kpi-info"><h4>Özürsüz 10 Günü Aşan</h4><h2 id="kpi_ozursuz">0</h2></div></div>
        <div class="kpi-card"><div class="kpi-icon" style="background: var(--block-pink);"><i data-lucide="x-octagon"></i></div><div class="kpi-info"><h4>Toplam 30 Günü Aşan</h4><h2 id="kpi_kalan">0</h2></div></div>
        <div class="kpi-card"><div class="kpi-icon" style="background: var(--block-lime);"><i data-lucide="award"></i></div><div class="kpi-info"><h4>0 Devamsızlık Yapan</h4><h2 id="kpi_sifir">0</h2></div></div>
        <div class="kpi-card"><div class="kpi-icon" style="background: var(--block-lilac);"><i data-lucide="file-text"></i></div><div class="kpi-info"><h4>Toplam Üretilen Evrak</h4><h2 id="kpi_evrak">0</h2></div></div>
    </div>
    <div class="dash-grid">
        <div class="dash-card span-2">
            <div class="dash-card-header" style="background-color: var(--block-mint);"><i data-lucide="trending-up" style="color: var(--fg-main);"></i> <h3>Aylık Trend Analizi (Devamsızlık vs Evrak)</h3></div>
            <div class="dash-card-body"><canvas id="chart_aylik"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-cream);"><i data-lucide="calendar" style="color: var(--fg-main);"></i> <h3>Haftanın Günlerine Göre</h3></div>
            <div class="dash-card-body"><canvas id="chart_gunluk"></canvas></div>
        </div>
    </div>
    <div class="dash-grid">
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-lilac);"><i data-lucide="pie-chart" style="color: var(--fg-main);"></i> <h3>Devamsızlık Türleri</h3></div>
            <div class="dash-card-body"><canvas id="chart_tur"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-lime);"><i data-lucide="bar-chart" style="color: var(--fg-main);"></i> <h3>Şubelere Göre Yoğunluk</h3></div>
            <div class="dash-card-body"><canvas id="chart_sube"></canvas></div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-pink);"><i data-lucide="users" style="color: var(--fg-main);"></i> <h3>Evrak Giden Branşlar</h3></div>
            <div class="dash-card-body"><canvas id="chart_evrak"></canvas></div>
        </div>
    </div>
    <div class="dash-grid">
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-pink);"><i data-lucide="user-x" style="color: var(--fg-main);"></i> <h3 style="color: var(--fg-main);">Riskli: En Çok G (Geç) Kalanlar</h3></div>
            <div class="dash-card-body" style="padding:0; overflow-y:auto;">
                <table class="modern-table"><thead><tr><th>Öğrenci</th><th>Şube</th><th>Gün</th></tr></thead><tbody id="tbody_g_riskli"></tbody></table>
            </div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-cream);"><i data-lucide="user-minus" style="color: var(--fg-main);"></i> <h3>En Çok Devamsızlık Yapan 5</h3></div>
            <div class="dash-card-body" style="padding:0; overflow-y:auto;">
                <table class="modern-table"><thead><tr><th>Öğrenci</th><th>Şube</th><th>Toplam</th></tr></thead><tbody id="tbody_riskli"></tbody></table>
            </div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header" style="background-color: var(--block-mint);"><i data-lucide="briefcase" style="color: var(--fg-main);"></i> <h3>En Çok Görevlendirilen 5 Personel</h3></div>
            <div class="dash-card-body" style="padding:0; overflow-y:auto;">
                <table class="modern-table"><thead><tr><th>Personel</th><th>Evrak Sayısı</th></tr></thead><tbody id="tbody_personel"></tbody></table>
            </div>
        </div>
    </div>
</div>
'''

# Safe string replacement by splitting at exact known boundaries to avoid regex swallowing
parts = html.split('<div class="tab-content" id="sekme_dashboard"')
if len(parts) == 2:
    start_html = parts[0]
    # Find where sekme_dashboard ends by looking for the NEXT tab-content (sekme_ayarlar)
    rest_html = parts[1]
    ayarlar_idx = rest_html.find('<div class="tab-content" id="sekme_ayarlar">')
    if ayarlar_idx != -1:
        # Safely insert the new dashboard block
        html = start_html + new_dashboard + '\n' + rest_html[ayarlar_idx:]

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Safe update completed.")
