import webview
import threading
import multiprocessing
import uvicorn
import os
import time
import json
import socket
import urllib.request
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# api.py içindeki FastAPI motorumuzu (app) buraya çağırıyoruz
from api import app
from sistem_motoru import SistemMotoru
from sabitler import MEVCUT_VERSIYON

yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
PENCERE_DOSYASI = os.path.join(yollar["ANA"], "pencere_durumu.json")

VARSAYILAN_DURUM = {"width": 1280, "height": 800, "x": None, "y": None, "maximized": False}

# Pencere maximize/restore olaylarını takip etmek için basit bir hafıza
son_durum = {"maximized": False}


def pencere_durumu_yukle():
    """Daha önce kaydedilmiş pencere durumunu okur. Bozuk/mantıksız değerler
    (örn. farklı ve daha küçük bir ekrandan kalma ekran-dışı konum) varsa
    güvenli varsayılana döner, böylece pencere karışık/taşmış görünmez."""
    try:
        with open(PENCERE_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)

        genislik = durum.get("width", VARSAYILAN_DURUM["width"])
        yukseklik = durum.get("height", VARSAYILAN_DURUM["height"])
        x = durum.get("x")
        y = durum.get("y")
        maximized = bool(durum.get("maximized", False))

        if not (400 <= genislik <= 6000):
            genislik = VARSAYILAN_DURUM["width"]
        if not (300 <= yukseklik <= 4000):
            yukseklik = VARSAYILAN_DURUM["height"]

        # x/y makul değilse (negatif, çok büyük, farklı bir ekrandan kalma vb.)
        # işletim sistemine bırak; pencere ekranın ortasında güvenle açılsın
        if x is None or y is None or x < -50 or y < -50 or x > 10000 or y > 10000:
            x, y = None, None

        return {"width": genislik, "height": yukseklik, "x": x, "y": y, "maximized": maximized}
    except Exception as e:
        logging.error(f"pencere_durumu_yukle hatasi: {e}")
        return dict(VARSAYILAN_DURUM)


def pencere_durumu_kaydet(pencere):
    """Program kapanırken çağrılır, son pencere durumunu diske yazar."""
    try:
        durum = {
            "width": pencere.width,
            "height": pencere.height,
            "x": pencere.x,
            "y": pencere.y,
            "maximized": son_durum["maximized"],
        }
        with open(PENCERE_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(durum, f)
    except Exception as e:
        logging.error(f"pencere_durumu_kaydet hatasi: {e}")
        pass  # Kaydetme başarısız olursa program kapanışını asla engellemesin


def api_zaten_calisiyor_mu():
    """127.0.0.1:8000'de kendi API'mizin hâlihazırda çalışıp çalışmadığını kontrol eder
    (programın kapanmayan eski bir kopyası arka planda kalmış olabilir)."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/ayarlar-getir", timeout=1) as r:
            return r.status == 200
    except Exception as e:
        logging.error(f"api_zaten_calisiyor_mu hatasi: {e}")
        return False


def port_dinleniyor_mu(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def sunucuyu_baslat():
    # Arka planda gizlice API sunucusunu çalıştırır.
    # Port zaten kullanımdaysa (örn. programın kapanmayan eski bir kopyası) burada
    # sessizce durur; program çökmez, sadece yeni bir sunucu başlatmamış olur.
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="critical")
    except (SystemExit, OSError) as e:
        logging.error(f"sunucuyu_baslat hatasi (Port dolu olabilir): {e}")
        pass


if __name__ == '__main__':
    multiprocessing.freeze_support()
    # 1. 8000 portu zaten kullanımdaysa (programın önceki bir kopyası hâlâ açıksa)
    #    yeni bir sunucu başlatmaya ÇALIŞMA — bu, Windows'ta gördüğün
    #    "WinError 10048 / adres zaten kullanımda" çökmesine sebep oluyordu.
    if port_dinleniyor_mu("127.0.0.1", 8000) and api_zaten_calisiyor_mu():
        # Zaten çalışan kendi sunucumuz var, onu kullanmaya devam ederiz.
        pass
    else:
        t = threading.Thread(target=sunucuyu_baslat)
        t.daemon = True
        t.start()
        time.sleep(1)

    try:
        from guncelleyici import GuncellemeMotoru
        import sys
        def resource_path_versiyon(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
            
        with open(resource_path_versiyon("versiyon.txt"), "r", encoding="utf-8") as vf:
            mevcut_versiyon = vf.read().strip()
        GuncellemeMotoru.kontrol_et(mevcut_versiyon)
    except Exception as e:
        logging.error(f"Guncelleme motoru baslatilamadi: {e}")

    import sys
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    # 2. Tasarladığımız HTML dosyasının yolunu bul
    html_yolu = resource_path('index.html')

    # 3. Daha önce kaydedilmiş pencere durumunu yükle
    kayitli = pencere_durumu_yukle()
    son_durum["maximized"] = kayitli["maximized"]

    # 4. Modern masaüstü penceresini oluştur ve HTML'i içine göm!
    pencere = webview.create_window(
        title='Elektronik Okul Sistemi V2',
        url=html_yolu,
        width=kayitli["width"],
        height=kayitli["height"],
        x=kayitli["x"],
        y=kayitli["y"],
        min_size=(1000, 650),   # Program hiçbir zaman bu boyuttan küçük açılmasın (üst üste binmeyi önler)
        resizable=True,
        maximized=kayitli["maximized"],
        background_color='#0F172A'  # Yüklenirken siyah ekran vermesi için tema rengimiz
    )

    # 5. Pencere olaylarını dinleyerek durumu güncel tut ve kapanışta kaydet
    def _maximize_oldu():
        son_durum["maximized"] = True

    def _restore_oldu():
        son_durum["maximized"] = False

    def _kapaniyor():
        pencere_durumu_kaydet(pencere)

    pencere.events.maximized += _maximize_oldu
    pencere.events.restored += _restore_oldu
    pencere.events.closing += _kapaniyor

    # 6. Programı başlat
    cache_klasoru = os.path.join(os.getcwd(), 'webview_cache')
    webview.start(private_mode=False, storage_path=cache_klasoru)