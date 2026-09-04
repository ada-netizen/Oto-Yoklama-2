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