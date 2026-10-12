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

