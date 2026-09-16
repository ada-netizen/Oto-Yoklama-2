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

router = APIRouter()

@router.get("/personeller")
def personelleri_getir():
    try:
        db.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
        personel_listesi = [{'ad': r[0], 'brans': r[1], 'gorev': r[2], 'grup': r[3]} for r in db.cursor.fetchall()]
        return {"personeller": personel_listesi}
    except Exception as e:
        logging.error(f"personelleri_getir hatasi: {e}")
        return {"personeller": []}


def _personel_excel_yukle_dogrudan(temp_yol, uzanti):
    """Hazırlanmış personel dosyasını okur ve tek transaction ile kaydeder."""
    try:
        tablo_oku = pd.read_csv if uzanti == ".csv" else pd.read_excel
        df_temp = tablo_oku(temp_yol, header=None)
        if df_temp.empty:
            return {"basarili": False, "mesaj": "Excel dosyası boş."}
        header_idx = 0
        for i, row in df_temp.iterrows():
            satir_metni = " ".join([str(x).upper() for x in row.values if pd.notna(x)])
            if "AD" in satir_metni and "SOYAD" in satir_metni:
                header_idx = i
                break

        df = tablo_oku(temp_yol, header=header_idx)
        df.columns = df.columns.str.strip().str.upper()

        ad_sutunu = _excel_sutunu_bul(df.columns, ['AD SOYAD', 'ADI SOYADI'])
        if not ad_sutunu:
            return {"basarili": False, "mesaj": "Excel'de 'Ad Soyad' başlığı bulunamadı!"}
        grup_sutunu = _excel_sutunu_bul(df.columns, ['GRUP', 'PERSONEL TÜRÜ', 'PERSONEL TURU', 'TÜR', 'TUR'])

        yeni_personeller = []
        for _, row in df.iterrows():
            ad = str(row[ad_sutunu]).strip()
            gorev = "-"
            gorev_sutunu = _excel_sutunu_bul(df.columns, ['GÖREVİ', 'GÖREVI', 'GÖREV', 'UNVAN', 'UNVANI', 'ÜNVANI'])
            if gorev_sutunu: gorev = str(row[gorev_sutunu]).strip()

            brans = "-"
            brans_sutunu = _excel_sutunu_bul(df.columns, ['BRANŞI', 'BRANSI', 'BRANŞ', 'ALANI', 'ALAN'])
            if brans_sutunu: brans = str(row[brans_sutunu]).strip()

            if not brans or brans.lower() == 'nan': brans = "-"
            if not gorev or gorev.lower() == 'nan': gorev = "-"

            if ad and ad.lower() != 'nan':
                grup = ""
                if grup_sutunu:
                    grup = str(row[grup_sutunu]).strip()
                    if not grup or grup.lower() == 'nan':
                        grup = ""
                if not grup:
                    grup = _personel_grup_tahmin_et(gorev)
                yeni_personeller.append((ad, brans, gorev, grup))

        if not yeni_personeller:
            return {"basarili": False, "mesaj": "Excel'de aktarılacak geçerli personel bulunamadı."}

        yedek_basarili, yedek_hatasi = SistemMotoru.yedek_al(db.db_yolu, ayarlari_al(), yollar["YEDEK"])
        if not yedek_basarili:
            return {"basarili": False, "mesaj": f"Aktarım öncesi yedek alınamadı: {yedek_hatasi}"}

        try:
            db.cursor.execute("BEGIN TRANSACTION")
            db.cursor.execute("DELETE FROM personel")
            db.cursor.executemany("INSERT INTO personel (ad_soyad, brans, gorev, grup) VALUES (?, ?, ?, ?)", yeni_personeller)
            db.conn.commit()
        except Exception:
            db.conn.rollback()
            raise

        return {"basarili": True, "mesaj": f"{len(yeni_personeller)} personel yüklendi ve gruplandırıldı."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass


def personel_excel_isleme_gorevi(temp_yol, uzanti, job_id):
    try:
        islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Personel Excel okunuyor...", "yuzde": 30}
        sonuc = _personel_excel_yukle_dogrudan(temp_yol, uzanti)
        if sonuc["basarili"]:
            islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": sonuc["mesaj"], "yuzde": 100}
        else:
            islem_durumlari[job_id] = {"durum": "hata", "mesaj": sonuc["mesaj"], "yuzde": 100}
    except Exception as e:
        islem_durumlari[job_id] = {"durum": "hata", "mesaj": str(e), "yuzde": 100}
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass


@router.post("/personel-excel-yukle")
async def personel_excel_yukle(background_tasks: BackgroundTasks, dosya: UploadFile = File(...)):
    """Personel Excel aktarımını arka plana alır ve işlem kimliği döndürür."""
    uzanti, hata = excel_yukleme_dogrula(dosya)
    if hata:
        return {"basarili": False, "mesaj": hata}
    job_id = str(uuid.uuid4())
    islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "Dosya alınıyor...", "yuzde": 0}
    temp_yol = f"temp_personel_{job_id}{uzanti}"
    with open(temp_yol, "wb") as buffer:
        shutil.copyfileobj(dosya.file, buffer)
    background_tasks.add_task(personel_excel_isleme_gorevi, temp_yol, uzanti, job_id)
    return {"basarili": True, "job_id": job_id}


@router.post("/personel-ekle")
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



@router.delete("/personel-sil/{ad}")
def personel_sil(ad: str):
    db.cursor.execute("DELETE FROM personel WHERE ad_soyad = ?", (ad,))
    db.conn.commit()
    
    # Eşleşmeleri sil (ad silindiği için eski eşleşmeleri de temizlemek iyi olabilir, ama şimdilik bırakıyoruz)
    return {"basarili": True, "mesaj": f"{ad} silindi."}

@router.put("/personel-guncelle/{eski_ad}")
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

@router.get("/personel-excel-indir")
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

@router.get("/personel-pdf-indir")
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



@router.delete("/personel-sifirla")
def personel_sifirla():
    try:
        basarili, hata = SistemMotoru.yedek_al(db.db_yolu, ayarlari_al(), yollar["YEDEK"])
        if not basarili:
            return {"basarili": False, "mesaj": f"Sıfırlama öncesi yedek alınamadı: {hata}"}
        db.cursor.execute("DELETE FROM personel")
        db.conn.commit()
        islem_logla("uyarı", "Personel sıfırlama", "Tüm personel kayıtları sıfırlandı.")
        return {"basarili": True, "mesaj": "Tüm personel silindi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

