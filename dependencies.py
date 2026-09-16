from sistem_motoru import SistemMotoru
from veritabani import VeritabaniYoneticisi

yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
db = VeritabaniYoneticisi(yollar["DB"])
ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])

islem_loglari = []

def islem_logla(seviye, islem, mesaj):
    if seviye.lower() == "hata":
        import logging
        logging.error(f"{islem} - {mesaj}")
    else:
        import logging
        logging.info(f"{islem} - {mesaj}")
    islem_loglari.append({"seviye": seviye, "islem": islem, "mesaj": mesaj})
    if len(islem_loglari) > 100:
        islem_loglari.pop(0)

# Job management definitions from api.py could go here or in a separate file, but for now we'll put them in dependencies so routes can access them.
import uuid
import datetime

GLOBAL_ISLEMLER = {}

def create_job(toplam=100):
    job_id = str(uuid.uuid4())
    GLOBAL_ISLEMLER[job_id] = {
        "durum": "basladi",
        "mesaj": "İşlem başlatılıyor...",
        "tamamlanan": 0,
        "toplam": toplam,
        "baslangic": datetime.datetime.now()
    }
    return job_id

def update_job(job_id, durum, mesaj, tamamlanan=None, hata=None):
    if job_id in GLOBAL_ISLEMLER:
        GLOBAL_ISLEMLER[job_id]["durum"] = durum
        if mesaj:
            GLOBAL_ISLEMLER[job_id]["mesaj"] = mesaj
        if tamamlanan is not None:
            GLOBAL_ISLEMLER[job_id]["tamamlanan"] = tamamlanan
        if hata:
            GLOBAL_ISLEMLER[job_id]["hata"] = hata
            
def get_job(job_id):
    return GLOBAL_ISLEMLER.get(job_id, None)


islem_durumlari = GLOBAL_ISLEMLER
