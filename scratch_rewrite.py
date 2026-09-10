import re

def rewrite():
    with open(r'C:\Users\HP\Downloads\Oto-Yoklama-2-guncel\ihale_motoru.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_func = re.search(r'def uret_muayene_kabul_pdf\(veri, hedef_klasor\):.*?(?=def uret_muayene_kabul_excel)', content, re.DOTALL).group(0)
    
    new_func = '''def uret_muayene_kabul_pdf(veri, hedef_klasor):
    import datetime
    import os
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dosya_adi = os.path.join(hedef_klasor, f"Muayene_Kabul_{timestamp}.pdf")
    
    try:
        pdfmetrics.registerFont(TTFont('Times_TR', r'C:\\Windows\\Fonts\\times.ttf'))
        pdfmetrics.registerFont(TTFont('Times_TR_Bold', r'C:\\Windows\\Fonts\\timesbd.ttf'))
        font_name = 'Times_TR'
        font_bold = 'Times_TR_Bold'
    except:
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        
    doc = SimpleDocTemplate(
        dosya_adi,
        pagesize=portrait(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=15*mm
    )
    
    style_normal = ParagraphStyle('Normal_TR', fontName=font_name, fontSize=10, leading=14, alignment=0)
    style_center = ParagraphStyle('Center_TR', fontName=font_name, fontSize=10, alignment=1, leading=14)
    
    elements = []
    
    # 1. Üstteki 3 satır bilgi girişinden
    baslik = veri.get('resmi_baslik', '')
    if baslik:
        for line in baslik.split('\\n'):
            line = line.strip()
            if line:
                elements.append(Paragraph(line, style_center))
    else:
        elements.append(Paragraph("T.C.", style_center))
        elements.append(Paragraph("KAYMAKAMLIĞI", style_center))
        elements.append(Paragraph("Okul Müdürlüğü", style_center))
        
    elements.append(Spacer(1, 10*mm))
    
    # Tablo Verileri
    table_data = []
    
    # Satır 0: Belge Başlığı
    table_data.append([
        Paragraph("MUAYENE VE KABUL BELGESİ", ParagraphStyle('Title_TR', fontName=font_bold, fontSize=13, alignment=1, spaceAfter=5, spaceBefore=5)), 
        "", "", ""
    ])
    
    # Satır 1: Başlıklar
    table_data.append([
        Paragraph(x, ParagraphStyle('tb', fontName=font_bold, fontSize=10, alignment=1)) for x in ["Sıra\\nNo", "Satın Alınacak Malın", "Özellikleri", "Miktarı"]
    ])
    
    # Kalemler
    kalemler = veri.get('kalemler', [])
    for idx, k in enumerate(kalemler):
        cins = k.get('cins', '')
        ozellik = k.get('aciklama', '') or k.get('ozellik', '') or ''
        miktar = str(k.get('miktar', ''))
        birim = k.get('birim', '')
        miktar_str = f"{miktar} {birim}" if birim else miktar
        table_data.append([
            str(idx+1), 
            Paragraph(cins, ParagraphStyle('tn', fontName=font_name, fontSize=10)), 
            Paragraph(ozellik, ParagraphStyle('tn', fontName=font_name, fontSize=10)), 
            Paragraph(miktar_str, ParagraphStyle('tn', fontName=font_name, fontSize=10, alignment=1))
        ])
        
    while len(table_data) < 17:
        table_data.append(["", "", "", ""])
        
    # Alt Metin
    tarih = format_date(veri.get('tarih', ''))
    text = f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Yukarıda yazılı malların / malzemelerin / işlerin dokümanlarda yazılı niteliklerinin muayene neticesinde tespit edilen niteliklerine uygundur. {tarih}"
    table_data.append([
        Paragraph(text, ParagraphStyle('Normal_TR', fontName=font_name, fontSize=10, leading=14, alignment=0)),
        "", "", ""
    ])
    
    # Komisyon Başlık
    table_data.append([
        Paragraph("MUAYENE VE KABUL GÖREVLİLERİ", ParagraphStyle('kom', fontName=font_bold, fontSize=11, alignment=1, spaceBefore=10, spaceAfter=5)),
        "", "", ""
    ])
    
    # İmzalar
    komisyon = veri.get('komisyon', {})
    kom_isimler = [
        komisyon.get('ihale_kom_muayene_1', ''),
        komisyon.get('ihale_kom_muayene_2', ''),
        komisyon.get('ihale_kom_muayene_3', '')
    ]
    kom_titles = ['Başkan', 'Üye', 'Üye']
    
    sig_data = [[Paragraph(f"{kom_isimler[0]}<br/>{kom_titles[0]}", style_center), 
                 Paragraph(f"{kom_isimler[1]}<br/>{kom_titles[1]}", style_center), 
                 Paragraph(f"{kom_isimler[2]}<br/>{kom_titles[2]}", style_center)]]
    
    sig_table = Table(sig_data, colWidths=[60*mm, 60*mm, 60*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    table_data.append([sig_table, "", "", ""])
    
    text_row_idx = len(table_data) - 3
    kom_title_idx = len(table_data) - 2
    kom_sig_idx = len(table_data) - 1
    
    row_heights = [15*mm, 10*mm] + [8*mm]*15 + [None, 12*mm, 25*mm]
    
    t = Table(table_data, colWidths=[15*mm, 85*mm, 50*mm, 30*mm], rowHeights=row_heights)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        
        # Span Title
        ('SPAN', (0,0), (3,0)),
        ('ALIGN', (0,0), (3,0), 'CENTER'),
        ('VALIGN', (0,0), (3,0), 'MIDDLE'),
        
        # Span Text row
        ('SPAN', (0, text_row_idx), (3, text_row_idx)),
        ('VALIGN', (0, text_row_idx), (3, text_row_idx), 'TOP'),
        ('TOPPADDING', (0, text_row_idx), (3, text_row_idx), 8),
        ('BOTTOMPADDING', (0, text_row_idx), (3, text_row_idx), 8),
        ('LEFTPADDING', (0, text_row_idx), (3, text_row_idx), 10),
        ('RIGHTPADDING', (0, text_row_idx), (3, text_row_idx), 10),
        
        # Span Kom_title
        ('SPAN', (0, kom_title_idx), (3, kom_title_idx)),
        ('VALIGN', (0, kom_title_idx), (3, kom_title_idx), 'MIDDLE'),
        
        # Span Kom_sig
        ('SPAN', (0, kom_sig_idx), (3, kom_sig_idx)),
        ('VALIGN', (0, kom_sig_idx), (3, kom_sig_idx), 'TOP'),
        ('BOTTOMPADDING', (0, kom_sig_idx), (3, kom_sig_idx), 10),
        
        # Header alignment
        ('ALIGN', (0,1), (-1,1), 'CENTER'),
        ('VALIGN', (0,1), (-1,1), 'MIDDLE'),
        
        # Items alignment
        ('ALIGN', (0,2), (0, text_row_idx-1), 'CENTER'), # Sıra No
        ('ALIGN', (1,2), (2, text_row_idx-1), 'LEFT'),   # Mal ve Özellik
        ('ALIGN', (3,2), (3, text_row_idx-1), 'CENTER'), # Miktar
        ('VALIGN', (0,2), (-1, text_row_idx-1), 'MIDDLE'),
        
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('WORDWRAP', (0,0), (-1,-1), True),
    ]))
    
    elements.append(t)
    
    doc.build(elements)
    return dosya_adi
'''
    
    new_content = content.replace(old_func, new_func)
    with open(r'C:\Users\HP\Downloads\Oto-Yoklama-2-guncel\ihale_motoru.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

rewrite()
