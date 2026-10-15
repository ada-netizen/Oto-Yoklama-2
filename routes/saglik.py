from fastapi import APIRouter
from veritabani import VeritabaniYoneticisi
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

router = APIRouter()
from dependencies import db
from araclar import VeriAraclari

class SaglikRaporuRequest(BaseModel):
    personel_ad: str
    baslangic_tarihi: str
    bitis_tarihi: Optional[str] = None
    gun_sayisi: int
    aciklama: Optional[str] = ""

class KesintiRequest(BaseModel):
    personel_ad: str
    onceden_kesilen: int

@router.get("/saglik/liste")
def saglik_liste():
    try:
        # Get all personnel
        db.cursor.execute("SELECT ad_soyad FROM personel ORDER BY ad_soyad")
        personel_listesi = [row[0] for row in db.cursor.fetchall()]

        # Get all health reports for the current year
        current_year = str(datetime.now().year)
        
        db.cursor.execute("SELECT personel_ad, baslangic_tarihi, gun_sayisi FROM saglik_raporlari WHERE baslangic_tarihi LIKE ?", (f"{current_year}-%",))
        raporlar = db.cursor.fetchall()
        
        # Get deductions
        db.cursor.execute("SELECT personel_ad, onceden_kesilen_gun FROM personel_rapor_kesinti")
        kesintiler = {row[0]: row[1] for row in db.cursor.fetchall()}

        sonuc = []
        for p in personel_listesi:
            aylik_gunler = {str(i): 0 for i in range(1, 13)}
            toplam_gun = 0
            
            p_raporlar = [r for r in raporlar if r[0] == p]
            for r in p_raporlar:
                ay = str(int(r[1].split("-")[1])) # Extract month as string without leading zero
                gun = r[2]
                aylik_gunler[ay] += gun
                toplam_gun += gun
            
            yedi_gecen = max(0, toplam_gun - 7)
            onceden_kesilen = kesintiler.get(p, 0)
            yeni_kesinti = max(0, yedi_gecen - onceden_kesilen)
            
            sonuc.append({
                "personel_ad": p,
                "aylar": aylik_gunler,
                "toplam": toplam_gun,
                "yedi_gecen": yedi_gecen,
                "onceden_kesilen": onceden_kesilen,
                "yeni_kesinti": yeni_kesinti
            })

        return {"basarili": True, "veri": sonuc}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

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
            SELECT id, personel_ad, baslangic_tarihi, COALESCE(NULLIF(bitis_tarihi, ''), baslangic_tarihi) as bitis, gun_sayisi, aciklama
            FROM saglik_raporlari
            WHERE baslangic_tarihi <= ?
              AND COALESCE(NULLIF(bitis_tarihi, ''), baslangic_tarihi) >= ?
            """,
            (bitis, baslangic)
        )
        rows = db.cursor.fetchall()
        
        target_norm = VeriAraclari.tr_normalize(personel_ad)
        for r in rows:
            r_id, r_ad, r_bas, r_bit, r_gun, r_acik = r
            if haric_id is not None and r_id == haric_id:
                continue
            if r_ad == personel_ad or VeriAraclari.tr_normalize(r_ad) == target_norm:
                return {
                    "id": r_id,
                    "personel_ad": r_ad,
                    "baslangic": r_bas,
                    "bitis": r_bit,
                    "gun_sayisi": r_gun,
                    "aciklama": r_acik
                }
    except Exception:
        pass
        
    return None

@router.post("/saglik/ekle")
def saglik_ekle(veri: SaglikRaporuRequest):
    try:
        bitis = veri.bitis_tarihi if veri.bitis_tarihi else veri.baslangic_tarihi
        cakisan = cakisan_rapor_kontrol(veri.personel_ad, veri.baslangic_tarihi, bitis)
        if cakisan:
            c_bas = format_tr_tarih(cakisan["baslangic"])
            c_bit = format_tr_tarih(cakisan["bitis"])
            tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
            return {
                "basarili": False,
                "cakisma": True,
                "mesaj": f"Bu tarihlerde zaten rapor girişi var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı bir sağlık raporu bulunmaktadır. Yeni rapor eklenemez."
            }

        db.cursor.execute(
            "INSERT INTO saglik_raporlari (personel_ad, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama) VALUES (?, ?, ?, ?, ?)",
            (veri.personel_ad, veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama)
        )
        db.conn.commit()
        return {"basarili": True, "mesaj": "Rapor eklendi."}
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
        return {"basarili": True, "mesaj": "Rapor silindi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.get("/saglik/raporlar/{personel_ad}")
def personel_raporlari(personel_ad: str):
    try:
        current_year = str(datetime.now().year)
        db.cursor.execute(
            "SELECT id, baslangic_tarihi, bitis_tarihi, gun_sayisi, aciklama FROM saglik_raporlari WHERE personel_ad = ? AND baslangic_tarihi LIKE ? ORDER BY baslangic_tarihi DESC",
            (personel_ad, f"{current_year}-%")
        )
        raporlar = [{"id": r[0], "baslangic": r[1], "bitis": r[2], "gun": r[3], "aciklama": r[4]} for r in db.cursor.fetchall()]
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
            return {
                "basarili": False,
                "cakisma": True,
                "mesaj": f"Bu tarihlerde zaten rapor girişi var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı başka bir sağlık raporu bulunmaktadır."
            }

        db.cursor.execute(
            "UPDATE saglik_raporlari SET baslangic_tarihi = ?, bitis_tarihi = ?, gun_sayisi = ?, aciklama = ? WHERE id = ?",
            (veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama, id)
        )
        db.conn.commit()
        return {"basarili": True, "mesaj": "Rapor güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


import io
import PyPDF2
from datetime import datetime, timedelta
import re
from fastapi import File, UploadFile, HTTPException

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

        # 1. Personel Adı Eşleştirme
        ad_soyad = ""
        # Öncelik 1: Sistemdeki kayıtlı personelleri tarayalım
        try:
            db.cursor.execute("SELECT ad_soyad FROM personel ORDER BY LENGTH(ad_soyad) DESC")
            kayitli_personeller = [r[0] for r in db.cursor.fetchall()]
        except Exception:
            kayitli_personeller = []

        text_upper = text.upper().replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
        for p_ad in kayitli_personeller:
            p_clean = p_ad.upper().replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
            if p_clean in text_upper:
                ad_soyad = p_ad
                break

        # Öncelik 2: Regex ile arama
        if not ad_soyad:
            ad_soyad_patterns = [
                r'G\s*\.\s*S\s*:\s*([\w\sÇÖŞİĞÜçöşiğü]+?)(?=\s+Tarih|\s+TC|\s+T\.C|\n|\r|$)',
                r'(?:Sigortalının\s+Adı\s+Soyadı|Adı\s+Soyadı|Hasta\s+Adı\s+Soyadı|Adı\s+ve\s+Soyadı)\s*:\s*([\w\sÇÖŞİĞÜçöşiğü]+?)(?=\s+Tarih|\s+TC|\s+T\.C|\n|\r|$)',
                r'Adı\s*:\s*([\w\sÇÖŞİĞÜçöşiğü]+?)\s+Soyadı\s*:\s*([\w\sÇÖŞİĞÜçöşiğü]+?)(?=\n|\r|$)'
            ]
            for pat in ad_soyad_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    if len(m.groups()) == 2:
                        ad_soyad = f"{m.group(1)} {m.group(2)}".strip()
                    else:
                        ad_soyad = m.group(1).strip()
                    break

        # 2. Başlangıç Tarihi
        baslangic = ""
        bas_patterns = [
            r'(?:[İiIı]stirahat\s+)?Ba[şs]la(?:ma|ng[ıi][çc])\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
            r'Rapor\s+Ba[şs]lang[ıi][çc]\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
            r'Ba[şs]lama\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})'
        ]
        for pat in bas_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                d, m_ay, y = m.groups()
                baslangic = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"
                break

        # 3. Bitiş Tarihi
        bitis = ""
        bit_patterns = [
            r'(?:[İiIı]stirahat\s+)?Biti[şs]\s+Tarihi\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
            r'Rapor\s+Biti[şs]\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})'
        ]
        for pat in bit_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                d, m_ay, y = m.groups()
                bitis = f"{y}-{m_ay.zfill(2)}-{d.zfill(2)}"
                break

        # Eğer doğrudan bitiş yoksa göreve başlama tarihinden bir önceki gün bitiş kabul edilir
        if not bitis:
            m_gorev = re.search(r'(?:[Gg][öo]reve\s+Ba[şs]lama|[Ççc]al[ıi][şs]abilece[gğ]i)\s+Tarih(?:i)?\s*:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})', text, re.IGNORECASE)
            if m_gorev:
                d, m_ay, y = m_gorev.groups()
                try:
                    dt_gorev = datetime(int(y), int(m_ay), int(d))
                    dt_bitis = dt_gorev - timedelta(days=1)
                    bitis = dt_bitis.strftime("%Y-%m-%d")
                except Exception:
                    pass

        # 4. Gün Sayısı
        gun_sayisi = 0
        sure_patterns = [
            r'(?:[İiIı]stirahat\s+)?S[üu]resi\s*:\s*(\d+)',
            r'G[üu]n\s+Say[ıi]s[ıi]\s*:\s*(\d+)',
            r'(\d+)\s*\(\s*\w+\s*\)\s*g[üu]n'
        ]
        for pat in sure_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                gun_sayisi = int(m.group(1))
                break

        # Gün sayısı bulunamadıysa tarihlerden hesaplayalım
        if gun_sayisi <= 0 and baslangic and bitis:
            try:
                d1 = datetime.strptime(baslangic, "%Y-%m-%d")
                d2 = datetime.strptime(bitis, "%Y-%m-%d")
                gun_sayisi = (d2 - d1).days + 1
            except Exception:
                gun_sayisi = 1

        # Eğer gün sayısı var ama bitiş tarihi yoksa
        if gun_sayisi > 0 and baslangic and not bitis:
            try:
                d1 = datetime.strptime(baslangic, "%Y-%m-%d")
                d2 = d1 + timedelta(days=gun_sayisi - 1)
                bitis = d2.strftime("%Y-%m-%d")
            except Exception:
                bitis = baslangic

        if not bitis and baslangic:
            bitis = baslangic

        if not ad_soyad and not baslangic:
            return {
                "basarili": False,
                "mesaj": "PDF'ten sağlık raporuna ait personel veya tarih bilgileri okunamadı. Lütfen formu elle doldurunuz."
            }

        # Çakışma kontrolü (aynı veya çakışan tarihlerde rapor var mı?)
        if ad_soyad and baslangic:
            cakisan = cakisan_rapor_kontrol(ad_soyad, baslangic, bitis)
            if cakisan:
                c_bas = format_tr_tarih(cakisan["baslangic"])
                c_bit = format_tr_tarih(cakisan["bitis"])
                tarih_mesaji = c_bas if c_bas == c_bit else f"{c_bas} - {c_bit}"
                return {
                    "basarili": False,
                    "cakisma": True,
                    "mesaj": f"Bu tarihlerde zaten rapor girişi var! {cakisan['personel_ad']} için {tarih_mesaji} tarihlerinde kayıtlı bir sağlık raporu bulunmaktadır. Yükleme işleme koyulmadı."
                }

        return {
            "basarili": True,
            "ad_soyad": ad_soyad,
            "gun_sayisi": max(1, gun_sayisi),
            "baslangic": baslangic,
            "bitis": bitis
        }
    except Exception as e:
        return {"basarili": False, "mesaj": f"PDF okuma hatası: {str(e)}"}
