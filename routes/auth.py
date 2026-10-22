import os
import json
import uuid
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, Depends

from dependencies import db, get_aktif_kullanici, denetim_kaydi_ekle
from veritabani import sifre_hashle, sifre_dogrula

router = APIRouter()

# Brute-force koruması için bellek içi sayaç: {kullanici_adi: [son_deneme_tarihleri]}
BASARISIZ_GIRISLER = {}
MAX_HATALI_DENEME = 5
KILITLEME_SURESI_DAKIKA = 5

def _kilitli_mi(kullanici_adi: str) -> tuple[bool, int]:
    k_norm = kullanici_adi.strip().lower()
    simdi = datetime.now()
    if k_norm in BASARISIZ_GIRISLER:
        # 5 dakikadan eski denemeleri temizle
        BASARISIZ_GIRISLER[k_norm] = [
            t for t in BASARISIZ_GIRISLER[k_norm] 
            if simdi - t < timedelta(minutes=KILITLEME_SURESI_DAKIKA)
        ]
        if len(BASARISIZ_GIRISLER[k_norm]) >= MAX_HATALI_DENEME:
            kalan_sn = int((BASARISIZ_GIRISLER[k_norm][0] + timedelta(minutes=KILITLEME_SURESI_DAKIKA) - simdi).total_seconds())
            return True, max(1, kalan_sn)
    return False, 0

def _hatali_giris_kaydet(kullanici_adi: str):
    k_norm = kullanici_adi.strip().lower()
    if k_norm not in BASARISIZ_GIRISLER:
        BASARISIZ_GIRISLER[k_norm] = []
    BASARISIZ_GIRISLER[k_norm].append(datetime.now())

def _hatali_giris_temizle(kullanici_adi: str):
    k_norm = kullanici_adi.strip().lower()
    if k_norm in BASARISIZ_GIRISLER:
        del BASARISIZ_GIRISLER[k_norm]

class IlkKurulumRequest(BaseModel):
    personel_id: Optional[int] = None
    ad_soyad: str
    unvan: Optional[str] = "Okul Müdürü"
    kullanici_adi: str
    sifre: str

class GirisRequest(BaseModel):
    kullanici_adi: str
    sifre: str
    beni_hatirla: Optional[bool] = False

class SifreDegistirRequest(BaseModel):
    mevcut_sifre: Optional[str] = None
    eski_sifre: Optional[str] = None
    yeni_sifre: str

@router.get("/auth/kurulum-durumu")
def kurulum_durumu():
    """Sistemde aktif bir Süper Yönetici bulunup bulunmadığını bildirir."""
    try:
        db.cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE super_admin_mi = 1 AND aktif = 1")
        super_sayisi = db.cursor.fetchone()[0] or 0
        db.cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        toplam_sayi = db.cursor.fetchone()[0] or 0
        return {
            "basarili": True,
            "kurulu": super_sayisi > 0,
            "kurulum_yapildi": super_sayisi > 0,
            "toplam_kullanici": toplam_sayi
        }
    except Exception as e:
        return {"basarili": False, "mesaj": str(e), "kurulu": False, "kurulum_yapildi": False}

@router.get("/auth/personeller-ozet")
def personeller_ozet():
    """İlk kurulum veya kullanıcı ekleme için okul personeli listesini döner."""
    try:
        db.cursor.execute("SELECT rowid, ad_soyad, COALESCE(unvan, ''), COALESCE(gorev, ''), COALESCE(brans, '') FROM personel WHERE aktif = 1 ORDER BY ad_soyad")
        rows = db.cursor.fetchall()
        liste = [
            {
                "id": r[0],
                "ad_soyad": r[1],
                "unvan": r[2] or r[3] or "Personel",
                "gorev": r[3] or "",
                "brans": r[4] or ""
            } for r in rows
        ]
        return {"basarili": True, "personeller": liste}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e), "personeller": []}

@router.post("/auth/ilk-kurulum")
def ilk_kurulum(veri: IlkKurulumRequest, request: Request):
    """Sistemin ilk dokunulmaz Süper Yöneticisini tanımlar."""
    try:
        db.cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE super_admin_mi = 1 AND aktif = 1")
        if (db.cursor.fetchone()[0] or 0) > 0:
            raise HTTPException(status_code=400, detail="İlk kurulum zaten tamamlanmış. Sistemde zaten bir Süper Yönetici hesabı mevcuttur.")

        ad_soyad = veri.ad_soyad.strip()
        k_adi = veri.kullanici_adi.strip().lower()
        unvan = veri.unvan.strip() if veri.unvan else "Okul Müdürü"
        sifre = veri.sifre.strip()

        if len(k_adi) < 3 or len(sifre) < 4:
            raise HTTPException(status_code=400, detail="Kullanıcı adı en az 3, şifre en az 4 karakter olmalıdır.")

        s_hash, salt = sifre_hashle(sifre)
        tum_izinler = {
            "ogrenci": True,
            "izin": True,
            "teblig": True,
            "terfi": True,
            "ihale": True,
            "admin": True
        }
        izinler_json = json.dumps(tum_izinler)
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        personel_id = veri.personel_id
        if not personel_id:
            # Personel tablosunda bu isimde bir kayıt var mı kontrol et (tekrar eklemeyi önle)
            db.cursor.execute("SELECT rowid FROM personel WHERE LOWER(TRIM(ad_soyad)) = LOWER(?)", (ad_soyad.strip(),))
            mevcut_p = db.cursor.fetchone()
            if mevcut_p:
                personel_id = mevcut_p[0]
            else:
                try:
                    db.cursor.execute(
                        "INSERT INTO personel (ad_soyad, unvan, gorev, aktif) VALUES (?, ?, ?, 1)",
                        (ad_soyad, unvan, unvan)
                    )
                    db.conn.commit()
                    personel_id = db.cursor.lastrowid
                except Exception:
                    pass

        db.cursor.execute("""
            INSERT INTO kullanicilar 
            (personel_id, kullanici_adi, sifre_hash, salt, ad_soyad, unvan, rol, izinler, super_admin_mi, aktif, son_giris, son_islem)
            VALUES (?, ?, ?, ?, ?, ?, 'SUPER_ADMIN', ?, 1, 1, ?, ?)
        """, (personel_id, k_adi, s_hash, salt, ad_soyad, unvan, izinler_json, simdi, simdi))
        db.conn.commit()
        yeni_id = db.cursor.lastrowid

        # Otomatik oturum token'ı oluştur
        token = secrets.token_hex(32)
        gecerlilik = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        client_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("User-Agent", "")

        db.cursor.execute("""
            INSERT INTO kullanici_oturumlar (token, kullanici_id, ip_adresi, cihaz_bilgisi, beni_hatirla, olusturma_tarihi, son_aktivite, gecerlilik_tarihi)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
        """, (token, yeni_id, client_ip, user_agent, simdi, simdi, gecerlilik))
        db.conn.commit()

        denetim_kaydi_ekle(yeni_id, k_adi, ad_soyad, "Güvenlik", "İlk Kurulum", "Sistemin ilk Süper Yöneticisi oluşturuldu.", client_ip)

        return {
            "basarili": True,
            "mesaj": "Süper Yönetici başarıyla oluşturuldu.",
            "token": token,
            "kullanici": {
                "id": yeni_id,
                "kullanici_adi": k_adi,
                "ad_soyad": ad_soyad,
                "unvan": unvan,
                "rol": "SUPER_ADMIN",
                "super_admin_mi": True,
                "izinler": tum_izinler
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"İlk kurulum hatası: {e}", exc_info=True)
        return {"basarili": False, "mesaj": f"Kurulum hatası: {str(e)}"}

@router.post("/auth/giris")
def giris(veri: GirisRequest, request: Request):
    """Kullanıcı adı ve şifre ile sisteme giriş yapar ve oturum token'ı üretir."""
    k_adi = veri.kullanici_adi.strip().lower()
    sifre = veri.sifre.strip()
    client_ip = request.client.host if request.client else ""

    kilitli, kalan_sn = _kilitli_mi(k_adi)
    if kilitli:
        raise HTTPException(
            status_code=429,
            detail=f"Çok fazla hatalı giriş denemesi! Güvenlik nedeniyle hesap {kalan_sn} saniye kilitlenmiştir."
        )

    try:
        db.cursor.execute("""
            SELECT id, personel_id, kullanici_adi, sifre_hash, salt, ad_soyad, unvan, rol, izinler, super_admin_mi, aktif
            FROM kullanicilar
            WHERE LOWER(kullanici_adi) = ?
        """, (k_adi,))
        row = db.cursor.fetchone()

        if not row:
            _hatali_giris_kaydet(k_adi)
            kalan = max(0, MAX_HATALI_DENEME - len(BASARISIZ_GIRISLER.get(k_adi, [])))
            raise HTTPException(status_code=401, detail=f"Kullanıcı adı veya şifre hatalı. (Kalan hakkınız: {kalan})")

        k_id, p_id, db_k_adi, s_hash, salt, ad_soyad, unvan, rol, izinler_str, super_mi, aktif = row

        if not aktif:
            raise HTTPException(status_code=403, detail="Hesabınız dondurulmuştur. Lütfen sistem yöneticisiyle iletişime geçiniz.")

        if not sifre_dogrula(sifre, s_hash, salt):
            _hatali_giris_kaydet(k_adi)
            kalan = max(0, MAX_HATALI_DENEME - len(BASARISIZ_GIRISLER.get(k_adi, [])))
            raise HTTPException(status_code=401, detail=f"Kullanıcı adı veya şifre hatalı. (Kalan hakkınız: {kalan})")

        _hatali_giris_temizle(k_adi)

        # Oturum oluştur
        token = secrets.token_hex(32)
        simdi = datetime.now()
        simdi_str = simdi.strftime("%Y-%m-%d %H:%M:%S")
        gun_sayisi = 30 if veri.beni_hatirla else 1
        gecerlilik_str = (simdi + timedelta(days=gun_sayisi)).strftime("%Y-%m-%d %H:%M:%S")
        user_agent = request.headers.get("User-Agent", "")

        db.cursor.execute("""
            INSERT INTO kullanici_oturumlar 
            (token, kullanici_id, ip_adresi, cihaz_bilgisi, beni_hatirla, olusturma_tarihi, son_aktivite, gecerlilik_tarihi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (token, k_id, client_ip, user_agent, 1 if veri.beni_hatirla else 0, simdi_str, simdi_str, gecerlilik_str))

        db.cursor.execute("UPDATE kullanicilar SET son_giris = ?, son_islem = ? WHERE id = ?", (simdi_str, simdi_str, k_id))
        db.conn.commit()

        izinler = {}
        if izinler_str:
            try:
                izinler = json.loads(izinler_str)
            except Exception:
                pass

        denetim_kaydi_ekle(k_id, db_k_adi, ad_soyad, "Güvenlik", "Giriş Yapıldı", f"Sisteme giriş yapıldı (Beni Hatırla: {'Evet' if veri.beni_hatirla else 'Hayır'}).", client_ip)

        return {
            "basarili": True,
            "mesaj": f"Hoş geldiniz, {ad_soyad}.",
            "token": token,
            "beni_hatirla": veri.beni_hatirla,
            "kullanici": {
                "id": k_id,
                "kullanici_adi": db_k_adi,
                "ad_soyad": ad_soyad,
                "unvan": unvan,
                "rol": rol,
                "super_admin_mi": bool(super_mi),
                "izinler": izinler
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Giriş hatası: {e}", exc_info=True)
        return {"basarili": False, "mesaj": f"Giriş sırasında bir hata oluştu: {str(e)}"}

@router.post("/auth/cikis")
def cikis(request: Request, aktif_kullanici = Depends(get_aktif_kullanici)):
    """Aktif oturum anahtarını sonlandırır."""
    try:
        token = aktif_kullanici.get("token")
        if token:
            db.cursor.execute("DELETE FROM kullanici_oturumlar WHERE token = ?", (token,))
            db.conn.commit()
            denetim_kaydi_ekle(
                aktif_kullanici["id"], 
                aktif_kullanici["kullanici_adi"], 
                aktif_kullanici["ad_soyad"], 
                "Güvenlik", 
                "Çıkış Yapıldı", 
                "Oturum güvenli şekilde kapatıldı.", 
                request.client.host if request.client else ""
            )
        return {"basarili": True, "mesaj": "Oturum başarıyla kapatıldı."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.get("/auth/ben")
def ben(aktif_kullanici = Depends(get_aktif_kullanici)):
    """Giriş yapmış olan aktif kullanıcının bilgilerini döner."""
    return {"basarili": True, "kullanici": aktif_kullanici}

@router.post("/auth/sifre-degistir")
def sifre_degistir(veri: SifreDegistirRequest, request: Request, aktif_kullanici = Depends(get_aktif_kullanici)):
    """Kullanıcının kendi şifresini güvenli şekilde değiştirmesini sağlar."""
    try:
        k_id = aktif_kullanici["id"]
        mevcut = (veri.mevcut_sifre or veri.eski_sifre or "").strip()
        yeni = veri.yeni_sifre.strip()

        if len(yeni) < 4:
            raise HTTPException(status_code=400, detail="Yeni şifre en az 4 karakter olmalıdır.")

        db.cursor.execute("SELECT sifre_hash, salt FROM kullanicilar WHERE id = ?", (k_id,))
        row = db.cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

        eski_hash, eski_salt = row
        if not sifre_dogrula(mevcut, eski_hash, eski_salt):
            raise HTTPException(status_code=400, detail="Mevcut şifreniz hatalı.")

        yeni_hash, yeni_salt = sifre_hashle(yeni)
        db.cursor.execute("UPDATE kullanicilar SET sifre_hash = ?, salt = ? WHERE id = ?", (yeni_hash, yeni_salt, k_id))
        db.conn.commit()

        denetim_kaydi_ekle(
            k_id, 
            aktif_kullanici["kullanici_adi"], 
            aktif_kullanici["ad_soyad"], 
            "Güvenlik", 
            "Şifre Güncellendi", 
            "Kullanıcı kendi şifresini güncelledi.",
            request.client.host if request.client else ""
        )

        return {"basarili": True, "mesaj": "Şifreniz başarıyla güncellendi."}
    except HTTPException:
        raise
    except Exception as e:
        return {"basarili": False, "mesaj": f"Şifre güncelleme hatası: {str(e)}"}
