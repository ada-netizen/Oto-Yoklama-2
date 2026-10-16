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
    assert bulunan["gorev"] == "MÜDÜR YARDIMCISI"
    assert bulunan["brans"] == "FİZİK"
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



