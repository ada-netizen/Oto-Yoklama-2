# Graph Report - .  (2026-07-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 206 nodes · 453 edges · 13 communities (7 shown, 6 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8b931a70`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.py
- kullanılabilir.py
- SistemMotoru
- ToolTip
- .detay_paneli_ciz
- YoklamaUygulamasi
- .arayuzu_olustur
- .ogrenci_tablosunu_doldur
- PDFYoneticisi
- VeritabaniYoneticisi
- .tree_parca_yukle

## God Nodes (most connected - your core abstractions)
1. `YoklamaUygulamasi` - 83 edges
2. `ToolTip` - 18 edges
3. `VeriAraclari` - 16 edges
4. `PDFYoneticisi` - 16 edges
5. `SistemMotoru` - 14 edges
6. `VeritabaniYoneticisi` - 12 edges
7. `AltPencerelerMixin` - 11 edges
8. `ayarlari_al()` - 11 edges
9. `ExcelMotoru` - 8 edges
10. `pdf_klasoru_hazirla()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `AltPencerelerMixin` --uses--> `SistemMotoru`  [INFERRED]
  alt_pencereler.py → sistem_motoru.py
- `YoklamaUygulamasi` --uses--> `AltPencerelerMixin`  [INFERRED]
  kullanılabilir.py → alt_pencereler.py
- `ToolTip` --uses--> `VeriAraclari`  [INFERRED]
  kullanılabilir.py → araclar.py
- `YoklamaUygulamasi` --uses--> `VeriAraclari`  [INFERRED]
  kullanılabilir.py → araclar.py
- `ToolTip` --uses--> `ExcelMotoru`  [INFERRED]
  kullanılabilir.py → excel_motoru.py

## Import Cycles
- None detected.

## Communities (13 total, 6 thin omitted)

### Community 0 - "api.py"
Cohesion: 0.08
Nodes (28): ayarlar_getir(), ayarlar_kaydet(), ayarlari_al(), dosyayi_otomatik_ac(), logo_yukle(), meb_pdf_oku(), ogrenci_excel_yukle(), pdf_klasoru_hazirla() (+20 more)

### Community 1 - "kullanılabilir.py"
Cohesion: 0.11
Nodes (10): devamsizlik_excel_yukle(), ogrencileri_getir(), VeriAraclari, ExcelMotoru, GuncellemeMotoru, global_hata_yakalayici(), Programın herhangi bir yerinde oluşan ve yakalanmayan hataları hapseder., 5 adet Geç (G) kalmanın tam olarak 0.5 gün Özürsüz yapıp yapmadığını test eder. (+2 more)

### Community 2 - "SistemMotoru"
Cohesion: 0.10
Nodes (11): api_zaten_calisiyor_mu(), _kapaniyor(), pencere_durumu_kaydet(), pencere_durumu_yukle(), Daha önce kaydedilmiş pencere durumunu okur. Bozuk/mantıksız değerler     (örn., Program kapanırken çağrılır, son pencere durumunu diske yazar., 127.0.0.1:8000'de kendi API'mizin hâlihazırda çalışıp çalışmadığını kontrol eder, JSON dosyasından ayarları RAM'e çeker. (+3 more)

### Community 3 - "ToolTip"
Cohesion: 0.14
Nodes (5): AltPencerelerMixin, Asenkron işlem bittiğinde yükleme penceresini kapatır ve dosyayı açar., Arayüz nesneleri için üzerine gelince açılan ipucu baloncukları oluşturur., ToolTip, object

### Community 9 - "PDFYoneticisi"
Cohesion: 0.24
Nodes (3): PDFYoneticisi, veri: [[sube, no, ad_soyad, deger], ...] şeklinde bir liste bekler., A5 Boyutunda Resmi Veli Devamsızlık Bildirim Formu Çizer

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `YoklamaUygulamasi` connect `YoklamaUygulamasi` to `kullanılabilir.py`, `SistemMotoru`, `ToolTip`, `.detay_paneli_ciz`, `.arayuzu_olustur`, `.ogrenci_tablosunu_doldur`, `.__init__`, `PDFYoneticisi`, `VeritabaniYoneticisi`, `.tr_upper`, `.tree_parca_yukle`?**
  _High betweenness centrality (0.576) - this node is a cross-community bridge._
- **Why does `SistemMotoru` connect `SistemMotoru` to `api.py`, `kullanılabilir.py`, `ToolTip`, `YoklamaUygulamasi`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Why does `PDFYoneticisi` connect `PDFYoneticisi` to `api.py`, `kullanılabilir.py`, `ToolTip`, `.detay_paneli_ciz`, `YoklamaUygulamasi`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `YoklamaUygulamasi` (e.g. with `AltPencerelerMixin` and `VeriAraclari`) actually correct?**
  _`YoklamaUygulamasi` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ToolTip` (e.g. with `AltPencerelerMixin` and `VeriAraclari`) actually correct?**
  _`ToolTip` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `VeriAraclari` (e.g. with `ExcelMotoru` and `ToolTip`) actually correct?**
  _`VeriAraclari` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `PDFYoneticisi` (e.g. with `ToolTip` and `YoklamaUygulamasi`) actually correct?**
  _`PDFYoneticisi` has 2 INFERRED edges - model-reasoned connections that need verification._