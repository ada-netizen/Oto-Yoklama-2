with open('pdf_motoru.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line index of the not_metni block and replace it
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'not_metni = self.metin_duzelt(' in line:
        start_idx = i - 1  # include the c.setFont line before it
        break

if start_idx is None:
    print('not_metni satiri bulunamadi')
    exit(1)

# Find end of block (drawOn line)
for i in range(start_idx, min(start_idx + 15, len(lines))):
    if 'not_p.drawOn' in lines[i]:
        end_idx = i
        break

if end_idx is None:
    print('drawOn satiri bulunamadi')
    exit(1)

print(f'Replacing lines {start_idx+1} to {end_idx+1}')
for l in lines[start_idx:end_idx+1]:
    print(repr(l))

replacement = [
    '            # Not: kutunun hemen altinda iki satir olarak yazilir\n',
    '            c.setFont(self.font, 8)\n',
    '            not_satir1 = self.metin_duzelt("Not: Toplam devamsızlık süresi 10 gün özürsüz, 20 gün özürlü olmak üzere 30 gün ile sınırlıdır.")\n',
    '            not_satir2 = self.metin_duzelt("Her 5 geç devamsızlık yarım gün özürsüz devamsızlık olarak toplam devamsızlığa eklenir.")\n',
    '            c.drawString(kutu_x_sol, kutu_y_alt - 12, not_satir1)\n',
    '            c.drawString(kutu_x_sol, kutu_y_alt - 22, not_satir2)\n',
]

new_lines = lines[:start_idx] + replacement + lines[end_idx+1:]

with open('pdf_motoru.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done')
