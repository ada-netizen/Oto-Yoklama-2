import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from araclar import VeriAraclari

def test_haftasonu_haric_hesaplama():
    """Hafta sonuna denk gelen devamsızlıkların genel toplamdan düşülüp düşülmediğini test eder."""
    
    ornek_devamsizliklar = [
        # 1. Kayıt: 1 Tam gün hafta içi (Cuma) - Özürsüz (D)
        {'no': '852', 'tarih': '01/05/2026', 'tur': 'D', 'gun': '1'}, 
        
        # 2. Kayıt: 2 Tam gün (Cumartesi ve Pazar) - Özürlü (İ)
        # Normalde 2 gün ekler ama hafta sonu olduğu için NET TOPLAMA 0 geçmeli!
        {'no': '852', 'tarih': '02/05/2026', 'tur': 'İ', 'gun': '2'}, 
        
        # 3. Kayıt: 1.5 Gün (Pazartesi ve Salı yarım) - Özürsüz (D)
        {'no': '852', 'tarih': '04/05/2026', 'tur': 'D', 'gun': '1.5'}, 
    ]

    ozsz_net, ozrl_net = VeriAraclari.hesapla_devamsizlik('852', ornek_devamsizliklar, [])

    # Özürsüz (D) = 1 (Cuma) + 1.5 (Pzt-Salı) = 2.5 Gün
    # Özürlü (İ)  = Sadece Cmt-Pzr'ye denk geldiği için = 0.0 Gün
    assert ozsz_net == 2.5, f"HATA! Özürsüz hesaplaması bozuk. Beklenen: 2.5, Sistemdeki: {ozsz_net}"
    assert ozrl_net == 0.0, f"HATA! Hafta sonu filtresi bozulmuş. Beklenen: 0.0, Sistemdeki: {ozrl_net}"

def test_gec_kalma_hesaplamasi():
    """5 adet Geç (G) kalmanın tam olarak 0.5 gün Özürsüz yapıp yapmadığını test eder."""
    
    ornek_dev = [
        {'no': '852', 'tarih': '01/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '02/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '03/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '04/05/2026', 'tur': 'G', 'gun': '1'},
        {'no': '852', 'tarih': '05/05/2026', 'tur': 'G', 'gun': '1'},
    ]
    
    ozsz_net, ozrl_net = VeriAraclari.hesapla_devamsizlik('852', ornek_dev, [])
    assert ozsz_net == 0.5, "HATA! 5 adet Geç (G) kaydı 0.5 gün Özürsüz yapmalıdır!"


def test_excel_motoru_tabloyu_guvenli_oku_html_xls(tmp_path):
    """MEB e-Okul tarzı HTML formatındaki sahte .xls dosyalarının güvenli okunduğunu doğrular."""
    from excel_motoru import ExcelMotoru
    
    html_icerik = """
    <html>
    <head><meta http-equiv="Content-Type" content="text/html; charset=windows-1254"></head>
    <body>
    <table>
        <tr><th>Öğrenci No</th><th>Adı Soyadı</th><th>Sınıf</th></tr>
        <tr><td>101</td><td>Ahmet Çelik</td><td>9/A</td></tr>
        <tr><td>102</td><td>Şule Öztürk</td><td>9/B</td></tr>
    </table>
    </body>
    </html>
    """
    dosya = tmp_path / "ogrenciler_fake.xls"
    dosya.write_bytes(html_icerik.encode("cp1254"))

    df = ExcelMotoru.tabloyu_guvenli_oku(str(dosya), header=0)
    assert not df.empty
    assert "Ahmet Çelik" in df.values
    assert "Şule Öztürk" in df.values


def test_excel_motoru_tabloyu_guvenli_oku_csv(tmp_path):
    """CSV formatındaki aktarım dosyalarının hatasız okunduğunu doğrular."""
    from excel_motoru import ExcelMotoru

    csv_icerik = "Öğrenci No;Adı Soyadı;Sınıf\n201;Çağlar Şahin;10/C\n202;İpek Aydın;10/C\n"
    dosya = tmp_path / "ogrenciler.csv"
    dosya.write_bytes(csv_icerik.encode("utf-8-sig"))

    df = ExcelMotoru.tabloyu_guvenli_oku(str(dosya), header=0)
    assert not df.empty
    assert len(df) >= 2


def test_excel_motoru_fuzzy_sutun_haritalama(tmp_path):
    """ExcelMotoru'nun farklı e-Okul sütun varyasyonlarını (Okul No, Adı Soyadı, Sınıf/Şube) doğru tespit ettiğini doğrular."""
    from excel_motoru import ExcelMotoru
    import pandas as pd

    # Varyasyon 1: Okul No / Adı Soyadı / Sınıf
    dosya1 = tmp_path / "ogrenciler_v1.xlsx"
    pd.DataFrame([
        {"Okul No": "301", "Adı Soyadı": "Canan Yılmaz", "Sınıf": "11/A"},
        {"Okul No": "302", "Adı Soyadı": "Burak Demir", "Sınıf": "11/B"}
    ]).to_excel(dosya1, index=False)

    ogrenciler1, hata1 = ExcelMotoru.ogrenci_oku(str(dosya1), [])
    assert not hata1
    assert len(ogrenciler1) == 2
    assert ogrenciler1[0]["no"] == "301"
    assert ogrenciler1[0]["ad_soyad"] == "Canan Yılmaz"
    assert "11/A" in ogrenciler1[0]["sube"]

    # Varyasyon 2: Numara / Ad / Soyad / Sınıf/Şube
    dosya2 = tmp_path / "ogrenciler_v2.xlsx"
    pd.DataFrame([
        {"Numara": "401", "Ad": "Elif", "Soyad": "Koç", "Sınıf/Şube": "12/C"}
    ]).to_excel(dosya2, index=False)

    ogrenciler2, hata2 = ExcelMotoru.ogrenci_oku(str(dosya2), [])
    assert not hata2
    assert len(ogrenciler2) == 1
    assert ogrenciler2[0]["no"] == "401"
    assert ogrenciler2[0]["ad_soyad"] == "Elif Koç"


def test_ihale_stilleri_font_ve_stil_onbellekleme():
    """ihale_stilleri modülünün ReportLab ve openpyxl stillerini önbellekten tutarlı döndürdüğünü doğrular."""
    from ihale_stilleri import font_hazirla, get_ihale_stilleri, FONT_TITLE_12, THIN_BORDER
    
    font1 = font_hazirla()
    font2 = font_hazirla()
    assert font1 == font2
    assert isinstance(font1, str)

    stiller = get_ihale_stilleri()
    assert 'normal' in stiller
    assert 'justify' in stiller
    assert 'center' in stiller
    assert 'title' in stiller

    assert FONT_TITLE_12.bold is True
    assert THIN_BORDER.left.style == "thin"


