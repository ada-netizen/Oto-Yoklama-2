import urllib.request
import webbrowser
import threading
import hashlib
import json
import os
import subprocess
import tempfile
from tkinter import messagebox
from packaging.version import InvalidVersion, Version
from sistem_motoru import SistemMotoru


def surum_parse(surum):
    """v1.9 ve v1.10 gibi sürümleri doğru sırada karşılaştırır."""
    temiz_surum = str(surum).strip().lower().removeprefix("v")
    return Version(temiz_surum)


def sha256_hesapla(dosya_yolu):
    ozet = hashlib.sha256()
    with open(dosya_yolu, "rb") as dosya:
        for parca in iter(lambda: dosya.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest().lower()


def guncelleme_paketi_indir(manifest_url, hedef_klasor=None):
    """Manifestteki installer'ı indirir ve SHA-256 eşleşmesini doğrular."""
    with urllib.request.urlopen(manifest_url, timeout=10) as cevap:
        manifest = json.loads(cevap.read().decode("utf-8"))
    url = manifest["installer_url"]
    beklenen_hash = manifest["sha256"].lower()
    klasor = hedef_klasor or tempfile.gettempdir()
    hedef = os.path.join(klasor, "Elektronik_Okul_V2.0_guncelleme.exe")
    urllib.request.urlretrieve(url, hedef)
    if sha256_hesapla(hedef) != beklenen_hash:
        os.remove(hedef)
        raise ValueError("Güncelleme paketi SHA-256 doğrulamasından geçemedi.")
    return hedef, manifest["version"]

class GuncellemeMotoru:
    @staticmethod
    def kontrol_et(mevcut_versiyon):
        versiyon_url = "https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/versiyon.txt"
        manifest_url = "https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/update_manifest.json"
        indirme_linki = "https://github.com/ada-netizen/yoklama_otomasyonu/releases/latest"

        def islem():
            try:
                # İnternete bağlanıp en güncel sürüm numarasını çeker
                req = urllib.request.Request(manifest_url, headers={'Cache-Control': 'no-cache'})
                try:
                    with urllib.request.urlopen(req, timeout=3) as response:
                        manifest = json.loads(response.read().decode('utf-8'))
                except (OSError, json.JSONDecodeError):
                    with urllib.request.urlopen(versiyon_url, timeout=3) as response:
                        manifest = {"version": response.read().decode('utf-8').strip()}
                en_yeni_versiyon = manifest["version"]

                if surum_parse(en_yeni_versiyon) > surum_parse(mevcut_versiyon):
                        import time
                        time.sleep(1) # Kısa bir bekleme
                        import tkinter as tk
                        from tkinter import messagebox
                        root = tk.Tk()
                        root.withdraw() # Gizli pencere
                        cevap = messagebox.askyesno(
                            "Yeni Güncelleme Çıktı!",
                            f"Programın yeni bir sürümü bulundu!\n\n"
                            f"Sizin Sürümünüz: {mevcut_versiyon}\n"
                            f"Yeni Sürüm: {en_yeni_versiyon}\n\n"
                            f"Yeni sürümü (Tek tıklamalı güncel .exe dosyasını) indirmek ister misiniz?",
                            parent=root
                        )
                        if cevap:
                            yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
                            basarili, hata = SistemMotoru.yedek_al(yollar["DB"], {}, yollar["YEDEK"])
                            if not basarili:
                                messagebox.showerror("Güncelleme iptal edildi", f"Veri yedeği alınamadı: {hata}", parent=root)
                            elif "installer_url" not in manifest or "sha256" not in manifest:
                                webbrowser.open(indirme_linki)
                            else:
                                paket, _ = guncelleme_paketi_indir(manifest_url)
                                subprocess.Popen([paket])
                        root.destroy()
            except (OSError, InvalidVersion, KeyError, TypeError, ValueError, json.JSONDecodeError):
                # Manifest yayınlanana kadar güncelleme kontrolü sessizce atlanır.
                pass

        # Program açılışını yavaşlatmamak için arka planda başlatıyoruz
        threading.Thread(target=islem, daemon=True).start()


