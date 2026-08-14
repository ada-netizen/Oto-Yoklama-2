# ================= api.py (FULL BACKEND) =================
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from veritabani import VeritabaniYoneticisi
from sistem_motoru import SistemMotoru
from excel_motoru import ExcelMotoru
from pdf_motoru import PDFYoneticisi
from araclar import VeriAraclari
import ihale_motoru
import shutil
import os
import json
import PyPDF2
import re
from datetime import datetime, timedelta
import uuid
import pandas as pd
import threading
import time
import platform
import subprocess
import logging
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

logging.basicConfig(filename='app.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

def dosyayi_otomatik_ac(dosya_yolu):
    """Oluşturulan PDF veya Excel dosyasını bilgisayarın varsayılan programıyla anında açar"""
    try:
        if platform.system() == 'Windows':
            os.startfile(dosya_yolu)
        elif platform.system() == 'Darwin':
            subprocess.call(('open', dosya_yolu))
        else:
            subprocess.call(('xdg-open', dosya_yolu))
    except Exception as e:
        logging.error(f"dosyayi_otomatik_ac hatasi: {e}")
        pass

app = FastAPI(title="Elektronik Okul API V2")

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


# =====================================================================
# PYDANTIC MODELLERİ (VERİ DOĞRULAMA VE GÜVENLİK)
# =====================================================================
class DevamsizlikEkleRequest(BaseModel):
    no: str
    tarih: str
    tur: str
    gun: str

class KayitModel(BaseModel):
    tarih: Optional[str] = None
    gun: Optional[str] = None
    tarih_duzgun: Optional[str] = None
    gun_str: Optional[str] = None
    tur: str
    
    class Config:
        extra = "allow"

class PdfVeliFormuRequest(BaseModel):
    no: str
    ad: str
    sube: str
    kayitlar: List[KayitModel]

class PersonelRequest(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = None

class PersonelModel(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    
class TebligBireyselRequest(BaseModel):
    kurum: Optional[str] = ""
    sayi: str
    konu: str
    tarih: str
    eden: PersonelModel
    edilen: PersonelModel
    yer: str
    teblig_tarihi: Optional[str] = None
    gecici_pdf_yolu: Optional[str] = None

class TebligTopluRequest(BaseModel):
    kurum: Optional[str] = ""
    sayi: str
    konu: str
    tarih: str
    personeller: List[PersonelModel]
    gecici_pdf_yolu: Optional[str] = None

class RaporAlRequest(BaseModel):
    tur: str
    format: str
    ozel_deger: Optional[str] = None
from contextlib import contextmanager

@contextmanager
def gecici_dosya_olustur(dosya: UploadFile, prefix="temp_"):
    temp_yol = f"{prefix}{dosya.filename}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    try:
        yield temp_yol
    finally:
        if os.path.exists(temp_yol):
            os.remove(temp_yol)


_son_ayarlar_mtime = 0

def ayarlari_al():
    """Ayarları sadece dosya degistiginde okur (Cache)."""
    global ayarlar, _son_ayarlar_mtime
    try:
        mtime = os.path.getmtime(yollar["AYARLAR"])
    except OSError:
        mtime = 0
        
    if mtime != _son_ayarlar_mtime or _son_ayarlar_mtime == 0:
        ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
        _son_ayarlar_mtime = mtime
    return ayarlar


def pdf_klasoru_hazirla():
    ayar = ayarlari_al()
    ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    if not os.path.exists(ana_klasor):
        os.makedirs(ana_klasor)
    return ana_klasor, ayar


# =====================================================================
# OTOMATİK ZAMANLI YEDEKLEME (arka planda sürekli çalışan iş parçacığı)
# Tkinter sürümündeki zamanlanmis_yedek_kontrolu ile birebir aynı mantık.
# =====================================================================
def _zamanlanmis_yedek_dongusu():
    while True:
        try:
            ayar = ayarlari_al()
            su_an = datetime.now()
            saat_str = su_an.strftime("%H:%M")
            bugun_str = su_an.strftime("%Y-%m-%d")

            ayar_saat = ayar.get("yedek_saati", "17:00")
            if len(ayar_saat) == 4 and ":" in ayar_saat:
                ayar_saat = "0" + ayar_saat  # "9:00" -> "09:00"

            if saat_str == ayar_saat:
                son_yedek = ayar.get("son_yedekleme_gunu", "")
                if son_yedek != bugun_str:
                    siklik = ayar.get("yedek_sikligi", "Her Gün")
                    yedekle = False
                    if not son_yedek:
                        yedekle = True
                    else:
                        try:
                            son_tarih = datetime.strptime(son_yedek, "%Y-%m-%d")
                            fark_gun = (su_an - son_tarih).days
                            if siklik == "Her Gün" and fark_gun >= 1: yedekle = True
                            elif siklik == "Özel Gün" and fark_gun >= int(ayar.get("yedek_gun_sayisi", 3)): yedekle = True
                            elif siklik == "Haftada 1" and fark_gun >= 7: yedekle = True
                            elif siklik == "Ayda 1" and fark_gun >= 30: yedekle = True
                        except Exception as e:
                            logging.error(f"Zamanlanmis yedek kontrol hatasi: {e}")
                            pass

                    if yedekle:
                        basarili, _ = SistemMotoru.yedek_al(yollar["DB"], ayar, yollar["YEDEK"])
                        if basarili:
                            ayar["son_yedekleme_gunu"] = bugun_str
                            SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
        except Exception as e:
            logging.error(f"_zamanlanmis_yedek_dongusu hatasi: {e}")
            pass
        time.sleep(60)  # Saati her 60 saniyede bir kontrol eder


threading.Thread(target=_zamanlanmis_yedek_dongusu, daemon=True).start()


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

    with gecici_dosya_olustur(dosya, prefix='temp_') as temp_yol:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, hata = ExcelMotoru.ogrenci_oku(temp_yol, mevcut_ogrenciler)
        if hata:
            return {"basarili": False, "mesaj": hata}
        if yeni_liste:
            mevcut_ogrenciler.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{len(yeni_liste)} yeni öğrenci eklendi!"}
        return {"basarili": False, "mesaj": "Dosyada yeni öğrenci bulunamadı."}


@app.post("/devamsizlik-excel-yukle")
async def devamsizlik_excel_yukle(dosya: UploadFile = File(...)):

    with gecici_dosya_olustur(dosya, prefix='temp_dev_') as temp_yol:
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        yeni_liste, eklenen, hata = ExcelMotoru.devamsizlik_oku(temp_yol, mevcut_devamsizliklar)
        if hata:
            return {"basarili": False, "mesaj": hata}
        if eklenen > 0:
            mevcut_devamsizliklar.extend(yeni_liste)
            db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            return {"basarili": True, "mesaj": f"{eklenen} yeni devamsızlık işlendi!"}
        return {"basarili": False, "mesaj": "Yeni devamsızlık bulunamadı."}


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
def devamsizlik_manuel_ekle(veri: DevamsizlikEkleRequest):
    ogrenciler, devler = db.yukle()
    yeni = {
        "id": str(uuid.uuid4().hex),
        "no": veri.no,
        "tarih": veri.tarih,
        "tur": veri.tur,
        "gun": veri.gun,
        "secili": False
    }
    devler.append(yeni)
    db.kaydet(ogrenciler, devler)
    return {"basarili": True, "mesaj": "Manuel devamsızlık eklendi."}


@app.post("/pdf-veli-formu")
def pdf_veli_formu_olustur(veri: PdfVeliFormuRequest, background_tasks: BackgroundTasks):
    ana_klasor, ayar = pdf_klasoru_hazirla()
    sube_temiz = str(veri.sube).replace("/", "-").replace("\\", "-").replace(":", "").strip()
    sube_klasoru = os.path.join(ana_klasor, sube_temiz)
    if not os.path.exists(sube_klasoru):
        os.makedirs(sube_klasoru)

    kayit_yeri = os.path.join(sube_klasoru, f"{veri.no}_{veri.ad.replace(' ', '_')}.pdf")
    try:
        # Ön yüzden gelen kayıtlarda ham 'tarih'/'gun' alanları var; PDF motoru
        # düzgün biçimlendirilmiş 'tarih_duzgun'/'gun_str' bekliyor. Burada dönüştürüyoruz.
        kayitlar_islenmis = []
        for k in veri.kayitlar:
            k2 = k.model_dump()
            k2['tarih_duzgun'] = k.tarih_duzgun or VeriAraclari.tarih_formatla(k.tarih or '')
            k2['gun_str'] = k.gun_str or VeriAraclari.temiz_sure(k.gun or '')
            kayitlar_islenmis.append(k2)

        def gorev_pdf_olustur():
            try:
                motor = PDFYoneticisi(ayar)
                motor.veli_formu_ciz(veri.no, veri.ad, veri.sube, kayitlar_islenmis, kayit_yeri)
                dosyayi_otomatik_ac(kayit_yeri)
            except Exception as e:
                logging.error(f"Veli formu cizim hatasi: {e}")

        background_tasks.add_task(gorev_pdf_olustur)
        return {"basarili": True, "mesaj": f"PDF işlemi arka plana alındı. Hazırlandığında otomatik açılacaktır.", "yol": kayit_yeri}
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
    except Exception as e:
        logging.error(f"personelleri_getir hatasi: {e}")
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
def personel_ekle(veri: PersonelRequest):
    ad = str(veri.ad).strip().upper()
    if not ad:
        return {"basarili": False, "mesaj": "Ad Soyad boş bırakılamaz!"}
    gorev = str(veri.gorev).strip().upper() or "-"
    brans = str(veri.brans).strip().upper() or "-"
    grup = veri.grup or _personel_grup_tahmin_et(gorev)

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
    
    # Eşleşmeleri sil (ad silindiği için eski eşleşmeleri de temizlemek iyi olabilir, ama şimdilik bırakıyoruz)
    return {"basarili": True, "mesaj": f"{ad} silindi."}

@app.put("/personel-guncelle/{eski_ad}")
def personel_guncelle(eski_ad: str, veri: PersonelRequest):
    yeni_ad = str(veri.ad).strip().upper()
    if not yeni_ad:
        return {"basarili": False, "mesaj": "Ad Soyad boş bırakılamaz!"}
    gorev = str(veri.gorev).strip().upper() or "-"
    brans = str(veri.brans).strip().upper() or "-"
    grup = veri.grup or _personel_grup_tahmin_et(gorev)

    db.cursor.execute("UPDATE personel SET ad_soyad=?, brans=?, gorev=?, grup=? WHERE ad_soyad=?", (yeni_ad, brans, gorev, grup, eski_ad))
    db.conn.commit()
    
    # Oto-eşleşmeleri güncelle
    ayar = ayarlari_al()
    eslesmeler = ayar.get("oto_eslesmeler", [])
    degisiklik_var = False
    for eslesme in eslesmeler:
        if eslesme.get("hedef") == eski_ad:
            eslesme["hedef"] = yeni_ad
            degisiklik_var = True
    
    if degisiklik_var:
        ayar["oto_eslesmeler"] = eslesmeler
        SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
        
    return {"basarili": True, "mesaj": f"Personel güncellendi."}

@app.get("/personel-excel-indir")
def personel_excel_indir():
    db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel ORDER BY ad_soyad")
    personel_listesi = [{'Ad Soyad': r[0], 'Branş': r[1], 'Görev': r[2], 'Grup': r[3]} for r in db.cursor.fetchall()]
    
    if not personel_listesi:
        return {"basarili": False, "mesaj": "Personel listesi boş!"}
        
    df = pd.DataFrame(personel_listesi)
    ana_klasor, ayar = pdf_klasoru_hazirla()
    yol = os.path.join(ana_klasor, "Personel_Listesi.xlsx")
    df.to_excel(yol, index=False)
    os.startfile(yol)
    return {"basarili": True, "mesaj": "Excel dosyası oluşturuldu."}

@app.get("/personel-pdf-indir")
def personel_pdf_indir():
    db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel ORDER BY ad_soyad")
    veri = [[r[0], r[1], r[2], r[3]] for r in db.cursor.fetchall()]
    
    if not veri:
        return {"basarili": False, "mesaj": "Personel listesi boş!"}
        
    ana_klasor, ayar = pdf_klasoru_hazirla()
    yol = os.path.join(ana_klasor, "Personel_Listesi.pdf")
    motor = PDFYoneticisi(ayar)
    
    # Yeni eklenecek PDF methodu: personel_raporu_ciz
    motor.personel_raporu_ciz(veri, yol)
    
    os.startfile(yol)
    return {"basarili": True, "mesaj": "PDF oluşturuldu."}



@app.post("/meb-pdf-oku")
async def meb_pdf_oku(dosya: UploadFile = File(...)):

    try:
        with gecici_dosya_olustur(dosya, prefix='temp_meb_') as temp_yol:
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
                
                # Konu ile İlgi arasında kalan hedef makam adını ayıklama
                lines = konu_ham.split('\n')
                temiz_lines = []
                for line in lines:
                    line_str = line.strip()
                    if not line_str: continue
                    
                    # Kurum hitap kelimelerinden birini içeriyorsa veya satır tamamen büyük harfliyse (min 15 karakter) dur!
                    if re.search(r'(?:MÜDÜRLÜĞÜNE|LİSESİNE|KAYMAKAMLIĞINA|VALİLİĞİNE|BAKANLIĞINA|OKULUNA|MERKEZİNE|BAŞKANLIĞINA|MÜDÜRLÜĞÜ|LİSESİ)\b', line_str, re.IGNORECASE):
                        break
                    if len(line_str) > 15 and line_str.isupper():
                        break
                        
                    temiz_lines.append(line_str)
                
                konu = " ".join(temiz_lines)
                if sayi and sayi in konu:
                    konu = konu.replace(sayi, "").replace(":", "").strip()

            # --- ZEKİ KURUM (GELDİĞİ YER) OKUYUCU ---
            kurum = ""
            tc_match = re.search(r'T\.\s*C\.\s*\r?\n((?:.*\r?\n){1,4})', ilk_sayfa)
            if tc_match:
                satirlar = [s.strip() for s in tc_match.group(1).split('\n') if s.strip()]
                if len(satirlar) >= 2:
                    kurum = satirlar[1]   # T.C.'den sonraki 2. dolu satır = kurumun asıl adı
                elif satirlar:
                    kurum = satirlar[0]

            ana_klasor, _ = pdf_klasoru_hazirla()
            gecici_klasor = os.path.join(ana_klasor, "_gecici_meb_yazilari")
            if not os.path.exists(gecici_klasor):
                os.makedirs(gecici_klasor)
            kalici_yol = os.path.join(gecici_klasor, f"son_meb_yazisi_{uuid.uuid4().hex[:8]}.pdf")
            shutil.copy(temp_yol, kalici_yol)

            return {"basarili": True, "sayi": sayi, "konu": konu, "tarih": tarih, "kurum": kurum, "gecici_pdf_yolu": kalici_yol}

    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@app.post("/teblig-bireysel-pdf")
def teblig_bireysel_pdf(veri: TebligBireyselRequest, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    yedek_klasoru = ayar.get("yedek_kayit_klasoru", yollar["YEDEK"])
    
    # Yeni klasör yapısını oluştur
    teblig_klasoru = os.path.join(yedek_klasoru, "Tebliğler", "Bireysel Tebliğ-Tebellüğ")
    os.makedirs(teblig_klasoru, exist_ok=True)
    
    yol = os.path.join(teblig_klasoru, f"Bireysel_Teblig_{veri.edilen.ad.replace(' ', '_')}_{datetime.now().strftime('%H%M')}.pdf")
    try:
        yuklenen_pdf = veri.gecici_pdf_yolu
        
        def gorev_bireysel_teblig():
            try:
                motor = PDFYoneticisi(ayar)
                motor.bireysel_teblig_ciz(veri.kurum, veri.sayi, veri.konu, veri.tarih, veri.eden.model_dump(), veri.edilen.model_dump(), veri.yer, veri.teblig_tarihi, yol, yuklenen_pdf)
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Bireysel teblig cizim hatasi: {e}")

        background_tasks.add_task(gorev_bireysel_teblig)
        return {"basarili": True, "mesaj": f"Tebliğ PDF işlemi arka plana alındı, açılacaktır.", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@app.post("/teblig-toplu-pdf")
def teblig_toplu_pdf(veri: TebligTopluRequest, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    yedek_klasoru = ayar.get("yedek_kayit_klasoru", yollar["YEDEK"])
    
    # Yeni klasör yapısını oluştur
    teblig_klasoru = os.path.join(yedek_klasoru, "Tebliğler", "Toplu İmza Sirküsü")
    os.makedirs(teblig_klasoru, exist_ok=True)
    
    yol = os.path.join(teblig_klasoru, f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y_%H%M')}.pdf")
    try:
        kurum = veri.kurum
        yuklenen_pdf = veri.gecici_pdf_yolu
        personeller_dict = [p.model_dump() for p in veri.personeller]
        
        def gorev_toplu_teblig():
            try:
                motor = PDFYoneticisi(ayar)
                motor.teblig_tebellug_ciz(veri.sayi, veri.konu, veri.tarih, personeller_dict, yol, kurum, yuklenen_pdf)
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Toplu teblig cizim hatasi: {e}")

        background_tasks.add_task(gorev_toplu_teblig)
        return {"basarili": True, "mesaj": f"Toplu Liste işlemi arka plana alındı, açılacaktır.", "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": f"PDF Hatası: {str(e)}"}



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
        except Exception as e:
            logging.error(f"_rapor_verisi_hazirla tarih formati hatasi: {e}")
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
                except Exception as e:
                    logging.error(f"_rapor_verisi_hazirla dongu hatasi: {e}")
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


@app.get("/rapor-esik-siniflar/{format_tipi}")
def rapor_esik_siniflar(format_tipi: str, background_tasks: BackgroundTasks):
    try:
        # Tüm öğrencileri al
        db.cursor.execute("SELECT no, ad_soyad, sube FROM ogrenciler")
        ogrenciler = [{'no': r[0], 'ad_soyad': r[1], 'sube': r[2]} for r in db.cursor.fetchall()]
        
        # Tüm devamsızlıkları al (hafta sonu mantığıyla günleri toplama)
        db.cursor.execute("SELECT no, tur, gun FROM devamsizliklar")
        dev_kayitlar = db.cursor.fetchall()
        
        # Öğrenci başına devamsızlık toplamı
        dev_toplamlari = {o['no']: 0.0 for o in ogrenciler}
        
        # Tur: Özürsüz -> D, Y, SY
        # Tur: Özürlü -> G, I, S, R, M
        # Tur: Diğer -> N, F, SV (bunları saymıyoruz)
        sayilmayacak_turler = ['N', 'F', 'SV']
        
        for no, tur, gun in dev_kayitlar:
            if not tur or tur.upper() in sayilmayacak_turler:
                continue
            
            try:
                gun_mik = float(gun)
            except:
                gun_mik = 0.0
            
            if no in dev_toplamlari:
                dev_toplamlari[no] += gun_mik
                
        # Sınıflara göre grupla
        sinif_verileri = {}
        for ogr in ogrenciler:
            sube = ogr['sube']
            no = ogr['no']
            toplam = dev_toplamlari[no]
            
            if toplam < 5:
                continue 
                
            if sube not in sinif_verileri:
                sinif_verileri[sube] = {'5-14': 0, '15-24': 0, '25-39': 0, '40+': 0}
                
            if 5 <= toplam <= 14.5:
                sinif_verileri[sube]['5-14'] += 1
            elif 15 <= toplam <= 24.5:
                sinif_verileri[sube]['15-24'] += 1
            elif 25 <= toplam <= 39.5:
                sinif_verileri[sube]['25-39'] += 1
            elif toplam >= 40:
                sinif_verileri[sube]['40+'] += 1

        def sinif_sirala(sube_adi):
            import re
            m = re.match(r'(\d+)', sube_adi)
            num = int(m.group(1)) if m else 99
            return (num, sube_adi)
            
        sirali_subeler = sorted(sinif_verileri.keys(), key=sinif_sirala)
        
        import re
        veri_listesi = []
        
        mevcut_kademe = None
        kademe_toplamlari = [0, 0, 0, 0]
        genel_toplamlar = [0, 0, 0, 0]
        
        for sube in sirali_subeler:
            m = re.match(r'(\d+)', sube)
            kademe = int(m.group(1)) if m else 99
            
            if mevcut_kademe is not None and kademe != mevcut_kademe:
                veri_listesi.append([f"{mevcut_kademe}. Sınıflar Toplamı", kademe_toplamlari[0], kademe_toplamlari[1], kademe_toplamlari[2], kademe_toplamlari[3]])
                kademe_toplamlari = [0, 0, 0, 0]
                
            mevcut_kademe = kademe
            v = sinif_verileri[sube]
            veri_listesi.append([sube, v['5-14'], v['15-24'], v['25-39'], v['40+']])
            
            kademe_toplamlari[0] += v['5-14']
            kademe_toplamlari[1] += v['15-24']
            kademe_toplamlari[2] += v['25-39']
            kademe_toplamlari[3] += v['40+']
            
            genel_toplamlar[0] += v['5-14']
            genel_toplamlar[1] += v['15-24']
            genel_toplamlar[2] += v['25-39']
            genel_toplamlar[3] += v['40+']

        if mevcut_kademe is not None:
            veri_listesi.append([f"{mevcut_kademe}. Sınıflar Toplamı", kademe_toplamlari[0], kademe_toplamlari[1], kademe_toplamlari[2], kademe_toplamlari[3]])
            
        veri_listesi.append(["GENEL TOPLAM", genel_toplamlar[0], genel_toplamlar[1], genel_toplamlar[2], genel_toplamlar[3]])

        if not veri_listesi:
            return {"basarili": False, "mesaj": "Bu kritere uygun öğrenci bulunamadı."}

        ana_klasor, ayar = pdf_klasoru_hazirla()
        rapor_klasoru = os.path.join(ana_klasor, "Raporlar")
        if not os.path.exists(rapor_klasoru):
            os.makedirs(rapor_klasoru)

        baslik = "Sınıf Bazlı Devamsızlık Eşik Raporu"
        dosya_adi_temiz = "Sinif_Bazli_Esik_Raporu"
        bugun_str = datetime.now().strftime("%d_%m_%Y_%H%M")
        otomatik_isim = f"{dosya_adi_temiz}_{bugun_str}"
        
        def gorev_esik_raporu():
            try:
                if format_tipi == "excel":
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.xlsx")
                    motor = ExcelMotoru()
                    motor.esik_raporu_excel_ciz(veri_listesi, yol)
                else:
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.pdf")
                    motor = PDFYoneticisi(ayar)
                    motor.esik_raporu_pdf_ciz(veri_listesi, yol)
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Esik raporu cizim hatasi: {e}")

        background_tasks.add_task(gorev_esik_raporu)
        return {"basarili": True, "mesaj": f"Rapor arka planda oluşturuluyor...", "yol": "Raporlar"}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@app.post("/rapor-al")
def rapor_al(veri: RaporAlRequest, background_tasks: BackgroundTasks):
    tur = veri.tur
    format_tipi = veri.format  # "excel" | "pdf"
    ozel_deger = veri.ozel_deger

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
        def gorev_rapor():
            try:
                if format_tipi == "excel":
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.xlsx")
                    df = pd.DataFrame(veri_listesi, columns=excel_kolonlar)
                    df.to_excel(yol, index=False)
                else:
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.pdf")
                    motor = PDFYoneticisi(ayar)
                    motor.rapor_ciz(baslik, kolon4_adi, veri_listesi, yol)
                        
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Rapor cizim hatasi: {e}")

        background_tasks.add_task(gorev_rapor)
        return {"basarili": True, "mesaj": f"Rapor arka planda oluşturuluyor...", "yol": "Raporlar", "adet": len(veri_listesi)}
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


def safe_float(val, default=0.0):
    if pd.isna(val):
        return default
    try:
        s = str(val).replace('₺', '').replace('$', '').strip()
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        elif ',' in s and '.' in s:
            s = s.replace(',', '')
        return float(s)
    except:
        return default

@app.post("/ihale-excel-oku")
async def ihale_excel_oku(dosya: UploadFile = File(...)):
    try:
        temp_path = os.path.join(yollar["TEMP"], f"ihale_{uuid.uuid4().hex}.xls")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(dosya.file, f)
        
        xl = pd.ExcelFile(temp_path)
        sheet_name = xl.sheet_names[1] if len(xl.sheet_names) > 1 else xl.sheet_names[0]
        
        df = xl.parse(sheet_name)
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        kalemler = []
        sira = 1
        for idx, row in df.iterrows():
            try:
                cins = str(row.iloc[1]).strip()
                if cins and cins.lower() not in ['nan', 'c i̇ n s i̇', 'c i n s i', 'none', 'satın alinacak malin']:
                    miktar_raw = row.iloc[2]
                    birim = row.iloc[3]
                    f1_raw = row.iloc[4]
                    f2_raw = row.iloc[5]
                    f3_raw = row.iloc[6]
                    
                    if pd.notna(cins) and pd.notna(miktar_raw):
                        miktar = safe_float(miktar_raw, 1.0)
                        f1 = safe_float(f1_raw, 0.0)
                        f2 = safe_float(f2_raw, 0.0)
                        f3 = safe_float(f3_raw, 0.0)
                        
                        kalemler.append({
                            "sira": sira,
                            "cins": cins,
                            "miktar": miktar,
                            "birim": str(birim).strip() if pd.notna(birim) else "Adet",
                            "f1": f1,
                            "f2": f2,
                            "f3": f3,
                        })
                        sira += 1
            except:
                pass
                
        return {"basarili": True, "kalemler": kalemler}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}



@app.post("/ihale-tekli-belge")
def ihale_tekli_belge(veri: dict, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    pdf_yol = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    
    # Get personnel
    mudur_adi = "Okul Müdürü"
    try:
        db.cursor.execute("SELECT ad_soyad FROM personel WHERE gorev LIKE '%MÜDÜR%' AND gorev NOT LIKE '%MÜDÜR YARDIMCISI%' LIMIT 1")
        row = db.cursor.fetchone()
        if row:
            mudur_adi = row[0]
    except: pass

    veri["okul_adi"] = ayar.get("okul_adi", "Okul Müdürlüğü")
    veri["okul_muduru"] = mudur_adi
    
    try:
        import ihale_motoru
        sonuc_dosyasi = ihale_motoru.belge_uret(veri, pdf_yol)
        if platform.system() == "Windows" and sonuc_dosyasi and os.path.exists(sonuc_dosyasi):
            os.startfile(sonuc_dosyasi)
        return {"basarili": True, "mesaj": "Belge başarıyla üretildi!", "dosya": sonuc_dosyasi}
    except Exception as e:
        import traceback
        logging.error(f"Tekli belge hatasi: {e}\n{traceback.format_exc()}")
        return {"basarili": False, "mesaj": f"Hata: {e}"}
