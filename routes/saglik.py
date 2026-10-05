from fastapi import APIRouter
from veritabani import VeritabaniYoneticisi
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

router = APIRouter()
from dependencies import db

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

@router.post("/saglik/ekle")
def saglik_ekle(veri: SaglikRaporuRequest):
    try:
        bitis = veri.bitis_tarihi if veri.bitis_tarihi else veri.baslangic_tarihi
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
        db.cursor.execute(
            "UPDATE saglik_raporlari SET baslangic_tarihi = ?, bitis_tarihi = ?, gun_sayisi = ?, aciklama = ? WHERE id = ?",
            (veri.baslangic_tarihi, bitis, veri.gun_sayisi, veri.aciklama, id)
        )
        db.conn.commit()
        return {"basarili": True, "mesaj": "Rapor güncellendi."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

