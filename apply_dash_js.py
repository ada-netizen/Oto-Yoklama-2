import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\dashboard.js", "r", encoding="utf-8") as f:
    content = f.read()

js_code = """
async function dashboardKritikOgrencilerYukle() {
    const tbody = document.getElementById("dashboard_kritik_ogrenciler_body");
    if (!tbody) return;
    try {
        const response = await fetch(`${API}/dashboard/kritik-ogrenciler`);
        if (!response.ok) throw new Error("Veri alinamadi");
        const data = await response.json();
        
        tbody.innerHTML = "";
        
        if (data.basarili && data.veri.length > 0) {
            data.veri.forEach(ogr => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="font-weight: bold;">${ogr.sinif}</td>
                    <td>${ogr.no}</td>
                    <td>${ogr.ad_soyad}</td>
                    <td style="text-align: center;"><span class="badge badge-warning">${ogr.ozursuz}</span></td>
                    <td style="text-align: center;"><span class="badge badge-success">${ogr.ozurlu}</span></td>
                    <td style="text-align: center;"><span class="badge badge-danger">${ogr.toplam}</span></td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--fg-sub);">Kritik sınırda öğrenci bulunmamaktadır.</td></tr>`;
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">Veriler yüklenemedi.</td></tr>`;
    }
}
"""

if "dashboardKritikOgrencilerYukle" not in content:
    content += js_code
    # Hook into dashboardYukle
    content = re.sub(r'(async function dashboardYukle\(\) \{[\s\S]*?)(?=\})', r'\1\n    await dashboardKritikOgrencilerYukle();\n', content, count=1)
    
    with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\dashboard.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("dashboard.js updated.")
