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
    assert "Çağrı Özışık" in metin
    assert "Özürlü" in metin
    assert "MÜDÜRLÜĞÜNE" in metin
    assert "DEVAMSIZLIK BİLGİLENDİRME FORMU" in metin


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
    assert "Sayfa 1/2" in (sayfalar[0].extract_text() or "")
    assert "Sayfa 2/2" in (sayfalar[1].extract_text() or "")
    assert "Devamı arka sayfadadır." not in (sayfalar[0].extract_text() or "")
    assert "DEVAMSIZLIK BİLGİLENDİRME FORMU - DEVAMI" not in (sayfalar[1].extract_text() or "")


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