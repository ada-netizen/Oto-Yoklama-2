with open('pdf_motoru.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = (
    '            c.setFont(self.font, 8)\n'
    '            c.drawString(kutu_x_sol, kutu_y_alt - 15, self.metin_duzelt(\n'
    '                "Not: Toplam devamsızlık süresi 10 gün özürsüz, 20 gün özürlü olmak üzere 30 gün ile sınırlıdır. Her 5 geç devamsızlık yarım gün özürsüz devamsızlık olarak toplam devamsızlığa eklenir."\n'
    '            ))'
)

new = (
    '            c.setFont(self.font, 8)\n'
    '            not_metni = self.metin_duzelt(\n'
    '                "Not: Toplam devamsızlık süresi 10 gün özürsüz, 20 gün özürlü olmak üzere 30 gün ile sınırlıdır. "\n'
    '                "Her 5 geç devamsızlık yarım gün özürsüz devamsızlık olarak toplam devamsızlığa eklenir."\n'
    '            )\n'
    '            from reportlab.platypus import Paragraph\n'
    '            from reportlab.lib.styles import ParagraphStyle\n'
    "            style_not = ParagraphStyle(name='Not', fontName=self.font, fontSize=8, leading=10)\n"
    '            not_p = Paragraph(not_metni, style_not)\n'
    '            not_genislik = kutu_x_sag - kutu_x_sol\n'
    '            not_w, not_h = not_p.wrapOn(c, not_genislik, 40)\n'
    '            not_p.drawOn(c, kutu_x_sol, kutu_y_alt - not_h - 4)'
)

if old in content:
    content = content.replace(old, new)
    with open('pdf_motoru.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced OK')
else:
    print('Pattern not found - showing lines 345-352:')
    lines = content.splitlines()
    for i, l in enumerate(lines[344:353], start=345):
        print(f'{i}: {repr(l)}')
