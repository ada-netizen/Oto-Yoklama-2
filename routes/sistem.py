from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Form, Body, HTTPException, Request
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
from dependencies import db, yollar, ayarlar, islem_logla, islem_loglari, create_job, update_job, get_job, GLOBAL_ISLEMLER, islem_durumlari
from utils import *

router = APIRouter()

@router.get("/islem-durumu/{job_id}")
def islem_durumu(job_id: str):
    return islem_durumlari.get(job_id, {"durum": "bulunamadi"})

def ogrenci_isleme_gorevi(temp_yol, job_id):
    try:
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Veritabani okunuyor...", "yuzde": 10}
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Excel ayristiriliyor...", "yuzde": 40}
        yeni_liste, hata = ExcelMotoru.ogrenci_oku(temp_yol, mevcut_ogrenciler)
        if hata:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": hata}
            islem_logla("hata", "Öğrenci aktarımı", hata)
            return
        if yeni_liste and len(yeni_liste) > 0:
            mevcut_ogrenciler.extend(yeni_liste)
            islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Veritabanina kaydediliyor...", "yuzde": 80}
            basarili, hata = db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            if not basarili:
                islem_durumlari[job_id] = {"durum": "hata", "mesaj": f"Veritabanina kaydedilemedi: {hata}"}
                islem_logla("hata", "Öğrenci aktarımı", f"Veritabanına kaydedilemedi: {hata}")
                return
            islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": f"{len(yeni_liste)} yeni ogrenci eklendi!", "yuzde": 100}
            islem_logla("bilgi", "Öğrenci aktarımı", f"{len(yeni_liste)} öğrenci aktarıldı.")
        else:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": "Dosyada yeni ogrenci bulunamadi."}
    except Exception as e:
        islem_durumlari[job_id] = {"durum": "hata", "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass

def devamsizlik_isleme_gorevi(temp_yol, job_id):
    try:
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Veritabani okunuyor...", "yuzde": 10}
        mevcut_ogrenciler, mevcut_devamsizliklar = db.yukle()
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Excel ayristiriliyor...", "yuzde": 40}
        yeni_liste, eklenen, hata = ExcelMotoru.devamsizlik_oku(temp_yol, [])
        if hata:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": hata}
            islem_logla("hata", "Devamsızlık aktarımı", hata)
            return
        if eklenen > 0 and len(yeni_liste) > 0:
            # Eşleşme kontrolü (Hiçbir öğrenci eşleşmiyorsa uyar)
            yuklenen_nolari = {str(d.get("no", "")).strip() for d in yeni_liste if str(d.get("no", "")).strip()}
            mevcut_nolari = {str(o.get("no", "")).strip() for o in mevcut_ogrenciler if str(o.get("no", "")).strip()}
            
            if yuklenen_nolari and mevcut_nolari and len(yuklenen_nolari.intersection(mevcut_nolari)) == 0:
                islem_durumlari[job_id] = {
                    "durum": "hata", 
                    "mesaj": "DİKKAT: Yüklenen devamsızlık listesindeki hiçbir öğrenci numarası, sistemde kayıtlı öğrencilerle eşleşmiyor! Lütfen doğru dosyayı yüklediğinizden veya öğrenci listesinin güncel olduğundan emin olun."
                }
                return

            mevcut_devamsizliklar = yeni_liste
            islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Veritabanina kaydediliyor...", "yuzde": 80}
            basarili, hata = db.kaydet(mevcut_ogrenciler, mevcut_devamsizliklar)
            if not basarili:
                islem_durumlari[job_id] = {"durum": "hata", "mesaj": f"Veritabanina kaydedilemedi: {hata}"}
                islem_logla("hata", "Devamsızlık aktarımı", f"Veritabanına kaydedilemedi: {hata}")
                return
            islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": f"{eklenen} yeni devamsizlik islendi!", "yuzde": 100}
            islem_logla("bilgi", "Devamsızlık aktarımı", f"{eklenen} kayıt aktarıldı.")
        else:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": "Yeni devamsizlik bulunamadi."}
    except Exception as e:
        islem_durumlari[job_id] = {"durum": "hata", "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass

def personel_isleme_gorevi(temp_yol, job_id):
    try:
        import pandas as pd
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Personel Excel okunuyor...", "yuzde": 30}
        df_temp = pd.read_excel(temp_yol, header=None)
        header_idx = 0
        for i, row in df_temp.iterrows():
            satir_metni = " ".join([str(x).upper() for x in row.values if pd.notna(x)])
            if "AD" in satir_metni and "SOYAD" in satir_metni:
                header_idx = i
                break
        try:
            df = pd.read_excel(temp_yol, header=header_idx)
        except Exception:
            try:
                df_list = pd.read_html(temp_yol, header=header_idx)
                df = max(df_list, key=len) if df_list else pd.DataFrame()
            except Exception:
                df = pd.read_csv(temp_yol, header=header_idx, on_bad_lines='skip')
        df.columns = df.columns.str.strip().str.upper()
        if df.empty:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": "Excel dosyası boş."}
            return
        personeller = []
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Kayitlar donusturuluyor...", "yuzde": 60}
        for _, row in df.iterrows():
            if pd.isna(row.get("AD")): continue
            ad = str(row.get("AD", "")).strip()
            soyad = str(row.get("SOYAD", "")).strip()
            gorev = str(row.get("GÖREVİ", "")).strip()
            brans = str(row.get("ALANI", "")).strip()
            if not gorev or gorev == "nan": gorev = "-"
            if not brans or brans == "nan": brans = "-"
            personeller.append({"ad": ad, "soyad": soyad, "gorev": gorev, "brans": brans})
        
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Veritabanina kaydediliyor...", "yuzde": 90}
        db.personel_kaydet(personeller)
        islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": f"{len(personeller)} personel basariyla yuklendi!", "yuzde": 100}
    except Exception as e:
        islem_durumlari[job_id] = {"durum": "hata", "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass

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
    yeni = await request.json()
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
