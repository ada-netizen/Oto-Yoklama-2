# ================= tests/test_mektup_takip.py =================
# MEB Resmi Tebligat / Mektup Takip Çizelgesi (5, 15, 25 Gün) Testleri

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import api
import veritabani

app = api.app
client = TestClient(app)


def test_veritabani_mektup_durumu_kaydet_ve_getir(tmp_path):
    """Veritabanı mektup durumu CRUD ve toplu kayıt işlemlerini test eder."""
    db_path = str(tmp_path / "test_mektup.db")
    db = veritabani.VeritabaniYoneticisi(db_path)

    # Başlangıçta boş olmalı
    durumlar = db.mektup_durumlari_getir()
    assert len(durumlar) == 0

    # Tekil kayıt ekleme
    db.mektup_durumu_kaydet("101", "5_gun", True, "2026-10-18T10:00:00")
    durumlar = db.mektup_durumlari_getir()
    assert ("101", "5_gun") in durumlar
    assert durumlar[("101", "5_gun")]["gonderildi"] is True
    assert durumlar[("101", "5_gun")]["tarih"] == "2026-10-18T10:00:00"

    # Durumu güncelleme (Geri alma / işareti kaldırma)
    db.mektup_durumu_kaydet("101", "5_gun", False)
    durumlar = db.mektup_durumlari_getir("5_gun")
    assert durumlar[("101", "5_gun")]["gonderildi"] is False

    # Toplu kayıt ekleme
    db.mektup_durumu_toplu_kaydet(["102", "103", "104"], "15_gun", True, "2026-10-18T12:00:00")
    durumlar_15 = db.mektup_durumlari_getir("15_gun")
    assert len(durumlar_15) == 3
    for no in ["102", "103", "104"]:
        assert durumlar_15[(no, "15_gun")]["gonderildi"] is True

    # Sıfırlama kontrolü
    db.sifirla()
    durumlar_son = db.mektup_durumlari_getir()
    assert len(durumlar_son) == 0

    db.kapat()


def test_api_mektup_takip_ve_esikler(monkeypatch, tmp_path):
    """API üzerinden eşik hesaplamalarını ve mektup durumu kaydetme endpointlerini test eder."""
    test_db = veritabani.VeritabaniYoneticisi(str(tmp_path / "test_api_mektup.db"))
    
    modules_to_patch = [
        "dependencies", "api", "utils",
        "routes.personel", "routes.ogrenci", "routes.dashboard",
        "routes.ihale", "routes.pdf", "routes.rapor",
        "routes.saglik", "routes.sistem"
    ]
    for mod_name in modules_to_patch:
        if mod_name in sys.modules:
            monkeypatch.setattr(sys.modules[mod_name], "db", test_db)

    ogrenciler = [
        {"no": "101", "ad_soyad": "Ahmet Yılmaz", "sube": "11. Sınıf / A Şubesi (ALANI YOK)"},
        {"no": "102", "ad_soyad": "Mehmet Demir", "sube": "10. Sınıf / B Şubesi"},
        {"no": "103", "ad_soyad": "Ayşe Kaya", "sube": "12. Sınıf / C Şubesi"},
        {"no": "104", "ad_soyad": "Fatma Çelik", "sube": "9. Sınıf / D Şubesi"}
    ]
    devamsizliklar = [
        # 101: 6 gün özürsüz ("D"), 2 gün özürlü ("İ") -> toplam 8 (Sadece 5 gün eşiğine girer)
        {"id": 1, "no": "101", "tarih": "", "tur": "D", "gun": 6.0},
        {"id": 2, "no": "101", "tarih": "", "tur": "İ", "gun": 2.0},
        # 102: 4 gün özürsüz ("D"), 12 gün özürlü ("İ") -> toplam 16 (Sadece 15 gün toplam eşiğine girer)
        {"id": 3, "no": "102", "tarih": "", "tur": "D", "gun": 4.0},
        {"id": 4, "no": "102", "tarih": "", "tur": "İ", "gun": 12.0},
        # 103: 8 gün özürsüz ("D"), 18 gün özürlü ("İ") -> toplam 26 (5G özürsüz, 15G toplam ve 25G toplamın TÜMÜNE girer)
        {"id": 5, "no": "103", "tarih": "", "tur": "D", "gun": 8.0},
        {"id": 6, "no": "103", "tarih": "", "tur": "İ", "gun": 18.0},
        # 104: 2 gün özürsüz ("D"), 1 gün özürlü ("İ") -> toplam 3 (Hiçbir eşiğe girmez)
        {"id": 7, "no": "104", "tarih": "", "tur": "D", "gun": 2.0},
        {"id": 8, "no": "104", "tarih": "", "tur": "İ", "gun": 1.0},
    ]
    test_db.kaydet(ogrenciler, devamsizliklar)

    # GET /mektup-takip-ozet çağrısı
    res = client.get("/mektup-takip-ozet")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["basarili"] is True
    data = res_json["veriler"]

    assert "5_gun" in data
    assert "15_gun" in data
    assert "25_gun" in data

    # 5 Gün Eşiği: 101 (6G) ve 103 (8G) -> 2 öğrenci
    assert data["5_gun"]["toplam_ogrenci"] == 2
    assert data["5_gun"]["kalan_sayi"] == 2
    assert data["5_gun"]["gonderilen_sayi"] == 0
    assert data["5_gun"]["hepsi_gonderildi"] is False
    assert data["5_gun"]["ogrenciler"][0]["no"] == "103"  # Sıralı: 8.0 > 6.0
    assert data["5_gun"]["ogrenciler"][1]["no"] == "101"
    # Kısa şube formatı kontrolü (11. Sınıf / A Şubesi (ALANI YOK) -> 11/A)
    assert data["5_gun"]["ogrenciler"][1]["sube"] == "11/A"

    # 15 Gün Eşiği: 102 (16G) ve 103 (26G) -> 2 öğrenci
    assert data["15_gun"]["toplam_ogrenci"] == 2
    assert data["15_gun"]["kalan_sayi"] == 2

    # 25 Gün Eşiği: 103 (26G) -> 1 öğrenci
    assert data["25_gun"]["toplam_ogrenci"] == 1
    assert data["25_gun"]["kalan_sayi"] == 1

    # POST /mektup-durumu-kaydet ile 101 nolu öğrenciyi 5_gun için gönderildi yap
    res_kayit = client.post("/mektup-durumu-kaydet", json={
        "ogrenci_no": "101",
        "esik_turu": "5_gun",
        "gonderildi": True
    })
    assert res_kayit.status_code == 200
    assert res_kayit.json()["basarili"] is True

    # Tekrar kontrol et: 5_gun için 1 gönderildi, 1 kalan olmalı
    res2 = client.get("/mektup-takip-ozet")
    data2 = res2.json()["veriler"]
    assert data2["5_gun"]["gonderilen_sayi"] == 1
    assert data2["5_gun"]["kalan_sayi"] == 1
    assert data2["5_gun"]["hepsi_gonderildi"] is False

    # POST /mektup-durumu-toplu-kaydet ile kalan öğrenciyi de işaretle
    res_toplu = client.post("/mektup-durumu-toplu-kaydet", json={
        "ogrenci_nolar": ["101", "103"],
        "esik_turu": "5_gun",
        "gonderildi": True
    })
    assert res_toplu.status_code == 200
    assert res_toplu.json()["basarili"] is True

    # Şimdi 5_gun için hepsi gönderilmiş olmalı
    res3 = client.get("/mektup-takip-ozet")
    data3 = res3.json()["veriler"]
    assert data3["5_gun"]["gonderilen_sayi"] == 2
    assert data3["5_gun"]["kalan_sayi"] == 0
    assert data3["5_gun"]["hepsi_gonderildi"] is True

    # GET /istatistikler entegrasyon kontrolü
    res_ist = client.get("/istatistikler")
    assert res_ist.status_code == 200
    ist_data = res_ist.json()
    assert "mektup_takip" in ist_data
    assert ist_data["mektup_takip"]["5_gun"]["hepsi_gonderildi"] is True
    assert ist_data["mektup_takip"]["15_gun"]["kalan_sayi"] == 2

    # Şampiyon şubeler tablosu & Okul emsal ortalaması kontrolü
    assert "sampiyon_subeler" in ist_data
    samp_info = ist_data["sampiyon_subeler"]
    assert "okul_ortalama" in samp_info
    assert "subeler" in samp_info
    assert len(samp_info["subeler"]) > 0
    assert "emsal_fark" in samp_info["subeler"][0]

    test_db.kapat()

