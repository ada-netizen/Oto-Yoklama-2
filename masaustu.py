import os
import sys
import json
import time
import glob
import socket
import ctypes
import logging
import threading
import multiprocessing
import urllib.request
from pathlib import Path

import webview
import uvicorn

# ─────────────────────────────────────────────
# 1. LOGGING AYARI
# ─────────────────────────────────────────────
def logging_ayarla() -> None:
    """Konsol ve dosya handler'larıyla logging'i başlatır.
    LOG_LEVEL ortam değişkeni ile seviye ayarlanabilir:
        set LOG_LEVEL=DEBUG   → ayrıntılı çıktı
        set LOG_LEVEL=WARNING → yalnızca uyarılar
    Varsayılan: INFO
    """
    seviye_adi = os.environ.get("LOG_LEVEL", "INFO").upper()
    seviye = getattr(logging, seviye_adi, logging.INFO)
    logging.basicConfig(
        level=seviye,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log", encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
    logging.info(f"Logging başlatıldı (seviye={seviye_adi})")

logging_ayarla()

# Beklenmedik çöküşleri ayrı bir crash.log'a yönlendir
sys.stderr = open('crash.log', 'w', encoding='utf-8')
sys.stdout = open('crash.log', 'a', encoding='utf-8')

# Windows görev çubuğu gruplama kimliği
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('adanetizen.otoyoklama.v2')
except Exception:
    pass

# ─────────────────────────────────────────────
# 2. KAYNAK YOLU
# ─────────────────────────────────────────────
def resource_path(relative_path: str) -> str:
    """PyInstaller paketiyle çalışırken sys._MEIPASS'ı, geliştirme ortamında
    ise bu dosyanın bulunduğu klasörü temel alarak mutlak yol döndürür.
    os.path.abspath('.') yerine __file__ kullanmak çalışma dizinine bağımlılığı kaldırır.
    """
    try:
        base = Path(sys._MEIPASS)
    except AttributeError:
        base = Path(__file__).parent
    return str(base / relative_path)


# ─────────────────────────────────────────────
# 3. UYGULAMA SABİTLERİ
# ─────────────────────────────────────────────
from api import app
from sistem_motoru import SistemMotoru

_yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
PENCERE_DOSYASI = os.path.join(_yollar["ANA"], "pencere_durumu.json")
VARSAYILAN_DURUM = {"width": 1280, "height": 800, "x": None, "y": None, "maximized": False}

# Sunucu referansları (graceful shutdown için)
_sunucu: uvicorn.Server | None = None
_sunucu_thread: threading.Thread | None = None

# Pencere durumu takibi
_son_durum = {"maximized": False}


# ─────────────────────────────────────────────
# 4. YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────
def pencere_durumu_yukle() -> dict:
    """Daha önce kaydedilmiş pencere durumunu okur.
    Bozuk veya mantıksız değerlerde güvenli varsayılana döner.
    """
    try:
        with open(PENCERE_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)

        genislik  = durum.get("width",     VARSAYILAN_DURUM["width"])
        yukseklik = durum.get("height",    VARSAYILAN_DURUM["height"])
        x         = durum.get("x")
        y         = durum.get("y")
        maximized = bool(durum.get("maximized", False))

        if not (400 <= genislik  <= 6000): genislik  = VARSAYILAN_DURUM["width"]
        if not (300 <= yukseklik <= 4000): yukseklik = VARSAYILAN_DURUM["height"]

        # Ekran dışı veya geçersiz konum → işletim sistemine bırak
        if x is None or y is None or x < -50 or y < -50 or x > 10000 or y > 10000:
            x, y = None, None

        return {"width": genislik, "height": yukseklik, "x": x, "y": y, "maximized": maximized}
    except Exception as e:
        logging.error(f"pencere_durumu_yukle hatasi: {e}")
        return dict(VARSAYILAN_DURUM)


def pencere_durumu_kaydet(pencere) -> None:
    """Program kapanırken son pencere durumunu diske yazar."""
    try:
        durum = {
            "width":     pencere.width,
            "height":    pencere.height,
            "x":         pencere.x,
            "y":         pencere.y,
            "maximized": _son_durum["maximized"],
        }
        with open(PENCERE_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(durum, f)
    except Exception as e:
        logging.error(f"pencere_durumu_kaydet hatasi: {e}")
        # Kaydetme başarısız olursa program kapanışını asla engellemesin


def port_dinleniyor_mu(host: str, port: int) -> bool:
    """Verilen host:port çiftine TCP bağlantısı açılıp açılmadığını test eder."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def api_zaten_calisiyor_mu() -> bool:
    """8000 portunda *kendi* API'mizin yanıt verip vermediğini kontrol eder.
    'Bağlantı reddedildi' ile 'farklı bir uygulama yanıt verdi' durumlarını
    ayırt etmek için /ayarlar-getir ucuna istek atılır.
    """
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/ayarlar-getir", timeout=1) as r:
            return r.status == 200
    except urllib.error.URLError:
        # Bağlantı reddedildi veya zaman aşımı → API çalışmıyor
        return False
    except Exception as e:
        logging.debug(f"api_zaten_calisiyor_mu beklenmedik hata: {e}")
        return False


def gecici_dosyalari_temizle() -> None:
    """Önceki çalışmadan kalan geçici dosyaları siler."""
    for desen in ("temp_ogr_*", "temp_dev_*", "temp_personel_*"):
        for dosya in glob.glob(desen):
            try:
                if os.path.isfile(dosya):
                    os.remove(dosya)
            except OSError as e:
                logging.warning(f"Gecici dosya silinemedi ({dosya}): {e}")


# ─────────────────────────────────────────────
# 5. SUNUCU YÖNETİMİ
# ─────────────────────────────────────────────
def sunucuyu_baslat() -> None:
    """FastAPI/Uvicorn sunucusunu bu thread'de çalıştırır.
    Port zaten kullanımdaysa sessizce durur; program çökmez.
    """
    global _sunucu
    try:
        config  = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="critical")
        _sunucu = uvicorn.Server(config)
        _sunucu.run()
    except Exception as e:
        import traceback
        logging.error(f"sunucuyu_baslat hatasi: {e}")
        logging.error(traceback.format_exc())


def api_sunucusunu_baslat(bekleme_suresi: float = 10.0) -> None:
    """Sunucuyu daemon thread'de başlatır ve hazır olana kadar bekler."""
    global _sunucu_thread

    _sunucu_thread = threading.Thread(
        target=sunucuyu_baslat,
        name="oto-yoklama-api",
        daemon=True
    )
    _sunucu_thread.start()

    bitis = time.monotonic() + bekleme_suresi
    while time.monotonic() < bitis:
        if port_dinleniyor_mu("127.0.0.1", 8000):
            logging.info("API sunucusu hazır.")
            return
        time.sleep(0.1)

    logging.warning(f"API sunucusu {bekleme_suresi:.0f} saniye içinde başlatılamadı; devam ediliyor.")


def guncelleme_motoru_baslat() -> None:
    """Versiyon dosyasini okuyarak guncelleme kontrolunu tetikler."""
    try:
        from guncelleyici import GuncellemeMotoru
        v_path = resource_path("versiyon.txt")
        logging.info(f"Versiyon dosyasi araniyor: {v_path}")
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as vf:
                mevcut_versiyon = vf.read().strip()
            logging.info(f"Okunan mevcut versiyon: {mevcut_versiyon}")
            GuncellemeMotoru.kontrol_et(mevcut_versiyon)
        else:
            logging.error(f"versiyon.txt BULUNAMADI! Yol: {v_path}")
    except Exception as e:
        logging.error(f"Guncelleme motoru baslatilamadi: {e}")


def zaten_calisiyor_uyar() -> None:
    """Programın başka bir kopyası çalışıyorsa kullanıcıyı bilgilendirip çıkar."""
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        "Zaten Çalışıyor",
        "Elektronik Okul V2.0 programı zaten arka planda veya başka bir pencerede çalışıyor.\n\n"
        "Lütfen açık olan pencereyi kullanın veya görev yöneticisinden kapatıp tekrar deneyin."
    )
    root.destroy()
    sys.exit(0)


# ─────────────────────────────────────────────
# 6. PENCERE OLUŞTURMA VE BAŞLATMA
# ─────────────────────────────────────────────
def arayuzu_baslat() -> None:
    """WebView penceresini oluşturur, olayları bağlar ve döngüyü başlatır."""
    kayitli = pencere_durumu_yukle()
    _son_durum["maximized"] = kayitli["maximized"]

    pencere = webview.create_window(
        title='Elektronik Okul Sistemi V2',
        url=f'http://127.0.0.1:8000/?t={int(time.time())}',
        width=kayitli["width"],
        height=kayitli["height"],
        x=kayitli["x"],
        y=kayitli["y"],
        min_size=(1000, 650),
        resizable=True,
        maximized=kayitli["maximized"],
        background_color='#0F172A',
    )

    # Pencere olayları
    def _maximize_oldu():
        _son_durum["maximized"] = True

    def _restore_oldu():
        _son_durum["maximized"] = False

    def _kapaniyor():
        """Graceful shutdown: durumu kaydet, API sunucusunu durdur."""
        pencere_durumu_kaydet(pencere)
        if _sunucu is not None:
            logging.info("API sunucusu durduruluyor...")
            _sunucu.should_exit = True
        if _sunucu_thread is not None and _sunucu_thread.is_alive():
            _sunucu_thread.join(timeout=5)
            if _sunucu_thread.is_alive():
                logging.warning("API thread 5 saniyede durmadı; zorla bırakılıyor.")

    pencere.events.maximized += _maximize_oldu
    pencere.events.restored  += _restore_oldu
    pencere.events.closing   += _kapaniyor

    cache_klasoru = os.path.join(os.getcwd(), 'webview_cache_v3')
    webview.start(private_mode=False, storage_path=cache_klasoru)


# ─────────────────────────────────────────────
# 7. GİRİŞ NOKTASI
# ─────────────────────────────────────────────
if __name__ == '__main__':
    multiprocessing.freeze_support()
    gecici_dosyalari_temizle()

    if port_dinleniyor_mu("127.0.0.1", 8000) and api_zaten_calisiyor_mu():
        zaten_calisiyor_uyar()
    else:
        api_sunucusunu_baslat()

    guncelleme_motoru_baslat()
    arayuzu_baslat()