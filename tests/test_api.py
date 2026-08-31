# ================= tests/test_api.py =================
# API endpoint'lerinin varlığını ve temel davranışını doğrular.
# Çalıştırmak için: uv run pytest tests/ -v

from fastapi.testclient import TestClient
import sys
import os

# Üst klasörü import yollarına ekle ki api.py bulunabilsin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app

client = TestClient(app)


# -----------------------------------------------------------
# TEMEL ENDPOINT VARLIK TESTLERİ
# -----------------------------------------------------------

def test_root_not_found():
    """Kök dizin tanımlı değil, 404 dönmeli."""
    response = client.get("/")
    assert response.status_code == 404


def test_get_ogrenciler_endpoint_exists():
    """Öğrenci listesi endpoint'i erişilebilir olmalı (404 olmayacak)."""
    response = client.get("/ogrenciler")
    assert response.status_code != 404


def test_get_personeller_endpoint_exists():
    """Personel listesi endpoint'i erişilebilir olmalı."""
    response = client.get("/personeller")
    assert response.status_code != 404


def test_get_ayarlar_endpoint_exists():
    """Ayarlar endpoint'i erişilebilir olmalı."""
    response = client.get("/ayarlar-getir")
    assert response.status_code != 404


def test_get_yedekler_listele_endpoint_exists():
    """Yedek listesi endpoint'i erişilebilir olmalı."""
    response = client.get("/yedekler-listele")
    assert response.status_code != 404


# -----------------------------------------------------------
# DEVAMSIZLIK İŞLEMLERİ TESTLERİ
# -----------------------------------------------------------

def test_devamsizlik_manuel_ekle_yanlis_veri():
    """Eksik veri ile devamsızlık ekleme isteği 422 (Unprocessable Entity) dönmeli."""
    response = client.post("/devamsizlik-manuel-ekle", json={})
    assert response.status_code == 422


def test_devamsizlik_manuel_ekle_veri_yapisi():
    """Doğru veri yapısıyla istek gönderildiğinde 422 dönmemeli."""
    veri = {"no": "999", "tarih": "01.09.2026", "tur": "Özürsüz", "gun": "1"}
    response = client.post("/devamsizlik-manuel-ekle", json=veri)
    # 422 olmamalı (veri yapısı doğru kabul edilmeli)
    assert response.status_code != 422


# -----------------------------------------------------------
# PERSONEL İŞLEMLERİ TESTLERİ
# -----------------------------------------------------------

def test_personel_ekle_yanlis_veri():
    """Eksik veri ile personel ekleme isteği 422 dönmeli."""
    response = client.post("/personel-ekle", json={})
    assert response.status_code == 422


def test_personel_ekle_veri_yapisi():
    """Doğru veri yapısıyla personel ekleme isteği 422 dönmemeli."""
    veri = {"ad": "Test Kullanıcı", "gorev": "Öğretmen", "brans": "Matematik"}
    response = client.post("/personel-ekle", json=veri)
    assert response.status_code != 422


# -----------------------------------------------------------
# AYARLAR TESTLERİ
# -----------------------------------------------------------

def test_ayarlar_kaydet_yanlis_veri():
    """Yanlış yapıda ayar kaydetme isteği başarısız olmalı."""
    response = client.post("/ayarlar-kaydet", json=None)
    assert response.status_code in [400, 422, 500]


# -----------------------------------------------------------
# RAPOR TESTLERİ
# -----------------------------------------------------------

def test_rapor_al_yanlis_veri():
    """Eksik veri ile rapor isteği 422 dönmeli."""
    response = client.post("/rapor-al", json={})
    assert response.status_code == 422


def test_rapor_al_veri_yapisi():
    """Doğru veri yapısıyla rapor isteği 422 dönmemeli."""
    veri = {"tur": "esik", "format": "pdf", "ozel_deger": None}
    response = client.post("/rapor-al", json=veri)
    assert response.status_code != 422
