from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os, json, re, tempfile, shutil, uuid
import pandas as pd
import PyPDF2
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

@router.post("/pdf-veli-formu")
def pdf_veli_formu_olustur(veri: PdfVeliFormuRequest, background_tasks: BackgroundTasks):
    ana_klasor, ayar = pdf_klasoru_hazirla()
    izin_klasoru = os.path.join(ana_klasor, "İzin Dilekçeleri")
    sube_temiz = str(veri.sube).replace("/", "-").replace("\\", "-").replace(":", "").strip()
    sube_klasoru = os.path.join(izin_klasoru, sube_temiz)
    if not os.path.exists(sube_klasoru):
        os.makedirs(sube_klasoru)

    zaman_damgasi = datetime.now().strftime("%d-%m-%Y_%H%M%S")
    kayit_yeri = os.path.join(sube_klasoru, f"{veri.no}_{veri.ad.replace(' ', '_')}_{zaman_damgasi}.pdf")
    try:
        job_id = str(uuid.uuid4())
        islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "PDF hazırlığı başlatıldı...", "yuzde": 0}
        # Ön yüzden gelen kayıtlarda ham 'tarih'/'gun' alanları var; PDF motoru
        # düzgün biçimlendirilmiş 'tarih_duzgun'/'gun_str' bekliyor. Burada dönüştürüyoruz.
        kayitlar_islenmis = []
        for k in veri.kayitlar:
            k2 = k.model_dump()
            k2['tarih_duzgun'] = k.tarih_duzgun or VeriAraclari.tarih_formatla(k.tarih or '')
            k2['gun_str'] = k.gun_str or VeriAraclari.temiz_sure(k.gun or '')
            kayitlar_islenmis.append(k2)

        def gorev_pdf_olustur():
            try:
                islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "PDF oluşturuluyor...", "yuzde": 50}
                motor = PDFYoneticisi(ayar)
                motor.veli_formu_ciz(veri.no, veri.ad, veri.sube, kayitlar_islenmis, kayit_yeri, veri.ozurlu_str, veri.ozursuz_str)
                dosyayi_otomatik_ac(kayit_yeri)
                islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": "PDF oluşturuldu.", "yuzde": 100, "yol": kayit_yeri}
            except Exception as e:
                logging.error(f"Veli formu cizim hatasi: {e}")
                islem_durumlari[job_id] = {"durum": "hata", "mesaj": f"PDF oluşturulamadı: {e}", "yuzde": 100}

        background_tasks.add_task(gorev_pdf_olustur)
        return {"basarili": True, "mesaj": "PDF işlemi başlatıldı.", "job_id": job_id, "yol": kayit_yeri}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@router.post("/meb-pdf-oku")
def meb_pdf_oku(dosya: UploadFile = File(...)):

    try:
        with gecici_dosya_olustur(dosya, prefix='temp_meb_') as temp_yol:
            with open(temp_yol, "rb") as file:
                ilk_sayfa = PyPDF2.PdfReader(file).pages[0].extract_text()

            # --- TARİH BULMA ---
            tarih = ""
            tarih_match = re.search(r'(?<!\d)(\d{2}[./-]\d{2}[./-]\d{4})(?!\d)', ilk_sayfa)
            if tarih_match:
                tarih = tarih_match.group(1).replace('/', '.').replace('-', '.')
            else:
                tarih_match2 = re.search(r'(?<!\d)(\d{1,2}\s+[A-Za-zğüşöçİĞÜŞÖÇ]+\s+\d{4})(?!\d)', ilk_sayfa)
                if tarih_match2:
                    tarih = tarih_match2.group(1)

            # --- SAYI BULMA ---
            sayi_match = re.search(r'Sayı\s*[:]\s*([^\s]+)', ilk_sayfa, re.IGNORECASE)
            if sayi_match:
                sayi = sayi_match.group(1)
                # Bazen satır sonuna yapışık oluyor, "Konu" gibi kelimelerden temizle
                if "Konu" in sayi:
                    sayi = sayi.split("Konu")[0].strip()
            else:
                sayi = ""

            konu = ""
            konu_match = re.search(r'Konu\s*(?::|\n)(.*?)(?=\nİlgi|\nT\.C\.|\nDAĞITIM|\nOkul ve kurumlarda)', ilk_sayfa, re.DOTALL | re.IGNORECASE)
            if konu_match:
                konu_ham = konu_match.group(1).strip()
                
                # Konu ile İlgi arasında kalan hedef makam adını ayıklama
                lines = konu_ham.split('\n')
                temiz_lines = []
                for line in lines:
                    line_str = line.strip()
                    if not line_str: continue
                    
                    # Kurum hitap kelimelerinden birini içeriyorsa veya satır tamamen büyük harfliyse (min 15 karakter) dur!
                    if re.search(r'(?:MÜDÜRLÜĞÜNE|LİSESİNE|KAYMAKAMLIĞINA|VALİLİĞİNE|BAKANLIĞINA|OKULUNA|MERKEZİNE|BAŞKANLIĞINA|MÜDÜRLÜĞÜ|LİSESİ)\b', line_str, re.IGNORECASE):
                        break
                    if len(line_str) > 15 and line_str.isupper():
                        break
                        
                    temiz_lines.append(line_str)
                
                konu = " ".join(temiz_lines)
                if sayi and sayi in konu:
                    konu = konu.replace(sayi, "").replace(":", "").strip()

            # --- YAZI TEBLİĞİ VE İHALE İÇİN GELDİĞİ YER (KURUM) OCR İLE BULMA ---
            kurum = "Okul Müdürlüğü"
            satirlar = [s.strip() for s in ilk_sayfa.split('\n') if s.strip()]
            
            for i, satir in enumerate(satirlar):
                if 'T.C.' in satir:
                    for j in range(1, 6):
                        if i + j < len(satirlar):
                            aday = satirlar[i + j]
                            # Bitiş şartları
                            if any(x in aday for x in ['Sayı', 'Konu', 'Tarih', 'İletişim', 'Tel:', 'Adres', 'Kep', 'Bu belge', 'Doğrulama', '1 /', '2 /', '3 /', '4 /']):
                                break
                            # Geçerli kurum kelimeleri
                            if any(x in aday for x in ['Müdürlüğü', 'Müdürlügü', 'Lisesi', 'Okulu', 'Bakanlığı', 'Başkanlığı', 'Kurumu', 'Merkezi', 'Enstitüsü', 'Anaokulu', 'Kaymakamlığı', 'Valiliği']):
                                kurum = aday
                    break
                    
            # Baş harflerini büyüt
            def turkce_title(metin):
                if not metin: return ""
                return " ".join([k.capitalize() for k in metin.split()])
            
            kurum = turkce_title(kurum)
            
            if kurum == "Okul Müdürlüğü" or not kurum:
                kurum = ""
            
            if not kurum:
                for satir in satirlar:
                    s_lower = satir.replace('I','ı').replace('İ','i').lower()
                    if s_lower.endswith("ne") or s_lower.endswith("na"):
                        continue
                    if "müdürlü" in s_lower or "kaymakamlı" in s_lower or "valili" in s_lower or "bakanlı" in s_lower or "başkanlı" in s_lower:
                        kurum = satir.replace("lçe", "İlçe").replace("E itim", "Eğitim").replace("Müdürlü ü", "Müdürlüğü").replace("Müdürlüg ü", "Müdürlüğü")
                        kurum = kurum.strip().title()
                        break

            ana_klasor, _ = pdf_klasoru_hazirla()
            gecici_klasor = os.path.join(ana_klasor, "_gecici_meb_yazilari")
            os.makedirs(gecici_klasor, exist_ok=True)

            # Eski geçici MEB yazılarını temizle (24 saatten eski olanları sil)
            try:
                simdi = datetime.now().timestamp()
                for eski_dosya in os.listdir(gecici_klasor):
                    eski_yol = os.path.join(gecici_klasor, eski_dosya)
                    if os.path.isfile(eski_yol) and (simdi - os.path.getmtime(eski_yol)) > 86400:
                        os.remove(eski_yol)
                        logging.info(f"Eski gecici MEB yazisi silindi: {eski_dosya}")
            except Exception as temizlik_hatasi:
                logging.warning(f"Gecici dosya temizleme hatasi: {temizlik_hatasi}")

            kalici_yol = os.path.join(gecici_klasor, f"son_meb_yazisi_{uuid.uuid4().hex[:8]}.pdf")
            shutil.copy(temp_yol, kalici_yol)

            return {"basarili": True, "sayi": sayi, "konu": konu, "tarih": tarih, "kurum": kurum, "gecici_pdf_yolu": kalici_yol}

    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}

@router.post("/teblig-bireysel-pdf")
def teblig_bireysel_pdf(veri: TebligBireyselRequest, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    
    # Yeni klasör yapısını oluştur
    teblig_klasoru = os.path.join(ana_klasor, "Bireysel Tebliğ")
    os.makedirs(teblig_klasoru, exist_ok=True)
    
    yol = os.path.join(teblig_klasoru, f"Bireysel_Teblig_{veri.edilen.ad.replace(' ', '_')}_{datetime.now().strftime('%H%M')}.pdf")
    try:
        yuklenen_pdf = veri.gecici_pdf_yolu
        job_id = str(uuid.uuid4())
        islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "Bireysel tebliğ hazırlığı başlatıldı...", "yuzde": 0}
        
        def gorev_bireysel_teblig():
            try:
                islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Bireysel tebliğ PDF'i oluşturuluyor...", "yuzde": 50}
                motor = PDFYoneticisi(ayar)
                
                # Geldiği yer (kurum) "Müdürlüğü" ile bitmiyorsa ekle
                kurum_adi = veri.kurum.strip() if veri.kurum else ""
                if kurum_adi and not kurum_adi.lower().endswith("müdürlüğü"):
                    kurum_adi += " Müdürlüğü"
                    
                motor.bireysel_teblig_ciz(kurum_adi, veri.sayi, veri.konu, veri.tarih, veri.eden.model_dump(), veri.edilen.model_dump(), veri.yer, veri.teblig_tarihi, veri.teblig_saati, yol, yuklenen_pdf)
                dosyayi_otomatik_ac(yol)
                islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": "Bireysel tebliğ PDF'i oluşturuldu.", "yuzde": 100, "yol": yol}
            except Exception as e:
                logging.error(f"Bireysel teblig cizim hatasi: {e}")
                islem_durumlari[job_id] = {"durum": "hata", "mesaj": f"Bireysel tebliğ oluşturulamadı: {e}", "yuzde": 100}

        background_tasks.add_task(gorev_bireysel_teblig)
        return {"basarili": True, "mesaj": "Bireysel tebliğ işlemi başlatıldı.", "job_id": job_id, "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": str(e)}


@router.post("/teblig-toplu-pdf")
def teblig_toplu_pdf(veri: TebligTopluRequest, background_tasks: BackgroundTasks):
    ayar = ayarlari_al()
    ana_klasor = ayar.get("pdf_kayit_klasoru", yollar["PDF"])
    
    # Yeni klasör yapısını oluştur
    teblig_klasoru = os.path.join(ana_klasor, "Toplu Tebliğ")
    os.makedirs(teblig_klasoru, exist_ok=True)
    
    yol = os.path.join(teblig_klasoru, f"Toplu_Imza_Sirkusu_{datetime.now().strftime('%d_%m_%Y_%H%M')}.pdf")
    try:
        kurum_adi = veri.kurum.strip() if veri.kurum else ""
        if kurum_adi and not kurum_adi.lower().endswith("müdürlüğü"):
            kurum_adi += " Müdürlüğü"
            
        yuklenen_pdf = veri.gecici_pdf_yolu
        personeller_dict = [p.model_dump() for p in veri.personeller]
        job_id = str(uuid.uuid4())
        islem_durumlari[job_id] = {"durum": "basladi", "mesaj": "Toplu tebliğ hazırlığı başlatıldı...", "yuzde": 0}
        
        def gorev_toplu_teblig():
            try:
                islem_durumlari[job_id] = {"durum": "isleniyor", "mesaj": "Toplu tebliğ PDF'i oluşturuluyor...", "yuzde": 50}
                motor = PDFYoneticisi(ayar)
                motor.teblig_tebellug_ciz(veri.sayi, veri.konu, veri.tarih, personeller_dict, yol, kurum_adi, yuklenen_pdf)
                dosyayi_otomatik_ac(yol)
                islem_durumlari[job_id] = {"durum": "tamamlandi", "mesaj": "Toplu tebliğ PDF'i oluşturuldu.", "yuzde": 100, "yol": yol}
            except Exception as e:
                logging.error(f"Toplu teblig cizim hatasi: {e}")
                islem_durumlari[job_id] = {"durum": "hata", "mesaj": f"Toplu tebliğ oluşturulamadı: {e}", "yuzde": 100}

        background_tasks.add_task(gorev_toplu_teblig)
        return {"basarili": True, "mesaj": "Toplu tebliğ işlemi başlatıldı.", "job_id": job_id, "yol": yol}
    except Exception as e:
        return {"basarili": False, "mesaj": f"PDF Hatası: {str(e)}"}



