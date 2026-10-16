import os
import sys
import pytest
import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api
import dependencies
from routes.personel import _personel_excel_yukle_dogrudan, pdf_klasoru_hazirla

app = api.app
client = TestClient(app)

@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    """Her API testi gerçek kullanıcı veritabanından tamamen bağımsız çalışır."""
    test_db = api.VeritabaniYoneticisi(str(tmp_path / "test_excel_yedek.db"))
    monkeypatch.setattr(api, "db", test_db)
    monkeypatch.setattr(dependencies, "db", test_db)
    import routes.personel
    monkeypatch.setattr(routes.personel, "db", test_db)

    # PDF / Excel çıkış klasörünü de izole edelim
    sahte_klasor = str(tmp_path / "ciktilar")
    os.makedirs(sahte_klasor, exist_ok=True)
    monkeypatch.setattr(routes.personel, "pdf_klasoru_hazirla", lambda: (sahte_klasor, {}))

    return test_db

def _ornek_personelleri_ekle(test_db):
    """Farklı istihdam türlerinden zengin 3 personel kaydı ekler."""
    kayitlar = [
        (
            "AHMET YILMAZ", "11111111110", "Öğretmen", "Matematik", "Öğretmen", "Kadrolu",
            "Ankara / Çankaya", "Atatürk Anadolu Lisesi", "123456", "01/09/2020",
            "Uzman Öğretmen", "1/4", "Yüksek Lisans", "E", "A Rh(+)", "15/05/1985",
            "01/09/2010", "SICIL-001", "EMEKLI-999", "ARSIV-77", "05551112233",
            "ahmet@meb.k12.tr", "Sınav komisyonunda görevli", 1
        ),
        (
            "AYŞE KAYA", "22222222220", "Memur", "-", "Yazı İşleri", "Kadrolu",
            "Ankara / Keçiören", "Atatürk Anadolu Lisesi", "123456", "15/02/2021",
            "-", "3/2", "Lisans", "K", "0 Rh(+)", "20/11/1990",
            "15/02/2015", "SICIL-002", "EMEKLI-888", "ARSIV-88", "05552223344",
            "ayse@meb.k12.tr", "Evrak kayıt sorumlusu", 1
        ),
        (
            "MEHMET DEMİR", "33333333330", "Katılımcı", "-", "Temizlik ve Bakım", "İUP",
            "Ankara / Mamak", "Atatürk Anadolu Lisesi", "123456", "01/10/2024",
            "-", "-", "İlköğretim", "E", "B Rh(+)", "10/01/1995",
            "01/10/2024", "", "", "", "05553334455",
            "", "Haftalık 3 gün çalışır", 0
        )
    ]

    test_db.cursor.executemany("""
        INSERT INTO personel (
            ad_soyad, tc_no, unvan, brans, gorev, grup, il_ilce, kurum_adi,
            kurum_kodu, kurumda_baslama, kariyer, kademe_derece, ogrenim_durumu,
            cinsiyet, kan_grubu, dogum_tarihi, goreve_baslama, kurum_sicil_no,
            emekli_sicil_no, arsiv_no, telefon, eposta, notlar, aktif
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, kayitlar)
    test_db.conn.commit()


def test_bos_personel_listesi_indir(isolated_database):
    """Veritabanı boşken Excel indirme hata mesajı dönmelidir."""
    resp_ozet = client.get("/personel-excel-indir?format=ozet")
    assert resp_ozet.status_code == 200
    assert resp_ozet.json()["basarili"] is False
    assert "boş" in resp_ozet.json()["mesaj"]

    resp_tam = client.get("/personel-excel-indir?format=tam")
    assert resp_tam.status_code == 200
    assert resp_tam.json()["basarili"] is False
    assert "boş" in resp_tam.json()["mesaj"]


def test_personel_excel_indir_ozet(isolated_database, tmp_path):
    """Özet Excel indirme 4 sütun içermelidir."""
    _ornek_personelleri_ekle(isolated_database)

    resp = client.get("/personel-excel-indir?format=ozet")
    assert resp.status_code == 200
    assert resp.json()["basarili"] is True

    cikti_yolu = tmp_path / "ciktilar" / "Personel_Listesi.xlsx"
    assert cikti_yolu.exists()

    df = pd.read_excel(str(cikti_yolu))
    assert list(df.columns) == ["Ad Soyad", "Branş", "Görev", "Grup"]
    assert len(df) == 3


def test_personel_excel_indir_tam_yedek(isolated_database, tmp_path):
    """Tam Yedek Excel indirme 24 sütunun tamamını içermelidir."""
    _ornek_personelleri_ekle(isolated_database)

    resp = client.get("/personel-excel-indir?format=tam")
    assert resp.status_code == 200
    assert resp.json()["basarili"] is True

    cikti_yolu = tmp_path / "ciktilar" / "Personel_Veritabani_Tam_Yedek.xlsx"
    assert cikti_yolu.exists()

    df = pd.read_excel(str(cikti_yolu), dtype=str)
    assert len(df.columns) == 24
    assert len(df) == 3

    # Önemli sütunların varlığını kontrol et
    beklenen_sutunlar = [
        "Ad Soyad", "T.C. Kimlik No", "Unvan", "Branş", "Görev", "Grup / Statü",
        "Kariyer Basamağı", "Derece / Kademe", "Öğrenim Durumu", "Cinsiyet",
        "Kan Grubu", "Doğum Tarihi", "Göreve Başlama", "Kurum Adı", "Kurum Kodu",
        "İl / İlçe", "Kurumda Başlama", "Kurum Sicil No", "Emekli / SGK Sicil No",
        "Arşiv No", "Telefon", "E-Posta", "Notlar", "Aktif Durum (1:Aktif, 0:Pasif)"
    ]
    assert list(df.columns) == beklenen_sutunlar

    # Değerlerin doğruluğunu kontrol et
    ahmet = df[df["Ad Soyad"] == "AHMET YILMAZ"].iloc[0]
    assert ahmet["T.C. Kimlik No"] == "11111111110"
    assert ahmet["Kariyer Basamağı"] == "Uzman Öğretmen"
    assert ahmet["Derece / Kademe"] == "1/4"
    assert ahmet["Telefon"] == "05551112233"
    assert str(ahmet["Aktif Durum (1:Aktif, 0:Pasif)"]) == "1"

    mehmet = df[df["Ad Soyad"] == "MEHMET DEMİR"].iloc[0]
    assert mehmet["Grup / Statü"] == "İUP"
    assert str(mehmet["Aktif Durum (1:Aktif, 0:Pasif)"]) == "0"


def test_round_trip_tam_yedek_kurtarma(isolated_database, tmp_path):
    """
    TAM KURTARMA ZIRHI:
    1. Personeller veritabanına eklenir.
    2. Tam Yedek Excel olarak indirilir.
    3. Veritabanındaki 'personel' tablosu TAMAMEN SİLİNİR (Simüle Edilmiş Veri Kaybı).
    4. İndirilen Tam Yedek Excel geri yüklenir.
    5. Tüm 24 alanın %100 kayıpsız geri geldiği doğrulanır.
    """
    _ornek_personelleri_ekle(isolated_database)

    # 1. Tam Yedek İndir
    resp = client.get("/personel-excel-indir?format=tam")
    assert resp.status_code == 200
    yedek_dosyasi = str(tmp_path / "ciktilar" / "Personel_Veritabani_Tam_Yedek.xlsx")
    assert os.path.exists(yedek_dosyasi)

    # 2. Veritabanını tamamen boşalt
    isolated_database.cursor.execute("DELETE FROM personel")
    isolated_database.conn.commit()

    isolated_database.cursor.execute("SELECT COUNT(*) FROM personel")
    assert isolated_database.cursor.fetchone()[0] == 0  # Kesinlikle 0 personel kaldı!

    # 3. Tam Yedek Excel dosyasını geri yükle
    sonuc = _personel_excel_yukle_dogrudan(yedek_dosyasi, ".xlsx")
    assert sonuc["basarili"] is True
    assert "tam yedeğinden" in sonuc["mesaj"]
    assert "3 personel" in sonuc["mesaj"]

    # 4. Veritabanını 24 alan bazında sorgula ve karşılaştır
    isolated_database.cursor.execute("""
        SELECT ad_soyad, tc_no, unvan, brans, gorev, grup, il_ilce, kurum_adi,
               kurum_kodu, kurumda_baslama, kariyer, kademe_derece, ogrenim_durumu,
               cinsiyet, kan_grubu, dogum_tarihi, goreve_baslama, kurum_sicil_no,
               emekli_sicil_no, arsiv_no, telefon, eposta, notlar, aktif
        FROM personel ORDER BY ad_soyad
    """)
    rows = isolated_database.cursor.fetchall()
    assert len(rows) == 3

    # Ahmet Yılmaz kontrolü
    ahmet = rows[0]
    assert ahmet[0] == "AHMET YILMAZ"
    assert ahmet[1] == "11111111110"
    assert ahmet[2] == "Öğretmen"
    assert ahmet[3] == "MATEMATİK" or ahmet[3] == "Matematik"
    assert ahmet[4] == "ÖĞRETMEN" or ahmet[4] == "Öğretmen"
    assert ahmet[5] == "Kadrolu"
    assert ahmet[6] == "Ankara / Çankaya"
    assert ahmet[7] == "Atatürk Anadolu Lisesi"
    assert ahmet[8] == "123456"
    assert ahmet[9] == "01/09/2020"
    assert ahmet[10] == "Uzman Öğretmen"
    assert ahmet[11] == "1/4"
    assert ahmet[12] == "Yüksek Lisans"
    assert ahmet[13] == "E"
    assert ahmet[14] == "A Rh(+)"
    assert ahmet[15] == "15/05/1985"
    assert ahmet[16] == "01/09/2010"
    assert ahmet[17] == "SICIL-001"
    assert ahmet[18] == "EMEKLI-999"
    assert ahmet[19] == "ARSIV-77"
    assert ahmet[20] == "05551112233"
    assert ahmet[21] == "ahmet@meb.k12.tr"
    assert ahmet[22] == "Sınav komisyonunda görevli"
    assert ahmet[23] == 1

    # Mehmet Demir (İUP Pasif personel) kontrolü
    mehmet = rows[2]
    assert mehmet[0] == "MEHMET DEMİR"
    assert mehmet[1] == "33333333330"
    assert mehmet[5] == "İUP"
    assert mehmet[10] == "-"
    assert mehmet[11] == "-"
    assert mehmet[20] == "05553334455"
    assert mehmet[23] == 0  # Pasif durumu (0) da kayıpsız geri yüklendi!


def test_ozet_excel_yukleme_uyumlulugu(isolated_database, tmp_path):
    """Özet 4 sütunlu Excel yüklendiğinde eski davranışın sorunsuz çalıştığı doğrulanır."""
    _ornek_personelleri_ekle(isolated_database)

    resp = client.get("/personel-excel-indir?format=ozet")
    assert resp.status_code == 200
    ozet_dosyasi = str(tmp_path / "ciktilar" / "Personel_Listesi.xlsx")

    # Sıfırla ve özet dosyayı yükle
    isolated_database.cursor.execute("DELETE FROM personel")
    isolated_database.conn.commit()

    sonuc = _personel_excel_yukle_dogrudan(ozet_dosyasi, ".xlsx")
    assert sonuc["basarili"] is True
    assert "gruplandırıldı" in sonuc["mesaj"]

    isolated_database.cursor.execute("SELECT ad_soyad, brans, gorev, grup FROM personel")
    rows = isolated_database.cursor.fetchall()
    assert len(rows) == 3
