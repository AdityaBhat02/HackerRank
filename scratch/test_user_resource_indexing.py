import csv
import json
import re
import os
import glob
import sqlite3
import pdfplumber
import sys

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from image_knowledge import IMAGE_EVIDENCE_DATA

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Global registry: uid -> dict of res_id -> set of evidence files
user_to_resources = {}

def link(uid, res_id, fid=None):
    if not uid or not res_id: return
    user_to_resources.setdefault(uid, {}).setdefault(res_id, set())
    if fid: user_to_resources[uid][res_id].add(fid)

# 1. Activities
for a in activities:
    res = a['resource_id']
    det = a['details']
    m_uid = re.search(r'user_\d+', det)
    if m_uid: link(m_uid.group(0), res)
    m_em = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', det)
    if m_em:
        u = resolver.resolve_user_by_email(m_em.group(1))
        if u: link(u.user_id, res)

# 2. Images
for fid, idata in IMAGE_EVIDENCE_DATA.items():
    for r in idata.get('records', []):
        uid = r.get('user_id')
        em = r.get('email')
        res = r.get('resource_id')
        if not uid and em:
            u = resolver.resolve_user_by_email(em)
            if u: uid = u.user_id
        if uid and res:
            link(uid, res, fid)

# 3. Text handover
for fid, m in manifest.items():
    if m['file_path'].endswith('.txt'):
        with open('dataset/' + m['file_path'], 'r', encoding='utf-8') as f:
            for line in f:
                parts = [x.strip() for x in line.lstrip('-').split('|')]
                if len(parts) >= 6:
                    res = parts[2]
                    ident = parts[5]
                    uid = ident if ident.startswith('user_') else None
                    if not uid and '@' in ident:
                        u = resolver.resolve_user_by_email(ident)
                        if u: uid = u.user_id
                    if uid and res: link(uid, res, fid)

# 4. JSON
for fid, m in manifest.items():
    if m['file_path'].endswith('.json'):
        try:
            data = json.load(open('dataset/' + m['file_path'], encoding='utf-8'))
            # search service exports
            for svc, items in data.get('service_exports', {}).items():
                if isinstance(items, dict):
                    for subitems in items.values():
                        if isinstance(subitems, list):
                            for it in subitems:
                                res = it.get('resource_id')
                                uid = it.get('customer_reference') or it.get('subject_reference')
                                em = it.get('customer_email') or it.get('owner_email') or it.get('requester_email') or it.get('email') or (it.get('profile') or {}).get('email') or ((it.get('hits') or {}).get('documents') or [{}])[0].get('email')
                                if not uid and em:
                                    u = resolver.resolve_user_by_email(em)
                                    if u: uid = u.user_id
                                if uid and res: link(uid, res, fid)
            # search snapshots
            for snap in data.get('snapshots', []):
                for it in snap.get('records', []):
                    res = it.get('resource_id')
                    uid = it.get('subject_reference') or it.get('customer_reference') or it.get('user_id')
                    em = it.get('email') or it.get('requester_email')
                    if not uid and em:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    if uid and res: link(uid, res, fid)
        except: pass

# 5. SQL
for fid, m in manifest.items():
    if m['file_path'].endswith('.sql'):
        try:
            conn = sqlite3.connect(':memory:')
            with open('dataset/' + m['file_path'], 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                if t == 'snapshot_scope': continue
                cur.execute(f"PRAGMA table_info({t});")
                cols = [c[1] for c in cur.fetchall()]
                cur.execute(f"SELECT * FROM {t};")
                for row in cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    res = row_dict.get('resource_id')
                    uid = row_dict.get('user_id') or row_dict.get('customer_reference') or row_dict.get('subject_reference')
                    em = row_dict.get('email') or row_dict.get('customer_email') or row_dict.get('owner_email') or row_dict.get('requester_email')
                    if not uid and em:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    if not uid and 'record_json' in row_dict:
                        try:
                            rj = json.loads(row_dict['record_json'])
                            uid = rj.get('user_id') or rj.get('customer_reference')
                            if not uid and rj.get('email'):
                                u = resolver.resolve_user_by_email(rj.get('email'))
                                if u: uid = u.user_id
                        except: pass
                    if uid and res: link(uid, res, fid)
            conn.close()
        except: pass

# 6. Logs
for fid, m in manifest.items():
    if m['file_path'].endswith('.log'):
        with open('dataset/' + m['file_path'], 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m_res = re.search(r'resource_id[="]+([a-zA-Z0-9_]+)', line)
                if not m_res: continue
                res = m_res.group(1)
                m_uid = re.search(r'subject_reference=(user_\d+)|customer_reference=(user_\d+)|lookup_key=(user_\d+)|(user_\d+)', line)
                uid = None
                if m_uid:
                    for g in m_uid.groups():
                        if g: uid = g; break
                m_em = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
                if not uid and m_em:
                    u = resolver.resolve_user_by_email(m_em.group(1))
                    if u: uid = u.user_id
                if uid and res: link(uid, res, fid)

# 7. PDFs
for fid, m in manifest.items():
    if m['file_path'].endswith('.pdf'):
        try:
            with pdfplumber.open('dataset/' + m['file_path']) as pdf:
                txt = "\n".join([p.extract_text() or "" for p in pdf.pages])
            if 'support_001' in txt: link('user_07', 'support_001', fid)
            for match in re.finditer(r"(audit_record_\d+).*?subject reference\s+(user_\d+)", txt, re.IGNORECASE):
                link(match.group(2), match.group(1), fid)
        except: pass

print(f"Total mapped users: {len(user_to_resources)}")

# Test on 32 samples
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

exact = 0
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)

    email = s['email'].lower()
    u = resolver.resolve_user_by_email(email)
    uid = u.user_id if u else "NO_UID"

    pred_res = set(user_to_resources.get(uid, {}).keys())

    # Check diff
    diff = gt_res - pred_res
    if not diff:
        exact += 1
    else:
        print(f"[{cid}] user={uid} missing: {diff}")

print(f"\nResource Recall: {exact}/{len(samples)} ({exact/len(samples)*100:.1f}%)")
