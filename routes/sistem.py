
from fastapi import APIRouter
from dependencies import db, yollar, ayarlar

router = APIRouter(tags=["Sistem"])

@router.get("/ayarlar-getir")
async def ayarlar_getir():
    return ayarlar
