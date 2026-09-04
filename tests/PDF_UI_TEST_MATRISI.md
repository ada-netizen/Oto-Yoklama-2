# PDF ve Windows UI Test Matrisi

Bu kontrol, temiz bir Windows 10/11 makinesinde yayın adayı ile uygulanır.

## PDF testleri

| Senaryo | Beklenen sonuç |
|---|---|
| Türkçe karakterli okul, öğrenci ve personel adları | `ç, ğ, ı, İ, ö, ş, ü` karakterleri doğru görünür |
| Veli formu | A5 ölçüsünde açılır ve içerik sayfa dışına taşmaz |
| Bireysel tebliğ | Tarih, sayı, konu ve kişi bilgileri doğru hizalanır |
| Toplu tebliğ | Tablo çizgileri görünür, uzun adlar hücre dışına taşmaz |
| 20+ satırlı tablo | Sayfa geçişi bozulmaz, satırlar üst üste binmez |
| PDF yazdırma önizlemesi | A4/A5 seçimine göre içerik kenarlara taşmaz |
| Arial fontu olmayan bilgisayar | PDF üretimi başarısız olmaz; Türkçe metin okunabilir kalır |

## Windows ekran ölçeği

Her ölçek için uygulama kapatılıp yeniden açılır ve aşağıdaki kontroller yapılır:

| Ölçek | Kontroller |
|---|---|
| `%100` | Sekmeler, tablolar, düğmeler ve modallar görünür |
| `%125` | Metin kesilmez, yatay taşma oluşmaz, düğmeler üst üste binmez |
| `%150` | Ayarlar, personel yönetimi ve tebliğ ekranları kullanılabilir |

## Yayın kabul kriterleri

- Ana pencere açıldığında içerik kesilmemeli.
- Ayarlar ekranındaki tüm düğmeler erişilebilir olmalı.
- Uzun dosya ve klasör yolları arayüzü bozmamalı.
- Modal pencereler ekranın dışına taşmamalı.
- PDF çıktısının görsel düzeni ekran ölçeğinden etkilenmemeli.
- Yazdırma önizlemesinde metin, tablo ve imza alanları sayfa sınırları içinde kalmalı.
- Her test sonucunda Windows sürümü, ekran ölçeği, çözünürlük ve uygulama sürümü kaydedilmeli.
