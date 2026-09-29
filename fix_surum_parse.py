with open('guncelleyici.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace lines 14-17 (surum_parse function)
new_func = [
    'def surum_parse(surum):\n',
    '    """v1.9, v1.10, v2.3.1.1 gibi surumleri dogru sirada karsilastirir.\n',
    '    packaging.version yerine tuple karsilastirmasi kullanilir;\n',
    '    boylece 4+ parcali versiyonlar da sorunsuz calisir.\n',
    '    """\n',
    '    temiz = str(surum).strip().lower().removeprefix("v")\n',
    '    try:\n',
    '        return tuple(int(x) for x in temiz.split("."))\n',
    '    except ValueError:\n',
    '        return (0,)\n',
]

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('def surum_parse'):
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip().startswith('def '):
        end_idx = i
        break

print(f'surum_parse: lines {start_idx+1} to {end_idx}')

new_lines = lines[:start_idx] + new_func + ['\n'] + lines[end_idx:]

# Fix the except clause - remove InvalidVersion
result = []
for line in new_lines:
    if 'except (OSError, InvalidVersion,' in line:
        line = line.replace('except (OSError, InvalidVersion, KeyError, TypeError, ValueError, json.JSONDecodeError):', 
                           'except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):')
    if 'from packaging.version import' in line:
        line = ''  # Remove this import
    result.append(line)

with open('guncelleyici.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

print('Done')
