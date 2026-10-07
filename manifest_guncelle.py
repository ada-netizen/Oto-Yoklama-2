import os
import json
import hashlib
import glob

def sha256_hesapla(dosya_yolu):
    """Verilen dosyanın SHA256 özetini hesaplar."""
    print(f"[{dosya_yolu}] için SHA256 hesaplanıyor, lütfen bekleyin...")
    ozet = hashlib.sha256()
    with open(dosya_yolu, "rb") as dosya:
        for parca in iter(lambda: dosya.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest().lower()

def main():
    # 1. Versiyonu oku
    if not os.path.exists("versiyon.txt"):
        print("HATA: versiyon.txt bulunamadı!")
        return

    with open("versiyon.txt", "r", encoding="utf-8") as f:
        versiyon = f.read().strip()
    
    print(f"Mevcut versiyon okundu: {versiyon}")

    # 2. Kurulum (Setup) dosyasını bul (installer klasöründeki en yeni .exe'yi seçer)
    setup_dosyalari = glob.glob(f"installer/Elektronik_Okul_*_Setup.exe")
    
    if not setup_dosyalari:
        print("HATA: installer klasöründe hiçbir Setup (.exe) dosyası bulunamadı!")
        print("Lütfen önce Inno Setup ile kurulum dosyasını oluşturun.")
        return

    # En son oluşturulan dosyayı seç (Eğer klasörde eski setuplar da varsa en yenisini bulur)
    en_yeni_setup = max(setup_dosyalari, key=os.path.getctime)
    setup_adi = os.path.basename(en_yeni_setup)
    print(f"Bulunan Kurulum Dosyası: {setup_adi}")

    # 3. SHA256 Şifresini hesapla
    sha256_sifresi = sha256_hesapla(en_yeni_setup)
    print(f"Hesaplanan SHA256: {sha256_sifresi}")

    # 4. İndirme URL'sini oluştur
    indirme_linki = f"https://github.com/ada-netizen/Oto-Yoklama-2/releases/download/{versiyon}/{setup_adi}"

    # 5. Manifest dosyasını oluştur
    manifest_verisi = {
        "version": versiyon,
        "installer_url": indirme_linki,
        "sha256": sha256_sifresi
    }

    with open("update_manifest.json", "w", encoding="utf-8") as mf:
        json.dump(manifest_verisi, mf, indent=4, ensure_ascii=False)

    print("--------------------------------------------------")
    print("BAŞARILI: update_manifest.json dosyası otomatik olarak GÜNCELLENDİ!")
    print("Artık yeni sürümünüzü GitHub'a yükleyebilirsiniz.")

if __name__ == "__main__":
    main()
