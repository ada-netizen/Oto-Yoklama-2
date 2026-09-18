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
import tempfile
from contextlib import contextmanager
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from utils import *
from utils import ayarlari_al

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = FastAPI(title="Elektronik Okul Sistemi API")

from routes import ogrenci, personel, ihale, pdf, rapor, sistem
app.include_router(ogrenci.router)
app.include_router(personel.router)
app.include_router(ihale.router)
app.include_router(pdf.router)
app.include_router(rapor.router)
app.include_router(sistem.router)


from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logging.error(f"UNHANDLED EXCEPTION in {request.url.path}: {error_msg}")
    return JSONResponse(status_code=500, content={"basarili": False, "mesaj": f"Beklenmeyen sunucu hatası: {str(exc)}"})

class LogMessage(BaseModel):
    level: str
    message: str

@app.post("/log-error")
def log_frontend_error(log: LogMessage):
    if log.level == 'error':
        logging.error(f"Frontend Error: {log.message}")
    else:
        logging.info(f"Frontend Log: {log.message}")
    return {"status": "ok"}


class SablonVerisi(BaseModel):
    kalemler: List[Dict]
    firmaVergiler: List[str] = []
    firmalar: List[str] = []
    firmaAdresleri: List[str] = []


islem_durumlari = {}
MAX_IMPORT_SIZE = 25 * 1024 * 1024
ALLOWED_IMPORT_EXTENSIONS = {".xlsx", ".xls", ".csv"}


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
islem_loglari = []


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
    ozurlu_str: Optional[str] = "0"
    ozursuz_str: Optional[str] = "0"

class PersonelRequest(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = None

class PersonelModel(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = "-"
    
class TebligBireyselRequest(BaseModel):
    kurum: Optional[str] = ""
    sayi: str
    konu: str
    tarih: str
    eden: PersonelModel
    edilen: PersonelModel
    yer: str
    teblig_tarihi: Optional[str] = None
    teblig_saati: Optional[str] = None
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
_son_ayarlar_mtime = 0

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
# =====================================================================
# 2. YAZI TEBLİĞİ VE PERSONEL İŞLEMLERİ
# =====================================================================
# =====================================================================
# 3. RAPORLAR
# =====================================================================
# =====================================================================
# 4. AYARLAR, LOGO VE YEDEKLEME
# =====================================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sys

def resource_path_api(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# Jinja2 Templates
templates = Jinja2Templates(directory=resource_path_api('frontend'))
js_dir = resource_path_api(os.path.join('frontend', 'js'))
if os.path.isdir(js_dir):
    app.mount('/js', StaticFiles(directory=js_dir), name='js')

assets_dir = resource_path_api(os.path.join('frontend', 'assets'))
if os.path.isdir(assets_dir):
    app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

sab_dir = resource_path_api('sablonlar')
if os.path.isdir(sab_dir):
    app.mount('/sablonlar', StaticFiles(directory=sab_dir), name='sablonlar')

@app.get('/', response_class=HTMLResponse)
async def read_index(request: Request):
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return templates.TemplateResponse(request=request, name="index.html", context={}, headers=headers)

@app.get('/style.css')
def read_style():
    return FileResponse(resource_path_api(os.path.join('frontend', 'style.css')))

@app.get('/lucide.min.js')
def read_lucide():
    return FileResponse(resource_path_api(os.path.join('frontend', 'lucide.min.js')))
