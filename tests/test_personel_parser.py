import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api
from excel_motoru import ExcelMotoru
from araclar import VeriAraclari
import dependencies

app = api.app
client = TestClient(app)

@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    """Her API testi gerçek kullanıcı veritabanından tamamen bağımsız çalışır."""
    test_db = api.VeritabaniYoneticisi(str(tmp_path / "test_parser.db"))
    monkeypatch.setattr(api, "db", test_db)
    monkeypatch.setattr(dependencies, "db", test_db)
    import routes.personel
    monkeypatch.setattr(routes.personel, "db", test_db)
    return test_db

def test_mebbis_mi_kontrol_et():
    dosya_yolu = "PERSONEL DENEME.xls"
    if os.path.exists(dosya_yolu):
        assert ExcelMotoru.mebbis_mi_kontrol_et(dosya_yolu) is True

def test_mebbis_personel_oku():
    dosya_yolu = "PERSONEL DENEME.xls"
    if not os.path.exists(dosya_yolu):
        pytest.skip("PERSONEL DENEME.xls bulunamadı.")

    personeller = ExcelMotoru.mebbis_personel_oku(dosya_yolu)
    assert len(personeller) == 7

    # 1. Ali Yazar (Memur(Ş), AB Rh(+), 3-2)
    ali = next((p for p in personeller if p["tc_no"] == "12345678910"), None)
    assert ali is not None
    assert "YAZAR" in VeriAraclari.tr_upper(ali["ad_soyad"])
    assert ali["unvan"] == "Memur(Ş)"
    assert ali["gorev"] == "Memur(Ş)"
    assert ali["brans"] == "-"
    assert ali["kariyer"] == "-"
    assert ali["kan_grubu"] == "AB Rh(+)"
    assert ali["kademe_derece"] == "3-2"
    assert ali["cinsiyet"] == "E"
    assert "Ön Lisans" in ali["ogrenim_durumu"]

    # 2. Veli Mustafa Yılmaz (Öğretmen, Matematik, Uzman Öğretmen)
    veli = next((p for p in personeller if p["tc_no"] == "10987654321"), None)
    assert veli is not None
    assert veli["unvan"] == "Öğretmen"
    assert veli["gorev"] == "Öğretmen"
    assert veli["brans"] == "Matematik"
    assert veli["kariyer"] == "Uzman Öğretmen"

    # 3. Muhtar Kent (Müdür Yardımcısı, Bilgisayar ve Öğretim Teknolojileri, Uzman Öğretmen)
    muhtar = next((p for p in personeller if p["tc_no"] == "25252525252"), None)
    assert muhtar is not None
    assert muhtar["unvan"] == "Öğretmen"
    assert muhtar["gorev"] == "Müdür Yardımcısı"
    assert muhtar["brans"] == "Bilgisayar ve Öğretim Teknolojileri"
    assert muhtar["kariyer"] == "Uzman Öğretmen"

    # 4. Muhteşem Donat (Arşiv No K-A2, B Rh(+), 1-4, Müzik, Başöğretmen)
    muhtesem = next((p for p in personeller if p["tc_no"] == "0123456789"), None)
    assert muhtesem is not None
    assert muhtesem["unvan"] == "Öğretmen"
    assert muhtesem["gorev"] == "Öğretmen"
    assert muhtesem["brans"] == "Müzik"
    assert muhtesem["kariyer"] == "Başöğretmen"
    assert muhtesem["arsiv_no"] == "K-A2"
    assert muhtesem["kan_grubu"] == "B Rh(+)"
    assert muhtesem["kademe_derece"] == "1-4"

    # 5. Polat Alemdar (TC 34343434343, A Rh(+), Emekli Sicil 15935723, Türk Dili ve Edebiyatı, Başöğretmen)
    polat = next((p for p in personeller if p["tc_no"] == "34343434343"), None)
    assert polat is not None
    assert polat["unvan"] == "Öğretmen"
    assert polat["gorev"] == "Öğretmen"
    assert polat["brans"] == "Türk Dili ve Edebiyatı"
    assert polat["kariyer"] == "Başöğretmen"
    assert polat["kan_grubu"] == "A Rh(+)"
    assert polat["emekli_sicil_no"] == "15935723"

def test_personeller_detayli_alanlar_doner():
    client.post("/personel-ekle", json={"ad": "DETAY TEST PERSONEL", "unvan": "Öğretmen", "gorev": "Öğretmen", "brans": "Kimya"})
    res = client.get("/personeller")
    assert res.status_code == 200
    data = res.json()
    assert "personeller" in data
    assert len(data["personeller"]) > 0
    ilk = data["personeller"][0]
    assert "unvan" in ilk
    assert "tc_no" in ilk
    assert "kan_grubu" in ilk
    assert "kademe_derece" in ilk
    assert "ogrenim_durumu" in ilk
    assert "grup" in ilk

def test_personel_profil_guncelle():
    client.post("/personel-ekle", json={"ad": "TEST PROFİL PERSONELİ", "unvan": "Memur", "gorev": "Memur", "brans": "-"})

    guncelle_veri = {
        "ad_soyad": "TEST PROFİL PERSONELİ",
        "tc_no": "99988877766",
        "unvan": "Öğretmen",
        "brans": "Fizik",
        "gorev": "Müdür Yardımcısı",
        "kariyer": "Uzman Öğretmen",
        "grup": "Sözleşmeli",
        "kan_grubu": "0 Rh(+)",
        "kademe_derece": "2-1",
        "telefon": "05551112233",
        "notlar": "Test özel notu"
    }
    res = client.post("/personel-profil-guncelle", json=guncelle_veri)
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    tum = client.get("/personeller").json()["personeller"]
    bulunan = next((p for p in tum if p["ad"] == "TEST PROFİL PERSONELİ"), None)
    assert bulunan is not None
    assert bulunan["tc_no"] == "99988877766"
    assert bulunan["unvan"] == "Öğretmen"
    assert bulunan["gorev"] == "Müdür Yardımcısı"
    assert bulunan["brans"] == "Fizik"
    assert bulunan["kariyer"] == "Uzman Öğretmen"
    assert bulunan["grup"] == "Sözleşmeli"
    assert bulunan["kan_grubu"] == "0 Rh(+)"
    assert bulunan["telefon"] == "05551112233"
    assert bulunan["notlar"] == "Test özel notu"

def test_mebbis_excel_yukle_ve_personeller_getir_end_to_end(tmp_path):
    dosya_yolu = "PERSONEL DENEME.xls"
    if not os.path.exists(dosya_yolu):
        pytest.skip("PERSONEL DENEME.xls bulunamadı.")

    import shutil
    from routes.personel import _personel_excel_yukle_dogrudan

    # İzole geçici dosya üzerinde çalış
    temp_dosya = str(tmp_path / "personel_yukle_test.xls")
    shutil.copyfile(dosya_yolu, temp_dosya)

    sonuc = _personel_excel_yukle_dogrudan(temp_dosya, ".xls")
    assert sonuc["basarili"] is True

    res = client.get("/personeller")
    assert res.status_code == 200
    personeller = res.json()["personeller"]
    assert len(personeller) == 7

    # Veli Mustafa Yılmaz kontrolü
    veli = next((p for p in personeller if p["tc_no"] == "10987654321"), None)
    assert veli is not None
    assert veli["unvan"] == "Öğretmen"
    assert veli["gorev"] == "Öğretmen"
    assert veli["brans"] == "Matematik"
    assert veli["kariyer"] == "Uzman Öğretmen"

    # Muhtar Kent (Müdür Yardımcısı) kontrolü
    muhtar = next((p for p in personeller if p["tc_no"] == "25252525252"), None)
    assert muhtar is not None
    assert muhtar["unvan"] == "Öğretmen"
    assert muhtar["gorev"] == "Müdür Yardımcısı"
    assert muhtar["brans"] == "Bilgisayar ve Öğretim Teknolojileri"
    assert muhtar["kariyer"] == "Uzman Öğretmen"

    # Ali Yazar (Memur(Ş)) kontrolü
    ali = next((p for p in personeller if p["tc_no"] == "12345678910"), None)
    assert ali is not None
    assert ali["unvan"] == "Memur(Ş)"
    assert ali["gorev"] == "Memur(Ş)"
    assert ali["brans"] == "-"
    assert ali["kariyer"] == "-"
    assert ali["aktif"] == 1

def test_personel_baska_kuruma_gorevlendirildi_pasif():
    # 1. Personel Ekle
    client.post("/personel-ekle", json={"ad": "GÖREVLENDİRİLEN ÖĞRETMEN", "unvan": "Öğretmen", "gorev": "Öğretmen", "brans": "Biyoloji"})

    # 2. Başka kuruma görevlendirildi olarak güncelle (aktif = 0)
    guncelle = {
        "ad_soyad": "GÖREVLENDİRİLEN ÖĞRETMEN",
        "tc_no": "11122233344",
        "unvan": "Öğretmen",
        "brans": "Biyoloji",
        "gorev": "Öğretmen",
        "grup": "Kadrolu",
        "aktif": 0
    }
    res = client.post("/personel-profil-guncelle", json=guncelle)
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # 3. /personeller sorgusunda aktif=0 olduğunu doğrula
    tum = client.get("/personeller").json()["personeller"]
    bulunan = next((p for p in tum if p["ad"] == "GÖREVLENDİRİLEN ÖĞRETMEN"), None)
    assert bulunan is not None
    assert bulunan["aktif"] == 0

    # 4. Tekrar aktif yap (aktif = 1)
    guncelle["aktif"] = 1
    res2 = client.post("/personel-profil-guncelle", json=guncelle)
    assert res2.status_code == 200
    tum2 = client.get("/personeller").json()["personeller"]
    bulunan2 = next((p for p in tum2 if p["ad"] == "GÖREVLENDİRİLEN ÖĞRETMEN"), None)
    assert bulunan2 is not None
    assert bulunan2["aktif"] == 1

def test_yeni_personel_profil_ekle_dogrudan():
    # Profil modalı üzerinden sıfırdan yeni personel ekleme (id verilmeden)
    yeni_personel_veri = {
        "ad_soyad": "YENİ PROFİL İLE EKLENEN PERSONEL",
        "tc_no": "55544433322",
        "unvan": "Memur",
        "brans": "-",
        "gorev": "VHKİ",
        "grup": "Kadrolu",
        "kariyer": "-",
        "kan_grubu": "A Rh(+)",
        "telefon": "05321112233",
        "aktif": 1
    }
    res = client.post("/personel-profil-guncelle", json=yeni_personel_veri)
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    tum = client.get("/personeller").json()["personeller"]
    bulunan = next((p for p in tum if p["ad"] == "YENİ PROFİL İLE EKLENEN PERSONEL"), None)
    assert bulunan is not None
    assert bulunan["tc_no"] == "55544433322"
    assert bulunan["unvan"] == "Memur"
    assert bulunan["gorev"] == "VHKİ"
    assert bulunan["telefon"] == "05321112233"
    assert bulunan["aktif"] == 1


def test_personel_dogal_harf_bicimi_korunur():
    # Doğal yazımlı personel ekle
    client.post("/personel-ekle", json={"ad": "Ahmet Yılmaz", "unvan": "Öğretmen", "gorev": "Müdür Yardımcısı", "brans": "Tarih"})

    # Başka kuruma görevlendirildi (pasif) olarak güncelle
    res = client.post("/personel-profil-guncelle", json={
        "ad_soyad": "Ahmet Yılmaz",
        "tc_no": "12312312312",
        "unvan": "Öğretmen",
        "gorev": "Müdür Yardımcısı",
        "brans": "Tarih",
        "aktif": 0
    })
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # Adın büyük harfe (AHMET YILMAZ) dönüşmediğini, doğal yazımını koruduğunu doğrula
    tum = client.get("/personeller").json()["personeller"]
    bulunan = next((p for p in tum if p["ad"] == "Ahmet Yılmaz"), None)
    assert bulunan is not None
    assert bulunan["ad"] == "Ahmet Yılmaz"
    assert bulunan["gorev"] == "Müdür Yardımcısı"
    assert bulunan["aktif"] == 0


def test_akilli_kademe_derece_tarih_duzeltme():
    from datetime import datetime, date
    import pandas as pd

    # 1. datetime / Timestamp / date nesneleri (Excel'in 1/4'ü 1 Nisan tarihine çevirmesi)
    dt1 = datetime(2026, 4, 1)
    assert ExcelMotoru.akilli_kademe_derece(dt1) == "1/4"

    ts1 = pd.Timestamp("2026-04-01")
    assert ExcelMotoru.akilli_kademe_derece(ts1) == "1/4"

    d1 = date(2026, 4, 1)
    assert ExcelMotoru.akilli_kademe_derece(d1) == "1/4"

    # 2. ISO Tarih Stringi
    assert ExcelMotoru.akilli_kademe_derece("2026-04-01") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("2026-04-01 00:00:00") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("2026-03-02") == "2/3"

    # 3. Türkçe ay isimleri (1 Nisan, 1-Nis vb.)
    assert ExcelMotoru.akilli_kademe_derece("1 Nisan") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("1-Nis") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("3-Şub") == "3/2"

    # 4. Standart oranlar
    assert ExcelMotoru.akilli_kademe_derece("1/4") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("1-4") == "1/4"
    assert ExcelMotoru.akilli_kademe_derece("3/2") == "3/2"

    # 5. Boş/Geçersiz durumlar
    assert ExcelMotoru.akilli_kademe_derece(None) == "-"
    assert ExcelMotoru.akilli_kademe_derece("") == "-"
    assert ExcelMotoru.akilli_kademe_derece("nan") == "-"


def test_mebbis_gorevlendirme_dosya_ve_tablo_okuma():
    dosya_yolu = "görevlendirme persoel.xlsx"
    if os.path.exists(dosya_yolu):
        assert ExcelMotoru.mebbis_gorevlendirme_mi(dosya_yolu) is True
        personeller = ExcelMotoru.mebbis_gorevlendirme_personel_oku(dosya_yolu)
        assert len(personeller) > 0
        ilk = personeller[0]
        assert "ad_soyad" in ilk
        assert ilk["grup"] == "Görevlendirme"
        # Derece/Kademe'nin 1 Nisan yerine 1/4 olarak çözümlendiğini doğrula
        assert ilk["kademe_derece"] in ["1/4", "1-4", "4/1"] or "/" in ilk["kademe_derece"]

    # Simüle edilmiş pano metni (TSV) ile test
    tsv_metin = (
        "TC Kimlik No\tAdı\tSoyadı\tİstihdam Tipi\tKariyer Basamağı\tAy.Der/Kad.\tGörevi\tAlanı\tGörev Yeri\tDurumu\tCinsiyeti\n"
        "99887766554\tCanan\tKaya\tKadrolu\tUzman Öğretmen\t1 Nisan\tÖğretmen\tFizik\tMerkez Lisesi\tGörevde\tKadın\n"
    )
    assert ExcelMotoru.mebbis_gorevlendirme_mi(tsv_metin) is True
    tsv_personeller = ExcelMotoru.mebbis_gorevlendirme_personel_oku(tsv_metin)
    assert len(tsv_personeller) == 1
    p = tsv_personeller[0]
    assert p["ad_soyad"] == "Canan KAYA"
    assert p["tc_no"] == "99887766554"
    assert p["grup"] == "Görevlendirme"
    assert p["kademe_derece"] == "1/4"  # '1 Nisan' otomatik '1/4' yapıldı!
    assert p["brans"] == "Fizik"
    assert p["cinsiyet"] == "K"


def test_personel_pano_yukle_ve_upsert():
    # 1. Önce kadrolu bir personel ekle
    client.post("/personel-ekle", json={
        "ad": "Kadrolu Mehmet",
        "unvan": "Öğretmen",
        "gorev": "Öğretmen",
        "brans": "Kimya",
        "grup": "Kadrolu"
    })

    # 2. MEBBİS Görevlendirme tablosunu pano endpoint'ine gönder
    tsv_metin = (
        "TC Kimlik No\tAdı\tSoyadı\tİstihdam Tipi\tKariyer Basamağı\tAy.Der/Kad.\tGörevi\tAlanı\tGörev Yeri\tDurumu\tCinsiyeti\n"
        "11223344556\tZeynep\tDemir\tKadrolu\tUzman Öğretmen\t1/4\tÖğretmen\tBiyoloji\tFen Lisesi\tGörevde\tKadın\n"
    )
    res = client.post("/personel-pano-yukle", json={
        "icerik": tsv_metin,
        "yukleme_tipi": "mebbis_gorevlendirme"
    })
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # 3. UPSERT Doğrulaması: Hem 'Kadrolu Mehmet' hem de 'Zeynep DEMİR' listede olmalı (birbirini silmedi)
    tum = client.get("/personeller").json()["personeller"]
    adlar = [p["ad"] for p in tum]
    assert any("Kadrolu Mehmet" in a or "MEHMET" in a for a in adlar)
    assert any("Zeynep" in a and "DEMİR" in a for a in adlar)


def test_personel_sablon_indir_gorevlendirme():
    res = client.get("/personel-sablon-indir/gorevlendirme")
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert "MEBBIS_Gorevlendirme_Personel_Sablonu.xlsx" in res.headers["content-disposition"]
    assert len(res.content) > 1000


def test_personel_pano_yukle_uyumsuz_sutun_sayisi_zirhi():
    # Kullanıcının karşılaştığı durum: Line 1 (23 sütun), Line 2 (24 sütun)
    # Önceden pandas: "Expected 23 fields in line 2, saw 24" hatası veriyordu.
    header_23 = "TC Kimlik No\tAdı\tSoyadı\tİstihdam Tipi\tKariyer Basamağı\tÖğretmenlik Kariyer Basamağı\tBaba Adı\tDoğum Yılı\tKadro\tAy.Der/Kad.\tSon Terfi Tarihi\tEmekli Sicil No\tKurum Sicil No\tKadro Ünvanı\tGörevi\tAlanı\tGörev Yeri\tİli\tİlçesi\tDurumu\tCinsiyeti\tArşiv No\tAnd/BİLSEM Yerleştirme Bilgisi"
    data_24 = "\t12345678910\tERDAL\tKÖMÜRCÜ\tKadrolu\tÖğretmen\tUzman Öğretmen\tABUZER\t1984\t1\t1 Nisan\t2026-08-29\t12345678\t1234\tÖğretmen\tÖğretmen\tRehberlik\tİlçe Milli Eğitim Müdürlüğü\tESKİŞEHİR\tTEPEBAŞI\tGörevde\tErkek\t\t"

    tsv_metin = f"{header_23}\n{data_24}"

    # 1. ExcelMotoru.mebbis_gorevlendirme_personel_oku doğrudan çağrılır
    personeller = ExcelMotoru.mebbis_gorevlendirme_personel_oku(tsv_metin)
    assert len(personeller) == 1
    p = personeller[0]
    assert p["ad_soyad"] == "Erdal KÖMÜRCÜ"  # ALL CAPS 'ERDAL KÖMÜRCÜ' -> 'Erdal KÖMÜRCÜ' yapıldı!
    assert p["tc_no"] == "12345678910"
    assert p["kademe_derece"] == "1/4"  # '1 Nisan' -> '1/4'
    assert p["brans"] == "Rehberlik"
    assert p["grup"] == "Görevlendirme"

    # 2. Endpoint üzerinden çağrılır
    res = client.post("/personel-pano-yukle", json={
        "icerik": tsv_metin,
        "yukleme_tipi": "mebbis_gorevlendirme"
    })
    assert res.status_code == 200
    assert res.json()["basarili"] is True


def test_mebbis_kadrolu_pano_ve_tablo_okuma():
    # MEBBİS web sayfasından kopyalanan Kadrolu personel tablosu simülasyonu
    kadrolu_tsv = (
        "Sıra\tTC Kimlik No\tAdı\tSoyadı\tKadro Ünvanı\tGörevi\tBranşı\tKariyer Basamağı\tDerece / Kademe\tCinsiyeti\n"
        "1\t98765432101\tAHMET CEVDET\tPAŞA\tÖğretmen\tMüdür\tTarih\tBaşöğretmen\t1/4\tErkek\n"
        "2\t87654321098\tFATMA ALİYE\tTOPUZ\tÖğretmen\tÖğretmen\tTürk Dili ve Edebiyatı\tUzman Öğretmen\t1 Nisan\tKadın\n"
    )

    # 1. ExcelMotoru.mebbis_personel_oku (Tabular fallback)
    personeller = ExcelMotoru.mebbis_personel_oku(kadrolu_tsv)
    assert len(personeller) == 2

    ilk = personeller[0]
    assert ilk["ad_soyad"] == "Ahmet Cevdet PAŞA"
    assert ilk["tc_no"] == "98765432101"
    assert ilk["unvan"] == "Öğretmen"
    assert ilk["gorev"] == "Müdür"
    assert ilk["brans"] == "Tarih"
    assert ilk["cinsiyet"] == "E"
    assert ilk["grup"] == "Kadrolu"

    ikinci = personeller[1]
    assert ikinci["ad_soyad"] == "Fatma Aliye TOPUZ"
    assert ikinci["tc_no"] == "87654321098"
    assert ikinci["kademe_derece"] == "1/4"  # '1 Nisan' -> '1/4'
    assert ikinci["cinsiyet"] == "K"

    # 2. /personel-pano-yukle endpoint'i ile MEBBİS Kadrolu aktarımı
    res = client.post("/personel-pano-yukle", json={
        "icerik": kadrolu_tsv,
        "yukleme_tipi": "mebbis_kadrolu"
    })
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # 3. Veritabanından doğrula
    tum = client.get("/personeller").json()["personeller"]
    p_ahmet = next((p for p in tum if p["tc_no"] == "98765432101"), None)
    assert p_ahmet is not None
    assert p_ahmet["ad"] == "Ahmet Cevdet PAŞA"
    assert p_ahmet["cinsiyet"] == "E"


def test_personel_hiyerarsik_gorev_siralama_ve_bilesenler():
    # 1. Frontend bileşen doğrulamaları (5 sütun, detaylı switch, kadro sütunu)
    modal_path = os.path.join("frontend", "components", "personel_yonetim_modal.html")
    assert os.path.exists(modal_path)
    with open(modal_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "detayli-switch-btn" in html
    assert "detayli-switch-thumb" in html
    assert "Türü / Kadro" in html
    assert "getGorevKademesi" in html

    # 2. Hiyerarşik görev önceliği algoritması simülasyonu
    def get_kademe(p):
        gorev_str = f"{p.get('gorev', '')} {p.get('unvan', '')}".upper().strip()
        if "MÜDÜR" in gorev_str and not any(k in gorev_str for k in ["YARDIMCI", "BAŞYARDIMCI", "YRD"]):
            return 1
        if "MÜDÜR" in gorev_str and any(k in gorev_str for k in ["YARDIMCI", "BAŞYARDIMCI", "YRD"]):
            return 2
        return 3

    personeller = [
        {"ad": "Zeynep KAYA", "gorev": "Öğretmen", "unvan": "Öğretmen"},
        {"ad": "Hasan YILDIRIM", "gorev": "Müdür Yardımcısı", "unvan": "Öğretmen"},
        {"ad": "Kemal ATATÜRK", "gorev": "Müdür", "unvan": "Öğretmen"},
        {"ad": "Ali VELİ", "gorev": "Müdür Yardımcısı", "unvan": "Öğretmen"},
        {"ad": "Bekir MEMUR", "gorev": "Memur", "unvan": "Memur"},
    ]

    sirali = sorted(personeller, key=lambda p: (get_kademe(p), p["ad"]))

    # Beklenen sıra:
    # 1. Müdür (Kemal ATATÜRK)
    # 2. Müdür Yardımcıları alfabetik: Ali VELİ, ardından Hasan YILDIRIM
    # 3. Diğer personeller alfabetik: Bekir MEMUR, ardından Zeynep KAYA
    assert sirali[0]["ad"] == "Kemal ATATÜRK"
    assert sirali[1]["ad"] == "Ali VELİ"
    assert sirali[2]["ad"] == "Hasan YILDIRIM"
    assert sirali[3]["ad"] == "Bekir MEMUR"
    assert sirali[4]["ad"] == "Zeynep KAYA"


def test_personel_uzun_sureli_saglik_izni_durumu():
    """657 SK Md. 105 uyarınca uzun süreli sağlık izni (aktif=2) durumunun kaydı ve listelenmesi testi."""
    # 1. Yeni personel ekle
    res_ekle = client.post("/personel-ekle", json={
        "ad": "Dr. Ayşe YILMAZ",
        "unvan": "Öğretmen",
        "gorev": "Öğretmen",
        "brans": "Biyoloji",
        "grup": "Kadrolu"
    })
    assert res_ekle.status_code == 200

    tum = client.get("/personeller").json()["personeller"]
    p = next((x for x in tum if x["ad"] == "Dr. Ayşe YILMAZ"), None)
    assert p is not None
    assert p["aktif"] == 1

    # 2. Personel profilini aktif=2 (Uzun Süreli Sağlık İzninde) olarak güncelle
    res_profil = client.post("/personel-profil-guncelle", json={
        "id": p["id"],
        "ad_soyad": "Dr. Ayşe YILMAZ",
        "unvan": "Öğretmen",
        "gorev": "Öğretmen",
        "brans": "Biyoloji",
        "grup": "Kadrolu",
        "aktif": 2
    })
    assert res_profil.status_code == 200
    assert res_profil.json()["basarili"] is True

    # 3. Personeller listesinden doğrula
    tum_guncel = client.get("/personeller").json()["personeller"]
    p_guncel = next((x for x in tum_guncel if x["ad"] == "Dr. Ayşe YILMAZ"), None)
    assert p_guncel is not None
    assert p_guncel["aktif"] == 2

    # 4. Aktif=0 (Başka Kuruma Görevlendirildi) güncellemesi de sorunsuz çalışmalı
    res_pasif = client.post("/personel-profil-guncelle", json={
        "id": p["id"],
        "ad_soyad": "Dr. Ayşe YILMAZ",
        "unvan": "Öğretmen",
        "gorev": "Öğretmen",
        "brans": "Biyoloji",
        "grup": "Kadrolu",
        "aktif": 0
    })
    assert res_pasif.status_code == 200
    assert client.get("/personeller").json()["personeller"][0]["aktif"] == 0

    # 5. Frontend modal kontrolleri (pp_aktif_durum select ve badge'leri)
    profil_modal_path = os.path.join("frontend", "components", "personel_profil_modal.html")
    assert os.path.exists(profil_modal_path)
    with open(profil_modal_path, "r", encoding="utf-8") as f:
        profil_html = f.read()
    assert "pp_aktif_durum" in profil_html
    assert "Uzun Süreli Sağlık İzninde" in profil_html

    yonetim_modal_path = os.path.join("frontend", "components", "personel_yonetim_modal.html")
    assert os.path.exists(yonetim_modal_path)
    with open(yonetim_modal_path, "r", encoding="utf-8") as f:
        yonetim_html = f.read()
    assert "getDurumBadgeHtml" in yonetim_html


def test_personel_tum_uzun_sureli_izin_turleri():
    """Tüm uzun süreli izin türlerinin (Doğum, Aylıksız, Refakat, Askerlik, Yurtdışı, Sendika) uçtan uca testi."""
    # 1. /personel-durumlari endpoint testi
    res_durumlar = client.get("/personel-durumlari")
    assert res_durumlar.status_code == 200
    data = res_durumlar.json()
    assert data["basarili"] is True
    durumlar = data["durumlar"]
    # 1: Aktif, 0: Başka Kurumda, 2: Sağlık, 3: Doğum, 4: Aylıksız, 5: Refakat, 6: Askerlik, 7: Yurtdışı/Eğitim, 8: Sendika
    for kod in ["0", "1", "2", "3", "4", "5", "6", "7", "8"]:
        assert kod in durumlar, f"Durum kodu {kod} durumlar sözlüğünde bulunamadı."
        assert "renk" in durumlar[kod]
        assert "yasal_dayanak" in durumlar[kod]

    # 2. Personel ekle ve her bir statüyü tek tek güncelle
    res_ekle = client.post("/personel-ekle", json={
        "ad": "Mehmet Öğretmen",
        "unvan": "Öğretmen",
        "gorev": "Öğretmen",
        "brans": "Fizik",
        "grup": "Kadrolu"
    })
    assert res_ekle.status_code == 200
    p_id = client.get("/personeller").json()["personeller"][0]["id"]

    izin_testleri = [
        (3, "Doğum / Analık İzninde"),
        (4, "Aylıksız İzninde"),
        (5, "Refakat İzninde"),
        (6, "Askerlik Görevinde"),
        (7, "Yurtdışı / Eğitim İzninde"),
        (8, "Sendika Görevinde"),
        (1, "Aktif (Görevde)")
    ]

    for kod, aciklama in izin_testleri:
        res_up = client.post("/personel-profil-guncelle", json={
            "id": p_id,
            "ad_soyad": "Mehmet Öğretmen",
            "unvan": "Öğretmen",
            "gorev": "Öğretmen",
            "brans": "Fizik",
            "grup": "Kadrolu",
            "aktif": kod
        })
        assert res_up.status_code == 200
        assert res_up.json()["basarili"] is True
        
        # /personeller sorgusunda güncel aktif kodunu doğrula
        tum = client.get("/personeller").json()["personeller"]
        p = next((x for x in tum if x["id"] == p_id), None)
        assert p is not None
        assert p["aktif"] == kod, f"Beklenen aktif={kod} ({aciklama}), ancak {p['aktif']} geldi."

    # 3. Frontend JS dosyasında PERSONEL_DURUMLARI ve getPersonelDurumBadgeHtml varlığı
    js_path = os.path.join("frontend", "js", "personel_teblig.js")
    assert os.path.exists(js_path)
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    assert "PERSONEL_DURUMLARI" in js_content
    assert "getPersonelDurumBilgisi" in js_content
    assert "getPersonelDurumBadgeHtml" in js_content
    assert "Doğum / Analık İzninde" in js_content
    assert "Aylıksız İzninde" in js_content
    assert "Refakat İzninde" in js_content
    assert "Askerlik Görevinde" in js_content
    assert "Yurtdışı / Lisansüstü Eğitim İzninde" in js_content
    assert "Sendika Görevinde" in js_content





