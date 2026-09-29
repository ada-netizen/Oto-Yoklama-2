from fastapi import APIRouter
from dependencies import db
from collections import defaultdict
import datetime

router = APIRouter()

@router.get("/istatistikler")
def get_istatistikler():
    try:
        # Tumu
        db.cursor.execute("SELECT no, sube, ad_soyad FROM ogrenciler")
        tum_ogrenciler = db.cursor.fetchall()
        toplam_ogrenci = len(tum_ogrenciler)

        db.cursor.execute("SELECT no, tarih, tur, gun FROM devamsizliklar")
        dev_ham = db.cursor.fetchall()

        # Iskeleler
        sube_dev = defaultdict(float)
        tur_dev = defaultdict(float)
        aylik_dev = defaultdict(float)
        gunluk_dev = defaultdict(float)
        ogrenci_toplam = defaultdict(float)
        ogrenci_ozursuz = defaultdict(float)
        ogrenci_g = defaultdict(float)

        aylar = {"01":"Oca", "02":"Şub", "03":"Mar", "04":"Nis", "05":"May", "06":"Haz", "07":"Tem", "08":"Ağu", "09":"Eyl", "10":"Eki", "11":"Kas", "12":"Ara"}
        hafta_gunleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        ozursuz_turler = ["G", "Y", "ÖZÜRSÜZ"] # Ozel veya yaygin ozursuz tur kodlari

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
                ogrenci_g[no] += g_val

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

        # KPI'lar
        kpi_ozursuz_10 = sum(1 for v in ogrenci_ozursuz.values() if v > 10)
        kpi_toplam_30 = sum(1 for v in ogrenci_toplam.values() if v > 30)
        kpi_sifir = toplam_ogrenci - len(ogrenci_toplam)

        # Evraklar
        db.cursor.execute("SELECT tur, personel_ad, brans, tarih FROM uretilen_evraklar")
        evrak_ham = db.cursor.fetchall()
        kpi_evrak = len(evrak_ham)

        evrak_brans = defaultdict(int)
        evrak_personel = defaultdict(int)
        evrak_aylik = defaultdict(int)

        for r in evrak_ham:
            etur, pad, brans, etarih = r
            evrak_brans[brans if brans else "Belirtilmemiş"] += 1
            evrak_personel[pad] += 1
            try:
                # ISO date format: YYYY-MM-DDTHH:MM:SS
                if "T" in str(etarih) or "-" in str(etarih):
                    dt = datetime.datetime.fromisoformat(str(etarih).split('.')[0])
                    ay_ad = aylar.get(f"{dt.month:02d}", str(dt.month))
                    evrak_aylik[ay_ad] += 1
            except: pass

        # Sortings
        sube_dev_sorted = sorted(sube_dev.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Riskli listeler
        riskli_list = []
        g_riskli_list = []
        for no, topt in ogrenci_toplam.items():
            if topt > 0:
                riskli_list.append({"ad": ogrenci_ad_map.get(no, no), "sube": ogrenci_sube_map.get(no, ""), "toplam": topt})
        for no, topt in ogrenci_g.items():
            if topt > 0:
                g_riskli_list.append({"ad": ogrenci_ad_map.get(no, no), "sube": ogrenci_sube_map.get(no, ""), "toplam": topt})

        riskli_list = sorted(riskli_list, key=lambda x: x["toplam"], reverse=True)[:5]
        g_riskli_list = sorted(g_riskli_list, key=lambda x: x["toplam"], reverse=True)[:5]
        
        personel_top = [{"ad": k, "toplam": v} for k, v in sorted(evrak_personel.items(), key=lambda x: x[1], reverse=True)[:5]]

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
            "sube_dev": [{"sube": k, "toplam": v} for k, v in sube_dev_sorted],
            "tur_dev": [{"tur": k, "toplam": v} for k, v in tur_dev.items()],
            "aylik_trend": aylik_trend,
            "aylik_evrak": aylik_evrak_trend,
            "haftanin_gunleri": haftanin_gunleri,
            "riskli_ogrenciler": riskli_list,
            "g_turu_riskli": g_riskli_list,
            "evrak_branslar": [{"brans": k, "toplam": v} for k, v in sorted(evrak_brans.items(), key=lambda x: x[1], reverse=True)[:10]],
            "personel_top": personel_top
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"hata": str(e)}
