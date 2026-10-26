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
import socket
from fastapi import Request, HTTPException, Depends

def yerel_ip_al() -> str:
    """Ana makinenin okul yerel ağındaki IPv4 adresini tespit eder."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def denetim_kaydi_ekle(kullanici_id, kullanici_adi, ad_soyad, modul, islem, detay, ip_adresi=""):
    """Admin panelinde gösterilmek üzere işlem denetim kaydı ekler."""
    try:
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.cursor.execute(
            """INSERT INTO islem_denetim_kayitlari 
               (kullanici_id, kullanici_adi, ad_soyad, modul, islem, detay, ip_adresi, tarih) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (kullanici_id, kullanici_adi, ad_soyad, modul, islem, detay, ip_adresi, simdi)
        )
        db.conn.commit()
    except Exception as e:
        logging.warning(f"Denetim kaydı eklenemedi: {e}")

def get_aktif_kullanici(request: Request):
    """İstek sahibinin kimliğini oturum token'ı üzerinden doğrular."""
    # Test ortamı veya geriye dönük uyumluluk bypass'ı
    if os.environ.get("TEST_BYPASS_AUTH") == "1":
        return {
            "id": 1,
            "kullanici_adi": "test_admin",
            "ad_soyad": "Test Süper Yöneticisi",
            "unvan": "Okul Müdürü",
            "rol": "SUPER_ADMIN",
            "super_admin_mi": 1,
            "izinler": {"ogrenci": True, "izin": True, "teblig": True, "terfi": True, "ihale": True, "admin": True},
            "aktif": 1
        }

    # Sistemde henüz hiç kullanıcı yoksa (İlk kurulum durumu)
    try:
        db.cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        if (db.cursor.fetchone()[0] or 0) == 0:
            return {
                "id": 0,
                "kullanici_adi": "kurulum_bekleniyor",
                "ad_soyad": "Kurulum Bekleniyor",
                "unvan": "Sistem",
                "rol": "SUPER_ADMIN",
                "super_admin_mi": 1,
                "izinler": {"ogrenci": True, "izin": True, "teblig": True, "terfi": True, "ihale": True, "admin": True},
                "aktif": 1
            }
    except Exception:
        pass

    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.headers.get("X-Session-Token"):
        token = request.headers.get("X-Session-Token").strip()
    elif request.cookies.get("session_token"):
        token = request.cookies.get("session_token").strip()
    elif request.query_params.get("token"):
        token = request.query_params.get("token").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Oturum açmanız gerekmektedir.")

    try:
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.cursor.execute("""
            SELECT k.id, k.kullanici_adi, k.ad_soyad, k.unvan, k.rol, k.izinler, 
                   k.super_admin_mi, k.aktif, o.gecerlilik_tarihi, o.token
            FROM kullanici_oturumlar o
            JOIN kullanicilar k ON o.kullanici_id = k.id
            WHERE o.token = ?
        """, (token,))
        row = db.cursor.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Geçersiz veya sonlandırılmış oturum.")

        k_id, k_adi, ad_soyad, unvan, rol, izinler_str, super_mi, aktif, gecerlilik, t_val = row

        if not aktif:
            raise HTTPException(status_code=403, detail="Hesabınız dondurulmuştur. Lütfen sistem yöneticisiyle iletişime geçiniz.")

        if gecerlilik and gecerlilik < simdi:
            db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE token = ?", (token,))
            db.conn.commit()
            raise HTTPException(status_code=401, detail="Oturum süreniz dolmuştur. Lütfen tekrar giriş yapınız.")

        # Son aktiviteyi güncelle
        client_ip = request.client.host if request.client else ""
        db.cursor.execute("UPDATE kullanici_oturumlar SET son_aktivite = ?, ip_adresi = ? WHERE token = ?", (simdi, client_ip, token))
        db.cursor.execute("UPDATE kullanicilar SET son_islem = ? WHERE id = ?", (simdi, k_id))
        db.conn.commit()

        izinler = {}
        if izinler_str:
            try:
                izinler = json.loads(izinler_str)
            except Exception:
                pass

        return {
            "id": k_id,
            "kullanici_adi": k_adi,
            "ad_soyad": ad_soyad,
            "unvan": unvan,
            "rol": rol,
            "izinler": izinler,
            "super_admin_mi": bool(super_mi),
            "aktif": bool(aktif),
            "token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"get_aktif_kullanici hatası: {e}")
        raise HTTPException(status_code=401, detail="Oturum doğrulama hatası.")

def yetki_gerekli(modul_adi: str):
    """Belirtilen modüle erişim yetkisini denetleyen FastAPI bağımlılığı."""
    def _denetle(kullanici = Depends(get_aktif_kullanici)):
        if kullanici.get("super_admin_mi"):
            return kullanici
        izinler = kullanici.get("izinler") or {}
        if izinler.get(modul_adi) is True:
            return kullanici
        raise HTTPException(
            status_code=403, 
            detail=f"Bu işlem için '{modul_adi}' modül yetkiniz bulunmamaktadır."
        )
    return _denetle


def is_yerel_istek(request: Optional[Request]) -> bool:
    """İsteğin ana bilgisayardan (localhost / masaüstü) mi yoksa ağdaki uzak istemciden mi geldiğini tespit eder."""
    if not request or not request.client:
        return True
    host = request.client.host
    return host in ("127.0.0.1", "localhost", "::1", "testclient")

