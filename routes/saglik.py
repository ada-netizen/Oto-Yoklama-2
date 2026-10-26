from fastapi import APIRouter, File, UploadFile, HTTPException
from veritabani import VeritabaniYoneticisi
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import io
import re
import calendar
import PyPDF2
import logging

router = APIRouter()
from dependencies import db, islem_logla
from araclar import VeriAraclari
from mevzuat_kurallari import ogretmen_mi, yonetici_mi, PERSONEL_DURUMLARI_REHBERI

class SaglikRaporuRequest(BaseModel):
    personel_ad: str
    baslangic_tarihi: str
    bitis_tarihi: Optional[str] = None
    gun_sayisi: Optional[int] = 1
    aciklama: Optional[str] = ""
    izin_turu: Optional[str] = "SAĞLIK"  # SAĞLIK, YILLIK, MAZERET, İDARİ, AYLIKSIZ, DİĞER
    mevzuat_maddesi: Optional[str] = ""
    belge_no: Optional[str] = ""
    izin_adresi: Optional[str] = ""
    rapor_turu: Optional[str] = ""

class KesintiRequest(BaseModel):
    personel_ad: str
    onceden_kesilen: int

def format_tr_tarih(tarih_str: str) -> str:
    if not tarih_str:
        return ""
    try:
        parts = tarih_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    except Exception:
        pass
    return tarih_str

def cakisan_rapor_kontrol(personel_ad: str, baslangic: str, bitis: str, haric_id: Optional[int] = None):
    if not bitis:
        bitis = baslangic

    try:
        db.cursor.execute(
            """
            SELECT id, personel_ad, baslangic_tarihi, COALESCE(NULLIF(bitis_tarihi, ''), baslangic_tarihi) as bitis, 
                   gun_sayisi, aciklama, COALESCE(izin_turu, 'SAĞLIK')
            FROM saglik_raporlari
            WHERE baslangic_tarihi <= ?
              AND COALESCE(NULLIF(bitis_tarihi, ''), baslangic_tarihi) >= ?
            """,
            (bitis, baslangic)
        )
        rows = db.cursor.fetchall()
        
        target_norm = VeriAraclari.tr_normalize(personel_ad)
        for r in rows:
            r_id, r_ad, r_bas, r_bit, r_gun, r_acik, r_tur = r
            if haric_id is not None and r_id == haric_id:
                continue
            if r_ad == personel_ad or VeriAraclari.tr_normalize(r_ad) == target_norm:
                return {
                    "id": r_id,
                    "personel_ad": r_ad,
                    "baslangic": r_bas,
                    "bitis": r_bit,
                    "gun_sayisi": r_gun,
                    "aciklama": r_acik,
                    "izin_turu": r_tur
                }
    except Exception:
        pass
        
    return None

def saglik_personel_isimlerini_senkronize_et():
    """
    saglik_raporlari tablosundaki kayitlarin isimlerini personel tablosundaki
    resmi (kanonik) yazimlarla esitler (buyuk/kucuk harf ve karakter tutarsizliklarini giderir).
    """
    try:
        db.cursor.execute("SELECT ad_soyad FROM personel")
        personel_harita = {VeriAraclari.tr_normalize(r[0]): r[0] for r in db.cursor.fetchall()}
        if not personel_harita:
            return
        
        db.cursor.execute("SELECT DISTINCT personel_ad FROM saglik_raporlari")
        distinct_adlar = [r[0] for r in db.cursor.fetchall()]
        
        degisiklik_var = False
        for eski_ad in distinct_adlar:
            if not eski_ad:
                continue
            norm = VeriAraclari.tr_normalize(eski_ad)
            kanonik = personel_harita.get(norm)
            if kanonik and kanonik != eski_ad:
                db.cursor.execute("UPDATE saglik_raporlari SET personel_ad = ? WHERE personel_ad = ?", (kanonik, eski_ad))
                degisiklik_var = True
        
        if degisiklik_var:
            db.conn.commit()
            logging.info("[IZIN MASASI] saglik_raporlari personel isimleri kanonik yazimlarla esitlendi.")
    except Exception as e:
        logging.warning(f"[IZIN MASASI] Isim senkronizasyonu atlandi: {e}")

@router.get("/saglik/liste")
def saglik_liste(yil: Optional[int] = None):
    try:
        saglik_personel_isimlerini_senkronize_et()
        hedef_yil = str(yil or datetime.now().year)

        # Personel listesini unvan, grup, brans bilgileriyle alalim
        db.cursor.execute("""
            SELECT ad_soyad, COALESCE(unvan, ''), COALESCE(grup, 'Kadrolu'), COALESCE(brans, ''), COALESCE(gorev, '')
            FROM personel 
            ORDER BY ad_soyad
        """)
        personel_rows = db.cursor.fetchall()
        personel_bilgi_haritasi = {
            r[0]: {
                "unvan": r[1],
                "grup": r[2],
                "brans": r[3],
                "gorev": r[4],
                "yonetici_mi": yonetici_mi(r[1], r[4]),
                "ogretmen_mi": ogretmen_mi(r[2], r[1], r[4])
            } for r in personel_rows
        }
        personel_listesi = [r[0] for r in personel_rows]

        # Secili yilin tum izin kayitlarini alalim
        db.cursor.execute("""
            SELECT personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, COALESCE(izin_turu, 'SAĞLIK') 
            FROM saglik_raporlari 
            WHERE baslangic_tarihi LIKE ? OR bitis_tarihi LIKE ?
        """, (f"{hedef_yil}-%", f"{hedef_yil}-%"))
        raporlar = db.cursor.fetchall()

        # saglik_raporlari tablosunda kaydi olup personel tablosunda yer almayan personelleri de listeye dahil edelim
        mevcut_normlar = {VeriAraclari.tr_normalize(p): p for p in personel_listesi}
        for r in raporlar:
            r_ad = (r[0] or "").strip()
            if not r_ad:
                continue
            r_norm = VeriAraclari.tr_normalize(r_ad)
            if r_norm not in mevcut_normlar:
                personel_listesi.append(r_ad)
                mevcut_normlar[r_norm] = r_ad
                personel_bilgi_haritasi[r_ad] = {
                    "unvan": "Personel",
                    "grup": "Kadrolu",
                    "brans": "",
                    "gorev": "",
                    "yonetici_mi": False,
                    "ogretmen_mi": True
                }

        # Onceden kesilen gunleri alalim
        db.cursor.execute("SELECT personel_ad, onceden_kesilen_gun FROM personel_rapor_kesinti")
        kesintiler = {VeriAraclari.tr_normalize(row[0]): row[1] for row in db.cursor.fetchall()}

        sonuc = []
        for p in personel_listesi:
            p_norm = VeriAraclari.tr_normalize(p)
            aylik_gunler = {str(i): 0 for i in range(1, 13)}
            aylik_detay = {str(i): {"toplam": 0, "turler": {}} for i in range(1, 13)}
            toplam_gun = 0
            saglik_gun = 0
            yillik_gun = 0
            mazeret_gun = 0
            idari_gun = 0
            ayliksiz_gun = 0
            diger_gun = 0
            tur_dagilimi = {}
            
            p_raporlar = [r for r in raporlar if VeriAraclari.tr_normalize(r[0]) == p_norm]
            for r in p_raporlar:
                r_bas = r[1]
                r_bit = r[2] or r[1]
                gun = r[3]
                tur = (r[4] or "SAĞLIK").upper()

                toplam_gun += gun
                tur_dagilimi[tur] = tur_dagilimi.get(tur, 0) + gun

                if tur == "SAĞLIK":
                    saglik_gun += gun
                elif tur == "YILLIK":
                    yillik_gun += gun
                elif tur == "MAZERET":
                    mazeret_gun += gun
                elif tur in ("İDARİ", "IDARI"):
                    idari_gun += gun
                elif tur == "AYLIKSIZ":
                    ayliksiz_gun += gun
                else:
                    diger_gun += gun

                try:
                    dt_bas = datetime.strptime(r_bas, "%Y-%m-%d")
                    dt_bit = datetime.strptime(r_bit, "%Y-%m-%d")
                    if dt_bit < dt_bas:
                        dt_bas, dt_bit = dt_bit, dt_bas
                except Exception:
                    try:
                        ay = str(int(r_bas.split("-")[1]))
                        aylik_gunler[ay] = aylik_gunler.get(ay, 0) + gun
                        aylik_detay[ay]["toplam"] += gun
                        aylik_detay[ay]["turler"][tur] = aylik_detay[ay]["turler"].get(tur, 0) + gun
                    except Exception:
                        pass
                    continue

                if dt_bas.month == dt_bit.month:
                    ay = str(dt_bas.month)
                    aylik_gunler[ay] = aylik_gunler.get(ay, 0) + gun
                    aylik_detay[ay]["toplam"] += gun
                    aylik_detay[ay]["turler"][tur] = aylik_detay[ay]["turler"].get(tur, 0) + gun
                else:
                    curr = dt_bas
                    while curr <= dt_bit:
                        if curr.year == int(hedef_yil):
                            ay = str(curr.month)
                            aylik_gunler[ay] = aylik_gunler.get(ay, 0) + 1
                            aylik_detay[ay]["toplam"] += 1
                            aylik_detay[ay]["turler"][tur] = aylik_detay[ay]["turler"].get(tur, 0) + 1
                        curr += timedelta(days=1)
            
            # 657 SK Md. 152: 7 gunu asan zam ve tazminat kesintisi YALNIZCA saglik izinlerine uygulanir!
            # Yillik ve Mazeret izinleri kesinlikle 7 gunluk saglik kesintisine dahil edilmez!
            p_info = personel_bilgi_haritasi.get(p, {})
            is_isci = (p_info.get("grup") == "Sürekli İşçi")
            
            if is_isci:
                # 4/D Surekli iscide SGK istirahat sistemi gecerlidir
                yedi_gecen = 0
                onceden_kesilen = 0
                yeni_kesinti = 0
            else:
                yedi_gecen = max(0, saglik_gun - 7)
                onceden_kesilen = kesintiler.get(p_norm, 0)
                yeni_kesinti = max(0, yedi_gecen - onceden_kesilen)
            
            sonuc.append({
                "personel_ad": p,
                "unvan": p_info.get("unvan", ""),
                "grup": p_info.get("grup", "Kadrolu"),
                "brans": p_info.get("brans", ""),
                "gorev": p_info.get("gorev", ""),
                "yonetici_mi": p_info.get("yonetici_mi", False),
                "ogretmen_mi": p_info.get("ogretmen_mi", True),
                "aylar": aylik_gunler,
                "aylik_detay": aylik_detay,
                "toplam": toplam_gun,
                "saglik_gun": saglik_gun,
                "yillik_gun": yillik_gun,
                "mazeret_gun": mazeret_gun,
                "idari_gun": idari_gun,
                "ayliksiz_gun": ayliksiz_gun,
                "diger_gun": diger_gun,
                "tur_dagilimi": tur_dagilimi,
                "yedi_gecen": yedi_gecen,
                "onceden_kesilen": onceden_kesilen,
                "yeni_kesinti": yeni_kesinti
            })

        return {"basarili": True, "veri": sonuc}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.get("/saglik/takvim")
def saglik_takvim(yil: Optional[int] = None, izin_turu: Optional[str] = None, personel_turu: Optional[str] = None):
    """
    365 günlük yıllık matris takvim haritasını (12 ay x 31 gün) ve istatistikleri döner.
    """
    try:
        hedef_yil = int(yil or datetime.now().year)

        # Personel bilgileri
        db.cursor.execute("""
            SELECT ad_soyad, COALESCE(unvan, ''), COALESCE(grup, 'Kadrolu'), COALESCE(brans, ''), COALESCE(gorev, '')
            FROM personel
        """)
        personel_bilgileri = {}
        for r in db.cursor.fetchall():
            ad, unvan, grup, brans, gorev = r
            p_dict = {
                "ad": ad,
                "unvan": unvan,
                "grup": grup,
                "brans": brans,
                "gorev": gorev,
                "yonetici_mi": yonetici_mi(unvan, gorev),
                "ogretmen_mi": ogretmen_mi(grup, unvan, gorev)
            }
            personel_bilgileri[ad] = p_dict
            personel_bilgileri[VeriAraclari.tr_normalize(ad)] = p_dict

        # İzin kayıtları
        db.cursor.execute("""
            SELECT id, personel_ad, baslangic_tarihi, COALESCE(NULLIF(bitis_tarihi, ''), baslangic_tarihi) as bitis, 
                   gun_sayisi, aciklama, COALESCE(izin_turu, 'SAĞLIK'), COALESCE(mevzuat_maddesi, ''), COALESCE(belge_no, ''),
                   COALESCE(izin_adresi, ''), COALESCE(rapor_turu, '')
            FROM saglik_raporlari
            WHERE baslangic_tarihi LIKE ? OR bitis_tarihi LIKE ?
            ORDER BY baslangic_tarihi ASC
        """, (f"{hedef_yil}-%", f"{hedef_yil}-%"))
        kayitlar = db.cursor.fetchall()

        takvim_haritasi = {}
        izinli_personeller = set()
        toplam_izin_gunu = 0
        saglik_gun_toplam = 0
        yillik_gun_toplam = 0
        mazeret_gun_toplam = 0
        idari_gun_toplam = 0
        ayliksiz_gun_toplam = 0
        diger_gun_toplam = 0
        personel_saglik_gunleri = {}

        for row in kayitlar:
            r_id, p_ad, r_bas, r_bit, r_gun, r_acik, r_tur, r_mevzuat, r_belge, r_adres, r_rapor_turu = row
            tur = (r_tur or "SAĞLIK").upper()

            p_info = personel_bilgileri.get(p_ad) or personel_bilgileri.get(VeriAraclari.tr_normalize(p_ad), {
                "unvan": "", "grup": "Kadrolu", "brans": "", "gorev": "", "yonetici_mi": False, "ogretmen_mi": True
            })
            p_gosterim_ad = p_info.get("ad", p_ad)

            # Filtreler
            if izin_turu and izin_turu != "TUMU" and tur != izin_turu.upper():
                continue
            if personel_turu and personel_turu != "TUMU":
                if personel_turu == "IDARECI" and not p_info.get("yonetici_mi"):
                    continue
                elif personel_turu == "OGRETMEN" and (not p_info.get("ogretmen_mi") or p_info.get("yonetici_mi")):
                    continue
                elif personel_turu == "MEMUR" and (p_info.get("ogretmen_mi") or p_info.get("yonetici_mi")):
                    continue
                elif personel_turu == "KADROLU" and p_info.get("grup") != "Kadrolu":
                    continue
                elif personel_turu == "GOREVLENDIRME" and p_info.get("grup") != "Görevlendirme":
                    continue

            izinli_personeller.add(p_gosterim_ad)
            toplam_izin_gunu += r_gun
            if tur == "SAĞLIK":
                saglik_gun_toplam += r_gun
                personel_saglik_gunleri[p_gosterim_ad] = personel_saglik_gunleri.get(p_gosterim_ad, 0) + r_gun
            elif tur == "YILLIK":
                yillik_gun_toplam += r_gun
            elif tur == "MAZERET":
                mazeret_gun_toplam += r_gun
            elif tur in ("İDARİ", "IDARI"):
                idari_gun_toplam += r_gun
            elif tur == "AYLIKSIZ":
                ayliksiz_gun_toplam += r_gun
            else:
                diger_gun_toplam += r_gun

            # Başlangıç ve bitiş arasındaki tüm günleri takvim haritasına ekle
            try:
                dt_bas = datetime.strptime(r_bas, "%Y-%m-%d")
                dt_bit = datetime.strptime(r_bit, "%Y-%m-%d") if r_bit else dt_bas
            except Exception:
                continue

            curr = dt_bas
            while curr <= dt_bit:
                if curr.year == hedef_yil:
                    key = f"{curr.month}-{curr.day}"
                    if key not in takvim_haritasi:
                        takvim_haritasi[key] = []
                    
                    # Aynı personelin aynı gün mükerrer kaydını engelle
                    if not any(x["id"] == r_id and (x["personel_ad"] == p_ad or x["personel_ad"] == p_gosterim_ad) for x in takvim_haritasi[key]):
                        takvim_haritasi[key].append({
                            "id": r_id,
                            "personel_ad": p_gosterim_ad,
                            "unvan": p_info.get("unvan", ""),
                            "grup": p_info.get("grup", "Kadrolu"),
                            "brans": p_info.get("brans", ""),
                            "yonetici_mi": p_info.get("yonetici_mi", False),
                            "ogretmen_mi": p_info.get("ogretmen_mi", True),
                            "izin_turu": tur,
                            "mevzuat_maddesi": r_mevzuat,
                            "belge_no": r_belge,
                            "baslangic": r_bas,
                            "bitis": r_bit,
                            "gun_sayisi": r_gun,
                            "aciklama": r_acik or "-",
                            "izin_adresi": r_adres,
                            "rapor_turu": r_rapor_turu
                        })
                curr += timedelta(days=1)

        # 7 günü aşan sağlık izni alan personel sayısı
        kesinti_siniri_asan = sum(1 for g in personel_saglik_gunleri.values() if g > 7)

        return {
            "basarili": True,
            "yil": hedef_yil,
            "takvim_haritasi": takvim_haritasi,
            "istatistikler": {
                "toplam_izinli_personel": len(izinli_personeller),
                "toplam_izin_gunu": toplam_izin_gunu,
                "saglik_gun_toplam": saglik_gun_toplam,
                "yillik_gun_toplam": yillik_gun_toplam,
                "mazeret_gun_toplam": mazeret_gun_toplam,
                "idari_gun_toplam": idari_gun_toplam,
                "ayliksiz_gun_toplam": ayliksiz_gun_toplam,
                "diger_gun_toplam": diger_gun_toplam,
                "kesinti_siniri_asan": kesinti_siniri_asan
            }
        }
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/saglik/ekle")
def saglik_ekle(veri: SaglikRaporuRequest):
    try:
        bas = (veri.baslangic_tarihi or "").strip()
        bit = (veri.bitis_tarihi or veri.baslangic_tarihi or "").strip()
        if "." in bas and len(bas.split(".")) == 3 and len(bas.split(".")[2]) == 4:
            p = bas.split(".")
            bas = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"
        if "." in bit and len(bit.split(".")) == 3 and len(bit.split(".")[2]) == 4:
            p = bit.split(".")
            bit = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"
        if bit < bas:
            bas, bit = bit, bas

        gun_sayisi = veri.gun_sayisi if (veri.gun_sayisi and veri.gun_sayisi > 0) else 1

        logging.info(f"=== [İZİN EKLE İSTEĞİ] Personel: '{veri.personel_ad}', Tür: '{veri.izin_turu}', Tarih: {bas} - {bit}, Gün: {gun_sayisi} ===")
        cakisan = cakisan_rapor_kontrol(veri.personel_ad, bas, bit)
        if cakisan:
            c_bas = format_tr_tarih(cakisan["baslangic"])
            c_bit = format_tr_tarih(cakisan["bitis"])
            tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
            tur_adi = cakisan.get("izin_turu", "izin")
            logging.warning(f"[İZİN ÇAKIŞMA] {veri.personel_ad} için {tarih_mesaji} çakışan kayıt: {cakisan}")
            return {
                "basarili": False,
                "cakisma": True,
                "mesaj": f"Bu tarihlerde zaten izin/rapor kaydı var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı bir {tur_adi} bulunmaktadır. Yeni kayıt eklenemez."
            }

        izin_turu = (veri.izin_turu or "SAĞLIK").strip().upper()
        mevzuat_maddesi = veri.mevzuat_maddesi or ""
        if not mevzuat_maddesi:
            if izin_turu == "SAĞLIK":
                mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"
            elif izin_turu == "YILLIK":
                mevzuat_maddesi = "657 sayılı DMK Madde 102"
            elif izin_turu == "MAZERET":
                mevzuat_maddesi = "657 sayılı DMK Madde 104"
            elif izin_turu == "AYLIKSIZ":
                mevzuat_maddesi = "657 sayılı DMK Madde 108"
            elif izin_turu == "İDARİ":
                mevzuat_maddesi = "Genel İdari İzin"

        # Personel tablosundaki resmi yazimi bulup kanonik adla kaydet
        db.cursor.execute("SELECT ad_soyad FROM personel")
        personel_harita = {VeriAraclari.tr_normalize(r[0]): r[0] for r in db.cursor.fetchall()}
        kanonik_ad = personel_harita.get(VeriAraclari.tr_normalize(veri.personel_ad), veri.personel_ad)

        db.cursor.execute(
            """INSERT INTO saglik_raporlari 
               (personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama, izin_turu, mevzuat_maddesi, belge_no, izin_adresi, rapor_turu) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (kanonik_ad, bas, bit, gun_sayisi, veri.aciklama, izin_turu, mevzuat_maddesi, veri.belge_no or "", veri.izin_adresi or "", veri.rapor_turu or "")
        )
        db.conn.commit()
        kayit_id = db.cursor.lastrowid
        logging.info(f"[İZİN EKLENDİ] ID: {kayit_id}, Personel: {veri.personel_ad}, Tür: {izin_turu}, Gün: {gun_sayisi}")
        try:
            islem_logla("bilgi", "İzin Kaydı Ekleme", f"{veri.personel_ad} için {gun_sayisi} günlük {izin_turu} izni kaydedildi.")
        except Exception:
            pass
        return {"basarili": True, "mesaj": f"{izin_turu.capitalize()} kaydı başarıyla eklendi."}
    except Exception as e:
        logging.error(f"[İZİN EKLEME HATASI] Personel: '{veri.personel_ad}', Hata: {e}", exc_info=True)
        try:
            islem_logla("hata", "İzin Kaydı Ekleme", f"{veri.personel_ad} izin kaydı eklenemedi: {e}")
        except Exception:
            pass
        return {"basarili": False, "mesaj": str(e)}

@router.post("/saglik/kesinti-guncelle")
def kesinti_guncelle(veri: KesintiRequest):
    try:
        db.cursor.execute("INSERT OR REPLACE INTO personel_rapor_kesinti (personel_ad, onceden_kesilen_gun) VALUES (?, ?)", (veri.personel_ad, veri.onceden_kesilen))
        db.conn.commit()
        return {"basarili": True, "mesaj": "Kesinti güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.delete("/saglik/sil/{id}")
def saglik_sil(id: int):
    try:
        db.cursor.execute("DELETE FROM saglik_raporlari WHERE id = ?", (id,))
        db.conn.commit()
        return {"basarili": True, "mesaj": "İzin kaydı silindi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.get("/saglik/raporlar/{personel_ad}")
def personel_raporlari(personel_ad: str, yil: Optional[int] = None):
    try:
        hedef_yil = str(yil or datetime.now().year)
        db.cursor.execute(
            """SELECT id, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama, 
                      COALESCE(izin_turu, 'SAĞLIK') as izin_turu,
                      COALESCE(mevzuat_maddesi, '') as mevzuat_maddesi,
                      COALESCE(belge_no, '') as belge_no,
                      COALESCE(izin_adresi, '') as izin_adresi,
                      COALESCE(rapor_turu, '') as rapor_turu,
                      personel_ad
               FROM saglik_raporlari 
               WHERE (baslangic_tarihi LIKE ? OR bitis_tarihi LIKE ?) 
               ORDER BY baslangic_tarihi DESC""",
            (f"{hedef_yil}-%", f"{hedef_yil}-%")
        )
        p_norm = VeriAraclari.tr_normalize(personel_ad)
        raporlar = [{
            "id": r[0], 
            "baslangic": r[1], 
            "bitis": r[2] or r[1], 
            "gun": r[3], 
            "aciklama": r[4], 
            "izin_turu": r[5],
            "mevzuat_maddesi": r[6],
            "belge_no": r[7],
            "izin_adresi": r[8],
            "rapor_turu": r[9]
        } for r in db.cursor.fetchall() if VeriAraclari.tr_normalize(r[10]) == p_norm]
        return {"basarili": True, "veri": raporlar}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.put("/saglik/duzenle/{id}")
def saglik_duzenle(id: int, veri: SaglikRaporuRequest):
    try:
        bitis = veri.bitis_tarihi if veri.bitis_tarihi else veri.baslangic_tarihi
        cakisan = cakisan_rapor_kontrol(veri.personel_ad, veri.baslangic_tarihi, bitis, haric_id=id)
        if cakisan:
            c_bas = format_tr_tarih(cakisan["baslangic"])
            c_bit = format_tr_tarih(cakisan["bitis"])
            tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
            tur_adi = cakisan.get("izin_turu", "izin")
            return {
                "basarili": False,
                "cakisma": True,
                "mesaj": f"Bu tarihlerde zaten izin kaydı var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı başka bir {tur_adi} bulunmaktadır."
            }

        izin_turu = (veri.izin_turu or "SAĞLIK").strip().upper()
        mevzuat_maddesi = veri.mevzuat_maddesi or ""
        if not mevzuat_maddesi:
            if izin_turu == "SAĞLIK":
                mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"
            elif izin_turu == "YILLIK":
                mevzuat_maddesi = "657 sayılı DMK Madde 102"
            elif izin_turu == "MAZERET":
                mevzuat_maddesi = "657 sayılı DMK Madde 104"
            elif izin_turu == "AYLIKSIZ":
                mevzuat_maddesi = "657 sayılı DMK Madde 108"
            elif izin_turu == "İDARİ":
                mevzuat_maddesi = "Genel İdari İzin"

        db.cursor.execute("SELECT ad_soyad FROM personel")
        personel_harita = {VeriAraclari.tr_normalize(r[0]): r[0] for r in db.cursor.fetchall()}
        kanonik_ad = personel_harita.get(VeriAraclari.tr_normalize(veri.personel_ad), veri.personel_ad) if veri.personel_ad else None

        if kanonik_ad:
            db.cursor.execute(
                """UPDATE saglik_raporlari 
                   SET personel_ad = ?, baslangic_tarihi = ?, bitis_tarihi = ?, gun_sayisi = ?, aciklama = ?, izin_turu = ?, mevzuat_maddesi = ?, belge_no = ?, izin_adresi = ?, rapor_turu = ? 
                   WHERE id = ?""",
                (kanonik_ad, veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama, izin_turu, mevzuat_maddesi, veri.belge_no or "", veri.izin_adresi or "", veri.rapor_turu or "", id)
            )
        else:
            db.cursor.execute(
                """UPDATE saglik_raporlari 
                   SET baslangic_tarihi = ?, bitis_tarihi = ?, gun_sayisi = ?, aciklama = ?, izin_turu = ?, mevzuat_maddesi = ?, belge_no = ?, izin_adresi = ?, rapor_turu = ? 
                   WHERE id = ?""",
                (veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama, izin_turu, mevzuat_maddesi, veri.belge_no or "", veri.izin_adresi or "", veri.rapor_turu or "", id)
            )
        db.conn.commit()
        return {"basarili": True, "mesaj": "İzin kaydı güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/saglik/pdf-oku")
@router.post("/pdf-oku")
async def saglik_pdf_oku(dosya: UploadFile = File(...)):
    try:
        content = await dosya.read()
        logging.info(f"=== [PDF İZİN ÇÖZÜMLEME BAŞLADI] Dosya: '{dosya.filename}', Boyut: {len(content)} byte ===")
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page_idx, page in enumerate(pdf_reader.pages):
            t = page.extract_text()
            if t:
                text += t + "\n"
                
        if not text.strip():
            logging.warning(f"[PDF İZİN HATA] Dosyada okunabilir metin bulunamadı (Taranmış/Resim tabanlı PDF): '{dosya.filename}'")
            return {
                "basarili": False,
                "mesaj": "PDF belgesinde okunabilir metin bulunamadı (Taranmış/Resim tabanlı PDF olabilir). Lütfen bilgileri elle giriniz."
            }

        first_preview = "\n".join([line for line in text.splitlines() if line.strip()][:12])
        logging.info(f"[PDF METİN ÖNİZLEME (İlk Satırlar)]:\n{first_preview}")

        text_clean = VeriAraclari.tr_normalize(text).upper()

        # 1. İzin Türü Tespiti (Öncelik: Tablo İzin Çeşidi / Türü -> Konu Satırı -> Tüm Metin)
        # MEB Ek-1 ve DYS belgelerinde: İznin Çeşidi / İzin Türü / Mazeret Türü satırları
        m_tur_satiri = re.search(
            r'(?:(?:İznin|İzin|Rapor)\s*(?:Çeşidi|Türü|Nedeni|Sebebi|Cinsi|Tipi)|Mazeret\s*(?:Türü|Nedeni|Sebebi))\s*[:=\t]\s*([^\r\n]+)',
            text, re.IGNORECASE
        )
        tur_satir_metni = m_tur_satiri.group(1).strip() if m_tur_satiri else ""
        tur_satir_clean = VeriAraclari.tr_normalize(tur_satir_metni) if tur_satir_metni else ""

        m_konu = re.search(r'Konu\s*:\s*([^\r\n]+)', text, re.IGNORECASE)
        konu_metni = m_konu.group(1).strip() if m_konu else ""
        konu_clean = VeriAraclari.tr_normalize(konu_metni) if konu_metni else ""

        izin_turu = "SAĞLIK"
        mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"

        # Arama Havuzları (Öncelik sırasıyla)
        hedef_kaynaklar = [tur_satir_clean, konu_clean, text_clean]

        for hedef in hedef_kaynaklar:
            if not hedef:
                continue
            if any(k in hedef for k in ["YILLIK"]):
                izin_turu = "YILLIK"
                mevzuat_maddesi = "657 sayılı DMK Madde 102"
                break
            elif any(k in hedef for k in ["MAZERET", "BABALIK", "EVLILIK", "VEFAT", "OLUM", "REFAKAT", "DOGUM", "SUT IZNI", "ENGEL"]):
                izin_turu = "MAZERET"
                mevzuat_maddesi = "657 sayılı DMK Madde 104"
                break
            elif any(k in hedef for k in ["AYLIKSIZ", "UCRETSIZ"]):
                izin_turu = "AYLIKSIZ"
                mevzuat_maddesi = "657 sayılı DMK Madde 108"
                break
            elif any(k in hedef for k in ["IDARI", "GOREV IZNI"]):
                izin_turu = "İDARİ"
                mevzuat_maddesi = "Genel İdari İzin"
                break
            elif any(k in hedef for k in ["HASTALIK", "SAGLIK", "RAPOR", "ISTIRAHAT", "IS GOREMEZLIK", "HEKIM"]):
                izin_turu = "SAĞLIK"
                mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"
                break

        logging.info(f"[PDF İZİN TÜRÜ TESPİTİ] Tür: '{izin_turu}', Mevzuat: '{mevzuat_maddesi}' (Satır: '{tur_satir_metni}', Konu: '{konu_metni}')")

        # 2. Personel Adı Tespiti
        ad_soyad = ""
        kayitli_personeller = []
        try:
            db.cursor.execute("SELECT ad_soyad FROM personel ORDER BY LENGTH(ad_soyad) DESC")
            kayitli_personeller = [r[0] for r in db.cursor.fetchall()]
        except Exception:
            kayitli_personeller = []

        ad_soyad_patterns = [
            # 1. MEB DYS / e-İçişleri satır başlığı kalıpları
            r'(?:Adı\s*(?:ve|/|-)?\s*Soyadı|Ad\s*Soyad)\s*[:=\t]\s*([^\r\n]+)',
            r'(?:Sigortalının|Hasta|İlgilinin|Memurun|Personelin|İzin\s+İsteyenin)\s+Adı\s*(?:ve|/|-)?\s*Soyadı\s*[:=\t]\s*([^\r\n]+)',
            r'G\s*\.\s*S\s*[:=\t]\s*([^\r\n]+)',
            r'Adı\s*[:=\t]\s*([^\r\n]+?)\s+Soyadı\s*[:=\t]\s*([^\r\n]+)',
            # 2. Tablo yapısı (Adı Soyadı başlığı ve bir sonraki satırda isim)
            r'(?:Adı\s*(?:ve|/|-)?\s*Soyadı|Ad\s*Soyad)\s*[:=\t]?\r?\n\s*([A-ZÇÖŞİĞÜa-zçöşiğü\s]{3,45})(?=\r?\n|$)',
            # 3. İkincil SGK / Rapor kalıpları
            r'(?:Sigortalının\s+Adı\s+Soyadı|Hasta\s+Adı\s+Soyadı|İlgilinin\s+Adı\s+Soyadı|Memurun\s+Adı\s+Soyadı)\s*[:=\t]?\s*([^\r\n]+)'
        ]

        for pat in ad_soyad_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                if len(m.groups()) == 2:
                    ham_ad = f"{m.group(1)} {m.group(2)}".strip()
                else:
                    ham_ad = m.group(1).strip()

                # Satırdaki olası ek etiketleri temizle (TC No, Sicil, Parantez içi vb.)
                ham_ad = re.split(r'\s{2,}|\t|(?:\bT\.?C\.?|\bSicil|\bUnvan|\bBranş|\bGörev|\bTC:|\bT\.C\b)', ham_ad)[0].strip()
                ham_ad = re.sub(r'\(.*?\)', '', ham_ad).strip()

                if ham_ad:
                    norm_ham = VeriAraclari.tr_normalize(ham_ad).replace(" ", "")
                    # 1. Tam veya normalize eşitlik
                    for p_ad in kayitli_personeller:
                        norm_p = VeriAraclari.tr_normalize(p_ad).replace(" ", "")
                        if norm_ham == norm_p:
                            ad_soyad = p_ad
                            break
                    # 2. İkinci isim veya kelime kesişimi
                    if not ad_soyad:
                        ham_words = set(VeriAraclari.tr_normalize(ham_ad).split())
                        for p_ad in kayitli_personeller:
                            p_words = set(VeriAraclari.tr_normalize(p_ad).split())
                            if (len(ham_words) >= 2 and len(ham_words & p_words) >= 2) or ham_words.issubset(p_words) or p_words.issubset(ham_words):
                                ad_soyad = p_ad
                                break
                    if not ad_soyad:
                        ad_soyad = ham_ad
                    break

        # 2.1 Konu Satırında Parantez İçi İsim Tespiti (Örn: Konu: Mazeret İzni (Fatma YILMAZ))
        if not ad_soyad and m_konu:
            m_konu_ad = re.search(r'\(([^)]+)\)', konu_metni)
            if m_konu_ad:
                ham_konu_ad = m_konu_ad.group(1).strip()
                norm_konu_ad = VeriAraclari.tr_normalize(ham_konu_ad).replace(" ", "")
                for p_ad in kayitli_personeller:
                    norm_p = VeriAraclari.tr_normalize(p_ad).replace(" ", "")
                    if norm_konu_ad == norm_p:
                        ad_soyad = p_ad
                        break
                if not ad_soyad and len(ham_konu_ad.split()) >= 2:
                    ad_soyad = ham_konu_ad

        # 2.2 Düz Yazı / Olur Metninden İsim Tespiti
        if not ad_soyad:
            prose_patterns = [
                r'(?:Öğretmeni|Öğretmen|Memuru|Memur|Personeli|Personel)\s+([A-ZÇÖŞİĞÜa-zçöşiğü\s]{3,35}?)(?:\'n[ıi]n|\'in|\'un|\'ün|\'a|\'e|\s+adlı|\s+isimli|\s+\d)',
                r'([A-ZÇÖŞİĞÜa-zçöşiğü\s]{3,35}?)(?:\'n[ıi]n|\'in|\'un|\'ün)\s+(?:\d{1,2}[./-]\d{1,2}[./-]\d{4}|\w+\s+tarih|yıllık|mazeret|izin)'
            ]
            for pat in prose_patterns:
                m_prose = re.search(pat, text, re.IGNORECASE)
                if m_prose:
                    ham_prose = m_prose.group(1).strip()
                    norm_prose = VeriAraclari.tr_normalize(ham_prose).replace(" ", "")
                    for p_ad in kayitli_personeller:
                        norm_p = VeriAraclari.tr_normalize(p_ad).replace(" ", "")
                        if norm_prose == norm_p:
                            ad_soyad = p_ad
                            break
                    if not ad_soyad and len(ham_prose.split()) >= 2:
                        ad_soyad = ham_prose
                    if ad_soyad:
                        break

        # 2.3 Belge İçi Güvenli Arama (Müdür / Yetkili ve doktor hariç)
        if not ad_soyad:
            lines = text.split('\n')
            safe_lines = [
                l for l in lines 
                if not any(k in VeriAraclari.tr_normalize(l) for k in [
                    'MUDUR', 'OKUL MUDURU', 'SUBE MUDURU', 'ILCE MILLI', 'DOKTOR', 'UZM. DR', 'BASHEKIM', 'TABIP', 'IMZA', 'ONAYLAYAN'
                ])
            ]
            norm_metin = VeriAraclari.tr_normalize(' '.join(safe_lines))
            for p_ad in kayitli_personeller:
                norm_p = VeriAraclari.tr_normalize(p_ad)
                if norm_p and norm_p in norm_metin:
                    ad_soyad = p_ad
                    break

        logging.info(f"[PDF PERSONEL TESPİTİ] Sonuç: '{ad_soyad}'")

        # 3. İzin Süresi (Gün Sayısı) - MEB Yıllık, Mazeret ve Sağlık kalıpları
        gun_sayisi = 0
        sure_patterns = [
            # 1. Resmi MEB başlıkları: "İznin Süresi : 10", "İzin Süresi : 5 Gün", "Kullanacağı İzin Süresi : 7"
            r'(?:(?:Hastalık|Yıllık|Mazeret|Kullanacağı|Talep\s+Edilen|Verilen)\s+)?(?:İznin|İzin|Rapor)?\s*(?:Süresi|Gün\s+Sayısı)\s*(?:\([^)]*\))?\s*[:=\t]\s*(\d+)',
            # 2. Genel gün sayısı etiketi
            r'G[üu]n\s+Say[ıi]s[ıi]\s*[:=\t]\s*(\d+)',
            r'S[üu]resi\s*[:=\t]\s*(\d+)',
            # 3. Metin içi ifadeler: "10 (on) gün", "7 gün süreyle"
            r'(\d+)\s*\(\s*\w+\s*\)\s*g[üu]n\s*(?:s[üu]reyle)?',
            r'(\d+)\s*g[üu]n\s*(?:s[üu]reyle)?'
        ]
        for pat in sure_patterns:
            m_s = re.search(pat, text, re.IGNORECASE)
            if m_s:
                gun_sayisi = int(m_s.group(1))
                break

        logging.info(f"[PDF GÜN SAYISI TESPİTİ] Sonuç: {gun_sayisi}")

        # 4. Başlangıç Tarihi - MEB Yıllık/Mazeret: "İznin Başlama Tarihi", "Ayrılış Tarihi", "İzne Ayrıldığı Tarih"
        baslangic = ""
        bas_patterns = [
            # 1. MEB İzne Ayrıldığı Tarih (DYS Formları)
            r'(?:İzne\s+)?Ayr[ıi]ld[ıi][ğg][ıi]\s+Tarih\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})',
            # 2. MEB ve SGK tam başlıkları
            r'(?:(?:Raporun|Rapor|İznin|İzin|İzne|İstirahatin|İstirahat)\s+)?(?:Başlangıç|Ayrılış|Başlangıcı|Başlaması)\s*(?:Tarihi)?\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})',
            # 3. Göreve başlama hariç bağımsız Başlama / Ayrılış Tarihi
            r'(?<!G[öo]reve\s)(?<!G[öo]rev\s)(?:Ayrılış|Başlama|Başlangıç)\s+Tarihi\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})',
            # 4. Düz yazı Olur metni: "14/10/2026 tarihinden itibaren / başlayarak"
            r'(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})\s*(?:tarihinden\s+itibaren|tarihinden\s+ge[çc]erli|tarihinden\s+ba[şs]layarak|ba[şs]lamak\s+[üu]zere|tarihli)',
            r'(?:tarihinden|itibaren)\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})'
        ]
        for pat in bas_patterns:
            m_b = re.search(pat, text, re.IGNORECASE)
            if m_b:
                d, m_ay, y = m_b.groups()
                baslangic = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"
                break

        logging.info(f"[PDF BAŞLANGIÇ TARİHİ TESPİTİ] Sonuç: '{baslangic}'")

        # 5. Göreve Başlayacağı Tarih ve Bitiş Tarihi
        bitis = ""
        dt_gorev = None
        m_gorev = re.search(
            r'(?:Göreve\s+Başlayacağı|Göreve\s+Başlama|Görev\s+Başı|İş\s+Başı|İşbaşı)\s*(?:Tarih(?:i)?)?\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})',
            text, re.IGNORECASE
        )
        if m_gorev:
            d, m_ay, y = m_gorev.groups()
            try:
                dt_gorev = datetime(int(y), int(m_ay), int(d))
                dt_bitis = dt_gorev - timedelta(days=1)
                bitis = dt_bitis.strftime("%Y-%m-%d")
            except Exception:
                pass

        if not bitis:
            m_bit = re.search(
                r'(?:(?:Raporun|Rapor|İznin|İzin)\s+)?Biti[şs](?:i)?\s*(?:Tarihi)?\s*[:=\t]?\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})',
                text, re.IGNORECASE
            )
            if m_bit:
                d, m_ay, y = m_bit.groups()
                bitis = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"

        # Süre ve bitiş tarihini çapraz tamamla
        if gun_sayisi <= 0 and baslangic and bitis:
            try:
                d1 = datetime.strptime(baslangic, "%Y-%m-%d")
                d2 = datetime.strptime(bitis, "%Y-%m-%d")
                gun_sayisi = (d2 - d1).days + 1
            except Exception:
                gun_sayisi = 1

        if gun_sayisi > 0 and baslangic and not bitis:
            try:
                d1 = datetime.strptime(baslangic, "%Y-%m-%d")
                d2 = d1 + timedelta(days=gun_sayisi - 1)
                bitis = d2.strftime("%Y-%m-%d")
            except Exception:
                bitis = baslangic

        # Eğer başlangıç okunamadıysa fakat göreve başlama ve gün sayısı biliniyorsa
        if not baslangic and dt_gorev and gun_sayisi > 0:
            baslangic = (dt_gorev - timedelta(days=gun_sayisi)).strftime("%Y-%m-%d")

        # Ters tarih tespiti ve otomatik düzeltme (Bitiş başlangıçtan önce olamaz)
        if baslangic and bitis and bitis < baslangic:
            logging.warning(f"[PDF TARİH TERSLİĞİ DÜZELTİLİYOR] Başlangıç ({baslangic}) bitişten ({bitis}) sonra geldi. Düzeltiliyor.")
            if dt_gorev and gun_sayisi > 0:
                baslangic = (dt_gorev - timedelta(days=gun_sayisi)).strftime("%Y-%m-%d")
                bitis = (dt_gorev - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                baslangic, bitis = bitis, baslangic

        if not bitis and baslangic:
            bitis = baslangic

        logging.info(f"[PDF BİTİŞ VE GÜN] Bitiş: '{bitis}', Gün Sayısı: {gun_sayisi}")

        # 6. İznini Geçireceği Açık Adres
        m_adres = re.search(
            r'(?:İznini|İzni|İzin|Tatil|Bulunacağı|İkametgah)\s*(?:Geçireceği)?\s*(?:Açık)?\s*Adres(?:i)?\s*[:=\t]?\s*([^\r\n]+)',
            text, re.IGNORECASE
        )
        izin_adresi = m_adres.group(1).strip() if m_adres else ""

        # 7. Rapor / İzin Alt Türü / Mazeret Nedeni
        m_rapor_turu = re.search(
            r'(?:Rapor\s*T[üu]r[üu]|İzin\s*Alt\s*T[üu]r[üu]|Mazeret\s*(?:T[üu]r[üu]|Nedeni|Gerek[çc]esi))\s*[:=\t]?\s*([^\r\n]+)',
            text, re.IGNORECASE
        )
        rapor_turu = m_rapor_turu.group(1).strip() if m_rapor_turu else ""
        if rapor_turu:
            rapor_turu = re.sub(r'\s+', ' ', rapor_turu).strip()

        # 8. Belge / Evrak Sayısı
        m_sayi = re.search(r'(?:Sayı|Evrak\s+No|Belge\s+No)\s*[:=\t]\s*([^\r\n]+)', text, re.IGNORECASE)
        belge_no = m_sayi.group(1).strip() if m_sayi else ""

        # Ne ad ne tarih bulunamadıysa uyarı
        if not ad_soyad and not baslangic:
            logging.warning(f"[PDF ÇÖZÜMLEME BAŞARISIZ] Ne personel ne de tarih bulunamadı! Belge metni:\n{text[:500]}...")
            return {
                "basarili": False,
                "mesaj": "PDF belgesinden personel veya izin tarih bilgileri tespit edilemedi. Belge taranmış resim olabilir veya farklı bir formatta düzenlenmiş olabilir. Lütfen bilgileri elle doldurunuz."
            }

        # Kısmi başarı uyarısı
        uyari_notu = ""
        if ad_soyad and not baslangic:
            uyari_notu = "Personel adı tespit edildi fakat izin başlangıç tarihi okunamadı. Lütfen takvimden tarihi seçiniz."
            logging.warning(f"[PDF KISMİ UYARI] {uyari_notu} (Personel: {ad_soyad})")
        elif not ad_soyad and baslangic:
            uyari_notu = "İzin tarihleri tespit edildi fakat personel adı okunamadı. Lütfen personeli seçiniz."
            logging.warning(f"[PDF KISMİ UYARI] {uyari_notu} (Tarih: {baslangic})")

        # Çakışma kontrolü
        if ad_soyad and baslangic:
            cakisan = cakisan_rapor_kontrol(ad_soyad, baslangic, bitis)
            if cakisan:
                c_bas = format_tr_tarih(cakisan["baslangic"])
                c_bit = format_tr_tarih(cakisan["bitis"])
                tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
                tur_adi = cakisan.get("izin_turu", "izin")
                logging.warning(f"[PDF ÇAKIŞMA ENGELİ] {ad_soyad} için {tarih_mesaji} aralığında çakışan {tur_adi} kaydı var.")
                return {
                    "basarili": False,
                    "cakisma": True,
                    "mesaj": f"Bu tarihlerde zaten kayıt var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı bir {tur_adi} bulunmaktadır. Yükleme işleme koyulmadı."
                }

        logging.info(f"=== [PDF İZİN ÇÖZÜMLEME BAŞARILI] Personel: '{ad_soyad}', Tür: '{izin_turu}', Gün: {gun_sayisi}, Başlangıç: '{baslangic}', Bitiş: '{bitis}' ===")
        try:
            islem_logla("bilgi", "PDF İzin Okuma", f"'{dosya.filename}' belgesinden {ad_soyad or 'Personel'} için {izin_turu} izni okundu ({gun_sayisi} gün).")
        except Exception:
            pass

        return {
            "basarili": True,
            "ad_soyad": ad_soyad,
            "izin_turu": izin_turu,
            "mevzuat_maddesi": mevzuat_maddesi,
            "gun_sayisi": max(1, gun_sayisi),
            "baslangic": baslangic,
            "bitis": bitis,
            "izin_adresi": izin_adresi,
            "rapor_turu": rapor_turu,
            "belge_no": belge_no,
            "konu": konu_metni,
            "uyari_notu": uyari_notu
        }
    except Exception as e:
        logging.error(f"[PDF OKUMA HATASI] Dosya: '{dosya.filename}', Hata: {e}", exc_info=True)
        try:
            islem_logla("hata", "PDF İzin Okuma", f"'{dosya.filename}' PDF okuma hatası: {e}")
        except Exception:
            pass
        return {"basarili": False, "mesaj": f"PDF okuma hatası: {str(e)}"}
