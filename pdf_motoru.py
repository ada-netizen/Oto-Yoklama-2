import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm

class PDFYoneticisi:
    def __init__(self, ayarlar):
        self.ayarlar = ayarlar
        # Türkçe Karakter Destekli Font Ayarları
        try:
            pdfmetrics.registerFont(TTFont('ArialTR', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('ArialTR-Bold', 'arialbd.ttf'))
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

    def veli_formu_ciz(self, ogrenci_no, ogrenci_ad, kisa_sube, secili_kayitlar, kayit_yeri):
        """A5 Boyutunda Resmi Veli Devamsızlık Bildirim Formu Çizer"""
        genislik, yukseklik = 419.53, 595.27 # A5 Boyutu
        c = canvas.Canvas(kayit_yeri, pagesize=(genislik, yukseklik))
        
        # --- 1. BAŞLIK VE LOGOLAR ---
        orta_y = yukseklik - 42.5  
        logo_y = orta_y - 20
        
        meb_logo_yolu = self.ayarlar.get("meb_logosu", "")
        if meb_logo_yolu and os.path.exists(meb_logo_yolu):
            c.drawImage(meb_logo_yolu, 25, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')
            
        okul_logo_yolu = self.ayarlar.get("okul_logosu", "")
        if okul_logo_yolu and os.path.exists(okul_logo_yolu):
            c.drawImage(okul_logo_yolu, genislik - 65, logo_y, width=40, height=40, preserveAspectRatio=True, mask='auto')

        style_baslik = ParagraphStyle(name='CenterTitle', fontName=self.font_bold, fontSize=12, alignment=TA_CENTER, leading=14)
        okul_adi_metni = self.ayarlar.get("okul_adi", "Okul Adı")
        p_okul = Paragraph(self.metin_duzelt(okul_adi_metni), style_baslik)
        
        guvenli_genislik = genislik - 150 
        p_w, p_h = p_okul.wrap(guvenli_genislik, 85)
        baslik_y = orta_y - (p_h / 2)
        p_okul.drawOn(c, 75, baslik_y)

        c.setLineWidth(1)
        c.line(25, yukseklik - 85, genislik - 25, yukseklik - 85)
        
        # --- 2. FORM BAŞLIĞI VE METİN ---
        c.setFont(self.font_bold, 11)
        c.drawCentredString(genislik / 2, yukseklik - 105, "Devamsızlık Bilgilendirme Formu")
        
        style_metin = ParagraphStyle(name='JustifyIndent', fontName=self.font, fontSize=10, alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm, leading=14)
        metin_p1 = f"Velisi bulunduğum {ogrenci_no} numaralı, {kisa_sube} sınıfı öğrencisi {ogrenci_ad} aşağıda belirtilen tarihlerde bilgim dahilinde okula devam etmemiştir/etmeyecektir."
        
        p1 = Paragraph(self.metin_duzelt(metin_p1), style_metin)
        p1_genislik, p1_yukseklik = p1.wrapOn(c, genislik - 50, yukseklik) 
        y_p1 = yukseklik - 130 - p1_yukseklik 
        p1.drawOn(c, 25, y_p1)

        p2 = Paragraph(self.metin_duzelt("Gereğini bilgilerinize arz ederim."), style_metin)
        p2_genislik, p2_yukseklik = p2.wrapOn(c, genislik - 50, yukseklik)
        y_p2 = y_p1 - p2_yukseklik - 10
        p2.drawOn(c, 25, y_p2) 

        # --- 3. DEVAMSIZLIK TABLOSU ---
        y_pozisyon = y_p2 - 25
        c.setFont(self.font_bold, 10)
        c.drawString(60, y_pozisyon, "Tarih")
        c.drawString(160, y_pozisyon, self.metin_duzelt("Tür"))
        c.drawString(260, y_pozisyon, self.metin_duzelt("Süre"))
        c.line(40, y_pozisyon - 5, genislik - 40, y_pozisyon - 5)

        y_pozisyon -= 20
        c.setFont(self.font, 10)
        toplam_gun = 0.0
        for kayit in secili_kayitlar:
            if y_pozisyon < 100:
                c.showPage(); c.setFont(self.font, 10)
                y_pozisyon = yukseklik - 50
            
            c.drawString(60, y_pozisyon, kayit['tarih_duzgun'])
            c.drawString(160, y_pozisyon, self.metin_duzelt(kayit['tur']))
            c.drawString(260, y_pozisyon, str(kayit['gun_str']) + " Gün")
            
            try: toplam_gun += float(kayit['gun_str'])
            except: pass
            y_pozisyon -= 15

        c.line(40, y_pozisyon + 10, genislik - 40, y_pozisyon + 10)
        c.setFont(self.font_bold, 10)
        c.drawString(160, y_pozisyon - 5, "Toplam:")
        toplam_str = int(toplam_gun) if float(toplam_gun).is_integer() else toplam_gun
        c.drawString(260, y_pozisyon - 5, f"{toplam_str} Gün")

        # --- 4. İMZA ALANI ---
        # --- 4. İMZA ALANI ---
        bugun = datetime.now().strftime("%d/%m/%Y") 
        c.setFont(self.font, 10)
        
        # 25 karakterlik bir ismin rahatça sığabilmesi için ideal nokta sayısı (yaklaşık 120 punto genişlik)
        noktalar = "." * 45
        nokta_genislik = c.stringWidth(noktalar, self.font, 10)
        
        # İp gibi hizalama için sağ kenardan geriye doğru kusursuz matematik hesaplaması
        sag_margin = genislik - 30
        x_value = sag_margin - nokta_genislik
        x_colon = x_value - 10
        x_label = x_colon - 55
        
        # Yüksekliği belirleyen Y koordinatları
        y_tarih = 80
        y_ad = 60
        y_veli = 48
        y_imza = 30
        
        # 1. Satır: Tarih
        merkez_x = x_value + (nokta_genislik / 2)
        c.drawCentredString(merkez_x, y_tarih, f"Tarih : {bugun}")
        
        # 2. Satır: Ad Soyad
        c.drawString(x_label, y_ad, "Ad Soyad")
        c.drawString(x_colon, y_ad, ":")
        c.drawString(x_value, y_ad, noktalar)
        
        # 3. Ara Satır: Velisi (Noktaların genişliğinin tam merkezine ortalanır)
        merkez_x = x_value + (nokta_genislik / 2)
        c.drawCentredString(merkez_x, y_veli, "Velisi")
        
        # 4. Satır: İmza
        c.drawString(x_label, y_imza, self.metin_duzelt("İmza"))
        c.drawString(x_colon, y_imza, ":")
        c.drawString(x_value, y_imza, noktalar)

        c.save()
        return True, ""

        c.save()
        return True, ""
