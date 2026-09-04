# Oto Yoklama V2 - Yayın Kapsamı

## Hedef ürün

Windows üzerinde çalışan, tek kullanıcılı ve yerel veri saklayan bir masaüstü uygulaması.

## Bu sürümde garanti edilecekler

- Uygulama Windows 10 ve Windows 11 üzerinde çalışacak.
- Kullanıcının bilgisayarında Python kurulumu gerekmeyecek.
- Öğrenci, devamsızlık, personel, ayar ve yedek verileri yerel bilgisayarda tutulacak.
- Veriler kullanıcı profilindeki `YoklamaOtomasyonuVerileri` klasöründe saklanacak.
- Kullanıcının verileri herhangi bir uzak sunucuya gönderilmeyecek.
- Uygulama aynı bilgisayarda tek aktif kullanıcı/tek aktif süreç olarak çalışacak.
- Güncellemeler otomatik olarak kurulmayacak; kullanıcı açıkça onay vermeden güncelleme başlatılmayacak.
- Güncelleme öncesinde veritabanı yedeği alınacak.
- İçe aktarma, PDF üretimi ve yedekleme işlemlerinde kullanıcıya işlem durumu gösterilecek.
- Kritik toplu veri işlemleri başarısız olursa mevcut veriler korunacak.

## Veri ve gizlilik sınırları

- Bu sürümde merkezi kullanıcı hesabı, bulut senkronizasyonu ve çok kullanıcılı çalışma olmayacak.
- API yalnızca yerel masaüstü uygulamasının ihtiyacı için `127.0.0.1` üzerinde çalışacak.
- Kullanıcı verileri, hata kayıtları ve oluşturulan belgeler yerel diskte tutulacak.
- Hassas verilerin loglara yazılmaması temel kural olacak.

## Yayın paketi

- Windows için imzalanmış veya en azından doğrulanmış bir kurulum paketi hazırlanacak.
- Paket, Python kurulumu olmayan temiz bir Windows bilgisayarında test edilecek.
- Kurulum ve kaldırma işlemleri kullanıcı verilerini izinsiz silmeyecek.
- İlk yayın adayı, sürüm numarası ve değişiklik özetiyle birlikte üretilecek.

## Yayın kabul koşulları

1. Temiz Windows ortamında uygulama kurulup açılabilmeli.
2. Uygulama kapatılıp yeniden açıldığında yerel veriler korunmalı.
3. Hatalı Excel veya PDF işlemi mevcut verileri bozmamalı.
4. Türkçe karakterler ve PDF çıktıları desteklenen test senaryolarında doğru görünmeli.
5. Güncelleme yalnızca kullanıcı onayıyla başlamalı ve başarısız güncellemede veri kaybı olmamalı.
6. Testler gerçek kullanıcı veritabanını değiştirmemeli.

## Kapsam dışı özellikler

- Web sunucusu olarak uzaktan erişim
- Kullanıcı hesapları ve yetkilendirme sistemi
- Bulut yedekleme veya çevrim içi veri senkronizasyonu
- Mobil uygulama
- Otomatik, kullanıcı onaysız güncelleme
