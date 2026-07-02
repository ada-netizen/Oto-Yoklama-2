# ================= api.py (FULL BACKEND) =================
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from veritabani import VeritabaniYoneticisi
from sistem_motoru import SistemMotoru
from excel_motoru import ExcelMotoru
from pdf_motoru import PDFYoneticisi
from araclar import VeriAraclari
import shutil
import os
import json
import PyPDF2
import re
from datetime import datetime, timedelta
import uuid
import pandas as pd

app = FastAPI(title="Oto-Yoklama API V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
db = VeritabaniYoneticisi(yollar["DB"])
ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])


def ayarlari_al():
    """Ayarları her seferinde diskten taze okur (ayar penceresi açıkken bile güncel kalsın diye)."""
    global ayarlar
    ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
    return ayarlar


def pdf_klasoru_hazirla():
    ayar = ayarlari_al()
    ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor):
        os.makedirs(ana_klasor)
    return ana_klasor, ayar


# =====================================================================
# 1. ÖĞRENCİ VE YOKLAMA İŞLEMLERİ
# =====================================================================
@app.get("/ogrenciler")
def ogrencileri_getir():
    ogrenci_listesi, devamsizlik_listesi = db.yukle()

    gruplu_devamsizlik = {}
    for dev in devamsizlik_listesi:
        no = str(dev['no']).strip()
        gruplu_devamsizlik.setdefault(no, []).append(dev)

    sonuclar = []
    for ogr in ogrenci_listesi:
        ogr_no = str(ogr['no']).strip()
        ogr_devleri = gruplu_devamsizlik.get(ogr_no, [])
        ozsz, ozrl = VeriAraclari.hesapla_devamsizlik(ogr_no, ogr_devleri, [])
        sonuclar.append({
            "no": ogr_no,
            "ad_soyad": ogr['ad_soyad'],
            "sube": ogr['sube'],
            "ozursuz": ozsz,
            "ozurlu": ozrl
        })
    return {"ogrenciler": sonuclar}


@app.get("/ogrenci-detay/{ogr_no}")
def ogrenci_detay_getir(ogr_no: str):
    _, devamsizlik_listesi = db.yukle()
    ogr_devleri = [d for d in devamsizlik_listesi if str(d['no']).strip() == str(ogr_no).strip()]
    return {"devamsizliklar": ogr_devleri}


@app.post("/ogrenci-excel-yukle")
async def ogrenci_excel_yukle(dosya: UploadFile = File(...)):
    temp_yol = f"temp_{dosya.filename}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, hata = ExcelMotoru.ogrenci_oku(temp_yol, mevcut_ogrenciler)
        if hata:
            return {"basarili": False, "mesaj": hata}
        if yeni_liste:
            mevcut_ogrenciler.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{len(yeni_liste)} yeni öğrenci eklendi!"}
        return {"basarili": False, "mesaj": "Dosyada yeni öğrenci bulunamadı."}
    finally:
        if os.path.exists(temp_yol):
            os.remove(temp_yol)


@app.post("/devamsizlik-excel-yukle")
async def devamsizlik_excel_yukle(dosya: UploadFile = File(...)):
    temp_yol = f"temp_dev_{dosya.filename}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, eklenen, hata = ExcelMotoru.devamsizlik_oku(temp_yol, mevcut_devamsizliklar)
        if hata:
            return {"basarili": False, "mesaj": hata}
        if eklenen > 0:
            mevcut_devamsizliklar.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{eklenen} yeni devamsızlık işlendi!"}
        return {"basarili": False, "mesaj": "Yeni devamsızlık bulunamadı."}
    finally:
        if os.path.exists(temp_yol):
            os.remove(temp_yol)


@app.delete("/ogrenci-sil/{ogr_no}")
def ogrenci_sil(ogr_no: str):
    ogrenciler, devler = db.yukle()
    yeni_ogr = [o for o in ogrenciler if str(o['no']).strip() != str(ogr_no).strip()]
    yeni_dev = [d for d in devler if str(d['no']).strip() != str(ogr_no).strip()]
    db.kaydet(yeni_ogr, yeni_dev)
    return {"basarili": True, "mesaj": f"{ogr_no} numaralı öğrenci ve devamsızlıkları silindi."}


@app.delete("/devamsizlik-sil/{d_id}")
def devamsizlik_sil(d_id: str):
    ogrenciler, devler = db.yukle()
    yeni_dev = [d for d in devler if str(d.get('id', '')) != str(d_id)]
    db.kaydet(ogrenciler, yeni_dev)
    return {"basarili": True, "mesaj": "Devamsızlık kaydı başarıyla silindi."}


@app.post("/devamsizlik-manuel-ekle")
def devamsizlik_manuel_ekle(veri: dict):
    ogrenciler, devler = db.yukle()
    yeni = {
        "id": str(uuid.uuid4().hex),
        "no": veri["no"],
        "tarih": veri["tarih"],
        "tur": veri["tur"],
        "gun": veri["gun"],
        "secili": False
    }
    devler.append(yeni)
    db.kaydet(ogrenciler, devler)
    return {"basarili": True, "mesaj": "Manuel devamsızlık eklendi."}


@app.post("/pdf-veli-formu")
def pdf_veli_formu_olustur(veri: dict):
    ana_klasor, ayar = pdf_klasoru_hazirla()
    sube_temiz = str(veri['sube']).replace("/", "-").replace("\\", "-").replace(":", "").strip()
    sube_klasoru = os.path.join(ana_klasor, sube_temiz)
    if not os.path.exists(sube_klasoru):
        os.makedirs(sube_klasoru)

    kayit_yeri = os.path.join(sube_klasoru, f"{veri['no']}_{veri['ad'].replace(' ', '_')}.pdf")
    try:
        # Ön yüzden gelen kayıtlarda ham 'tarih'/'gun' alanları var; PDF motoru
        # düzgün biçimlendirilmiş 'tarih_duzgun'/'gun_str' bekliyor. Burada dönüştürüyoruz.
        kayitlar_islenmis = []
        for k in veri['kayitlar']:
            k2 = dict(k)
            k2['tarih_duzgun'] = k.get('tarih_duzgun') or VeriAraclari.tarih_formatla(k.get('tarih', ''))
            k2['gun_str'] = k.get('gun_str') or VeriAraclari.temiz_sure(k.get('gun', ''))
            kayitlar_islenmis.append(k2)

        motor = PDFYoneticisi(ayar)
        motor.veli_formu_ciz(veri['no'], veri['ad'], veri['sube'], kayitlar_islenmis, kayit_yeri)
        return {"basarili": True, "mesaj": f"PDF Başarıyla Oluşturuldu!\nKonum: {kayit_yeri}", "yol": kayit_yeri}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


# =====================================================================
# 2. YAZI TEBLİĞİ VE PERSONEL İŞLEMLERİ
# =====================================================================
def _personel_grup_tahmin_et(gorev):
    g = str(gorev).upper()
    if "ÖĞRETMEN" in g:
        return "Öğretmenler"
    if g in ["OKUL MÜDÜRÜ", "MÜDÜR YARDIMCISI", "MÜDÜR BAŞYARDIMCISI", "VHKİ", "MEMUR"]:
        return "İdare"
    return "Diğer Personel"


@app.get("/personeller")
def personelleri_getir():
    try:
        db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
        personel_listesi = [{'ad': r[0], 'brans': r[1], 'gorev': r[2], 'grup': r[3]} for r in db.cursor.fetchall()]
        return {"personeller": personel_listesi}
    except:
        return {"personeller": []}


@app.post("/personel-excel-yukle")
async def personel_excel_yukle(dosya: UploadFile = File(...)):
    """E-Okul/MEB'den indirilen personel Excel listesini okuyup personel tablosunu tamamen günceller."""
    temp_yol = f"temp_personel_{dosya.filename}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        df_temp = pd.read_excel(temp_yol, header=None)
        header_idx = 0
        for i, row in df_temp.iterrows():
            satir_metni = " ".join([str(x).upper() for x in row.values if pd.notna(x)])
            if "AD" in satir_metni and "SOYAD" in satir_metni:
                header_idx = i
                break

        df = pd.read_excel(temp_yol, header=header_idx)
        df.columns = df.columns.str.strip().str.upper()

        ad_sutunu = 'AD SOYAD' if 'AD SOYAD' in df.columns else ('ADI SOYADI' if 'ADI SOYADI' in df.columns else None)
        if not ad_sutunu:
            return {"basarili": False, "mesaj": "Excel'de 'Ad Soyad' başlığı bulunamadı!"}

        yeni_personeller = []
        for _, row in df.iterrows():
            ad = str(row[ad_sutunu]).strip()
            gorev = "-"
            if 'GÖREVI' in df.columns: gorev = str(row['GÖREVI']).strip()
            elif 'GÖREVİ' in df.columns: gorev = str(row['GÖREVİ']).strip()

            brans = "-"
            if 'BRANŞI' in df.columns: brans = str(row['BRANŞI']).strip()
            elif 'BRANSI' in df.columns: brans = str(row['BRANSI']).strip()

            if not brans or brans.lower() == 'nan': brans = "-"
            if not gorev or gorev.lower() == 'nan': gorev = "-"

            if ad and ad.lower() != 'nan':
                grup = _personel_grup_tahmin_et(gorev)
                yeni_personeller.append((ad, brans, gorev, grup))

        db.cursor.execute("DELETE FROM personel")
        db.cursor.executemany("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", yeni_personeller)
        db.conn.commit()

        return {"basarili": True, "mesaj": f"{len(yeni_personeller)} personel yüklendi ve gruplandırıldı."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            os.remove(temp_yol)


@app.post("/personel-ekle")
def personel_ekle(veri: dict):
    ad = str(veri.get("ad", "")).strip().upper()
    if not ad:
        return {"basarili": False, "mesaj": "Ad Soyad boş bırakılamaz!"}
    gorev = str(veri.get("gorev", "")).strip().upper() or "-"
    brans = str(veri.get("brans", "")).strip().upper() or "-"
    grup = veri.get("grup") or _personel_grup_tahmin_et(gorev)

    db.cursor.execute("PRAGMA table_info(personel)")
    if 'grup' not in [col[1] for col in db.cursor.fetchall()]:
        db.cursor.execute("ALTER TABLE personel ADD COLUMN grup TEXT DEFAULT 'Diğer Personel'")

    db.cursor.execute("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", (ad, brans, gorev, grup))
    db.conn.commit()
    return {"basarili": True, "mesaj": f"{ad} eklendi."}


@app.delete("/personel-sil/{ad}")
def personel_sil(ad: str):
    db.cursor.execute("DELETE FROM personel WHERE ad_soyad = ?", (ad,))
    db.conn.commit()
    return {"basarili": True, "mesaj": f"{ad} silindi."}


@app.post("/meb-pdf-oku")
async def meb_pdf_oku(dosya: UploadFile = File(...)):
    temp_yol = f"temp_meb_{dosya.filename}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        with open(temp_yol, "rb") as file:
            ilk_sayfa = PyPDF2.PdfReader(file).pages[0].extract_text()

        tarih_match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', ilk_sayfa)
        tarih = tarih_match.group(0) if tarih_match else ""

        sayi_match = re.search(r'(E-\d+-\d+\.\d+-\d+)', ilk_sayfa)
        if not sayi_match:
            sayi_match = re.search(r'Sayı\s*[:\n]\s*([A-Za-z0-9\-.]+)', ilk_sayfa)
        sayi = sayi_match.group(1) if sayi_match else ""

        konu = ""
        konu_match = re.search(r'Konu\s*(?::|\n)(.*?)(?=\nİlgi|\nT\.C\.|\nDAĞITIM|\nOkul ve kurumlarda)', ilk_sayfa, re.DOTALL | re.IGNORECASE)
        if konu_match:
            konu_ham = konu_match.group(1).strip()
            konu = " ".join(konu_ham.split())
            if sayi and sayi in konu:
                konu = konu.replace(sayi, "").replace(":", "").strip()

        # Yüklenen orijinal yazıyı, bireysel tebliğde PDF'e eklenebilmesi için saklıyoruz
        ana_klasor, _ = pdf_klasoru_hazirla()
        gecici_klasor = os.path.join(ana_klasor, "_gecici_meb_yazilari")
        if not os.path.exists(gecici_klasor):
            os.makedirs(gecici_klasor)
        kalici_yol = os.path.join(gecici_klasor, f"son_meb_yazisi_{uuid.uuid4().hex[:8]}.pdf")
        shutil.copy(temp_yol, kalici_yol)

        return {"basarili": True, "sayi": sayi, "konu": konu, "tarih": tarih, "gecici_pdf_yolu": kalici_yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            os.remove(temp_yol)


@app.post("/teblig-bireysel-pdf")
def teblig_bireysel_pdf(veri: dict):
    ana_klasor, ayar = pdf_klasoru_hazirla()
    yol = os.path.join(ana_klasor, f"Bireysel_Teblig_{veri['edilen']['ad'].replace(' ', '_')}_{datetime.now().strftime('%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayar)
        yuklenen_pdf = veri.get("gecici_pdf_yolu")
        motor.bireysel_teblig_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['eden'], veri['edilen'], veri['yer'], yol, yuklenen_pdf)
        return {"basarili": True, "mesaj": f"PDF Oluşturuldu:\n{yol}", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@app.post("/teblig-toplu-pdf")
def teblig_toplu_pdf(veri: dict):
    ana_klasor, ayar = pdf_klasoru_hazirla()
    yol = os.path.join(ana_klasor, f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y_%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayar)
        motor.teblig_tebellug_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['personeller'], yol)
        return {"basarili": True, "mesaj": f"Toplu Liste Oluşturuldu:\n{yol}", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


# =====================================================================
# 3. RAPORLAR
# =====================================================================
def _rapor_verisi_hazirla(tur, ozel_deger):
    ogrenci_listesi, devamsizlik_listesi = db.yukle()
    gruplu = {}
    for dev in devamsizlik_listesi:
        no = str(dev['no']).strip()
        gruplu.setdefault(no, []).append(dev)

    hedef_tarih_obj = None
    if tur == "tarih_bazli":
        try:
            gg, aa, yy = map(int, str(ozel_deger).split('/'))
            hedef_tarih_obj = datetime(yy, aa, gg)
        except Exception:
            return None, "Tarih formatı hatalı! (GG/AA/YYYY olmalı)"

    veri = []
    for ogr in ogrenci_listesi:
        ogr_no = str(ogr['no']).strip()
        ogr_devleri = gruplu.get(ogr_no, [])
        ozsz, ozrl = VeriAraclari.hesapla_devamsizlik(ogr_no, ogr_devleri, [])
        gosterilen_sube = VeriAraclari.kisa_sube_adi(ogr['sube'])

        if tur == "ozursuz" and ozsz < 10: continue
        if tur == "ozurlu" and ozrl < 20: continue
        if tur == "gun_siniri" and ozsz < float(ozel_deger): continue
        if tur == "sube_bazli" and gosterilen_sube.replace(" ", "") != str(ozel_deger).replace(" ", ""): continue

        if tur == "tarih_bazli":
            bulundu = False
            dev_turu = ""
            for dev in ogr_devleri:
                if dev['tur'].upper() not in ["D", "ÖY", "SY"]:
                    continue
                try:
                    gun_mik = float(VeriAraclari.temiz_sure(dev['gun']))
                    tam_g = int(gun_mik) if gun_mik >= 1 else 1
                    bd, bm, by = map(int, VeriAraclari.tarih_formatla(dev['tarih']).split('/'))
                    bas_tarih = datetime(by, bm, bd)
                    for i in range(tam_g):
                        g_t = bas_tarih + timedelta(days=i)
                        if g_t.weekday() < 5 and g_t.date() == hedef_tarih_obj.date():
                            bulundu = True
                            dev_turu = dev['tur'].upper()
                            break
                    if bulundu:
                        break
                except Exception:
                    pass
            if not bulundu:
                continue
            veri.append([gosterilen_sube, ogr_no, ogr['ad_soyad'], dev_turu])
        else:
            veri.append([gosterilen_sube, ogr_no, ogr['ad_soyad'], ozsz])

    if tur == "tarih_bazli":
        def anahtar(x):
            r = re.findall(r'\d+', str(x[0]))
            return (int(r[0]) if r else 99, x[0], x[1])
        veri.sort(key=anahtar)
    else:
        veri.sort(key=lambda x: x[3], reverse=True)

    return veri, None


@app.post("/rapor-al")
def rapor_al(veri: dict):
    tur = veri.get("tur")
    format_tipi = veri.get("format")  # "excel" | "pdf"
    ozel_deger = veri.get("ozel_deger")

    basliklar = {
        "ozursuz": "Özürsüz Devamsızlık Sınırını Aşan Öğrenciler (10+ Gün)",
        "ozurlu": "Özürlü Devamsızlık Sınırını Aşan Öğrenciler (20+ Gün)",
        "gun_siniri": f"Özürsüz Devamsızlığı {ozel_deger} Gün ve Üstü Olan Öğrenciler",
        "sube_bazli": f"{ozel_deger} Şubesi Özürsüz Devamsızlık Listesi",
        "tarih_bazli": f"{ozel_deger} Tarihli Özürsüz Devamsızlık Listesi",
    }
    if tur not in basliklar:
        return {"basarili": False, "mesaj": "Geçersiz rapor türü."}

    veri_listesi, hata = _rapor_verisi_hazirla(tur, ozel_deger)
    if hata:
        return {"basarili": False, "mesaj": hata}
    if not veri_listesi:
        return {"basarili": False, "mesaj": "Bu kritere uygun öğrenci bulunamadı."}

    baslik = basliklar[tur]
    kolon4_adi = "Tür" if tur == "tarih_bazli" else "Özürsüz (Gün)"
    excel_kolonlar = ["Sınıf/Şube", "Numara", "Ad Soyad", "Devamsızlık Türü" if tur == "tarih_bazli" else "Özürsüz Toplam (Gün)"]

    ana_klasor, ayar = pdf_klasoru_hazirla()
    rapor_klasoru = os.path.join(ana_klasor, "Raporlar")
    if not os.path.exists(rapor_klasoru):
        os.makedirs(rapor_klasoru)

    dosya_adi_temiz = re.sub(r'[\\/*?:"<>|]', "", baslik).replace(" ", "_")
    bugun_str = datetime.now().strftime("%d_%m_%Y_%H%M")
    otomatik_isim = f"{dosya_adi_temiz}_{bugun_str}"

    try:
        if format_tipi == "excel":
            yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.xlsx")
            df = pd.DataFrame(veri_listesi, columns=excel_kolonlar)
            df.to_excel(yol, index=False)
        else:
            yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.pdf")
            motor = PDFYoneticisi(ayar)
            motor.rapor_ciz(baslik, kolon4_adi, veri_listesi, yol)
        return {"basarili": True, "mesaj": f"Rapor başarıyla oluşturuldu:\n{yol}", "yol": yol, "adet": len(veri_listesi)}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


# =====================================================================
# 4. AYARLAR, LOGO VE YEDEKLEME
# =====================================================================
@app.get("/ayarlar-getir")
def ayarlar_getir():
    return {"ayarlar": ayarlari_al(), "yollar": yollar}


@app.post("/ayarlar-kaydet")
def ayarlar_kaydet(yeni: dict):
    ayar = ayarlari_al()
    ayar.update(yeni)
    SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
    return {"basarili": True, "mesaj": "Ayarlar başarıyla kaydedildi."}


@app.post("/logo-yukle")
async def logo_yukle(tur: str = Form(...), dosya: UploadFile = File(...)):
    """tur: 'meb' veya 'okul'"""
    hedef_klasor = yollar["MEB_LOGO"] if tur == "meb" else yollar["OKUL_LOGO"]
    if not os.path.exists(hedef_klasor):
        os.makedirs(hedef_klasor)
    hedef_yol = os.path.join(hedef_klasor, dosya.filename)
    with open(hedef_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)

    ayar = ayarlari_al()
    anahtar = "meb_logosu" if tur == "meb" else "okul_logosu"
    ayar[anahtar] = hedef_yol
    SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
    return {"basarili": True, "mesaj": "Logo başarıyla yüklendi.", "yol": hedef_yol}


@app.post("/yedek-al")
def yedek_al():
    ayar = ayarlari_al()
    basarili, hata = SistemMotoru.yedek_al(yollar["DB"], ayar, yollar["YEDEK"])
    if basarili:
        ayar["son_yedekleme_gunu"] = datetime.now().strftime("%Y-%m-%d")
        SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
        return {"basarili": True, "mesaj": "Veritabanı başarıyla yedeklendi!"}
    return {"basarili": False, "mesaj": f"Yedekleme Hatası: {hata}"}


@app.get("/yedekler-listele")
def yedekler_listele():
    ayar = ayarlari_al()
    return {"yedekler": SistemMotoru.yedekleri_listele(ayar, yollar["YEDEK"])}


@app.post("/yedek-geri-yukle")
def yedek_geri_yukle(veri: dict):
    ayar = ayarlari_al()
    hedef_klasor = ayar.get("yedek_kayit_klasoru", yollar["YEDEK"])
    dosya_adi = veri.get("dosya", "")
    kaynak_yol = os.path.join(hedef_klasor, dosya_adi)
    if not os.path.exists(kaynak_yol):
        return {"basarili": False, "mesaj": "Seçilen yedek dosyası bulunamadı."}
    try:
        db.kapat()
        shutil.copy(kaynak_yol, yollar["DB"])
        db.baglan_ve_hazirla()
        return {"basarili": True, "mesaj": "Yedek başarıyla yüklendi. Sayfayı yenileyin."}
    except Exception as e:
        db.baglan_ve_hazirla()
        return {"basarili": False, "mesaj": f"Yedek yüklenirken hata oluştu: {e}"}


@app.delete("/veritabani-sifirla")
def veritabani_sifirla():
    db.sifirla()
    return {"basarili": True, "mesaj": "Tüm öğrenci, devamsızlık ve personel kayıtları SIFIRLANDI!"}
