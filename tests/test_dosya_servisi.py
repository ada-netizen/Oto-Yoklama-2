import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tempfile
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api import app
from dependencies import yollar, is_yerel_istek
from utils import dosyayi_otomatik_ac
from veritabani import VeritabaniYoneticisi

client = TestClient(app)

@pytest.fixture
def auth_test_ortami(monkeypatch, tmp_path):
    """Her test için izole, geçici bir test veritabanı oluşturur."""
    test_db = VeritabaniYoneticisi(str(tmp_path / "test_dosya.db"))
    test_db.cursor.execute("INSERT INTO personel (ad_soyad, unvan, aktif) VALUES ('Resmi Personel', 'Müdür', 1)")
    test_db.conn.commit()

    modules_to_patch = ["dependencies", "api", "routes.auth", "routes.admin", "routes.sistem", "routes.pdf"]
    for mod_name in modules_to_patch:
        if mod_name in sys.modules:
            monkeypatch.setattr(sys.modules[mod_name], "db", test_db)

    monkeypatch.setenv("TEST_BYPASS_AUTH", "0")
    yield test_db


@pytest.fixture
def auth_token_ve_dosya(auth_test_ortami, tmp_path):
    """Geçerli bir oturum token'ı ve test amaçlı güvenli PDF dosyası hazırlar."""
    # Test kullanıcısı oluştur
    res = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Dosya Test Yöneticisi",
        "unvan": "Müdür",
        "kullanici_adi": "dosya.admin",
        "sifre": "Admin1234!"
    }).json()
    token = res["token"]

    # Güvenli dizin altında test dosyası oluştur
    pdf_klasoru = yollar.get("PDF") or str(tmp_path)
    os.makedirs(pdf_klasoru, exist_ok=True)
    test_pdf = os.path.join(pdf_klasoru, "test_guvenli_belge.pdf")
    with open(test_pdf, "wb") as f:
        f.write(b"%PDF-1.4 test pdf content")

    test_xlsx = os.path.join(pdf_klasoru, "test_tablo.xlsx")
    with open(test_xlsx, "wb") as f:
        f.write(b"PK test excel content")

    return token, test_pdf, test_xlsx


def test_dosya_indir_yetkisiz_erisim_engeli(auth_token_ve_dosya):
    """Oturum token'ı olmadan dosya indirme/görüntüleme isteğinin 401 ile reddedildiğini doğrular."""
    _, test_pdf, _ = auth_token_ve_dosya
    client.cookies.clear()
    res = client.get(f"/dosya/indir?yol={test_pdf}")
    assert res.status_code == 401


def test_dosya_indir_guvenli_pdf_goruntuleme(auth_token_ve_dosya):
    """Geçerli token ile PDF'in inline (tarayıcıda açılır) başlığıyla geldiğini doğrular."""
    token, test_pdf, _ = auth_token_ve_dosya
    
    # 1. Header ile yetkilendirme
    res1 = client.get(f"/dosya/indir?yol={test_pdf}", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    assert res1.headers["content-type"] == "application/pdf"
    assert "inline" in res1.headers.get("content-disposition", "")
    assert res1.content == b"%PDF-1.4 test pdf content"

    # 2. Query parametresi token ile yetkilendirme (window.open uyumluluğu)
    res2 = client.get(f"/dosya/indir?yol={test_pdf}&token={token}")
    assert res2.status_code == 200
    assert res2.headers["content-type"] == "application/pdf"
    assert "inline" in res2.headers.get("content-disposition", "")


def test_dosya_indir_excel_attachment_indirme(auth_token_ve_dosya):
    """Excel dosyalarının veya indir=1 parametresinin attachment (indirme) olarak geldiğini doğrular."""
    token, test_pdf, test_xlsx = auth_token_ve_dosya

    # PDF + indir=1 -> attachment olmalı
    res_pdf_indir = client.get(f"/dosya/indir?yol={test_pdf}&indir=1&token={token}")
    assert res_pdf_indir.status_code == 200
    assert "attachment" in res_pdf_indir.headers.get("content-disposition", "")

    # Excel dosyası -> otomatik attachment olmalı
    res_xlsx = client.get(f"/dosya/indir?yol={test_xlsx}&token={token}")
    assert res_xlsx.status_code == 200
    assert "attachment" in res_xlsx.headers.get("content-disposition", "")


def test_dosya_indir_path_traversal_ve_gecersiz_dosya(auth_token_ve_dosya):
    """Yetkisiz dizinlere (Path traversal) veya olmayan dosyalara erişimin engellendiğini doğrular."""
    token, _, _ = auth_token_ve_dosya

    # Olmayan dosya
    res1 = client.get(f"/dosya/indir?yol=C:\\olmayan_dosya.pdf&token={token}")
    assert res1.status_code == 404

    # Sistem dizinine sızma denemesi (örn: Windows veya System32)
    sistem_dosyasi = "C:\\Windows\\system.ini"
    res2 = client.get(f"/dosya/indir?yol={sistem_dosyasi}&token={token}")
    assert res2.status_code == 404


def test_is_yerel_istek_ve_dosyayi_otomatik_ac_filtresi(monkeypatch):
    """Uzak ağ istemcisi (192.168.x.x) istek attığında ana bilgisayarda os.startfile çağrılmadığını doğrular."""
    yerel_req = MagicMock()
    yerel_req.client.host = "127.0.0.1"

    uzak_req = MagicMock()
    uzak_req.client.host = "192.168.7.45"

    assert is_yerel_istek(yerel_req) is True
    assert is_yerel_istek(uzak_req) is False
    assert is_yerel_istek(None) is True

    # os.startfile çağrısını izlemek için mockla
    startfile_cagirildi = []
    monkeypatch.setattr(os, "startfile", lambda yol: startfile_cagirildi.append(yol), raising=False)

    # 1. Uzak istemci için çağırma -> startfile çağrılmamalı!
    dosyayi_otomatik_ac("test_dosya.pdf", request=uzak_req)
    assert len(startfile_cagirildi) == 0

    # 2. Yerel istemci için çağırma -> startfile çağrılmalı!
    dosyayi_otomatik_ac("test_dosya.pdf", request=yerel_req)
    assert len(startfile_cagirildi) == 1
    assert "test_dosya.pdf" in startfile_cagirildi[0]

def test_dosya_indir_cookie_ile_yetkilendirme(auth_token_ve_dosya):
    """Tarayıcı sekmesinde açılan dosyalarda cookie (session_token) ile otomatik yetkilendirme doğrulanır."""
    token, test_pdf, _ = auth_token_ve_dosya
    res = client.get(f"/dosya/indir?yol={test_pdf}", cookies={"session_token": token})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content == b"%PDF-1.4 test pdf content"


def test_dosya_indir_oturum_token_query_ile_yetkilendirme(auth_token_ve_dosya):
    """URL parametresi ?oturum_token=... veya ?token=... ile dosya indirme/görüntüleme doğrulanır."""
    token, test_pdf, _ = auth_token_ve_dosya
    res = client.get(f"/dosya/indir?yol={test_pdf}&oturum_token={token}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_frontend_dosyaindirurl_oturum_token_uyumu():
    """Frontend tarafında dosyaIndirUrl'in oturum_token değerini okuduğu ve tokenAl ile uyumlu olduğu doğrulanır."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    core_path = os.path.join(base_dir, "frontend", "js", "core.js")
    with open(core_path, "r", encoding="utf-8") as f:
        core_js = f.read()

    assert "oturum_token" in core_js, "core.js içindeki dosyaIndirUrl oturum_token değerini okumalıdır"

    auth_path = os.path.join(base_dir, "frontend", "js", "auth.js")
    with open(auth_path, "r", encoding="utf-8") as f:
        auth_js = f.read()

    assert "window.tokenAl = tokenAl" in auth_js, "auth.js tokenAl fonksiyonunu dışa açmalıdır"
    assert "session_token=" in auth_js, "auth.js giriş ve kurulum esnasında session_token çerezini ayarlamalıdır"
