import os

with open('app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

personel_start = -1
ihale_start = -1

for i, line in enumerate(lines):
    if 'PERSONEL' in line and 'Y' in line and 'NET' in line:
        personel_start = i
    if 'let ihaleKalemleri' in line:
        ihale_start = i - 2
        break

if personel_start == -1 or ihale_start == -1:
    print('Could not find markers:', personel_start, ihale_start)
    exit(1)

core_lines = lines[:personel_start]
personel_lines = lines[personel_start:ihale_start]
ihale_lines = lines[ihale_start:]

with open('js/core.js', 'w', encoding='utf-8') as f:
    f.writelines(core_lines)
    
with open('js/personel_teblig.js', 'w', encoding='utf-8') as f:
    f.writelines(personel_lines)
    
with open('js/ihale.js', 'w', encoding='utf-8') as f:
    f.writelines(ihale_lines)

print('Split successfully!')
