from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os, json, re, tempfile, shutil, uuid
import pandas as pd
from datetime import datetime, timedelta
from veritabani import VeritabaniYoneticisi
from sistem_motoru import SistemMotoru
from excel_motoru import ExcelMotoru
from pdf_motoru import PDFYoneticisi
import logging
from araclar import VeriAraclari
from dependencies import db, yollar, ayarlar, islem_logla, create_job, update_job, get_job, GLOBAL_ISLEMLER, islem_durumlari
from utils import *

router = APIRouter()

@router.get("/rapor-esik-siniflar/{format_tipi}")
def rapor_esik_siniflar(format_tipi: str, background_tasks: BackgroundTasks):
    try:
        # Tüm öğrencileri al
        db.cursor.execute("SELECT no, ad_soyad, sube FROM ogrenciler")
        ogrenciler = [{'no': r[0], 'ad_soyad': r[1], 'sube': r[2]} for r in db.cursor.fetchall()]
        
        # Tüm devamsızlıkları al (hafta sonu mantığıyla günleri toplama)
        db.cursor.execute("SELECT no, tur, gun FROM devamsizliklar")
        dev_kayitlar = db.cursor.fetchall()
        
        # Öğrenci başına devamsızlık toplamı
        dev_toplamlari = {o['no']: 0.0 for o in ogrenciler}
        
        # Tur: Özürsüz -> D, Y, SY
        # Tur: Özürlü -> G, I, S, R, M
        # Tur: Diğer -> N, F, SV (bunları saymıyoruz)
        sayilmayacak_turler = ['N', 'F', 'SV']
        
        for no, tur, gun in dev_kayitlar:
            if not tur or tur.upper() in sayilmayacak_turler:
                continue
            
            try:
                gun_mik = float(gun)
            except:
                gun_mik = 0.0
            
            if no in dev_toplamlari:
                dev_toplamlari[no] += gun_mik
                
        # Sınıflara göre grupla
        sinif_verileri = {}
        for ogr in ogrenciler:
            sube = ogr['sube']
            no = ogr['no']
            toplam = dev_toplamlari[no]
            
            if toplam < 5:
                continue 
                
            if sube not in sinif_verileri:
                sinif_verileri[sube] = {'5-14': 0, '15-24': 0, '25-39': 0, '40+': 0}
                
            if 5 <= toplam <= 14.5:
                sinif_verileri[sube]['5-14'] += 1
            elif 15 <= toplam <= 24.5:
                sinif_verileri[sube]['15-24'] += 1
            elif 25 <= toplam <= 39.5:
                sinif_verileri[sube]['25-39'] += 1
            elif toplam >= 40:
                sinif_verileri[sube]['40+'] += 1

        def sinif_sirala(sube_adi):
            import re
            m = re.match(r'(\d+)', sube_adi)
            num = int(m.group(1)) if m else 99
            return (num, sube_adi)
            
        sirali_subeler = sorted(sinif_verileri.keys(), key=sinif_sirala)
        
        import re
        veri_listesi = []
        
        mevcut_kademe = None
        kademe_toplamlari = [0, 0, 0, 0]
        genel_toplamlar = [0, 0, 0, 0]
        
        for sube in sirali_subeler:
            m = re.match(r'(\d+)', sube)
            kademe = int(m.group(1)) if m else 99
            
            if mevcut_kademe is not None and kademe != mevcut_kademe:
                veri_listesi.append([f"{mevcut_kademe}. Sınıflar Toplamı", kademe_toplamlari[0], kademe_toplamlari[1], kademe_toplamlari[2], kademe_toplamlari[3]])
                kademe_toplamlari = [0, 0, 0, 0]
                
            mevcut_kademe = kademe
            v = sinif_verileri[sube]
            veri_listesi.append([sube, v['5-14'], v['15-24'], v['25-39'], v['40+']])
            
            kademe_toplamlari[0] += v['5-14']
            kademe_toplamlari[1] += v['15-24']
            kademe_toplamlari[2] += v['25-39']
            kademe_toplamlari[3] += v['40+']
            
            genel_toplamlar[0] += v['5-14']
            genel_toplamlar[1] += v['15-24']
            genel_toplamlar[2] += v['25-39']
            genel_toplamlar[3] += v['40+']

        if mevcut_kademe is not None:
            veri_listesi.append([f"{mevcut_kademe}. Sınıflar Toplamı", kademe_toplamlari[0], kademe_toplamlari[1], kademe_toplamlari[2], kademe_toplamlari[3]])
            
        veri_listesi.append(["GENEL TOPLAM", genel_toplamlar[0], genel_toplamlar[1], genel_toplamlar[2], genel_toplamlar[3]])

        if not veri_listesi:
            return {"basarili": False, "mesaj": "Bu kritere uygun öğrenci bulunamadı."}

        ana_klasor, ayar = pdf_klasoru_hazirla()
        rapor_klasoru = os.path.join(ana_klasor, "Raporlar")
        if not os.path.exists(rapor_klasoru):
            os.makedirs(rapor_klasoru)

        baslik = "Sınıf Bazlı Devamsızlık Eşik Raporu"
        dosya_adi_temiz = "Sinif_Bazli_Esik_Raporu"
        bugun_str = datetime.now().strftime("%d_%m_%Y_%H%M")
        otomatik_isim = f"{dosya_adi_temiz}_{bugun_str}"
        
        def gorev_esik_raporu():
            try:
                if format_tipi == "excel":
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.xlsx")
                    motor = ExcelMotoru()
                    motor.esik_raporu_excel_ciz(veri_listesi, yol)
                else:
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.pdf")
                    motor = PDFYoneticisi(ayar)
                    motor.esik_raporu_pdf_ciz(veri_listesi, yol)
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Esik raporu cizim hatasi: {e}")

        background_tasks.add_task(gorev_esik_raporu)
        return {"basarili": True, "mesaj": f"Rapor arka planda oluşturuluyor...", "yol": "Raporlar"}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@router.post("/rapor-al")
def rapor_al(veri: RaporAlRequest, background_tasks: BackgroundTasks):
    tur = veri.tur
    format_tipi = veri.format  # "excel" | "pdf"
    ozel_deger = veri.ozel_deger

    basliklar = {
        "ozursuz": "Özürsüz Devamsızlık Sınırını Aşan Öğrenciler (10+ Gün)",
        "ozurlu": "Özürlü Devamsızlık Sınırını Aşan Öğrenciler (20+ Gün)",
        "gun_siniri": f"Özürsüz Devamsızlığı {ozel_deger} Gün ve Üstü Olan Öğrenciler",
        "sube_bazli": f"{ozel_deger} Şubesi Özürsüz Devamsızlık Listesi",
        "tarih_bazli": f"{ozel_deger} Tarihli Özürsüz Devamsızlık Listesi",
    }
    if tur not in basliklar:
        return {"basarili": False, "mesaj": "Geçersiz rapor türü."}

    veri_listesi, hata = _rapor_verisi_hazirla(tur, ozel_deger)
    if hata:
        return {"basarili": False, "mesaj": hata}
    if not veri_listesi:
        return {"basarili": False, "mesaj": "Bu kritere uygun öğrenci bulunamadı."}

    baslik = basliklar[tur]
    kolon4_adi = "Tür" if tur == "tarih_bazli" else "Özürsüz (Gün)"
    excel_kolonlar = ["Sınıf/Şube", "Numara", "Ad Soyad", "Devamsızlık Türü" if tur == "tarih_bazli" else "Özürsüz Toplam (Gün)"]

    ana_klasor, ayar = pdf_klasoru_hazirla()
    rapor_klasoru = os.path.join(ana_klasor, "Raporlar")
    if not os.path.exists(rapor_klasoru):
        os.makedirs(rapor_klasoru)

    dosya_adi_temiz = re.sub(r'[\\/*?:"<>|]', "", baslik).replace(" ", "_")
    bugun_str = datetime.now().strftime("%d_%m_%Y_%H%M")
    otomatik_isim = f"{dosya_adi_temiz}_{bugun_str}"

    try:
        def gorev_rapor():
            try:
                if format_tipi == "excel":
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.xlsx")
                    df = pd.DataFrame(veri_listesi, columns=excel_kolonlar)
                    df.to_excel(yol, index=False)
                else:
                    yol = os.path.join(rapor_klasoru, f"{otomatik_isim}.pdf")
                    motor = PDFYoneticisi(ayar)
                    motor.rapor_ciz(baslik, kolon4_adi, veri_listesi, yol)
                        
                dosyayi_otomatik_ac(yol)
            except Exception as e:
                logging.error(f"Rapor cizim hatasi: {e}")

        background_tasks.add_task(gorev_rapor)
        return {"basarili": True, "mesaj": f"Rapor arka planda oluşturuluyor...", "yol": "Raporlar", "adet": len(veri_listesi)}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@router.get("/gec-bugun-sayisi")
def gec_bugun_sayisi():
    try:
        bugun = datetime.now().strftime("%d/%m/%Y")
        db.cursor.execute("SELECT COUNT(DISTINCT d.no) FROM devamsizliklar d JOIN ogrenciler o ON d.no = o.no WHERE d.tur = 'G' AND d.tarih = ?", (bugun,))
        sayi = db.cursor.fetchone()[0]
        return {"basarili": True, "sayi": sayi}
    except Exception as e:
        return {"basarili": False, "sayi": 0, "mesaj": str(e)}

@router.get("/rapor-gec-bugun")
def rapor_gec_bugun(background_tasks: BackgroundTasks):
    try:
        ayar = ayarlari_al()
        bugun = datetime.now().strftime("%d/%m/%Y")
        
        db.cursor.execute("""
            SELECT o.no, o.ad_soyad, o.sube 
            FROM devamsizliklar d
            JOIN ogrenciler o ON d.no = o.no
            WHERE d.tur = 'G' AND d.tarih = ?
            GROUP BY o.no, o.ad_soyad, o.sube
            ORDER BY o.sube ASC, o.no ASC
        """, (bugun,))
        liste = db.cursor.fetchall()
        
        if not liste:
            return {"basarili": False, "mesaj": "Bugün geç kalan öğrenci bulunamadı."}
            
        kayit_yeri = os.path.join(ayar.get("pdf_kayit_klasoru", yollar["PDF"]), f"Bugun_Gec_Kalanlar_{bugun.replace('/','_')}.pdf")
        
        def pdf_olustur():
            try:
                motor = PDFYoneticisi(ayar)
                motor.gec_kalanlar_pdf_ciz(liste, bugun, kayit_yeri)
                dosyayi_otomatik_ac(kayit_yeri)
            except Exception as e:
                logging.error(f"PDF olusturma hatasi: {e}")
            
        background_tasks.add_task(pdf_olustur)
        return {"basarili": True, "mesaj": "PDF hazırlanıyor..."}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

