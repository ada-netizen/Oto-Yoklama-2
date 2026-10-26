from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class DevamsizlikEkleRequest(BaseModel):
    no: str
    tarih: str
    tur: str
    gun: str

class KayitModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    tarih: Optional[str] = None
    gun: Optional[str] = None
    tarih_duzgun: Optional[str] = None
    gun_str: Optional[str] = None
    tur: str

class PdfVeliFormuRequest(BaseModel):
    no: str
    ad: str
    sube: str
    kayitlar: List[KayitModel]
    ozurlu_str: Optional[str] = "0"
    ozursuz_str: Optional[str] = "0"

class PersonelRequest(BaseModel):
    ad: str
    unvan: Optional[str] = "-"
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = None
    aktif: Optional[int] = 1

class PersonelModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    ad: str
    unvan: Optional[str] = "-"
    gorev: Optional[str] = "-"
    brans: Optional[str] = "-"
    grup: Optional[str] = "-"
    id: Optional[int] = None
    tc_no: Optional[str] = ""
    il_ilce: Optional[str] = ""
    kurum_adi: Optional[str] = ""
    kurum_kodu: Optional[str] = ""
    kurumda_baslama: Optional[str] = ""
    kariyer: Optional[str] = "-"
    kademe_derece: Optional[str] = ""
    ogrenim_durumu: Optional[str] = ""
    cinsiyet: Optional[str] = ""
    kan_grubu: Optional[str] = ""
    dogum_tarihi: Optional[str] = ""
    goreve_baslama: Optional[str] = ""
    olagan_terfi_tarihi: Optional[str] = ""
    kurum_sicil_no: Optional[str] = ""
    emekli_sicil_no: Optional[str] = ""
    arsiv_no: Optional[str] = ""
    telefon: Optional[str] = ""
    eposta: Optional[str] = ""
    notlar: Optional[str] = ""
    aktif: Optional[int] = 1

class PersonelGuncelleRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[int] = None
    ad_soyad: str
    tc_no: Optional[str] = ""
    unvan: Optional[str] = "-"
    brans: Optional[str] = "-"
    gorev: Optional[str] = "-"
    grup: Optional[str] = "Kadrolu"
    il_ilce: Optional[str] = ""
    kurum_adi: Optional[str] = ""
    kurum_kodu: Optional[str] = ""
    kurumda_baslama: Optional[str] = ""
    kariyer: Optional[str] = "-"
    kademe_derece: Optional[str] = ""
    ogrenim_durumu: Optional[str] = ""
    cinsiyet: Optional[str] = ""
    kan_grubu: Optional[str] = ""
    dogum_tarihi: Optional[str] = ""
    goreve_baslama: Optional[str] = ""
    olagan_terfi_tarihi: Optional[str] = ""
    kurum_sicil_no: Optional[str] = ""
    emekli_sicil_no: Optional[str] = ""
    arsiv_no: Optional[str] = ""
    telefon: Optional[str] = ""
    eposta: Optional[str] = ""
    notlar: Optional[str] = ""
    aktif: Optional[int] = 1
    
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
    tarih: Optional[str] = None
    devamsizlik_turu: Optional[str] = None
