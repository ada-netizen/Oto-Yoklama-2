from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Form, Body, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os, json, re, tempfile, shutil, uuid
import pandas as pd
from datetime import datetime, timedelta
from veritabani import VeritabaniYoneticisi
from sistem_motoru import SistemMotoru
from excel_motoru import ExcelMotoru
from pdf_motoru import PDFYoneticisi
import logging
from araclar import VeriAraclari
from dependencies import db, yollar, ayarlar, islem_logla, islem_loglari, create_job, update_job, get_job, GLOBAL_ISLEMLER, islem_durumlari, get_aktif_kullanici
from utils import *

router = APIRouter()

@router.get("/versiyon")
def versiyon_getir():
    import sys, os, logging
    from pathlib import Path
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent.parent
    try:
        v_path = base_path / "versiyon.txt"
        with open(v_path, "r", encoding="utf-8") as f:
            v = f.read().strip()
            if not v: raise ValueError("versiyon.txt bos")
            return {"versiyon": v}
    except Exception as e:
        logging.error(f"versiyon.txt okunamadi. Hata: {e}")
        return {"versiyon": "v2.0"}

@router.get("/islem-durumu/{job_id}")
def islem_durumu(job_id: str):
    return get_job(job_id)


@router.get("/dosya/indir")
def dosya_indir(
    yol: str, 
    indir: Optional[bool] = False, 
    dosya_adi: Optional[str] = None, 
    aktif_kullanici = Depends(get_aktif_kullanici)
):
    """
    Sistem tarafından üretilen PDF, Excel veya Word belgelerini istemciye sunar veya indirir.
    Güvenlik: Yalnızca izin verilen veri ve çıktı dizinlerindeki dosyalara erişilebilir.
    """
    if not yol:
        raise HTTPException(status_code=400, detail="Dosya yolu belirtilmedi.")

    gercek_yol = os.path.normpath(os.path.abspath(yol))

    ana_proje_dizini = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    izin_verilen_dizinler = [
        os.path.normpath(os.path.abspath(yollar.get("VERI_DIZINI", ""))),
        os.path.normpath(os.path.abspath(yollar.get("PDF", ""))),
        os.path.normpath(os.path.abspath(yollar.get("YEDEK", ""))),
        os.path.normpath(os.path.abspath(tempfile.gettempdir())),
        ana_proje_dizini
    ]

    guvenli = any(gercek_yol.startswith(dizin) for dizin in izin_verilen_dizinler if dizin)
    if not guvenli or not os.path.isfile(gercek_yol):
        raise HTTPException(status_code=404, detail="Belirtilen dosya bulunamadı veya erişim yetkiniz yok.")

    uzanti = os.path.splitext(gercek_yol)[1].lower()
    ad = dosya_adi or os.path.basename(gercek_yol)

    media_type = "application/octet-stream"
    if uzanti == ".pdf":
        media_type = "application/pdf"
    elif uzanti in (".xlsx", ".xls"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif uzanti in (".docx", ".doc"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    disposition = "attachment" if (indir or uzanti != ".pdf") else "inline"

    return FileResponse(
        gercek_yol,
        media_type=media_type,
        filename=ad,
        content_disposition_type=disposition
    )

@router.get("/loglar")
def loglari_getir():
    try:
        with open(yollar["LOG"], "r", encoding="utf-8") as dosya:
            kayitlar = [json.loads(satir) for satir in dosya if satir.strip()]
        return {"loglar": list(reversed(kayitlar[-200:]))}
    except (OSError, json.JSONDecodeError):
        return {"loglar": list(reversed(islem_loglari))}


@router.delete("/loglar")
def loglari_temizle():
    islem_loglari.clear()
    try:
        open(yollar["LOG"], "w", encoding="utf-8").close()
    except OSError as e:
        return {"basarili": False, "mesaj": f"Loglar temizlenemedi: {e}"}
    return {"basarili": True, "mesaj": "İşlem logları temizlendi."}


@router.get("/ayarlar-getir")
def ayarlar_getir():
    return {"ayarlar": ayarlari_al(), "yollar": yollar}


@router.post("/ayarlar-kaydet")
async def ayarlar_kaydet(request: Request):
    try:
        yeni = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz JSON verisi.")
    if not isinstance(yeni, dict):
        raise HTTPException(status_code=400, detail="Ayar verisi sözlük formatında olmalıdır.")
    ayar = ayarlari_al()
    ayar.update(yeni)
    SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
    return {"basarili": True, "mesaj": "Ayarlar başarıyla kaydedildi."}


@router.post("/logo-yukle")
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


@router.post("/yedek-al")
def yedek_al():
    ayar = ayarlari_al()
    basarili, hata = SistemMotoru.yedek_al(yollar["DB"], ayar, yollar["YEDEK"])
    if basarili:
        ayar["son_yedekleme_gunu"] = datetime.now().strftime("%Y-%m-%d")
        SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
        islem_logla("bilgi", "Yedekleme", "Veritabanı yedeği oluşturuldu.")
        return {"basarili": True, "mesaj": "Veritabanı başarıyla yedeklendi!"}
    islem_logla("hata", "Yedekleme", f"Yedekleme başarısız: {hata}")
    return {"basarili": False, "mesaj": f"Yedekleme Hatası: {hata}"}


@router.get("/yedekler-listele")
def yedekler_listele():
    ayar = ayarlari_al()
    return {"yedekler": SistemMotoru.yedekleri_listele(ayar, yollar["YEDEK"])}


@router.post("/yedek-geri-yukle")
async def yedek_geri_yukle(request: Request):
    veri = await request.json()
    ayar = ayarlari_al()
    hedef_klasor = ayar.get("yedek_kayit_klasoru", yollar["YEDEK"])
    dosya_adi = veri.get("dosya", "")
    if os.path.basename(dosya_adi) != dosya_adi or not dosya_adi.startswith("veritabani_yedek_") or not dosya_adi.endswith(".db"):
        return {"basarili": False, "mesaj": "Geçersiz yedek dosyası."}
    kaynak_yol = os.path.join(hedef_klasor, dosya_adi)
    if not os.path.exists(kaynak_yol):
        return {"basarili": False, "mesaj": "Seçilen yedek dosyası bulunamadı."}
    try:
        mevcut_yedek_basarili, mevcut_yedek_hatasi = SistemMotoru.yedek_al(db.db_yolu, ayar, yollar["YEDEK"])
        if not mevcut_yedek_basarili:
            return {"basarili": False, "mesaj": f"Mevcut veriler korunamadı: {mevcut_yedek_hatasi}"}
        db.kapat()
        shutil.copy(kaynak_yol, yollar["DB"])
        
        # Ayarları da geri yükle
        zaman_etiketi = dosya_adi.replace("veritabani_yedek_", "").replace(".db", "")
        ayarlar_kaynak = os.path.join(hedef_klasor, f"ayarlar_yedek_{zaman_etiketi}.json")
        if os.path.exists(ayarlar_kaynak):
            shutil.copy(ayarlar_kaynak, yollar["AYARLAR"])
            # Geri yüklenen ayarları sistemin hemen kullanması için güncelliyoruz
            global ayarlar
            ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])
            
        db.baglan_ve_hazirla()
        islem_logla("uyarı", "Geri yükleme", f"Yedek geri yüklendi: {dosya_adi}")
        return {"basarili": True, "mesaj": "Yedek başarıyla yüklendi. Sayfayı yenileyin."}
    except Exception as e:
        db.baglan_ve_hazirla()
        islem_logla("hata", "Geri yükleme", f"Yedek yüklenemedi: {e}")
        return {"basarili": False, "mesaj": f"Yedek yüklenirken hata oluştu: {e}"}


@router.post("/son-islemi-geri-al")
def son_islemi_geri_al():
    yedekler = SistemMotoru.yedekleri_listele(ayarlari_al(), yollar["YEDEK"])
    if not yedekler:
        return {"basarili": False, "mesaj": "Geri alınabilecek bir yedek bulunamadı."}
    sonuc = yedek_geri_yukle({"dosya": yedekler[0]["dosya_adi"]})
    if sonuc["basarili"]:
        islem_logla("uyarı", "Geri alma", "Son işlem geri alındı.")
    return sonuc



@router.delete("/veritabani-sifirla")
def veritabani_sifirla():
    basarili, hata = SistemMotoru.yedek_al(db.db_yolu, ayarlari_al(), yollar["YEDEK"])
    if not basarili:
        return {"basarili": False, "mesaj": f"Sıfırlama öncesi yedek alınamadı: {hata}"}
    db.sifirla()
    islem_logla("uyarı", "Veritabanı sıfırlama", "Tüm veritabanı sıfırlandı.")
    return {"basarili": True, "mesaj": "Tüm veritabanı başarıyla sıfırlandı."}


class GeriBildirim(BaseModel):
    isim: Optional[str] = ""
    eposta: Optional[str] = ""
    tur: str
    mesaj: str

# Kendi e-postanıza mesaj gelmesi için formspree.io veya web3forms.com üzerinden aldığınız API URL'sini buraya yapıştırın.
# Örnek Formspree: "https://formspree.io/f/xbjnq..."
# Örnek Web3Forms: "https://api.web3forms.com/submit" (Ayrıca subject veya access_key göndermek gerekir)
GERI_BILDIRIM_URL = "https://formspree.io/f/mqpapdkd" 

@router.post("/geri-bildirim")
def geri_bildirim_gonder(veri: GeriBildirim):
    if not GERI_BILDIRIM_URL:
        # Eğer henüz URL girilmediyse, mesajı log dosyasına yazıp başarıyla iletilmiş gibi yapalım (Prototip testi için)
        import logging
        logging.info(f"YENİ GERİ BİLDİRİM ({veri.tur}):\nKimden: {veri.isim} ({veri.eposta})\nMesaj: {veri.mesaj}")
        return {"basarili": True, "mesaj": "Sistem test modunda olduğu için mesajınız başarıyla yerel kayıtlara alındı."}
    
    # Gerçek gönderim
    import urllib.request
    import json
    
    payload = {
        "İsim_Kurum": veri.isim,
        "Eposta": veri.eposta,
        "Mesaj_Türü": veri.tur,
        "Mesaj": veri.mesaj
    }
    
    try:
        import ssl
        import logging
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            GERI_BILDIRIM_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            logging.info("Geri bildirim basariyla gonderildi.")
            return {"basarili": True, "mesaj": "Mesajınız başarıyla iletildi."}
    except Exception as e:
        import logging
        logging.error(f"Geri bildirim gonderim hatasi: {str(e)}")
        return {"basarili": False, "mesaj": f"Mesaj gönderilirken hata oluştu (Lütfen app.log dosyasını kontrol edin)"}

@router.post("/arsivle")
async def arsivle_sistem(request: Request):
    data = await request.json()
    arsiv_adi = data.get("arsiv_adi", "Arsiv")
    
    import shutil, os
    from dependencies import db, yollar
    
    arsiv_klasoru = os.path.join(yollar["ANA"], "Arsivler", arsiv_adi)
    os.makedirs(arsiv_klasoru, exist_ok=True)
    
    try:
        # Copy DB
        if os.path.exists(yollar["DB"]):
            shutil.copy(yollar["DB"], os.path.join(arsiv_klasoru, "yoklama_veritabani.db"))
        
        # Copy PDFs
        if os.path.exists(yollar["PDF"]):
            hedef_pdf = os.path.join(arsiv_klasoru, "PDF_Ciktilari")
            if os.path.exists(hedef_pdf):
                shutil.rmtree(hedef_pdf)
            shutil.copytree(yollar["PDF"], hedef_pdf)
            
        # Sifirla DB (Keep personel)
        db.sifirla()
        
        return {"basarili": True, "mesaj": "Arşivleme tamamlandı ve veritabanı sıfırlandı."}
    except Exception as e:
        return {"basarili": False, "mesaj": f"Hata: {str(e)}"}


@router.get("/sistem-teshis")
def sistem_teshis_getir():
    """Sistem sağlığı, SQLite bütünlük ve kayıt teşhis verilerini döndürür."""
    import platform
    try:
        db_yolu = db.db_yolu
        db_boyut_kb = round(os.path.getsize(db_yolu) / 1024, 1) if os.path.exists(db_yolu) else 0

        # SQLite PRAGMA kontrolleri
        integrity = "OK"
        journal_mode = "WAL"
        try:
            db.cursor.execute("PRAGMA integrity_check")
            row = db.cursor.fetchone()
            if row:
                integrity = str(row[0])
            db.cursor.execute("PRAGMA journal_mode")
            row_j = db.cursor.fetchone()
            if row_j:
                journal_mode = str(row_j[0]).upper()
        except Exception as pe:
            logging.warning(f"Pragma kontrol uyarısı: {pe}")

        # Kayıt sayıları
        ogrenci_sayisi = 0
        devamsizlik_sayisi = 0
        personel_sayisi = 0
        evrak_sayisi = 0
        try:
            db.cursor.execute("SELECT COUNT(*) FROM ogrenciler")
            ogrenci_sayisi = db.cursor.fetchone()[0]
            db.cursor.execute("SELECT COUNT(*) FROM devamsizliklar")
            devamsizlik_sayisi = db.cursor.fetchone()[0]
            db.cursor.execute("SELECT COUNT(*) FROM personel")
            personel_sayisi = db.cursor.fetchone()[0]
            db.cursor.execute("SELECT COUNT(*) FROM uretilen_evraklar")
            evrak_sayisi = db.cursor.fetchone()[0]
        except Exception as ce:
            logging.warning(f"Kayıt sayısı sorgu uyarısı: {ce}")

        return {
            "basarili": True,
            "veritabani": {
                "yol": db_yolu,
                "boyut_kb": db_boyut_kb,
                "butunluk": integrity,
                "journal_mode": journal_mode,
                "ogrenci_sayisi": ogrenci_sayisi,
                "devamsizlik_sayisi": devamsizlik_sayisi,
                "personel_sayisi": personel_sayisi,
                "evrak_sayisi": evrak_sayisi,
                "snapshot_var": getattr(db, "_son_snapshot", None) is not None
            },
            "sistem": {
                "python_versiyon": platform.python_version(),
                "os": f"{platform.system()} {platform.release()}",
                "versiyon": "v2.0 MEB Uyumlu",
                "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }
        }
    except Exception as e:
        logging.error(f"/sistem-teshis genel hatası: {e}")
        return {"basarili": False, "mesaj": f"Sistem teşhis hatası: {e}"}

