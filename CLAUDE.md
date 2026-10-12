# CLAUDE.md - Oto-Yoklama-2 Ajan Davranış ve Geliştirme Kılavuzu

Bu belge, Claude Code ve diğer yapay zekâ kodlama ajanlarının (Antigravity, Cursor, Codex) `Oto-Yoklama-2` projesinde çalışırken uyması gereken temel mimari kuralları, davranış standartlarını ve kalite kriterlerini belirler.

---

## 1. Temel Proje Vizyonu ve Mimari
* **Proje:** MEB İlkokul, Ortaokul ve Lise kurumları için geliştirilmiş modern, yerel (offline-first) Masaüstü Otomatik Yoklama ve İzin Takip Sistemi.
* **Teknoloji Yığını:**
  * **Backend:** Python 3.11+, FastAPI (REST API), Uvicorn, SQLite3 (WAL Modu).
  * **Masaüstü Katmanı:** `pywebview` (Edge Chromium WebView2).
  * **Frontend:** Vanilla HTML5, CSS3 (Modern CSS Değişkenleri, Glassmorphism & WCAG AA Kontrast), Vanilla JS (Bileşen ve sekme yönetimi).
  * **Raporlama:** ReportLab & PyPDF2 (Türkçe font destekli MEB resmi izin belgesi oluşturma).
  * **Veri İçe/Dışa Aktarım:** Pandas, openpyxl, xlrd, lxml (e-Okul sahte XLS/HTML ve gerçek ikili OLE2 XLS/XLSX dosyaları).

---

## 2. Ajan Davranış Kuralları (Behaviour & Senior Engineering)

### A. Tembel Kıdemli Geliştirici İlkesi (Ponytail / YAGNI)
* **En Küçük Tam Çözüm:** İşi çözen en yalın kodu yaz. İhtiyaç duyulmayan soyutlamalar, gereksiz kütüphane bağımlılıkları veya aşırı mühendislik ekleme.
* **Kalıcı Dökümantasyon Bütünlüğü:** Değiştirilmeyen mevcut yorum satırlarını, docstring'leri ve mimari açıklamaları koru.
* **Kırılgan Olmayan Değişiklik:** Var olan API endpoint'lerini, parametre adlarını ve veritabanı şemasını geriye dönük uyumsuzluk yaratacak şekilde değiştirme.

### B. MEB Mevzuat Kuralları (Dokunulmaz Mantık)
* **5 Geç Kalma = Yarım Gün Özürsüz:** 5 adet Geç (G) devamsızlık kaydı tam olarak 0.5 gün Özürsüz devamsızlığa dönüşür (`hesapla_devamsizlik` fonksiyonu).
* **Hafta Sonu Filtresi:** Cumartesi ve Pazar günlerine denk gelen devamsızlık kayıtları genel net toplama eklenmez (`gun_farki_hesapla`).
* **Devamsızlık Sınırları:** Özürsüz 10 gün, Toplam 30 gün yasal sınırları kontrol edilir ve arayüzde renkli rozetlerle vurgulanır.

### C. Dosya ve Veri Güvenliği
* **Excel Okuma:** Her zaman `ExcelMotoru.tabloyu_guvenli_oku` kullan. Asla doğrudan `pd.read_csv` veya salt `pd.read_excel` ile yetinme; dosya sihirli baytlarını (`\xd0\xcf\x11\xe0` OLE2 ikili XLS, `PK\x03\x04` ZIP XLSX) ve Türkçe encoding'leri (`cp1254`, `iso-8859-9`, `utf-8-sig`) gözet. Bu sayede `0xd0` UTF-8 çökmesi engellenir.
* **Veritabanı Eşzamanlılığı:** SQLite işlemlerinde WAL modunun (`PRAGMA journal_mode=WAL;`) devrede olduğundan emin ol. `sqlite-concurrency-guard` kurallarına uyarak bağlantıların `with` blokları veya `try...finally` ile kapatılmasını sağla.

---

## 3. UI/UX Yekpare Tasarım ve Frontend Standartları

### A. Yekpare Sekme Başlık Düzeni (52px Standartı)
* Tüm sekmelerin tepe paneli `.top-bar` sınıfı altında `52px` sabit yükseklikte olmalıdır (`height: 52px !important; min-height: 52px !important; max-height: 52px !important; padding: 0 16px !important; margin-bottom: 12px !important`).
* Sekmeler arası geçiş yapıldığında hiçbir dikey zıplama veya piksel kayması yaşanmamalıdır.
* Sekme butonlarına tıklandığında `core.js` içerisindeki `sekmeAc()` fonksiyonu simgeleri ve verileri tazelemelidir.

### B. Arama Kutuları ve Mercek İkonu Standardı
* Arama alanlarında `.input-with-icon` ve `input.search-input` sarmalayıcısı kullanılmalıdır.
* Mercek ikonu (`left: 11px`) ile placeholder metni kesinlikle çakışmamalı; metin ve placeholder girişi `padding-left: 36px !important` ile merceğin sağından başlamalıdır.

### C. Kurumsal Açılış (Splash) Ekranı
* Açılışta cam efektli kurumsal kart (`glassmorphism`), degrade kep amblemi (`graduation-cap`) ve dengeli tipografi sunulmalıdır.
* Sayfa ve öğrenci verileri yüklendiğinde 700ms içinde zarif bir şekilde opaklığı azalarak çalışma alanına geçilmelidir.

### D. Modern Onay Pencereleri & Mikro-Etkileşimler
* Tarayıcının ilkel `alert()` veya `confirm()` popup'ları yerine her zaman `core.js` içerisindeki `modernOnayGoster(baslik, mesaj, tip)` fonksiyonunu kullan.
* `Esc` tuşu açık modalları ve onay diyaloglarını kapatmalıdır.
* Uzun süren işlemlerde butonlarda spinner (`fa-spin`) göster, işlem bitiminde `bildirimGoster()` toast mesajı ile kullanıcıyı bilgilendir.

### E. Renk ve Kontrast Standartları (`a11y-contrast-guard`)
* Hem Aydınlık (Light) hem Koyu (Dark) temada WCAG 2.1 AA kontrast şartı (en az 4.5:1) sağlanmalıdır.
* Özürsüz: Koyu Kırmızı (`#991B1B` / `#FCA5A5`), Özürlü: Amber (`#92400E` / `#FDE68A`), Geç: Turuncu (`#9A3412` / `#FDBA74`).

### F. Kısayollar ve Performans (Power-User)
* `Ctrl+K`: Evrensel Komut Paletini (Command Palette) açar/kapatır.
* `F1` veya `Ctrl+/`: Klavye Kısayolları Rehberini (Cheat Sheet) açar.
* `Ctrl+Z`: Son devamsızlık aktarımını geri alır (Undo Snapshot).
* `Ctrl+S`: Aktif sekmedeki form veya ayarları kaydeder.
* `Ctrl+B`: Canlı veritabanı yedeği alır.
* `Ctrl+P`: Veli mektubu / izin dilekçesi PDF oluşturur.
* `Ctrl+T`: Aydınlık / Karanlık temayı değiştirir (WCAG AA).
* `Ctrl+Shift+R`: Raporlar penceresini açar.
* `Ctrl+O`: Öğrenci yönetimi penceresini açar.
* `F5` / `Ctrl+R`: Verileri yumuşak yeniler (Soft Refresh).
* `Ctrl+F` arama çubuğuna odaklanmalı, `Ctrl+D` dosya yükleme diyaloğunu açmalı, `Ctrl+1..7` sekmeler arası geçiş yapmalıdır.
* Arama filtrelerinde en az 180ms `debounce` kullanılmalı, tablo DOM render'larında `DocumentFragment` kullanılmalıdır.

### G. 3-Bölmeli Komuta Merkezi & MEB Bordeaux Hiyerarşisi
* **Sol Navigasyon Rayı (Sidebar Rail - Sıfır İtmeli Açılır Hover Overlay & 4 Kategori)**:
  * **Kapalı Durum (60px)**: Üstte ortalanmış MEB kep amblemi ve pencere boyunca inen dikey kenarlık (`border-right`), ortalanmış modül ikonları, dikey power butonları ve yeşil canlı nabız (`pulse-dot`) + tema anahtarı. Kategori başlıkları kapalıyken gizlidir.
  * **Hover Overlay (236px)**: Menü üzerine gelindiğinde sağa doğru akıcı şekilde açılır (`transition: 0.24s`); sabit 60px kapsayıcısı sayesinde yanındaki çalışma alanını (`.app-main-stage`) kesinlikle itmez veya kaydırmaz. Açıldığında 4 mantıksal kategori (`ÖĞRENCİ İŞLEMLERİ`, `PERSONEL İŞLEMLERİ`, `DOĞRUDAN TEMİN`, `SİSTEM & REHBER`) belirir (`Ctrl+O` ile Öğrenci Yönetimi modalı doğrudan açılır).
  * **Gölge & Taşmama**: Sağ tarafa derin, katmanlı bir gölge yayar (`box-shadow: 18px 0 38px -4px rgba(0,0,0,0.65)`). Yükseklik `100vh` ve dikeyde esnek nav çubuğu sayesinde alt butonlar ve göstergeler pencere dışına taşmaz.
* **Orta Liste Akışı (380px) & Ergonomik Filtre Rayı**:
  * **Tam Genişlik Arama (34px)**: Üstte tek başına ferah, tam genişlikte arama çubuğu (`#ent_arama`).
  * **Sabit 380px Genişlik & Açılır Eşik/Rozet Menüsü (32px)**: Asla genişlemeyen ve taşmayan 380px sabit panel (`min-width: 0 !important; max-width: 380px !important; width: 380px !important;`). Arama çubuğunun hemen altında canlı öğrenci sayaçlı kompakt açılır durum/rozet seçim menüsü (`#combo_esik_filtre` - `[🔵 Tümü]`, `[🚨 10G Ramak]`, `[⛔ 10G+ Aşan]`, `[📬 5G Mektup]`, `[⏳ 25G+ Toplam Risk]`, `[🌟 Kusursuz]`, `[🏥 Sağlık / Raporlu]`).
  * **Tümü Sola Yaslı Tablo Başlıkları**: Tüm sütun başlıkları (`Sınıf ↕`, `No ↕`, `Ad Soyad ↕`, `Özürsüz ↕`, `Özürlü ↕`) `text-align: left` ve `padding: 6px 4px` ile veri hücreleriyle tam hizada sola yaslanmıştır.
* **Sağ Tuval (Genişletilmiş Esnek Çalışma Alanı)**: Takvim başlığı iki katmanlı tam simetrik merkezleme (üstte ortalanmış Aylık/Yıllık seçici, altta ortalanmış ay navigasyonu) ile düzenlenmiştir; takvim ve önizleme dikeyde en tepeye çekilmiş (+90px net alan) durumdadır. Zenginleştirilmiş rozetler (yasal risk, kalan haklar, 5 geç kuralı analizi, hafta sonu birleştirme eğilimi, devamsızlık türü) ve 1-Tık WhatsApp kopyalama butonu öğrenciye çift tıklamayla açılan Yıllık Devamsızlık Karnesi (`yillik_modal`) içerisine entegre edilmiştir.
* **MEB Bordeaux Renk Hiyerarşisi**: `--meb-bordeaux: #881337`, `--meb-bordeaux-hover: #9F1239`, `--gradient-bordeaux`.

---

## 4. Test ve Kalite Güvencesi
* Yapılan her kod değişikliğinden sonra `.\venv\Scripts\pytest -q` komutunu çalıştırarak tüm **46/46** testin yeşil (PASSED) olduğunu doğrula.
* Mevcut testlerin hiçbirini silme veya devre dışı bırakma.
* Kod tabanı grafını senkronize tutmak için kritik değişikliklerden sonra `graphify extract . --code-only; graphify cluster-only .` çalıştır.

---

## 5. Proje Komutları
* **Testleri Çalıştırma:** `.\venv\Scripts\pytest -q`
* **Geliştirme Sunucusu:** `.\venv\Scripts\python api.py`
* **Masaüstü Uygulama:** `.\venv\Scripts\python masaustu.py`
* **Graphify Kod Grafı:** `graphify extract . --code-only; graphify cluster-only .`
* **Skill Arama & Ekleme:** `npx.cmd skills find <sorgu>` / `npx.cmd skills add <paket>`
