import pytest
import sqlite3
import os
import sys
import json
from fastapi.testclient import TestClient

from api import app
from veritabani import VeritabaniYoneticisi, sifre_hashle, sifre_dogrula

client = TestClient(app)

@pytest.fixture(autouse=True)
def auth_test_ortami(monkeypatch, tmp_path):
    """Her test için izole, geçici bir test veritabanı oluşturur; gerçek kullanıcı veritabanına ASLA dokunmaz."""
    test_db = VeritabaniYoneticisi(str(tmp_path / "test_auth.db"))
    
    # Testler için örnek personeller ekle
    test_db.cursor.execute("INSERT INTO personel (ad_soyad, unvan, aktif) VALUES ('Resmi Personel', 'Müdür', 1)")
    test_db.cursor.execute("INSERT INTO personel (ad_soyad, unvan, aktif) VALUES ('Fatma Memur', 'VHKİ', 1)")
    test_db.cursor.execute("INSERT INTO personel (ad_soyad, unvan, aktif) VALUES ('İkinci Aday', 'Müdür Yrd.', 1)")
    test_db.conn.commit()

    modules_to_patch = ["dependencies", "api", "routes.auth", "routes.admin", "routes.personel"]
    for mod_name in modules_to_patch:
        if mod_name in sys.modules:
            monkeypatch.setattr(sys.modules[mod_name], "db", test_db)

    monkeypatch.setenv("TEST_BYPASS_AUTH", "0")
    yield test_db
    test_db.kapat()


def test_password_hashing_and_verification():
    """PBKDF2-HMAC-SHA256 tuzlu şifreleme ve doğrulama mekanizmasını test eder."""
    sifre = "MebGuvenli123!"
    h1, salt1 = sifre_hashle(sifre)
    h2, salt2 = sifre_hashle(sifre)

    # Tuz (Salt) dinamik ve rastgele olduğu için iki hash birbirinden farklı olmalıdır
    assert h1 != h2
    assert len(h1) == 64
    assert len(salt1) == 32

    # Doğrulama kontrolleri
    assert sifre_dogrula(sifre, h1, salt1) is True
    assert sifre_dogrula(sifre, h2, salt2) is True
    assert sifre_dogrula("YanlisSifre", h1, salt1) is False
    assert sifre_dogrula("", h1, salt1) is False


def test_ilk_kurulum_ve_kurulum_durumu():
    """İlk kurulum sihirbazını ve süper yönetici oluşturulmasını test eder."""
    # 1. Başlangıçta kurulu olmamalı
    res = client.get("/auth/kurulum-durumu")
    assert res.status_code == 200
    assert res.json()["kurulu"] is False

    # 2. İlk kurulumu gerçekleştir
    payload = {
        "ad_soyad": "Erdal ÇAM",
        "unvan": "Okul Müdürü",
        "kullanici_adi": "erdal.cam",
        "sifre": "SuperMudur2026!",
        "personel_id": None
    }
    kurulum_res = client.post("/auth/ilk-kurulum", json=payload)
    assert kurulum_res.status_code == 200
    data = kurulum_res.json()
    assert data["basarili"] is True
    assert "token" in data
    assert data["kullanici"]["kullanici_adi"] == "erdal.cam"
    assert data["kullanici"]["super_admin_mi"] is True

    # 3. Artık sistem kurulu olmalı
    res2 = client.get("/auth/kurulum-durumu")
    assert res2.status_code == 200
    assert res2.json()["kurulu"] is True

    # 4. İkinci defa ilk kurulum denenirse reddedilmeli
    tekrar_res = client.post("/auth/ilk-kurulum", json=payload)
    assert tekrar_res.status_code == 400
    assert "zaten tamamlanmış" in tekrar_res.json()["detail"]


def test_auth_giris_ve_brute_force_kilitleme():
    """Kullanıcı girişini, oturum token üretimini ve brute force korumasını test eder."""
    # İlk kurulum
    client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Test Yönetici",
        "unvan": "Müdür",
        "kullanici_adi": "yonetici",
        "sifre": "DogruSifre123"
    })

    # 5 yanlış deneme yap
    for i in range(5):
        hata_res = client.post("/auth/giris", json={
            "kullanici_adi": "yonetici",
            "sifre": f"Yanlis_{i}"
        })
        assert hata_res.status_code == 401

    # 5 yanlış denemeden sonra hesap 5 dakika kilitlenmeli (429)
    kilit_res = client.post("/auth/giris", json={
        "kullanici_adi": "yonetici",
        "sifre": "Yanlis_6"
    })
    assert kilit_res.status_code == 429
    assert "kilitlenmiştir" in kilit_res.json()["detail"]

    # Kilitliyken doğru şifre girilse bile 429 dönmeli
    dogru_ama_kilitli = client.post("/auth/giris", json={
        "kullanici_adi": "yonetici",
        "sifre": "DogruSifre123"
    })
    assert dogru_ama_kilitli.status_code == 429

    # Kilidi bellekten temizle
    from routes.auth import _hatali_giris_temizle
    _hatali_giris_temizle("yonetici")

    giris_res = client.post("/auth/giris", json={
        "kullanici_adi": "yonetici",
        "sifre": "DogruSifre123",
        "beni_hatirla": True
    })
    assert giris_res.status_code == 200
    assert "token" in giris_res.json()


def test_auth_ben_ve_sifre_degistir():
    """Aktif oturum sorgulama (/auth/ben) ve self-service şifre değiştirmeyi test eder."""
    # Kurulum yap
    kurulum = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Ahmet Yılmaz",
        "unvan": "Müdür Yrd.",
        "kullanici_adi": "ahmet.yilmaz",
        "sifre": "EskiSifre123"
    }).json()
    token = kurulum["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /auth/ben kontrolü
    ben_res = client.get("/auth/ben", headers=headers)
    assert ben_res.status_code == 200
    assert ben_res.json()["kullanici"]["kullanici_adi"] == "ahmet.yilmaz"

    # Yanlış eski şifre ile değişim denenirse 400 ile reddedilmeli
    hata_res = client.post("/auth/sifre-degistir", headers=headers, json={
        "mevcut_sifre": "YanlisEski",
        "yeni_sifre": "YeniGucluSifre456"
    })
    assert hata_res.status_code == 400
    assert "Mevcut şifreniz hatalı" in hata_res.json()["detail"]

    # Doğru eski şifre ile değişim
    basarili_res = client.post("/auth/sifre-degistir", headers=headers, json={
        "mevcut_sifre": "EskiSifre123",
        "yeni_sifre": "YeniGucluSifre456"
    })
    assert basarili_res.status_code == 200
    assert basarili_res.json()["basarili"] is True

    # Yeni şifreyle giriş yapılabilmeli
    giris_yeni = client.post("/auth/giris", json={
        "kullanici_adi": "ahmet.yilmaz",
        "sifre": "YeniGucluSifre456"
    })
    assert giris_yeni.status_code == 200


def test_admin_kullanici_ekle_ve_yetki_kisiye_ozel(auth_test_ortami):
    """Admin panelinden yeni kullanıcı oluşturma, izin atama ve yetkisiz erişim kontrolünü test eder."""
    test_db = auth_test_ortami
    # Süper yönetici kur
    super_admin = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Süper Yönetici",
        "unvan": "Müdür",
        "kullanici_adi": "super.admin",
        "sifre": "AdminSifre123"
    }).json()
    super_token = super_admin["token"]
    super_headers = {"Authorization": f"Bearer {super_token}"}

    # Fixture'da eklenen 'Fatma Memur' personel id'sini al
    test_db.cursor.execute("SELECT rowid FROM personel WHERE ad_soyad = 'Fatma Memur'")
    personel_id = test_db.cursor.fetchone()[0]

    # Yeni memur kullanıcısı oluştur
    ekle_res = client.post("/admin/kullanici-ekle", headers=super_headers, json={
        "personel_id": personel_id,
        "kullanici_adi": "fatma.vhki",
        "sifre": "Memur12345",
        "rol": "MEMUR",
        "izinler": {
            "ogrenci": False,
            "izin": True,
            "teblig": True,
            "terfi": False,
            "ihale": False,
            "admin": False
        }
    })
    assert ekle_res.status_code == 200
    assert ekle_res.json()["basarili"] is True

    # Memur kullanıcısıyla giriş yap
    memur_giris = client.post("/auth/giris", json={
        "kullanici_adi": "fatma.vhki",
        "sifre": "Memur12345"
    }).json()
    memur_token = memur_giris["token"]
    memur_headers = {"Authorization": f"Bearer {memur_token}"}

    # Memur admin paneline erişmeye çalışırsa 403 Forbidden almalı
    admin_list = client.get("/admin/kullanicilar", headers=memur_headers)
    assert admin_list.status_code == 403


def test_super_admin_dokunulmazligi_ve_devir(auth_test_ortami):
    """Süper yöneticinin silinemezliğini ve yetki devrini test eder."""
    test_db = auth_test_ortami
    # 1. Süper yönetici oluştur
    super_admin = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "İlk Süper",
        "unvan": "Okul Müdürü",
        "kullanici_adi": "ilk.super",
        "sifre": "SuperPass123"
    }).json()
    super_id = super_admin["kullanici"]["id"]
    super_headers = {"Authorization": f"Bearer {super_admin['token']}"}

    # 2. İkinci bir yönetici ekle (İkinci Aday)
    test_db.cursor.execute("SELECT rowid FROM personel WHERE ad_soyad = 'İkinci Aday'")
    p2_id = test_db.cursor.fetchone()[0]

    aday_res = client.post("/admin/kullanici-ekle", headers=super_headers, json={
        "personel_id": p2_id,
        "kullanici_adi": "ikinci.aday",
        "sifre": "Aday12345",
        "rol": "YONETICI",
        "izinler": {"admin": True}
    }).json()
    aday_id = aday_res["kullanici_id"]

    # 3. Süper yöneticiyi silmeye çalışırsak 400 ile reddedilmeli
    sil_res = client.delete(f"/admin/kullanici-sil/{super_id}", headers=super_headers)
    assert sil_res.status_code == 400
    assert "Süper Yönetici hesabı silinemez" in sil_res.json()["detail"]

    # 4. Süper yöneticiliği devret (Yanlış şifre ile 400 almalı)
    devir_hata = client.post("/admin/super-admin-devret", headers=super_headers, json={
        "hedef_kullanici_id": aday_id,
        "onay_sifresi": "YanlisSifre"
    })
    assert devir_hata.status_code == 400

    # 5. Doğru şifre ile devret
    devir_ok = client.post("/admin/super-admin-devret", headers=super_headers, json={
        "hedef_kullanici_id": aday_id,
        "onay_sifresi": "SuperPass123"
    })
    assert devir_ok.status_code == 200
    assert devir_ok.json()["basarili"] is True

    # Artık ikinci.aday süper yönetici olmalı
    test_db.cursor.execute("SELECT super_admin_mi FROM kullanicilar WHERE id = ?", (aday_id,))
    assert test_db.cursor.fetchone()[0] == 1
    test_db.cursor.execute("SELECT super_admin_mi FROM kullanicilar WHERE id = ?", (super_id,))
    assert test_db.cursor.fetchone()[0] == 0


def test_personel_silme_korumasi_kullanici_baglantisi(auth_test_ortami):
    """Kullanıcı hesabına bağlı olan bir personelin personel listesinden silinmesi engellenmelidir."""
    test_db = auth_test_ortami
    test_db.cursor.execute("SELECT rowid FROM personel WHERE ad_soyad = 'Resmi Personel'")
    pid = test_db.cursor.fetchone()[0]

    super_admin = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Resmi Personel",
        "unvan": "Müdür",
        "kullanici_adi": "resmi.mudur",
        "sifre": "Pass123456",
        "personel_id": pid
    }).json()

    # Bu personeli silmeye çalış
    sil_res = client.delete("/personel-sil/Resmi Personel")
    assert sil_res.status_code == 200
    data = sil_res.json()
    assert data["basarili"] is False
    assert "Süper Yöneticisidir" in data["mesaj"] or "kullanıcı" in data["mesaj"]


def test_tum_oturumlar_kapat_kill_switch():
    """Tüm diğer oturumları sonlandırma (kill switch) mekanizmasını test eder."""
    super_admin = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Admin Oturum",
        "unvan": "Müdür",
        "kullanici_adi": "admin.oturum",
        "sifre": "Pass123456"
    }).json()
    token1 = super_admin["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # İkinci bir oturum oluştur (farklı bir istemci gibi)
    giris2 = client.post("/auth/giris", json={
        "kullanici_adi": "admin.oturum",
        "sifre": "Pass123456"
    }).json()
    token2 = giris2["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # token2 ile /auth/ben çalışıyor mu?
    assert client.get("/auth/ben", headers=headers2).status_code == 200

    # token1 ile tüm diğer oturumları kapat
    kill_res = client.post("/admin/tum-oturumlar-kapat", headers=headers1)
    assert kill_res.status_code == 200
    assert kill_res.json()["kapatilan_oturum_sayisi"] >= 1

    # Şimdi token2 geçersiz olmalı (401)
    assert client.get("/auth/ben", headers=headers2).status_code == 401

    # token1 ise halen geçerli kalmalı (kendi oturumu korunmalı)
    assert client.get("/auth/ben", headers=headers1).status_code == 200


def test_kullanici_durum_degistir_dondur_ve_aktif_et(auth_test_ortami):
    """Kullanıcı dondurma ve tekrar aktif etme işlemlerini test eder."""
    super_admin = client.post("/auth/ilk-kurulum", json={
        "ad_soyad": "Admin Durum",
        "unvan": "Müdür",
        "kullanici_adi": "admin.durum",
        "sifre": "Admin1234!"
    }).json()
    token = super_admin["token"]
    super_id = super_admin["kullanici"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Yeni memur oluştur
    ekle_res = client.post("/admin/kullanici-ekle", json={
        "personel_id": 1,
        "kullanici_adi": "memur.durum",
        "sifre": "Memur1234!",
        "rol": "MEMUR"
    }, headers=headers).json()
    assert ekle_res["basarili"] is True
    memur_id = ekle_res["kullanici_id"]

    # Kullanıcı listesinde aktif_mi ve aktif doğrula
    k_list = client.get("/admin/kullanicilar", headers=headers).json()
    memur_obj = next(u for u in k_list["kullanicilar"] if u["id"] == memur_id)
    assert memur_obj["aktif"] is True
    assert memur_obj["aktif_mi"] is True

    # Süper yöneticiyi dondurma denemesi engellenmeli
    super_dondur = client.post("/admin/durum-degistir", json={
        "kullanici_id": super_id,
        "aktif": False
    }, headers=headers).json()
    assert super_dondur["basarili"] is False
    assert "Süper Yönetici hesabı dondurulamaz" in super_dondur["mesaj"]

    # Memur hesabını dondur (aktif_mi: False parametresiyle)
    dondur_res = client.post("/admin/durum-degistir", json={
        "kullanici_id": memur_id,
        "aktif_mi": False
    }, headers=headers).json()
    assert dondur_res["basarili"] is True

    # Memur giriş yapmaya çalışınca donduruldu uyarısı almalı (HTTP 403)
    giris_deneme = client.post("/auth/giris", json={
        "kullanici_adi": "memur.durum",
        "sifre": "Memur1234!"
    })
    assert giris_deneme.status_code == 403
    assert "dondurulmuştur" in giris_deneme.json()["detail"]

    # Memur hesabını tekrar aktif et (aktif: True ve aktif_mi: True)
    aktif_res = client.post("/admin/durum-degistir", json={
        "kullanici_id": memur_id,
        "aktif_mi": True
    }, headers=headers).json()
    assert aktif_res["basarili"] is True

    # Memur şimdi başarıyla giriş yapabilmeli
    giris_basarili = client.post("/auth/giris", json={
        "kullanici_adi": "memur.durum",
        "sifre": "Memur1234!"
    }).json()
    assert giris_basarili["basarili"] is True
    assert "token" in giris_basarili

