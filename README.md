# Oto-Yoklama Yönetim Sistemi V2

Oto-Yoklama, okul ve eğitim kurumları için tasarlanmış modern, hızlı ve kullanımı kolay bir öğrenci devamsızlık yönetim sistemidir. 

## Özellikler

- **Öğrenci ve Personel Yönetimi:** Excel listelerinden hızlı içe aktarım veya manuel ekleme.
- **Devamsızlık Takibi:** Kolay kullanılabilir bir arayüz ile günlük devamsızlık takibi.
- **Raporlama ve Çıktı Alma:** Resmi formatlara uygun devamsızlık mektubu, imza sirküsü ve şube bazlı listelerin PDF veya Excel olarak otomatik oluşturulması.
- **Arka Planda Otomatik Yedekleme:** Olası veri kayıplarına karşı belirlediğiniz zamanlarda veritabanınızı otomatik yedekler.
- **Modern Arayüz:** Göz yormayan, dinamik ve arama/filtreleme özellikleri ile güçlendirilmiş kullanıcı deneyimi.

## Teknoloji Altyapısı

- **Backend:** `FastAPI` (Python)
- **Frontend:** HTML, CSS, JavaScript (`webview` ile masaüstü penceresine gömülü)
- **Veritabanı:** `SQLite`
- **Raporlama:** `PyPDF2`, `reportlab`, `pandas`

## Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8 veya üzeri yüklü olmalıdır.

### Adımlar

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. Uygulamayı başlatın:
   ```bash
   python masaustu.py
   ```

## Notlar

Uygulama çalıştırıldığında kendi içerisinde gizli bir FastAPI sunucusu (localhost:8000) başlatır ve ardından `index.html` dosyasını `webview` kütüphanesi yardımıyla modern bir masaüstü penceresi formunda açar.
