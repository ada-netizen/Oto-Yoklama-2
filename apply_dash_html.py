import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "r", encoding="utf-8") as f:
    content = f.read()

dashboard_cards_pattern = r'(<div class="dash-grid" style="margin-bottom: 20px;">\s*<div class="dash-card">.*?</div>\s*</div>)'

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

if "Kritik Sınırdaki Öğrenciler" not in content:
    # Insert right after the dash-grid in sekme_dashboard
    # We find the specific dash-grid in the Dashboard section.
    # The dashboard tab starts with id="sekme_dashboard"
    dashboard_section_match = re.search(r'<div class="tab-content aktif" id="sekme_dashboard".*?</div>\s*</div>', content, re.DOTALL)
    if dashboard_section_match:
        dashboard_content = dashboard_section_match.group(0)
        # Find the first dash-grid inside it
        new_dashboard_content = re.sub(r'(<div class="dash-grid" style="margin-bottom: 20px;">.*?</div>\s*</div>)', r'\1\n' + risk_table, dashboard_content, count=1, flags=re.DOTALL)
        content = content.replace(dashboard_content, new_dashboard_content)

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Dashboard risk table added to index.html.")
