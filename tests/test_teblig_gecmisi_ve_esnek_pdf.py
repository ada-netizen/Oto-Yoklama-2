import os
import sys
import json
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api
import dependencies

app = api.app
client = TestClient(app)

@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Her test bağımsız geçici veritabanında çalışır."""
    test_db = api.VeritabaniYoneticisi(str(tmp_path / "test_teblig.db"))
    monkeypatch.setattr(api, "db", test_db)
    monkeypatch.setattr(dependencies, "db", test_db)
    import routes.pdf
    monkeypatch.setattr(routes.pdf, "db", test_db)
    import routes.saglik
    monkeypatch.setattr(routes.saglik, "db", test_db)

    # Personel ekle
    test_db.cursor.execute("""
        INSERT INTO personel (ad_soyad, tc_no, unvan, brans, gorev, grup, aktif)
        VALUES 
            ('FATMA YILMAZ', '11111111111', 'Öğretmen', 'Matematik', 'Öğretmen', 'Kadrolu', 1),
            ('MEHMET ÖZTÜRK', '22222222222', 'Müdür Yardımcısı', 'Bilişim', 'Müdür Yardımcısı', 'Kadrolu', 1),
            ('ALİ KAYA', '33333333333', 'Memur', '-', 'Memur', 'Kadrolu', 1)
    """)
    test_db.conn.commit()
    return test_db


def test_teblig_gecmisi_bos_ve_ekleme(isolated_db):
    """Tebliğ geçmişinin boş başladığını, doğrudan ekleme yapıldığında ve API çağrıldığında doğru listelendiğini test eder."""
    resp = client.get("/teblig-gecmisi")
    assert resp.status_code == 200
    assert resp.json()["basarili"] is True
    assert len(resp.json()["veri"]) == 0

    # Veritabanına bir toplu tebliğ kaydı simüle edelim
    edilenler = [{"ad": "FATMA YILMAZ", "gorev": "Öğretmen", "brans": "Matematik"}, {"ad": "ALİ KAYA", "gorev": "Memur", "brans": "-"}]
    isolated_db.cursor.execute("""
        INSERT INTO tebligat_kayitlari (olusturma_tarihi, kurum, sayi, evrak_tarihi, konu, teblig_turu, teblig_eden, teblig_edilenler, kisi_sayisi, dosya_yolu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "2026-10-21 10:00:00",
        "Kadıköy İlçe Millî Eğitim Müdürlüğü",
        "E-12345678",
        "20.10.2026",
        "29 Ekim Cumhuriyet Bayramı Kutlama Programı",
        "Toplu Tebliğ",
        "",
        json.dumps(edilenler, ensure_ascii=False),
        2,
        "C:/tmp/Toplu_Imza_Sirkusu.pdf"
    ))
    isolated_db.conn.commit()

    # Tekrar oku
    resp2 = client.get("/teblig-gecmisi")
    assert resp2.status_code == 200
    data = resp2.json()["veri"]
    assert len(data) == 1
    kayit = data[0]
    assert kayit["kurum"] == "Kadıköy İlçe Millî Eğitim Müdürlüğü"
    assert kayit["sayi"] == "E-12345678"
    assert kayit["teblig_turu"] == "Toplu Tebliğ"
    assert kayit["kisi_sayisi"] == 2
    assert len(kayit["teblig_edilenler"]) == 2
    assert kayit["teblig_edilenler"][0]["ad"] == "FATMA YILMAZ"


def test_teblig_silme(isolated_db):
    """Tebliğ kaydının silinebildiğini doğrular."""
    isolated_db.cursor.execute("""
        INSERT INTO tebligat_kayitlari (olusturma_tarihi, kurum, sayi, evrak_tarihi, konu, teblig_turu, teblig_eden, teblig_edilenler, kisi_sayisi, dosya_yolu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "2026-10-21 11:00:00",
        "İl Millî Eğitim Müdürlüğü",
        "E-99999",
        "21.10.2026",
        "Seminer Duyurusu",
        "Bireysel Tebliğ",
        "MEHMET ÖZTÜRK",
        json.dumps([{"ad": "FATMA YILMAZ"}], ensure_ascii=False),
        1,
        ""
    ))
    isolated_db.conn.commit()
    kayit_id = isolated_db.cursor.lastrowid

    # Sil
    resp_del = client.delete(f"/teblig-gecmisi/{kayit_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["basarili"] is True

    # Artık listede olmamalı
    resp = client.get("/teblig-gecmisi")
    assert len(resp.json()["veri"]) == 0


def test_saglik_pdf_konu_parantez_ici_ad(monkeypatch):
    """MEB DYS belgelerinde Konu satırında parantez içinde yer alan personel adının başarıyla çözümlendiğini doğrular."""
    pdf_text = (
        "T.C.\n"
        "KADIKÖY KAYMAKAMLIĞI\n"
        "İlçe Millî Eğitim Müdürlüğü\n"
        "Sayı : E-12345678-903.02-998877\n"
        "Konu : Hastalık İzni (Fatma YILMAZ)\n\n"
        "KADIKÖY ANADOLU LİSESİ MÜDÜRLÜĞÜNE\n"
        "Okulunuz personeli Fatma YILMAZ'ın 14/10/2026 tarihinden itibaren 5 gün süreyle hastalık izni kullanması uygun görülmüştür.\n"
        "Bilgilerinizi ve gereğini rica ederim.\n"
    )

    class MockPage:
        def extract_text(self):
            return pdf_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin_konu.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["izin_turu"] == "SAĞLIK"
    assert res["baslangic"] == "2026-10-14"
    assert res["gun_sayisi"] == 5


def test_saglik_pdf_duz_yazi_olur_metni(monkeypatch):
    """Tablosuz DYS Olur metinlerinde öğretmen adı ve '... tarihinden itibaren X gün' ifadesinin çözümlendiğini doğrular."""
    pdf_text = (
        "T.C. MİLLÎ EĞİTİM BAKANLIĞI\n"
        "Valilik Oluru\n"
        "Konu : Mazeret İzni\n\n"
        "Okulumuz Matematik Öğretmeni FATMA YILMAZ'ın 20.11.2026 tarihinden itibaren 7 (yedi) gün süreyle mazeret izni kullanması hususunda;\n"
        "Olurlarınıza arz ederim.\n"
        "Okul Müdürü : AHMET DEMİR\n"
        "Uygundur.\n"
    )

    class MockPage:
        def extract_text(self):
            return pdf_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin_olur.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["izin_turu"] == "MAZERET"
    assert res["baslangic"] == "2026-11-20"
    assert res["gun_sayisi"] == 7


def test_saglik_pdf_kismi_eslesme_uyari_notu(monkeypatch):
    """Tarih okunamasa bile personel adı bulunduğunda başarısızlık yerine formu açıp uyarı verdiğini doğrular."""
    pdf_text = (
        "T.C. İÇİŞLERİ BAKANLIĞI\n"
        "Konu : Yıllık İzin (ALİ KAYA)\n"
        "İlgili personelin yıllık izin talebi onaylanmıştır.\n"
    )

    class MockPage:
        def extract_text(self):
            return pdf_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin_kismi.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "ALİ KAYA"
    assert res["izin_turu"] == "YILLIK"
    assert "tarih" in res.get("uyari_notu", "").lower()



def test_yillik_izin_pdf_tam_cozumleme_ve_kayit(monkeypatch, isolated_db):
    """MEB Yıllık İzin Onay Belgesinden 'İznin Çeşidi', 'İznin Süresi', 'Ayrılış/Başlama Tarihi' ve 'Adres' alanlarının başarıyla çözümlendiğini ve loglandığını doğrular."""
    pdf_text = (
        "T.C.\n"
        "İSTANBUL VALİLİĞİ\n"
        "Kadıköy İlçe Millî Eğitim Müdürlüğü\n"
        "Sayı : E-2026/12345\n"
        "Konu : İzin Onayı\n\n"
        "KADIKÖY ANADOLU LİSESİ MÜDÜRLÜĞÜNE\n"
        "Adı ve Soyadı : FATMA YILMAZ\n"
        "Unvanı : Memur\n"
        "İznin Çeşidi : Yıllık İzin\n"
        "İznin Süresi : 15 Gün\n"
        "İznin Başlama Tarihi : 01.07.2026\n"
        "Göreve Başlayacağı Tarih : 16.07.2026\n"
        "İznini Geçireceği Açık Adres : Bodrum / MUĞLA\n"
    )

    class MockPage:
        def extract_text(self):
            return pdf_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("yillik_izin.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["izin_turu"] == "YILLIK"
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["gun_sayisi"] == 15
    assert res["baslangic"] == "2026-07-01"
    assert res["bitis"] == "2026-07-15"
    assert "Bodrum" in res["izin_adresi"]

    # Şimdi bu yıllık izni ekleyelim
    resp_ekle = client.post("/saglik/ekle", json={
        "personel_ad": res["ad_soyad"],
        "izin_turu": res["izin_turu"],
        "baslangic_tarihi": res["baslangic"],
        "bitis_tarihi": res["bitis"],
        "gun_sayisi": res["gun_sayisi"],
        "izin_adresi": res["izin_adresi"]
    })
    assert resp_ekle.status_code == 200
    assert resp_ekle.json()["basarili"] is True


def test_mazeret_izni_pdf_tam_cozumleme(monkeypatch):
    """MEB Mazeret İzni Formundan 'İzin Türü', 'İzin İsteyenin Adı Soyadı', 'İzin Süresi' ve tarihlerin çözümlendiğini doğrular."""
    pdf_text = (
        "T.C. MİLLÎ EĞİTİM BAKANLIĞI\n"
        "Konu : İzin Formu\n\n"
        "İzin İsteyenin Adı Soyadı : ALİ KAYA\n"
        "Görevi : Öğretmen\n"
        "İzin Türü : Mazeret İzni\n"
        "İzin Süresi : 7 Gün\n"
        "İzin Başlangıç Tarihi : 10/05/2026\n"
        "İzin Bitiş Tarihi : 16/05/2026\n"
        "İzni Geçireceği Adres : Çeşme / İZMİR\n"
    )

    class MockPage:
        def extract_text(self):
            return pdf_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("mazeret_izin.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["izin_turu"] == "MAZERET"
    assert res["ad_soyad"] == "ALİ KAYA"
    assert res["gun_sayisi"] == 7
    assert res["baslangic"] == "2026-05-10"
    assert res["bitis"] == "2026-05-16"
    assert "Çeşme" in res["izin_adresi"]
