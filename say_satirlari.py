import os

extensions = {'.py', '.js', '.html', '.css'}
skip_dirs = {'dist', '__pycache__', '.git', 'node_modules'}
skip_name_prefixes = ('fix_', 'revert_', 'build_')

totals = {}
files_detail = []

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        ext = os.path.splitext(fname)[1]
        if ext not in extensions:
            continue
        if any(fname.startswith(p) for p in skip_name_prefixes):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, encoding='utf-8', errors='ignore') as f:
                count = sum(1 for _ in f)
        except Exception:
            count = 0
        totals[ext] = totals.get(ext, 0) + count
        files_detail.append((count, ext, fname))

files_detail.sort(reverse=True)

print("=== EN BÜYÜK 10 DOSYA ===")
for count, ext, fname in files_detail[:10]:
    print(f"  {count:>5} satır  {fname}")

print()
print("=== TOPLAM ===")
grand = 0
for ext, count in sorted(totals.items()):
    print(f"  {ext:<6} → {count:>6} satır")
    grand += count
print(f"  ─────────────────")
print(f"  TOPLAM → {grand:>6} satır")
print(f"  ({len(files_detail)} dosya)")
