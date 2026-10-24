import glob
import json
import sqlite3
import re
import pdfplumber

audit_records_by_user = {}

# JSON
for p in glob.glob('dataset/evidence/**/*.json', recursive=True):
    try:
        data = json.load(open(p, encoding='utf-8'))
        for item in data.get('service_exports', {}).get('security_service', {}).get('audit_records', []):
            uid = item.get('subject_reference')
            rid = item.get('resource_id')
            if uid and rid: audit_records_by_user[uid] = rid
        for snap in data.get('snapshots', []):
            for item in snap.get('records', []):
                rid = item.get('resource_id', '')
                if 'audit_record' in rid:
                    uid = item.get('subject_reference') or item.get('user_id')
                    if uid: audit_records_by_user[uid] = rid
    except: pass

# SQL
for p in glob.glob('dataset/evidence/**/*.sql', recursive=True):
    try:
        conn = sqlite3.connect(':memory:')
        with open(p, 'r', encoding='utf-8') as f: conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for t in [r[0] for r in cur.fetchall()]:
            if 'security_audit_records' in t or 'audit' in t:
                cur.execute(f"SELECT resource_id, subject_reference FROM {t}")
                for rid, uid in cur.fetchall():
                    if uid and rid: audit_records_by_user[uid] = rid
        conn.close()
    except: pass

# LOGS
for p in glob.glob('dataset/evidence/**/*.log', recursive=True):
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'audit_record_' in line:
                    m_rid = re.search(r'resource_id=(audit_record_\d+)', line)
                    m_uid = re.search(r'(?:subject_reference|lookup_key)=(user_\d+)', line)
                    if m_rid and m_uid:
                        audit_records_by_user[m_uid.group(1)] = m_rid.group(1)
    except: pass

# PDF
for p in glob.glob('dataset/evidence/**/*.pdf', recursive=True):
    try:
        with pdfplumber.open(p) as pdf:
            txt = '\n'.join([page.extract_text() or '' for page in pdf.pages])
            for m in re.finditer(r'(audit_record_\d+).*?(user_\d+)', txt):
                audit_records_by_user[m.group(2)] = m.group(1)
    except: pass

# TXT
for p in glob.glob('dataset/evidence/**/*.txt', recursive=True):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                if 'audit_record_' in line:
                    parts = [x.strip() for x in line.lstrip('-').split('|')]
                    if len(parts) >= 6:
                        res = parts[2]
                        ident = parts[5]
                        if ident.startswith('user_'):
                            audit_records_by_user[ident] = res
    except: pass

print(f"Total users with audit records from all evidence: {len(audit_records_by_user)}")
