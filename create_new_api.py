import os

os.makedirs('routes', exist_ok=True)

ogrenci_code = """
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
"""

with open('routes/ogrenci.py', 'w', encoding='utf-8') as f:
    f.write(ogrenci_code)

sistem_code = """
from fastapi import APIRouter
from dependencies import db, yollar, ayarlar

router = APIRouter(tags=["Sistem"])

@router.get("/ayarlar-getir")
async def ayarlar_getir():
    return ayarlar
"""

with open('routes/sistem.py', 'w', encoding='utf-8') as f:
    f.write(sistem_code)

new_api_code = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import ogrenci, sistem

app = FastAPI(title="Elektronik Okul Sistemi API (Modüler)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ogrenci.router)
app.include_router(sistem.router)

# Diğer routerlar buraya eklenecek
"""

with open('new_api.py', 'w', encoding='utf-8') as f:
    f.write(new_api_code)

print("Created new_api.py and basic routes.")
