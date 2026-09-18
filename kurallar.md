# Proje Kuralları (Oto Yoklama 2)

Bu dosya, projede uyulması gereken temel kuralları barındırır. Projeye yeni bir özellik eklendiğinde veya kod geliştirilirken bu kurallara dikkat edilmelidir.

## 1. Hata Loglama (Error Logging)
- **Kapsamlı Loglama**: Programa eklenen **HER YENİ ÖZELLİK İÇİN** hata loglama özelliği eklenmesi ZORUNLUDUR.
- **Backend**: Her uç nokta (endpoint), işlem motoru sınıfı, utils fonksiyonu try-catch veya FastAPI genel exception handler kullanılarak sarmalanmalı ve olası tüm istisnalar `logging.error(...)` ile `app.log` dosyasına kaydedilmelidir.
- **Frontend**: Frontend kısmında gerçekleşen JavaScript hataları (Uncaught Exceptions ve Unhandled Promise Rejections), `fetch('/log-error')` aracılığıyla arka plana iletilmeli ve onların da `app.log` dosyasına kaydedilmesi güvence altına alınmalıdır.
- **Gizli Hata Bırakmama**: Hatalar, sessizce geçiştirilmemeli (e.g. `except: pass` kullanımından kaçınılmalı), loglara sebebiyle birlikte yazdırılmalıdır ki hata ayıklama süreci kesintiye uğramasın.

