import glob
import os

log_files = sorted(glob.glob('dataset/evidence/logs/*.log'))
print(f"Total log files: {len(log_files)}")

for fpath in log_files:
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8') as f:
        first_few = [f.readline().strip() for _ in range(3)]
    print(f"\n{fname}:")
    for l in first_few:
        if l:
            print("  ", l[:140])
