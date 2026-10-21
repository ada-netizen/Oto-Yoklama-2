import os
import sys

from PyPDF2 import PdfReader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_motoru import PDFYoneticisi


def test_veli_pdf_turkce_karakter_a5_ve_cerceveyi_korur(tmp_path):
    hedef = tmp_path / "veli_formu.pdf"
    motor = PDFYoneticisi({"okul_adi": "Çınar Şehitliği ÖĞRETMEN Lisesi"})

    basarili, hata = motor.veli_formu_ciz(
        "12",
        "Çağrı Özışık",
        "9/A",
        [{"tarih_duzgun": "01/09/2026", "tur": "Özürlü", "gun_str": "1"}],
        str(hedef),
        ozurlu_str="1",
        ozursuz_str="0",
    )

    assert basarili is True
    assert hata == ""
    assert hedef.exists() and hedef.stat().st_size > 0

    sayfa = PdfReader(str(hedef)).pages[0]
    assert round(float(sayfa.mediabox.width), 2) == 419.53
    assert round(float(sayfa.mediabox.height), 2) == 595.27
    metin = sayfa.extract_text() or ""
    assert "Çağrı ÖZIŞIK" in metin
    assert "Özürlü" in metin
    assert "MÜDÜRLÜĞÜNE" in metin
    assert "DEVAMSIZLIK BİLGİLENDİRME FORMU" in metin
    assert "Tarih" in metin
    assert "İmza" in metin
    assert "Tel" in metin


def test_veli_pdf_cok_sayfada_sayfa_numarasini_ve_alt_imza_blogunu_tekrarlar(tmp_path):
    hedef = tmp_path / "cok_sayfali_veli_formu.pdf"
    kayitlar = [
        {"tarih_duzgun": f"{gun:02d}/09/2026", "tur": "D", "gun_str": "1"}
        for gun in range(1, 21)
    ]
    motor = PDFYoneticisi({"okul_adi": "Çınar Lisesi"})

    basarili, hata = motor.veli_formu_ciz(
        "12", "Çağrı Özışık", "9/A", kayitlar, str(hedef), "2", "3"
    )

    assert basarili is True
    assert hata == ""
    sayfalar = PdfReader(str(hedef)).pages
    assert len(sayfalar) >= 2
    for sayfa in sayfalar:
        metin = sayfa.extract_text() or ""
        assert "Özürsüz Devamsızlık" in metin
        assert "Özürlü Devamsızlık" in metin
        assert "Toplam Devamsızlık" in metin
        assert "İmza" in metin
        assert "Tarih" in metin
        assert "Tel" in metin
    assert "Sayfa 1/2" in (sayfalar[0].extract_text() or "")
    assert "Sayfa 2/2" in (sayfalar[1].extract_text() or "")
    assert "Devamı arka sayfadadır." not in (sayfalar[0].extract_text() or "")
    assert "DEVAMSIZLIK BİLGİLENDİRME FORMU - DEVAMI" not in (sayfalar[1].extract_text() or "")


def test_izin_sablonu_tarih_ve_tel_satiri(tmp_path):
    hedef = tmp_path / "izin_sablonu.pdf"
    motor = PDFYoneticisi({"okul_adi": "Çınar Lisesi"})
    basarili, hata = motor.izin_sablonu_ciz(str(hedef))

    assert basarili is True
    assert hata == ""
    assert hedef.exists() and hedef.stat().st_size > 0
    sayfa = PdfReader(str(hedef)).pages[0]
    metin = sayfa.extract_text() or ""
    assert "Tarih" in metin
    assert "Velisi" in metin
    assert "İmza" in metin
    assert "Tel" in metin


def test_toplu_teblig_turkce_okul_adi_ve_personel_bilgilerini_yazar(tmp_path):
    hedef = tmp_path / "toplu_teblig.pdf"
    motor = PDFYoneticisi({"okul_adi": "Çınar Şehitliği Lisesi"})

    motor.teblig_tebellug_ciz(
        "12",
        "Görev yazısı",
        "06/09/2026",
        [{
            "ad": "Çağrı Özışık",
            "gorev": "Öğretmen",
            "brans": "Türkçe",
            "grup": "Öğretmenler",
        }],
        str(hedef),
    )

    metin = PdfReader(str(hedef)).pages[0].extract_text() or ""
    assert "ÇINAR ŞEHİTLİĞİ LİSESİ" in metin
    assert "Çağrı Özışık" in metin
    assert "Grup" not in metin
    assert "Branş" not in metin


def test_piyasa_fiyat_arastirmasi_tutanağı_adi_ve_onay_cumlesi_dogru_yazilir(tmp_path):
    from ihale_motoru import uret_piyasa_arastirmasi_pdf

    veri = {
        "resmi_baslik": "ATATÜRK ORTAOKULU",
        "ihale_konusu": "Kırtasiye Alımı",
        "belge_tarihi": "2026-09-09",
        "komisyon_onaylari": {
            "ihale_kom_piyasa": {
                "kurum": "ATATÜRK ORTAOKULU",
                "sayi": "2026/14",
                "tarih": "06.09.2026",
            }
        },
        "firmalar": ["A Firma", "B Firma", "C Firma", "D Firma"],
        "firma_vergiler": ["1234567890", "12345678901", "1234567890", "1234567890"],
        "firma_adresleri": ["İstanbul", "Ankara", "İzmir", "Bursa"],
        "kalemler": [{"cins": "Kalem", "miktar": "10", "birim": "Adet", "fiyatlar": [10, 12, 11, 9]}],
    }

    dosya = uret_piyasa_arastirmasi_pdf(veri, str(tmp_path))

    assert os.path.exists(dosya)
    metin = PdfReader(dosya).pages[0].extract_text() or ""
    assert "Atatürk Ortaokulu Müdürlüğü" in metin
    assert "Yetkilendirilen Görevlilere ilişkin Onayın Tarih ve Nosu" in metin
    assert "Müdürlüğünün 2026/14 sayılı ve 06.09.2026 tarihli onayı" in metin or "Müdürlüğünün 2026/14 Sayılı ve 06.09.2026 Tarihli onayı" in metin
    assert "PİYASA FİYAT ARAŞTIRMASI TUTANAĞI" in metin or "P İ Y A S A F İ Y A T A R A Ş T I R M A S I T U T A N A Ğ I" in metin
    assert "PİYASA FİYAT ARAŞTIRMASI GÖREVLİSİ / GÖREVLİLERİ" in metin or "P İ Y A S A F İ Y A T A R A Ş T I R M A S I G Ö R E V L İ S İ / G Ö R E V L İ L E R İ" in metin
    assert "Tümünün Bu Kişi / Firmadan Alımı Uygun Görülmüştür." in metin
    assert "İstanbul" in metin or "Ankara" in metin or "İzmir" in metin or "Bursa" in metin

def test_ihale_bilgi_girisi_verileri_pdfye_islenir(tmp_path):
    """Bilgi Girişi modalından girilen resmi_baslik ve yazisma_kodu alanlarının PDF belgelerine aktarılmasını test eder."""
    from ihale_motoru import uret_fiyat_isteme_pdf, uret_ozel_fiyat_isteme_pdf, uret_muayene_kabul_pdf
    
    veri = {
        "resmi_baslik": "T.C.\nBİNGÖL VALİLİĞİ\n100. Yıl İlkokulu Müdürlüğü",
        "yazisma_kodu": "12345678-903.02.01",
        "ihale_konusu": "Kırtasiye Malzemesi Alımı",
        "belge_tarihi": "2026-10-21",
        "firmalar": ["Firma A", "Firma B", "Firma C"],
        "firma_vergiler": ["1111111111", "2222222222", "3333333333"],
        "firma_adresleri": ["Adres 1", "Adres 2", "Adres 3"],
        "kalemler": [{"cins": "A4 Kağıt", "miktar": "20", "birim": "Paket", "fiyatlar": [100, 110, 105]}],
        "komisyon": {
            "ihale_kom_yaklasik_1": "Ali Yılmaz",
            "ihale_kom_yaklasik_2": "Veli Kaya",
            "ihale_kom_yaklasik_3": "Ayşe Demir"
        }
    }
    
    # 1. Fiyat İsteme PDF
    fiyat_pdf = uret_fiyat_isteme_pdf(veri, str(tmp_path))
    assert os.path.exists(fiyat_pdf)
    fiyat_text = PdfReader(fiyat_pdf).pages[0].extract_text() or ""
    assert "T.C." in fiyat_text
    assert "BİNGÖL VALİLİĞİ" in fiyat_text
    assert "100. Yıl İlkokulu Müdürlüğü" in fiyat_text
    assert "12345678-903.02.01" in fiyat_text
    
    # 2. Özel Fiyat İsteme PDF
    ozel_pdf = uret_ozel_fiyat_isteme_pdf(veri, str(tmp_path))
    assert os.path.exists(ozel_pdf)
    ozel_text = PdfReader(ozel_pdf).pages[0].extract_text() or ""
    assert "T.C." in ozel_text
    assert "BİNGÖL VALİLİĞİ" in ozel_text
    assert "12345678-903.02.01" in ozel_text
    
    # 3. Muayene Kabul PDF
    muayene_pdf = uret_muayene_kabul_pdf(veri, str(tmp_path))
    assert os.path.exists(muayene_pdf)
    muayene_text = PdfReader(muayene_pdf).pages[0].extract_text() or ""
    assert "T.C." in muayene_text
    assert "BİNGÖL VALİLİĞİ" in muayene_text
    assert "100. Yıl İlkokulu Müdürlüğü" in muayene_text


def test_ihale_tekli_belge_endpoint_resmi_baslik_ve_yazisma_kodu_korur():
    """/ihale-tekli-belge endpoint'inin resmi_baslik ve yazisma_kodu alanlarını doğru işlediğini doğrular."""
    from fastapi.testclient import TestClient
    import api
    app = api.app
    from unittest.mock import patch

    client = TestClient(app)
    
    istek_verisi = {
        "resmi_baslik": "T.C.\nBİNGÖL VALİLİĞİ\nMerkez İlkokulu Müdürlüğü",
        "yazisma_kodu": "98765432-805.01",
        "ihale_konusu": "Temizlik Malzemesi",
        "belge_tarihi": "2026-10-21",
        "belge_tipi": "fiyat_isteme",
        "format": "pdf",
        "kalemler": [{"cins": "Sabun", "miktar": "10", "birim": "Adet"}]
    }
    
    yakalanan_veri = {}
    def mock_belge_uret(veri, yol):
        yakalanan_veri.update(veri)
        return "dummy_path.pdf"
        
    with patch("ihale_motoru.belge_uret", side_effect=mock_belge_uret):
        with patch("os.path.exists", return_value=False):
            resp = client.post("/ihale-tekli-belge", json=istek_verisi)
            assert resp.status_code == 200
            assert resp.json()["basarili"] is True
            
    assert yakalanan_veri.get("resmi_baslik") == "T.C.\nBİNGÖL VALİLİĞİ\nMerkez İlkokulu Müdürlüğü"
    assert yakalanan_veri.get("yazisma_kodu") == "98765432-805.01"

def test_toplu_teblig_imza_sirkusunde_idareciler_en_ustte_siralanir(tmp_path):
    """Toplu tebliğ imza sirküsü tablosunda idarecilerin (Müdür, Müdür Yardımcısı) en üstte sıralandığını doğrular."""
    from pdf_motoru import PDFYoneticisi
    
    motor = PDFYoneticisi({})
    kayit_yeri = str(tmp_path / "toplu_sirkusu_test.pdf")
    
    personeller = [
        {"ad": "Zeynep Çelik", "gorev": "Öğretmen", "unvan": "Öğretmen", "grup": "Öğretmenler"},
        {"ad": "Mehmet Demir", "gorev": "Müdür Yardımcısı", "unvan": "Müdür Yardımcısı", "grup": "İdare"},
        {"ad": "Ahmet Aslan", "gorev": "Öğretmen", "unvan": "Öğretmen", "grup": "Öğretmenler"},
        {"ad": "Kemal Şahin", "gorev": "Okul Müdürü", "unvan": "Müdür", "grup": "İdare"},
    ]
    
    motor.teblig_tebellug_ciz(
        sayi="2026/100",
        konu="Önemli Duyuru",
        tarih="21.10.2026",
        personeller=personeller,
        kayit_yeri=kayit_yeri,
        kurum="İlçe Milli Eğitim Müdürlüğü"
    )
    
    assert os.path.exists(kayit_yeri)
    pdf_metin = PdfReader(kayit_yeri).pages[0].extract_text() or ""
    
    # Sıralamayı metin akışındaki pozisyonlarına göre kontrol et
    pos_kemal = pdf_metin.find("Kemal Şahin")
    pos_mehmet = pdf_metin.find("Mehmet Demir")
    pos_ahmet = pdf_metin.find("Ahmet Aslan")
    pos_zeynep = pdf_metin.find("Zeynep Çelik")
    
    assert pos_kemal != -1, "Müdür Kemal Şahin PDF'te bulunamadı"
    assert pos_mehmet != -1, "Müdür Yardımcısı Mehmet Demir PDF'te bulunamadı"
    assert pos_ahmet != -1, "Ahmet Aslan PDF'te bulunamadı"
    assert pos_zeynep != -1, "Zeynep Çelik PDF'te bulunamadı"
    
    # Hiyerarşi doğrulaması:
    # 1. Okul Müdürü (Kemal Şahin)
    # 2. Müdür Yardımcısı (Mehmet Demir)
    # 3. Öğretmen Ahmet Aslan
    # 4. Öğretmen Zeynep Çelik
    assert pos_kemal < pos_mehmet, "Okul Müdürü (1. Kademe), Müdür Yardımcısından (2. Kademe) önce olmalıdır!"
    assert pos_mehmet < pos_ahmet, "Müdür Yardımcısı (2. Kademe), Öğretmenlerden (3. Kademe) önce olmalıdır!"
    assert pos_ahmet < pos_zeynep, "Öğretmenler kendi aralarında alfabetik olmalıdır (Ahmet < Zeynep)!"

