import time
import os
import glob
import json
import sqlite3
import re
import csv
import pdfplumber
import sys
sys.path.insert(0, os.path.abspath('code'))
from image_knowledge import IMAGE_EVIDENCE_DATA

start = time.time()
print("Starting full evidence parsing test...")

manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
print(f"Loaded manifest with {len(manifest)} files.")

# Count each type
parsed_records = []

for fid, m in manifest.items():
    fpath = os.path.join('dataset', m['file_path'])
    origin = m['origin']
    captured_at = m['captured_at']
    ext = os.path.splitext(fpath)[1].lower()

    if ext == '.json':
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            parsed_records.append((fid, 'json', captured_at, len(str(data))))
        except Exception as e:
            print(f"Error {fid} {fpath}: {e}")

    elif ext == '.txt':
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed_records.append((fid, 'txt', captured_at, len(content)))
        except Exception as e:
            print(f"Error {fid} {fpath}: {e}")

    elif ext == '.sql':
        try:
            conn = sqlite3.connect(':memory:')
            with open(fpath, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.close()
            parsed_records.append((fid, 'sql', captured_at, 1))
        except Exception as e:
            print(f"Error {fid} {fpath}: {e}")

    elif ext == '.pdf':
        try:
            with pdfplumber.open(fpath) as pdf:
                text = "".join([p.extract_text() or "" for p in pdf.pages])
            parsed_records.append((fid, 'pdf', captured_at, len(text)))
        except Exception as e:
            print(f"Error {fid} {fpath}: {e}")

    elif ext == '.png':
        records = IMAGE_EVIDENCE_DATA.get(fid, {}).get('records', [])
        parsed_records.append((fid, 'image', captured_at, len(records)))

print(f"Successfully processed {len(parsed_records)} / {len(manifest)} evidence files in {time.time() - start:.2f}s!")
