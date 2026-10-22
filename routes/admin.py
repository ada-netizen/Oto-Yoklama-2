import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, Depends

from dependencies import db, get_aktif_kullanici, yetki_gerekli, denetim_kaydi_ekle, yerel_ip_al
from veritabani import sifre_hashle, sifre_dogrula

router = APIRouter()

class KullaniciEkleRequest(BaseModel):
    personel_id: int
    kullanici_adi: str
    sifre: str
    rol: Optional[str] = "MEMUR"
    izinler: Optional[Dict[str, bool]] = None

class YetkiGuncelleRequest(BaseModel):
    kullanici_id: int
    rol: Optional[str] = None
    izinler: Dict[str, bool]

class SifreSifirlaRequest(BaseModel):
    kullanici_id: int
    yeni_sifre: str

class DurumDegistirRequest(BaseModel):
    kullanici_id: int
    aktif: Optional[bool] = None
    aktif_mi: Optional[bool] = None

class SuperAdminDevretRequest(BaseModel):
    yeni_super_admin_id: Optional[int] = None
    hedef_kullanici_id: Optional[int] = None
    onay_sifresi: str

class PersonelEslestirRequest(BaseModel):
    kullanici_id: int
    hedef_personel_id: int
    eski_taslak_silinsin_mi: Optional[bool] = True
    taslak_sil: Optional[bool] = None

def _cevrimici_durum_hesapla(son_islem_str: Optional[str]) -> tuple[bool, str]:
    if not son_islem_str:
        return False, "Henüz giriş yapmadı"
    try:
        son_islem = datetime.strptime(son_islem_str, "%Y-%m-%d %H:%M:%S")
        fark = datetime.now() - son_islem
        fark_dakika = int(fark.total_seconds() / 60)

        if fark_dakika < 4:
            return True, "Çevrimiçi"
        elif fark_dakika < 60:
            return False, f"{fark_dakika} dk önce"
        elif fark_dakika < 1440:
            saat = fark_dakika // 60
            return False, f"{saat} saat önce"
        else:
            return False, son_islem.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return False, son_islem_str

@router.get("/admin/kullanicilar")
def kullanicilari_listele(aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Tüm kullanıcıları canlı durumları ve yetkileriyle listeler."""
    try:
        db.cursor.execute("""
            SELECT id, personel_id, kullanici_adi, ad_soyad, unvan, rol, 
                   izinler, super_admin_mi, aktif, son_giris, son_islem
            FROM kullanicilar
            ORDER BY super_admin_mi DESC, id ASC
        """)
        rows = db.cursor.fetchall()
        kullanicilar = []

        for r in rows:
            k_id, p_id, k_adi, ad, unv, rol, izn_str, super_mi, aktif, s_giris, s_islem = r
            cevrimici, durum_metni = _cevrimici_durum_hesapla(s_islem)
            izinler = {}
            if izn_str:
                try:
                    izinler = json.loads(izn_str)
                except Exception:
                    pass

            kullanicilar.append({
                "id": k_id,
                "personel_id": p_id,
                "kullanici_adi": k_adi,
                "ad_soyad": ad,
                "unvan": unv,
                "rol": rol,
                "izinler": izinler,
                "super_admin_mi": bool(super_mi),
                "aktif": bool(aktif),
                "aktif_mi": bool(aktif),
                "son_giris": s_giris or "-",
                "son_islem": s_islem or "-",
                "son_gorulme": s_islem or s_giris or "-",
                "cevrimici": cevrimici,
                "cevrimici_mi": cevrimici,
                "durum_metni": durum_metni
            })

        return {"basarili": True, "kullanicilar": kullanicilar}
    except Exception as e:
        logging.error(f"Kullanıcı listesi alma hatası: {e}", exc_info=True)
        return {"basarili": False, "mesaj": str(e), "kullanicilar": []}

@router.post("/admin/kullanici-ekle")
def kullanici_ekle(veri: KullaniciEkleRequest, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Okul personeli listesinden seçilen bir personele kullanıcı hesabı açar."""
    try:
        k_adi = veri.kullanici_adi.strip().lower()
        sifre = veri.sifre.strip()

        if len(k_adi) < 3 or len(sifre) < 4:
            return {"basarili": False, "mesaj": "Kullanıcı adı en az 3, şifre en az 4 karakter olmalıdır."}

        # Kullanıcı adı çakışma kontrolü
        db.cursor.execute("SELECT id FROM kullanicilar WHERE LOWER(kullanici_adi) = ?", (k_adi,))
        if db.cursor.fetchone():
            return {"basarili": False, "mesaj": f"'{k_adi}' kullanıcı adı zaten kullanımda."}

        # Personel tablosundan bilgileri çek
        db.cursor.execute("SELECT ad_soyad, COALESCE(unvan, ''), COALESCE(gorev, '') FROM personel WHERE rowid = ?", (veri.personel_id,))
        p_row = db.cursor.fetchone()
        if not p_row:
            return {"basarili": False, "mesaj": "Seçilen personel okul personel listesinde bulunamadı."}

        ad_soyad = p_row[0]
        unvan = p_row[1] or p_row[2] or "Personel"

        # Bu personele zaten hesap açılmış mı?
        db.cursor.execute("SELECT id FROM kullanicilar WHERE personel_id = ?", (veri.personel_id,))
        if db.cursor.fetchone():
            return {"basarili": False, "mesaj": f"'{ad_soyad}' adına zaten tanımlı bir kullanıcı hesabı mevcuttur."}

        s_hash, salt = sifre_hashle(sifre)
        varsayilan_izinler = veri.izinler or {
            "ogrenci": False,
            "izin": True,
            "teblig": True,
            "terfi": False,
            "ihale": False,
            "admin": False
        }
        izinler_str = json.dumps(varsayilan_izinler)

        db.cursor.execute("""
            INSERT INTO kullanicilar 
            (personel_id, kullanici_adi, sifre_hash, salt, ad_soyad, unvan, rol, izinler, super_admin_mi, aktif)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
        """, (veri.personel_id, k_adi, s_hash, salt, ad_soyad, unvan, veri.rol or "MEMUR", izinler_str))
        db.conn.commit()
        yeni_id = db.cursor.lastrowid

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            "Kullanıcı Eklendi",
            f"'{ad_soyad}' personeli için '{k_adi}' kullanıcı hesabı oluşturuldu.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "kullanici_id": yeni_id, "mesaj": f"'{ad_soyad}' için kullanıcı hesabı başarıyla oluşturuldu."}
    except Exception as e:
        logging.error(f"Kullanıcı ekleme hatası: {e}", exc_info=True)
        return {"basarili": False, "mesaj": f"Kullanıcı ekleme hatası: {str(e)}"}

@router.post("/admin/yetki-guncelle")
def yetki_guncelle(veri: YetkiGuncelleRequest, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Kullanıcının modül bazlı yetkilerini günceller."""
    try:
        db.cursor.execute("SELECT id, kullanici_adi, ad_soyad, super_admin_mi FROM kullanicilar WHERE id = ?", (veri.kullanici_id,))
        hedef = db.cursor.fetchone()
        if not hedef:
            return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

        h_id, h_kadi, h_ad, h_super = hedef

        # Root Dokunulmazlığı
        if h_super and not aktif_kullanici.get("super_admin_mi"):
            return {"basarili": False, "mesaj": "Süper Yöneticinin yetkilerini yalnızca Süper Yönetici düzenleyebilir."}

        izinler_str = json.dumps(veri.izinler)
        if veri.rol:
            db.cursor.execute("UPDATE kullanicilar SET izinler = ?, rol = ? WHERE id = ?", (izinler_str, veri.rol, veri.kullanici_id))
        else:
            db.cursor.execute("UPDATE kullanicilar SET izinler = ? WHERE id = ?", (izinler_str, veri.kullanici_id))
        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            "Yetki Güncellendi",
            f"'{h_ad}' kullanıcısının modül yetkileri güncellendi.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"'{h_ad}' yetkileri başarıyla güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/admin/sifre-sifirla")
def sifre_sifirla(veri: SifreSifirlaRequest, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Yöneticinin bir kullanıcının şifresini sıfırlamasını sağlar."""
    try:
        yeni = veri.yeni_sifre.strip()
        if len(yeni) < 4:
            return {"basarili": False, "mesaj": "Yeni şifre en az 4 karakter olmalıdır."}

        db.cursor.execute("SELECT id, kullanici_adi, ad_soyad, super_admin_mi FROM kullanicilar WHERE id = ?", (veri.kullanici_id,))
        row = db.cursor.fetchone()
        if not row:
            return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

        h_id, h_kadi, h_ad, h_super = row

        # Root Dokunulmazlığı: Başkası Süper Yöneticinin şifresini sıfırlayamaz!
        if h_super and aktif_kullanici["id"] != h_id:
            return {"basarili": False, "mesaj": "Süper Yöneticinin şifresi başka bir kullanıcı tarafından sıfırlanamaz!"}

        yeni_hash, salt = sifre_hashle(yeni)
        db.cursor.execute("UPDATE kullanicilar SET sifre_hash = ?, salt = ? WHERE id = ?", (yeni_hash, salt, veri.kullanici_id))
        
        # Kullanıcının mevcut oturumlarını da düşür ki yeni şifreyle girmesi zorunlu olsun
        db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE kullanici_id = ?", (veri.kullanici_id,))
        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            "Şifre Sıfırlandı",
            f"'{h_ad}' kullanıcısının şifresi yönetici tarafından sıfırlandı.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"'{h_ad}' kullanıcısının şifresi başarıyla güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/admin/durum-degistir")
def durum_degistir(veri: DurumDegistirRequest, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Kullanıcı hesabını dondurur veya yeniden aktifleştirir."""
    try:
        db.cursor.execute("SELECT id, kullanici_adi, ad_soyad, super_admin_mi FROM kullanicilar WHERE id = ?", (veri.kullanici_id,))
        row = db.cursor.fetchone()
        if not row:
            return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

        h_id, h_kadi, h_ad, h_super = row

        if h_super:
            return {"basarili": False, "mesaj": "Süper Yönetici hesabı dondurulamaz!"}

        # Hem 'aktif' hem de 'aktif_mi' parametrelerini destekle
        durum_bool = veri.aktif if veri.aktif is not None else veri.aktif_mi
        if durum_bool is None:
            durum_bool = True

        yeni_durum = 1 if durum_bool else 0
        db.cursor.execute("UPDATE kullanicilar SET aktif = ? WHERE id = ?", (yeni_durum, veri.kullanici_id))
        if not durum_bool:
            db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE kullanici_id = ?", (veri.kullanici_id,))
        db.conn.commit()

        islem_adi = "Hesap Aktif Edildi" if durum_bool else "Hesap Donduruldu"
        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            islem_adi,
            f"'{h_ad}' hesabı {'aktif edildi' if durum_bool else 'donduruldu'}.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"'{h_ad}' hesabı başarıyla {'aktifleştirildi' if durum_bool else 'donduruldu'}."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.delete("/admin/kullanici-sil/{id}")
def kullanici_sil(id: int, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Kullanıcı hesabını kalıcı olarak siler (Süper admin silinemez)."""
    try:
        db.cursor.execute("SELECT id, kullanici_adi, ad_soyad, super_admin_mi FROM kullanicilar WHERE id = ?", (id,))
        row = db.cursor.fetchone()
        if not row:
            return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

        h_id, h_kadi, h_ad, h_super = row

        if h_super:
            raise HTTPException(status_code=400, detail="Süper Yönetici hesabı silinemez!")

        db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE kullanici_id = ?", (id,))
        db.cursor.execute("DELETE FROM kullanicilar WHERE id = ?", (id,))
        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            "Kullanıcı Silindi",
            f"'{h_ad}' ({h_kadi}) kullanıcı hesabı silindi.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"'{h_ad}' kullanıcı hesabı silindi."}
    except HTTPException:
        raise
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/admin/super-admin-devret")
def super_admin_devret(veri: SuperAdminDevretRequest, request: Request, aktif_kullanici = Depends(get_aktif_kullanici)):
    """Süper Yöneticilik görev ve dokunulmazlığını başka bir personele devreder."""
    try:
        if not aktif_kullanici.get("super_admin_mi"):
            raise HTTPException(status_code=403, detail="Bu işlemi yalnızca mevcut Süper Yönetici gerçekleştirebilir.")

        # Mevcut yöneticinin şifresini doğrula
        db.cursor.execute("SELECT sifre_hash, salt FROM kullanicilar WHERE id = ?", (aktif_kullanici["id"],))
        s_row = db.cursor.fetchone()
        if not s_row or not sifre_dogrula(veri.onay_sifresi.strip(), s_row[0], s_row[1]):
            raise HTTPException(status_code=400, detail="Güvenlik onayı başarısız! Kendi şifrenizi hatalı girdiniz.")

        hedef_id = veri.yeni_super_admin_id or veri.hedef_kullanici_id
        if not hedef_id:
            raise HTTPException(status_code=400, detail="Devredilecek hedef kullanıcı belirtilmedi.")

        # Hedef kullanıcıyı bul
        db.cursor.execute("SELECT id, ad_soyad FROM kullanicilar WHERE id = ?", (hedef_id,))
        h_row = db.cursor.fetchone()
        if not h_row:
            raise HTTPException(status_code=404, detail="Devredilecek kullanıcı bulunamadı.")

        h_id, h_ad = h_row

        if h_id == aktif_kullanici["id"]:
            raise HTTPException(status_code=400, detail="Zaten Süper Yönetici sizsiniz.")

        tum_izinler = json.dumps({
            "ogrenci": True, "izin": True, "teblig": True, "terfi": True, "ihale": True, "admin": True
        })

        # Eski yöneticiyi normal yöneticiye çek, yenisini süper yönetici yap
        db.cursor.execute("UPDATE kullanicilar SET super_admin_mi = 0, rol = 'YONETICI' WHERE id = ?", (aktif_kullanici["id"],))
        db.cursor.execute("UPDATE kullanicilar SET super_admin_mi = 1, rol = 'SUPER_ADMIN', izinler = ?, aktif = 1 WHERE id = ?", (tum_izinler, h_id))
        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Güvenlik",
            "Süper Yönetici Devri",
            f"Süper Yöneticilik yetkisi '{h_ad}' personeline devredildi.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"Süper Yöneticilik görevi başarıyla '{h_ad}' personeline devredildi."}
    except HTTPException:
        raise
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/admin/personel-eslestir")
def personel_eslestir(veri: PersonelEslestirRequest, request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Kullanıcı hesabını resmi personel kartıyla birleştirir (merge)."""
    try:
        # Hedef personeli bul
        db.cursor.execute("SELECT rowid, ad_soyad, COALESCE(unvan, ''), COALESCE(gorev, '') FROM personel WHERE rowid = ?", (veri.hedef_personel_id,))
        p_row = db.cursor.fetchone()
        if not p_row:
            return {"basarili": False, "mesaj": "Hedef personel kartı bulunamadı."}

        p_id, p_ad, p_unvan, p_gorev = p_row

        # Mevcut kullanıcıyı bul
        db.cursor.execute("SELECT id, personel_id, ad_soyad FROM kullanicilar WHERE id = ?", (veri.kullanici_id,))
        k_row = db.cursor.fetchone()
        if not k_row:
            return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

        k_id, eski_pid, eski_ad = k_row

        # Kullanıcıyı güncelle
        unvan_str = p_unvan or p_gorev or "Personel"
        db.cursor.execute("""
            UPDATE kullanicilar 
            SET personel_id = ?, ad_soyad = ?, unvan = ?
            WHERE id = ?
        """, (p_id, p_ad, unvan_str, k_id))

        # Eğer eski taslak bir personel kartı varsa ve silinmesi istenmişse temizle
        if (veri.eski_taslak_silinsin_mi or veri.taslak_sil) and eski_pid and eski_pid != p_id:
            try:
                db.cursor.execute("DELETE FROM personel WHERE rowid = ?", (eski_pid,))
            except Exception:
                pass

        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Kullanıcı Yönetimi",
            "Personel Kartı Eşleştirildi",
            f"'{eski_ad}' kullanıcısı resmi '{p_ad}' personel kartına bağlandı.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": f"Kullanıcı başarıyla '{p_ad}' resmi personel kartına bağlandı."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/admin/tum-oturumlar-kapat")
def tum_oturumlari_kapat(request: Request, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Mevcut kullanıcı hariç ağdaki tüm açık oturumları sonlandırır."""
    try:
        mevcut_token = aktif_kullanici.get("token") or ""
        db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE token != ?", (mevcut_token,))
        etkilenen = db.cursor.rowcount
        db.conn.commit()

        denetim_kaydi_ekle(
            aktif_kullanici["id"],
            aktif_kullanici["kullanici_adi"],
            aktif_kullanici["ad_soyad"],
            "Güvenlik",
            "Tüm Oturumlar Kapatıldı",
            f"Sistemdeki {etkilenen} adet diğer oturum zorla sonlandırıldı.",
            request.client.host if request.client else ""
        )

        return {
            "basarili": True, 
            "mesaj": f"Sistemdeki diğer {etkilenen} açık oturum başarıyla sonlandırıldı.",
            "kapatilan_oturum_sayisi": etkilenen
        }
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.get("/admin/ag-durumu")
def ag_durumu(aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Ana bilgisayarın yerel IP adresini ve bağlantı linkini döner."""
    ip = yerel_ip_al()
    port = 8000
    adres = f"http://{ip}:{port}"
    return {
        "basarili": True,
        "yerel_ip": ip,
        "port": port,
        "baglanti_adresi": adres,
        "tam_adres": adres
    }

@router.get("/admin/denetim-loglari")
def denetim_loglari(limit: int = 100, aktif_kullanici = Depends(yetki_gerekli("admin"))):
    """Sistem işlem ve güvenlik denetim kayıtlarını listeler."""
    try:
        db.cursor.execute("""
            SELECT id, COALESCE(kullanici_adi, '-'), COALESCE(ad_soyad, '-'), 
                   COALESCE(modul, '-'), COALESCE(islem, '-'), COALESCE(detay, '-'), 
                   COALESCE(ip_adresi, '-'), tarih
            FROM islem_denetim_kayitlari
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = db.cursor.fetchall()
        loglar = [
            {
                "id": r[0],
                "kullanici_adi": r[1],
                "ad_soyad": r[2],
                "modul": r[3],
                "islem": r[4],
                "detay": r[5],
                "ip_adresi": r[6],
                "tarih": r[7]
            } for r in rows
        ]
        return {"basarili": True, "loglar": loglar}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e), "loglar": []}
