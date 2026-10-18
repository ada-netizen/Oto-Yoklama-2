import pytest
from fastapi.testclient import TestClient
from api import app
from mevzuat_kurallari import ogretmen_mi, mevzuat_bilgisi_al, devamsizlik_yaptirim_uyarisi

client = TestClient(app)

def test_ogretmen_tespiti_kurallari():
    # Öğretmen olanlar
    assert ogretmen_mi("Kadrolu", "Öğretmen", "Öğretmen") is True
    assert ogretmen_mi("Kadrolu", "Müdür Yardımcısı", "İdareci") is True
    assert ogretmen_mi("Sözleşmeli", "Sözleşmeli Öğretmen", "") is True
    assert ogretmen_mi("Ücretli", "", "") is True

    # Öğretmen olmayanlar (Memur, İşçi, TYP, İUP)
    assert ogretmen_mi("Sürekli İşçi", "Temizlik Personeli", "İşçi") is False
    assert ogretmen_mi("TYP", "Temizlik", "Katılımcı") is False
    assert ogretmen_mi("İUP", "Uyum Katılımcısı", "Destek") is False
    assert ogretmen_mi("Kadrolu", "VHKİ", "Veri Hazırlama") is False
    assert ogretmen_mi("Kadrolu", "Memur", "Yazı İşleri") is False
    assert ogretmen_mi("Hizmet Alımı", "Güvenlik Görevlisi", "Güvenlik") is False

def test_mevzuat_bilgisi_matrisi():
    # İUP bilgisi
    iup = mevzuat_bilgisi_al("İUP")
    assert iup["ogretmen_mi"] is False
    assert iup["brans_goster"] is False
    assert iup["kariyer_goster"] is False
    assert "140" in iup["calisma_duzeni"] or "140" in iup.get("aciklama", "") or "140" in iup.get("calisma_duzeni", "")

    # TYP bilgisi
    typ = mevzuat_bilgisi_al("TYP")
    assert typ["ogretmen_mi"] is False
    assert typ["brans_goster"] is False
    assert "5 gün" in typ["izin_hakki"].lower() or "5 güne" in typ["izin_hakki"].lower()

    # Sürekli İşçi (4857)
    isci = mevzuat_bilgisi_al("Sürekli İşçi")
    assert isci["ogretmen_mi"] is False
    assert "4857" in isci["kanun"]
    assert isci["brans_goster"] is False

    # Kadrolu Öğretmen (657)
    ogr = mevzuat_bilgisi_al("Kadrolu", "Öğretmen")
    assert ogr["ogretmen_mi"] is True
    assert ogr["brans_goster"] is True
    assert ogr["kariyer_goster"] is True

    # Kadrolu Memur (657)
    memur = mevzuat_bilgisi_al("Kadrolu", "Memur")
    assert memur["ogretmen_mi"] is False
    assert memur["brans_goster"] is False
    assert memur["kariyer_goster"] is False

def test_devamsizlik_yaptirim_uyarilari():
    # İUP: 1 gün mazeretsiz derhal fesih
    u_iup = devamsizlik_yaptirim_uyarisi("İUP", 1)
    assert u_iup is not None
    assert u_iup["seviye"] == "KRİTİK"
    assert "İLİŞİK KESİLİR" in u_iup["mesaj"]

    # TYP: 5 günü aşarsa ilişik kesilir
    u_typ_ok = devamsizlik_yaptirim_uyarisi("TYP", 2)
    assert u_typ_ok is None
    u_typ_kesim = devamsizlik_yaptirim_uyarisi("TYP", 6)
    assert u_typ_kesim is not None
    assert u_typ_kesim["seviye"] == "KRİTİK"

    # Sürekli İşçi: 3 işgünü haklı fesih
    u_isci = devamsizlik_yaptirim_uyarisi("Sürekli İşçi", 3)
    assert u_isci is not None
    assert "FESİH" in u_isci["mesaj"]

def test_mevzuat_bilgisi_endpoint():
    res = client.get("/mevzuat-bilgisi/İUP")
    assert res.status_code == 200
    data = res.json()
    assert data["basarili"] is True
    assert data["veri"]["brans_goster"] is False

def test_personel_ekle_memur_veya_isci_brans_ve_kariyer_sormadan_kaydeder():
    # Sürekli işçi personeli branş ve kariyer alanları olmadan ekleme
    payload = {
        "ad_soyad": "TEST SÜREKLİ İŞÇİ AHMET",
        "unvan": "Temizlik Personeli",
        "gorev": "Destek Hizmetleri",
        "grup": "Sürekli İşçi",
        "tc_no": "11111111118",
        "aktif": 1
    }
    res = client.post("/personel-profil-guncelle", json=payload)
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # Personeller listesinden kontrol et
    p_res = client.get("/personeller")
    assert p_res.status_code == 200
    personeller = p_res.json().get("personeller", [])
    bulunan = next((p for p in personeller if p["ad"] == "TEST SÜREKLİ İŞÇİ AHMET"), None)
    assert bulunan is not None
    assert bulunan["grup"] == "Sürekli İşçi"
    # brans ve kariyer otomatik '-' olmalıdır
    assert bulunan["brans"] == "-"
    assert bulunan["kariyer"] == "-"

    # Temizle
    client.delete("/personel-sil/TEST SÜREKLİ İŞÇİ AHMET")

def test_personel_ekle_iup_kariyer_derece_kademe_olmadan_kaydeder():
    # İUP personeli eklenirken kariyer, derece-kademe, branş, emekli sicil girilmez
    payload = {
        "ad_soyad": "TEST IUP PERSONEL MEHMET",
        "unvan": "İUP Katılımcısı",
        "gorev": "Temizlik ve Bakım",
        "grup": "İUP",
        "tc_no": "11111111119",
        "kurumda_baslama": "01/10/2026",
        "kurum_adi": "Örnek Anadolu Lisesi",
        "telefon": "05551234567",
        "aktif": 1
    }
    res = client.post("/personel-profil-guncelle", json=payload)
    assert res.status_code == 200
    assert res.json()["basarili"] is True

    # Personeller listesinden kontrol et
    p_res = client.get("/personeller")
    assert p_res.status_code == 200
    personeller = p_res.json().get("personeller", [])
    bulunan = next((p for p in personeller if p["ad"] == "TEST IUP PERSONEL MEHMET"), None)
    assert bulunan is not None
    assert bulunan["grup"] == "İUP"
    # İUP için branş, kariyer ve kademe_derece otomatik '-' olmalıdır
    assert bulunan["brans"] == "-"
    assert bulunan["kariyer"] == "-"
    assert bulunan["kademe_derece"] == "-"

    # Temizle
    client.delete("/personel-sil/TEST IUP PERSONEL MEHMET")

def test_frontend_wizard_ve_dinamik_form_bilesenleri():
    # Profil modalında Adım 1 seçim ekranı ve Adım 2 form ekranı olmalı
    with open("frontend/components/personel_profil_modal.html", "r", encoding="utf-8") as f:
        modal_html = f.read()

    assert "id=\"pp_adim_statu_secimi\"" in modal_html
    assert "id=\"pp_adim_form_alani\"" in modal_html
    assert "id=\"pp_btn_tur_degistir\"" in modal_html
    assert "ppStatuSecildi('İUP'" in modal_html
    assert "id=\"pp_brans_kapsayici\"" in modal_html
    assert "id=\"pp_kariyer_kapsayici\"" in modal_html
    assert "id=\"pp_kademe_derece_kapsayici\"" in modal_html
    assert "id=\"pp_kurum_sicil_kapsayici\"" in modal_html

    # JS tarafında sihirbaz ve statü fonksiyonları tanımlı olmalı
    with open("frontend/js/personel_teblig.js", "r", encoding="utf-8") as f:
        js_code = f.read()

    assert "function ppStatuSecildi" in js_code
    assert "function ppStatuSecimineGeriDon" in js_code
    assert "function ppFormuStatuyaGoreAyarla" in js_code
    assert "pp_adim_statu_secimi" in js_code


def test_yeni_mevzuat_fonksiyonlari_ve_kutuphanesi():
    from mevzuat_kurallari import (
        DAYANAK_MEVZUAT_ENVANTERI,
        OGRENCI_MEVZUAT_KURALLARI,
        KARIYER_BASAMAKLARI_KURALLARI,
        YONETICI_GOREVLERI_KURALLARI,
        yonetici_mi,
        yonetici_oncelik_sirasi,
        kariyer_basamagi_hakki,
        ogrenci_devamsizlik_durumu,
        tum_mevzuat_ozeti
    )

    # 1. Dayanak kütüphanesi kontrolü
    assert "657_SK" in DAYANAK_MEVZUAT_ENVANTERI
    assert "7528_SK" in DAYANAK_MEVZUAT_ENVANTERI
    assert "MEB_ORTAOGRETIM_YON" in DAYANAK_MEVZUAT_ENVANTERI

    # 2. Yönetici hiyerarşisi ve öncelik sıralaması
    assert yonetici_mi("Müdür", "Okul Müdürü") is True
    assert yonetici_mi("Müdür Yardımcısı", "İdareci") is True
    assert yonetici_mi("Öğretmen", "Matematik") is False

    assert yonetici_oncelik_sirasi("Okul Müdürü") == 1
    assert yonetici_oncelik_sirasi("Müdür Başyardımcısı") == 2
    assert yonetici_oncelik_sirasi("Müdür Yardımcısı") == 3
    assert yonetici_oncelik_sirasi("Müdür Yetkili Öğretmen") == 4
    assert yonetici_oncelik_sirasi("Öğretmen") == 99

    # 3. 7528 SK Kariyer basamağı hak hesaplama
    # 10 yıl hizmet -> Uzman Öğretmen (+1 derece)
    u_hak = kariyer_basamagi_hakki(10, "Öğretmen", ceza_var_mi=False)
    assert u_hak["basvuru_yapabilir_mi"] is True
    assert u_hak["hak_kazanilan_unvan"] == "Uzman Öğretmen"
    assert u_hak["derece_artisi"] == "+1 Derece"

    # 20 yıl hizmet -> Başöğretmen (7528 SK Geçici Md. 1)
    b_hak = kariyer_basamagi_hakki(20, "Öğretmen", ceza_var_mi=False)
    assert b_hak["basvuru_yapabilir_mi"] is True
    assert b_hak["hak_kazanilan_unvan"] == "Başöğretmen"

    # Ceza engeli
    c_hak = kariyer_basamagi_hakki(15, "Öğretmen", ceza_var_mi=True)
    assert c_hak["basvuru_yapabilir_mi"] is False

    # 4. Öğrenci devamsızlık ve yasal sınır değerlendirmesi (2025 RG)
    # Standart öğrenci: 10.5 gün özürsüz -> kaldı
    d_std = ogrenci_devamsizlik_durumu(10.5, 20.0)
    assert d_std["sinif_tekrar_riski"] is True

    # 1. derece vefat: 10 gün özürsüz, 35 gün toplam -> kalmadı (sınır 40)
    d_vefat = ogrenci_devamsizlik_durumu(8.0, 35.0, ozel_durum="vefat_1_derece")
    assert d_vefat["sinif_tekrar_riski"] is False
    assert d_vefat["toplam_sinir"] == 40.0

    # Ağır tedavi: toplam 50 gün -> kalmadı (sınır 60)
    d_tedavi = ogrenci_devamsizlik_durumu(7.0, 50.0, ozel_durum="agir_tedavi_ve_koruma")
    assert d_tedavi["sinif_tekrar_riski"] is False
    assert d_tedavi["toplam_sinir"] == 60.0

    # Kaynaştırma: özürsüz 15 gün, toplam 65 gün -> kalmadı (sınır 20 ve 70)
    d_kay = ogrenci_devamsizlik_durumu(15.0, 65.0, ozel_durum="kaynastirma_ve_ozel_egitim")
    assert d_kay["sinif_tekrar_riski"] is False
    assert d_kay["toplam_sinir"] == 70.0

    # 5. API /mevzuat-ozeti endpoint testi
    res = client.get("/mevzuat-ozeti")
    assert res.status_code == 200
    veri = res.json()["veri"]
    assert "dayanak_envanteri" in veri
    assert "ogrenci_devamsizlik_mevzuati" in veri
    assert "kariyer_basamaklari" in veri

