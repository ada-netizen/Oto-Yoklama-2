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

    # pdf_motoru.py içinde tablo_basligi_ciz fonksiyonunu bul ve değiştir:
        def tablo_basligi_ciz(y):
            c.setFont(self.font_bold, 10)
            c.setFillColorRGB(0.9, 0.9, 0.9) 
            c.rect(40, y - 5, genislik - 80, 20, fill=1)
            c.setFillColorRGB(0, 0, 0)
            
            # YENİ HİZALAMALAR (Görev ve Branş Ayrı Ayrı)
            c.drawString(45, y, "S.N")
            c.drawString(80, y, self.metin_duzelt("Görevi"))
            c.drawString(165, y, self.metin_duzelt("Branşı"))
            c.drawString(255, y, "Ad Soyad")
            c.drawString(375, y, "Tarih")
            c.drawString(450, y, self.metin_duzelt("İmza"))
            
            c.line(40, y - 5, genislik - 40, y - 5)
            c.line(40, y + 15, genislik - 40, y + 15)
            # Dikey çizgiler güncellendi
            for x in [40, 75, 160, 250, 370, 440, genislik - 40]:
                c.line(x, y - 5, x, y + 15)
            return y - 20

        y_pos = tablo_basligi_ciz(y_pos)
        
        # ... Altındaki Döngüyü de şu şekilde güncelle:
        c.setFont(self.font, 10)
        satir_yuksekligi = 25
        
        for i, personel in enumerate(personel_listesi, 1):
            if y_pos < 50: 
                c.showPage(); y_pos = sayfa_basligi_ciz(); y_pos = tablo_basligi_ciz(y_pos)
                c.setFont(self.font, 10)
                
            c.line(40, y_pos - 5, genislik - 40, y_pos - 5)
            
            c.drawString(45, y_pos + 5, str(i))
            c.drawString(80, y_pos + 5, self.metin_duzelt(personel['gorev'][:14]))
            c.drawString(165, y_pos + 5, self.metin_duzelt(personel['brans'][:14]))
            c.drawString(255, y_pos + 5, self.metin_duzelt(personel['ad'][:25]))
            
            for x in [40, 75, 160, 250, 370, 440, genislik - 40]:
                c.line(x, y_pos + 20, x, y_pos - 5)
                
            y_pos -= satir_yuksekligi
                  
        c.save()
        return True, ""
    
    # --- TOPLU İMZA SİRKÜSÜ (A4 LİSTE) ÇİZİM MOTORU ---
    def teblig_tebellug_ciz(self, sayi, konu, yazi_tarihi, personel_listesi, kayit_yeri):
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(kayit_yeri, pagesize=A4)
        genislik, yukseklik = A4
        
        def sayfa_basligi_ciz():
            c.setFont(self.font_bold, 12)
            c.drawCentredString(genislik / 2, yukseklik - 40, self.metin_duzelt("TEBLİĞ / TEBELLÜĞ BELGESİ"))
            
            c.setFont(self.font_bold, 10)
            c.drawString(40, yukseklik - 70, "Sayı:")
            c.drawString(40, yukseklik - 85, "Konu:")
            c.drawString(40, yukseklik - 100, "Tarih:")
            
            c.setFont(self.font, 10)
            c.drawString(80, yukseklik - 70, self.metin_duzelt(sayi))
            c.drawString(80, yukseklik - 85, self.metin_duzelt(konu))
            c.drawString(80, yukseklik - 100, self.metin_duzelt(yazi_tarihi))
            return yukseklik - 130

        def tablo_basligi_ciz(y):
            c.setFont(self.font_bold, 10)
            c.setFillColorRGB(0.9, 0.9, 0.9) 
            c.rect(40, y - 5, genislik - 80, 20, fill=1)
            c.setFillColorRGB(0, 0, 0)
            
            # Sütun Başlıkları (Yeni düzene göre Görev ve Branş ayrıldı)
            c.drawString(45, y, "S.N")
            c.drawString(75, y, self.metin_duzelt("Görevi"))
            c.drawString(160, y, self.metin_duzelt("Branşı"))
            c.drawString(250, y, "Ad Soyad")
            c.drawString(375, y, "Tarih")
            c.drawString(450, y, self.metin_duzelt("İmza"))
            
            c.line(40, y - 5, genislik - 40, y - 5)
            c.line(40, y + 15, genislik - 40, y + 15)
            
            # Dikey çizgilerin x koordinatları
            for x in [40, 70, 155, 245, 370, 440, genislik - 40]:
                c.line(x, y - 5, x, y + 15)
            return y - 20

        y_pos = sayfa_basligi_ciz()
        y_pos = tablo_basligi_ciz(y_pos)
        
        c.setFont(self.font, 10)
        satir_yuksekligi = 25
        
        for i, personel in enumerate(personel_listesi, 1):
            if y_pos < 50: 
                c.showPage()
                y_pos = sayfa_basligi_ciz()
                y_pos = tablo_basligi_ciz(y_pos)
                c.setFont(self.font, 10)
                
            c.line(40, y_pos - 5, genislik - 40, y_pos - 5)
            
            # Sütunlara verileri nizami bir şekilde bas
            c.drawString(45, y_pos + 5, str(i))
            c.drawString(75, y_pos + 5, self.metin_duzelt(personel.get('gorev', '-')[:14]))
            c.drawString(160, y_pos + 5, self.metin_duzelt(personel.get('brans', '-')[:14]))
            c.drawString(250, y_pos + 5, self.metin_duzelt(personel.get('ad', '')[:23]))
            
            for x in [40, 70, 155, 245, 370, 440, genislik - 40]:
                c.line(x, y_pos + 20, x, y_pos - 5)
                
            y_pos -= satir_yuksekligi
            
        c.save()
        return True, ""
    
    def bireysel_teblig_ciz(self, sayi, konu, yazi_tarihi, t_eden, t_edilen, t_yeri, yuklenen_pdf, kayit_yeri):
        from reportlab.lib.pagesizes import A4
        from datetime import datetime
        import io
        
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("Lütfen terminale 'pip install PyPDF2' yazıp kütüphaneyi yükleyin.")
            
        genislik, yukseklik = A4
        
        # A5 Makbuzunu diske değil, bilgisayarın "Geçici Hafızasına (RAM)" çiziyoruz
        temp_pdf = io.BytesIO()
        c = canvas.Canvas(temp_pdf, pagesize=A4)
        
        # ================= 2 ADET A5 (ÜST VE ALT) ÇİZİMİ =================
        def a5_belge_ciz(y_offset):
            baslangic_y = y_offset + 380
            
            c.setFont(self.font_bold, 14)
            c.drawCentredString(genislik / 2, baslangic_y, self.metin_duzelt("TEBLİĞ - TEBELLÜĞ BELGESİ"))
            
            c.setFont(self.font_bold, 11)
            c.drawString(40, baslangic_y - 40, self.metin_duzelt("YAZININ TARİH VE SAYISI"))
            c.drawString(200, baslangic_y - 40, ":")
            c.setFont(self.font, 11)
            c.drawString(210, baslangic_y - 40, self.metin_duzelt(f"{yazi_tarihi} - {sayi}"))
            
            c.setFont(self.font_bold, 11)
            c.drawString(40, baslangic_y - 65, self.metin_duzelt("YAZININ ÖZÜ (KONUSU)"))
            c.drawString(200, baslangic_y - 65, ":")
            
            p_konu2 = Paragraph(self.metin_duzelt(konu), ParagraphStyle(name='N', fontName=self.font, fontSize=11, leading=14))
            p_konu2.wrapOn(c, genislik - 240, 100)
            p_konu2.drawOn(c, 210, baslangic_y - 65 - (p_konu2.height - 11))
            
            y_next = baslangic_y - 65 - (p_konu2.height - 11) - 25
            
            c.setFont(self.font_bold, 11)
            c.drawString(40, y_next, self.metin_duzelt("TEBLİĞ EDİLEN YER"))
            c.drawString(200, y_next, ":")
            c.setFont(self.font, 11)
            c.drawString(210, y_next, self.metin_duzelt(t_yeri))
            
            y_next -= 25
            bugun = datetime.now().strftime("%d/%m/%Y")
            c.setFont(self.font_bold, 11)
            c.drawString(40, y_next, self.metin_duzelt("TEBLİĞ TARİHİ VE SAATİ"))
            c.drawString(200, y_next, ":")
            c.setFont(self.font, 11)
            c.drawString(210, y_next, self.metin_duzelt(f"{bugun}   Saat: ......:......"))
            
            y_next -= 50
            c.setFont(self.font_bold, 11)
            c.drawCentredString(140, y_next, self.metin_duzelt("TEBLİĞ EDEN"))
            c.drawCentredString(425, y_next, self.metin_duzelt("TEBELLÜĞ EDEN"))
            
            y_next -= 45
            c.setFont(self.font, 10)
            c.drawCentredString(140, y_next, self.metin_duzelt(t_eden['ad']))
            c.drawCentredString(425, y_next, self.metin_duzelt(t_edilen['ad']))
            
            y_next -= 15
            c.drawCentredString(140, y_next, self.metin_duzelt(t_eden['gorev']))
            c.drawCentredString(425, y_next, self.metin_duzelt(t_edilen['gorev']))
            
            if y_offset > 0:
                c.setDash(6, 4)
                c.line(0, yukseklik/2, genislik, yukseklik/2)
                c.setDash(1, 0)
                
        a5_belge_ciz(yukseklik / 2) # Sayfanın Üstü
        a5_belge_ciz(0)             # Sayfanın Altı
        c.save()
        temp_pdf.seek(0)
        
        # ================= PDF'LERİ BİRLEŞTİRME MUCİZESİ =================
        merger = PyPDF2.PdfMerger()
        
        # 1. Klasöre gidip senin seçtiğin DYS Orijinal Resmi Yazısını (PDF) alır
        if yuklenen_pdf and os.path.exists(yuklenen_pdf):
            merger.append(yuklenen_pdf)
            
        # 2. Üzerine bizim RAM'de hazırladığımız Makaslı A5 Makbuzunu yapıştırır
        merger.append(temp_pdf)
        
        # 3. Sonuç olarak ikisini tek bir PDF dosyası olarak kaydeder!
        with open(kayit_yeri, "wb") as f_out:
            merger.write(f_out)
            
        merger.close()
        return True, ""
        
        c.save()
        return True, ""