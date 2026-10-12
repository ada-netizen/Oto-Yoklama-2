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
        from araclar import VeriAraclari
        ogrenci_listesi, devamsizlik_listesi = db.yukle()
        toplam_ogrenci = len(ogrenci_listesi)

        gruplu_dev = defaultdict(list)
        for d in devamsizlik_listesi:
            gruplu_dev[str(d.get('no', '')).strip()].append(d)

        ogrenci_ozursuz = {}
        ogrenci_ozurlu = {}
        ogrenci_toplam = {}
        ogrenci_sube_map = {}
        ogrenci_ad_map = {}
        sube_counts = defaultdict(int)

        for ogr in ogrenci_listesi:
            no_key = str(ogr.get('no', '')).strip()
            sube = ogr.get('sube', '')
            ad = ogr.get('ad_soyad', '')
            ogrenci_sube_map[no_key] = sube
            ogrenci_ad_map[no_key] = ad
            sube_counts[sube] += 1

            ozsz, ozrl = VeriAraclari.hesapla_devamsizlik(no_key, gruplu_dev.get(no_key, []), [])
            ozsz = round(ozsz, 1)
            ozrl = round(ozrl, 1)
            topt = round(ozsz + ozrl, 1)

            ogrenci_ozursuz[no_key] = ozsz
            ogrenci_ozurlu[no_key] = ozrl
            ogrenci_toplam[no_key] = topt

        sube_dev = defaultdict(float)
        sube_ozursuz = defaultdict(float)
        for no_key, topt in ogrenci_toplam.items():
            sube = ogrenci_sube_map.get(no_key, "Bilinmeyen")
            sube_dev[sube] += topt
            sube_ozursuz[sube] += ogrenci_ozursuz.get(no_key, 0.0)

        sube_ort_list = []
        for sube, toplam in sube_dev.items():
            count = sube_counts.get(sube, 0)
            if count > 0:
                ozursuz_toplam = sube_ozursuz.get(sube, 0.0)
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

        # Özürlü / Özürsüz genel toplamları
        ozursuz_genel = round(sum(ogrenci_ozursuz.values()), 1)
        ozurlu_genel = round(sum(ogrenci_ozurlu.values()), 1)

        # KPI'lar
        kpi_ozursuz_10 = sum(1 for v in ogrenci_ozursuz.values() if v >= 10.0)
        kpi_toplam_30 = sum(1 for v in ogrenci_toplam.values() if v >= 30.0)
        kpi_sifir = sum(1 for v in ogrenci_toplam.values() if v == 0.0)

        # Evraklar
        db.cursor.execute("SELECT tarih FROM uretilen_evraklar")
        evrak_ham = db.cursor.fetchall()
        kpi_evrak = len(evrak_ham)

        aylar = {"01":"Oca", "02":"Şub", "03":"Mar", "04":"Nis", "05":"May", "06":"Haz", "07":"Tem", "08":"Ağu", "09":"Eyl", "10":"Eki", "11":"Kas", "12":"Ara"}
        hafta_gunleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        evrak_aylik = defaultdict(int)
        for r in evrak_ham:
            etarih = r[0]
            try:
                if "T" in str(etarih) or "-" in str(etarih):
                    dt = datetime.datetime.fromisoformat(str(etarih).split('.')[0])
                    ay_ad = aylar.get(f"{dt.month:02d}", str(dt.month))
                    evrak_aylik[ay_ad] += 1
            except: pass

        tur_dev = defaultdict(float)
        aylik_dev = defaultdict(float)
        gunluk_dev = defaultdict(float)
        ogrenci_g = defaultdict(int)

        for d in devamsizlik_listesi:
            no = str(d.get('no', '')).strip()
            tarih = d.get('tarih', '')
            tur = str(d.get('tur', '')).upper()
            try:
                g_val = float(VeriAraclari.temiz_sure(d.get('gun', 0)))
            except:
                continue

            tur_dev[tur] += g_val
            if tur == 'G':
                ogrenci_g[no] += 1

            parts = str(tarih).replace('.', '/').replace('-', '/').split('/')
            if len(parts) == 3:
                ay_num = parts[1].zfill(2)
                ay_ad = aylar.get(ay_num, ay_num)
                aylik_dev[ay_ad] += g_val
                try:
                    dt = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                    gun_adi = hafta_gunleri[dt.weekday()]
                    gunluk_dev[gun_adi] += g_val
                except:
                    pass

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

        # Kritik Eşik Erken Uyarı Verileri
        esik_kategorileri = {
            "ramakkala_10": [],    # 8.5 <= ozursuz < 10.0 (Kritik Eşik: Ramak Kala)
            "asanlar_10": [],      # ozursuz >= 10.0 (Sınıf Tekrarı Riski)
            "mektup_siniri_5": [], # 4.5 <= ozursuz <= 5.0 (1. Mektup Eşiği)
            "toplam_risk_25": []   # toplam >= 25.0 (Toplam Sınır 30'a Yaklaşanlar)
        }

        for ogr in ogrenci_listesi:
            no = str(ogr.get('no', '')).strip()
            topt = ogrenci_toplam.get(no, 0.0)
            ozst = ogrenci_ozursuz.get(no, 0.0)
            ozlt = ogrenci_ozurlu.get(no, 0.0)
            if topt == 0 and ozst == 0:
                continue

            ogr_ozet = {
                "no": no,
                "ad": ogrenci_ad_map.get(no, no),
                "sube": kisa_sube(ogrenci_sube_map.get(no, "")),
                "ozursuz": ozst,
                "ozurlu": ozlt,
                "toplam": topt
            }

            if 8.5 <= ozst < 10.0:
                esik_kategorileri["ramakkala_10"].append(ogr_ozet)
            elif ozst >= 10.0:
                esik_kategorileri["asanlar_10"].append(ogr_ozet)

            if 4.5 <= ozst <= 5.0:
                esik_kategorileri["mektup_siniri_5"].append(ogr_ozet)

            if topt >= 25.0:
                esik_kategorileri["toplam_risk_25"].append(ogr_ozet)

        esik_kategorileri["ramakkala_10"].sort(key=lambda x: x["ozursuz"], reverse=True)
        esik_kategorileri["asanlar_10"].sort(key=lambda x: x["ozursuz"], reverse=True)
        esik_kategorileri["mektup_siniri_5"].sort(key=lambda x: x["ozursuz"], reverse=True)
        esik_kategorileri["toplam_risk_25"].sort(key=lambda x: x["toplam"], reverse=True)

        return {
            "kpis": {
                "ozursuz_10": kpi_ozursuz_10,
                "toplam_30": kpi_toplam_30,
                "sifir_hata": kpi_sifir,
                "toplam_evrak": kpi_evrak,
                "ramakkala_10_sayi": len(esik_kategorileri["ramakkala_10"]),
                "mektup_5_sayi": len(esik_kategorileri["mektup_siniri_5"])
            },
            "sube_dev": [{"sube": k, "toplam": v} for k, v in sube_dev.items()],
            "sube_ortalamalar": sube_ort_list,
            "ozurlu_vs_ozursuz": {"ozurlu": ozurlu_genel, "ozursuz": ozursuz_genel},
            "tur_dev": [{"tur": k, "toplam": v} for k, v in tur_dev.items()],
            "aylik_trend": aylik_trend,
            "aylik_evrak": aylik_evrak_trend,
            "haftanin_gunleri": haftanin_gunleri,
            "riskli_ogrenciler": riskli_list,
            "g_turu_riskli": g_riskli_list,
            "kritik_esikler": esik_kategorileri
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"hata": str(e)}

@router.get("/kritik-esikler")
def get_kritik_esikler():
    stats = get_istatistikler()
    if isinstance(stats, dict) and "kritik_esikler" in stats:
        return {"basarili": True, "veriler": stats["kritik_esikler"]}
    return {"basarili": False, "mesaj": stats.get("hata", "Veri alınamadı")}
