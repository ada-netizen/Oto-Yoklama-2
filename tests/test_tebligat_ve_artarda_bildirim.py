import pytest
from fastapi.testclient import TestClient
from api import app
from mevzuat_kurallari import ogrenci_tebligat_ve_artarda_analiz

client = TestClient(app)

def test_ogrenci_tebligat_esikleri_analizi():
    """5., 15. ve 25. gün resmi tebligat eşiklerini doğrular."""
    # 1. 5. Gün Eşiği (Özürsüz 5 gün veya toplam 5 gün bandı)
    dev_bos = []
    res_5g = ogrenci_tebligat_ve_artarda_analiz(dev_bos, ozursuz=5.0, ozurlu=0.0)
    assert res_5g["tebligat_asamasi"] == "5_gun"
    assert "1. Resmi Tebligat" in res_5g["tebligat_etiketi"]
    assert "Önleme Komisyonu" in res_5g["tebligat_aciklama"] or "komisyon" in res_5g["tebligat_aciklama"].lower()

    # 4.5 gün özürsüz de 5. gün tebligat eşiği bandına girmelidir
    res_4_5g = ogrenci_tebligat_ve_artarda_analiz(dev_bos, ozursuz=4.5, ozurlu=0.0)
    assert res_4_5g["tebligat_asamasi"] == "5_gun"

    # 2. 15. Gün Eşiği (Toplam 15 gün bandı: 14.5 - 16.0 gün)
    res_15g = ogrenci_tebligat_ve_artarda_analiz(dev_bos, ozursuz=7.0, ozurlu=8.0)
    assert res_15g["tebligat_asamasi"] == "15_gun"
    assert "2. Resmi Tebligat" in res_15g["tebligat_etiketi"]

    # 3. 25. Gün Eşiği (Toplam 25+ gün: 24.5 - 29.5 gün bandı)
    res_25g = ogrenci_tebligat_ve_artarda_analiz(dev_bos, ozursuz=9.5, ozurlu=16.0)
    assert res_25g["tebligat_asamasi"] == "25_gun"
    assert "Nihai" in res_25g["tebligat_etiketi"] or "3. Tebligat" in res_25g["tebligat_etiketi"]

    # 4. Güvenli bölge (örnek 2 gün devamsızlık)
    res_guvenli = ogrenci_tebligat_ve_artarda_analiz(dev_bos, ozursuz=2.0, ozurlu=1.0)
    assert res_guvenli["tebligat_asamasi"] is None


def test_art_arda_2gun_ozursuz_tespiti():
    """Hafta içi ve hafta sonu atlamalı art arda 2 gün özürsüz devamsızlık analizini doğrular."""
    # Durum 1: Hafta içi ardışık 2 gün (Salı - Çarşamba)
    dev_hafta_ici = [
        {"tarih": "10/03/2026", "tur": "D", "gun": "1"}, # Salı
        {"tarih": "11/03/2026", "tur": "D", "gun": "1"}, # Çarşamba
    ]
    res_ardisik = ogrenci_tebligat_ve_artarda_analiz(dev_hafta_ici, ozursuz=2.0, ozurlu=0.0)
    assert res_ardisik["art_arda_2gun"] is True
    assert "10/03/2026" in res_ardisik["art_arda_tarihler"]
    assert "11/03/2026" in res_ardisik["art_arda_tarihler"]

    # Durum 2: Hafta sonu atlaması (Cuma - Pazartesi)
    dev_hafta_sonu = [
        {"tarih": "13/03/2026", "tur": "D", "gun": "1"}, # Cuma
        {"tarih": "16/03/2026", "tur": "D", "gun": "1"}, # Pazartesi
    ]
    res_hs = ogrenci_tebligat_ve_artarda_analiz(dev_hafta_sonu, ozursuz=2.0, ozurlu=0.0)
    assert res_hs["art_arda_2gun"] is True
    assert "13/03/2026" in res_hs["art_arda_tarihler"]
    assert "16/03/2026" in res_hs["art_arda_tarihler"]

    # Durum 3: Aralıklı günler (Pazartesi ve Çarşamba - ardışık değil)
    dev_aralikli = [
        {"tarih": "09/03/2026", "tur": "D", "gun": "1"}, # Pazartesi
        {"tarih": "11/03/2026", "tur": "D", "gun": "1"}, # Çarşamba
    ]
    res_aralikli = ogrenci_tebligat_ve_artarda_analiz(dev_aralikli, ozursuz=2.0, ozurlu=0.0)
    assert res_aralikli["art_arda_2gun"] is False

    # Durum 4: Biri özürlü (İzinli) biri özürsüz (D) - Özürsüz art arda sayılmaz
    dev_biri_ozurlu = [
        {"tarih": "10/03/2026", "tur": "İ", "gun": "1"}, # İzinli
        {"tarih": "11/03/2026", "tur": "D", "gun": "1"}, # Özürsüz
    ]
    res_ozurlu = ogrenci_tebligat_ve_artarda_analiz(dev_biri_ozurlu, ozursuz=1.0, ozurlu=1.0)
    assert res_ozurlu["art_arda_2gun"] is False


def test_tebligat_bildirimleri_endpoint():
    """GET /tebligat-bildirimleri endpoint formatını ve sayılarını test eder."""
    res = client.get("/tebligat-bildirimleri")
    assert res.status_code == 200
    veri = res.json()
    assert veri["basarili"] is True
    assert "toplam_bildirim" in veri
    assert "sayilar" in veri
    assert "gruplar" in veri
    assert "artarda_2gun" in veri["sayilar"]
    assert "tebligat_5" in veri["sayilar"]
    assert "tebligat_15" in veri["sayilar"]
    assert "tebligat_25" in veri["sayilar"]
    assert isinstance(veri["gruplar"]["artarda_2gun"], list)
    assert isinstance(veri["gruplar"]["tebligat_5"], list)
    assert isinstance(veri["gruplar"]["tebligat_15"], list)
    assert isinstance(veri["gruplar"]["tebligat_25"], list)


def test_dashboard_kpis_ve_kritik_esikler_uyumu():
    """Dashboard KPI'larında tebligat ve art arda sayaçlarının yer aldığını doğrular."""
    res = client.get("/istatistikler")
    assert res.status_code == 200
    veri = res.json()
    assert "kpis" in veri
    kpis = veri["kpis"]
    assert "artarda_2gun_sayi" in kpis
    assert "tebligat_5_sayi" in kpis
    assert "tebligat_15_sayi" in kpis
    assert "tebligat_25_sayi" in kpis

    # Kritik eşikler sözlüğünde yeni gruplar bulunmalı
    esikler = veri.get("kritik_esikler", {})
    assert "artarda_2gun" in esikler
    assert "tebligat_5" in esikler
    assert "tebligat_15" in esikler
    assert "tebligat_25" in esikler
    assert len(esikler["artarda_2gun"]) == kpis["artarda_2gun_sayi"]


def test_frontend_bilesenleri_varlik():
    """Tebligat bildirim modal dosyasının ve index.html entegrasyonunun varlığını doğrular."""
    import os
    modal_yolu = os.path.join("frontend", "components", "tebligat_bildirim_modal.html")
    assert os.path.exists(modal_yolu)
    with open(modal_yolu, "r", encoding="utf-8") as f:
        icerik = f.read()
    assert "tebligat_bildirim_modal" in icerik
    assert "artarda_2gun" in icerik
    assert "tebligat_5" in icerik
    assert "tebligat_15" in icerik
    assert "tebligat_25" in icerik
    assert "tebligatBildirimComponent" in icerik

    # index.html içinde modal include ve eşik kontrolü
    with open(os.path.join("frontend", "index.html"), "r", encoding="utf-8") as f:
        index_icerik = f.read()
    assert "tebligat_bildirim_modal.html" in index_icerik
    assert "artarda_2gun" in index_icerik
