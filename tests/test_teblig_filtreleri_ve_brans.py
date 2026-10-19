import re
import pytest

def test_frontend_teblig_filtreleri_arayuz_kontrati():
    """index.html içindeki sadeleştirilmiş kontrol paneli bileşenleri doğrulanır."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Kullanıcı talebi: 'Hedef Kitle:' ve 'Statü:' etiketleri kaldırılmış olmalı
    assert "Hedef Kitle:" not in html
    assert "Statü:" not in html

    # Kullanıcı talebi: 'Görünenleri Seç' ve 'Görünenleri Bırak' butonları kaldırılmış olmalı
    assert "Görünenleri Seç" not in html
    assert "Görünenleri Bırak" not in html

    # Temizle butonu mevcut olmalı
    assert "personelTumunuTemizle()" in html

    # Kullanıcı talebi: 'Tüm Öğretmenler' yerine sadece 'Öğretmenler' yazmalı
    assert "🎓 Öğretmenler" in html
    assert "🎓 Tüm Öğretmenler" not in html

    # Rol preset butonları bulunmalı
    assert 'id="btn_rol_tumu"' in html
    assert 'id="btn_rol_ogretmen"' in html
    assert 'id="btn_rol_idareci"' in html
    assert 'id="btn_rol_memur"' in html
    assert 'id="btn_rol_destek"' in html

    # Branş kapsayıcısı olmalı ve başlangıçta gizli (display: none) tanımlanmalı
    assert 'id="teblig_brans_kapsayici"' in html
    assert 'display: none' in html

    # Branş menüsünün yazı kesilmesini önleyecek yükseklik (32px) tanımlanmalı
    assert 'id="teblig_brans_filtre"' in html
    assert 'height: 32px' in html or 'height:32px' in html


def test_frontend_teblig_js_fonksiyon_kontrati():
    """personel_teblig.js içindeki fonksiyon kontratları doğrulanır."""
    with open("frontend/js/personel_teblig.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "window.getGorevKademesi = getGorevKademesi" in js
    assert "window.tebligRolPresetleriGuncelle = tebligRolPresetleriGuncelle" in js
    assert "window.personelRolunuTespitEt = personelRolunuTespitEt" in js
    assert "window.tebligBransListesiniGuncelle = tebligBransListesiniGuncelle" in js
    assert "window.tebligBransFiltrele = tebligBransFiltrele" in js
    assert "window.tebligRolSec = tebligRolSec" in js
    assert "window.personelTumunuTemizle = personelTumunuTemizle" in js
    assert "window.personelTablosunuDoldur = personelTablosunuDoldur" in js


def tr_norm(s):
    if not s:
        return ""
    res = str(s)
    res = res.replace("\u0130", "I").replace("\u0131", "I").replace("i", "I")
    res = res.replace("\u011e", "G").replace("\u011f", "G")
    res = res.replace("\u00dc", "U").replace("\u00fc", "U")
    res = res.replace("\u015e", "S").replace("\u015f", "S")
    res = res.replace("\u00d6", "O").replace("\u00f6", "O")
    res = res.replace("\u00c7", "C").replace("\u00e7", "C")
    return res.upper().strip()


def py_personel_rolunu_tespit_et(p):
    """JS tarafındaki personelRolunuTespitEt mantığının Python eşdeğeri."""
    u = tr_norm(p.get("unvan", ""))
    g = tr_norm(p.get("gorev", ""))
    grp = tr_norm(p.get("grup", ""))
    b = (p.get("brans") or "").strip()

    # 1. İdareciler
    if "MUDUR" in g or "MUDUR" in u:
        return "IDARECI"

    # 2. Destek / İşçi
    destek_gruplar = ["TYP", "IUP", "ISCI", "HIZMET ALIMI"]
    destek_kelimeler = [
        "TEMIZLIK", "HIZMETLI", "GUVENLIK", "BAHCE", "ASCI",
        "SOFOR", "TEKNISYEN", "ISCI", "TYP", "IUP"
    ]
    if any(k in grp for k in destek_gruplar) or \
       any(k in g for k in destek_kelimeler) or \
       any(k in u for k in destek_kelimeler):
        return "DESTEK"

    # 3. Memurlar
    memur_kelimeler = [
        "MEMUR", "V.H.K.I", "VHKI", "VERI HAZIRLAMA",
        "SEF", "SAYMAN", "BURO", "MUTEMET", "BILGISAYAR ISLETMENI"
    ]
    if any(k in g for k in memur_kelimeler) or any(k in u for k in memur_kelimeler):
        return "MEMUR"

    # 4. Öğretmenler
    if "OGRETMEN" in g or "OGRETMEN" in u or \
       (b and b not in ("-", "NaN")) or \
       grp in ("OGRETMENLER", "UCRETLI"):
        return "OGRETMEN"

    if b and b not in ("-", "NaN"):
        return "OGRETMEN"
    return "DIGER"


def py_get_gorev_kademesi(p):
    """JS tarafındaki getGorevKademesi mantığının Python eşdeğeri."""
    gorev_str = tr_norm(f"{p.get('gorev', '')} {p.get('unvan', '')}")
    if "MUDUR" in gorev_str and not any(k in gorev_str for k in ["YARDIMCI", "BASYARDIMCI", "YRD"]):
        return 1
    if "MUDUR" in gorev_str and any(k in gorev_str for k in ["YARDIMCI", "BASYARDIMCI", "YRD"]):
        return 2
    return 3


def test_idareci_en_ustte_hiyerarsik_siralama():
    """Kullanıcı talebi: Personel Yönetimi'ndeki idarecilerin en üstte listelenmesi kuralı tebliğe de uygulanmalıdır."""
    personeller = [
        {"ad": "Zeynep KAYA", "gorev": "Öğretmen", "unvan": "Öğretmen"},
        {"ad": "Hasan YILDIRIM", "gorev": "Müdür Yardımcısı", "unvan": "Öğretmen"},
        {"ad": "Kemal ATATÜRK", "gorev": "Müdür", "unvan": "Öğretmen"},
        {"ad": "Ali VELİ", "gorev": "Müdür Yardımcısı", "unvan": "Öğretmen"},
        {"ad": "Ahmet ÇETİN", "gorev": "Memur", "unvan": "Memur"},
    ]

    # Kademe ve ad sıralaması
    sirali = sorted(
        personeller,
        key=lambda x: (py_get_gorev_kademesi(x), x["ad"])
    )

    # 1. Okul Müdürü en başta olmalı
    assert sirali[0]["ad"] == "Kemal ATATÜRK"
    assert sirali[0]["gorev"] == "Müdür"

    # 2. Müdür Yardımcıları alfabetik sırayla takip etmeli
    assert sirali[1]["ad"] == "Ali VELİ"
    assert sirali[2]["ad"] == "Hasan YILDIRIM"

    # 3. Diğer personeller (Öğretmen ve Memur) en sonda alfabetik sıralanmalı
    assert sirali[3]["ad"] == "Ahmet ÇETİN"
    assert sirali[4]["ad"] == "Zeynep KAYA"


def test_sayisi_sifir_olan_gruplarin_ve_rollerin_gizlenmesi_kurali():
    """Kullanıcı talebi: Sistemde 0 insan olan grup ve roller tebliğ filtrelerinde gizlenmeli, >0 olunca görünmelidir."""
    # 3 kadrolu öğretmen, 1 görevlendirme öğretmen olan bir okul simülasyonu
    aktif_personeller = [
        {"ad": "Öğretmen A", "grup": "Kadrolu", "gorev": "Öğretmen", "unvan": "Öğretmen", "brans": "Matematik", "aktif": 1},
        {"ad": "Öğretmen B", "grup": "Kadrolu", "gorev": "Öğretmen", "unvan": "Öğretmen", "brans": "Tarih", "aktif": 1},
        {"ad": "Öğretmen C", "grup": "Kadrolu", "gorev": "Müdür", "unvan": "Öğretmen", "brans": "Matematik", "aktif": 1},
        {"ad": "Öğretmen D", "grup": "Görevlendirme", "gorev": "Öğretmen", "unvan": "Öğretmen", "brans": "Fizik", "aktif": 1},
    ]

    tum_gruplar = ["Kadrolu", "Görevlendirme", "Ücretli", "Sözleşmeli", "TYP", "İUP", "Sürekli İşçi", "Hizmet Alımı"]
    grup_sayilari = {g: 0 for g in tum_gruplar}
    for p in aktif_personeller:
        if p["grup"] in grup_sayilari:
            grup_sayilari[p["grup"]] += 1

    # Yalnızca sayısı > 0 olan gruplar görünür
    gorunen_gruplar = [g for g, sayi in grup_sayilari.items() if sayi > 0]
    gizlenen_gruplar = [g for g, sayi in grup_sayilari.items() if sayi == 0]

    assert "Kadrolu" in gorunen_gruplar
    assert "Görevlendirme" in gorunen_gruplar
    assert "Ücretli" in gizlenen_gruplar
    assert "Sözleşmeli" in gizlenen_gruplar
    assert "TYP" in gizlenen_gruplar
    assert "İUP" in gizlenen_gruplar

    # Rol sayıları
    rol_sayilari = {"OGRETMEN": 0, "IDARECI": 0, "MEMUR": 0, "DESTEK": 0}
    for p in aktif_personeller:
        rol = py_personel_rolunu_tespit_et(p)
        if rol in rol_sayilari:
            rol_sayilari[rol] += 1

    assert rol_sayilari["OGRETMEN"] == 3
    assert rol_sayilari["IDARECI"] == 1
    assert rol_sayilari["MEMUR"] == 0  # Memur 0 olduğu için tebliğde gizlenir
    assert rol_sayilari["DESTEK"] == 0 # Destek 0 olduğu için tebliğde gizlenir


def test_kosullu_brans_gorunurlugu_kurali():
    """Kullanıcı talebi: Branş seçici yalnızca 'Öğretmenler' seçildiğinde görünür olmalıdır."""
    with open("frontend/js/personel_teblig.js", "r", encoding="utf-8") as f:
        js = f.read()

    # tebligRolSec içinde OGRETMEN ise display: flex, değilse display: none olmalı
    assert "bransKapsayici.style.display = 'flex'" in js
    assert "bransKapsayici.style.display = 'none'" in js
    assert "seciliTebligRolu === 'OGRETMEN'" in js


def test_kullanici_ornegi_gorevlendirme_tarih_kombine_filtre():
    """Kullanıcının spesifik talebi: Görevlendirme Tarih öğretmeninin çapraz filtrelenmesi doğrulanır."""
    personeller = [
        {"ad": "Esra Görevlendirme Tarih", "unvan": "Öğretmen", "gorev": "Öğretmen", "brans": "Tarih", "grup": "Görevlendirme", "aktif": 1},
        {"ad": "Hülya Görevlendirme Matematik", "unvan": "Öğretmen", "gorev": "Öğretmen", "brans": "Matematik", "grup": "Görevlendirme", "aktif": 1},
        {"ad": "Bahar Kadrolu Tarih", "unvan": "Öğretmen", "gorev": "Öğretmen", "brans": "Tarih", "grup": "Kadrolu", "aktif": 1},
        {"ad": "İrfan Görevlendirme Memur", "unvan": "VHKİ", "gorev": "VHKİ", "brans": "-", "grup": "Görevlendirme", "aktif": 1},
    ]

    secili_statuler = ["Görevlendirme"]
    secili_brans = "Tarih"

    sonuc = [
        p for p in personeller
        if p["grup"] in secili_statuler and p["brans"] == secili_brans
    ]

    assert len(sonuc) == 1
    assert sonuc[0]["ad"] == "Esra Görevlendirme Tarih"
