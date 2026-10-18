import sys
import os
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from veritabani import VeritabaniYoneticisi

@pytest.fixture
def test_db():
    # Bellek-içi (in-memory) veritabanı simülasyonu
    # İşlemler bitince otomatik silinir, diski kirletmez
    db = VeritabaniYoneticisi(":memory:")
    yield db
    db.kapat()

def test_veritabani_tablo_olusumu(test_db):
    """Tabloların init anında başarıyla kurulup kurulmadığını test eder."""
    cursor = test_db.cursor
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    
    assert "ogrenciler" in tables
    assert "devamsizliklar" in tables
    assert "personel" in tables
    assert "saglik_raporlari" in tables
    assert "personel_rapor_kesinti" in tables
    assert "uretilen_evraklar" in tables
    assert "devamsizlik_mektup_takip" in tables

def test_kaydet_ve_yukle(test_db):
    """Transaction tabanlı kaydetme ve okuma işlemini doğrular."""
    
    ornek_ogrenciler = [
        {"no": "100", "ad_soyad": "Test Öğrenci 1", "sube": "9/A"},
        {"no": "101", "ad_soyad": "Test Öğrenci 2", "sube": "9/B"}
    ]
    
    ornek_devamsizliklar = [
        {"id": "uuid-1", "no": "100", "tarih": "01/01/2026", "tur": "D", "gun": "1", "secili": True},
        {"id": "uuid-2", "no": "101", "tarih": "02/01/2026", "tur": "G", "gun": "0.5", "secili": False}
    ]
    
    # Kaydetme işlemi
    basari, hata = test_db.kaydet(ornek_ogrenciler, ornek_devamsizliklar)
    assert basari is True
    assert hata == ""
    
    # Yükleme (Okuma) İşlemi
    ogrenciler, devamsizliklar = test_db.yukle()
    
    assert len(ogrenciler) == 2
    assert ogrenciler[0]["no"] == "100"
    assert ogrenciler[1]["sube"] == "9/B"
    
    assert len(devamsizliklar) == 2
    assert devamsizliklar[0]["no"] == "100"
    assert devamsizliklar[0]["secili"] is False # secili bellekte False olarak döner yukle fonksiyonunda
    assert devamsizliklar[1]["tur"] == "G"

def test_sifirla(test_db):
    """Tüm kayıtların başarıyla silindiğini test eder."""
    ornek_ogr = [{"no": "999", "ad_soyad": "X", "sube": "Y"}]
    test_db.kaydet(ornek_ogr, [])
    
    # Önce eklendiğini teyit et
    ogr, _ = test_db.yukle()
    assert len(ogr) == 1
    
    # Sıfırla
    test_db.sifirla()
    
    # Silindiğini teyit et
    ogr_son, dev_son = test_db.yukle()
    assert len(ogr_son) == 0
    assert len(dev_son) == 0

def test_son_islemi_geri_al(test_db):
    """Son kaydetme işleminin başarıyla geri alındığını doğrular."""
    ilk_ogrenciler = [{"no": "101", "ad_soyad": "Öğrenci 1", "sube": "9/A"}]
    test_db.kaydet(ilk_ogrenciler, [])
    
    # İkinci bir kaydetme işlemi yapalım
    ikinci_ogrenciler = [
        {"no": "101", "ad_soyad": "Öğrenci 1", "sube": "9/A"},
        {"no": "102", "ad_soyad": "Öğrenci 2", "sube": "9/B"}
    ]
    test_db.kaydet(ikinci_ogrenciler, [])
    
    ogr, _ = test_db.yukle()
    assert len(ogr) == 2
    
    # Geri alma işlemini çalıştır
    basarili, mesaj = test_db.son_islemi_geri_al()
    assert basarili is True
    
    # Veritabanının ilk haline döndüğünü doğrula
    ogr_onceki, _ = test_db.yukle()
    assert len(ogr_onceki) == 1
    assert ogr_onceki[0]["no"] == "101"

def test_canli_yedekleme_ve_surum(tmp_path):
    """Canlı SQLite yedekleme API'si ve şema user_version sürümünü test eder."""
    db_yol = str(tmp_path / "okul_test.db")
    db = VeritabaniYoneticisi(db_yol)
    
    # User version doğrula
    db.cursor.execute("PRAGMA user_version;")
    ver = db.cursor.fetchone()[0]
    assert ver >= 1
    
    # Veri ekle
    db.kaydet([{"no": "500", "ad_soyad": "Yedek Test", "sube": "10/A"}], [])
    
    # Yedekle
    yedek_dosyasi = str(tmp_path / "yedek.db")
    basarili, yol = db.yedekle(hedef_yol=yedek_dosyasi)
    assert basarili is True
    assert os.path.exists(yedek_dosyasi)
    
    # Yedekten oku
    db_yedek = VeritabaniYoneticisi(yedek_dosyasi)
    ogr_yedek, _ = db_yedek.yukle()
    assert len(ogr_yedek) == 1
    assert ogr_yedek[0]["no"] == "500"
    
    db_yedek.kapat()
    db.kapat()


def test_tum_tablolarin_ve_ayarlarin_online_yedeklenmesi(tmp_path):
    """SistemMotoru.yedek_al'ın SQLite Online Backup ile tüm 7 tabloyu ve ayar dosyasını eksiksiz yedeklediğini test eder."""
    import json
    from sistem_motoru import SistemMotoru

    db_dir = tmp_path / "data"
    db_dir.mkdir()
    db_yol = str(db_dir / "okul_veritabani.db")
    yedek_dir = str(tmp_path / "Yedekler")

    db = VeritabaniYoneticisi(db_yol)

    # 1. ogrenciler & devamsizliklar ekle
    db.kaydet(
        [{"no": "1001", "ad_soyad": "Zeynep Kaya", "sube": "11/C"}],
        [{"id": "dev-1", "no": "1001", "tarih": "10/03/2026", "tur": "D", "gun": "1.0", "secili": False}]
    )

    # 2. personel ekle
    db.cursor.execute(
        "INSERT INTO personel (ad_soyad, tc_no, unvan, brans, gorev, grup, aktif) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Ahmet Demir", "12345678901", "Öğretmen", "Matematik", "MÜDÜR", "Kadrolu", 1)
    )

    # 3. saglik_raporlari & kesinti ekle
    db.cursor.execute(
        "INSERT INTO saglik_raporlari (personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama) VALUES (?, ?, ?, ?, ?)",
        ("Ahmet Demir", "01.03.2026", "05.03.2026", 5, "Grip İstirahat")
    )
    db.cursor.execute(
        "INSERT INTO personel_rapor_kesinti (personel_ad, onceden_kesilen_gun) VALUES (?, ?)",
        ("Ahmet Demir", 2)
    )

    # 4. uretilen_evraklar ekle
    db.cursor.execute(
        "INSERT INTO uretilen_evraklar (tur, personel_ad, brans, tarih) VALUES (?, ?, ?, ?)",
        ("Veli İzin Dilekçesi", "Ahmet Demir", "Matematik", "10.03.2026 14:00")
    )

    # 5. devamsizlik_mektup_takip ekle
    db.mektup_durumu_kaydet("1001", "5_gun", True, "10.03.2026 15:30")
    db.conn.commit()

    # 6. yoklama_ayarlar.json oluştur
    ayarlar_dosya = str(db_dir / "yoklama_ayarlar.json")
    ayarlar_veri = {"okul_adi": "Test Anadolu Lisesi", "mudur_adi": "Ahmet Demir"}
    with open(ayarlar_dosya, "w", encoding="utf-8") as f:
        json.dump(ayarlar_veri, f)

    # 7. SistemMotoru.yedek_al çalıştır
    basarili, hata = SistemMotoru.yedek_al(db_yol, {"yedek_kayit_klasoru": yedek_dir}, yedek_dir)
    assert basarili is True, f"Yedekleme başarısız: {hata}"

    # 8. Yedek dosyasını bul ve doğrula
    yedek_dosyalari = [f for f in os.listdir(yedek_dir) if f.startswith("veritabani_yedek_") and f.endswith(".db")]
    assert len(yedek_dosyalari) == 1
    yedek_db_yol = os.path.join(yedek_dir, yedek_dosyalari[0])

    # 9. Yedeklenen veritabanını aç ve tüm 7 tablodaki verileri doğrula
    yedek_db = VeritabaniYoneticisi(yedek_db_yol)
    
    # ogrenciler & devamsizliklar
    ogr_y, dev_y = yedek_db.yukle()
    assert len(ogr_y) == 1
    assert ogr_y[0]["no"] == "1001"
    assert len(dev_y) == 1
    assert dev_y[0]["gun"] == "1.0"

    # personel
    yedek_db.cursor.execute("SELECT ad_soyad, gorev, grup FROM personel WHERE tc_no = '12345678901'")
    pers_row = yedek_db.cursor.fetchone()
    assert pers_row is not None
    assert pers_row[0] == "Ahmet Demir"
    assert pers_row[1] == "MÜDÜR"
    assert pers_row[2] == "Kadrolu"

    # saglik_raporlari & kesinti
    yedek_db.cursor.execute("SELECT gun_sayisi FROM saglik_raporlari WHERE personel_ad = 'Ahmet Demir'")
    assert yedek_db.cursor.fetchone()[0] == 5

    yedek_db.cursor.execute("SELECT onceden_kesilen_gun FROM personel_rapor_kesinti WHERE personel_ad = 'Ahmet Demir'")
    assert yedek_db.cursor.fetchone()[0] == 2

    # uretilen_evraklar
    yedek_db.cursor.execute("SELECT tur FROM uretilen_evraklar WHERE personel_ad = 'Ahmet Demir'")
    assert yedek_db.cursor.fetchone()[0] == "Veli İzin Dilekçesi"

    # devamsizlik_mektup_takip
    mektup_durum = yedek_db.mektup_durumlari_getir("5_gun")
    assert ("1001", "5_gun") in mektup_durum
    assert mektup_durum[("1001", "5_gun")]["gonderildi"] is True
    assert mektup_durum[("1001", "5_gun")]["tarih"] == "10.03.2026 15:30"

    # 10. Ayar yedeğini doğrula
    ayar_yedek_dosyalari = [f for f in os.listdir(yedek_dir) if f.startswith("ayarlar_yedek_") and f.endswith(".json")]
    assert len(ayar_yedek_dosyalari) == 1
    with open(os.path.join(yedek_dir, ayar_yedek_dosyalari[0]), "r", encoding="utf-8") as f:
        yuklenen_ayar = json.load(f)
    assert yuklenen_ayar["okul_adi"] == "Test Anadolu Lisesi"

    yedek_db.kapat()
    db.kapat()


