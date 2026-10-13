# ================= api.py (FULL BACKEND) =================
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import sys
import time
import logging
import threading
import traceback
from datetime import datetime

from veritabani import VeritabaniYoneticisi
from sistem_motoru import SistemMotoru
from utils import ayarlari_al
from dependencies import db, yollar, ayarlar, islem_durumlari, islem_loglari

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = FastAPI(title="Elektronik Okul Sistemi API")

from routes import ogrenci, personel, ihale, pdf, rapor, sistem, dashboard, saglik
app.include_router(ogrenci.router)
app.include_router(personel.router)
app.include_router(ihale.router)
app.include_router(pdf.router)
app.include_router(rapor.router)
app.include_router(sistem.router)
app.include_router(dashboard.router)
app.include_router(saglik.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/js", "/assets", "/sablonlar", "/istatistikler")) or request.url.path in ("/", "/style.css", "/lucide.min.js"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

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


# =====================================================================
# OTOMATİK ZAMANLI YEDEKLEME (arka planda çalışan iş parçacığı)
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
                ayar_saat = "0" + ayar_saat

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

                    if yedekle:
                        basarili, _ = SistemMotoru.yedek_al(yollar["DB"], ayar, yollar["YEDEK"])
                        if basarili:
                            ayar["son_yedekleme_gunu"] = bugun_str
                            SistemMotoru.ayarlari_kaydet(yollar["AYARLAR"], ayar)
        except Exception as e:
            logging.error(f"_zamanlanmis_yedek_dongusu hatasi: {e}")
        time.sleep(60)

threading.Thread(target=_zamanlanmis_yedek_dongusu, daemon=True).start()


# =====================================================================
# STATİK DOSYALAR VE TEMPLATE YÖNETİMİ
# =====================================================================
def resource_path_api(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

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
    return templates.TemplateResponse(request=request, name="index.html", context={"ts": int(time.time())}, headers=headers)

@app.get('/style.css')
def read_style():
    return FileResponse(resource_path_api(os.path.join('frontend', 'style.css')))

@app.get('/lucide.min.js')
def read_lucide():
    return FileResponse(resource_path_api(os.path.join('frontend', 'lucide.min.js')))
