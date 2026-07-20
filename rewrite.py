import re

with open("ihale_motoru.py", "r", encoding="utf-8") as f:
    content = f.read()

new_func = """def uret_yaklasik_maliyet_pdf(veri, hedef_klasor):
    import os
    import datetime
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dosya_adi = os.path.join(hedef_klasor, f"Yaklasik_Maliyet_Hesap_Cetveli_{timestamp}.pdf")
    
    try:
        pdfmetrics.registerFont(TTFont('Arial_TR', r'C:\\Windows\\Fonts\\arial.ttf'))
        font_name = 'Arial_TR'
    except:
        font_name = 'Helvetica'
        
    doc = SimpleDocTemplate(
        dosya_adi,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12.5*mm,
        bottomMargin=12.5*mm
    )
    
    style_normal = ParagraphStyle('Normal_TR', fontName=font_name, fontSize=8, leading=10)
    style_center = ParagraphStyle('Center_TR', fontName=font_name, fontSize=8, alignment=1, leading=10)
    style_right = ParagraphStyle('Right_TR', fontName=font_name, fontSize=8, alignment=2, leading=10)
    style_title = ParagraphStyle('Title_TR', fontName=font_name, fontSize=11, alignment=1, leading=13)
    
    elements = []
    
    elements.append(Paragraph("YAKLAŞIK MALİYET HESAP CETVELİ", style_title))
    elements.append(Spacer(1, 4*mm))
    
    tarih = ""
    if "belge_tarihi" in veri:
        date_str = veri["belge_tarihi"]
        if "T" in date_str:
            d = datetime.datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
        elif "-" in date_str:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        else:
            try: d = datetime.datetime.strptime(date_str, "%d.%m.%Y")
            except: d = datetime.datetime.now()
        tarih = d.strftime("%d.%m.%Y")
        
    konu = veri.get("konu", "Kırtasiye Alımı")
    
    baslik = veri.get("resmi_baslik", "")
    lines = [L.strip() for L in baslik.split("\\n") if L.strip()]
    if len(lines) >= 3:
        idare_adi = lines[2]
    elif lines:
        idare_adi = lines[-1]
    else:
        idare_adi = "Gazi Mustafa Kemal Anadolu Lisesi Müdürlüğü"
    
    table_data = []
    
    row0 = ["İdarenin Adı", "", "", "", "", idare_adi, "", "", "", "", "", "", "", Paragraph("İdarece Tesbit<br/>ve Takdir Edilen<br/>Yaklaşık Maliyet<br/>( KDV Hariç )", style_center), ""]
    table_data.append([Paragraph(x, style_normal) if isinstance(x, str) and x else x for x in row0])
    
    row1 = ["Yaklaşık Maliyeti Yapılan İş / Mal / Hizmetin Adı, Niteliği", "", "", "", "", konu, "", "", "", "", "", "", "", "", ""]
    table_data.append([Paragraph(x, style_normal) if isinstance(x, str) and x else x for x in row1])
    
    row2 = ["Düzenleme Tarihi", "", "", tarih, "", Paragraph("Kişiler / Kurumlar / Firmalar ve Yaklaşık Maliyet İçin<br/>Bildirilen Fiyatlar ( KDV Hariç )", style_center), "", "", "", "", "", "", "", "", ""]
    table_data.append([Paragraph(x, style_normal) if isinstance(x, str) and x else x for x in row2])
    
    firmalar = veri.get("firmalar", ["", "", "", ""])
    firma_vergiler = veri.get("firma_vergiler", ["", "", "", ""])
    while len(firmalar) < 4: firmalar.append("")
    while len(firma_vergiler) < 4: firma_vergiler.append("")
    
    f_headers = []
    for i in range(4):
        f = firmalar[i].strip()
        v = firma_vergiler[i].strip()
        f_text = f"{f}" if f else ""
        if v:
            if len(v) == 10:
                f_text += f"<br/>(Vergi No: {v})"
            elif len(v) == 11:
                f_text += f"<br/>(T.C. No: {v})"
            else:
                f_text += f"<br/>({v})"
        f_headers.append(Paragraph(f_text, style_center))
        
    row3 = [Paragraph("Sıra<br/>No", style_center), Paragraph("Yaklaşık Maliyeti Hesaplanacak Mal ve Hizmetin", style_center), "", "", "", f_headers[0], "", f_headers[1], "", f_headers[2], "", f_headers[3], "", Paragraph("Birim Yaklaşık<br/>Maliyet<br/>Fiyatı", style_center), Paragraph("Toplam<br/>Yaklaşık<br/>Maliyet<br/>Fiyatı", style_center)]
    table_data.append(row3)
    
    row4 = ["", Paragraph("Cinsi", style_center), Paragraph("Özelliği", style_center), Paragraph("Miktarı", style_center), Paragraph("Ölçüsü", style_center)]
    for i in range(4):
        row4.extend([Paragraph("Birim<br/>Fiyat", style_center), Paragraph("Toplam<br/>Fiyat", style_center)])
    row4.extend(["", ""])
    table_data.append(row4)
    
    kalemler = veri.get("kalemler", [])
    gecerli_kalemler = [k for k in kalemler if k.get("cins", "").strip()]
    if not gecerli_kalemler:
        gecerli_kalemler = [{}]
        
    col_sums = [0.0, 0.0, 0.0, 0.0, 0.0]
    
    for idx, k in enumerate(gecerli_kalemler):
        val = str(k.get("miktar", ""))
        miktar_float = 0.0
        try:
            miktar_float = float(val)
            if miktar_float == int(miktar_float): val = str(int(miktar_float))
        except: pass
        
        row = [
            Paragraph(str(idx+1), style_center),
            Paragraph(k.get("cins", ""), style_normal),
            Paragraph(k.get("ozellik", ""), style_normal),
            Paragraph(val, style_center),
            Paragraph(k.get("birim", ""), style_center)
        ]
        
        fiyatlar = k.get("fiyatlar", [])
        gecerli_fiyatlar = []
        
        for fidx in range(4):
            bf = ""
            tf = ""
            if fidx < len(fiyatlar) and fiyatlar[fidx] not in ["", None]:
                try:
                    fiyat_val = float(fiyatlar[fidx])
                    if fiyat_val > 0:
                        bf = f"{fiyat_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        tf_float = fiyat_val * miktar_float
                        tf = f"{tf_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        gecerli_fiyatlar.append(fiyat_val)
                        col_sums[fidx] += tf_float
                except:
                    pass
            row.extend([Paragraph(bf, style_right), Paragraph(tf, style_right)])
            
        yak_maliyet_birim = ""
        yak_maliyet_toplam = ""
        if gecerli_fiyatlar:
            ymb = sum(gecerli_fiyatlar) / len(gecerli_fiyatlar)
            ymt = ymb * miktar_float
            yak_maliyet_birim = f"{ymb:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            yak_maliyet_toplam = f"{ymt:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            col_sums[4] += ymt
            
        row.extend([Paragraph(yak_maliyet_birim, style_right), Paragraph(yak_maliyet_toplam, style_right)])
        table_data.append(row)
        
    t_row = [
        "", Paragraph("Kişiler / Firmalarca Bildirilen Yaklaşık Maliyet Fiyatları Toplamı ( KDV HARİÇ )", style_normal), "", "", "", 
        Paragraph("TOPLAM", style_center), Paragraph(f"{col_sums[0]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if col_sums[0]>0 else "", style_center), 
        Paragraph("TOPLAM", style_center), Paragraph(f"{col_sums[1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if col_sums[1]>0 else "", style_center), 
        Paragraph("TOPLAM", style_center), Paragraph(f"{col_sums[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if col_sums[2]>0 else "", style_center), 
        Paragraph("TOPLAM", style_center), Paragraph(f"{col_sums[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if col_sums[3]>0 else "", style_center), 
        Paragraph("TOPLAM", style_center), Paragraph(f"{col_sums[4]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if col_sums[4]>0 else "", style_center)
    ]
    table_data.append(t_row)
        
    col_widths = [8*mm, 25*mm, 30*mm, 12*mm, 15*mm, 17*mm, 18*mm, 17*mm, 18*mm, 17*mm, 18*mm, 17*mm, 18*mm, 20*mm, 20*mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=5)
    
    t_style = [
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        
        # Row 0 merges
        ('SPAN', (0,0), (4,0)),
        ('SPAN', (5,0), (12,0)),
        ('SPAN', (13,0), (14,2)), # Idarece Tesbit spans rows 0,1,2 and cols 13,14
        
        # Row 1 merges
        ('SPAN', (0,1), (4,1)),
        ('SPAN', (5,1), (12,1)),
        
        # Row 2 merges
        ('SPAN', (0,2), (2,2)),
        ('SPAN', (3,2), (4,2)),
        ('SPAN', (5,2), (12,2)),
        
        # Row 3 merges
        ('SPAN', (0,3), (0,4)), # Sira No
        ('SPAN', (1,3), (4,3)), # Mal ve Hizmet
        ('SPAN', (5,3), (6,3)), # Firm 1
        ('SPAN', (7,3), (8,3)), # Firm 2
        ('SPAN', (9,3), (10,3)), # Firm 3
        ('SPAN', (11,3), (12,3)), # Firm 4
        ('SPAN', (13,3), (13,4)), # Birim Yaklasik
        ('SPAN', (14,3), (14,4)), # Toplam Yaklasik
    ]
    
    # Dashed lines
    data_row_start = 4
    data_row_end = len(table_data) - 2 # Before total row
    if data_row_end >= data_row_start:
        for r in range(data_row_start, data_row_end + 1):
            t_style.append(('LINEBEFORE', (6, r), (6, r), 0.5, colors.black, None, (2, 2)))
            t_style.append(('LINEBEFORE', (8, r), (8, r), 0.5, colors.black, None, (2, 2)))
            t_style.append(('LINEBEFORE', (10, r), (10, r), 0.5, colors.black, None, (2, 2)))
            t_style.append(('LINEBEFORE', (12, r), (12, r), 0.5, colors.black, None, (2, 2)))
    
    # Total row merges
    last_row = len(table_data) - 1
    t_style.extend([
        ('SPAN', (1, last_row), (4, last_row)),
    ])
    
    t.setStyle(TableStyle(t_style))
    elements.append(t)
    
    elements.append(Spacer(1, 4*mm))
    
    p1 = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;İdaremizce ihtiyaç duyulan ve satın alınması düşünülen aşağıda cinsi, özellikleri ve miktarları yazılı malların / hizmetlerin 4734 Sayılı Kamu İhale Kanunu'nun 9'uncu Maddesi gereğince yaklaşık maliyetinin tesbitine esas olmak üzere; ilgili kişi kurum ve firmalardan yaklaşık maliyetinin tesbitine esas olmak üzere, her türlü fiyat araştırması yapılmıştır. Araştırma sonuçları yukarıda tabloda gösterilmiştir."
    p2 = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Yukarıda açıklandığı üzere, ihaleye çıkılması düşünülen mal / hizmetlerin fiyat araştırması neticesinde; 4734 Sayılı İhale Kanunu'nun 9. Maddesi gereğince yaklaşık maliyetinin KDV hariç yukarıda belirtildiği gibi takdir ve tesbit edilerek iş bu Hesap Cetveli tarafımca / tarafımızca düzenlenerek imza altına alınmıştır."
    
    elements.append(Paragraph(p1, style_normal))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(p2, style_normal))
    elements.append(Spacer(1, 5*mm))
    
    elements.append(Paragraph("Y A K L A Ş I K   M A L İ Y E T İ   Y A P A N   G Ö R E V L İ / G Ö R E V L İ L E R", style_center))
    elements.append(Spacer(1, 5*mm))
    
    def get_komisyon_local(veri):
        secimler = veri.get("komisyon", {})
        ids = ["ihale_kom_yaklasik_1", "ihale_kom_yaklasik_2", "ihale_kom_yaklasik_3"]
        uyeler = []
        for i in ids:
            u = secimler.get(i)
            if u: uyeler.append(u)
        return uyeler
        
    komisyon_uyeleri = get_komisyon_local(veri)
    if len(komisyon_uyeleri) > 0:
        imza_data = [[]]
        for idx, uye in enumerate(komisyon_uyeleri):
            title = "Başkan" if idx == 0 else "Üye"
            imza_data[0].append(Paragraph(f"{uye}<br/>{title}", style_center))
        
        col_w = 260*mm / len(komisyon_uyeleri)
        sig_table = Table(imza_data, colWidths=[col_w] * len(komisyon_uyeleri))
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(sig_table)
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("Not:Yaklaşık Maliyet Hesap Cetveli ve Ekleri İhale Onay Belgesi'ne Eklenecektir.", style_normal))
    
    doc.build(elements)
    return dosya_adi
"""

pattern = r"def uret_yaklasik_maliyet_pdf\(veri, hedef_klasor\):[\s\S]*?(?=\n\n#|$|\n\ndef uret_yaklasik_maliyet_excel)"
content = re.sub(pattern, lambda m: new_func, content, count=1)

with open("ihale_motoru.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Replaced!")
