# Graph Report - C:\\Users\\Halil İbrahim\\Desktop\\Oto-Yoklama-2  (2026-08-31)

## Corpus Check
- Corpus is ~27.587 words - fits in a single context window. You may not need a graph.

## Summary
- 308 nodes · 523 edges · 99 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Structure Signals
- Entity graph basis: 287 non-file, non-concept node(s)
- Weakly connected components: 63
- Singleton components: 45
- Isolated nodes: 45
- Largest component: 80 node(s) (28% of the entity graph basis)
- Low-cohesion communities: 0
- Largest low-cohesion community: none on the entity graph basis

## Workspace Bridges
1. `app` - connects `API — Al`, `API — Ayarlar`, `API — Ayarlar \(2\)`, `API — Belge`, `API — Bireysel`, `API — Bugun`, `API — Bugun \(2\)`, `API — Detay`, `API — Devamsizlik`, `API — Devamsizlik \(2\)`, `API — Devamsizlik \(3\)`, `API — Esik`, `API — Excel`, `API — Excel \(2\)`, `API — Excel \(3\)`, `API — Geri`, `API — Getir`, `API — Guncelle`, `API — Indir`, `API — Listele`, `API — Logo`, `API — Meb`, `API — Ogrenci`, `API — PDF`, `API — PDF \(2\)`, `API — Personel`, `API — Personel \(2\)`, `API — Personel \(3\)`, `API — Rapor`; home: `API — App`; degree 30; score 537.5
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/api.py`
2. `ayarlari\_al\(\)` - connects `API — Ayarlar`, `API — Ayarlar \(2\)`, `API — Belge`, `API — Bireysel`, `API — Bugun \(2\)`, `API — Geri`, `API — Guncelle`, `API — Listele`, `API — Logo`, `API — PDF`, `API — PDF \(2\)`; home: `API — Al`; degree 14; score 332.5
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/api.py`
3. `bildirimGoster\(\)` - connects `App — Ac \(2\)`, `App — Adim1`, `App — Adim2`, `App — Belge`, `App — Grubu`, `App — Ihale`, `App — Ihale \(2\)`, `App — Ihale \(3\)`, `App — PDF`, `App — Personel`, `App — Tarih`; home: `App — Al`; degree 22; score 256.58
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/app.js`
4. `pdf\_klasoru\_hazirla\(\)` - connects `API — Al`, `API — Esik`, `API — Excel \(2\)`, `API — Indir`, `API — Meb`, `API — Rapor`; home: `API — PDF`; degree 7; score 80.5
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/api.py`
5. `SistemMotoru` - connects `Sistem Motoru — Al`, `Sistem Motoru — Ayarlar`, `Sistem Motoru — Ayarlar \(2\)`, `Sistem Motoru — En`, `Sistem Motoru — Eski`; home: `Sistem Motoru`; degree 6; score 1948
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/sistem\_motoru.py`
6. `VeriAraclari` - connects `Araclar — Devamsizlik`, `Araclar — Tarih`, `Excel Motoru`, `Test Motoru`; home: `Araclar`; degree 9; score 1571.17
  source files: `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/araclar.py`, `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/excel\_motoru.py`, `C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/test\_motoru.py`

## God Nodes
1. `app` - 31 edges
2. `bildirimGoster\(\)` - 23 edges
3. `ayarlari\_al\(\)` - 15 edges
4. `PDFYoneticisi` - 10 edges
5. `VeriAraclari` - 10 edges
6. `VeritabaniYoneticisi` - 10 edges
7. `belge\_uret\(\)` - 9 edges
8. `format\_date\(\)` - 8 edges
9. `get\_komisyon\(\)` - 8 edges
10. `pdf\_klasoru\_hazirla\(\)` - 8 edges

## Surprising Connections
- `ExcelMotoru` --uses--> `VeriAraclari`  [INFERRED 0.50]
  C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/excel\_motoru.py → C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/araclar.py  _inferred connection - not explicitly stated in source; bridges separate communities_
- `TestDevamsizlikMatematigi` --uses--> `VeriAraclari`  [INFERRED 0.50]
  C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/test\_motoru.py → C:/Users/Halil İbrahim/Desktop/Oto-Yoklama-2/araclar.py  _inferred connection - not explicitly stated in source; bridges separate communities_

## Semantic Anomalies
- **[HIGH] Bridge node** - SistemMotoru bridges Sistem Motoru and Masaustu, Sistem Motoru — Ayarlar \(2\), Sistem Motoru — Ayarlar, Sistem Motoru — Al, Sistem Motoru — En, Sistem Motoru — Eski.
  _High betweenness centrality \(1892.000\) across 7 communities makes this node a likely dependency chokepoint._
- **[HIGH] Bridge node** - VeriAraclari bridges Araclar and Araclar — Py, Araclar — Devamsizlik, Araclar — Tarih, Excel Motoru, Test Motoru.
  _High betweenness centrality \(1522.167\) across 6 communities makes this node a likely dependency chokepoint._
- **[HIGH] Bridge node** - PDFYoneticisi bridges PDF Motoru and PDF Motoru — Ciz, PDF Motoru — Formu, PDF Motoru — Ad.
  _High betweenness centrality \(1730.500\) across 4 communities makes this node a likely dependency chokepoint._
- **[HIGH] Cross-boundary edge** - ExcelMotoru → VeriAraclari crosses graph boundaries in an unexpected way.
  _inferred connection - not explicitly stated in source; bridges separate communities_
- **[HIGH] Cross-boundary edge** - TestDevamsizlikMatematigi → VeriAraclari crosses graph boundaries in an unexpected way.
  _inferred connection - not explicitly stated in source; bridges separate communities_

## Communities

### Community 0 - "App"
Cohesion (entity basis within full-graph community): 0
Nodes (34): akilliEslesmeSil\(\), ayarlariGetirPersonelGruplariIcin\(\), ayarlariKaydet\(\), ayarlariYukle\(\), esikRaporuAl\(\), gecKalanlariIndir\(\), guncellemeKontrolEt\(\), ihaleAdim3Geri\(\) (+26 more)

### Community 1 - "Ihale Motoru"
Cohesion (entity basis within full-graph community): 0.4
Nodes (11): belge\_uret\(\), format\_date\(\), get\_komisyon\(\), uret\_fiyat\_isteme\_excel\(\), uret\_fiyat\_isteme\_pdf\(\), uret\_ozel\_fiyat\_isteme\_excel\(\), uret\_ozel\_fiyat\_isteme\_pdf\(\), uret\_piyasa\_arastirmasi\_excel\(\) (+3 more)

### Community 2 - "App — Al"
Cohesion (entity basis within full-graph community): 0.2
Nodes (10): akilliEslesmeEkle\(\), bildirimGoster\(\), bireyselTebligPdfAl\(\), ihaleAdim3Goster\(\), kopyalaAd\(\), kopyalaNo\(\), personelDrawerKaydet\(\), raporAl\(\) (+2 more)

### Community 3 - "API"
Cohesion (entity basis within full-graph community): 0
Nodes (8): DevamsizlikEkleRequest, PdfVeliFormuRequest, PersonelModel, PersonelRequest, RaporAlRequest, safe\_float\(\), TebligBireyselRequest, TebligTopluRequest

### Community 4 - "Veritabani"
Cohesion (entity basis within full-graph community): 0.29
Nodes (7): VeritabaniYoneticisi, .baglan\_ve\_hazirla\(\), .conn\(\), .kapat\(\), .kaydet\(\), .sifirla\(\), .yukle\(\)

### Community 5 - "App — Personel"
Cohesion (entity basis within full-graph community): 0.29
Nodes (7): filtreTumuDegisti\(\), otomatikPersonelSec\(\), personelDurumDegistir\(\), personelMasterSecim\(\), personelSayaciGuncelle\(\), personelTablosunuDoldur\(\), personelTumunuTemizle\(\)

### Community 6 - "API — Al"
Cohesion (entity basis within full-graph community): 0.5
Nodes (5): POST /yedek-al, ayarlari\_al\(\), Ayarları sadece dosya degistiginde okur \(Cache\)., yedek\_al\(\), \_zamanlanmis\_yedek\_dongusu\(\)

### Community 7 - "App — Ihale"
Cohesion (entity basis within full-graph community): 0.5
Nodes (5): ihaleKalemSatiriEkle\(\), ihaleKalemSatiriSil\(\), ihaleKalemTablosunuCiz\(\), ihaleSifirla\(\), ihaleTaslaginiKaydet\(\)

### Community 8 - "Excel Motoru"
Cohesion (entity basis within full-graph community): 0.4
Nodes (5): ExcelMotoru, .devamsizlik\_oku\(\), .esik\_raporu\_excel\_ciz\(\), .ihale\_oku\(\), .ogrenci\_oku\(\)

### Community 9 - "PDF Motoru"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): PDFYoneticisi, .bireysel\_teblig\_ciz\(\), .\_\_init\_\_\(\), .teblig\_tebellug\_ciz\(\)

### Community 10 - "App — Ay"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): ayDegistir\(\), hucreSagTikla\(\), onizlemeTemizle\(\), takvimiCiz\(\)

### Community 11 - "App — Basliklari"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): basliklariGuncelle\(\), filtreTemizle\(\), sirala\(\), tabloyuDoldur\(\)

### Community 12 - "App — Yukle"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): dosyaYukle\(\), mebPdfYukle\(\), personelExcelYukle\(\), yuklemeGoster\(\)

### Community 13 - "App — Ihale \(2\)"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): ihaleBilgiGirisiKaydet\(\), ihaleKomisyonKaydet\(\), modalKapat\(\), personelAta\(\)

### Community 14 - "App — Ozel"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): ozelAyDegistir\(\), ozelGunSec\(\), ozelTakvimCiz\(\), takvimBaloncuguAc\(\)

### Community 15 - "App — Personel \(2\)"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): personelFiltreAyarla\(\), personelGruplariCiz\(\), personelYonetimAc\(\), yonetimPersonelTablosunuDoldur\(\)

### Community 16 - "Araclar"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): VeriAraclari, .kisa\_sube\_adi\(\), .parse\_tarih\(\), .tr\_upper\(\)

### Community 17 - "Masaustu"
Cohesion (entity basis within full-graph community): 0
Nodes (2): port\_dinleniyor\_mu\(\), sunucuyu\_baslat\(\)

### Community 18 - "PDF Motoru — Ciz"
Cohesion (entity basis within full-graph community): 0.5
Nodes (4): .esik\_raporu\_pdf\_ciz\(\), .gec\_kalanlar\_pdf\_ciz\(\), .metin\_duzelt\(\), .personel\_raporu\_ciz\(\)

### Community 19 - "API — App"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): app, GET /ogrenciler, ogrencileri\_getir\(\)

### Community 20 - "API — Logo"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /logo-yukle, logo\_yukle\(\), tur: 'meb' veya 'okul'

### Community 21 - "API — Excel"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /ogrenci-excel-yukle, gecici\_dosya\_olustur\(\), ogrenci\_excel\_yukle\(\)

### Community 22 - "API — PDF"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /pdf-veli-formu, pdf\_klasoru\_hazirla\(\), pdf\_veli\_formu\_olustur\(\)

### Community 23 - "API — Personel"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /personel-ekle, personel\_ekle\(\), \_personel\_grup\_tahmin\_et\(\)

### Community 24 - "API — Personel \(2\)"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /personel-excel-yukle, personel\_excel\_yukle\(\), E-Okul/MEB'den indirilen personel Excel listesini okuyup personel tablosunu tamamen günceller.

### Community 25 - "API — Rapor"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): POST /rapor-al, rapor\_al\(\), \_rapor\_verisi\_hazirla\(\)

### Community 26 - "App — Akilli"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): aeTurDegisti\(\), akilliEslesmeCiz\(\), akilliEslesmeModalAc\(\)

### Community 27 - "App — Butce"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): butceTertibiEkle\(\), butceTertibiSil\(\), ihaleBaslat\(\)

### Community 28 - "App — Fiyat"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): fiyatGirisHesapla\(\), fiyatGirisTablosunuCiz\(\), ihaleFirmaSil\(\)

### Community 29 - "App — Firma"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): fiyatGirisModalAc\(\), ihaleFirmaEkle\(\), ihaleFirmaTablosunuCiz\(\)

### Community 30 - "App — Onizleme"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): hucreTikla\(\), onizlemeCikar\(\), onizlemeGuncelle\(\)

### Community 31 - "App — Ac"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): ihaleBilgiGirisiModalAc\(\), modalAc\(\), personelGrupYonetimiAc\(\)

### Community 32 - "App — Personel \(3\)"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): personelAra\(\), personelHavuzunuCiz\(\), personelSecimEkraniAc\(\)

### Community 33 - "App — Grubu"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): personelGrubuKaydet\(\), personelGrubuSil\(\), yeniPersonelGrubuEkle\(\)

### Community 34 - "App — Yukle \(2\)"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): personelleriYukle\(\), sekmeAc\(\), verileriYukle\(\)

### Community 35 - "App — Mouse"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): tabloSutunBoyutlandirma\(\), mouseMove\(\), mouseUp\(\)

### Community 36 - "Guncelleyici"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GuncellemeMotoru, .kontrol\_et\(\)

### Community 37 - "Sistem Motoru"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): SistemMotoru, .klasorleri\_ve\_yollari\_hazirla\(\), Programın ihtiyaç duyduğu tüm ana klasörleri oluşturur ve dosya yollarını döndürür.

### Community 38 - "Veritabani — Init"
Cohesion (entity basis within full-graph community): 0.67
Nodes (3): .cursor\(\), .\_\_init\_\_\(\), .\_init\_db\(\)

### Community 39 - "API — Devamsizlik"
Cohesion (entity basis within full-graph community): 1
Nodes (2): DELETE /devamsizlik-sil/{d\_id}, devamsizlik\_sil\(\)

### Community 40 - "API — Ogrenci"
Cohesion (entity basis within full-graph community): 1
Nodes (2): DELETE /ogrenci-sil/{ogr\_no}, ogrenci\_sil\(\)

### Community 41 - "API — Personel \(3\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): DELETE /personel-sil/{ad}, personel\_sil\(\)

### Community 42 - "API — Ayarlar"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /ayarlar-getir, ayarlar\_getir\(\)

### Community 43 - "API — Bugun"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /gec-bugun-sayisi, gec\_bugun\_sayisi\(\)

### Community 44 - "API — Detay"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /ogrenci-detay/{ogr\_no}, ogrenci\_detay\_getir\(\)

### Community 45 - "API — Excel \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /personel-excel-indir, personel\_excel\_indir\(\)

### Community 46 - "API — Indir"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /personel-pdf-indir, personel\_pdf\_indir\(\)

### Community 47 - "API — Getir"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /personeller, personelleri\_getir\(\)

### Community 48 - "API — Esik"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /rapor-esik-siniflar/{format\_tipi}, rapor\_esik\_siniflar\(\)

### Community 49 - "API — Bugun \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /rapor-gec-bugun, rapor\_gec\_bugun\(\)

### Community 50 - "API — Listele"
Cohesion (entity basis within full-graph community): 1
Nodes (2): GET /yedekler-listele, yedekler\_listele\(\)

### Community 51 - "API — Ayarlar \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /ayarlar-kaydet, ayarlar\_kaydet\(\)

### Community 52 - "API — Devamsizlik \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /devamsizlik-excel-yukle, devamsizlik\_excel\_yukle\(\)

### Community 53 - "API — Devamsizlik \(3\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /devamsizlik-manuel-ekle, devamsizlik\_manuel\_ekle\(\)

### Community 54 - "API — Excel \(3\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /ihale-excel-oku, ihale\_excel\_oku\(\)

### Community 55 - "API — Belge"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /ihale-tekli-belge, ihale\_tekli\_belge\(\)

### Community 56 - "API — Meb"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /meb-pdf-oku, meb\_pdf\_oku\(\)

### Community 57 - "API — Bireysel"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /teblig-bireysel-pdf, teblig\_bireysel\_pdf\(\)

### Community 58 - "API — PDF \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /teblig-toplu-pdf, teblig\_toplu\_pdf\(\)

### Community 59 - "API — Geri"
Cohesion (entity basis within full-graph community): 1
Nodes (2): POST /yedek-geri-yukle, yedek\_geri\_yukle\(\)

### Community 60 - "API — Guncelle"
Cohesion (entity basis within full-graph community): 1
Nodes (2): PUT /personel-guncelle/{eski\_ad}, personel\_guncelle\(\)

### Community 61 - "API — Config"
Cohesion (entity basis within full-graph community): 1
Nodes (2): Config, KayitModel

### Community 62 - "API — Ac"
Cohesion (entity basis within full-graph community): 1
Nodes (2): dosyayi\_otomatik\_ac\(\), Oluşturulan PDF veya Excel dosyasını bilgisayarın varsayılan programıyla anında açar

### Community 63 - "App — Adim1"
Cohesion (entity basis within full-graph community): 1
Nodes (2): adim1Ileri\(\), ihaleAdim2Goster\(\)

### Community 64 - "App — Adim2"
Cohesion (entity basis within full-graph community): 1
Nodes (2): adim2Ileri\(\), ihaleBelgeUretimEkraniGoster\(\)

### Community 65 - "App — Belge"
Cohesion (entity basis within full-graph community): 1
Nodes (2): belgeUret\(\), fiyatGirisTamamla\(\)

### Community 66 - "App — Filtre"
Cohesion (entity basis within full-graph community): 1
Nodes (2): filtreleriHesapla\(\), personelFiltreTopluUygula\(\)

### Community 67 - "App — PDF"
Cohesion (entity basis within full-graph community): 1
Nodes (2): gercekPdfIstegiAt\(\), pdfCiktisiAl\(\)

### Community 68 - "App — Ihale \(3\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): ihaleExcelYukle\(\), ihaleTablosunuCiz\(\)

### Community 69 - "App — Ac \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): ihaleKomisyonModalAc\(\), yuklemeGizle\(\)

### Community 70 - "App — Tarih"
Cohesion (entity basis within full-graph community): 1
Nodes (2): ozelTarihUygula\(\), parseTarihStr\(\)

### Community 71 - "App — Parse"
Cohesion (entity basis within full-graph community): 1
Nodes (2): topluSecim\(\), parseTarih\(\)

### Community 72 - "App — Ac \(3\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): yillikListeAc\(\), ozetKutusuCiz\(\)

### Community 73 - "Araclar — Py"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 74 - "Araclar — Tarih"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .excel\_tarih\_cevir\(\), .tarih\_formatla\(\)

### Community 75 - "Araclar — Devamsizlik"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .hesapla\_devamsizlik\(\), .temiz\_sure\(\)

### Community 76 - "Masaustu — Al"
Cohesion (entity basis within full-graph community): 1
Nodes (2): api\_zaten\_calisiyor\_mu\(\), 127.0.0.1:8000'de kendi API'mizin hâlihazırda çalışıp çalışmadığını kontrol eder \(programın kapanmayan eski bir kopyası arka planda kalmış olabilir\).

### Community 77 - "Masaustu — Pencere"
Cohesion (entity basis within full-graph community): 1
Nodes (2): pencere\_durumu\_kaydet\(\), Program kapanırken çağrılır, son pencere durumunu diske yazar.

### Community 78 - "Masaustu — Pencere \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): pencere\_durumu\_yukle\(\), Daha önce kaydedilmiş pencere durumunu okur. Bozuk/mantıksız değerler \(örn. farklı ve daha küçük bir ekrandan kalma ekran-dışı konum\) varsa güvenli varsayılana döner, böylece pencere karışık/taşmış görünmez.

### Community 79 - "PDF Motoru — Ad"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .rapor\_ciz\(\), veri: \[\[sube, no, ad\_soyad, deger\], ...\] şeklinde bir liste bekler.

### Community 80 - "PDF Motoru — Formu"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .veli\_formu\_ciz\(\), A5 Boyutunda Resmi Veli Devamsızlık Bildirim Formu Çizer

### Community 81 - "Sistem Motoru — Ayarlar"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .ayarlari\_kaydet\(\), Ayarları JSON dosyasına yazar.

### Community 82 - "Sistem Motoru — Ayarlar \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .ayarlari\_yukle\(\), JSON dosyasından ayarları RAM'e çeker.

### Community 83 - "Sistem Motoru — Eski"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .eski\_yedekleri\_temizle\(\), Kullanıcının belirlediği gün sayısından eski yedek dosyalarını siler.

### Community 84 - "Sistem Motoru — Al"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .yedek\_al\(\), Veritabanını kopyalayarak yedekler ve eski çöpleri temizler.

### Community 85 - "Sistem Motoru — En"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .yedekleri\_listele\(\), Yedek klasöründeki .db dosyalarını \(en yeniden en eskiye\) listeler.

### Community 86 - "Ciktilar Test"
Cohesion (entity basis within full-graph community): 1
Nodes (1): untitled

### Community 87 - "Test Motoru"
Cohesion (entity basis within full-graph community): 1
Nodes (1): TestDevamsizlikMatematigi

### Community 88 - "Test Motoru — Test"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .test\_gec\_kalma\_hesaplamasi\(\), 5 adet Geç \(G\) kalmanın tam olarak 0.5 gün Özürsüz yapıp yapmadığını test eder.

### Community 89 - "Test Motoru — Test \(2\)"
Cohesion (entity basis within full-graph community): 1
Nodes (2): .test\_haftasonu\_haric\_hesaplama\(\), Hafta sonuna denk gelen devamsızlıkların genel toplamdan düşülüp düşülmediğini test eder.

### Community 90 - "1 Png"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 91 - "2 Png"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 92 - "3 Png"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 93 - "4 Png"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 94 - "5 Png"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 95 - "Adblock Snippet Js"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 96 - "Build Exe Py"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 97 - "Dummy PDF"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

### Community 98 - "Sabitler Py"
Cohesion (entity basis within full-graph community): n/a
Nodes (0): 

## Knowledge Gaps
- **145 weakly connected node(s):** `dosyayi\_otomatik\_ac\(\)`, `DevamsizlikEkleRequest`, `KayitModel`, `Config`, `PdfVeliFormuRequest` (+140 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `API — Devamsizlik`** (2 nodes): `DELETE /devamsizlik-sil/{d\_id}`, `devamsizlik\_sil\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Ogrenci`** (2 nodes): `DELETE /ogrenci-sil/{ogr\_no}`, `ogrenci\_sil\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Personel \(3\)`** (2 nodes): `DELETE /personel-sil/{ad}`, `personel\_sil\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Ayarlar`** (2 nodes): `GET /ayarlar-getir`, `ayarlar\_getir\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Bugun`** (2 nodes): `GET /gec-bugun-sayisi`, `gec\_bugun\_sayisi\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Detay`** (2 nodes): `GET /ogrenci-detay/{ogr\_no}`, `ogrenci\_detay\_getir\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Excel \(2\)`** (2 nodes): `GET /personel-excel-indir`, `personel\_excel\_indir\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Indir`** (2 nodes): `GET /personel-pdf-indir`, `personel\_pdf\_indir\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Getir`** (2 nodes): `GET /personeller`, `personelleri\_getir\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Esik`** (2 nodes): `GET /rapor-esik-siniflar/{format\_tipi}`, `rapor\_esik\_siniflar\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Bugun \(2\)`** (2 nodes): `GET /rapor-gec-bugun`, `rapor\_gec\_bugun\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Listele`** (2 nodes): `GET /yedekler-listele`, `yedekler\_listele\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Ayarlar \(2\)`** (2 nodes): `POST /ayarlar-kaydet`, `ayarlar\_kaydet\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Devamsizlik \(2\)`** (2 nodes): `POST /devamsizlik-excel-yukle`, `devamsizlik\_excel\_yukle\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Devamsizlik \(3\)`** (2 nodes): `POST /devamsizlik-manuel-ekle`, `devamsizlik\_manuel\_ekle\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Excel \(3\)`** (2 nodes): `POST /ihale-excel-oku`, `ihale\_excel\_oku\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Belge`** (2 nodes): `POST /ihale-tekli-belge`, `ihale\_tekli\_belge\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Meb`** (2 nodes): `POST /meb-pdf-oku`, `meb\_pdf\_oku\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Bireysel`** (2 nodes): `POST /teblig-bireysel-pdf`, `teblig\_bireysel\_pdf\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — PDF \(2\)`** (2 nodes): `POST /teblig-toplu-pdf`, `teblig\_toplu\_pdf\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Geri`** (2 nodes): `POST /yedek-geri-yukle`, `yedek\_geri\_yukle\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Guncelle`** (2 nodes): `PUT /personel-guncelle/{eski\_ad}`, `personel\_guncelle\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Config`** (2 nodes): `Config`, `KayitModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API — Ac`** (2 nodes): `dosyayi\_otomatik\_ac\(\)`, `Oluşturulan PDF veya Excel dosyasını bilgisayarın varsayılan programıyla anında açar`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Adim1`** (2 nodes): `adim1Ileri\(\)`, `ihaleAdim2Goster\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Adim2`** (2 nodes): `adim2Ileri\(\)`, `ihaleBelgeUretimEkraniGoster\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Belge`** (2 nodes): `belgeUret\(\)`, `fiyatGirisTamamla\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Filtre`** (2 nodes): `filtreleriHesapla\(\)`, `personelFiltreTopluUygula\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — PDF`** (2 nodes): `gercekPdfIstegiAt\(\)`, `pdfCiktisiAl\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Ihale \(3\)`** (2 nodes): `ihaleExcelYukle\(\)`, `ihaleTablosunuCiz\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Ac \(2\)`** (2 nodes): `ihaleKomisyonModalAc\(\)`, `yuklemeGizle\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Tarih`** (2 nodes): `ozelTarihUygula\(\)`, `parseTarihStr\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Parse`** (2 nodes): `topluSecim\(\)`, `parseTarih\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App — Ac \(3\)`** (2 nodes): `yillikListeAc\(\)`, `ozetKutusuCiz\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Araclar — Py`** (2 nodes): `araclar.py`, `excel\_motoru.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Araclar — Tarih`** (2 nodes): `.excel\_tarih\_cevir\(\)`, `.tarih\_formatla\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Araclar — Devamsizlik`** (2 nodes): `.hesapla\_devamsizlik\(\)`, `.temiz\_sure\(\)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Masaustu — Al`** (2 nodes): `api\_zaten\_calisiyor\_mu\(\)`, `127.0.0.1:8000'de kendi API'mizin hâlihazırda çalışıp çalışmadığını kontrol eder \(programın kapanmayan eski bir kopyası arka planda kalmış olabilir\).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Masaustu — Pencere`** (2 nodes): `pencere\_durumu\_kaydet\(\)`, `Program kapanırken çağrılır, son pencere durumunu diske yazar.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Masaustu — Pencere \(2\)`** (2 nodes): `pencere\_durumu\_yukle\(\)`, `Daha önce kaydedilmiş pencere durumunu okur. Bozuk/mantıksız değerler \(örn. farklı ve daha küçük bir ekrandan kalma ekran-dışı konum\) varsa güvenli varsayılana döner, böylece pencere karışık/taşmış görünmez.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PDF Motoru — Ad`** (2 nodes): `.rapor\_ciz\(\)`, `veri: \[\[sube, no, ad\_soyad, deger\], ...\] şeklinde bir liste bekler.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PDF Motoru — Formu`** (2 nodes): `.veli\_formu\_ciz\(\)`, `A5 Boyutunda Resmi Veli Devamsızlık Bildirim Formu Çizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sistem Motoru — Ayarlar`** (2 nodes): `.ayarlari\_kaydet\(\)`, `Ayarları JSON dosyasına yazar.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sistem Motoru — Ayarlar \(2\)`** (2 nodes): `.ayarlari\_yukle\(\)`, `JSON dosyasından ayarları RAM'e çeker.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sistem Motoru — Eski`** (2 nodes): `.eski\_yedekleri\_temizle\(\)`, `Kullanıcının belirlediği gün sayısından eski yedek dosyalarını siler.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sistem Motoru — Al`** (2 nodes): `.yedek\_al\(\)`, `Veritabanını kopyalayarak yedekler ve eski çöpleri temizler.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sistem Motoru — En`** (2 nodes): `.yedekleri\_listele\(\)`, `Yedek klasöründeki .db dosyalarını \(en yeniden en eskiye\) listeler.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Ciktilar Test`** (2 nodes): `test.pdf`, `untitled`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Motoru`** (2 nodes): `test\_motoru.py`, `TestDevamsizlikMatematigi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Motoru — Test`** (2 nodes): `.test\_gec\_kalma\_hesaplamasi\(\)`, `5 adet Geç \(G\) kalmanın tam olarak 0.5 gün Özürsüz yapıp yapmadığını test eder.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Test Motoru — Test \(2\)`** (2 nodes): `.test\_haftasonu\_haric\_hesaplama\(\)`, `Hafta sonuna denk gelen devamsızlıkların genel toplamdan düşülüp düşülmediğini test eder.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `1 Png`** (1 nodes): `1.png`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `2 Png`** (1 nodes): `2.png`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `3 Png`** (1 nodes): `3.png`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `4 Png`** (1 nodes): `4.png`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `5 Png`** (1 nodes): `5.png`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adblock Snippet Js`** (1 nodes): `adblock\_snippet.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Build Exe Py`** (1 nodes): `build\_exe.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dummy PDF`** (1 nodes): `dummy.pdf`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sabitler Py`** (1 nodes): `sabitler.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does \`SistemMotoru\` connect \`Sistem Motoru\` to \`Masaustu\`, \`Sistem Motoru — Ayarlar \(2\)\`, \`Sistem Motoru — Ayarlar\`, \`Sistem Motoru — Al\`, \`Sistem Motoru — En\`, \`Sistem Motoru — Eski\`?**
  _High betweenness centrality \(1892.000\) - this node is a cross-community bridge._
- **Why does \`PDFYoneticisi\` connect \`PDF Motoru\` to \`PDF Motoru — Ciz\`, \`PDF Motoru — Formu\`, \`PDF Motoru — Ad\`?**
  _High betweenness centrality \(1730.500\) - this node is a cross-community bridge._
- **Why does \`VeriAraclari\` connect \`Araclar\` to \`Araclar — Py\`, \`Araclar — Devamsizlik\`, \`Araclar — Tarih\`, \`Excel Motoru\`, \`Test Motoru\`?**
  _High betweenness centrality \(1522.167\) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving \`VeriAraclari\` \(e.g. with \`ExcelMotoru\` and \`TestDevamsizlikMatematigi\`\) actually correct?**
  _\`VeriAraclari\` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects \`dosyayi\_otomatik\_ac\(\)\`, \`DevamsizlikEkleRequest\`, \`KayitModel\` to the rest of the system?**
  _145 weakly-connected nodes found - possible documentation gaps or missing edges._
