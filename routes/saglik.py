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

router = APIRouter()
from dependencies import db
from araclar import VeriAraclari
from mevzuat_kurallari import ogretmen_mi, yonetici_mi, PERSONEL_DURUMLARI_REHBERI

class SaglikRaporuRequest(BaseModel):
    personel_ad: str
    baslangic_tarihi: str
    bitis_tarihi: Optional[str] = None
    gun_sayisi: int
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

@router.get("/saglik/liste")
def saglik_liste(yil: Optional[int] = None):
    try:
        hedef_yil = str(yil or datetime.now().year)

        # Personel listesini unvan, grup, brans bilgileriyle alalım
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

        # Seçili yılın tüm izin kayıtlarını alalım
        db.cursor.execute("""
            SELECT personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, COALESCE(izin_turu, 'SAĞLIK') 
            FROM saglik_raporlari 
            WHERE baslangic_tarihi LIKE ? OR bitis_tarihi LIKE ?
        """, (f"{hedef_yil}-%", f"{hedef_yil}-%"))
        raporlar = db.cursor.fetchall()

        # saglik_raporlari tablosunda kaydı olup personel tablosunda yer almayan personelleri de listeye dahil edelim
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

        # Önceden kesilen günleri alalım
        db.cursor.execute("SELECT personel_ad, onceden_kesilen_gun FROM personel_rapor_kesinti")
        kesintiler = {VeriAraclari.tr_normalize(row[0]): row[1] for row in db.cursor.fetchall()}

        sonuc = []
        for p in personel_listesi:
            p_norm = VeriAraclari.tr_normalize(p)
            aylik_gunler = {str(i): 0 for i in range(1, 13)}
            toplam_gun = 0
            saglik_gun = 0
            yillik_gun = 0
            mazeret_gun = 0
            idari_gun = 0
            
            p_raporlar = [r for r in raporlar if VeriAraclari.tr_normalize(r[0]) == p_norm]
            for r in p_raporlar:
                try:
                    ay = str(int(r[1].split("-")[1])) # Extract month as string without leading zero
                except Exception:
                    continue
                gun = r[3]
                tur = (r[4] or "SAĞLIK").upper()
                aylik_gunler[ay] = aylik_gunler.get(ay, 0) + gun
                toplam_gun += gun

                if tur == "SAĞLIK":
                    saglik_gun += gun
                elif tur == "YILLIK":
                    yillik_gun += gun
                elif tur == "MAZERET":
                    mazeret_gun += gun
                else:
                    idari_gun += gun
            
            # 657 SK Md. 152: 7 günü aşan zam ve tazminat kesintisi YALNIZCA sağlık izinlerine uygulanır!
            # Yıllık ve Mazeret izinleri kesinlikle 7 günlük sağlık kesintisine dahil edilmez!
            p_info = personel_bilgi_haritasi.get(p, {})
            is_isci = (p_info.get("grup") == "Sürekli İşçi")
            
            if is_isci:
                # 4/D Sürekli işçide SGK istirahat sistemi geçerlidir
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
                "toplam": toplam_gun,
                "saglik_gun": saglik_gun,
                "yillik_gun": yillik_gun,
                "mazeret_gun": mazeret_gun,
                "idari_gun": idari_gun,
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
            personel_bilgileri[ad] = {
                "unvan": unvan,
                "grup": grup,
                "brans": brans,
                "gorev": gorev,
                "yonetici_mi": yonetici_mi(unvan, gorev),
                "ogretmen_mi": ogretmen_mi(grup, unvan, gorev)
            }

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
        personel_saglik_gunleri = {}

        for row in kayitlar:
            r_id, p_ad, r_bas, r_bit, r_gun, r_acik, r_tur, r_mevzuat, r_belge, r_adres, r_rapor_turu = row
            tur = (r_tur or "SAĞLIK").upper()

            p_info = personel_bilgileri.get(p_ad, {
                "unvan": "", "grup": "Kadrolu", "brans": "", "gorev": "", "yonetici_mi": False, "ogretmen_mi": True
            })

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

            izinli_personeller.add(p_ad)
            toplam_izin_gunu += r_gun
            if tur == "SAĞLIK":
                saglik_gun_toplam += r_gun
                personel_saglik_gunleri[p_ad] = personel_saglik_gunleri.get(p_ad, 0) + r_gun
            elif tur == "YILLIK":
                yillik_gun_toplam += r_gun
            elif tur == "MAZERET":
                mazeret_gun_toplam += r_gun
            else:
                idari_gun_toplam += r_gun

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
                    if not any(x["id"] == r_id and x["personel_ad"] == p_ad for x in takvim_haritasi[key]):
                        takvim_haritasi[key].append({
                            "id": r_id,
                            "personel_ad": p_ad,
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
                "kesinti_siniri_asan": kesinti_siniri_asan
            }
        }
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/saglik/ekle")
def saglik_ekle(veri: SaglikRaporuRequest):
    try:
        bitis = veri.bitis_tarihi if veri.bitis_tarihi else veri.baslangic_tarihi
        cakisan = cakisan_rapor_kontrol(veri.personel_ad, veri.baslangic_tarihi, bitis)
        if cakisan:
            c_bas = format_tr_tarih(cakisan["baslangic"])
            c_bit = format_tr_tarih(cakisan["bitis"])
            tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
            tur_adi = cakisan.get("izin_turu", "izin")
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

        db.cursor.execute(
            """INSERT INTO saglik_raporlari 
               (personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama, izin_turu, mevzuat_maddesi, belge_no, izin_adresi, rapor_turu) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (veri.personel_ad, veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama, izin_turu, mevzuat_maddesi, veri.belge_no or "", veri.izin_adresi or "", veri.rapor_turu or "")
        )
        db.conn.commit()
        return {"basarili": True, "mesaj": f"{izin_turu.capitalize()} kaydı başarıyla eklendi."}
    except Exception as e:
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
                      COALESCE(rapor_turu, '') as rapor_turu
               FROM saglik_raporlari 
               WHERE personel_ad = ? AND (baslangic_tarihi LIKE ? OR bitis_tarihi LIKE ?) 
               ORDER BY baslangic_tarihi DESC""",
            (personel_ad, f"{hedef_yil}-%", f"{hedef_yil}-%")
        )
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
        } for r in db.cursor.fetchall()]
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
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
                
        if not text.strip():
            return {
                "basarili": False,
                "mesaj": "PDF belgesinde okunabilir metin bulunamadı (Taranmış/Resim tabanlı PDF olabilir). Lütfen bilgileri elle giriniz."
            }

        text_clean = text.upper().replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')

        # 1. Konu Alanından İzin Türü Tespiti
        m_konu = re.search(r'Konu\s*:\s*([^\r\n]+)', text, re.IGNORECASE)
        konu_metni = m_konu.group(1).strip() if m_konu else ""
        konu_clean = VeriAraclari.tr_normalize(konu_metni) if konu_metni else ""

        izin_turu = "SAĞLIK"
        mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"

        hedef_ara_metin = konu_clean if konu_clean else text_clean

        if any(k in hedef_ara_metin for k in ["HASTALIK", "SAGLIK", "RAPOR"]):
            izin_turu = "SAĞLIK"
            mevzuat_maddesi = "657 sayılı DMK Madde 105 & 152"
        elif "YILLIK" in hedef_ara_metin:
            izin_turu = "YILLIK"
            mevzuat_maddesi = "657 sayılı DMK Madde 102"
        elif any(k in hedef_ara_metin for k in ["MAZERET", "BABALIK", "EVLILIK", "VEFAT", "OLUM", "REFAKAT", "DOGUM"]):
            izin_turu = "MAZERET"
            mevzuat_maddesi = "657 sayılı DMK Madde 104"
        elif any(k in hedef_ara_metin for k in ["AYLIKSIZ", "UCRETSIZ"]):
            izin_turu = "AYLIKSIZ"
            mevzuat_maddesi = "657 sayılı DMK Madde 108"
        elif any(k in hedef_ara_metin for k in ["IDARI", "GOREV"]):
            izin_turu = "İDARİ"
            mevzuat_maddesi = "Genel İdari İzin"

        # 2. Personel Adı Tespiti
        ad_soyad = ""
        kayitli_personeller = []
        try:
            db.cursor.execute("SELECT ad_soyad FROM personel ORDER BY LENGTH(ad_soyad) DESC")
            kayitli_personeller = [r[0] for r in db.cursor.fetchall()]
        except Exception:
            kayitli_personeller = []

        ad_soyad_patterns = [
            # 1. MEB DYS / e-İçişleri satır başlığı kalıpları (iki nokta, tire, slaş veya tab)
            r'(?:Adı\s*(?:ve|/|-)?\s*Soyadı|Ad\s*Soyad)\s*[:=\t]\s*([^\r\n]+)',
            r'(?:Sigortalının|Hasta|İlgilinin|Memurun)\s+Adı\s*(?:ve|/|-)?\s*Soyadı\s*[:=\t]\s*([^\r\n]+)',
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
                    # 2. İkinci isim veya kızlık soyadı durumu (kelime kesişimi)
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

        # YALNIZCA hiçbir başlık kalıbıyla isim bulunamadıysa (ad_soyad tamamen boşsa) metin araması yap
        # İmzacı yöneticilerin ve doktorların isimlerini hariç tut
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

        # 3. İzin Süresi (Öncelik: "Hastalık İzin Süresi:" / "İzin Süresi:")
        gun_sayisi = 0
        m_sure = re.search(r'(?:Hastalık\s+)?İzin\s+Süresi\s*:\s*(\d+)', text, re.IGNORECASE)
        if m_sure:
            gun_sayisi = int(m_sure.group(1))
        else:
            sure_patterns = [
                r'G[üu]n\s+Say[ıi]s[ıi]\s*:\s*(\d+)',
                r'(\d+)\s*\(\s*\w+\s*\)\s*g[üu]n',
                r'(\d+)\s*g[üu]n'
            ]
            for pat in sure_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    gun_sayisi = int(m.group(1))
                    break

        # 4. Başlangıç Tarihi (Öncelik: "Raporun Başlangıç Tarihi:" / "İznin Başlangıç Tarihi:")
        baslangic = ""
        m_bas = re.search(r'(?:(?:Raporun|İznin)\s+)?Ba[şs]lang[ıi][çc]\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})', text, re.IGNORECASE)
        if m_bas:
            d, m_ay, y = m_bas.groups()
            baslangic = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"
        else:
            bas_patterns = [
                r'(?:[İiIı]stirahat\s+|[İiIı]zin\s+)?Ba[şs]la(?:ma|ng[ıi][çc])\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
                r'(?:Rapor|İzin)\s+Ba[şs]lang[ıi][çc]\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
                r'Ba[şs]lama\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})'
            ]
            for pat in bas_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    d, m_ay, y = m.groups()
                    baslangic = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"
                    break

        # 5. Göreve Başlayacağı Tarih ve Bitiş Tarihi
        bitis = ""
        m_gorev = re.search(r'G[öo]reve\s+Ba[şs]layaca[gğ][ıi]\s+Tarih(?:i)?\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})', text, re.IGNORECASE)
        if m_gorev:
            d, m_ay, y = m_gorev.groups()
            try:
                dt_gorev = datetime(int(y), int(m_ay), int(d))
                dt_bitis = dt_gorev - timedelta(days=1)
                bitis = dt_bitis.strftime("%Y-%m-%d")
            except Exception:
                pass

        if not bitis:
            m_bit = re.search(r'(?:(?:Raporun|İznin)\s+)?Biti[şs]\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})', text, re.IGNORECASE)
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

        if not bitis and baslangic:
            bitis = baslangic

        # 6. İznini Geçireceği Açık Adres
        m_adres = re.search(r'[İiIı]znini\s+Ge[çc]irece[gğ]i\s+(?:A[çc][ıi]k\s+)?Adres\s*:\s*([^\r\n]+)', text, re.IGNORECASE)
        izin_adresi = m_adres.group(1).strip() if m_adres else ""

        # 7. Rapor Türü
        m_rapor_turu = re.search(r'Rapor\s+T[üu]r[üu]\s*:\s*([^\r\n]+)', text, re.IGNORECASE)
        rapor_turu = m_rapor_turu.group(1).strip() if m_rapor_turu else ""

        if not ad_soyad and not baslangic:
            return {
                "basarili": False,
                "mesaj": "PDF belgesinden personel veya izin tarih bilgileri okunamadı. Lütfen formu elle doldurunuz."
            }

        # Çakışma kontrolü
        if ad_soyad and baslangic:
            cakisan = cakisan_rapor_kontrol(ad_soyad, baslangic, bitis)
            if cakisan:
                c_bas = format_tr_tarih(cakisan["baslangic"])
                c_bit = format_tr_tarih(cakisan["bitis"])
                tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
                tur_adi = cakisan.get("izin_turu", "izin")
                return {
                    "basarili": False,
                    "cakisma": True,
                    "mesaj": f"Bu tarihlerde zaten kayıt var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı bir {tur_adi} bulunmaktadır. Yükleme işleme koyulmadı."
                }

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
            "konu": konu_metni
        }
    except Exception as e:
        return {"basarili": False, "mesaj": f"PDF okuma hatası: {str(e)}"}
        return {"basarili": False, "mesaj": f"PDF okuma hatası: {str(e)}"}
