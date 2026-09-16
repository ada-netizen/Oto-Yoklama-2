
from fastapi import APIRouter
from dependencies import db, islem_logla

router = APIRouter(prefix="/ogrenciler", tags=["Öğrenciler"])

@router.get("/")
async def get_ogrenciler():
    try:
        db.cursor.execute("SELECT no, ad_soyad, sube FROM ogrenciler ORDER BY sube ASC, no ASC")
        ogrenciler = [{'no': r[0], 'ad_soyad': r[1], 'sube': r[2]} for r in db.cursor.fetchall()]
        return {"ogrenciler": ogrenciler}
    except Exception as e:
        return {"ogrenciler": [], "mesaj": str(e)}
