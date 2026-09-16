from pydantic import BaseModel
from typing import List, Optional, Dict

class DevamsizlikEkleRequest(BaseModel):
    no: str
    tarih: str
    tur: str
    gun: str

class KayitModel(BaseModel):
    tarih: Optional[str] = None
    gun: Optional[str] = None
    tarih_duzgun: Optional[str] = None
    gun_str: Optional[str] = None
    tur: str
    
    class Config:
        extra = "allow"

class PdfVeliFormuRequest(BaseModel):
    no: str
    ad: str
    sube: str
    kayitlar: List[KayitModel]
    ozurlu_str: Optional[str] = "0"
    ozursuz_str: Optional[str] = "0"

class PersonelRequest(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = None

class PersonelModel(BaseModel):
    ad: str
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = "-"
    
class TebligBireyselRequest(BaseModel):
    kurum: Optional[str] = ""
    sayi: str
    konu: str
    tarih: str
    eden: PersonelModel
    edilen: PersonelModel
    yer: str
    teblig_tarihi: Optional[str] = None
    teblig_saati: Optional[str] = None
    gecici_pdf_yolu: Optional[str] = None

class TebligTopluRequest(BaseModel):
    kurum: Optional[str] = ""
    sayi: str
    konu: str
    tarih: str
    personeller: List[PersonelModel]
    gecici_pdf_yolu: Optional[str] = None

class RaporAlRequest(BaseModel):
    tur: str
    format: str
    ozel_deger: Optional[str] = None
