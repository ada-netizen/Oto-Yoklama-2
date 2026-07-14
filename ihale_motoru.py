import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import datetime

# Register font (assuming arial or standard font is needed for Turkish chars)
# Reportlab standard fonts don't support TR chars well, so we use a safe approach
try:
    pdfmetrics.registerFont(TTFont('Helvetica-TR', 'C:\\Windows\\Fonts\\arial.ttf'))
    pdfmetrics.registerFont(TTFont('Helvetica-TR-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
except:
    pass # Fallback to standard if missing

def uret_piyasa_arastirma(veriler, pdf_yolu):
    """
    veriler = {
        "ihale_konusu": "Kırtasiye Alımı",
        "tarih": "14.07.2026",
        "firmalar": ["Firma A", "Firma B", "Firma C"],
        "kalemler": [
            {"sira": 1, "cins": "A4 Kağıt", "miktar": 10, "birim": "Paket", "f1": 100, "f2": 110, "f3": 105},
            ...
        ]
    }
    """
    doc = SimpleDocTemplate(pdf_yolu, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-TR-Bold', fontSize=14, alignment=1, spaceAfter=20)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName='Helvetica-TR', fontSize=10)

    # Başlık
    elements.append(Paragraph("PİYASA FİYAT ARAŞTIRMASI TUTANAĞI", title_style))
    
    # Bilgiler
    elements.append(Paragraph(f"<b>İşin Adı / Konusu:</b> {veriler.get('ihale_konusu', '')}", normal_style))
    elements.append(Paragraph(f"<b>Tarih:</b> {veriler.get('tarih', '')}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Tablo Verisi
    firmalar = veriler.get('firmalar', ['', '', ''])
    
    table_data = [
        ["Sıra", "Mal/Hizmetin Cinsi", "Miktarı", "Birimi", firmalar[0], firmalar[1], firmalar[2]]
    ]
    
    toplam_f1, toplam_f2, toplam_f3 = 0, 0, 0
    
    for k in veriler.get('kalemler', []):
        f1 = float(k.get('f1', 0))
        f2 = float(k.get('f2', 0))
        f3 = float(k.get('f3', 0))
        m = float(k.get('miktar', 1))
        
        tf1 = f1 * m
        tf2 = f2 * m
        tf3 = f3 * m
        
        toplam_f1 += tf1
        toplam_f2 += tf2
        toplam_f3 += tf3
        
        table_data.append([
            str(k.get('sira', '')),
            str(k.get('cins', '')),
            str(k.get('miktar', '')),
            str(k.get('birim', '')),
            f"{f1:.2f} ₺",
            f"{f2:.2f} ₺",
            f"{f3:.2f} ₺"
        ])
        
    # Toplam Satırı
    table_data.append([
        "", "GENEL TOPLAM", "", "", 
        f"{toplam_f1:.2f} ₺", f"{toplam_f2:.2f} ₺", f"{toplam_f3:.2f} ₺"
    ])
    
    # Tablo Stili
    t = Table(table_data, colWidths=[10*mm, 80*mm, 20*mm, 20*mm, 40*mm, 40*mm, 40*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-TR'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-TR-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-TR-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-2), 'LEFT'), # İsimler sola dayalı
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'), # Fiyatlar sağa dayalı
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20*mm))
    
    # İmzalar
    imza_tablosu = [
        ["Piyasa Fiyat Araştırması Görevlileri", "", ""],
        ["İmza", "İmza", "İmza"],
        ["......................", "......................", "......................"],
        ["Görevli 1", "Görevli 2", "Görevli 3"]
    ]
    imza_t = Table(imza_tablosu, colWidths=[80*mm, 80*mm, 80*mm])
    imza_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-TR'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(imza_t)
    
    doc.build(elements)
    return pdf_yolu

def uret_onay_belgesi(veriler, pdf_yolu):
    # Basit bir onay belgesi PDF'i
    doc = SimpleDocTemplate(pdf_yolu, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading2'], fontName='Helvetica-TR-Bold', alignment=1, spaceAfter=20)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName='Helvetica-TR', fontSize=11, spaceAfter=10)
    
    elements.append(Paragraph("İHALE ONAY BELGESİ", title_style))
    elements.append(Paragraph(f"<b>İşin Adı:</b> {veriler.get('ihale_konusu', '')}", normal_style))
    elements.append(Paragraph(f"<b>Tarih:</b> {veriler.get('tarih', '')}", normal_style))
    elements.append(Paragraph(f"<b>Açıklama:</b> Yukarıda belirtilen mal/hizmetin 4734 Sayılı Kamu İhale Kanununun 22/d maddesi uyarınca doğrudan temin usulüyle alınması hususunu olurlarınıza arz ederim.", normal_style))
    
    elements.append(Spacer(1, 30*mm))
    elements.append(Paragraph("OLUR", ParagraphStyle('O', parent=normal_style, alignment=1, fontName="Helvetica-TR-Bold")))
    elements.append(Paragraph(veriler.get('tarih', ''), ParagraphStyle('T', parent=normal_style, alignment=1)))
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("Okul Müdürü / Harcama Yetkilisi", ParagraphStyle('H', parent=normal_style, alignment=1)))
    
    doc.build(elements)
    return pdf_yolu

def tum_evraklari_uret(veriler, kayit_klasoru):
    os.makedirs(kayit_klasoru, exist_ok=True)
    tarih_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    klasor = os.path.join(kayit_klasoru, f"Ihale_{tarih_str}")
    os.makedirs(klasor, exist_ok=True)
    
    piyasa_pdf = os.path.join(klasor, "Piyasa_Fiyat_Arastirmasi.pdf")
    onay_pdf = os.path.join(klasor, "Onay_Belgesi.pdf")
    
    uret_piyasa_arastirma(veriler, piyasa_pdf)
    uret_onay_belgesi(veriler, onay_pdf)
    
    return klasor
