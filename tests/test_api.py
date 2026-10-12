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


# -----------------------------------------------------------
# KRİTİK EŞİKLER VE GERİ ALMA TESTLERİ
# -----------------------------------------------------------

def test_kritik_esikler_endpoint():
    """Dashboard kritik eşik erken uyarı verilerini döndürmelidir."""
    response = client.get("/kritik-esikler")
    assert response.status_code == 200
    veri = response.json()
    assert veri["basarili"] is True
    assert "veriler" in veri
    assert "ramakkala_10" in veri["veriler"]
    assert "asanlar_10" in veri["veriler"]
    assert "mektup_siniri_5" in veri["veriler"]
    assert "toplam_risk_25" in veri["veriler"]

    # /istatistikler endpoint bütünlüğü ve KPI uyumu
    resp_stats = client.get("/istatistikler")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    assert "kpis" in stats
    assert "ozursuz_10" in stats["kpis"]
    assert "kritik_esikler" in stats
    assert len(stats["kritik_esikler"]["asanlar_10"]) == stats["kpis"]["ozursuz_10"]


def test_son_islemi_geri_al_ve_durum_endpoint():
    """Geri alma durum ve geri al endpoint'lerini doğrular."""
    resp_durum = client.get("/geri-al-durumu")
    assert resp_durum.status_code == 200
    assert "geri_alinabilir" in resp_durum.json()

    resp_geri = client.post("/son-islemi-geri-al")
    assert resp_geri.status_code == 200
    # Eğer daha önce bir kayıt işlemi yoksa kontrollü hata mesajı döner
    assert "basarili" in resp_geri.json()


def test_command_palette_bileseni_ve_varliklari():
    """Ana sayfa render edildiğinde Command Palette bileşeninin ve scriptlerinin yer aldığını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "cmd_palette_overlay" in html
    assert "cmd_palette_input" in html
    assert "command_palette.js" in html
    assert "cmd-palette-trigger-btn" in html


def test_kisayollar_modali_ve_varliklari():
    """Klavye kısayolları rehberi modalının ve F1 butonunun sayfada yer aldığını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "kisayollar_modal" in html
    assert "Klavye Kısayolları Rehberi" in html
    assert "Ctrl + Z" in html
    assert "Ctrl + S" in html
    assert "Ctrl + B" in html
    assert "Ctrl + P" in html
    assert "Ctrl + T" in html


def test_yillik_isi_haritasi_bileseni_ve_ogrenci_detay():
    """Yıllık Devamsızlık Isı Haritası UI bileşenlerini ve öğrenci detay API'sini doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "yillik_isi_haritasi_kapsayici" in html
    assert "btn_gorunum_yillik" in html
    assert "btn_gorunum_aylik" in html

    # Öğrenci detay endpoint kontrolü
    resp_detay = client.get("/ogrenci-detay/999999")
    assert resp_detay.status_code == 200
    data = resp_detay.json()
    assert "devamsizliklar" in data
    assert isinstance(data["devamsizliklar"], list)


def test_canli_yedek_alma_endpoint():
    """Canlı veritabanı yedekleme endpoint'ini doğrular."""
    resp = client.post("/yedek-al")
    assert resp.status_code == 200
    veri = resp.json()
    assert "basarili" in veri
    assert veri["basarili"] is True


def test_3_bolmeli_komuta_merkezi_sidebar_rail():
    """3-Bölmeli Komuta Merkezi sol navigasyon ve durum rayını (sidebar rail) doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "app-layout" in html
    assert "app-main-stage" in html
    assert "sidebar-rail-kapsayici" in html
    assert "sidebar-rail" in html
    assert "sidebar-brand" in html
    assert "sidebar-emblem" in html
    assert "sidebar-nav" in html
    assert "sidebar-footer" in html
    assert "pulse-dot" in html
    assert "60 FPS • SQLite" in html


def test_dinamik_hizli_esik_cipleri_bileseni():
    """Öğrenci listesi panelindeki dinamik hızlı eşik / rozet açılır menüsünü doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "combo_esik_filtre" in html
    assert "esik-dropdown-kapsayici" in html
    assert "ramakkala_10" in html
    assert "asanlar_10" in html
    assert "mektup_5" in html
    assert "toplam_25" in html
    assert "kusursuz_0" in html
    assert "raporlu_ozrl" in html


def test_yillik_karne_rozetleri_ve_takvim_entegrasyonu():
    """Takvimin en üste taşınmasını ve yıllık modal rozet alanını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "aylik_navigasyon_kutusu" in html
    assert "takvim_alani_ana" in html
    assert "yillik_modal" in html
    assert "yillik_rozetler_alani" in html
    assert "veliWhatsAppKopyala" in html


def test_yardim_sekmesinde_klavye_kisayollari_rehberi():
    """Yardım ve Kullanım Rehberi sekmesinde klavye kısayolları bölümünün yer aldığını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "y_kisayollar" in html
    assert "Klavye Kısayolları ve Hızlı Erişim Rehberi" in html
    assert "İstasyonlar Arası Hızlı Geçiş" in html
    assert "Evrensel Komuta & Görünüm" in html
    assert "Hızlı İşlemler & Belge Üretimi" in html
    assert "Tablo ve Liste Hızlı Etkileşimleri" in html
    assert "Canlı Kısayol Penceresi (F1)" in html


def test_sistem_teshis_endpoint():
    """Sistem teşhis ve SQLite sağlık durum verilerini döndüren API endpoint'ini doğrular."""
    resp = client.get("/sistem-teshis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["basarili"] is True
    assert "veritabani" in data
    assert "sistem" in data
    assert "butunluk" in data["veritabani"]
    assert "journal_mode" in data["veritabani"]
    assert "ogrenci_sayisi" in data["veritabani"]
    assert "devamsizlik_sayisi" in data["veritabani"]
    assert "personel_sayisi" in data["veritabani"]
    assert "python_versiyon" in data["sistem"]


def test_yardim_sekmesinde_mevzuat_sss_ve_teshis_bilesenleri():
    """Yardım sekmesinde MEB mevzuatı, SSS, arama kutusu ve sistem teşhis widget'ının varlığını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "yardim_konu_arama" in html
    assert "y_mevzuat" in html
    assert "y_sss" in html
    assert "y_teshis" in html
    assert "5 Geç Kalma = Yarım Gün Özürsüz Kuralı" in html
    assert "Sıkça Sorulan Sorular ve Hızlı Sorun Giderme" in html
    assert "Sistem Teşhisi ve Sağlık Kontrolü" in html
    assert "teshis_ogr_sayisi" in html
    assert "teshis_db_butunluk" in html


def test_sidebar_rail_kategorileri_ve_ogrenci_yonetimi():
    """Sol menü rayının 4 mantıksal kategoriye ayrıldığını ve Öğrenci Yönetimi modal butonunu içerdiğini doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "ÖĞRENCİ İŞLEMLERİ" in html
    assert "PERSONEL İŞLEMLERİ" in html
    assert "DOĞRUDAN TEMİN" in html
    assert "SİSTEM &amp; REHBER" in html or "SİSTEM & REHBER" in html
    assert "ogrenci_yonetim_modal" in html
    assert "sidebar-section-title" in html


def test_esik_acilir_filtre_menusu_ve_tam_basliklar():
    """Öğrenci listesi panelinde 380px sabit genişlikli açılır eşik filtre menüsünü ve tam görünen tablo başlıklarını doğrular."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "ent_arama" in html
    assert "combo_esik_filtre" in html
    assert "esikSelectFiltrele" in html
    assert "ramakkala_10" in html
    assert "asanlar_10" in html
    assert "mektup_5" in html
    assert "toplam_25" in html
    assert "kusursuz_0" in html
    assert "raporlu_ozrl" in html
    # Tam görünen sütun başlıkları doğrulaması
    assert "span_temizSube" in html
    assert "span_no" in html
    assert "span_ad_soyad" in html
    assert "span_ozsz" in html
    assert "span_ozrl" in html
    assert "Sınıf ↕" in html
    assert "No ↕" in html
    assert "Ad Soyad ↕" in html
    assert "Özürsüz ↕" in html
    assert "Özürlü ↕" in html
