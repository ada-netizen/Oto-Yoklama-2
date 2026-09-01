import os

with open('api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'islem_durumlari =' in line:
        print('Already patched')
        exit(0)

print('Patching api.py...')
