# Proje Kuralları (Oto Yoklama 2)

Bu dosya, projede uyulması gereken temel kuralları barındırır. Projeye yeni bir özellik eklendiğinde veya kod geliştirilirken bu kurallara dikkat edilmelidir.

## 1. Hata Loglama (Error Logging)
- **Kapsamlı Loglama**: Programa eklenen **HER YENİ ÖZELLİK İÇİN** hata loglama özelliği eklenmesi ZORUNLUDUR.
- **Backend**: Her uç nokta (endpoint), işlem motoru sınıfı, utils fonksiyonu try-catch veya FastAPI genel exception handler kullanılarak sarmalanmalı ve olası tüm istisnalar `logging.error(...)` ile `app.log` dosyasına kaydedilmelidir.
- **Frontend**: Frontend kısmında gerçekleşen JavaScript hataları (Uncaught Exceptions ve Unhandled Promise Rejections), `fetch('/log-error')` aracılığıyla arka plana iletilmeli ve onların da `app.log` dosyasına kaydedilmesi güvence altına alınmalıdır.
- **Gizli Hata Bırakmama**: Hatalar, sessizce geçiştirilmemeli (e.g. `except: pass` kullanımından kaçınılmalı), loglara sebebiyle birlikte yazdırılmalıdır ki hata ayıklama süreci kesintiye uğramasın.

## 2. Ponytail / YAGNI Prensibi (En Küçük Tam Çözüm)
- **Gereksiz Kod Yazmama**: İstenmeyen soyutlamalar, kullanılmayacak konfigürasyonlar veya gereksiz sarmalayıcılar (wrapper) yazılmamalıdır.
- **Önce Mevcut Kod ve Standart Kütüphane**: Kod yazmadan önce projede var olan yardımcı fonksiyonlar ve standart kütüphane araçları kontrol edilmeli, tekerlek yeniden icat edilmemelidir.
- **En Kısa Temiz Çözüm**: İşi eksiksiz yapan en az satırlı ve yalın kod tercih edilmelidir. Gerekmedikçe harici bağımlılık eklenmemelidir.
- **Taviz Verilmeyecekler**: Hata yakalama/loglama, veri güvenliği ve doğrulama mekanizmaları asla kırpılmamalıdır.

## 3. Ekosistem, MCP ve Yetenek (Skill) Entegrasyonu
- **Veritabanı İşlemleri (`sqlite-concurrency-guard` & `sqlite-veritabani` MCP)**: Veritabanı sorguları yapılırken doğrudan MCP üzerinden güvenli okuma yapılabilir. Kod tarafında her zaman WAL modu ve kısa transaction prensibine uyulmalı, `database is locked` hatası önlenmelidir.
- **MEB Kural Doğrulama (`pytest-runner`)**: MEB devamsızlık hesaplamalarını (5 geç = 0.5 gün vb.) ilgilendiren her değişiklik sonrasında `pytest` test paketi çalıştırılmalı ve 26/26 testin geçtiği doğrulanmalıdır.
- **Excel Doğrulama (`excel-schema-validator`)**: Okul Excel listeleri işlenirken Türkçe karakter kodlama (mojibake) ve boşluk temizleme kurallarına uyulmalıdır.
- **Sürüm ve Paketleme (`semantic-release-sync` & `pyinstaller-desktop-packager`)**: Yeni sürüm derlenirken `versiyon.txt`, `update_manifest.json` ve `installer.iss` uyumlu tutulmalı, gizli importlar (hidden imports) korunmalıdır.
- **PDF Denetimi (`markitdown-pdf` MCP)**: `pdf_motoru.py` tarafından üretilen veli mektupları ve tutanakların içerik formatı gerektiğinde doğrulanmalıdır.

## 4. UI/UX Tasarım ve Arayüz Standartları
- **E2E ve Görsel Test (`playwright-e2e` MCP)**: Arayüz değişikliklerinde buton, form ve modal davranışları otomatik test edilir.
- **Bileşen Düzeni (`tailwind-ui-craftsman`)**: Tablo başlıkları sabit (sticky), form alanları erişilebilir ve eylem butonları (kaydet/sil) net görsel hiyerarşiye sahip olmalıdır.
- **İkon Standardı (`icon-design-system`)**: Anlaşılır SVG ikonlar kullanılmalı, tüm butonlarda `aria-label`/tooltip bulunmalı, harici ağır webfontlardan kaçınılmalıdır.
- **Geri Bildirim ve İlerleme (`ux-micro-interactions`)**: 300ms'den uzun süren işlemlerde (toplu PDF mektubu, Excel yükleme) ilerleme çubuğu veya yükleniyor göstergesi sunulmalı; işlem bitiminde toast bildirimi verilmelidir.
- **Erişilebilirlik ve Kontrast (`a11y-contrast-guard`)**: MEB devamsızlık durumları (özürlü, özürsüz, faaliyet, geç) için açık/koyu temalarda WCAG AA uyumlu yüksek kontrastlı renkler kullanılmalıdır.

