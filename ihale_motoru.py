import os
import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# Font Handling
font_name = 'Helvetica-TR'
font_name_bold = 'Helvetica-TR-Bold'

try:
    pdfmetrics.registerFont(TTFont('Helvetica-TR', 'C:\\Windows\\Fonts\\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Helvetica-TR-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
except:
    font_name = 'Helvetica'
    font_name_bold = 'Helvetica-Bold'

def get_fonts():
    return font_name, font_name_bold

def format_date(date_str):
    if not date_str:
        return datetime.datetime.now().strftime("%d.%m.%Y")
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except:
        return date_str

def hesapla_toplamlar(kalemler):
    t1, t2, t3 = 0.0, 0.0, 0.0
    for k in kalemler:
        m = float(k.get('miktar', 1.0))
        f1 = float(k.get('f1', 0.0))
        f2 = float(k.get('f2', 0.0))
        f3 = float(k.get('f3', 0.0))
        t1 += f1 * m
        t2 += f2 * m
        t3 += f3 * m
    return t1, t2, t3

def hesapla_toplam_yaklasik_maliyet(kalemler):
    toplam = 0.0
    for k in kalemler:
        f1 = float(k.get('f1', 0.0))
        f2 = float(k.get('f2', 0.0))
        f3 = float(k.get('f3', 0.0))
        m = float(k.get('miktar', 1.0))
        avg = (f1 + f2 + f3) / 3.0
        toplam += avg * m
    return toplam

def uret_onay_belgesi(veriler, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=10, spaceAfter=8)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    # Institution Header
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 10*mm))
    
    elements.append(Paragraph("ONAY BELGESİ", title_style))
    
    # Total Approximate Cost
    kalemler = veriler.get('kalemler', [])
    toplam_yaklasik = hesapla_toplam_yaklasik_maliyet(kalemler)
    tarih = format_date(veriler.get('tarih', ''))
    
    # Details Table
    details_data = [
        [Paragraph("<b>İşin Adı / Konusu:</b>", normal_style), Paragraph(veriler.get('ihale_konusu', ''), normal_style)],
        [Paragraph("<b>Alım Usulü:</b>", normal_style), Paragraph("4734 Sayılı Kamu İhale Kanununun 22/d Maddesi (Doğrudan Temin)", normal_style)],
        [Paragraph("<b>Yaklaşık Maliyet:</b>", normal_style), Paragraph(f"{toplam_yaklasik:.2f} ₺ (KDV Hariç)", normal_style)],
        [Paragraph("<b>Kullanılabilir Ödenek:</b>", normal_style), Paragraph("Okul Aile Birliği / Genel Bütçe", normal_style)],
        [Paragraph("<b>Tarih:</b>", normal_style), Paragraph(tarih, normal_style)],
        [Paragraph("<b>İhale Yetkilisi:</b>", normal_style), Paragraph(veriler.get('okul_muduru', 'Okul Müdürü'), normal_style)]
    ]
    
    t_details = Table(details_data, colWidths=[50*mm, 130*mm])
    t_details.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.lightgrey),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 10*mm))
    
    body_text = ("Yukarıda belirtilen mal/hizmet/yapım işinin, 4734 Sayılı Kamu İhale Kanunu'nun "
                 "22/d maddesi uyarınca doğrudan temin usulüyle alımı hususunda yaklaşık maliyet tespiti "
                 "ve piyasa fiyat araştırması yapmak üzere görevlendirilen komisyon üyelerinin "
                 "çalışmalara başlamasını onaylarınıza arz ederim.")
    elements.append(Paragraph(body_text, normal_style))
    elements.append(Spacer(1, 15*mm))
    
    # Gerçekleştirme Görevlisi and OLUR block
    mudur_yard = veriler.get('gerceklesdirme_gorevlisi', 'Müdür Yardımcısı')
    okul_muduru = veriler.get('okul_muduru', 'Okul Müdürü')
    
    imza_data = [
        [
            Paragraph("<b>Gerçekleştirme Görevlisi</b><br/><br/><br/>...........................<br/>" + mudur_yard, ParagraphStyle('I1', parent=normal_style, alignment=1)),
            Paragraph("<b>OLUR</b><br/>" + tarih + "<br/><br/><br/>...........................<br/>" + okul_muduru + "<br/>Okul Müdürü / Harcama Yetkilisi", ParagraphStyle('I2', parent=normal_style, alignment=1))
        ]
    ]
    t_imza = Table(imza_data, colWidths=[90*mm, 90*mm])
    t_imza.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_imza)
    
    doc.build(elements)
    return pdf_yolu

def uret_yaklasik_maliyet(veriler, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=9)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=fnb, fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("YAKLAŞIK MALİYET HESAP CETVELİ", title_style))
    
    # Table Header
    firmalar = veriler.get('firmalar', ['', '', ''])
    table_data = [
        [
            Paragraph("<b>S.No</b>", bold_style),
            Paragraph("<b>Mal/Hizmetin Cinsi</b>", bold_style),
            Paragraph("<b>Miktar</b>", bold_style),
            Paragraph("<b>Birim</b>", bold_style),
            Paragraph(f"<b>{firmalar[0]} (₺)</b>", bold_style),
            Paragraph(f"<b>{firmalar[1]} (₺)</b>", bold_style),
            Paragraph(f"<b>{firmalar[2]} (₺)</b>", bold_style),
            Paragraph("<b>Yaklaşık Birim Fiyat (₺)</b>", bold_style),
            Paragraph("<b>Yaklaşık Toplam Fiyat (₺)</b>", bold_style)
        ]
    ]
    
    kalemler = veriler.get('kalemler', [])
    toplam_maliyet = 0.0
    
    for k in kalemler:
        f1 = float(k.get('f1', 0.0))
        f2 = float(k.get('f2', 0.0))
        f3 = float(k.get('f3', 0.0))
        m = float(k.get('miktar', 1.0))
        
        avg_birim = (f1 + f2 + f3) / 3.0
        avg_toplam = avg_birim * m
        toplam_maliyet += avg_toplam
        
        table_data.append([
            Paragraph(str(k.get('sira', '')), normal_style),
            Paragraph(str(k.get('cins', '')), normal_style),
            Paragraph(str(k.get('miktar', '')), normal_style),
            Paragraph(str(k.get('birim', '')), normal_style),
            Paragraph(f"{f1:.2f} ₺", normal_style),
            Paragraph(f"{f2:.2f} ₺", normal_style),
            Paragraph(f"{f3:.2f} ₺", normal_style),
            Paragraph(f"{avg_birim:.2f} ₺", normal_style),
            Paragraph(f"{avg_toplam:.2f} ₺", normal_style),
        ])
        
    table_data.append([
        "", Paragraph("<b>GENEL TOPLAM (Yaklaşık Maliyet)</b>", bold_style), "", "", 
        "", "", "", "", Paragraph(f"<b>{toplam_maliyet:.2f} ₺</b>", bold_style)
    ])
    
    t = Table(table_data, colWidths=[10*mm, 87*mm, 15*mm, 15*mm, 28*mm, 28*mm, 28*mm, 28*mm, 28*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-2), 'LEFT'), 
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'), 
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10*mm))
    
    # Yaklaşık Maliyet Tespit Komisyonu Üyeleri
    kom = veriler.get('komisyon', {})
    k1 = kom.get('ihale_kom_yaklasik_1', 'Komisyon Başkanı')
    k2 = kom.get('ihale_kom_yaklasik_2', 'Komisyon Üyesi')
    k3 = kom.get('ihale_kom_yaklasik_3', 'Komisyon Üyesi')
    
    komisyon_t_data = [
        ["Yaklaşık Maliyet Tespit Komisyonu Üyeleri", "", ""],
        ["İmza", "İmza", "İmza"],
        ["......................", "......................", "......................"],
        [k1, k2, k3],
        ["Komisyon Başkanı", "Komisyon Üyesi", "Komisyon Üyesi"]
    ]
    kom_t = Table(komisyon_t_data, colWidths=[89*mm, 89*mm, 89*mm])
    kom_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('FONTNAME', (0,0), (-1,0), fnb),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(kom_t)
    
    doc.build(elements)
    return pdf_yolu

def uret_teklif_mektubu(veriler, firma_adi, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=9)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=fnb, fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 5*mm))
    
    tarih = format_date(veriler.get('tarih', ''))
    
    top_meta = [
        [Paragraph(f"Sayı: 22/d - Doğrudan Temin", normal_style), Paragraph(f"Tarih: {tarih}", ParagraphStyle('RightD', parent=normal_style, alignment=2))]
    ]
    t_top_meta = Table(top_meta, colWidths=[90*mm, 90*mm])
    t_top_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_top_meta)
    elements.append(Spacer(1, 5*mm))
    
    elements.append(Paragraph(f"<b>SAYIN: {firma_adi.upper()}</b>", ParagraphStyle('FirmaS', parent=bold_style, fontSize=10, alignment=1)))
    elements.append(Spacer(1, 5*mm))
    
    body = (f"Okulumuzun ihtiyacı olan aşağıda cins ve miktarı belirtilen mal/hizmet alımı, 4734 Sayılı "
            f"Kamu İhale Kanunu'nun 22/d maddesi (Doğrudan Temin) uyarınca yapılacaktır. "
            f"Söz konusu işe ait KDV hariç birim ve toplam teklif ettiğiniz fiyatları aşağıdaki tabloya yazarak "
            f"en geç {tarih} tarihine kadar okulumuza teslim etmenizi rica ederim.")
    elements.append(Paragraph(body, normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Table Header
    table_data = [
        [
            Paragraph("<b>S.No</b>", bold_style),
            Paragraph("<b>Mal/Hizmetin Cinsi</b>", bold_style),
            Paragraph("<b>Miktar</b>", bold_style),
            Paragraph("<b>Birim</b>", bold_style),
            Paragraph("<b>Birim Fiyat (₺)</b>", bold_style),
            Paragraph("<b>Toplam Fiyat (₺)</b>", bold_style)
        ]
    ]
    
    kalemler = veriler.get('kalemler', [])
    for k in kalemler:
        table_data.append([
            Paragraph(str(k.get('sira', '')), normal_style),
            Paragraph(str(k.get('cins', '')), normal_style),
            Paragraph(str(k.get('miktar', '')), normal_style),
            Paragraph(str(k.get('birim', '')), normal_style),
            Paragraph("....................", normal_style),
            Paragraph("....................", normal_style)
        ])
        
    table_data.append([
        "", Paragraph("<b>TOPLAM BEDEL (KDV Hariç)</b>", bold_style), "", "", 
        "", Paragraph("<b>.................... ₺</b>", bold_style)
    ])
    
    t = Table(table_data, colWidths=[10*mm, 85*mm, 15*mm, 15*mm, 27*mm, 28*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-2), 'LEFT'),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10*mm))
    
    # Signatures
    okul_muduru = veriler.get('okul_muduru', 'Okul Müdürü')
    
    imza_block = [
        ["", "<b>Okul Müdürlüğü / Harcama Yetkilisi</b>"],
        ["", "İmza / Mühür"],
        ["", "......................"],
        ["", okul_muduru]
    ]
    t_imza = Table(imza_block, colWidths=[90*mm, 90*mm])
    t_imza.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))
    elements.append(t_imza)
    elements.append(Spacer(1, 5*mm))
    
    # Firm Commitment Box
    commitment_text = (
        "<b>YÜKLENİCİ TAAHHÜT BEYANI:</b><br/>"
        "Yukarıda belirtilen işe ait teklif mektubunu okudum ve inceledim. "
        "Teklif konusu mal/hizmetleri tabloda belirttiğimiz KDV Hariç toplam "
        "<b>........................................................... ₺</b> bedelle "
        "teslim etmeyi kabul ve taahhüt ederiz.<br/><br/>"
        "<b>Firma Kaşesi / İmza:</b> .................................................."
    )
    
    p_commitment = Paragraph(commitment_text, ParagraphStyle('CommStyle', parent=normal_style, leading=14))
    t_commitment = Table([[p_commitment]], colWidths=[180*mm])
    t_commitment.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t_commitment)
    
    doc.build(elements)
    return pdf_yolu

def uret_piyasa_arastirma(veriler, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=9)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=fnb, fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("PİYASA FİYAT ARAŞTIRMASI TUTANAĞI", title_style))
    
    # Info
    elements.append(Paragraph(f"<b>İşin Adı / Konusu:</b> {veriler.get('ihale_konusu', '')}", normal_style))
    elements.append(Paragraph(f"<b>Tarih:</b> {format_date(veriler.get('tarih', ''))}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    firmalar = veriler.get('firmalar', ['', '', ''])
    
    table_data = [
        [
            Paragraph("<b>S.No</b>", bold_style),
            Paragraph("<b>Mal/Hizmetin Cinsi</b>", bold_style),
            Paragraph("<b>Miktar</b>", bold_style),
            Paragraph("<b>Birim</b>", bold_style),
            Paragraph(f"<b>{firmalar[0]} (₺)</b>", bold_style),
            Paragraph(f"<b>{firmalar[1]} (₺)</b>", bold_style),
            Paragraph(f"<b>{firmalar[2]} (₺)</b>", bold_style)
        ]
    ]
    
    t1, t2, t3 = hesapla_toplamlar(veriler.get('kalemler', []))
    
    for k in veriler.get('kalemler', []):
        f1 = float(k.get('f1', 0))
        f2 = float(k.get('f2', 0))
        f3 = float(k.get('f3', 0))
        m = float(k.get('miktar', 1))
        
        # Find minimum price to highlight
        min_f = min(f1, f2, f3)
        c_f1 = f"<b>{f1:.2f} ₺ *</b>" if f1 == min_f and f1 > 0 else f"{f1:.2f} ₺"
        c_f2 = f"<b>{f2:.2f} ₺ *</b>" if f2 == min_f and f2 > 0 else f"{f2:.2f} ₺"
        c_f3 = f"<b>{f3:.2f} ₺ *</b>" if f3 == min_f and f3 > 0 else f"{f3:.2f} ₺"
        
        table_data.append([
            Paragraph(str(k.get('sira', '')), normal_style),
            Paragraph(str(k.get('cins', '')), normal_style),
            Paragraph(str(k.get('miktar', '')), normal_style),
            Paragraph(str(k.get('birim', '')), normal_style),
            Paragraph(c_f1, normal_style),
            Paragraph(c_f2, normal_style),
            Paragraph(c_f3, normal_style)
        ])
        
    table_data.append([
        "", Paragraph("<b>GENEL TOPLAM (KDV Hariç)</b>", bold_style), "", "", 
        Paragraph(f"<b>{t1:.2f} ₺</b>", bold_style), 
        Paragraph(f"<b>{t2:.2f} ₺</b>", bold_style), 
        Paragraph(f"<b>{t3:.2f} ₺</b>", bold_style)
    ])
    
    t = Table(table_data, colWidths=[10*mm, 117*mm, 15*mm, 15*mm, 36*mm, 37*mm, 37*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-2), 'LEFT'),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10*mm))
    
    # Signatures
    kom = veriler.get('komisyon', {})
    k1 = kom.get('ihale_kom_piyasa_1', 'Görevli 1')
    k2 = kom.get('ihale_kom_piyasa_2', 'Görevli 2')
    k3 = kom.get('ihale_kom_piyasa_3', 'Görevli 3')
    
    imza_tablosu = [
        ["Piyasa Fiyat Araştırması Görevlileri", "", ""],
        ["İmza", "İmza", "İmza"],
        ["......................", "......................", "......................"],
        [k1, k2, k3],
        ["Görevli Personel", "Görevli Personel", "Görevli Personel"]
    ]
    imza_t = Table(imza_tablosu, colWidths=[89*mm, 89*mm, 89*mm])
    imza_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('FONTNAME', (0,0), (-1,0), fnb),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(imza_t)
    
    doc.build(elements)
    return pdf_yolu

def uret_karar_tutanagi(veriler, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=10, spaceAfter=8)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=fnb, fontSize=10, spaceAfter=8)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 10*mm))
    
    elements.append(Paragraph("DOĞRUDAN TEMİN ALIM KARARI", title_style))
    
    tarih = format_date(veriler.get('tarih', ''))
    firmalar = veriler.get('firmalar', ['', '', ''])
    t1, t2, t3 = hesapla_toplamlar(veriler.get('kalemler', []))
    
    # We find the winner
    winner_name = firmalar[0]
    winner_total = t1
    
    # Sort firm offers to find cheapest
    teklifler = [(firmalar[0], t1), (firmalar[1], t2), (firmalar[2], t3)]
    teklifler.sort(key=lambda x: x[1])
    
    valid_teklifler = [t for t in teklifler if t[1] > 0]
    if valid_teklifler:
        winner_name, winner_total = valid_teklifler[0]
        
    details_data = [
        [Paragraph("<b>İşin Adı / Konusu:</b>", normal_style), Paragraph(veriler.get('ihale_konusu', ''), normal_style)],
        [Paragraph("<b>Karar Tarihi:</b>", normal_style), Paragraph(tarih, normal_style)],
        [Paragraph("<b>Alım Usulü:</b>", normal_style), Paragraph("4734 Sayılı Kamu İhale Kanununun 22/d Maddesi", normal_style)]
    ]
    t_details = Table(details_data, colWidths=[50*mm, 130*mm])
    t_details.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.lightgrey),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 5*mm))
    
    decision_intro = (
        "Okul Müdürlüğümüzün ihtiyacı için doğrudan temin usulüyle piyasa araştırması yapılmış "
        "ve alınan teklifler değerlendirilmiştir. Tekliflerin KDV hariç genel toplamları aşağıda sunulmuştur:"
    )
    elements.append(Paragraph(decision_intro, normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Offers list Table
    offers_data = [
        [Paragraph("<b>Sıra</b>", bold_style), Paragraph("<b>Teklif Veren Firma</b>", bold_style), Paragraph("<b>Toplam Teklif Tutarı (₺)</b>", bold_style), Paragraph("<b>Açıklama</b>", bold_style)]
    ]
    
    s_idx = 1
    for name, total in teklifler:
        aciklama = "En Avantajlı Teklif (Kazanan)" if name == winner_name else "Diğer Teklif"
        offers_data.append([
            Paragraph(str(s_idx), normal_style),
            Paragraph(name, normal_style),
            Paragraph(f"{total:.2f} ₺", normal_style),
            Paragraph(aciklama, ParagraphStyle('BoldAc', parent=bold_style if name == winner_name else normal_style))
        ])
        s_idx += 1
        
    t_offers = Table(offers_data, colWidths=[15*mm, 80*mm, 45*mm, 40*mm])
    t_offers.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    elements.append(t_offers)
    elements.append(Spacer(1, 5*mm))
    
    decision_text = (
        f"Yapılan piyasa fiyat araştırması sonucunda, en ekonomik teklifi sunan <b>{winner_name.upper()}</b> "
        f"firmasından KDV hariç toplam <b>{winner_total:.2f} ₺</b> bedelle mal/hizmet satın alınması, komisyonumuzca "
        f"karara bağlanmıştır."
    )
    elements.append(Paragraph(decision_text, normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Commission signatures
    kom = veriler.get('komisyon', {})
    k1 = kom.get('ihale_kom_piyasa_1', 'Görevli 1')
    k2 = kom.get('ihale_kom_piyasa_2', 'Görevli 2')
    k3 = kom.get('ihale_kom_piyasa_3', 'Görevli 3')
    
    imza_t_data = [
        ["Piyasa Fiyat Araştırması Görevlileri", "", ""],
        ["İmza", "İmza", "İmza"],
        ["......................", "......................", "......................"],
        [k1, k2, k3]
    ]
    imza_t = Table(imza_t_data, colWidths=[60*mm, 60*mm, 60*mm])
    imza_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(imza_t)
    elements.append(Spacer(1, 10*mm))
    
    # Director Approval (ONAY)
    okul_muduru = veriler.get('okul_muduru', 'Okul Müdürü')
    approval_data = [
        [
            Paragraph("<b>ONAY</b><br/>Yukarıdaki komisyon kararı tarafımdan onaylanmıştır.<br/>" + tarih + "<br/><br/><br/>...........................<br/>" + okul_muduru + "<br/>Okul Müdürü / Harcama Yetkilisi", ParagraphStyle('I2', parent=normal_style, alignment=1))
        ]
    ]
    t_approval = Table(approval_data, colWidths=[180*mm])
    t_approval.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t_approval)
    
    doc.build(elements)
    return pdf_yolu

def uret_muayene_kabul(veriler, pdf_yolu):
    doc = SimpleDocTemplate(pdf_yolu, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    fn, fnb = get_fonts()
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName=fnb, fontSize=12, alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=fn, fontSize=10, spaceAfter=8)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=fnb, fontSize=10, spaceAfter=8)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontName=fnb, fontSize=11, alignment=1, leading=14)
    
    okul_adi = veriler.get("okul_adi", "Okul Müdürlüğü").upper()
    elements.append(Paragraph(f"T.C.<br/>MİLLÎ EĞİTİM BAKANLIĞI<br/>{okul_adi} MÜDÜRLÜĞÜ", header_style))
    elements.append(Spacer(1, 10*mm))
    
    elements.append(Paragraph("MUAYENE VE KABUL TUTANAĞI", title_style))
    
    tarih = format_date(veriler.get('tarih', ''))
    firmalar = veriler.get('firmalar', ['', '', ''])
    t1, t2, t3 = hesapla_toplamlar(veriler.get('kalemler', []))
    
    winner_name = firmalar[0]
    winner_total = t1
    
    # Sort firm offers to find cheapest
    teklifler = [(firmalar[0], t1), (firmalar[1], t2), (firmalar[2], t3)]
    teklifler.sort(key=lambda x: x[1])
    valid_teklifler = [t for t in teklifler if t[1] > 0]
    if valid_teklifler:
        winner_name, winner_total = valid_teklifler[0]
        
    details_data = [
        [Paragraph("<b>İşin Adı / Konusu:</b>", normal_style), Paragraph(veriler.get('ihale_konusu', ''), normal_style)],
        [Paragraph("<b>Yüklenici (Firma):</b>", normal_style), Paragraph(winner_name, normal_style)],
        [Paragraph("<b>Toplam Kabul Tutarı:</b>", normal_style), Paragraph(f"{winner_total:.2f} ₺ (KDV Hariç)", normal_style)],
        [Paragraph("<b>Muayene Tarihi:</b>", normal_style), Paragraph(tarih, normal_style)]
    ]
    t_details = Table(details_data, colWidths=[50*mm, 130*mm])
    t_details.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.25, colors.lightgrey),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 10*mm))
    
    body_text = (
        "Okul Müdürlüğümüzün ihtiyacı için satın alınan ve yukarıda detayları belirtilen mal/hizmetler, "
        "Muayene ve Kabul Komisyonumuzca incelenmiş olup, sipariş şartlarına ve fatura içeriğine "
        "tam olarak uygun olduğu, eksiksiz, sağlam ve hasarsız bir şekilde teslim alındığı tespit edilmiştir. "
        "İşbu muayene ve kabul belgesi komisyonumuzca tanzim edilerek imza altına alınmıştır."
    )
    elements.append(Paragraph(body_text, normal_style))
    elements.append(Spacer(1, 20*mm))
    
    # Commission signatures
    kom = veriler.get('komisyon', {})
    k1 = kom.get('ihale_kom_muayene_1', 'Görevli 1')
    k2 = kom.get('ihale_kom_muayene_2', 'Görevli 2')
    k3 = kom.get('ihale_kom_muayene_3', 'Görevli 3')
    
    imza_t_data = [
        ["Muayene ve Kabul Komisyonu Üyeleri", "", ""],
        ["İmza", "İmza", "İmza"],
        ["......................", "......................", "......................"],
        [k1, k2, k3],
        ["Komisyon Başkanı", "Komisyon Üyesi", "Komisyon Üyesi"]
    ]
    imza_t = Table(imza_t_data, colWidths=[60*mm, 60*mm, 60*mm])
    imza_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), fn),
        ('FONTNAME', (0,0), (-1,0), fnb),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(imza_t)
    
    doc.build(elements)
    return pdf_yolu

def tum_evraklari_uret(veriler, kayit_klasoru):
    os.makedirs(kayit_klasoru, exist_ok=True)
    tarih_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    klasor = os.path.join(kayit_klasoru, f"Ihale_{tarih_str}")
    os.makedirs(klasor, exist_ok=True)
    
    onay_pdf = os.path.join(klasor, "01_Onay_Belgesi.pdf")
    yaklasik_pdf = os.path.join(klasor, "02_Yaklasik_Maliyet_Hesap_Cetveli.pdf")
    
    firmalar = veriler.get('firmalar', ['', '', ''])
    f1_clean = firmalar[0].replace(' ', '_').replace('/', '_').replace('\\', '_')
    f2_clean = firmalar[1].replace(' ', '_').replace('/', '_').replace('\\', '_')
    f3_clean = firmalar[2].replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    teklif1_pdf = os.path.join(klasor, f"03_Teklif_Mektubu_{f1_clean}.pdf")
    teklif2_pdf = os.path.join(klasor, f"04_Teklif_Mektubu_{f2_clean}.pdf")
    teklif3_pdf = os.path.join(klasor, f"05_Teklif_Mektubu_{f3_clean}.pdf")
    
    piyasa_pdf = os.path.join(klasor, "06_Piyasa_Fiyat_Arastirmasi_Tutanagi.pdf")
    karar_pdf = os.path.join(klasor, "07_Karar_Tutanagi.pdf")
    muayene_pdf = os.path.join(klasor, "08_Muayene_ve_Kabul_Tutanagi.pdf")
    
    uret_onay_belgesi(veriler, onay_pdf)
    uret_yaklasik_maliyet(veriler, yaklasik_pdf)
    
    uret_teklif_mektubu(veriler, firmalar[0], teklif1_pdf)
    uret_teklif_mektubu(veriler, firmalar[1], teklif2_pdf)
    uret_teklif_mektubu(veriler, firmalar[2], teklif3_pdf)
    
    uret_piyasa_arastirma(veriler, piyasa_pdf)
    uret_karar_tutanagi(veriler, karar_pdf)
    uret_muayene_kabul(veriler, muayene_pdf)
    
    return klasor
