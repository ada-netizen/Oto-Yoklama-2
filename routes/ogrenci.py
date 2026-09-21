from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
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
from dependencies import db, yollar, ayarlar, islem_logla, create_job, update_job, get_job, GLOBAL_ISLEMLER, islem_durumlari
from utils import *

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



router = APIRouter()

@router.get("/ogrenciler")
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


@router.get("/ogrenci-detay/{ogr_no}")
def ogrenci_detay_getir(ogr_no: str):
    _, devamsizlik_listesi = db.yukle()
    ogr_devleri = [d for d in devamsizlik_listesi if str(d['no']).strip() == str(ogr_no).strip()]
    return {"devamsizliklar": ogr_devleri}


@router.post("/ogrenci-excel-yukle")
async def ogrenci_excel_yukle(background_tasks: BackgroundTasks, dosya: UploadFile = File(...)):
    uzanti, hata = excel_yukleme_dogrula(dosya)
    if hata:
        return {"basarili": False, "mesaj": hata}
    job_id = str(uuid.uuid4())
    islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "Dosya aliniyor...", "yuzde": 0}
    temp_yol = f"temp_ogr_{job_id}{uzanti}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    background_tasks.add_task(ogrenci_isleme_gorevi, temp_yol, job_id)
    return {"basarili": True, "job_id": job_id}


@router.post("/devamsizlik-excel-yukle")
async def devamsizlik_excel_yukle(background_tasks: BackgroundTasks, dosya: UploadFile = File(...)):
    uzanti, hata = excel_yukleme_dogrula(dosya)
    if hata:
        return {"basarili": False, "mesaj": hata}
    job_id = str(uuid.uuid4())
    islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "Dosya aliniyor...", "yuzde": 0}
    temp_yol = os.path.join(tempfile.gettempdir(), f"temp_dev_{job_id}{uzanti}")
    try:
        with open(temp_yol, "wb") as buffer:
            shutil.copyfileobj(dosya.file, buffer)
    except Exception as e:
        return {"basarili": False, "mesaj": f"Sunucuya kaydedilemedi: {e}"}
    background_tasks.add_task(devamsizlik_isleme_gorevi, temp_yol, job_id)
    return {"basarili": True, "job_id": job_id}


@router.delete("/ogrenci-sil/{ogr_no}")
def ogrenci_sil(ogr_no: str):
    ogrenciler, devler = db.yukle()
    yeni_ogr = [o for o in ogrenciler if str(o['no']).strip() != str(ogr_no).strip()]
    yeni_dev = [d for d in devler if str(d['no']).strip() != str(ogr_no).strip()]
    basarili, hata = db.kaydet(yeni_ogr, yeni_dev)
    if not basarili:
        return {"basarili": False, "mesaj": f"Öğrenci silinemedi: {hata}"}
    return {"basarili": True, "mesaj": f"{ogr_no} numaralı öğrenci ve devamsızlıkları silindi."}


@router.delete("/devamsizlik-sil/{d_id}")
def devamsizlik_sil(d_id: str):
    ogrenciler, devler = db.yukle()
    yeni_dev = [d for d in devler if str(d.get('id', '')) != str(d_id)]
    basarili, hata = db.kaydet(ogrenciler, yeni_dev)
    if not basarili:
        return {"basarili": False, "mesaj": f"Devamsızlık kaydı silinemedi: {hata}"}
    return {"basarili": True, "mesaj": "Devamsızlık kaydı başarıyla silindi."}


@router.post("/devamsizlik-manuel-ekle")
def devamsizlik_manuel_ekle(veri: DevamsizlikEkleRequest):
    # PDF için takvimden seçilen geçici tarihlerin kalıcı olmasını tamamen engellemek
    # adına bu fonksiyon artık veritabanına kayıt YAPMAMAKTADIR.
    # Tarayıcı önbelleğinde (cache) kalan eski JS kodları bu isteği atsa bile 
    # artık veritabanına yansımayacaktır.
    return {"basarili": True, "mesaj": "Manuel devamsızlıklar artık kalıcı kaydedilmiyor."}


@router.delete("/ogrencileri-sifirla")
def ogrencileri_sifirla():
    try:
        basarili, hata = SistemMotoru.yedek_al(db.db_yolu, ayarlari_al(), yollar["YEDEK"])
        if not basarili:
            return {"basarili": False, "mesaj": f"Sıfırlama öncesi yedek alınamadı: {hata}"}
        db.cursor.execute("DELETE FROM ogrenciler")
        db.cursor.execute("DELETE FROM devamsizliklar")
        db.conn.commit()
        islem_logla("uyarı", "Öğrenci sıfırlama", "Öğrenci ve devamsızlık kayıtları sıfırlandı.")
        return {"basarili": True, "mesaj": "Tüm öğrenciler ve devamsızlıkları silindi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


class OgrenciRequest(BaseModel):
    no: str
    ad_soyad: str
    sube: str
    eski_no: Optional[str] = None

@router.post("/ogrenci-ekle-guncelle")
def ogrenci_ekle_guncelle(ogr: OgrenciRequest):
    try:
        ogrenciler, devler = db.yukle()
        
        # Check if we are updating an existing student
        hedef_no = (ogr.eski_no if ogr.eski_no else ogr.no).strip()
        
        # If adding a new student or changing number, check if the NEW number already exists
        if (not ogr.eski_no or ogr.eski_no != ogr.no) and any(str(o['no']).strip() == str(ogr.no).strip() for o in ogrenciler):
            return {"basarili": False, "mesaj": f"{ogr.no} numarali ogrenci zaten kayitli!"}
            
        bulundu = False
        for o in ogrenciler:
            if str(o['no']).strip() == hedef_no:
                o['no'] = ogr.no.strip()
                o['ad_soyad'] = ogr.ad_soyad.upper().strip()
                o['sube'] = ogr.sube.strip().upper()
                bulundu = True
                break
                
        if not bulundu:
            ogrenciler.append({
                "no": ogr.no.strip(),
                "ad_soyad": ogr.ad_soyad.upper().strip(),
                "sube": ogr.sube.strip().upper()
            })
            
        # Update devamsizliklar if student number changed
        if ogr.eski_no and ogr.eski_no != ogr.no:
            for d in devler:
                if str(d.get('no', '')).strip() == hedef_no:
                    d['no'] = ogr.no.strip()
                    
        basarili, hata = db.kaydet(ogrenciler, devler)
        if not basarili: return {"basarili": False, "mesaj": hata}
        return {"basarili": True, "mesaj": "Ogrenci basariyla kaydedildi!"}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

