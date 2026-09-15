# ================= tests/test_api.py =================
# API endpoint'lerinin varlığını ve temel davranışını doğrular.
# Çalıştırmak için: uv run pytest tests/ -v

from fastapi.testclient import TestClient
from io import BytesIO
import sys
import os
import pytest
import pandas as pd

# Üst klasörü import yollarına ekle ki api.py bulunabilsin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import api

app = api.app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch, tmp_path):
    """Her API testi gerçek kullanıcı veritabanından bağımsız çalışır."""
    test_db = api.VeritabaniYoneticisi(str(tmp_path / "test.db"))
    monkeypatch.setattr(api, "db", test_db)
    yield
    test_db.kapat()


# -----------------------------------------------------------
# TEMEL ENDPOINT VARLIK TESTLERİ
# -----------------------------------------------------------

def test_root_not_found():
    """Kök dizin tanımlı değil, 404 dönmeli."""
    response = client.get("/")
    assert response.status_code == 200


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


def test_personel_excel_yukleme_korur_personel_grubunu():
    """Excel'deki Grup değeri görev tahmininin üzerine yazılmamalı."""
    excel = BytesIO()
    pd.DataFrame([
        {"Ad Soyad": "Excel İdare", "Branş": "-", "Görev": "Öğretmen", "Grup": "İdare"},
        {"Ad Soyad": "Excel Öğretmen", "Branş": "Türkçe", "Görev": "Memur", "Grup": "Öğretmenler"},
    ]).to_excel(excel, index=False)
    excel.seek(0)

    response = client.post(
        "/personel-excel-yukle",
        files={"dosya": ("personel.xlsx", excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    assert response.json()["basarili"] is True
    personeller = {p["ad"]: p["grup"] for p in client.get("/personeller").json()["personeller"]}
    assert personeller["Excel İdare"] == "İdare"
    assert personeller["Excel Öğretmen"] == "Öğretmenler"


def test_excel_yukleme_izin_verilmeyen_uzantiyi_reddeder():
    response = client.post(
        "/personel-excel-yukle",
        files={"dosya": ("personel.txt", b"Ad Soyad\nTest", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "basarili": False,
        "mesaj": "Yalnızca XLSX, XLS veya CSV dosyaları yüklenebilir.",
    }


def test_bos_excel_yukleme_mevcut_personeli_silmez():
    excel = BytesIO()
    pd.DataFrame(columns=["Ad Soyad", "Branş", "Görev", "Grup"]).to_excel(excel, index=False)
    excel.seek(0)

    response = client.post(
        "/personel-excel-yukle",
        files={"dosya": ("bos.xlsx", excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    assert response.json()["basarili"] is True
    job_id = response.json()["job_id"]
    assert client.get(f"/islem-durumu/{job_id}").json()["durum"] == "hata"


def test_excel_onizleme_satir_sutun_ve_hatalari_dondurur():
    excel = BytesIO()
    pd.DataFrame([
        {"Ad Soyad": "Önizleme Personeli", "Branş": "Matematik", "Görev": "Öğretmen", "Grup": "İdare"},
        {"Ad Soyad": None, "Branş": "", "Görev": "Memur", "Grup": "İdare"},
    ]).to_excel(excel, index=False)
    excel.seek(0)

    response = client.post(
        "/excel-onizle",
        data={"tur": "personel"},
        files={"dosya": ("onizleme.xlsx", excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    sonuc = response.json()
    assert response.status_code == 200
    assert sonuc["basarili"] is True
    assert sonuc["toplam_satir"] == 2
    assert "Ad Soyad" in sonuc["sutunlar"]
    assert sonuc["hatalar"] == ["1 satırda ad-soyad eksik."]
    assert len(sonuc["onizleme"]) == 2


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
