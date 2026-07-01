from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from veritabani import VeritabaniYoneticisi
import os
from sistem_motoru import SistemMotoru

# 1. API Uygulamasını Başlat
app = FastAPI(title="Oto-Yoklama API")

# İleride HTML/JS dosyalarımızın bu API'ye sorunsuz bağlanabilmesi için güvenlik izni (CORS) veriyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Veritabanını Bağla (Sizin yazdığınız motoru kullanıyoruz)
yollar = SistemMotoru.klasorleri_ve_yollari_hazirla()
db = VeritabaniYoneticisi(yollar["DB"])

# 3. İlk Veri Köprüsü (Endpoint)
@app.get("/")
def ana_sayfa():
    return {"mesaj": "Oto-Yoklama API Sistemine Hoş Geldiniz! Motorlar çalışıyor."}

@app.get("/ogrenciler")
def ogrencileri_getir():
    # Eski kodunuzdaki gibi veritabanından verileri çekiyoruz
    ogrenci_listesi, devamsizlik_listesi = db.yukle()
    
    # Veriyi doğrudan web arayüzüne (Frontend'e) gönderiyoruz
    return {
        "ogrenci_sayisi": len(ogrenci_listesi),
        "ogrenciler": ogrenci_listesi
    }

# Sunucuyu çalıştırma kodu
if __name__ == "__main__":
    import uvicorn
    # 8000 portunda yerel sunucuyu başlatır
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)