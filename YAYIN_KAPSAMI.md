# Oto-Yoklama Yönetim Sistemi (Elektronik Okul) - Yayın Kapsamı (v2.3.4)

## 📌 1. Hedef Ürün ve Dağıtım Modeli

Windows 10 ve Windows 11 üzerinde bağımsız çalışan, son kullanıcının bilgisayarında Python veya harici bağımlılık kurulumu gerektirmeyen, tüm verileri yerel kullanıcı profilinde (`YoklamaOtomasyonuVerileri`) güvenle saklayan tek kullanıcılı masaüstü yönetim otomasyonu.

---

## 🛡️ 2. Bu Sürümde Garanti Edilen Temel Yetenekler

### A. MEB Devamsızlık ve Mevzuat Motoru (Md. 36/4 Uyumlu)
- **MEB Ortaöğretim Kurumları Yönetmeliği Madde 36/4 Tam Uyumu:**
  - **Resmi Tebligat Eşikleri:** 5., 15. ve 25. gün sınırına ulaşan öğrencilerin otomatik tespiti ve takip çizelgesi.
  - **Devamsızlık Mektubu Takip Çizelgesi:** İki sütunlu sade arayüz; tıklanabilir öğrenci sayısı, öğrenci detay modalı ve tek tıkla işaretlenebilen "Mektup Gönderildi" onay kutuları.
  - **Mektup Gönderim Uyarısı:** Mektubu gönderilmemiş öğrenci bulunan eşiklerin yanında dikkat çekici ünlem işareti (`⚠️`) ve araç ipucu.
  - **Ard Arda 2 Gün Uyarısı:** Hafta içi ve hafta sonu (Cuma-Pazartesi) atlamalı ardışık 2 gün özürsüz devamsızlık yapan öğrencilerin anlık veli bildirim paneli.
- **Hassas Devamsızlık Hesaplaması:**
  - 5 geç kalma = 0.5 gün yarım gün devamsızlık kuralı.
  - Özürlü, özürsüz, faaliyet, sevkli (`SV`) ve izinli kayıtlarının ayrıştırılması.
  - 10 gün özürsüz (sınıf tekrarı riski) ve 30 gün toplam devamsızlık kritik erken uyarıları.

### B. MEBBİS & Personel Yönetim Masası
- **Çoklu Şablon ve Pano Desteği:**
  - MEBBİS Kadrolu Personel Listesi (Excel ve panodan kopyala-yapıştır).
  - MEBBİS Görevlendirme Personel Listesi (Excel ve panodan kopyala-yapıştır).
  - e-Okul / Standart Personel formatları.
- **Doğal İsim ve Künye Formatlama:**
  - Adlar ilk harf büyük, soyadlar tamamı büyük biçimlendirmesi (`Ahmet YILMAZ`).
  - Hiyerarşik görev önceliğine göre otomatik listeleme: `Müdür` ➔ `Müdür Başyardımcısı` ➔ `Müdür Yardımcısı` (alfabetik) ➔ `Öğretmenler` ➔ `Memur` ➔ `Diğer Personel`.
- **Mevzuat Sınıflandırması:**
  - 657 DMK Kadrolu, 4857 Sürekli İşçi, Sözleşmeli, İUP ve TYP personeli için otomatik branş/kariyer/kademe doğrulama mantığı.
  - Sağlık izinleri takibi ve yılda 7 günü aşan raporların maaş/ek ders kesinti hesabı.

### C. 4734 Sayılı Doğrudan Temin & İhale Motoru
- Kamu İhale Kanunu (KİK) 22/d doğrudan temin süreçleri için Yaklaşık Maliyet Cetveli, Piyasa Fiyat Araştırması Tutanağı, İhale Onay Belgesi ve Sözleşme üretimi.
- Personel havuzundan otomatik komisyon üyesi ve piyasa araştırma görevlisi ataması.

### D. Proaktif Analitik Dashboard
- **Devamsızlık Risk Piramidi:** Okul sağlık skoru ve risk grupları dağılımı.
- **Şampiyon Şubeler Sıralaması:** En az devamsızlık yapan şubelerin madalyalı sıralaması.
- **Emsal Değer Çubuğu:** Okul genel şube devamsızlık ortalaması baz alınarak şubelerin emsale göre devamsızlık farkı (`-3.6 G` avantaj rozeti).
- **Kademe ve Trend Grafikleri:** 9, 10, 11, 12. kademe devamsızlık yoğunluğu ve aylık trend analizi.

### E. Sistem Sağlığı, Teşhis ve Sıfır Kayıplı Yedekleme
- **Sistem Sağlığı ve Teşhis Paneli (`#y_teshis`):** Veritabanı bütünlük kontrolü (`PRAGMA integrity_check`), WAL modu denetimi, RAM, CPU, Disk alanı ve üretilen toplam evrak sayısı canlı takibi.
- **SQLite Online Backup API (`sqlite3.backup`):** Uygulama çalışırken WAL checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`) yapılarak tüm 7 tablonun (`ogrenciler`, `devamsizliklar`, `personel`, `saglik_raporlari`, `personel_rapor_kesinti`, `uretilen_evraklar`, `devamsizlik_mektup_takip`) ve `yoklama_ayarlar.json` dosyasının sıfır veri kaybı garantisiyle yedeklenmesi.
- **Zamanlanmış Otomatik Yedekleme:** 1 Hafta, 1 Ay, 3 Ay periyotlarında otomatik arşivleme ve çöp toplama.

---

## 🔒 3. Veri Güvenliği ve Gizlilik Sınırları

1. **Tamamen Yerel Mimari:** Veriler hiçbir harici sunucuya veya bulut servisine gönderilmez.
2. **Korumalı Yerel Dizin:** Kullanıcı verileri `C:\Users\<Kullanıcı>\YoklamaOtomasyonuVerileri\` altında izole edilir; program güncellense veya kaldırılsa dahi veriler silinmez.
3. **Yerel API Kısıtlaması:** FastAPI arka ucu sadece `127.0.0.1` yerel döngü arabiriminde dinler; dış ağlara kapalıdır.
4. **Log Gizliliği:** Kişisel veriler (TC No, telefon, özel sağlık verisi vb.) log dosyalarına yazılmaz.

---

## 📦 4. Yayın Paketi ve Dağıtım Gereksinimleri

- **Kurulum Dosyası:** Inno Setup ile derlenmiş `Elektronik_Okul_V2.3.4_Setup.exe`.
- **Otomatik Güncelleme:** GitHub Releases üzerinden yeni sürüm çıktığında `update_manifest.json` üzerinden algılama ve kullanıcı onayıyla indirme.
- **Kabul Koşulu:** Temiz Windows 10/11 ortamında sıfır kurulum, veri aktarımı, PDF çıktısı alma ve yedekleme fonksiyonlarının hatasız çalışması.
