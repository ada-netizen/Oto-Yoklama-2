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
from datetime import datetime
import uuid
from pdf_motoru import PDFYoneticisi
import PyPDF2
import re
from datetime import datetime

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

# --- 1. ÖĞRENCİ VE YOKLAMA İŞLEMLERİ ---
@app.get("/ogrenciler")
def ogrencileri_getir():
    ogrenci_listesi, devamsizlik_listesi = db.yukle()
    
    # Hızlı devamsızlık hesaplama (Önbellek mantığı)
    gruplu_devamsizlik = {}
    for dev in devamsizlik_listesi:
        no = str(dev['no']).strip()
        if no not in gruplu_devamsizlik: gruplu_devamsizlik[no] = []
        gruplu_devamsizlik[no].append(dev)

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
    with open(temp_yol, "wb") as buffer: shutil.copyfileobj(dosya.file, buffer)
    try:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, hata = ExcelMotoru.ogrenci_oku(temp_yol, mevcut_ogrenciler)
        if hata: return {"basarili": False, "mesaj": hata}
        if yeni_liste:
            mevcut_ogrenciler.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{len(yeni_liste)} yeni öğrenci eklendi!"}
        return {"basarili": False, "mesaj": "Dosyada yeni öğrenci bulunamadı."}
    finally:
        if os.path.exists(temp_yol): os.remove(temp_yol)

@app.post("/pdf-veli-formu")
async def pdf_veli_formu_olustur(veri: dict):
    # veri = {"no": "123", "ad": "Ali", "sube": "10/A", "kayitlar": [...]}
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor): os.makedirs(ana_klasor)
    
    sube_temiz = str(veri['sube']).replace("/", "-").replace("\\", "-").replace(":", "").strip()
    sube_klasoru = os.path.join(ana_klasor, sube_temiz)
    if not os.path.exists(sube_klasoru): os.makedirs(sube_klasoru)
    
    base_isim = f"{veri['no']}_{veri['ad'].replace(' ', '_')}"
    kayit_yeri = os.path.join(sube_klasoru, f"{base_isim}.pdf")
    
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.veli_formu_ciz(veri['no'], veri['ad'], veri['sube'], veri['kayitlar'], kayit_yeri)
        return {"basarili": True, "mesaj": f"PDF oluşturuldu: {kayit_yeri}", "yol": kayit_yeri}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

# --- 2. TEBLİĞ VE PERSONEL İŞLEMLERİ ---
@app.get("/personeller")
def personelleri_getir():
    try:
        db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
        personel_listesi = [{'ad': r[0], 'brans': r[1], 'gorev': r[2], 'grup': r[3]} for r in db.cursor.fetchall()]
        return {"personeller": personel_listesi}
    except:
        return {"personeller": []}

@app.post("/meb-pdf-oku")
async def meb_pdf_oku(dosya: UploadFile = File(...)):
    temp_yol = f"temp_meb_{dosya.filename}"
    with open(temp_yol, "wb") as buffer: shutil.copyfileobj(dosya.file, buffer)
    try:
        with open(temp_yol, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            ilk_sayfa = reader.pages[0].extract_text()

        tarih_match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', ilk_sayfa)
        tarih = tarih_match.group(0) if tarih_match else ""

        sayi_match = re.search(r'(E-\d+-\d+\.\d+-\d+)', ilk_sayfa)
        if not sayi_match: sayi_match = re.search(r'Sayı\s*[:\n]\s*([A-Za-z0-9\-.]+)', ilk_sayfa)
        sayi = sayi_match.group(1) if sayi_match else ""

        konu = ""
        konu_match = re.search(r'Konu\s*(?::|\n)(.*?)(?=\nİlgi|\nT\.C\.|\nDAĞITIM|\nOkul ve kurumlarda)', ilk_sayfa, re.DOTALL | re.IGNORECASE)
        if konu_match:
            konu_ham = konu_match.group(1).strip()
            konu = " ".join(konu_ham.split())
            if sayi and sayi in konu: konu = konu.replace(sayi, "").replace(":", "").strip()

        return {"basarili": True, "sayi": sayi, "konu": konu, "tarih": tarih}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol): os.remove(temp_yol)

@app.post("/teblig-toplu-pdf")
async def teblig_toplu_ciktisi_al(veri: dict):
    # veri = {"sayi": "...", "konu": "...", "tarih": "...", "personeller": [{"ad":"", "gorev":"", "brans":""}]}
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor): os.makedirs(ana_klasor)
    
    yol = os.path.join(ana_klasor, f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y_%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.teblig_tebellug_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['personeller'], yol)
        return {"basarili": True, "mesaj": "Toplu imza sirküsü oluşturuldu.", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    
    # ================= BUNDAN SONRASI api.py'NİN EN ALTINA EKLENECEKTİR =================

# --- 3. DEVAMSIZLIK YÜKLEME VE ÖĞRENCİ SİLME ---
@app.post("/devamsizlik-excel-yukle")
async def devamsizlik_excel_yukle(dosya: UploadFile = File(...)):
    temp_yol = f"temp_dev_{dosya.filename}"
    with open(temp_yol, "wb") as buffer: shutil.copyfileobj(dosya.file, buffer)
    try:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, eklenen, hata = ExcelMotoru.devamsizlik_oku(temp_yol, mevcut_devamsizliklar)
        if hata: return {"basarili": False, "mesaj": hata}
        if eklenen > 0:
            mevcut_devamsizliklar.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{eklenen} yeni devamsızlık işlendi!"}
        return {"basarili": False, "mesaj": "Yeni devamsızlık bulunamadı."}
    finally:
        if os.path.exists(temp_yol): os.remove(temp_yol)

@app.delete("/ogrenci-sil/{ogr_no}")
def ogrenci_sil(ogr_no: str):
    ogrenciler, devler = db.yukle()
    yeni_ogr = [o for o in ogrenciler if str(o['no']).strip() != str(ogr_no).strip()]
    yeni_dev = [d for d in devler if str(d['no']).strip() != str(ogr_no).strip()]
    db.kaydet(yeni_ogr, yeni_dev)
    return {"basarili": True, "mesaj": f"{ogr_no} numaralı öğrenci ve devamsızlıkları silindi."}

# --- 4. BİREYSEL TEBLİĞ MOTORU ---
@app.post("/teblig-bireysel-pdf")
def teblig_bireysel_pdf(veri: dict):
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor): os.makedirs(ana_klasor)
    
    yol = os.path.join(ana_klasor, f"Bireysel_Teblig_{veri['edilen']['ad'].replace(' ', '_')}_{datetime.now().strftime('%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.bireysel_teblig_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['eden'], veri['edilen'], veri['yer'], yol)
        return {"basarili": True, "mesaj": "Bireysel tebliğ oluşturuldu.", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

# --- 5. YEDEKLEME VE AYARLAR ---
@app.post("/yedek-al")
def yedek_al():
    basarili, hata = SistemMotoru.yedek_al(yollar["DB"], ayarlar, yollar["YEDEK"])
    if basarili: return {"basarili": True, "mesaj": "Veritabanı başarıyla yedeklendi!"}
    else: return {"basarili": False, "mesaj": hata}

# --- MANUEL EKLEME, SİLME VE PDF MOTORLARI ---

@app.delete("/devamsizlik-sil/{d_id}")
def devamsizlik_sil(d_id: str):
    ogrenciler, devler = db.yukle()
    # Gelen ID'ye sahip OLMAYANLARI tut (Yani seçileni sil)
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
    ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    
    # Sube klasörü oluştur
    import os
    sube_temiz = str(veri['sube']).replace("/", "-").replace("\\", "-").strip()
    sube_klasoru = os.path.join(ana_klasor, sube_temiz)
    if not os.path.exists(sube_klasoru): os.makedirs(sube_klasoru)
    
    kayit_yeri = os.path.join(sube_klasoru, f"{veri['no']}_{veri['ad'].replace(' ', '_')}.pdf")
    
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.veli_formu_ciz(veri['no'], veri['ad'], veri['sube'], veri['kayitlar'], kayit_yeri)
        return {"basarili": True, "mesaj": f"PDF Başarıyla Oluşturuldu!\nKonum: {kayit_yeri}"}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    
# ================= 2. SEKME: YAZI TEBLİĞİ VE PERSONEL MOTORLARI =================

@app.get("/personeller")
def personelleri_getir():
    try:
        db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
        personel_listesi = [{'ad': r[0], 'brans': r[1], 'gorev': r[2], 'grup': r[3]} for r in db.cursor.fetchall()]
        return {"personeller": personel_listesi}
    except:
        return {"personeller": []}

@app.post("/meb-pdf-oku")
async def meb_pdf_oku(dosya: UploadFile = File(...)):
    temp_yol = f"temp_meb_{dosya.filename}"
    with open(temp_yol, "wb") as buffer: shutil.copyfileobj(dosya.file, buffer)
    try:
        with open(temp_yol, "rb") as file:
            ilk_sayfa = PyPDF2.PdfReader(file).pages[0].extract_text()
        
        # Mükemmel Tkinter Regex zırhın (Tarih, Sayı, Konu ayıklama)
        tarih = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', ilk_sayfa)
        tarih = tarih.group(0) if tarih else ""
        
        sayi_match = re.search(r'(E-\d+-\d+\.\d+-\d+)', ilk_sayfa)
        sayi = sayi_match.group(1) if sayi_match else (re.search(r'Sayı\s*[:\n]\s*([A-Za-z0-9\-.]+)', ilk_sayfa).group(1) if re.search(r'Sayı\s*[:\n]\s*([A-Za-z0-9\-.]+)', ilk_sayfa) else "")
        
        konu_match = re.search(r'Konu\s*(?::|\n)(.*?)(?=\nİlgi|\nT\.C\.|\nDAĞITIM|\nOkul ve kurumlarda)', ilk_sayfa, re.DOTALL | re.IGNORECASE)
        konu = " ".join(konu_match.group(1).strip().split()) if konu_match else ""
        if sayi and sayi in konu: konu = konu.replace(sayi, "").replace(":", "").strip()
        
        return {"basarili": True, "sayi": sayi, "konu": konu, "tarih": tarih}
    except Exception as e: return {"basarili": False, "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol): os.remove(temp_yol)

@app.post("/teblig-bireysel-pdf")
def teblig_bireysel_pdf(veri: dict):
    ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor): os.makedirs(ana_klasor)
    
    yol = os.path.join(ana_klasor, f"Bireysel_Teblig_{veri['edilen']['ad'].replace(' ', '_')}_{datetime.now().strftime('%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.bireysel_teblig_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['eden'], veri['edilen'], veri['yer'], yol)
        return {"basarili": True, "mesaj": f"PDF Oluşturuldu:\n{yol}"}
    except Exception as e: return {"basarili": False, "mesaj": str(e)}

@app.post("/teblig-toplu-pdf")
def teblig_toplu_pdf(veri: dict):
    ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
    ana_klasor = ayarlar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor): os.makedirs(ana_klasor)
    
    yol = os.path.join(ana_klasor, f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y_%H%M')}.pdf")
    try:
        motor = PDFYoneticisi(ayarlar)
        motor.teblig_tebellug_ciz(veri['sayi'], veri['konu'], veri['tarih'], veri['personeller'], yol)
        return {"basarili": True, "mesaj": f"Toplu Liste Oluşturuldu:\n{yol}"}
    except Exception as e: return {"basarili": False, "mesaj": str(e)}

# ================= 3. SEKME: AYARLAR VE YEDEKLEME MOTORLARI =================

@app.get("/ayarlar-getir")
def ayarlar_getir():
    # SistemMotoru'ndaki yolları ve ayarları arayüze gönderir
    return {"ayarlar": ayarlar, "yollar": yollar}

@app.post("/ayarlar-kaydet")
def ayarlar_kaydet(yeni: dict):
    ayarlar.update(yeni)
    SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayarlar)
    return {"basarili": True, "mesaj": "Ayarlar başarıyla kaydedildi."}

@app.post("/yedek-al")
def yedek_al():
    # Sizin SistemMotoru.py içindeki kusursuz yedekleme fonksiyonunuzu tetikler
    basarili, hata = SistemMotoru.yedek_al(yollar["DB"], ayarlar, yollar["YEDEK"])
    return {"basarili": basarili, "mesaj": "Veritabanı başarıyla yedeklendi!" if basarili else f"Yedekleme Hatası: {hata}"}

@app.delete("/veritabani-sifirla")
def veritabani_sifirla():
    # Yeni eğitim öğretim yılı için sistemi fabrika ayarlarına döndürür
    db.sifirla()
    return {"basarili": True, "mesaj": "Tüm öğrenci, devamsızlık ve personel kayıtları SIFIRLANDI!"}