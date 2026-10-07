import re

with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\saglik.js", "r", encoding="utf-8") as f:
    content = f.read()

# Replace saglikTablosunuCiz function
pattern = re.compile(r"async function saglikTablosunuCiz\(\)\s*\{.*?\}(?=\n\n|\n$|async function|function|\Z)", re.DOTALL)

new_func = """async function saglikTablosunuCiz() {
    const tbody = document.getElementById("tbody_saglik");
    if (!tbody) return;

    try {
        const response = await fetch(`${API}/saglik/istatistik`);
        if (!response.ok) throw new Error("Veri alinamadi");
        const veriler = await response.json();

        tbody.innerHTML = "";

        if (veriler.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">Sağlık izni kaydı bulunamadı.</td></tr>`;
            return;
        }

        veriler.forEach(veri => {
            const tr = document.createElement("tr");

            // Personel Adı
            const tdAd = document.createElement("td");
            tdAd.innerHTML = `<strong>${veri.personel_adi}</strong>`;
            tr.appendChild(tdAd);

            // Ay/Yıl
            const tdAyYil = document.createElement("td");
            tdAyYil.innerHTML = `<span class="badge" style="background: var(--bg-soft); color: var(--text-color);">${veri.ay}/${veri.yil}</span>`;
            tr.appendChild(tdAyYil);

            // Toplam İzin (Gün)
            const tdToplam = document.createElement("td");
            let badgeClass = "badge-success";
            if (veri.toplam_izin_gunu > 0) badgeClass = "badge-warning";
            if (veri.toplam_izin_gunu >= 7) badgeClass = "badge-danger";
            
            tdToplam.innerHTML = `<span class="badge ${badgeClass}">${veri.toplam_izin_gunu} Gün</span>`;
            tr.appendChild(tdToplam);

            // Önceden Kesilmiş
            const tdKesilmis = document.createElement("td");
            const inputKesilmis = document.createElement("input");
            inputKesilmis.type = "number";
            inputKesilmis.value = veri.onceden_kesilmis || 0;
            inputKesilmis.className = "form-control input-onceden-kesilmis";
            inputKesilmis.min = 0;
            inputKesilmis.style.width = "70px";
            inputKesilmis.dataset.id = veri.id;
            
            inputKesilmis.addEventListener('change', async (e) => {
                const yeniDeger = parseInt(e.target.value) || 0;
                const kayitId = e.target.dataset.id;
                
                try {
                    const res = await fetch(`${API}/saglik/onceden-kesilmis-guncelle`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: kayitId, onceden_kesilmis: yeniDeger })
                    });
                    
                    if (res.ok) {
                        await saglikOzetKartlariniGuncelle();
                        await saglikTablosunuCiz();
                        toastGoster('Kesinti güncellendi', 'success');
                    } else {
                        toastGoster('Güncelleme hatası', 'error');
                    }
                } catch (error) {
                    console.error('Güncelleme hatası:', error);
                    toastGoster('Bağlantı hatası', 'error');
                }
            });
            tdKesilmis.appendChild(inputKesilmis);
            tr.appendChild(tdKesilmis);

            // Toplam Kesinti (Manuel + Sistem)
            const tdKesinti = document.createElement("td");
            tdKesinti.innerHTML = `<strong>${veri.toplam_kesinti_gunu} Gün</strong>`;
            tr.appendChild(tdKesinti);

            // Durum / Maaş Kesintisi uyarısı
            const tdDurum = document.createElement("td");
            if (veri.toplam_izin_gunu > 7) {
                tdDurum.innerHTML = `<span class="badge badge-danger"><i class="fas fa-exclamation-triangle"></i> Maaş Kesintisi</span>`;
            } else {
                tdDurum.innerHTML = `<span class="badge badge-success"><i class="fas fa-check"></i> Normal</span>`;
            }
            tr.appendChild(tdDurum);

            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Tablo çizim hatası:", error);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:red;">Veriler yüklenirken hata oluştu.</td></tr>`;
    }
}"""

if pattern.search(content):
    content = pattern.sub(new_func, content, count=1)
    with open(r"c:\Users\HP\Downloads\Oto-Yoklama-2-guncel\frontend\js\saglik.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("saglik.js updated successfully.")
else:
    print("Could not find saglikTablosunuCiz function in saglik.js.")
