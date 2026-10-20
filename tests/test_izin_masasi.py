import os
import sys
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
    test_db = api.VeritabaniYoneticisi(str(tmp_path / "test_izin_masasi.db"))
    monkeypatch.setattr(api, "db", test_db)
    monkeypatch.setattr(dependencies, "db", test_db)
    import routes.saglik
    monkeypatch.setattr(routes.saglik, "db", test_db)

    # Örnek personeller ekleyelim: 1 İdareci/Öğretmen, 1 Memur, 1 Sürekli İşçi
    test_db.cursor.execute("""
        INSERT INTO personel (ad_soyad, tc_no, unvan, brans, gorev, grup, aktif)
        VALUES 
            ('MEHMET ÖZTÜRK', '11111111111', 'Müdür Yardımcısı', 'Bilişim', 'Müdür Yardımcısı', 'Kadrolu', 1),
            ('FATMA YILMAZ', '22222222222', 'Öğretmen', 'Matematik', 'Öğretmen', 'Kadrolu', 1),
            ('ALİ KAYA', '33333333333', 'Memur', '-', 'Yazı İşleri', 'Kadrolu', 1),
            ('VELİ DEMİR', '44444444444', 'Sürekli İşçi', '-', 'Güvenlik', 'Sürekli İşçi', 1)
    """)
    test_db.conn.commit()

    return test_db


def test_coklu_izin_ekleme_ve_mevzuat(isolated_db):
    """Sağlık, Yıllık ve Mazeret izinlerinin doğru izin türü ve mevzuat maddesiyle eklendiğini doğrular."""
    # 1. Mehmet Öztürk için 3 günlük Sağlık İzni
    resp_saglik = client.post("/saglik/ekle", json={
        "personel_ad": "MEHMET ÖZTÜRK",
        "baslangic_tarihi": "2026-03-10",
        "bitis_tarihi": "2026-03-12",
        "gun_sayisi": 3,
        "izin_turu": "SAĞLIK",
        "aciklama": "Grip - İstirahat"
    })
    assert resp_saglik.status_code == 200
    assert resp_saglik.json()["basarili"] is True

    # 2. Ali Kaya için 5 günlük Yıllık İzin
    resp_yillik = client.post("/saglik/ekle", json={
        "personel_ad": "ALİ KAYA",
        "baslangic_tarihi": "2026-07-01",
        "bitis_tarihi": "2026-07-05",
        "gun_sayisi": 5,
        "izin_turu": "YILLIK",
        "aciklama": "Yaz Yıllık İzni"
    })
    assert resp_yillik.status_code == 200
    assert resp_yillik.json()["basarili"] is True

    # 3. Fatma Yılmaz için 7 günlük Mazeret İzni (Evlilik)
    resp_mazeret = client.post("/saglik/ekle", json={
        "personel_ad": "FATMA YILMAZ",
        "baslangic_tarihi": "2026-05-11",
        "bitis_tarihi": "2026-05-17",
        "gun_sayisi": 7,
        "izin_turu": "MAZERET",
        "aciklama": "Evlilik Mazeret İzni"
    })
    assert resp_mazeret.status_code == 200
    assert resp_mazeret.json()["basarili"] is True

    # Veritabanında kontrol
    isolated_db.cursor.execute("SELECT personel_ad, izin_turu, mevzuat_maddesi FROM saglik_raporlari ORDER BY id")
    rows = isolated_db.cursor.fetchall()
    assert len(rows) == 3
    assert rows[0][1] == "SAĞLIK"
    assert "105" in rows[0][2]
    assert rows[1][1] == "YILLIK"
    assert "102" in rows[1][2]
    assert rows[2][1] == "MAZERET"
    assert "104" in rows[2][2]


def test_yedi_gunluk_kesinti_ayrimi(isolated_db):
    """
    657 DMK Md. 152:
    7 günü aşan zam ve tazminat kesintisi YALNIZCA sağlık izinlerine uygulanır.
    Yıllık veya Mazeret izinleri kesinti sayacını kesinlikle artırmaz!
    """
    curr_year = datetime.now().year

    # Fatma Yılmaz için 10 günlük Mazeret İzni ekle (7 günü aşıyor ama mazeret izni olduğu için kesinti OLMAMALI!)
    client.post("/saglik/ekle", json={
        "personel_ad": "FATMA YILMAZ",
        "baslangic_tarihi": f"{curr_year}-04-01",
        "bitis_tarihi": f"{curr_year}-04-10",
        "gun_sayisi": 10,
        "izin_turu": "MAZERET"
    })

    # Mehmet Öztürk için 9 günlük Sağlık İzni ekle (9 gün sağlık raporu -> 9 - 7 = 2 gün kesilecek!)
    client.post("/saglik/ekle", json={
        "personel_ad": "MEHMET ÖZTÜRK",
        "baslangic_tarihi": f"{curr_year}-02-01",
        "bitis_tarihi": f"{curr_year}-02-09",
        "gun_sayisi": 9,
        "izin_turu": "SAĞLIK"
    })

    resp = client.get(f"/saglik/liste?yil={curr_year}")
    assert resp.status_code == 200
    veri = resp.json()["veri"]

    fatma = next(p for p in veri if p["personel_ad"] == "FATMA YILMAZ")
    assert fatma["toplam"] == 10
    assert fatma["mazeret_gun"] == 10
    assert fatma["saglik_gun"] == 0
    assert fatma["yedi_gecen"] == 0  # Kesinti 0 olmalı!
    assert fatma["yeni_kesinti"] == 0

    mehmet = next(p for p in veri if p["personel_ad"] == "MEHMET ÖZTÜRK")
    assert mehmet["toplam"] == 9
    assert mehmet["saglik_gun"] == 9
    assert mehmet["yedi_gecen"] == 2  # 9 - 7 = 2 gün kesinti!
    assert mehmet["yeni_kesinti"] == 2


def test_cakisma_kontrolu_farkli_izinler(isolated_db):
    """Mevcut iznin olduğu tarihlerde çakışan yeni izin eklenemez ve uyarı dönülür."""
    client.post("/saglik/ekle", json={
        "personel_ad": "ALİ KAYA",
        "baslangic_tarihi": "2026-06-10",
        "bitis_tarihi": "2026-06-15",
        "gun_sayisi": 6,
        "izin_turu": "YILLIK"
    })

    # Aynı tarihlerde sağlık izni girmeye çalışalım
    resp_cakisma = client.post("/saglik/ekle", json={
        "personel_ad": "ALİ KAYA",
        "baslangic_tarihi": "2026-06-12",
        "bitis_tarihi": "2026-06-14",
        "gun_sayisi": 3,
        "izin_turu": "SAĞLIK"
    })
    assert resp_cakisma.status_code == 200
    res = resp_cakisma.json()
    assert res["basarili"] is False
    assert res.get("cakisma") is True
    assert "YILLIK" in res["mesaj"]


def test_365_gunluk_takvim_matrisi_api(isolated_db):
    """GET /saglik/takvim endpoint'inin 365 günlük takvim haritasını ve istatistikleri doğru döndürdüğü doğrulanır."""
    # 2026 yılı için Mehmet Öztürk (İdareci) 2 gün Sağlık İzni: 15-16 Nisan
    client.post("/saglik/ekle", json={
        "personel_ad": "MEHMET ÖZTÜRK",
        "baslangic_tarihi": "2026-04-15",
        "bitis_tarihi": "2026-04-16",
        "gun_sayisi": 2,
        "izin_turu": "SAĞLIK"
    })

    # Fatma Yılmaz (Öğretmen) 1 gün Mazeret İzni: 15 Nisan
    client.post("/saglik/ekle", json={
        "personel_ad": "FATMA YILMAZ",
        "baslangic_tarihi": "2026-04-15",
        "bitis_tarihi": "2026-04-15",
        "gun_sayisi": 1,
        "izin_turu": "MAZERET"
    })

    resp = client.get("/saglik/takvim?yil=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["basarili"] is True
    assert data["yil"] == 2026

    harita = data["takvim_haritasi"]
    # 15 Nisan günü (4-15) hem Mehmet hem Fatma olmalı (Aynı gün iki farklı izin türü: Kombine!)
    assert "4-15" in harita
    gun_15 = harita["4-15"]
    assert len(gun_15) == 2
    turler = {x["izin_turu"] for x in gun_15}
    assert "SAĞLIK" in turler
    assert "MAZERET" in turler

    # Mehmet Öztürk idareci bayrağı doğru gelmeli
    mehmet_kaydi = next(x for x in gun_15 if x["personel_ad"] == "MEHMET ÖZTÜRK")
    assert mehmet_kaydi["yonetici_mi"] is True

    # 16 Nisan günü (4-16) yalnızca Mehmet olmalı
    assert "4-16" in harita
    assert len(harita["4-16"]) == 1
    assert harita["4-16"][0]["personel_ad"] == "MEHMET ÖZTÜRK"

    # İstatistikler
    stats = data["istatistikler"]
    assert stats["toplam_izinli_personel"] == 2
    assert stats["toplam_izin_gunu"] == 3
    assert stats["saglik_gun_toplam"] == 2
    assert stats["mazeret_gun_toplam"] == 1


def test_meb_pdf_7_alan_cozumleme(monkeypatch):
    """MEB DYS / e-İçişleri resmi izin belgesinden 7 alanın eksiksiz parse edildiğini test eder."""
    sample_text = (
        "T.C.\n"
        "MİLLÎ EĞİTİM BAKANLIĞI\n"
        "Konu : Hastalık İzni Onayı\n"
        "Adı Soyadı : FATMA YILMAZ\n"
        "Unvanı / Branşı : Öğretmen / Matematik\n"
        "Hastalık İzin Süresi : 5 Gün\n"
        "Raporun Başlangıç Tarihi : 20.10.2026\n"
        "Göreve Başlayacağı Tarih : 25.10.2026\n"
        "İznini Geçireceği Açık Adres : Atatürk Mah. Gül Sok. No:4 Kadıköy / İSTANBUL\n"
        "Rapor Türü : Tek Hekim Raporu\n"
    )

    class MockPage:
        def extract_text(self):
            return sample_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["izin_turu"] == "SAĞLIK"
    assert res["gun_sayisi"] == 5
    assert res["baslangic"] == "2026-10-20"
    assert res["bitis"] == "2026-10-24" # 25 Ekim'de göreve başlıyorsa 24 Ekim son gündür
    assert res["izin_adresi"] == "Atatürk Mah. Gül Sok. No:4 Kadıköy / İSTANBUL"
    assert res["rapor_turu"] == "Tek Hekim Raporu"


def test_meb_pdf_mazeret_ve_adres_cozumleme(monkeypatch):
    """MEB belgesinde mazeret izni ve görev başlangıç tarihi test edilir."""
    sample_text = (
        "T.C.\n"
        "MİLLÎ EĞİTİM BAKANLIĞI\n"
        "Konu : Mazeret İzni (Evlilik)\n"
        "Adı Soyadı : ALİ KAYA\n"
        "İzin Süresi : 7 Gün\n"
        "İznin Başlangıç Tarihi : 01.06.2026\n"
        "Göreve Başlayacağı Tarih : 08.06.2026\n"
        "İznini Geçireceği Açık Adres : Alsancak Mah. Kıbrıs Şehitleri Cad. No:12 Konak / İZMİR\n"
        "Rapor Türü : Resmi Nikah Belgesi\n"
    )

    class MockPage:
        def extract_text(self):
            return sample_text

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("mazeret.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "ALİ KAYA"
    assert res["izin_turu"] == "MAZERET"
    assert res["gun_sayisi"] == 7
    assert res["baslangic"] == "2026-06-01"
    assert res["bitis"] == "2026-06-07"
    assert "Alsancak" in res["izin_adresi"]
    assert res["rapor_turu"] == "Resmi Nikah Belgesi"


def test_izin_adresi_ve_rapor_turu_crud(isolated_db):
    """İzin adresi ve rapor türünün veritabanına kaydedildiği, güncellendiği ve takvime yansıdığı doğrulanır."""
    # 1. Ekle
    resp_ekle = client.post("/saglik/ekle", json={
        "personel_ad": "MEHMET ÖZTÜRK",
        "baslangic_tarihi": "2026-09-01",
        "bitis_tarihi": "2026-09-03",
        "gun_sayisi": 3,
        "izin_turu": "SAĞLIK",
        "aciklama": "Muayene İstirahat",
        "izin_adresi": "Çankaya / ANKARA",
        "rapor_turu": "Tek Hekim Raporu"
    })
    assert resp_ekle.status_code == 200
    assert resp_ekle.json()["basarili"] is True

    # 2. Raporlar listesinde kontrol et
    resp_liste = client.get("/saglik/raporlar/MEHMET%20ÖZTÜRK?yil=2026")
    assert resp_liste.status_code == 200
    kayitlar = resp_liste.json()["veri"]
    assert len(kayitlar) == 1
    kayit = kayitlar[0]
    assert kayit["izin_adresi"] == "Çankaya / ANKARA"
    assert kayit["rapor_turu"] == "Tek Hekim Raporu"
    kayit_id = kayit["id"]

    # 3. Düzenle
    resp_duzenle = client.put(f"/saglik/duzenle/{kayit_id}", json={
        "personel_ad": "MEHMET ÖZTÜRK",
        "baslangic_tarihi": "2026-09-01",
        "bitis_tarihi": "2026-09-03",
        "gun_sayisi": 3,
        "izin_turu": "SAĞLIK",
        "aciklama": "Güncellenmiş Açıklama",
        "izin_adresi": "Yenimahalle / ANKARA",
        "rapor_turu": "Sağlık Kurulu Raporu"
    })
    assert resp_duzenle.status_code == 200
    assert resp_duzenle.json()["basarili"] is True

    # Tekrar oku ve teyit et
    resp_liste2 = client.get("/saglik/raporlar/MEHMET%20ÖZTÜRK?yil=2026")
    kayit_guncel = resp_liste2.json()["veri"][0]
    assert kayit_guncel["izin_adresi"] == "Yenimahalle / ANKARA"
    assert kayit_guncel["rapor_turu"] == "Sağlık Kurulu Raporu"

    # 4. Takvimde kontrol et
    resp_takvim = client.get("/saglik/takvim?yil=2026")
    assert resp_takvim.status_code == 200
    t_data = resp_takvim.json()["takvim_haritasi"]
    assert "9-1" in t_data
    hucre_kaydi = next(x for x in t_data["9-1"] if x["personel_ad"] == "MEHMET ÖZTÜRK")
    assert hucre_kaydi["izin_adresi"] == "Yenimahalle / ANKARA"
    assert hucre_kaydi["rapor_turu"] == "Sağlık Kurulu Raporu"


def test_meb_pdf_tablo_ve_farkli_formatlar(monkeypatch):
    """Tablo yapısında (alt satırda isim) veya SGK e-Rapor formatlarında da personelin adının başarıyla alındığını doğrular."""
    # 1. Tablo formatı: Adı Soyadı başlığı ve alt satırda personelin adı
    table_sample = (
        "T.C. MİLLÎ EĞİTİM BAKANLIĞI\n"
        "İzin Onay Formu\n"
        "Adı Soyadı\n"
        "FATMA YILMAZ\n"
        "Unvanı\n"
        "Öğretmen\n"
        "Konu : Hastalık İzni\n"
        "Hastalık İzin Süresi : 3 Gün\n"
        "Raporun Başlangıç Tarihi : 12.11.2026\n"
        "Göreve Başlayacağı Tarih : 15.11.2026\n"
    )

    class MockPageTable:
        def extract_text(self):
            return table_sample

    class MockPdfReaderTable:
        def __init__(self, stream):
            self.pages = [MockPageTable()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReaderTable)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin_tablo.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["izin_turu"] == "SAĞLIK"
    assert res["gun_sayisi"] == 3
    assert res["baslangic"] == "2026-11-12"
    assert res["bitis"] == "2026-11-14"

    # 2. SGK Geçici İş Göremezlik Belgesi: G.S : [AD SOYAD]
    sgk_sample = (
        "T.C. SOSYAL GÜVENLİK KURUMU BAŞKANLIĞI\n"
        "GEÇİCİ İŞ GÖREMEZLİK BELGESİ\n"
        "G.S : MEHMET ÖZTÜRK  TC : 11111111111\n"
        "Rapor Başlangıç : 05.12.2026\n"
        "İş Başı / Kontrol Tarihi : 08.12.2026\n"
        "Süresi : 3 Gün\n"
    )

    class MockPageSGK:
        def extract_text(self):
            return sgk_sample

    class MockPdfReaderSGK:
        def __init__(self, stream):
            self.pages = [MockPageSGK()]

    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReaderSGK)

    resp_sgk = client.post("/saglik/pdf-oku", files={"dosya": ("sgk.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp_sgk.status_code == 200
    res_sgk = resp_sgk.json()
    assert res_sgk["basarili"] is True
    assert res_sgk["ad_soyad"] == "MEHMET ÖZTÜRK"
    assert res_sgk["gun_sayisi"] == 3





def test_mudur_imzasi_ogretmen_secimini_bozmaz(monkeypatch):
    """Belgede okul müdürünün veya şube müdürünün adı geçse dahi izni alan öğretmenin seçildiğini doğrular."""
    doc_sample = (
        "T.C.\n"
        "MİLLÎ EĞİTİM BAKANLIĞI\n"
        "Konu : Hastalık İzni\n"
        "Adı Soyadı : FATMA YILMAZ\n"
        "Unvanı / Branşı : Öğretmen / Matematik\n"
        "Hastalık İzin Süresi : 4 Gün\n"
        "Raporun Başlangıç Tarihi : 01.12.2026\n"
        "Göreve Başlayacağı Tarih : 05.12.2026\n"
        "Uygun görüşle arz ederim.\n"
        "Okul Müdürü : MEHMET ÖZTÜRK\n"
        "Uygundur.\n"
        "İlçe Millî Eğitim Müdürü : AHMET DEMİR\n"
    )

    class MockPage:
        def extract_text(self):
            return doc_sample

    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage()]

    import PyPDF2
    monkeypatch.setattr(PyPDF2, "PdfReader", MockPdfReader)

    resp = client.post("/saglik/pdf-oku", files={"dosya": ("izin_mudur.pdf", b"%PDF-1.4 mock", "application/pdf")})
    assert resp.status_code == 200
    res = resp.json()
    assert res["basarili"] is True
    # İmzacı müdür Mehmet Öztürk değil, kesinlikle izni alan Fatma Yılmaz seçilmeli!
    assert res["ad_soyad"] == "FATMA YILMAZ"
    assert res["izin_turu"] == "SAĞLIK"
    assert res["gun_sayisi"] == 4


def test_personel_tablosunda_olmayan_izinli_listede_gorunur(isolated_db):
    """Personel tablosunda henüz kaydı olmayan biri için izin girildiğinde listede ve takvimde göründüğü doğrulanır."""
    resp = client.post("/saglik/ekle", json={
        "personel_ad": "ZEHRA ÇELİK",
        "baslangic_tarihi": "2026-08-10",
        "bitis_tarihi": "2026-08-14",
        "gun_sayisi": 5,
        "izin_turu": "SAĞLIK",
        "aciklama": "Yeni Atanan Öğretmen Sağlık İzni"
    })
    assert resp.status_code == 200
    assert resp.json()["basarili"] is True

    # saglik/liste endpoint'inde Zehra Çelik listelenmeli
    resp_liste = client.get("/saglik/liste?yil=2026")
    assert resp_liste.status_code == 200
    veri = resp_liste.json()["veri"]
    zehra = next((p for p in veri if p["personel_ad"] == "ZEHRA ÇELİK"), None)
    assert zehra is not None
    assert zehra["toplam"] == 5
    assert zehra["saglik_gun"] == 5
