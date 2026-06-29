import os
import json
import shutil
from datetime import datetime

class SistemMotoru:
    @staticmethod
    def klasorleri_ve_yollari_hazirla():
        """Programın ihtiyaç duyduğu tüm ana klasörleri oluşturur ve dosya yollarını döndürür."""
        ana_klasor = os.path.join(os.path.expanduser("~"), "YoklamaOtomasyonuVerileri")
        yollar = {
            "ANA": ana_klasor,
            "YEDEK": os.path.join(ana_klasor, "Yedekler"),
            "PDF": os.path.join(ana_klasor, "PDF_Ciktilari"),
            "MEB_LOGO": os.path.join(ana_klasor, "Logolar", "MEB"),
            "OKUL_LOGO": os.path.join(ana_klasor, "Logolar", "Okul"),
            "DB": os.path.join(ana_klasor, "yoklama_veritabani.db"),
            "AYARLAR": os.path.join(ana_klasor, "yoklama_ayarlar.json"),
            "LOG": os.path.join(ana_klasor, "sistem_hatalari.log")
        }
        
        # Klasörleri fiziksel olarak oluştur
        klasor_listesi = [yollar["ANA"], yollar["YEDEK"], yollar["PDF"], os.path.join(ana_klasor, "Logolar"), yollar["MEB_LOGO"], yollar["OKUL_LOGO"]]
        for k in klasor_listesi:
            if not os.path.exists(k):
                try: os.makedirs(k)
                except: pass
                
        return yollar

    @staticmethod
    def ayarlari_yukle(ayar_dosyasi):
        """JSON dosyasından ayarları RAM'e çeker."""
        if os.path.exists(ayar_dosyasi):
            try:
                with open(ayar_dosyasi, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return {}

    @staticmethod
    def ayarlari_kaydet(ayar_dosyasi, ayarlar):
        """Ayarları JSON dosyasına yazar."""
        try:
            with open(ayar_dosyasi, 'w', encoding='utf-8') as f: json.dump(ayarlar, f, ensure_ascii=False, indent=4)
        except: pass

    @staticmethod
    def yedek_al(db_yolu, ayarlar, varsayilan_yedek_klasoru):
        """Veritabanını kopyalayarak yedekler ve eski çöpleri temizler."""
        try:
            hedef_klasor = ayarlar.get("yedek_kayit_klasoru", varsayilan_yedek_klasoru)
            if not os.path.exists(hedef_klasor): os.makedirs(hedef_klasor)
            
            zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
            hedef_dosya = os.path.join(hedef_klasor, f"veritabani_yedek_{zaman}.db")
            
            shutil.copy(db_yolu, hedef_dosya)
            
            # Yedek aldıktan sonra arkadan çöp toplayıcıyı çalıştır
            SistemMotoru.eski_yedekleri_temizle(ayarlar, varsayilan_yedek_klasoru)
            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def eski_yedekleri_temizle(ayarlar, varsayilan_yedek_klasoru):
        """Kullanıcının belirlediği gün sayısından eski yedek dosyalarını siler."""
        sure_secimi = ayarlar.get("yedek_silme_suresi", "1 Ay Sonra")
        if sure_secimi == "Asla Silme": return
        
        limit_map = {"1 Hafta Sonra": 7, "1 Ay Sonra": 30, "3 Ay Sonra": 90, "6 Ay Sonra": 180, "1 Yıl Sonra": 365}
        limit_gun = limit_map.get(sure_secimi, 30)
        
        hedef_klasor = ayarlar.get("yedek_kayit_klasoru", varsayilan_yedek_klasoru)
        if not os.path.exists(hedef_klasor): return
        
        su_an = datetime.now()
        for dosya in os.listdir(hedef_klasor):
            if dosya.startswith("veritabani_yedek_") and dosya.endswith(".db"):
                dosya_yolu = os.path.join(hedef_klasor, dosya)
                try:
                    # Dosyanın oluşturulma zamanını kontrol et, eskiyse imha et
                    mtime = os.path.getmtime(dosya_yolu)
                    if (su_an - datetime.fromtimestamp(mtime)).days > limit_gun:
                        os.remove(dosya_yolu)
                except: pass
