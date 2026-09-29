import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Tab Button
btn_old = '''<button class="tab-btn" onclick="sekmeAc(event, 'sekme_ayarlar')"><i data-lucide="settings" height="16" width="16"></i> Ayarlar ve Yedekleme</button>'''
btn_new = '''<button class="tab-btn" onclick="sekmeAc(event, 'sekme_dashboard'); dashboardYukle();"><i data-lucide="bar-chart-2" height="16" width="16"></i> İstatistikler</button>\n<button class="tab-btn" onclick="sekmeAc(event, 'sekme_ayarlar')"><i data-lucide="settings" height="16" width="16"></i> Ayarlar ve Yedekleme</button>'''
html = html.replace(btn_old, btn_new)

# 2. Add Archive Section in Ayarlar
arsiv_html = '''
              <div class="settings-section">
                  <h3 class="settings-section-title"><i data-lucide="archive" height="16" width="16"></i> Dönem Sonu Arşivleme</h3>
                  <div class="settings-list-card">
                      <div class="settings-list-item">
                          <div class="settings-item-info">
                              <span class="settings-item-name">Veritabanını Arşivle ve Sıfırla</span>
                              <span class="settings-item-desc">Mevcut dönemi arşivler (Personel sabit kalır, diğer veriler sıfırlanır).</span>
                          </div>
                          <div class="settings-item-action" style="display: flex; gap: 5px;">
                              <input id="arsiv_adi" placeholder="Örn: 2025-2026_Arsiv" type="text" style="padding: 6px; width: 150px;" />
                              <button class="btn btn-kirmizi" onclick="arsivle()">Arşivle</button>
                          </div>
                      </div>
                  </div>
              </div>
'''
html = html.replace('<!-- İLERİ DÜZEY VE YEDEKLEME -->', arsiv_html + '\n              <!-- İLERİ DÜZEY VE YEDEKLEME -->')

# 3. Add sekme_dashboard
dashboard_html = '''
<div class="tab-content" id="sekme_dashboard" style="overflow-y: auto; background-color: var(--bg-main); padding: 20px;">
    <div class="top-bar" style="margin-bottom: 20px; border-radius: 8px;">
        <h2 class="top-bar-title"><i data-lucide="bar-chart-2" height="20" width="20"></i> Okul İstatistikleri & Dashboard</h2>
        <button class="btn btn-dev" onclick="dashboardYukle()"><i data-lucide="refresh-cw" height="16" width="16"></i> Yenile</button>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
        <!-- KART 1: Sube Devamsizlik -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="margin-top: 0; font-size: 13px; color: var(--fg-main); text-align: center;">Şubelere Göre Devamsızlık</h3>
            <canvas id="chart_sube"></canvas>
        </div>
        
        <!-- KART 2: Tur Devamsizlik -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="margin-top: 0; font-size: 13px; color: var(--fg-main); text-align: center;">Devamsızlık Türü Dağılımı</h3>
            <canvas id="chart_tur"></canvas>
        </div>
        
        <!-- KART 3: Aylik Trend -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="margin-top: 0; font-size: 13px; color: var(--fg-main); text-align: center;">Aylara Göre Devamsızlık</h3>
            <canvas id="chart_aylik"></canvas>
        </div>
        
        <!-- KART 4: Evrak Branslari -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="margin-top: 0; font-size: 13px; color: var(--fg-main); text-align: center;">Evrak Giden Branşlar</h3>
            <canvas id="chart_evrak"></canvas>
        </div>
        
        <!-- KART 5: Riskli Ogrenciler -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
            <h3 style="margin-top: 0; font-size: 13px; color: var(--fg-main); text-align: center;">En Çok Devamsızlık (Genel)</h3>
            <table style="width: 100%; text-align: left; font-size: 11px; border-collapse: collapse;">
                <thead><tr style="border-bottom: 1px solid var(--border);"><th>Öğrenci</th><th>Şube</th><th>Gün</th></tr></thead>
                <tbody id="tbody_riskli"></tbody>
            </table>
        </div>
        
        <!-- KART 6: G Turu Riskli -->
        <div class="tree-card" style="background: var(--bg-card); padding: 15px; border-radius: 8px; border: 1px solid #ef4444;">
            <h3 style="margin-top: 0; font-size: 13px; color: #ef4444; text-align: center;">En Çok "G" (Geç) Kalanlar</h3>
            <table style="width: 100%; text-align: left; font-size: 11px; border-collapse: collapse;">
                <thead><tr style="border-bottom: 1px solid var(--border);"><th>Öğrenci</th><th>Şube</th><th>G-Gün</th></tr></thead>
                <tbody id="tbody_g_riskli"></tbody>
            </table>
        </div>
    </div>
</div>
'''

html = html.replace('<!-- ================= YILLIK DEVAMSIZLIK MODAL ================= -->', dashboard_html + '\n  <!-- ================= YILLIK DEVAMSIZLIK MODAL ================= -->')

# 4. Add dashboard.js reference
html = html.replace('<script src="js/core.js"></script>', '<script src="js/core.js"></script>\n<script src="js/dashboard.js"></script>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated index.html")
