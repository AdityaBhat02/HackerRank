import glob
import os

target_accounts = ['account_7566', 'account_6440', 'account_3960', 'account_9797', 'account_9102']

for root, dirs, files in os.walk('dataset'):
    for f in files:
        if f.endswith(('.csv', '.json', '.log', '.sql', '.txt')):
            fpath = os.path.join(root, f)
            try:
                content = open(fpath, 'r', encoding='utf-8', errors='ignore').read()
                for acc in target_accounts:
                    if acc in content:
                        print(f"Found {acc} in {fpath}")
            except Exception:
                pass
