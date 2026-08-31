# Oto-Yoklama Yönetim Sistemi V2

Oto-Yoklama, okullar ve eğitim kurumları için tasarlanmış modern, hızlı ve kullanımı kolay bir devamsızlık ve evrak yönetim sistemidir. Milli Eğitim Bakanlığı (MEB) mevzuatına uygun hesaplama motoruyla çalışır.

## 🚀 Yeni Gelen Özellikler (V2)

- **Tek Tıkla Çalışan Masaüstü Uygulaması (.exe):** Artık Python kurulumuna veya komut satırına gerek yok! PyInstaller ile derlenmiş bağımsız, taşınabilir (portable) yapı.
- **Otomatik Güncelleme Sistemi (Auto-Updater):** GitHub üzerinden yeni bir sürüm çıktığında sistem bunu otomatik tespit eder ve size tek tıklamayla indirme seçeneği sunar.
- **Akıllı MEB Devamsızlık Hesaplama Motoru:** Öğrencinin "Özürlü", "Özürsüz", "Faaliyet" ve "Geç (5 geç = 0.5 gün)" kayıtlarını MEB mantığıyla kusursuz hesaplar.
- **Dinamik Veli Bilgilendirme PDF'leri:** Çıktı alınan devamsızlık mektuplarının sol alt köşesinde anlık olarak güncellenmiş toplam Özürlü ve Özürsüz gün sayıları otomatik olarak kalın fontla yer alır.
- **Yapay Zeka (MCP) Entegrasyonu:** Geliştiriciler için proje kök dizinine entegre edilmiş SQLite, Puppeteer ve PDF MCP sunucuları ile LLM ajanlarının projeye anında müdahale edebileceği modüler bir altyapı oluşturulmuştur.

## 🎯 Temel Özellikler

- **Öğrenci ve Personel Yönetimi:** Excel listelerinden tek tuşla hızlı içe aktarım veya manuel veri girişi.
- **Kolay Devamsızlık Takibi:** Hızlı seçim arayüzü ile günlük ve geçmiş devamsızlık işleme.
- **Raporlama ve Çıktı Alma:** Resmi formatlara tam uyumlu veli devamsızlık mektupları, öğretmen imza sirküleri ve şube bazlı Excel/PDF raporları.
- **Arka Planda Otomatik Yedekleme:** Olası veri kayıplarına karşı veritabanınızı belirlediğiniz zamanlarda (1 Hafta, 1 Ay vb.) otomatik olarak yedekler ve eski çöpleri temizler.
- **Modern ve Hızlı Arayüz:** Göz yormayan, dinamik, arama/filtreleme özellikleri ile güçlendirilmiş koyu/açık tema (Dark/Light) destekli tasarım.

## 💻 Teknoloji Altyapısı

- **Backend:** `FastAPI` (Python)
- **Frontend:** HTML, CSS, JavaScript (`pywebview` ile bağımsız pencere)
- **Veritabanı:** `SQLite` (`VeritabaniYoneticisi` transaction yapısıyla disk yormayan hızlı kayıt)
- **Raporlama:** `reportlab`, `PyPDF2`, `pandas`, `openpyxl`
- **Derleme:** `PyInstaller` (Gizli kütüphane bağlamaları ve `multiprocessing.freeze_support` yamaları dahil edilmiştir)

## 🛠 Kurulum ve Kullanım

### Normal Kullanıcılar İçin (Önerilen)
Artık terminal ile uğraşmanıza gerek yok! 
1. Projenin `dist` klasörü içindeki `Oto_Yoklama.exe` dosyasını çalıştırın.
2. Program otomatik olarak arka planda kendi sunucusunu başlatacak ve modern masaüstü uygulamasını karşınıza getirecektir. (USB belleğe atıp istediğiniz bilgisayarda kullanabilirsiniz).

### Geliştiriciler İçin (Kaynak Koddan Çalıştırma)
1. Python 3.8 veya üzeri yüklü olmalıdır.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. Uygulamayı başlatın:
   ```bash
   python masaustu.py
   ```
4. Yeni bir `.exe` derlemek isterseniz hazırladığımız yapıyı kullanın:
   ```bash
   python build_exe.py
   ```

## 📁 Dosya ve Veri Yolları
Uygulamanın çalışması için gereken PDF'ler, veritabanı dosyaları ve yedekler, işletim sisteminizin kullanıcı dizini altında güvenli bir şekilde saklanır:
`C:\Users\KullanıcıAdınız\YoklamaOtomasyonuVerileri\` 
Bu sayede programın farklı sürümleri arasında geçiş yapsanız dahi verileriniz asla kaybolmaz.
