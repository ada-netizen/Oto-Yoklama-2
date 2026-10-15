from fastapi import APIRouter
from dependencies import db
from collections import defaultdict
import datetime
import re

router = APIRouter()

def kisa_sube(sube_adi):
    if not sube_adi:
        return ""
    from araclar import VeriAraclari
    return VeriAraclari.kisa_sube_adi(sube_adi)

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

        sube_toplam = defaultdict(float)
        sube_ozursuz = defaultdict(float)
        sube_ozurlu = defaultdict(float)
        for no_key, topt in ogrenci_toplam.items():
            sube = ogrenci_sube_map.get(no_key, "Bilinmeyen")
            sube_toplam[sube] += topt
            sube_ozursuz[sube] += ogrenci_ozursuz.get(no_key, 0.0)
            sube_ozurlu[sube] += ogrenci_ozurlu.get(no_key, 0.0)

        sube_ort_list = []
        for sube, count in sube_counts.items():
            if count > 0:
                ozursuz_toplam = round(sube_ozursuz.get(sube, 0.0), 1)
                ozurlu_toplam = round(sube_ozurlu.get(sube, 0.0), 1)
                toplam = round(ozursuz_toplam + ozurlu_toplam, 1)
                
                ort_ozursuz = round(ozursuz_toplam / count, 2)
                ort_ozurlu = round(ozurlu_toplam / count, 2)
                ort_toplam = round(toplam / count, 2)
                sube_ort_list.append({
                    "sube": kisa_sube(sube), 
                    "ortalama": ort_toplam, 
                    "ozursuz_ort": ort_ozursuz, 
                    "ozurlu_ort": ort_ozurlu,
                    "ozursuz_toplam": ozursuz_toplam,
                    "ozurlu_toplam": ozurlu_toplam,
                    "ogrenci_sayisi": count
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
        aylik_ozursuz = defaultdict(float)
        aylik_ozurlu = defaultdict(float)
        gunluk_dev = defaultdict(float)
        gunluk_ozursuz = defaultdict(float)
        gunluk_ozurlu = defaultdict(float)
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

            # Nöbetçi ve Faaliyet muafiyeti yasal devamsızlıktan sayılmaz (SV sağlık sevki olarak özürlü sayılır)
            if tur in ["N", "F"]:
                continue

            # G türü tek başına devamsızlık günü değildir (5 G = 0.5G kuralı öğrenci bazında işlenir)
            if tur == 'G':
                continue

            try:
                parts = str(tarih).replace('.', '/').replace('-', '/').split('/')
                cur_date = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                kalan_gun = g_val
                while kalan_gun > 0:
                    dusulecek = 1.0 if kalan_gun >= 1 else kalan_gun
                    # Hafta içi günleri yasal devamsızlık sayılır
                    if cur_date.weekday() < 5:
                        ay_num = f"{cur_date.month:02d}"
                        ay_ad = aylar.get(ay_num, ay_num)
                        gun_adi = hafta_gunleri[cur_date.weekday()]
                        
                        aylik_dev[ay_ad] += dusulecek
                        gunluk_dev[gun_adi] += dusulecek

                        if tur in ["D", "ÖY", "SY"]:
                            aylik_ozursuz[ay_ad] += dusulecek
                            gunluk_ozursuz[gun_adi] += dusulecek
                        else:
                            aylik_ozurlu[ay_ad] += dusulecek
                            gunluk_ozurlu[gun_adi] += dusulecek

                    kalan_gun -= dusulecek
                    cur_date += datetime.timedelta(days=1)
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
        aylik_trend = [
            {
                "ay": a, 
                "toplam": round(aylik_dev.get(a, 0), 1),
                "ozursuz": round(aylik_ozursuz.get(a, 0), 1),
                "ozurlu": round(aylik_ozurlu.get(a, 0), 1)
            } for a in ay_sirasi if a in aylik_dev or aylik_dev.get(a,0) > 0
        ]
        if not aylik_trend: 
            aylik_trend = [
                {
                    "ay": k, 
                    "toplam": round(v, 1),
                    "ozursuz": round(aylik_ozursuz.get(k, 0), 1),
                    "ozurlu": round(aylik_ozurlu.get(k, 0), 1)
                } for k, v in aylik_dev.items()
            ]
        
        aylik_evrak_trend = [{"ay": a, "toplam": evrak_aylik.get(a, 0)} for a in ay_sirasi if a in evrak_aylik or evrak_aylik.get(a,0) > 0]
        if not aylik_evrak_trend: aylik_evrak_trend = [{"ay": k, "toplam": v} for k, v in evrak_aylik.items()]

        gun_sirasi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        haftanin_gunleri = [
            {
                "gun": g, 
                "toplam": round(gunluk_dev.get(g, 0), 1),
                "ozursuz": round(gunluk_ozursuz.get(g, 0), 1),
                "ozurlu": round(gunluk_ozurlu.get(g, 0), 1)
            } for g in gun_sirasi
        ]

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

        # 1. Devamsızlık Risk Piramidi & Dağılımı (Özürsüz Gün Aralıkları)
        piramit_sayilari = {
            "guvenli": 0,      # 0 <= ozursuz < 2.5
            "uyari_1": 0,      # 2.5 <= ozursuz < 5.0
            "uyari_2": 0,      # 5.0 <= ozursuz < 8.5
            "ramakkala": 0,    # 8.5 <= ozursuz < 10.0
            "kritik": 0        # ozursuz >= 10.0
        }
        for no_key, ozsz in ogrenci_ozursuz.items():
            if ozsz < 2.5:
                piramit_sayilari["guvenli"] += 1
            elif ozsz < 5.0:
                piramit_sayilari["uyari_1"] += 1
            elif ozsz < 8.5:
                piramit_sayilari["uyari_2"] += 1
            elif ozsz < 10.0:
                piramit_sayilari["ramakkala"] += 1
            else:
                piramit_sayilari["kritik"] += 1

        toplam_ogr = max(1, len(ogrenci_listesi))
        risk_piramidi = [
            {"kademe": "Güvenli Bölge", "aralik": "0 - 2.5 Gün", "sayi": piramit_sayilari["guvenli"], "yuzde": round((piramit_sayilari["guvenli"] / toplam_ogr) * 100, 1), "renk": "#10b981"},
            {"kademe": "1. Uyarı Eşiği", "aralik": "2.5 - 5.0 Gün", "sayi": piramit_sayilari["uyari_1"], "yuzde": round((piramit_sayilari["uyari_1"] / toplam_ogr) * 100, 1), "renk": "#eab308"},
            {"kademe": "2. Uyarı / Takip", "aralik": "5.0 - 8.5 Gün", "sayi": piramit_sayilari["uyari_2"], "yuzde": round((piramit_sayilari["uyari_2"] / toplam_ogr) * 100, 1), "renk": "#f97316"},
            {"kademe": "Kritik Eşik / Ramak Kala", "aralik": "8.5 - 10.0 Gün", "sayi": piramit_sayilari["ramakkala"], "yuzde": round((piramit_sayilari["ramakkala"] / toplam_ogr) * 100, 1), "renk": "#ef4444"},
            {"kademe": "Sınıf Tekrarı Riski", "aralik": "10.0+ Gün", "sayi": piramit_sayilari["kritik"], "yuzde": round((piramit_sayilari["kritik"] / toplam_ogr) * 100, 1), "renk": "#b91c1c"}
        ]

        # 2. Kademe Bazlı Karşılaştırma (9, 10, 11, 12. Sınıflar)
        kademe_toplamlar = defaultdict(lambda: {"toplam": 0.0, "ozursuz": 0.0, "ozurlu": 0.0, "ogrenci": 0})
        for no_key, topt in ogrenci_toplam.items():
            sube = ogrenci_sube_map.get(no_key, "")
            k_sube = kisa_sube(sube)
            m = re.match(r'^(\d+)', k_sube)
            kademe_ad = f"{m.group(1)}. Sınıf" if m else "Diğer"
            
            kademe_toplamlar[kademe_ad]["toplam"] += topt
            kademe_toplamlar[kademe_ad]["ozursuz"] += ogrenci_ozursuz.get(no_key, 0.0)
            kademe_toplamlar[kademe_ad]["ozurlu"] += ogrenci_ozurlu.get(no_key, 0.0)
            kademe_toplamlar[kademe_ad]["ogrenci"] += 1

        kademe_analizi = []
        for kademe_ad, val in sorted(kademe_toplamlar.items(), key=lambda x: int(re.search(r'\d+', x[0]).group()) if re.search(r'\d+', x[0]) else 999):
            sayi = max(1, val["ogrenci"])
            kademe_analizi.append({
                "kademe": kademe_ad,
                "ogrenci_sayisi": val["ogrenci"],
                "ortalama": round(val["toplam"] / sayi, 2),
                "ozursuz_ort": round(val["ozursuz"] / sayi, 2),
                "ozurlu_ort": round(val["ozurlu"] / sayi, 2),
                "toplam_gun": round(val["toplam"], 1)
            })

        # 3. Geç Kalma Alarmı (5G Kuralı - Dönüşüm Eşiğindeki Öğrenciler: 4, 9, 14, 19...)
        g_esik_ogrenciler = []
        toplam_g_sayisi = sum(ogrenci_g.values())
        donusen_toplam_gun = sum((v // 5) * 0.5 for v in ogrenci_g.values())
        for no_key, g_cnt in ogrenci_g.items():
            if g_cnt > 0 and (g_cnt % 5 == 4):
                g_esik_ogrenciler.append({
                    "no": no_key,
                    "ad": ogrenci_ad_map.get(no_key, no_key),
                    "sube": kisa_sube(ogrenci_sube_map.get(no_key, "")),
                    "g_sayisi": g_cnt,
                    "mevcut_ceza": round((g_cnt // 5) * 0.5, 1),
                    "sonraki_ceza": round(((g_cnt + 1) // 5) * 0.5, 1)
                })
        g_esik_ogrenciler.sort(key=lambda x: x["g_sayisi"], reverse=True)

        # 4. Şampiyon Şubeler (En Düşük Ortalama Devamsızlık Yapan İlk 3 Şube)
        sampiyon_subeler = sorted(
            [s for s in sube_ort_list if s.get("ogrenci_sayisi", 0) > 0],
            key=lambda x: x["ortalama"]
        )[:3]

        return {
            "kpis": {
                "ozursuz_10": kpi_ozursuz_10,
                "toplam_30": kpi_toplam_30,
                "sifir_hata": kpi_sifir,
                "toplam_evrak": kpi_evrak,
                "ramakkala_10_sayi": len(esik_kategorileri["ramakkala_10"]),
                "mektup_5_sayi": len(esik_kategorileri["mektup_siniri_5"])
            },
            "sube_dev": [{"sube": k, "toplam": v} for k, v in sube_toplam.items()],
            "sube_ortalamalar": sube_ort_list,
            "ozurlu_vs_ozursuz": {"ozurlu": ozurlu_genel, "ozursuz": ozursuz_genel},
            "tur_dev": [{"tur": k, "toplam": v} for k, v in tur_dev.items()],
            "aylik_trend": aylik_trend,
            "aylik_evrak": aylik_evrak_trend,
            "haftanin_gunleri": haftanin_gunleri,
            "riskli_ogrenciler": riskli_list,
            "g_turu_riskli": g_riskli_list,
            "kritik_esikler": esik_kategorileri,
            "risk_piramidi": risk_piramidi,
            "kademe_analizi": kademe_analizi,
            "gec_kalma_alarmi": {
                "esik_ogrenciler": g_esik_ogrenciler[:8],
                "toplam_g": toplam_g_sayisi,
                "donusen_gun": round(donusen_toplam_gun, 1),
                "esik_sayisi": len(g_esik_ogrenciler)
            },
            "sampiyon_subeler": sampiyon_subeler
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
