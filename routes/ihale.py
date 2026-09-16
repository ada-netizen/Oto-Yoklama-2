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

VARSAYILAN_OLCU_BIRIMLERI = [
    "ADET_BIRIM",
    "AFIF_BIRIM_FIYATI",
    "ATV_BIRIM_FIYATI",
    "ALTIN_AYARI",
    "KG_METREKARE",
    "TON_BASINA_TASIMA_KAPASITESI",
    "ADET_CIFT",
    "BRUT_KALORI_DEGERI",
    "BIN_LITRE",
    "GUMUS",
    "GRAM",
    "GROS_TON",
    "YUZ_ADET",
    "KILOGRAM_ADET",
    "KILOWATT_SAAT",
    "KILOWATT",
    "LITRE",
    "METRE",
    "METREKUP",
    "METREKARE",
    "TON",
    "KALEM",
    "PUAN",
]

@router.get("/olcu-birimleri")
def olcu_birimleri_getir():
    return {"birimler": VARSAYILAN_OLCU_BIRIMLERI}

@router.post("/sablon-hazirla")
def sablon_hazirla(veri: SablonVerisi):
    try:
        logging.info(f"SABLON HAZIRLA DATA: {veri.dict()}")
        import openpyxl
        from openpyxl.styles import Font

        sablon_yolu = _sablon_excel_yolu_olustur()
        wb = openpyxl.load_workbook(sablon_yolu)
        ws = wb.active

        # Eski verileri temizle ve başlık satırını koru
        if ws.max_row > 1:
            ws.delete_rows(2, ws.max_row - 1)

        row_idx = 2
        for kalem in veri.kalemler:
            if not kalem or not str(kalem.get('cins', '')).strip():
                continue
            ws[f"A{row_idx}"] = kalem.get('cins', '')
            ws[f"B{row_idx}"] = kalem.get('miktar', '')
            ws[f"C{row_idx}"] = kalem.get('birim', '')
            row_idx += 1

        # Başlık satırını görünüm için bold tut
        for sutun in ["A", "B", "C"]:
            ws[f"{sutun}1"].font = Font(bold=True)

        ayar = ayarlari_al()
        ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
        if not os.path.exists(ana_klasor):
            os.makedirs(ana_klasor)
        dosya_yolu = os.path.join(ana_klasor, "Yaklasik_Maliyet_Sablon.xlsx")
        wb.save(dosya_yolu)
        dosyayi_otomatik_ac(dosya_yolu)

        return {"basarili": True, "mesaj": "Şablon hazırlandı ve açıldı."}
    except Exception as e:
        logging.error(f"Şablon hazırlanırken hata: {e}")
        return {"basarili": False, "mesaj": str(e)}

@router.post("/excel-onizle")
async def excel_onizle(dosya: UploadFile = File(...), tur: str = Form("personel")):
    """İçe aktarmadan önce dosyanın ilk satırlarını ve temel hatalarını döndürür."""
    uzanti, hata = excel_yukleme_dogrula(dosya)
    if hata:
        return {"basarili": False, "mesaj": hata}
    if tur not in {"ogrenci", "devamsizlik", "personel"}:
        return {"basarili": False, "mesaj": "Geçersiz içe aktarma türü."}

    temp_yol = os.path.join(tempfile.gettempdir(), f"onizleme_{uuid.uuid4().hex}{uzanti}")
    try:
        with open(temp_yol, "wb") as buffer:
            shutil.copyfileobj(dosya.file, buffer)

        if uzanti == ".csv":
            try:
                df_ham = pd.read_csv(temp_yol, header=None, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df_ham = pd.read_csv(temp_yol, header=None, encoding="cp1254")
        else:
            try:
                df_ham = pd.read_excel(temp_yol, header=None)
            except Exception:
                try:
                    df_list = pd.read_html(temp_yol, header=None)
                    df_ham = max(df_list, key=len) if df_list else pd.DataFrame()
                except Exception:
                    df_ham = pd.read_csv(temp_yol, header=None, on_bad_lines='skip')
        if df_ham.empty:
            return {"basarili": False, "mesaj": "Dosya boş."}

        header_idx = 0
        if tur == "personel":
            for i, row in df_ham.iterrows():
                basliklar = {_excel_sutunu_bul([deger], ["AD SOYAD", "ADI SOYADI"]) for deger in row.values}
                if any(basliklar):
                    header_idx = i
                    break

        if uzanti == ".csv":
            try:
                df = pd.read_csv(temp_yol, header=header_idx, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(temp_yol, header=header_idx, encoding="cp1254")
        else:
            try:
                df = pd.read_excel(temp_yol, header=header_idx)
            except Exception:
                try:
                    df_list = pd.read_html(temp_yol, header=header_idx)
                    df = max(df_list, key=len) if df_list else pd.DataFrame()
                except Exception:
                    df = pd.read_csv(temp_yol, header=header_idx, on_bad_lines='skip')
        df.columns = [str(sutun).strip() for sutun in df.columns]

        hatalar = []
        if tur == "personel":
            ad_sutunu = _excel_sutunu_bul(df.columns, ["AD SOYAD", "ADI SOYADI"])
            if not ad_sutunu:
                hatalar.append("Ad Soyad sütunu bulunamadı.")
            else:
                eksik_ad = int(df[ad_sutunu].isna().sum())
                if eksik_ad:
                    hatalar.append(f"{eksik_ad} satırda ad-soyad eksik.")

        onizleme_kayitlar = df.head(20).to_dict(orient="records")
        onizleme = [{str(k): (str(v) if pd.notna(v) else "") for k, v in row.items()} for row in onizleme_kayitlar]
        return {
            "basarili": True,
            "tur": tur,
            "toplam_satir": int(len(df)),
            "gosterilen_satir": len(onizleme),
            "sutunlar": list(df.columns),
            "onizleme": onizleme,
            "hatalar": hatalar,
        }
    except Exception as e:
        logging.error(f"Excel önizleme hatası: {e}")
        return {"basarili": False, "mesaj": f"Dosya önizlenemedi: {e}"}
    finally:
        if os.path.exists(temp_yol):
            try:
                os.remove(temp_yol)
            except Exception:
                pass

@router.post("/ihale-excel-oku")
async def ihale_excel_oku(dosya: UploadFile = File(...)):
    try:
        temp_path = os.path.join(yollar["TEMP"], f"ihale_{uuid.uuid4().hex}.xls")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(dosya.file, f)
        
        kalemler, hata = ExcelMotoru.ihale_oku(temp_path)
        if hata:
            return {"basarili": False, "mesaj": hata}
            
        return {"basarili": True, "kalemler": kalemler}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/ihale-tekli-belge")
def ihale_tekli_belge(veri: dict, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    pdf_yol = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    
    mudur_adi = "Okul Müdürü"
    try:
        db.cursor.execute("SELECT ad_soyad FROM personel WHERE gorev LIKE '%MÜDÜR%' AND gorev NOT LIKE '%MÜDÜR YARDIMCISI%' LIMIT 1")
        row = db.cursor.fetchone()
        if row:
            mudur_adi = row[0]
    except: pass

    veri["okul_adi"] = ayar.get("okul_adi", "Okul")
    baslik = str(veri.get("resmi_baslik") or "").strip()
    if not baslik:
        veri["resmi_baslik"] = f"{veri['okul_adi'].strip()} Müdürlüğü"
    else:
        if not re.search(r"(MÜDÜRLÜĞÜ|MÜDÜRLÜK|OKULU|LİSESİ|ORTAOKULU|İLKOKULU|ANAOKULU|KAYMAKAMLIĞI|VALİLİĞİ|BAŞKANLIĞI)$", baslik, flags=re.IGNORECASE):
            veri["resmi_baslik"] = f"{baslik} Müdürlüğü"
    veri["okul_muduru"] = mudur_adi
    
    # Komisyon üyelerinin görevlerini (unvanlarını) veritabanından çekip ekleyelim
    if "komisyon" in veri and isinstance(veri["komisyon"], dict):
        for k_key, k_name in list(veri["komisyon"].items()):
            if k_name and isinstance(k_name, str):
                try:
                    db.cursor.execute("SELECT gorev FROM personel WHERE ad_soyad = ?", (k_name,))
                    row = db.cursor.fetchone()
                    if row:
                        veri["komisyon"][f"{k_key}_gorev"] = row[0]
                    else:
                        veri["komisyon"][f"{k_key}_gorev"] = "Üye"
                except:
                    veri["komisyon"][f"{k_key}_gorev"] = "Üye"
    
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

