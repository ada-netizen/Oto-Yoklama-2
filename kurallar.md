# Proje Kuralları (Oto Yoklama 2)

Bu belge, `Oto-Yoklama-2` projesinde uyulması gereken temel mimari kuralları, veri işleme prensiplerini, arayüz standartlarını ve kalite kriterlerini belirler. Yeni bir özellik eklendiğinde, hata giderildiğinde veya kod yeniden düzenlendiğinde bu kurallara kesinlikle uyulmalıdır.

---

## 1. Hata Loglama (Error Logging)
- **Kapsamlı Loglama**: Programa eklenen **HER YENİ ÖZELLİK VE UÇ NOKTA İÇİN** hata loglama özelliği eklenmesi ZORUNLUDUR.
- **Backend**: Her uç nokta (endpoint), işlem motoru sınıfı ve yardımcı fonksiyon `try...except` blokları veya FastAPI genel exception handler kullanılarak sarmalanmalı; tüm istisnalar `logging.error(...)` ile `app.log` dosyasına kaydedilmelidir.
- **Frontend**: Frontend kısmında gerçekleşen JavaScript hataları (`window.onerror` ve `unhandledrejection`), `fetch('/log-error')` aracılığıyla arka plana iletilmeli ve `app.log` dosyasına yazılması güvence altına alınmalıdır.
- **Sessiz Hata Bırakmama**: Hatalar asla `except: pass` ile sessizce yutulmamalı; sebebi ve stack trace bilgisiyle loglanmalıdır.

---

## 2. Ponytail / YAGNI Prensibi (En Küçük Tam Çözüm)
- **Gereksiz Kod ve Aşırı Mühendislik Yasağı**: İhtiyaç duyulmayan soyutlamalar, kullanılmayacak konfigürasyonlar veya gereksiz sarmalayıcılar (wrapper) yazılmamalıdır.
- **Mevcut Kütüphane ve Kod Önceliği**: Kod yazmadan önce projede var olan fonksiyonlar ve standart kütüphane kontrol edilmeli, tekerlek yeniden icat edilmemelidir.
- **Dökümantasyon ve Yorum Bütünlüğü**: Değiştirilmeyen mevcut yorum satırları, docstring'ler ve mimari açıklamalar korunmalıdır.
- **Geriye Dönük Uyumluluk**: Var olan API uç noktaları, parametre isimleri ve veritabanı şeması geriye dönük uyumluluk bozulmadan korunmalıdır.

---

## 3. MEB Mevzuat Kuralları (Dokunulmaz Mantık)
- **5 Geç Kalma = 0.5 Gün Özürsüz**: 5 adet Geç (G) devamsızlık kaydı tam olarak 0.5 gün Özürsüz devamsızlığa dönüşür (`hesapla_devamsizlik` fonksiyonu).
- **Hafta Sonu Filtresi**: Cumartesi ve Pazar günlerine denk gelen devamsızlık kayıtları resmi devamsızlık toplamına dahil edilmez (`gun_farki_hesapla`).
- **Yasal Devamsızlık Sınırları**: Özürsüz 10 gün, toplam 30 gün yasal sınırları kontrol edilir; bu sınırları aşan öğrenciler arayüzde yüksek kontrastlı uyarı rozetleriyle (`status-pill`) vurgulanır.

---

## 4. Dosya, Excel ve Veri Güvenliği
- **Güvenli Excel Okuyucu**: Excel dosyaları işlenirken her zaman `ExcelMotoru.tabloyu_guvenli_oku` kullanılmalıdır.
  - Dosyanın ilk 8 baytı okunarak gerçek OLE2 ikili XLS (`\xd0\xcf\x11\xe0`) doğrudan `xlrd` motoruna yönlendirilmeli (böylece `0xd0` UTF-8 çökmesi engellenir),
  - ZIP tabanlı XLSX (`PK\x03\x04`) `openpyxl` motoruna yönlendirilmeli,
  - Sahte XLS (HTML tablo) için `lxml` kullanılmalı,
  - CSV ve metin formatları için Türkçe karakter kodlamaları (`cp1254`, `iso-8859-9`, `utf-8-sig`, `utf-8`) sırasıyla denenmelidir.
- **Veritabanı Eşzamanlılığı (`sqlite-concurrency-guard`)**: SQLite veritabanı her zaman WAL modunda (`PRAGMA journal_mode=WAL;`) çalışmalı, bağlantılar `with` veya `try...finally` blokları ile güvenle kapatılarak `database is locked` hataları önlenmelidir.

---

## 5. UI/UX Yekpare Tasarım Standartları
- **Sekmeler Arası 52px Başlık Bandı**:
  - Tüm sekmelerde tepe başlık alanı `.top-bar` sınıfı altında `52px` sabit yükseklikte olmalıdır (`height: 52px !important; min-height: 52px !important; max-height: 52px !important; padding: 0 16px !important; margin-bottom: 12px !important`).
  - Sekmeler arası geçişlerde dikey zıplama veya piksel kayması yaşanmamalıdır.
- **Arama Kutusu ve İkon Hizalaması**:
  - Arama alanları `.input-with-icon` ve `input.search-input` sarmalayıcısıyla tanımlanmalıdır.
  - Sol büyüteç simgesi `left: 11px` ile sabitlenmeli; placeholder ve giriş metni kesinlikle `padding-left: 36px !important` ile merceğin sağından başlamalıdır.
- **Kurumsal Açılış (Splash) Ekranı**:
  - Açılışta cam efektli kurumsal kart (`glassmorphism`), kep amblemi (`graduation-cap`) ve dengeli tipografi sunulmalıdır.
  - Arka planda veriler yüklendikten sonra 700ms içinde zarif bir animasyonla (`.splash-overlay.gizli`) çalışma alanına geçilmelidir.
- **Modern Onay Pencereleri**:
  - Tarayıcının ilkel `alert()` veya `confirm()` pencereleri yerine `core.js` içerisindeki modern cam efektli `modernOnayGoster(baslik, mesaj, tip)` kullanılmalıdır.
  - `Esc` tuşu tüm modalları ve onay diyaloglarını kapatmalıdır.
- **Erişilebilirlik ve Kontrast (`a11y-contrast-guard`)**:
  - Hem Aydınlık hem Karanlık temada WCAG 2.1 AA kontrast şartı (en az 4.5:1) sağlanmalıdır.
- **Sol Gezinme Rayı (Sidebar Rail) Kategorizasyonu**:
  - Sol menü 4 mantıksal gruba ayrılmalıdır: `ÖĞRENCİ İŞLEMLERİ`, `PERSONEL İŞLEMLERİ`, `DOĞRUDAN TEMİN`, `SİSTEM & REHBER`.
  - Menü kapalıyken (60px) kategori başlıkları sıfır yükseklikle gizlenmeli; fare üzerine gelip menü yana açıldığında (236px) şık mikro-tipografiyle görünür hale gelmelidir.
- **Tam Genişlik Arama ve Tek Satır Yatay Çip Rayı**:
  - Üst arama çubuğu (`#ent_arama`) tek başına tam genişlikte konumlandırılmalı; yanına buton/dropdown konulup arama alanı daraltılmamalıdır.
  - Risk eşik rozetleri arama çubuğunun hemen altında tek satırlık (28px) yatay rayda (`.esik-kaydirma-kapsayici`) yer almalıdır. Asla 2. satıra geçmemeli (`flex-wrap: nowrap !important;`), taşma durumunda fare tekerleğiyle pürüzsüz yatay kaymalıdır.
- **Tablo Başlıkları ve Hücre Aralıkları**:
  - Tablo sütun başlıkları (`th`) üzerinde `text-overflow: ellipsis` kullanılmamalı, başlıklar tam okunabilir olmalıdır.
  - Sütun hücre yatay dolgusu (`padding`) 4px olarak tutulmalı, dikey ve yatay alan verimliliği korunmalıdır.

---

## 6. Geri Alma (Undo) ve Canlı Yedekleme Standartları
- **Son İşlemi Geri Alma (Snapshot Rollback)**:
  - Toplu öğrenci veya devamsızlık aktarımları öncesinde `veritabani.py` otomatik olarak önceki durumun anlık görüntüsünü (`_son_snapshot`) saklamalıdır.
  - Hatalı bir aktarım yapıldığında `/api/son-islemi-geri-al` uç noktası ve arayüzdeki "Geri Al" butonu ile tek tıkla önceki duruma dönülebilmelidir.
- **Canlı SQLite Online Backup**:
  - Veritabanı yedeklemeleri kilitlenme ve veri bozulmasını önlemek için SQLite'ın yerel `backup` API'si (`db.yedekle()`) üzerinden çalışmalıdır.

---

## 7. Performans ve Klavye Ergonomisi (Power-User)
- **Arama Tuş Geciktirmesi (Debounce)**:
  - Metin filtreleme kutularında (`#ent_arama`, `#txt_personel_ara`) en az `180ms` debounce uygulanmalı, her harfte anında DOM render'ı tetiklenmemelidir.
- **Toplu DOM Ekleme (DocumentFragment)**:
  - Tablo satırları DOM'a tek tek (`appendChild`) değil, `DocumentFragment` içinde toplanarak tek bir işlemde eklenmelidir.
- **Evrensel Kısayollar**:
  - `Ctrl + K`: Evrensel Komut Paletini (Command Palette) açma/kapatma.
  - `F1` veya `Ctrl + /`: Klavye Kısayolları Rehberi (Cheat Sheet) modalını açma.
  - `Ctrl + F`: Aktif arama kutusuna odaklanma ve metni seçme.
  - `Ctrl + D`: Devamsızlık Excel dosya seçicisini açma.
  - `Ctrl + Z`: Son yapılan devamsızlık aktarımını geri alma (Undo Snapshot).
  - `Ctrl + S`: Aktif sekmedeki formu/ayarları kaydetme.
  - `Ctrl + B`: Canlı SQLite veritabanı yedeği alma.
  - `Ctrl + P`: Seçili öğrenci veli mektubu / boş izin dilekçesi PDF oluşturma.
  - `Ctrl + T`: Aydınlık / Karanlık temayı değiştirme (WCAG AA).
  - `Ctrl + Shift + R`: Devamsızlık raporları modalını açma.
  - `Ctrl + O`: Öğrenci yönetim modalını açma.
  - `F5` / `Ctrl + R`: Verileri yumuşak yenileme (Soft Refresh).
  - `Ctrl + 1..7`: Sekmeler arası hızlı geçiş (1: İzin, 2: Tebliğ, 3: İhale, 4: Dashboard, 5: Sağlık, 6: Ayarlar, 7: Yardım).
  - `Esc`: Açık modal, komut paleti ve onay pencerelerini kapatma.

---

## 8. Kritik Eşik Erken Uyarı Sistemi Standartları
- **MEB Mevzuatına Uygun 4 Eşik Grubu**:
  - `ramakkala_10`: 9.0 - 9.9 gün özürsüz devamsızlık yapanlar (Sınıf tekrarı öncesi acil uyarı).
  - `asanlar_10`: 10 gün ve üzeri özürsüz devamsızlık yapanlar.
  - `mektup_siniri_5`: 4.5 - 4.9 gün özürsüz devamsızlık yapanlar (1. Veli Mektubu eşiği).
  - `toplam_risk_25`: Toplam 25 gün ve üzeri devamsızlık yapanlar (30 gün genel sınırına yaklaşanlar).
- **Hızlı Veli Metni Kopyalama**:
  - Her riskli öğrenci satırında veliye gönderilecek standart bilgilendirme metnini tek tıkla panoya kopyalayan aksiyon butonu yer almalıdır.

---

## 9. Evrensel Komut Paleti (Command Palette) Standartları
- `Ctrl + K` veya üst çubuktaki "Komutlar" butonu ile tetiklenmeli, modal `Esc` veya dışına tıklama ile kapanmalıdır.
- Sistem komutları (eşikler, geri alma, canlı yedek, excel yükleme, tema değiştirme), canlı öğrenci araması ve personel araması tek çatı altında toplanmalıdır.
- Yön tuşları (`↑`, `↓`) ile seçim yapılmalı, `Enter` ile ilgili aksiyon çalıştırılmalıdır.

---

### 10. Test ve Kalite Güvencesi
- Yapılan her kod değişikliğinden sonra `.\venv\Scripts\pytest -q` çalıştırılmalı ve **46/46 testin** yeşil (PASSED) olduğu doğrulanmalıdır.
- Kritik mimari veya frontend değişikliklerinden sonra `graphify extract . --code-only; graphify cluster-only .` çalıştırılarak AST kod bağımlılık grafı güncel tutulmalıdır.
- **Sistem Sağlığı ve Teşhis Standartları**: `/sistem-teshis` uç noktası üzerinden SQLite bütünlüğü (`PRAGMA integrity_check`), WAL modu ve kayıt sayıları denetlenmeli; Yardım ve Kılavuz sekmesinden panoya tanı raporu kopyalanabilmelidir.

---

## 11. 3-Bölmeli Komuta Merkezi Düzeni & MEB Bordeaux Renk Sistemi
- **3-Bölmeli Mimari (`.app-layout`)**:
  - **1. Sol Navigasyon ve Durum Rayı (Sidebar Rail - Sıfır İtmeli Açılır Hover Overlay)**:
    - **Kapalı Ray Durumu (60px)**: Üstte ortalanmış MEB kep amblemi (`sidebar-emblem`) ve pencere boyunca uzanan dikey kenarlık (`border-right`), ortalanmış istasyon ikonları, dikey power-user butonları ve canlı yeşil durum nabzı (`pulse-dot`) ile tema anahtarı.
    - **Hover Overlay Durumu (236px)**: Menü üzerine gelindiğinde veya klavye odağında akıcı bir şekilde (`transition: 0.24s cubic-bezier(0.16, 1, 0.3, 1)`) 236px genişliğe ulaşır. 4 mantıksal kategori başlığı (`.sidebar-section-title`) altı çizili (`border-bottom: 1px solid var(--border)`) ve ferah aralıklarla ayrılmıştır.
    - **Sıfır İtme (Zero-Shift) & Taşmayan Footer**: Menü `.sidebar-rail-kapsayici` (sabit 60px) içinde `position: absolute` olarak sağa doğru genişler; yanındaki ana çalışma sahnesini (`.app-main-stage`) kesinlikle itmez. Alt panelde (`.sidebar-footer`) komut butonları tam satır genişliğinde sağa yaslı kısayol rozetleriyle (`margin-left: auto`) çakışmasız yer alır; gece/gündüz anahtarı (`40px × 22px`) ve 60 FPS SQLite nabız göstergesi menü dışına asla taşmaz.
  - **2. Orta Panel (Akıllı Liste Akışı - Sabit 380px)**: Asla genişlemeyen ve taşmayan sabit 380px genişlik (`width: 380px; min-width: 0 !important; max-width: 380px !important;`), tam genişlik arama kutusu (`#ent_arama`), canlı sayaçlı açılır durum/rozet seçim menüsü (`#combo_esik_filtre` - `[Tümü]`, `[🚨 10G Ramak]`, `[⛔ 10G+ Aşan]`, `[📬 5G Mektup]`, `[⏳ 25G+ Toplam]`, `[🌟 Kusursuz]`, `[🏥 Raporlu]`) ve sola yaslı tam metin sütun başlıkları.
  - **3. Sağ Panel (Genişletilmiş Detay & Takvim Tuvali - Esnek)**:
    - Takvim ve canlı PDF önizleme dikeyde en tepeye kaydırılarak net **+90px çalışma alanı** kazanmıştır; takvim başlığı iki katmanlı tam simetrik merkezleme (üstte ortalanmış Aylık/Yıllık seçici, altta ortalanmış ay navigasyonu) ile düzenlenmiştir. Öğrenci detayları yalnızca çift tıklama ile açılan Yıllık Devamsızlık Karnesi içinde toplanmıştır.
    - **Yıllık Devamsızlık Karnesi & Çeşitlendirilmiş Rozet Motoru (`yillik_modal`)**:
      - Öğrenciye listeden çift tıklama ile açılır.
      - Başlıkta doğrudan 1-tık WhatsApp metin kopyalama butonu (`[💬 WhatsApp Metni]`) yer alır.
      - Zenginleştirilmiş pedagojik rozetler: Yasal Risk (🚨 10G+ / ⚠️ 10G Ramak / 📬 5G Mektup / ⏳ 25G+ Toplam / ✅ Güvenli), Kalan Yasal Haklar (`🟢 Kalan Özürsüz`, `🛡️ Kalan Toplam`), MEB 5 Geç Kuralı Analizi (`⏱️ X Kez Geç Kalındı (${etki}G)`), Davranışsal Şablon (`🗓️ Hafta Sonu Birleştirme Eğilimi`), Devamsızlık Türü Dağılımı (`🏥 Sağlık Ağırlıklı` / `⚠️ İzinsiz Ağırlıklı` / `🌟 Kusursuz Katılım`).
- **MEB Bordeaux Renk Hiyerarşisi**:
  - Kurumsal vurgular ve birincil aksiyonlar için `--meb-bordeaux: #881337`, `--meb-bordeaux-hover: #9F1239` ve `--gradient-bordeaux: linear-gradient(135deg, #881337, #BE123C)`.
  - Derin Slate yüzeyler (`--bg-main: #0B1120`, `--bg-card-solid: #1E293B`) ve WCAG 2.1 AA kontrast şartı.
- **İnteraktif Devamsızlık Aktarımı Toast'ı**:
  - Devamsızlık aktarımı tamamlandığında açılan bildirimde doğrudan `↩️ Geri Al` butonu sunularak anında geri alma (Undo) imkanı sağlanmalıdır.

