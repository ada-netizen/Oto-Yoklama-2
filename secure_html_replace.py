import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

risk_table = """
    <!-- YENİ EKLENEN: Kritik Sınırdaki Öğrenciler Risk Tablosu -->
    <div class="dash-card" style="margin-bottom: 20px;">
        <div class="dash-card-header">
            <i data-lucide="alert-circle" style="color: #ef4444;"></i>
            <h3>Kritik Sınırdaki Öğrenciler</h3>
            <span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #ef4444; margin-left: 10px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">(10 gün ve üzeri)</span>
        </div>
        <div style="overflow-x: auto; max-height: 300px;">
            <table class="modern-table" style="width: 100%; white-space: nowrap;">
                <thead style="position: sticky; top: 0; background: var(--bg-card); z-index: 1;">
                    <tr>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: left;">Sınıf</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: left;">No</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: left;">Ad Soyad</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Özürsüz</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Özürlü</th>
                        <th style="padding: 12px; border-bottom: 2px solid var(--border); text-align: center;">Toplam</th>
                    </tr>
                </thead>
                <tbody id="dashboard_kritik_ogrenciler_body">
                    <!-- JS ile doldurulacak -->
                </tbody>
            </table>
        </div>
    </div>
"""

# 1. Dashboard: inject right before <!-- MAIN CHARTS (ROW 1) -->
if "Kritik Sınırdaki Öğrenciler Risk Tablosu" not in content:
    content = content.replace("    <!-- MAIN CHARTS (ROW 1) -->", risk_table + "\n    <!-- MAIN CHARTS (ROW 1) -->")


new_saglik = """<div class="tab-content" id="sekme_saglik" style="overflow-y: auto; background-color: var(--bg-main); padding: 20px;">
    <div class="top-bar" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <h2 class="top-bar-title" style="margin:0;"><i data-lucide="heart" height="20" width="20"></i> Personel Sağlık İzinleri (<span id="saglik_yil"></span> Yılı)</h2>
        <div style="display: flex; gap: 10px;">
            <div style="position: relative; display: inline-block;">
                <button class="btn" style="background-color: var(--bg-soft); color: var(--fg-main); border: 1px solid var(--border); padding: 10px 20px;"><i data-lucide="upload" height="16" width="16"></i> Sağlık İzni Yükle</button>
                <input type="file" accept=".pdf" onchange="saglikPdfYukle(event)" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;" title="PDF Yükle">
            </div>
            <button class="btn" style="background-color: var(--tree-sel); color: white; padding: 10px 20px;" onclick="saglikModalAc()"><i data-lucide="plus" height="16" width="16"></i> Yeni Rapor Ekle</button>
        </div>
    </div>
    
    <!-- YENİ: Özet Kartları -->
    <div class="dash-grid" style="margin-bottom: 20px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
        <div class="dash-card" style="background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column;">
            <div class="dash-card-header" style="display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px;">
                <i data-lucide="users" style="color: #3b82f6;"></i>
                <h3 style="margin: 0; font-size: 14px; color: var(--fg-main); font-weight: 600;">Raporlu Personel</h3>
            </div>
            <div class="dash-card-value" id="stat_raporlu_kisi" style="color: #3b82f6; font-size: 24px; font-weight: 800;">0</div>
        </div>
        <div class="dash-card" style="background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column;">
            <div class="dash-card-header" style="display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px;">
                <i data-lucide="calendar" style="color: #10b981;"></i>
                <h3 style="margin: 0; font-size: 14px; color: var(--fg-main); font-weight: 600;">Toplam Rapor Günü</h3>
            </div>
            <div class="dash-card-value" id="stat_toplam_gun" style="color: #10b981; font-size: 24px; font-weight: 800;">0</div>
        </div>
        <div class="dash-card" style="background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column;">
            <div class="dash-card-header" style="display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px;">
                <i data-lucide="alert-triangle" style="color: #ef4444;"></i>
                <h3 style="margin: 0; font-size: 14px; color: #ef4444; font-weight: 600;">Sınırı Aşan Personel</h3>
            </div>
            <div class="dash-card-value" id="stat_siniri_asan" style="color: #ef4444; font-size: 24px; font-weight: 800;">0</div>
        </div>
    </div>

    <div class="dash-card" style="background: var(--bg-card); border-radius: 12px; padding: 15px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow-x: auto;">
        <div class="dash-card-header" style="display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px;">
            <i data-lucide="table"></i> <h3 style="margin:0; font-size: 14px; color: var(--fg-main); font-weight: 600;">Personel Sağlık İzinleri Dökümü</h3>
        </div>
        <table class="modern-table" id="table_saglik" style="width: 100%; border-collapse: collapse; font-size: 11px; white-space: nowrap;">
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
    </div>
</div>
"""

pattern = r'(<div class="tab-content" id="sekme_saglik".*?)(?=\s*<div class="tab-content" id="sekme_ayarlar">)'
content = re.sub(pattern, new_saglik, content, flags=re.DOTALL)

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("index.html fully updated securely.")
