
import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacement = '''    <!-- YENİ: Özet Kartları -->
    <div class=\"dash-grid\" style=\"margin-bottom: 20px;\">
        <div class=\"dash-card\">
            <div class=\"dash-card-header\">
                <i data-lucide=\"users\" style=\"color: #3b82f6;\"></i>
                <h3>Raporlu Personel</h3>
            </div>
            <div class=\"dash-card-value\" id=\"stat_raporlu_kisi\" style=\"color: #3b82f6;\">0</div>
        </div>
        <div class=\"dash-card\">
            <div class=\"dash-card-header\">
                <i data-lucide=\"calendar\" style=\"color: #10b981;\"></i>
                <h3>Toplam Rapor Günü</h3>
            </div>
            <div class=\"dash-card-value\" id=\"stat_toplam_gun\" style=\"color: #10b981;\">0</div>
        </div>
        <div class=\"dash-card\">
            <div class=\"dash-card-header\">
                <i data-lucide=\"alert-triangle\" style=\"color: #ef4444;\"></i>
                <h3 style=\"color: #ef4444;\">Sınırı Aşan Personel</h3>
            </div>
            <div class=\"dash-card-value\" id=\"stat_siniri_asan\" style=\"color: #ef4444;\">0</div>
        </div>
    </div>

    <div class=\"dash-card\" style=\"overflow-x: auto;\">
        <div class=\"dash-card-header\">
            <i data-lucide=\"table\"></i> <h3>Personel Sağlık İzinleri Dökümü</h3>
        </div>
        <table class=\"modern-table\" id=\"table_saglik\" style=\"width: 100%; white-space: nowrap; min-width: 1100px;\">
            <thead>
                <tr>
                    <th style=\"position: sticky; left: 0; background: var(--bg-card); z-index: 2;\">Personel Adı</th>
                    <th>Oca</th>
                    <th>Şub</th>
                    <th>Mar</th>
                    <th>Nis</th>
                    <th>May</th>
                    <th>Haz</th>
                    <th>Tem</th>
                    <th>Ağu</th>
                    <th>Eyl</th>
                    <th>Eki</th>
                    <th>Kas</th>
                    <th>Ara</th>
                    <th style=\"border-left: 2px solid var(--border);\">Toplam</th>
                    <th>Önceden Kesilmiş (Manuel)</th>
                    <th>Kesilecek Gün Durumu</th>
                    <th>İşlemler</th>
                </tr>
            </thead>
            <tbody id=\"tbody_saglik\"></tbody>
        </table>
    </div>'''

new_html = re.sub(r'    <!-- YENİ: Özet Kartları -->.*?<tbody id=\
tbody_saglik\></tbody>\n\s*</table>\n\s*</div>', replacement.replace('\', ''), html, flags=re.DOTALL)
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

