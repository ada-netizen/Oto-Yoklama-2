import urllib.request
import webbrowser
import threading
import hashlib
import json
import os
import subprocess
import tempfile
import ssl
import shutil
import logging
from tkinter import messagebox
from sistem_motoru import SistemMotoru


def surum_parse(surum):
    """v1.9, v1.10, v2.3.1.1 gibi surumleri dogru sirada karsilastirir.
    packaging.version yerine tuple karsilastirmasi kullanilir;
    boylece 4+ parcali versiyonlar da sorunsuz calisir.
    """
    temiz = str(surum).strip().lower().removeprefix("v")
    try:
        return tuple(int(x) for x in temiz.split("."))
    except ValueError:
        return (0,)

def sha256_hesapla(dosya_yolu):
    ozet = hashlib.sha256()
    with open(dosya_yolu, "rb") as dosya:
        for parca in iter(lambda: dosya.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest().lower()


def guncelleme_paketi_indir(manifest_url, hedef_klasor=None):
    """Manifestteki installer'ı SSL güvenli akışla indirir ve SHA-256 eşleşmesini doğrular."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req_manifest = urllib.request.Request(manifest_url, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req_manifest, timeout=10, context=ctx) as cevap:
        manifest = json.loads(cevap.read().decode("utf-8"))
        
    url = manifest["installer_url"]
    beklenen_hash = manifest["sha256"].lower()
    klasor = hedef_klasor or tempfile.gettempdir()
    v_name = manifest["version"].replace(".", "_")
    hedef = os.path.join(klasor, f"Elektronik_Okul_{v_name}_guncelleme.exe")

    # SSL sertifika hatası yaşamamak için context=ctx ile akışlı indirme yapıyoruz
    req_file = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_file, timeout=60, context=ctx) as response, open(hedef, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    if sha256_hesapla(hedef) != beklenen_hash:
        if os.path.exists(hedef):
            os.remove(hedef)
        raise ValueError("Güncelleme paketi SHA-256 doğrulamasından geçemedi.")
    return hedef, manifest["version"]

class GuncellemeMotoru:
    @staticmethod
    def kontrol_et(mevcut_versiyon):
        versiyon_url = "https://raw.githubusercontent.com/ada-netizen/Oto-Yoklama-2/refs/heads/main/versiyon.txt"
        manifest_url = "https://raw.githubusercontent.com/ada-netizen/Oto-Yoklama-2/refs/heads/main/update_manifest.json"
        indirme_linki = "https://github.com/ada-netizen/Oto-Yoklama-2/releases/latest"

        def islem():
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                # İnternete bağlanıp en güncel sürüm numarasını çeker
                req = urllib.request.Request(manifest_url, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
                manifest = None
                try:
                    with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                        manifest = json.loads(response.read().decode('utf-8'))
                except Exception as e:
                    logging.warning(f"Manifest okunamadi, versiyon.txt deneniyor: {e}")
                    with urllib.request.urlopen(versiyon_url, timeout=5, context=ctx) as response:
                        manifest = {"version": response.read().decode('utf-8').strip()}
                        
                if not manifest or "version" not in manifest:
                    return

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
                        else:
                            indirildi = False
                            if "installer_url" in manifest and "sha256" in manifest:
                                try:
                                    paket, _ = guncelleme_paketi_indir(manifest_url)
                                    subprocess.Popen([paket])
                                    os._exit(0) # Programi hemen kapat, boylece installer dosyalari uzerine yazabilsin
                                except Exception as err:
                                    logging.error(f"Otomatik paket indirme hatasi: {err}")

                            # Otomatik doğrudan indirme başarısız olduysa veya manifest yoksa tarayıcıyı aç
                            try:
                                target_url = manifest.get("installer_url") or indirme_linki
                                messagebox.showinfo(
                                    "İndirme Başlatılıyor",
                                    "Güncelleme kurulum sayfası tarayıcınızda açılıyor.\n\n"
                                    "Açılan sayfadan yeni kurulum dosyasını indirip kurabilirsiniz.",
                                    parent=root
                                )
                                try:
                                    os.startfile(target_url)
                                except Exception:
                                    webbrowser.open(target_url)
                            except Exception as e_tarayici:
                                logging.error(f"Tarayici acilamadi: {e_tarayici}")
                                
                    root.destroy()
            except Exception as e:
                logging.error(f"Guncelleme kontrol hatasi: {e}")

        # Program açılışını yavaşlatmamak için arka planda başlatıyoruz
        threading.Thread(target=islem, daemon=True).start()
