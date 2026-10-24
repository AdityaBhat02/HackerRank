import glob
import os

print("--- Inspecting Log Files ---")
for p in sorted(glob.glob('dataset/evidence/logs/*.log'))[:10]:
    fname = os.path.basename(p)
    with open(p, 'r', encoding='utf-8') as f:
        lines = [f.readline().strip() for _ in range(5)]
    print(f"\n{fname}:")
    for l in lines:
        if l:
            print("  ", l[:120])
