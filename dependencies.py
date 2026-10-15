import os
import json
import uuid
import logging
from datetime import datetime
from sistem_motoru import SistemMotoru
from veritabani import VeritabaniYoneticisi

yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
db = VeritabaniYoneticisi(yollar["DB"])
ayarlar = SistemMotoru.ayarlari_yukle(yollar["AYARLAR"])

islem_loglari = []

def islem_logla(seviye, islem, mesaj):
    """Kullanıcıya gösterilebilecek hassas olmayan işlem kaydı oluşturur."""
    if str(seviye).lower() == "hata":
        logging.error(f"İşlem Hatası: {islem} - {mesaj}")
    else:
        logging.info(f"İşlem Kaydı: {islem} - {mesaj}")

    kayit = {
        "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seviye": seviye,
        "islem": islem,
        "mesaj": mesaj,
    }
    islem_loglari.append(kayit)
    del islem_loglari[:-200]
    try:
        if yollar and "LOG" in yollar and yollar["LOG"]:
            with open(yollar["LOG"], "a", encoding="utf-8") as dosya:
                dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except OSError:
        pass


GLOBAL_ISLEMLER = {}

def create_job(mesaj="İşlem başlatılıyor...", yuzde=0, **kwargs):
    """Yeni bir arka plan görevi oluşturur ve job_id döndürür."""
    job_id = str(uuid.uuid4())
    GLOBAL_ISLEMLER[job_id] = {
        "durum": "basladi",
        "mesaj": mesaj,
        "yuzde": yuzde,
        "baslangic": datetime.now().isoformat(),
        **kwargs
    }
    return job_id

def update_job(job_id, durum, mesaj=None, yuzde=None, **kwargs):
    """Mevcut bir arka plan görevinin durumunu günceller."""
    if job_id not in GLOBAL_ISLEMLER:
        GLOBAL_ISLEMLER[job_id] = {}
    GLOBAL_ISLEMLER[job_id]["durum"] = durum
    if mesaj is not None:
        GLOBAL_ISLEMLER[job_id]["mesaj"] = mesaj
    if yuzde is not None:
        GLOBAL_ISLEMLER[job_id]["yuzde"] = yuzde
    for k, v in kwargs.items():
        GLOBAL_ISLEMLER[job_id][k] = v

def get_job(job_id):
    """Belirtilen job_id'nin durum nesnesini döndürür."""
    return GLOBAL_ISLEMLER.get(job_id, {"durum": "bulunamadi"})

islem_durumlari = GLOBAL_ISLEMLER

