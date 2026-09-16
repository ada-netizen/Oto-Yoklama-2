
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
