import csv
import json
import glob
import os
import re

manifest = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))

print(f"Total evidence files: {len(manifest)}")

for m in manifest:
    fid = m['file_id']
    fpath = os.path.join('dataset', m['file_path'])
    if not os.path.exists(fpath):
        continue
    content = open(fpath, 'r', encoding='utf-8', errors='ignore').read()
    
    # Find all user_XX mentioned
    users = sorted(list(set(re.findall(r'user_\d+', content))))
    # Find emails mentioned
    emails = sorted(list(set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content))))
    # Filter out northstar.shop internal emails
    cust_emails = [e for e in emails if not e.endswith('northstar.shop') and not e.endswith('company.com')]
    
    # Find resources mentioned
    resources = sorted(list(set(re.findall(r'(account_\d+|search_\d+|support_\d+|analytics_\d+|data_flow_\d+|backup_\d+|export_\d+|audit_record_\d+|tombstone_\d+)', content))))
    
    if users or cust_emails or resources:
        print(f"[{fid}] {m['captured_at']} | {os.path.basename(fpath)}")
        print(f"   Users ({len(users)}): {users[:8]}")
        print(f"   Cust Emails ({len(cust_emails)}): {cust_emails[:4]}")
        print(f"   Resources ({len(resources)}): {resources[:8]}")
