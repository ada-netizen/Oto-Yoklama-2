import urllib.request
import webbrowser
import threading
from tkinter import messagebox

class GuncellemeMotoru:
    @staticmethod
    def kontrol_et(mevcut_versiyon, root):
        versiyon_url = "https://raw.githubusercontent.com/ada-netizen/Yoklama-Otomasyonu/refs/heads/main/versiyon.txt"
        indirme_linki = "https://github.com/ada-netizen/yoklama_otomasyonu/releases/latest"

        def islem():
            try:
                # İnternete bağlanıp en güncel sürüm numarasını çeker
                req = urllib.request.Request(versiyon_url, headers={'Cache-Control': 'no-cache'})
                with urllib.request.urlopen(req, timeout=3) as response:
                    en_yeni_versiyon = response.read().decode('utf-8').strip()

                    # Eğer internetteki sürüm (Örn: v1.1), bizimkinden (v1.0) büyükse uyar
                    if en_yeni_versiyon > mevcut_versiyon:
                        # Uyarıyı ana arayüzü kilitlemeden ekrana basar
                        root.after(1000, lambda: GuncellemeMotoru.uyari_goster(mevcut_versiyon, en_yeni_versiyon, indirme_linki))
            except:
                # İnternet yoksa veya link hatalıysa programı ASLA çökertmez, sessizce çalışmaya devam eder
                pass 

        # Program açılışını yavaşlatmamak için arka planda başlatıyoruz
        threading.Thread(target=islem, daemon=True).start()

    @staticmethod
    def uyari_goster(mevcut, yeni, link):
        cevap = messagebox.askyesno(
            "Yeni Güncelleme Çıktı!",
            f"Programın yeni bir sürümü bulundu!\n\n"
            f"Sizin Sürümünüz: {mevcut}\n"
            f"Yeni Sürüm: {yeni}\n\n"
            f"Yeni sürümü (Tek tıklamalı güncel .exe dosyasını) indirmek ister misiniz?"
        )
        if cevap:
            webbrowser.open(link)
