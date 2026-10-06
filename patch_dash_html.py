import re

def patch_index():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Chart 3 replacement
    content = content.replace(
        '<div class="dash-card-header"><i data-lucide="users" style="color: #06b6d4;"></i> <h3>Evrak Giden Branşlar</h3></div>\n              <div style="flex:1; position: relative;"><canvas id="chart_evrak"></canvas></div>',
        '<div class="dash-card-header"><i data-lucide="pie-chart" style="color: #06b6d4;"></i> <h3>Özürlü / Özürsüz Oranı</h3></div>\n              <div style="flex:1; position: relative;"><canvas id="chart_ozurlu_oran"></canvas></div>'
    )
    # Also handle corrupted characters if any (like BranYlar)
    content = re.sub(
        r'<div class="dash-card-header"><i data-lucide="users" style="color: #06b6d4;"></i> <h3>Evrak Giden Bran.*?lar</h3></div>\s*<div style="flex:1; position: relative;"><canvas id="chart_evrak"></canvas></div>',
        '<div class="dash-card-header"><i data-lucide="pie-chart" style="color: #06b6d4;"></i> <h3>Özürlü / Özürsüz Oranı</h3></div>\n              <div style="flex:1; position: relative;"><canvas id="chart_ozurlu_oran"></canvas></div>',
        content
    )

    # 2. Update Sube Chart title
    content = re.sub(
        r'<h3>.*?ubelere G.*?re.*?Yo.*?unluk</h3>',
        r'<h3>Sınıf Başına Düşen Ortalama</h3>',
        content
    )
    
    # 3. Update G table title
    content = re.sub(
        r'<h3 style="color: #ef4444;">Riskli: En .*?ok G \(Ge.*?\) Kalanlar</h3>',
        r'<h3 style="color: #ef4444;">Riskli: En Çok G (Geç) Kalanlar (Adet)</h3>',
        content
    )
    content = re.sub(
        r'<th>G.*?n</th></tr></thead>\s*<tbody id="tbody_g_riskli">',
        r'<th>Adet</th></tr></thead>\n                  <tbody id="tbody_g_riskli">',
        content
    )

    # 4. Remove Personel Table and expand Riskli table
    personel_table_regex = r'<div class="dash-card">\s*<div class="dash-card-header"><i data-lucide="briefcase".*?<h3>En .*?ok G.*?revlendirilen 5 Personel</h3></div>\s*<table class="modern-table">\s*<thead><tr><th>Personel</th><th>Evrak Say.*?s.*?</th></tr></thead>\s*<tbody id="tbody_personel"></tbody>\s*</table>\s*</div>'
    content = re.sub(personel_table_regex, '', content, flags=re.DOTALL)
    
    # Make the 2nd table span-2
    content = re.sub(
        r'<div class="dash-card">\s*<div class="dash-card-header"><i data-lucide="user-minus".*?<h3>En .*?ok Devams.*?zl.*?k Yapan 5</h3>',
        r'<div class="dash-card span-2">\n              <div class="dash-card-header"><i data-lucide="user-minus" style="color: #f59e0b;"></i> <h3>En Çok Devamsızlık Yapan 5</h3>',
        content
    )

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

patch_index()
