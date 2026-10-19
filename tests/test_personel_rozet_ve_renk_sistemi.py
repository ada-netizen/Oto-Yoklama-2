import os
import re
import pytest

def test_personel_grup_rozetleri_tanimlari():
    """Tüm 8 istihdam grubu için merkezi rozet sözlüğü ve benzersiz renkler doğrulanır."""
    with open("frontend/js/personel_teblig.js", "r", encoding="utf-8") as f:
        js_code = f.read()

    # PERSONEL_GRUP_ROZETLERI sözlüğü olmalı
    assert "window.PERSONEL_GRUP_ROZETLERI" in js_code
    assert "window.getPersonelGrupBadgeHtml" in js_code

    beklenen_gruplar = [
        "Kadrolu", "Sözleşmeli", "Ücretli", "Görevlendirme",
        "İUP", "TYP", "Sürekli İşçi", "Hizmet Alımı"
    ]
    for grup in beklenen_gruplar:
        assert f"'{grup}':" in js_code or f'"{grup}":' in js_code

    # İUP ve TYP renkleri kesinlikle birbirinden farklı olmalıdır
    m_iup = re.search(r"'İUP':\s*\{[^}]*renk:\s*'([^']+)'", js_code)
    m_typ = re.search(r"'TYP':\s*\{[^}]*renk:\s*'([^']+)'", js_code)
    assert m_iup is not None
    assert m_typ is not None
    assert m_iup.group(1) != m_typ.group(1), "İUP ve TYP aynı renkte olamaz!"
    assert m_iup.group(1) == "#059669"  # Zümrüt
    assert m_typ.group(1) == "#ea580c"  # Kiremit


def test_personel_durum_badge_sakin_aktif():
    """Aktif personeller için sakin gösterge (alert-on-exception) doğrulanır."""
    with open("frontend/js/personel_teblig.js", "r", encoding="utf-8") as f:
        js_code = f.read()

    assert "window.getPersonelDurumBadgeHtml" in js_code
    assert "d.fiilenGorevde" in js_code
    # Minimalist nokta veya sakin yeşil badge kontrolü
    assert "#16a34a" in js_code or "#15803d" in js_code


def test_personel_yonetim_tablo_sutunlari_ve_notr_buton():
    """Personel Yönetimi tablosunda grup rozeti fonksiyonu ve nötr işlem butonu doğrulanır."""
    with open("frontend/components/personel_yonetim_modal.html", "r", encoding="utf-8") as f:
        modal_html = f.read()

    # 3. Sütun getGrupBadgeHtml çağrısı içermeli
    assert "getGrupBadgeHtml(p.grup)" in modal_html

    # İşlemler butonunda gereksiz mavi rozet boyaması yerine nötr buton stili olmalı
    assert "btn-icon-soft" in modal_html
    assert "var(--bg-card)" in modal_html
    assert "var(--border)" in modal_html

    # Alpine bileşeninde getGrupBadgeHtml metodu tanımlı olmalı
    assert "getGrupBadgeHtml(grup)" in modal_html


def test_gorevlendirme_mevzuat_maddesi_profil_modalinda_yer_alir():
    """Kullanıcının özel isteği: Görevlendirme seçeneğinde (Pasif yerine) 657 SK Ek Md. 8 yer almalıdır."""
    with open("frontend/components/personel_profil_modal.html", "r", encoding="utf-8") as f:
        profil_html = f.read()

    assert "Başka Kuruma Görevlendirildi (657 SK Ek Md. 8)" in profil_html
    assert "value=\"0\"" in profil_html

