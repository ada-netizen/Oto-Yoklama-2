import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace js cache buster
content = re.sub(r'js/saglik\.js\?v=\d+', 'js/saglik.js?v=9', content)

# 1. Update the top bar for PDF Upload button and modern grid layout
top_bar_pattern = r'<div class="top-bar" style="margin-bottom: 20px;">.*?</div>'
new_top_bar = """<div class="top-bar" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <h2 class="top-bar-title" style="margin:0;"><i data-lucide="heart" height="20" width="20"></i> Personel Sağlık İzinleri (<span id="saglik_yil"></span> Yılı)</h2>
        <div style="display: flex; gap: 10px;">
            <div style="position: relative; display: inline-block;">
                <button class="btn" style="background-color: var(--bg-soft); color: var(--fg-main); border: 1px solid var(--border); padding: 10px 20px;"><i data-lucide="upload" height="16" width="16"></i> Sağlık İzni Yükle</button>
                <input type="file" accept=".pdf" onchange="saglikPdfYukle(event)" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" title="PDF Yükle">
            </div>
            <button class="btn" style="background-color: var(--tree-sel); color: white; padding: 10px 20px;" onclick="saglikModalAc()"><i data-lucide="plus" height="16" width="16"></i> Yeni Rapor Ekle</button>
        </div>
    </div>"""
content = re.sub(top_bar_pattern, new_top_bar, content, flags=re.DOTALL)


# 2. Replace the cards grid to use dash-grid and dash-card
cards_pattern = r'<!-- YENİ: Özet Kartları -->.*?</div>'
new_cards = """<!-- YENİ: Özet Kartları -->
    <div class="dash-grid" style="margin-bottom: 20px;">
        <div class="dash-card">
            <div class="dash-card-header">
                <i data-lucide="users" style="color: #3b82f6;"></i>
                <h3>Raporlu Personel</h3>
            </div>
            <div class="dash-card-value" id="stat_raporlu_kisi" style="color: #3b82f6;">0</div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header">
                <i data-lucide="calendar" style="color: #10b981;"></i>
                <h3>Toplam Rapor Günü</h3>
            </div>
            <div class="dash-card-value" id="stat_toplam_gun" style="color: #10b981;">0</div>
        </div>
        <div class="dash-card">
            <div class="dash-card-header">
                <i data-lucide="alert-triangle" style="color: #ef4444;"></i>
                <h3 style="color: #ef4444;">Sınırı Aşan Personel</h3>
            </div>
            <div class="dash-card-value" id="stat_siniri_asan" style="color: #ef4444;">0</div>
        </div>
    </div>"""
content = re.sub(cards_pattern, new_cards, content, count=1, flags=re.DOTALL)


# 3. Replace the tree-card and data-table with modern-table in dash-card
table_pattern = r'<div class="tree-card">\s*<table class="data-table" id="table_saglik".*?</table>\s*</div>'
new_table = """<div class="dash-card" style="overflow-x: auto;">
        <div class="dash-card-header" style="margin-bottom: 15px;">
            <i data-lucide="table"></i> <h3 style="margin:0;">Personel Sağlık İzinleri Dökümü</h3>
        </div>
        <table class="modern-table" id="table_saglik" style="width: 100%; white-space: nowrap; font-size: 14px;">
            <thead>
                <tr>
                    <th style="position: sticky; left: 0; background: var(--bg-card); z-index: 2; padding: 12px; border-bottom: 2px solid var(--border); text-align: left;">Personel Adı</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Oca</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Şub</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Mar</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Nis</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">May</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Haz</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Tem</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Ağu</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Eyl</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Eki</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Kas</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Ara</th>
                    <th style="border-left: 2px solid var(--border); padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Toplam</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Önceden Kesilmiş</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Kesilecek Gün</th>
                    <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: right;">İşlemler</th>
                </tr>
            </thead>
            <tbody id="tbody_saglik">
                <!-- JS ile dolacak -->
            </tbody>
        </table>
    </div>"""
content = re.sub(table_pattern, new_table, content, flags=re.DOTALL)


with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("index.html updated successfully.")
