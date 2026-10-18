# Oto-Yoklama Yönetim Sistemi (Elektronik Okul) v2.3.4

Oto-Yoklama (Elektronik Okul), Türkiye Cumhuriyeti Millî Eğitim Bakanlığı (MEB) mevzuatına tam uyumlu; ortaöğretim ve temel eğitim kurumları için geliştirilmiş modern, hızlı, güvenilir bir **Öğrenci Devamsızlık, Personel Tebliğ ve Doğrudan Temin Yönetim Sistemidir**.

---

## 🚀 Yeni Nesil Yetenekler (v2.3.4)

### 📬 1. MEB Md. 36/4 Resmi Devamsızlık Mektubu Takip Çizelgesi
- **Resmi Tebligat Eşikleri:** 5., 15. ve 25. gün sınırına ulaşan öğrenciler mevzuat uyarınca anında gruplandırılır.
- **İnteraktif Takip Çizelgesi:** İki sütunlu sade arayüz; tıklanabilir öğrenci sayıları, açılır öğrenci detay listesi ve tek tıkla işaretlenen *"Mektup Gönderildi"* onay kutuları.
- **Uyarı Ünlemi (`⚠️`):** Henüz devamsızlık mektubu tebliğ edilmemiş öğrenciler olduğunda sayının yanında animasyonlu uyarı ünlemi belirir.
- **Art Arda 2 Gün Devamsızlık Alarmı:** Hafta içi veya hafta sonu atlamalı ardışık 2 gün özürsüz devamsızlık yapan öğrencilerin veli bildirim paneli.

### 👥 2. MEBBİS Entegre Personel Masası & Pano Yapıştırma
- **Çoklu Şablon Desteği:** MEBBİS Kadrolu Personel ve MEBBİS Görevlendirme Personel listelerini Excel dosyasından veya doğrudan **panodan kopyala-yapıştır** ile içe aktarma.
- **Doğal İsim ve Künye Standardı:** Türkçe karakter duyarlı akıllı dönüştürücü: İsimler ilk harf büyük, soyadlar tamamı büyük (`Ahmet YILMAZ`).
- **Hiyerarşik Görev Sıralaması:** Liste otomatik olarak yönetimsel önceliğe göre dizilir: `Müdür` ➔ `Müdür Başyardımcısı` ➔ `Müdür Yardımcısı` (alfabetik) ➔ `Öğretmenler` ➔ `Memur` ➔ `Diğer Personel`.
- **Mevzuat Sınıflandırması:** 657 Kadrolu, 4857 Sürekli İşçi, Sözleşmeli, İUP ve TYP personeli için otomatik mevzuat kuralları.
- **Sağlık İzinleri ve Kesinti Takibi:** Rapor kayıtları ve yılda 7 günü aşan sağlık raporlarından kaynaklı maaş/ek ders kesinti hesabı.

### 📋 3. 4734 Sayılı KİK Doğrudan Temin & İhale Motoru
- 22/d Doğrudan Temin süreçleri için Yaklaşık Maliyet Cetveli, Piyasa Fiyat Araştırması Tutanağı, Onay Belgesi ve Sözleşme şablonlarının otomatik üretimi.
- Kurum personel havuzundan tek tıkla komisyon başkanı ve piyasa araştırma görevlileri ataması.

### 📊 4. Proaktif Analitik & Dashboard
- **Devamsızlık Risk Piramidi:** Okul sağlık skoru ve risk grupları dağılımı.
- **Şampiyon Şubeler Sıralaması:** En az devamsızlık yapan sınıfların madalyalı sıralaması.
- **Okul Ortalaması Emsal Değeri:** Okul genel şube devamsızlık ortalaması baz alınarak şubelerin emsale göre devamsızlık farkı (`-3.6 G` avantaj rozeti).
- **Kademe Dağılımı ve Geç Kalma Alarmları:** 9-12. sınıf dağılımı ve 5 geç = 0.5 gün devamsızlık dönüşümleri.

### 🛠️ 5. Sistem Sağlığı, Teşhis ve Sıfır Kayıplı Online Backup
- **Canlı Sistem Teşhisi (`#y_teshis`):** Veritabanı bütünlüğü (`PRAGMA integrity_check`), WAL modu denetimi, RAM/CPU/Disk kullanımı ve üretilen evrak sayısı canlı izleme.
- **SQLite Online Backup API (`sqlite3.backup`):** Uygulama çalışırken `PRAGMA wal_checkpoint(TRUNCATE)` yapılarak tüm 7 tablonun (`ogrenciler`, `devamsizliklar`, `personel`, `saglik_raporlari`, `personel_rapor_kesinti`, `uretilen_evraklar`, `devamsizlik_mektup_takip`) ve `yoklama_ayarlar.json` dosyasının sıfır veri kaybı garantisiyle yedeklenmesi.

### ⌨️ 6. Hızlı Komuta Merkezi & Klavye Kısayolları
- **Command Palette (`Ctrl+K`):** Tüm modüllere, filtrelere ve işlemlere tek tuşla klavyeden arama yaparak erişim.
- **Klavye Kısayolları:** Sekmeler arası hızlı geçiş (`Ctrl+1` İzin Dilekçesi, `Ctrl+2` Personel Tebliğ, `Ctrl+3` Doğrudan Temin, `Ctrl+4` İstatistikler, `Ctrl+5` Sağlık İzinleri, `Ctrl+6` İletişim, `Ctrl+7` Yardım).

---

## 💻 Teknoloji Yığını

- **Backend:** `FastAPI` (Python 3.11+, Asenkron RESTful mimari)
- **Desktop Shell:** `pywebview` (Bağımsız, yerel Chromium WebView penceresi)
- **Veritabanı:** `SQLite 3` (WAL modunda çalışan `VeritabaniYoneticisi`, Online Backup API)
- **Raporlama:** `reportlab`, `PyPDF2`, `pandas`, `openpyxl`
- **Frontend:** HTML5, CSS3 Modern Flex/Grid, Vanilla JavaScript, Alpine.js, Lucide Icons

---

## 🛠 Kurulum ve Kullanım

### Normal Kullanıcılar İçin (Önerilen)
1. GitHub Releases sayfasından en güncel `Elektronik_Okul_V2.3.4_Setup.exe` kurulum dosyasını indirin.
2. Kurulum dosyasını çalıştırın.
3. Masaüstündeki **Elektronik Okul** kısayoluna çift tıklayın; arka plan API sunucusu otomatik başlatılarak modern masaüstü penceresi açılacaktır.

> [!NOTE]
> **Windows SmartScreen Uyarısı Hakkında**
> Kurulum sırasında *"Windows bilgisayarınızı korudu"* uyarısı alırsanız: **"Daha fazla bilgi"** linkine tıklayıp **"Yine de çalıştır"** butonuna basarak kuruluma devam edebilirsiniz.

### Geliştiriciler İçin (Kaynak Koddan Çalıştırma)
```bash
# 1. Depoyu klonlayın
git clone https://github.com/ada-netizen/Oto-Yoklama-2.git
cd Oto-Yoklama-2

# 2. Sanal ortamı etkinleştirin ve bağımlılıkları yükleyin
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Testleri çalıştırın
pytest

# 4. Masaüstü uygulamasını başlatın
python masaustu.py

# 5. Bağımsız EXE derlemek için
python build_exe.py
```

---

## 📁 Veri Saklama ve Güvenlik Sınırları

Tüm kullanıcı verileri, işletim sisteminizin kullanıcı dizini altında izole edilmiş güvenli klasörde saklanır:
`C:\Users\<KullanıcıAdınız>\YoklamaOtomasyonuVerileri\`

- Program silinse veya güncellense bile verileriniz **asla silinmez**.
- Hiçbir öğrenci veya personel verisi uzak bir sunucuya gönderilmez; sistem tamamen yerel çalışır.
