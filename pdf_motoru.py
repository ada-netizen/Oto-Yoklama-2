import os
import io
import re
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm
from PyPDF2 import PdfReader, PdfWriter

class PDFYoneticisi:
    def __init__(self, ayarlar):
        self.ayarlar = ayarlar
        # Türkçe Karakter Destekli Font Ayarları
        try:
            font_yolu = 'arial.ttf'
            kalin_font_yolu = 'arialbd.ttf'
            if os.path.exists('C:/Windows/Fonts/arial.ttf'):
                font_yolu = 'C:/Windows/Fonts/arial.ttf'
                kalin_font_yolu = 'C:/Windows/Fonts/arialbd.ttf'
            pdfmetrics.registerFont(TTFont('ArialTR', font_yolu))
            pdfmetrics.registerFont(TTFont('ArialTR-Bold', kalin_font_yolu))
            self.font = 'ArialTR'
            self.font_bold = 'ArialTR-Bold'
        except:
            self.font = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def metin_duzelt(self, metin):
        # Eğer bilgisayarda Arial yoksa ve Helvetica kullanılıyorsa TR karakterleri düzeltir
        if self.font == 'Helvetica':
            degisim = {'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ç': 'c', 'Ç': 'C', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
            for a, b in degisim.items(): metin = metin.replace(a, b)
        return metin

    def turkce_buyuk_harf(self, metin):
        return str(metin).translate(str.maketrans({"i": "İ", "ı": "I"})).upper()

    def veli_formu_ciz(self, ogrenci_no, ogrenci_ad, kisa_sube, secili_kayitlar, kayit_yeri, ozurlu_str=0, ozursuz_str=0):
        """A5 Boyutunda Resmi Veli Devamsızlık Bildirim Formu Çizer"""
        genislik, yukseklik = 419.53, 595.27 # A5 Boyutu
        pdf_bellek = io.BytesIO()
        c = canvas.Canvas(pdf_bellek, pagesize=(genislik, yukseklik))
        
        # --- 1. BAŞLIK VE LOGOLAR ---
        orta_y = yukseklik - 42.5  
        logo_y = orta_y - 20
        
        meb_logo_yolu = self.ayarlar.get("meb_logosu", "")
        if meb_logo_yolu and os.path.exists(meb_logo_yolu):
            c.drawImage(meb_logo_yolu, 25, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')
            
        okul_logo_yolu = self.ayarlar.get("okul_logosu", "")
        if okul_logo_yolu and os.path.exists(okul_logo_yolu):
            c.drawImage(okul_logo_yolu, genislik - 65, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')

        style_baslik = ParagraphStyle(name='CenterTitle', fontName=self.font_bold, fontSize=10, alignment=TA_CENTER, leading=14)
        okul_adi_metni = self.ayarlar.get("okul_adi", "Okul Adı")
        okul_basligi = self.turkce_buyuk_harf(self.metin_duzelt(okul_adi_metni)) + " MÜDÜRLÜĞÜNE"
        form_basligi = self.turkce_buyuk_harf("Devamsızlık Bilgilendirme Formu")
        c.setFont(self.font_bold, 12)
        c.drawCentredString(genislik / 2, orta_y - 4, form_basligi)

        c.setLineWidth(1)
        c.line(25, yukseklik - 85, genislik - 25, yukseklik - 85)
        
        # --- 2. OKUL BAŞLIĞI VE METİN ---
        okul_baslik_para = Paragraph(okul_basligi, style_baslik)
        okul_baslik_genisligi = genislik - 50
        _, okul_baslik_yuksekligi = okul_baslik_para.wrap(okul_baslik_genisligi, 40)
        okul_baslik_merkezi = yukseklik - 105
        okul_baslik_para.drawOn(
            c,
            25,
            okul_baslik_merkezi - (okul_baslik_yuksekligi / 2)
        )
        
        style_metin = ParagraphStyle(name='JustifyIndent', fontName=self.font, fontSize=10, alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm, leading=14)
        metin_p1 = f"Velisi bulunduğum {ogrenci_no} numaralı, {kisa_sube} sınıfı öğrencisi {ogrenci_ad} aşağıda belirtilen tarihlerde bilgim dahilinde okula devam etmemiştir/etmeyecektir."
        
        p1 = Paragraph(self.metin_duzelt(metin_p1), style_metin)
        p1_genislik, p1_yukseklik = p1.wrapOn(c, genislik - 50, yukseklik) 
        cizgi_y = yukseklik - 85
        okul_baslik_ustu = okul_baslik_merkezi + (okul_baslik_yuksekligi / 2)
        okul_baslik_alti = okul_baslik_merkezi - (okul_baslik_yuksekligi / 2)
        cizgi_okul_boslugu = cizgi_y - okul_baslik_ustu
        p1_ustu = okul_baslik_alti - cizgi_okul_boslugu
        y_p1 = p1_ustu - p1_yukseklik
        p1.drawOn(c, 25, y_p1)

        p2 = Paragraph(self.metin_duzelt("Gereğini bilgilerinize arz ederim."), style_metin)
        p2_genislik, p2_yukseklik = p2.wrapOn(c, genislik - 50, yukseklik)
        y_p2 = y_p1 - p2_yukseklik - 10
        p2.drawOn(c, 25, y_p2) 

        # --- 3. DEVAMSIZLIK TABLOSU ---
        tablo_sol = 40
        tablo_sag = genislik - 40
        sutun_genisligi = (tablo_sag - tablo_sol) / 3
        sutun_merkezleri = [
            tablo_sol + sutun_genisligi * 0.5,
            tablo_sol + sutun_genisligi * 1.5,
            tablo_sol + sutun_genisligi * 2.5,
        ]

        def tablo_basligi_ciz(y, devam=False):
            c.setFont(self.font_bold, 10)
            if devam:
                c.drawCentredString(genislik / 2, y + 25, "DEVAMSIZLIK BİLGİLENDİRME FORMU - DEVAMI")
            c.drawCentredString(sutun_merkezleri[0], y, "Tarih")
            c.drawCentredString(sutun_merkezleri[1], y, self.metin_duzelt("Tür"))
            c.drawCentredString(sutun_merkezleri[2], y, self.metin_duzelt("Süre"))
            c.line(tablo_sol, y - 5, tablo_sag, y - 5)

        def alt_blok_ciz():
            c.setLineWidth(0.5)
            kutu_x_sol = 25
            kutu_x_sag = genislik - 25
            kutu_y_alt = 35
            kutu_y_ust = 110
            orta_x = genislik / 2

            c.rect(kutu_x_sol, kutu_y_alt, kutu_x_sag - kutu_x_sol, kutu_y_ust - kutu_y_alt)
            c.line(orta_x, kutu_y_alt, orta_x, kutu_y_ust)
            satir_yukseklik = (kutu_y_ust - kutu_y_alt) / 3
            c.line(kutu_x_sol, kutu_y_alt + satir_yukseklik, orta_x, kutu_y_alt + satir_yukseklik)
            c.line(kutu_x_sol, kutu_y_alt + 2 * satir_yukseklik, orta_x, kutu_y_alt + 2 * satir_yukseklik)

            def sol_metin_ciz(c_obj, x, y, label, value_str):
                c_obj.setFont(self.font, 9)
                c_obj.drawString(x, y, self.metin_duzelt(label))
                w = c_obj.stringWidth(self.metin_duzelt(label), self.font, 9)
                c_obj.setFont(self.font_bold, 9)
                c_obj.drawString(x + w, y, self.metin_duzelt(f"{value_str} Gün"))

            y_satir3 = kutu_y_alt + (satir_yukseklik * 2.5) - 3
            y_satir2 = kutu_y_alt + (satir_yukseklik * 1.5) - 3
            y_satir1 = kutu_y_alt + (satir_yukseklik * 0.5) - 3
            sol_icerik_x = kutu_x_sol + 10
            sol_metin_ciz(c, sol_icerik_x, y_satir3, "Özürsüz Devamsızlık: ", str(ozursuz_str))
            sol_metin_ciz(c, sol_icerik_x, y_satir2, "Özürlü Devamsızlık: ", str(ozurlu_str))
            sol_metin_ciz(c, sol_icerik_x, y_satir1, "Toplam Devamsızlık: ", str(toplam_hepsi_str))

            c.setFont(self.font, 9)
            bugun = datetime.now().strftime("%d/%m/%Y")
            sag_icerik_x = orta_x + 10
            noktalar = "." * 40
            nokta_genislik = c.stringWidth(noktalar, self.font, 9)
            y_tarih = kutu_y_ust - 15
            y_ad = kutu_y_ust - 35
            y_veli = kutu_y_ust - 50
            y_imza = kutu_y_alt + 10
            x_label = sag_icerik_x
            x_colon = x_label + 45
            x_value = kutu_x_sag - nokta_genislik - 10
            merkez_x_nokta = x_value + (nokta_genislik / 2)
            c.drawCentredString(merkez_x_nokta, y_tarih, f"Tarih: {bugun}")
            c.drawString(x_label, y_ad, "Ad Soyad")
            c.drawString(x_colon, y_ad, ":")
            c.drawString(x_value, y_ad, noktalar)
            c.drawCentredString(merkez_x_nokta, y_veli, "Velisi")
            c.drawString(x_label, y_imza, self.metin_duzelt("İmza"))
            c.drawString(x_colon, y_imza, ":")
            c.drawString(x_value, y_imza, noktalar)
            c.setFont(self.font, 8)
            c.drawString(kutu_x_sol, kutu_y_alt - 15, self.metin_duzelt(
                "Not: Toplam devamsızlık süresi 10 gün özürsüz, 20 gün özürlü olmak üzere 30 gün ile sınırlıdır."
            ))

        try:
            toplam_hepsi = float(ozurlu_str) + float(ozursuz_str)
            toplam_hepsi_str = int(toplam_hepsi) if toplam_hepsi.is_integer() else toplam_hepsi
        except (TypeError, ValueError):
            toplam_hepsi_str = 0

        y_pozisyon = y_p2 - 25
        tablo_basligi_ciz(y_pozisyon)
        y_pozisyon -= 20
        toplam_gun = 0.0
        c.setFont(self.font, 10)
        for kayit_index, kayit in enumerate(secili_kayitlar):
            if y_pozisyon < 135:
                alt_blok_ciz()
                c.showPage()
                c.setLineWidth(1)
                tablo_basligi_ciz(yukseklik - 70)
                c.setFont(self.font, 10)
                y_pozisyon = yukseklik - 90

            c.setFont(self.font, 10)
            c.drawCentredString(sutun_merkezleri[0], y_pozisyon, kayit['tarih_duzgun'])
            c.drawCentredString(sutun_merkezleri[1], y_pozisyon, self.metin_duzelt(kayit['tur']))
            c.drawCentredString(sutun_merkezleri[2], y_pozisyon, str(kayit['gun_str']) + " Gün")
            
            try: toplam_gun += float(kayit['gun_str'])
            except: pass
            y_pozisyon -= 15

        toplam_str = int(toplam_gun) if float(toplam_gun).is_integer() else toplam_gun
        c.line(tablo_sol, y_pozisyon + 10, tablo_sag, y_pozisyon + 10)
        c.setFont(self.font_bold, 10)
        c.drawCentredString(sutun_merkezleri[1], y_pozisyon - 5, "Toplam:")
        c.drawCentredString(sutun_merkezleri[2], y_pozisyon - 5, f"{toplam_str} Gün")
        alt_blok_ciz()

        c.save()
        pdf_bellek.seek(0)
        okuyucu = PdfReader(pdf_bellek)
        toplam_sayfa = len(okuyucu.pages)
        yazici = PdfWriter()

        for sayfa_no, sayfa in enumerate(okuyucu.pages, start=1):
            if toplam_sayfa > 1:
                numara_bellek = io.BytesIO()
                numara_canvas = canvas.Canvas(numara_bellek, pagesize=(genislik, yukseklik))
                numara_canvas.setFont(self.font, 8)
                numara_canvas.drawCentredString(genislik / 2, 8, f"Sayfa {sayfa_no}/{toplam_sayfa}")
                numara_canvas.save()
                numara_bellek.seek(0)
                sayfa.merge_page(PdfReader(numara_bellek).pages[0])
            yazici.add_page(sayfa)

        with open(kayit_yeri, "wb") as hedef:
            yazici.write(hedef)
        return True, ""

    def izin_sablonu_ciz(self, kayit_yeri):
        """A5 Boyutunda Boş İzin Dilekçesi Şablonu Çizer"""
        genislik, yukseklik = 419.53, 595.27 # A5 Boyutu
        pdf_bellek = io.BytesIO()
        c = canvas.Canvas(pdf_bellek, pagesize=(genislik, yukseklik))
        
        orta_y = yukseklik - 42.5  
        logo_y = orta_y - 20
        
        meb_logo_yolu = self.ayarlar.get("meb_logosu", "")
        if meb_logo_yolu and os.path.exists(meb_logo_yolu):
            c.drawImage(meb_logo_yolu, 25, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')
            
        okul_logo_yolu = self.ayarlar.get("okul_logosu", "")
        if okul_logo_yolu and os.path.exists(okul_logo_yolu):
            c.drawImage(okul_logo_yolu, genislik - 65, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')

        style_baslik = ParagraphStyle(name='CenterTitle', fontName=self.font_bold, fontSize=10, alignment=TA_CENTER, leading=14)
        okul_adi_metni = self.ayarlar.get("okul_adi", "Okul Adı")
        okul_basligi = self.turkce_buyuk_harf(self.metin_duzelt(okul_adi_metni)) + " MÜDÜRLÜĞÜNE"
        form_basligi = self.turkce_buyuk_harf("Devamsızlık Bilgilendirme Formu")
        c.setFont(self.font_bold, 12)
        c.drawCentredString(genislik / 2, orta_y - 4, form_basligi)

        c.setLineWidth(1)
        c.line(25, yukseklik - 85, genislik - 25, yukseklik - 85)
        
        okul_baslik_para = Paragraph(okul_basligi, style_baslik)
        okul_baslik_genisligi = genislik - 50
        _, okul_baslik_yuksekligi = okul_baslik_para.wrap(okul_baslik_genisligi, 40)
        okul_baslik_merkezi = yukseklik - 105
        okul_baslik_para.drawOn(
            c,
            25,
            okul_baslik_merkezi - (okul_baslik_yuksekligi / 2)
        )
        
        style_metin = ParagraphStyle(name='JustifyIndent', fontName=self.font, fontSize=10, alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm, leading=14)
        metin_p1 = "Velisi bulunduğum ......... numaralı, ......... sınıfı öğrencisi ....................................... aşağıda belirtilen tarihlerde bilgim dahilinde okula devam etmemiştir/etmeyecektir."
        
        p1 = Paragraph(self.metin_duzelt(metin_p1), style_metin)
        p1_genislik, p1_yukseklik = p1.wrapOn(c, genislik - 50, yukseklik) 
        cizgi_y = yukseklik - 85
        okul_baslik_ustu = okul_baslik_merkezi + (okul_baslik_yuksekligi / 2)
        okul_baslik_alti = okul_baslik_merkezi - (okul_baslik_yuksekligi / 2)
        cizgi_okul_boslugu = cizgi_y - okul_baslik_ustu
        p1_ustu = okul_baslik_alti - cizgi_okul_boslugu
        y_p1 = p1_ustu - p1_yukseklik
        p1.drawOn(c, 25, y_p1)

        p2 = Paragraph(self.metin_duzelt("Gereğini bilgilerinize arz ederim."), style_metin)
        p2_genislik, p2_yukseklik = p2.wrapOn(c, genislik - 50, yukseklik)
        y_p2 = y_p1 - p2_yukseklik - 10
        p2.drawOn(c, 25, y_p2) 

        tablo_sol = 40
        tablo_sag = genislik - 40
        sutun_genisligi = (tablo_sag - tablo_sol) / 3
        sutun_merkezleri = [
            tablo_sol + sutun_genisligi * 0.5,
            tablo_sol + sutun_genisligi * 1.5,
            tablo_sol + sutun_genisligi * 2.5,
        ]

        def tablo_basligi_ciz(y):
            c.setFont(self.font_bold, 10)
            c.drawCentredString(sutun_merkezleri[0], y, "Tarih")
            c.drawCentredString(sutun_merkezleri[1], y, self.metin_duzelt("Tür"))
            c.drawCentredString(sutun_merkezleri[2], y, self.metin_duzelt("Süre"))
            c.line(tablo_sol, y - 5, tablo_sag, y - 5)

        def alt_blok_ciz():
            c.setLineWidth(0.5)
            kutu_x_sol = 25
            kutu_x_sag = genislik - 25
            kutu_y_alt = 35
            kutu_y_ust = 110
            orta_x = genislik / 2

            c.rect(kutu_x_sol, kutu_y_alt, kutu_x_sag - kutu_x_sol, kutu_y_ust - kutu_y_alt)
            c.line(orta_x, kutu_y_alt, orta_x, kutu_y_ust)
            satir_yukseklik = (kutu_y_ust - kutu_y_alt) / 3
            c.line(kutu_x_sol, kutu_y_alt + satir_yukseklik, orta_x, kutu_y_alt + satir_yukseklik)
            c.line(kutu_x_sol, kutu_y_alt + 2 * satir_yukseklik, orta_x, kutu_y_alt + 2 * satir_yukseklik)

            def sol_metin_ciz(c_obj, x, y, label):
                c_obj.setFont(self.font, 9)
                c_obj.drawString(x, y, self.metin_duzelt(label))

            y_satir3 = kutu_y_alt + (satir_yukseklik * 2.5) - 3
            y_satir2 = kutu_y_alt + (satir_yukseklik * 1.5) - 3
            y_satir1 = kutu_y_alt + (satir_yukseklik * 0.5) - 3
            sol_icerik_x = kutu_x_sol + 10
            sol_metin_ciz(c, sol_icerik_x, y_satir3, "Özürsüz Devamsızlık: ......... Gün")
            sol_metin_ciz(c, sol_icerik_x, y_satir2, "Özürlü Devamsızlık: ......... Gün")
            sol_metin_ciz(c, sol_icerik_x, y_satir1, "Toplam Devamsızlık: ......... Gün")

            c.setFont(self.font, 9)
            sag_icerik_x = orta_x + 10
            noktalar = "." * 40
            nokta_genislik = c.stringWidth(noktalar, self.font, 9)
            y_tarih = kutu_y_ust - 15
            y_ad = kutu_y_ust - 35
            y_veli = kutu_y_ust - 50
            y_imza = kutu_y_alt + 10
            x_label = sag_icerik_x
            x_colon = x_label + 45
            x_value = kutu_x_sag - nokta_genislik - 10
            merkez_x_nokta = x_value + (nokta_genislik / 2)
            c.drawCentredString(merkez_x_nokta, y_tarih, "Tarih: ..../..../20...")
            c.drawString(x_label, y_ad, "Ad Soyad")
            c.drawString(x_colon, y_ad, ":")
            c.drawString(x_value, y_ad, noktalar)
            c.drawCentredString(merkez_x_nokta, y_veli, "Velisi")
            c.drawString(x_label, y_imza, self.metin_duzelt("İmza"))
            c.drawString(x_colon, y_imza, ":")
            c.drawString(x_value, y_imza, noktalar)
            c.setFont(self.font, 8)
            c.drawString(kutu_x_sol, kutu_y_alt - 15, self.metin_duzelt(
                "Not: Toplam devamsızlık süresi 10 gün özürsüz, 20 gün özürlü olmak üzere 30 gün ile sınırlıdır."
            ))

        y_pozisyon = y_p2 - 25
        tablo_basligi_ciz(y_pozisyon)
        y_pozisyon -= 20
        c.setFont(self.font, 10)
        
        # 5 adet boş satır çiz
        for i in range(5):
            c.drawCentredString(sutun_merkezleri[0], y_pozisyon, ".......................")
            c.drawCentredString(sutun_merkezleri[1], y_pozisyon, ".......................")
            c.drawCentredString(sutun_merkezleri[2], y_pozisyon, "................")
            y_pozisyon -= 15

        c.line(tablo_sol, y_pozisyon + 10, tablo_sag, y_pozisyon + 10)
        alt_blok_ciz()

        c.save()
        pdf_bellek.seek(0)
        okuyucu = PdfReader(pdf_bellek)
        yazici = PdfWriter()
        yazici.add_page(okuyucu.pages[0])

        with open(kayit_yeri, "wb") as hedef:
            yazici.write(hedef)
        return True, ""
    
    # --- TOPLU İMZA SİRKÜSÜ (A4 LİSTE) ÇİZİM MOTORU ---
    def teblig_tebellug_ciz(self, sayi, konu, tarih, personeller, kayit_yeri, kurum="", yuklenen_pdf=""):
        import os
        import shutil
        import PyPDF2
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

        # 1. TÜRKÇE FONT AYARI
        font_isim = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        if os.path.exists("C:/Windows/Fonts/arial.ttf"):
            pdfmetrics.registerFont(TTFont('Arial_TR', 'C:/Windows/Fonts/arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial_TR_Bold', 'C:/Windows/Fonts/arialbd.ttf'))
            font_isim = 'Arial_TR'
            font_bold = 'Arial_TR_Bold'

        temp_pdf = kayit_yeri.replace(".pdf", "_temp.pdf")
        doc = SimpleDocTemplate(temp_pdf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        # 2. STİLLER (Tablo puntosu 9'a düşürüldü)
        p_style = ParagraphStyle(name='Metin', fontName=font_isim, fontSize=12, leading=14, alignment=TA_JUSTIFY, firstLineIndent=30, spaceAfter=15)
        cell_style = ParagraphStyle(name='Cell', fontName=font_isim, fontSize=9, leading=11)
        cell_bold = ParagraphStyle(name='CellB', fontName=font_bold, fontSize=9, leading=11, alignment=TA_CENTER)

        # 3. KİLİTLİ VE HİZALI LOGOLAR
        meb_logo = self.ayarlar.get("meb_logosu", "")
        okul_logo = self.ayarlar.get("okul_logosu", "")
        
        img_meb = RLImage(meb_logo, width=45, height=45) if meb_logo and os.path.exists(meb_logo) else ""
        img_okul = RLImage(okul_logo, width=45, height=45) if okul_logo and os.path.exists(okul_logo) else ""
        
        okul_adi = self.ayarlar.get("okul_adi", "..................................................")
        okul_adi = self.turkce_buyuk_harf(self.metin_duzelt(okul_adi))
        baslik_metni = f"<font fontName='{font_bold}' size='12'>{okul_adi}<br/><br/>İMZA SİRKÜSÜ</font>"
        baslik_para = Paragraph(baslik_metni, ParagraphStyle(name='Hdr', alignment=TA_CENTER, leading=10))
        
        # A4 tam genişliği (535) kullanılarak logolar kenarlara sıfırlandı
        hdr_table = Table([[img_meb, baslik_para, img_okul]], colWidths=[50, 435, 50])
        hdr_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (2,0), (2,0), 0)
        ]))
        elements.append(hdr_table)
        elements.append(Spacer(1, 15))

        # 4. PARAGRAF METNİ
        kurum = str(kurum).strip()
        if not kurum: 
            kurum = "................................"
        else:
            if not re.search(r"(MÜDÜRLÜĞÜ|MÜDÜRLÜK|OKULU|LİSESİ|ORTAOKULU|İLKOKULU|ANAOKULU|KAYMAKAMLIĞI|VALİLİĞİ|BAŞKANLIĞI)$", kurum, flags=re.IGNORECASE):
                kurum = f"{kurum} Müdürlüğü"
        if not tarih: tarih = "..../..../20.."
        if not sayi: sayi = ".........."
        if not konu: konu = ".............................."
        
        metin = f"{kurum}'nün {tarih} tarih, {sayi} sayı ve {konu} konulu yazısını okudum ve anladım."
        elements.append(Paragraph(metin, p_style))

        # 5. 9 PUNTO LİSTE TABLOSU
        data = [[
            Paragraph("Sıra No", cell_bold), 
            Paragraph("Ad Soyad", cell_bold), 
            Paragraph("İmza", cell_bold),
            Paragraph("İmza Tarihi", cell_bold)
        ]]

        # Alfabetik sıralama (Ad'a göre)
        personeller = sorted(personeller, key=lambda x: self.turkce_buyuk_harf(x.get('ad', '')))

        for i, p in enumerate(personeller):
            data.append([
                Paragraph(str(i+1), cell_style), 
                Paragraph(p.get('ad', ''), cell_style), 
                Paragraph("", cell_style),
                Paragraph("", cell_style)
            ])

        col_widths = [35, 180, 160, 160]
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(t)
        doc.build(elements) 

        # 6. GÜVENLİ PDF BİRLEŞTİRME
        if yuklenen_pdf and os.path.exists(yuklenen_pdf):
            try:
                try:
                    merger = PyPDF2.PdfMerger()
                except AttributeError:
                    merger = PyPDF2.PdfFileMerger()
                
                merger.append(temp_pdf)     
                merger.append(yuklenen_pdf) 
                merger.write(kayit_yeri)
                merger.close()
                if os.path.exists(temp_pdf): os.remove(temp_pdf)
            except Exception as e:
                if os.path.exists(temp_pdf): shutil.move(temp_pdf, kayit_yeri)
                raise Exception(f"Sirkü oluşturuldu ancak MEB yazısı birleştirilemedi: {str(e)}")
        else:
            if os.path.exists(temp_pdf): shutil.move(temp_pdf, kayit_yeri)

            
    # --- GENEL LİSTE RAPORU (Özürsüz/Özürlü/Şube/Tarih Bazlı Raporlar) ---
    def rapor_ciz(self, baslik, kolon4_adi, veri, kayit_yeri):
        """veri: [[sube, no, ad_soyad, deger], ...] şeklinde bir liste bekler."""
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(kayit_yeri, pagesize=A4)
        w, h = A4

        def basligi_ciz():
            c.setFont(self.font_bold, 14)
            c.drawCentredString(w / 2, h - 50, self.metin_duzelt(baslik))
            y = h - 80
            c.setFont(self.font_bold, 10)
            c.drawString(50, y, self.metin_duzelt("Sınıf/Şube"))
            c.drawString(130, y, "No")
            c.drawString(180, y, "Ad Soyad")
            c.drawString(450, y, self.metin_duzelt(kolon4_adi))
            c.line(40, y - 5, w - 40, y - 5)
            return y - 20

        y_pos = basligi_ciz()
        c.setFont(self.font, 10)
        for satir in veri:
            if y_pos < 50:
                c.showPage()
                y_pos = basligi_ciz()
                c.setFont(self.font, 10)
            c.drawString(50, y_pos, self.metin_duzelt(str(satir[0])))
            c.drawString(130, y_pos, str(satir[1]))
            c.drawString(180, y_pos, self.metin_duzelt(str(satir[2])))
            c.drawString(450, y_pos, str(satir[3]))
            y_pos -= 15

        c.save()
        return True, ""

    def personel_raporu_ciz(self, veri, kayit_yeri):
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(kayit_yeri, pagesize=A4)
        w, h = A4

        def basligi_ciz():
            c.setFont(self.font_bold, 14)
            c.drawCentredString(w / 2, h - 50, self.metin_duzelt("Personel Listesi"))
            y = h - 80
            c.setFont(self.font_bold, 10)
            c.drawString(50, y, "Ad Soyad")
            c.drawString(200, y, self.metin_duzelt("Branş"))
            c.drawString(350, y, self.metin_duzelt("Görev"))
            c.drawString(450, y, "Grup")
            c.line(40, y - 5, w - 40, y - 5)
            return y - 20

        y_pos = basligi_ciz()
        c.setFont(self.font, 10)
        for satir in veri:
            if y_pos < 50:
                c.showPage()
                y_pos = basligi_ciz()
                c.setFont(self.font, 10)
            
            c.drawString(50, y_pos, self.metin_duzelt(str(satir[0])))
            c.drawString(200, y_pos, self.metin_duzelt(str(satir[1])))
            c.drawString(350, y_pos, self.metin_duzelt(str(satir[2])))
            c.drawString(450, y_pos, self.metin_duzelt(str(satir[3])))
            y_pos -= 15

        c.save()
        return True, ""

    def esik_raporu_pdf_ciz(self, veri, kayit_yeri):
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(kayit_yeri, pagesize=A4)
        w, h = A4

        def basligi_ciz():
            c.setFont(self.font_bold, 14)
            c.drawCentredString(w / 2, h - 50, self.metin_duzelt("Sınıf Bazlı Devamsızlık Eşik Raporu"))
            y = h - 80
            c.setFont(self.font_bold, 10)
            c.drawString(50, y, self.metin_duzelt("Sınıf/Şube"))
            c.drawString(150, y, "5-14 Gün")
            c.drawString(250, y, "15-24 Gün")
            c.drawString(350, y, "25-39 Gün")
            c.drawString(450, y, "40+ Gün")
            c.line(40, y - 5, w - 40, y - 5)
            return y - 20

        y_pos = basligi_ciz()
        for satir in veri:
            if y_pos < 50:
                c.showPage()
                y_pos = basligi_ciz()
            
            sube = self.metin_duzelt(str(satir[0]))
            
            # Check if this is a subtotal or grand total row
            if "Toplam" in sube or "TOPLAM" in sube:
                c.setFont(self.font_bold, 10)
                # Background highlight for totals
                c.setFillColorRGB(0.9, 0.9, 0.9)
                c.rect(40, y_pos - 2, w - 80, 15, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
                c.line(40, y_pos - 4, w - 40, y_pos - 4) # underline totals
            else:
                c.setFont(self.font, 10)
            
            c.drawString(50, y_pos, sube)
            c.drawString(150, y_pos, str(satir[1]))
            c.drawString(250, y_pos, str(satir[2]))
            c.drawString(350, y_pos, str(satir[3]))
            c.drawString(450, y_pos, str(satir[4]))
        c.save()
        return True, ""

    def bireysel_teblig_ciz(self, kurum, sayi, konu, yazi_tarihi, t_eden, t_edilen, t_yeri, teblig_tarihi, teblig_saati, kayit_yeri, yuklenen_pdf=None):
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from datetime import datetime
        import io
        import re
        
        kurum = str(kurum).strip()
        if not kurum:
            kurum = "................................"
        else:
            if not re.search(r"(MÜDÜRLÜĞÜ|MÜDÜRLÜK|OKULU|LİSESİ|ORTAOKULU|İLKOKULU|ANAOKULU|KAYMAKAMLIĞI|VALİLİĞİ|BAŞKANLIĞI)$", kurum, flags=re.IGNORECASE):
                kurum = f"{kurum} Müdürlüğü"
        
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("Lütfen terminale 'pip install PyPDF2' yazıp kütüphaneyi yükleyin.")
            
        genislik, yukseklik = A4
        
        # A5 Makbuzunu diske değil, bilgisayarın "Geçici Hafızasına (RAM)" çiziyoruz
        temp_pdf = io.BytesIO()
        c = canvas.Canvas(temp_pdf, pagesize=A4)
        if teblig_tarihi:
            bugun = teblig_tarihi
        else:
            bugun = datetime.now().strftime("%d/%m/%Y")
            
        if teblig_saati:
            saat_str = f" - {teblig_saati}"
        else:
            saat_str = ""
        
        def turkce_title(metin):
            if not metin: return ""
            kucuk_harfler = metin.replace('I', 'ı').replace('İ', 'i').lower()
            kelimeler = kucuk_harfler.split()
            sonuc = []
            for k in kelimeler:
                ilk_harf = k[0].replace('i', 'İ').replace('ı', 'I').upper() if k[0] in ['i', 'ı'] else k[0].upper()
                sonuc.append(ilk_harf + k[1:])
            return " ".join(sonuc)

        style_n = ParagraphStyle(name='N', fontName=self.font, fontSize=11, leading=14)
        style_c = ParagraphStyle(name='C', fontName=self.font, fontSize=11, leading=14, alignment=1)
        style_cb = ParagraphStyle(name='CB', fontName=self.font_bold, fontSize=11, leading=14, alignment=1)
        
        # ================= 2 ADET A5 (ÜST VE ALT) ÇİZİMİ =================
        def a5_belge_ciz(y_offset):
            baslangic_y = y_offset + 370
            
            c.setFont(self.font_bold, 14)
            c.drawCentredString(genislik / 2, baslangic_y, self.metin_duzelt("TEBLİĞ - TEBELLÜĞ BELGESİ"))
            
            data = [
                [Paragraph(self.metin_duzelt("TEBLİĞ YAPILACAK<br/>BELGENİN TARİHİ VE SAYISI"), style_n), Paragraph(self.metin_duzelt(f"{kurum}'nün {yazi_tarihi} tarih ve {sayi} sayılı yazısı."), style_n)],
                [Paragraph(self.metin_duzelt("YAZININ ÖZÜ"), style_n), Paragraph(self.metin_duzelt(konu), style_n)],
                [Paragraph(self.metin_duzelt("TEBLİĞ EDİLDİĞİ YER"), style_n), Paragraph(self.metin_duzelt(f"{t_yeri}"), style_n)],
                [Paragraph(self.metin_duzelt("TEBLİĞ TARİHİ VE SAATİ"), style_n), Paragraph(self.metin_duzelt(f"{bugun}{saat_str}"), style_n)],
                [[Paragraph(self.metin_duzelt("TEBLİĞ EDEN"), style_cb),
                  Paragraph(self.metin_duzelt(f"<br/><br/>İmza<br/>{t_eden['ad']}<br/>{t_eden['gorev']}"), style_c)],
                 [Paragraph(self.metin_duzelt("TEBELLÜĞ EDEN"), style_cb),
                  Paragraph(self.metin_duzelt(f"<br/><br/>İmza<br/>{t_edilen['ad']}<br/>{t_edilen['gorev']}"), style_c)]]
            ]
            
            col_widths = [genislik * 0.4, genislik * 0.5]
            
            t = Table(data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,3), 1, colors.black),
                ('BOX', (0,4), (-1,4), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBEFORE', (1,4), (1,4), 1, colors.black),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 8),
            ]))
            
            t.wrapOn(c, genislik, yukseklik)
            t_width, t_height = t.wrap(genislik, yukseklik)
            
            x = (genislik - t_width) / 2
            y = baslangic_y - 15 - t_height
            t.drawOn(c, x, y)
            
            if y_offset > 0:
                c.setDash(6, 4)
                c.line(0, yukseklik/2, genislik, yukseklik/2)
                c.setDash(1, 0)
                
        a5_belge_ciz(yukseklik / 2) # Sayfanın Üstü
        a5_belge_ciz(0)             # Sayfanın Altı
        c.save()
        temp_pdf.seek(0)

        # Eğer birleştirilecek orijinal bir DYS yazısı (PDF) verilmemişse,
        # sadece RAM'de hazırlanan makbuzu doğrudan diske yazarız.
        if not yuklenen_pdf or not os.path.exists(yuklenen_pdf):
            with open(kayit_yeri, "wb") as f_out:
                f_out.write(temp_pdf.getvalue())
            return True, ""

        # ================= PDF'LERİ BİRLEŞTİRME MUCİZESİ =================
        merger = PyPDF2.PdfMerger()

        # 1. Önce bizim RAM'de hazırladığımız Makaslı A5 Makbuzunu (Tebliğ Belgesi) ekler
        merger.append(temp_pdf)

        # 2. Sonra klasöre gidip senin seçtiğin DYS Orijinal Resmi Yazısını (PDF) arkasına ekler
        merger.append(yuklenen_pdf)

        # 3. Sonuç olarak ikisini tek bir PDF dosyası olarak kaydeder!
        with open(kayit_yeri, "wb") as f_out:
            merger.write(f_out)

        merger.close()
        return True, ""

    def gec_kalanlar_pdf_ciz(self, liste, bugun, kayit_yeri):
        from reportlab.pdfgen import canvas
        import re

        def sinif_formatla(orj):
            if not orj: return "-"
            s = str(orj)
            s = re.sub(r'\(.*?\)', '', s)
            for w in ['Sınıfı', 'Sınıf', 'Şubesi', 'sınıfı', 'sınıf', 'şubesi']:
                s = s.replace(w, '')
            s = s.replace(' ', '').replace('.', '').replace(',', '')
            return s.replace('/', '').upper() 

        def formatli_sube(orj):
            s = sinif_formatla(orj)
            if len(s) >= 2 and not '/' in s:
                match = re.match(r"(\d+)(.*)", s)
                if match:
                    return f"{match.group(1)}/{match.group(2)}"
            return s

        try:
            font_isim = self.font
            font_kalin = self.font_bold
            baslik = f"{bugun} Tarihli Geç (G) Kalan Öğrenciler Listesi"
            sutun3 = "Sınıf/Şube"
        except:
            font_isim = 'Helvetica'
            font_kalin = 'Helvetica-Bold'
            baslik = f"{bugun} Tarihli Gec (G) Kalan Ogrenciler Listesi"
            sutun3 = "Sinif/Sube"

        c = canvas.Canvas(kayit_yeri)
        c.setFont(font_kalin, 16)
        c.drawCentredString(300, 800, self.metin_duzelt(baslik))
        
        y = 750
        c.setFont(font_kalin, 12)
        c.drawString(50, y, "Numara")
        c.drawString(150, y, "Ad Soyad")
        c.drawString(450, y, self.metin_duzelt(sutun3))
        c.line(50, y - 5, 550, y - 5)
        
        c.setFont(font_isim, 11)
        y -= 25
        for row in liste:
            ogr_no, ad_soyad, sube_raw = row
            sube = formatli_sube(sube_raw)
            c.drawString(50, y, str(ogr_no))
            c.drawString(150, y, self.metin_duzelt(str(ad_soyad)))
            c.drawString(450, y, self.metin_duzelt(str(sube)))
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont(font_isim, 11)
                y = 800
                
        c.save()
        return True, ""
