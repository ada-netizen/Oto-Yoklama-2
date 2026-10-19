import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api
from mevzuat_kurallari import hesapla_personel_terfi_durumu

app = api.app
client = TestClient(app)

def test_hesapla_personel_terfi_kademe_ilerlemesi_md64():
    """657 SK Madde 64: Bulunduğu kademede 1 yılını dolduran personelin kademe ilerlemesi."""
    # 9/1 -> 9/2
    p1 = {
        "ad_soyad": "Ahmet YILMAZ",
        "grup": "Kadrolu",
        "kademe_derece": "9/1",
        "goreve_baslama": "15.09.2023"
    }
    res1 = hesapla_personel_terfi_durumu(p1, hedef_yil=2026)
    assert res1["kapsam_ici"] is True
    assert res1["terfi_turu"] == "KADEME"
    assert res1["yeni_kademe_derece"] == "9/2"
    assert "Madde 64" in res1["mevzuat_maddesi"]
    assert res1["terfi_tarihi"] == "15.09.2026"
    assert res1["ay_no"] == 9
    assert res1["gun_no"] == 15

    # 3/2 -> 3/3
    p2 = {
        "ad_soyad": "Mehmet KAYA",
        "grup": "Kadrolu",
        "kademe_derece": "3/2",
        "goreve_baslama": "01/03/2015"
    }
    res2 = hesapla_personel_terfi_durumu(p2, hedef_yil=2026)
    assert res2["kapsam_ici"] is True
    assert res2["terfi_turu"] == "KADEME"
    assert res2["yeni_kademe_derece"] == "3/3"
    assert "Madde 64" in res2["mevzuat_maddesi"]
    assert res2["terfi_tarihi"] == "01.03.2026"


def test_hesapla_personel_terfi_derece_yukselmesi_md68():
    """657 SK Madde 68: Bulunduğu derecede 3 yılı dolduran personelin derece yükselmesi."""
    # 9/3 -> 8/1
    p1 = {
        "ad_soyad": "Ayşe DEMİR",
        "grup": "Kadrolu",
        "kademe_derece": "9/3",
        "goreve_baslama": "20.10.2020"
    }
    res1 = hesapla_personel_terfi_durumu(p1, hedef_yil=2026)
    assert res1["kapsam_ici"] is True
    assert res1["terfi_turu"] == "DERECE"
    assert res1["yeni_kademe_derece"] == "8/1"
    assert "Madde 68" in res1["mevzuat_maddesi"]
    assert res1["terfi_tarihi"] == "20.10.2026"

    # 3/3 -> 2/1
    p2 = {
        "ad_soyad": "Fatma ŞAHİN",
        "grup": "Kadrolu",
        "kademe_derece": "3/3",
        "goreve_baslama": "2018-05-12"
    }
    res2 = hesapla_personel_terfi_durumu(p2, hedef_yil=2026)
    assert res2["kapsam_ici"] is True
    assert res2["terfi_turu"] == "DERECE"
    assert res2["yeni_kademe_derece"] == "2/1"
    assert "Madde 68" in res2["mevzuat_maddesi"]
    assert res2["terfi_tarihi"] == "12.05.2026"


def test_hesapla_personel_terfi_tavan_barem_1_4():
    """657 SK Madde 36: 1/4 tavan baremine ulaşmış memurlar."""
    p = {
        "ad_soyad": "Ali Rıza BEY",
        "grup": "Kadrolu",
        "kademe_derece": "1/4",
        "goreve_baslama": "10.09.1995"
    }
    res = hesapla_personel_terfi_durumu(p, hedef_yil=2026)
    assert res["kapsam_ici"] is True
    assert res["tavan_mi"] is True
    assert res["terfi_turu"] == "TAVAN"
    assert res["yeni_kademe_derece"] == "1/4"
    assert "Madde 36" in res["mevzuat_maddesi"]


def test_hesapla_personel_terfi_kapsam_disi_statuler():
    """Sözleşmeli, İUP, TYP, Ücretli ve Görevlendirme personelleri terfi listesine dahil edilmez."""
    statuler = ["Sözleşmeli", "İUP", "TYP", "Ücretli", "Görevlendirme", "Sürekli İşçi"]
    for st in statuler:
        p = {
            "ad_soyad": f"Personel {st}",
            "grup": st,
            "kademe_derece": "9/1",
            "goreve_baslama": "15.09.2022"
        }
        res = hesapla_personel_terfi_durumu(p, hedef_yil=2026)
        assert res["kapsam_ici"] is False, f"{st} kapsam dışı olmalıdır"
        assert "terfi_turu" in res and res["terfi_turu"] == "KAPSAM_DISI"


def test_hesapla_personel_terfi_eksik_tarih():
    """İlk göreve başlama ve kurumda başlama tarihi boş olan personel eksik tarih olarak işaretlenir."""
    p = {
        "ad_soyad": "Tarihsiz Personel",
        "grup": "Kadrolu",
        "kademe_derece": "4/1",
        "goreve_baslama": "",
        "kurumda_baslama": ""
    }
    res = hesapla_personel_terfi_durumu(p, hedef_yil=2026)
    assert res["kapsam_ici"] is True
    assert res["tarih_eksik"] is True
    assert res["terfi_tarihi"] == "-"


def test_api_personel_terfileri_endpoint():
    """GET /personel-terfileri uç noktası doğru JSON ve takvim haritası döndürür."""
    resp = client.get("/personel-terfileri?yil=2026")
    assert resp.status_code == 200
    veri = resp.json()
    assert veri["basarili"] is True
    assert veri["yil"] == 2026
    assert "istatistikler" in veri
    assert "personeller" in veri
    assert "takvim_haritasi" in veri
    assert "toplam_kadrolu" in veri["istatistikler"]
    assert "derece_sayisi" in veri["istatistikler"]
    assert "kademe_sayisi" in veri["istatistikler"]
    assert "tarih_eksik_sayisi" in veri["istatistikler"]


def test_terfi_tavan_personel_takvimde_gosterilmez():
    """Kullanıcı kuralı: 1/4 tavan derece/kademeye gelmiş memurlar takvimde T rozeti olarak gösterilmez."""
    resp = client.get("/personel-terfileri?yil=2026")
    assert resp.status_code == 200
    veri = resp.json()
    takvim = veri.get("takvim_haritasi", {})
    # Takvim haritasındaki hiçbir hücrede tavan_mi == True veya terfi_turu == "TAVAN" olmamalı
    for key, liste in takvim.items():
        for p in liste:
            assert p.get("terfi_turu") != "TAVAN", f"Tavan personel takvimde yer alamaz: {p}"
            assert p.get("tavan_mi") is not True


def test_baska_kuruma_gorevlendirilen_kadrolu_personel_terfisi_takip_edilir():
    """
    Kullanıcı kuralı: Kadrosu okulumuzda olan (Kadrolu) ancak başka kuruma görevlendirilen (aktif=0)
    personelin özlük hakları ve terfisi bizim tarafımızdan takip edilir.
    """
    # Test için geçici bir kadrolu ama başka kuruma görevli personel ekleyelim
    client.post("/personel-ekle", json={
        "ad": "GÖREVLİ KADROLU ÖĞRETMEN",
        "unvan": "Öğretmen",
        "brans": "Fizik",
        "gorev": "Öğretmen"
    })
    client.post("/personel-profil-guncelle", json={
        "ad_soyad": "GÖREVLİ KADROLU ÖĞRETMEN",
        "tc_no": "99988877766",
        "unvan": "Öğretmen",
        "brans": "Fizik",
        "gorev": "Öğretmen",
        "grup": "Kadrolu",
        "kademe_derece": "4/2",
        "goreve_baslama": "10.04.2019",
        "aktif": 0  # Başka Kuruma Görevlendirildi
    })

    resp = client.get("/personel-terfileri?yil=2026")
    assert resp.status_code == 200
    personeller = resp.json().get("personeller", [])
    bulunan = next((p for p in personeller if p["ad_soyad"] == "GÖREVLİ KADROLU ÖĞRETMEN"), None)
    
    assert bulunan is not None, "Başka kuruma görevlendirilen kadrolu öğretmen terfi listesinde yer almalıdır"
    assert bulunan["baska_kurumda"] is True
    assert bulunan["yeni_kademe_derece"] == "4/3"

    # Temizlik
    client.delete("/personel-sil/GÖREVLİ KADROLU ÖĞRETMEN")


def test_frontend_terfi_bilesenleri_ve_scriptler():
    """Frontend dosyalarında Personel Terfi sekmesi, HTML ve JS bileşenlerinin kontrat testi."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. sidebar_rail.html içinde sekme butonu
    sidebar_path = os.path.join(base_dir, "frontend", "components", "sidebar_rail.html")
    with open(sidebar_path, "r", encoding="utf-8") as f:
        sb = f.read()
    assert "sekme_terfi" in sb
    assert "Personel Terfi" in sb

    # 2. sekme_terfi.html bileşeni
    terfi_html_path = os.path.join(base_dir, "frontend", "components", "sekme_terfi.html")
    assert os.path.exists(terfi_html_path)
    with open(terfi_html_path, "r", encoding="utf-8") as f:
        th = f.read()
    assert 'id="sekme_terfi"' in th
    assert 'id="terfi_thead"' in th
    assert 'id="terfi_tbody"' in th
    assert 'id="modal_terfi_bilgi"' in th
    assert 'chk_terfi_uyari_bir_daha_gosterme' in th
    assert 'btn_terfi_filtre_tavan' in th
    assert "Bu Ay" in th

    # 3. index.html include ve script kontrolleri
    index_path = os.path.join(base_dir, "frontend", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        idx = f.read()
    assert "components/sekme_terfi.html" in idx
    assert "js/personel_terfi.js" in idx

    # 4. personel_terfi.js dosyası
    terfi_js_path = os.path.join(base_dir, "frontend", "js", "personel_terfi.js")
    assert os.path.exists(terfi_js_path)
    with open(terfi_js_path, "r", encoding="utf-8") as f:
        tj = f.read()
    assert "terfiYukle" in tj
    assert "terfiTakviminiCiz" in tj
    assert "terfiAcilisUyarisiKontrol" in tj
    assert "terfiBilgiModalOnayla" in tj
    assert 'seciliTerfiFiltresi !== "TAVAN" && isTavan' in tj
    assert 'hasKademe && hasDerece' in tj
    assert "bu-ay-satiri" in tj
    assert "bu-ay-baslik" in tj
    assert "bu-ay-kapsayici" in tj

    # 5. style.css içinde terfi sınıfları
    css_path = os.path.join(base_dir, "frontend", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    assert ".terfi-matris-tablo" in css
    assert ".terfi-hucre-rozet" in css
    assert ".terfi-hucre-rozet.karisik" in css
    assert "linear-gradient" in css
    assert "bu-ay-satiri" in css
    assert "bu-ay-baslik" in css
    assert "bu-ay-rozet" in css
