from fastapi import APIRouter
from dependencies import db
from collections import defaultdict
import datetime
import re

router = APIRouter()

def kisa_sube(sube_adi):
    if not sube_adi:
        return ""
    match = re.search(r'(\d+)\.\s*S.n.f\s*/\s*([A-Za-z0-9ÇĞİÖŞÜçğıöşü]+)\s*.ubesi', str(sube_adi))
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return sube_adi

@router.get("/istatistikler")
def get_istatistikler():
    try:
        # Tumu
        db.cursor.execute("SELECT no, sube, ad_soyad FROM ogrenciler")
        tum_ogrenciler = db.cursor.fetchall()
        toplam_ogrenci = len(tum_ogrenciler)
        
        sube_counts = defaultdict(int)
        for row in tum_ogrenciler:
            sube_counts[row[1]] += 1

        db.cursor.execute("SELECT no, tarih, tur, gun FROM devamsizliklar")
        dev_ham = db.cursor.fetchall()

        # Iskeleler
        sube_dev = defaultdict(float)
        tur_dev = defaultdict(float)
        aylik_dev = defaultdict(float)
        gunluk_dev = defaultdict(float)
        ogrenci_toplam = defaultdict(float)
        ogrenci_ozursuz = defaultdict(float)
        ogrenci_g = defaultdict(int)  # Changed to int for counting occurrences

        aylar = {"01":"Oca", "02":"Şub", "03":"Mar", "04":"Nis", "05":"May", "06":"Haz", "07":"Tem", "08":"Ağu", "09":"Eyl", "10":"Eki", "11":"Kas", "12":"Ara"}
        hafta_gunleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        ozursuz_turler = ["G", "Y", "ÖZÜRSÜZ"]

        for r in dev_ham:
            no, tarih, tur, gun = r
            try:
                g_val = float(gun)
            except:
                continue

            tur_dev[tur] += g_val
            ogrenci_toplam[no] += g_val
            if tur.upper() in ozursuz_turler or tur.upper() == 'G':
                ogrenci_ozursuz[no] += g_val
            
            if tur.upper() == 'G':
                ogrenci_g[no] += 1  # Count occurrences instead of sum

            # Tarih parcalama
            parts = str(tarih).split('/')
            if len(parts) == 3:
                # Aylik
                ay_num = parts[1].zfill(2)
                ay_ad = aylar.get(ay_num, ay_num)
                aylik_dev[ay_ad] += g_val
                
                # Gunluk (Haftanin Gunu)
                try:
                    dt = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                    gun_adi = hafta_gunleri[dt.weekday()]
                    gunluk_dev[gun_adi] += g_val
                except: pass

        # Sube bazli
        ogrenci_sube_map = {r[0]: r[1] for r in tum_ogrenciler}
        ogrenci_ad_map = {r[0]: r[2] for r in tum_ogrenciler}

        for no, g_val in ogrenci_toplam.items():
            sube = ogrenci_sube_map.get(no, "Bilinmeyen")
            sube_dev[sube] += g_val

        # Sube Ortalamalari
        sube_ozursuz = defaultdict(float)
        for no, g_val in ogrenci_ozursuz.items():
            sube = ogrenci_sube_map.get(no, "Bilinmeyen")
            sube_ozursuz[sube] += g_val

        sube_ort_list = []
        for sube, toplam in sube_dev.items():
            count = sube_counts.get(sube, 0)
            if count > 0:
                ozursuz_toplam = sube_ozursuz.get(sube, 0)
                ozurlu_toplam = toplam - ozursuz_toplam
                
                ort_ozursuz = round(ozursuz_toplam / count, 2)
                ort_ozurlu = round(ozurlu_toplam / count, 2)
                ort_toplam = round(toplam / count, 2)
                sube_ort_list.append({
                    "sube": kisa_sube(sube), 
                    "ortalama": ort_toplam, 
                    "ozursuz_ort": ort_ozursuz, 
                    "ozurlu_ort": ort_ozurlu
                })
        
        def sube_sort_key(item):
            s = item["sube"]
            m = re.match(r'^(\d+)/(.*)$', s)
            if m:
                return (int(m.group(1)), m.group(2))
            return (999, s)

        sube_ort_list = sorted(sube_ort_list, key=sube_sort_key)

        # Ozurlu / Ozursuz
        ozursuz_toplam = sum(ogrenci_ozursuz.values())
        ozurlu_toplam = sum(ogrenci_toplam.values()) - ozursuz_toplam

        # KPI'lar
        kpi_ozursuz_10 = sum(1 for v in ogrenci_ozursuz.values() if v >= 10)
        kpi_toplam_30 = sum(1 for v in ogrenci_toplam.values() if v >= 30)
        kpi_sifir = toplam_ogrenci - len(ogrenci_toplam)

        # Evraklar
        db.cursor.execute("SELECT tarih FROM uretilen_evraklar")
        evrak_ham = db.cursor.fetchall()
        kpi_evrak = len(evrak_ham)

        evrak_aylik = defaultdict(int)
        for r in evrak_ham:
            etarih = r[0]
            try:
                if "T" in str(etarih) or "-" in str(etarih):
                    dt = datetime.datetime.fromisoformat(str(etarih).split('.')[0])
                    ay_ad = aylar.get(f"{dt.month:02d}", str(dt.month))
                    evrak_aylik[ay_ad] += 1
            except: pass

        # Riskli listeler
        riskli_list = []
        g_riskli_list = []
        for no, topt in ogrenci_toplam.items():
            if topt > 0:
                riskli_list.append({"ad": ogrenci_ad_map.get(no, no), "sube": kisa_sube(ogrenci_sube_map.get(no, "")), "toplam": topt})
        for no, topt in ogrenci_g.items():
            if topt > 0:
                g_riskli_list.append({"ad": ogrenci_ad_map.get(no, no), "sube": kisa_sube(ogrenci_sube_map.get(no, "")), "toplam": topt})

        riskli_list = sorted(riskli_list, key=lambda x: x["toplam"], reverse=True)[:5]
        g_riskli_list = sorted(g_riskli_list, key=lambda x: x["toplam"], reverse=True)[:5]

        # Ay sirasi
        ay_sirasi = ["Eyl", "Eki", "Kas", "Ara", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu"]
        aylik_trend = [{"ay": a, "toplam": aylik_dev.get(a, 0)} for a in ay_sirasi if a in aylik_dev or aylik_dev.get(a,0) > 0]
        if not aylik_trend: aylik_trend = [{"ay": k, "toplam": v} for k, v in aylik_dev.items()]
        
        aylik_evrak_trend = [{"ay": a, "toplam": evrak_aylik.get(a, 0)} for a in ay_sirasi if a in evrak_aylik or evrak_aylik.get(a,0) > 0]
        if not aylik_evrak_trend: aylik_evrak_trend = [{"ay": k, "toplam": v} for k, v in evrak_aylik.items()]

        gun_sirasi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        haftanin_gunleri = [{"gun": g, "toplam": gunluk_dev.get(g, 0)} for g in gun_sirasi]

        return {
            "kpis": {
                "ozursuz_10": kpi_ozursuz_10,
                "toplam_30": kpi_toplam_30,
                "sifir_hata": kpi_sifir,
                "toplam_evrak": kpi_evrak
            },
            "sube_dev": [{"sube": k, "toplam": v} for k, v in sube_dev.items()], # Kept for maybe other logic
            "sube_ortalamalar": sube_ort_list,
            "ozurlu_vs_ozursuz": {"ozurlu": ozurlu_toplam, "ozursuz": ozursuz_toplam},
            "tur_dev": [{"tur": k, "toplam": v} for k, v in tur_dev.items()],
            "aylik_trend": aylik_trend,
            "aylik_evrak": aylik_evrak_trend,
            "haftanin_gunleri": haftanin_gunleri,
            "riskli_ogrenciler": riskli_list,
            "g_turu_riskli": g_riskli_list
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"hata": str(e)}
