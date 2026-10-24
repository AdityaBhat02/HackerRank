import os
import sys
import json
import csv
import re
from datetime import datetime

# Set up environment
dataset_dir = 'dataset'
sample_reqs = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# 1. Identity Resolver
resolver = {}
for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8')):
    resolver[r['email'].lower()] = r['user_id']
for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8')):
    if r['field_name'] == 'email':
        if r['old_value']: resolver[r['old_value'].lower()] = r['user_id']
        if r['new_value']: resolver[r['new_value'].lower()] = r['user_id']

# 2. Build Universal Audit Map: user_id -> (audit_record_id, file_id)
audit_map = {}
manifest = {r['file_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8'))}

# From JSON
for fid, m in manifest.items():
    if m['file_path'].endswith('.json'):
        fpath = os.path.join(dataset_dir, m['file_path'])
        try: data = json.load(open(fpath, encoding='utf-8'))
        except: continue
        for snap in data.get('snapshots', []):
            for rec in snap.get('records', []):
                rid = rec.get('resource_id', '')
                if rid.startswith('audit_record_'):
                    uid = rec.get('subject_reference')
                    if uid and uid not in audit_map:
                        audit_map[uid] = (rid, fid)
        for rec in data.get('service_exports', {}).get('security_service', {}).get('audit_records', []):
            rid = rec.get('resource_id', '')
            uid = rec.get('subject_reference')
            if uid and uid not in audit_map:
                audit_map[uid] = (rid, fid)

# From SQL
for fid, m in manifest.items():
    if m['file_path'].endswith('.sql'):
        fpath = os.path.join(dataset_dir, m['file_path'])
        try:
            txt = open(fpath, encoding='utf-8', errors='ignore').read()
            for m_aud in re.finditer(r"'(audit_record_\d+)',\s*'(user_\d+)'", txt):
                arid, uid = m_aud.groups()
                if uid not in audit_map:
                    audit_map[uid] = (arid, fid)
            for m_aud in re.finditer(r'["\']resource_id["\']:\s*["\'](audit_record_\d+)["\'],\s*["\']subject_reference["\']:\s*["\'](user_\d+)["\']', txt):
                arid, uid = m_aud.groups()
                if uid not in audit_map:
                    audit_map[uid] = (arid, fid)
        except: pass

# From Handover txt
for fid, m in manifest.items():
    if m['file_path'].endswith('.txt'):
        fpath = os.path.join(dataset_dir, m['file_path'])
        try:
            txt = open(fpath, encoding='utf-8', errors='ignore').read()
            for line in txt.splitlines():
                if 'audit_record_' in line:
                    m_aud = re.search(r'audit_record_\d+', line)
                    m_u = re.search(r'user_\d+', line)
                    m_em = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
                    arid = m_aud.group(0) if m_aud else None
                    uid = m_u.group(0) if m_u else (resolver.get(m_em.group(1).lower()) if m_em else None)
                    if uid and arid and uid not in audit_map:
                        audit_map[uid] = (arid, fid)
        except: pass

# From Logs with Trace Correlation
for fid, m in manifest.items():
    if m['file_path'].endswith('.log'):
        fpath = os.path.join(dataset_dir, m['file_path'])
        try:
            traces = {}
            with open(fpath, encoding='utf-8', errors='ignore') as logf:
                for line in logf:
                    tr_id = None
                    aud = None
                    uid = None
                    if '{' in line and '}' in line:
                        try:
                            obj = json.loads(line[line.find('{'):line.rfind('}')+1])
                            tr_id = obj.get('trace_id')
                            if str(obj.get('resource_id', '')).startswith('audit_record_'):
                                aud = obj['resource_id']
                            for k in ['subject_ref', 'subject_reference', 'user_id', 'correlation_key', 'lookup_key']:
                                v = str(obj.get(k, ''))
                                if v.startswith('user_'): uid = v
                                elif '@' in v and resolver.get(v.lower()): uid = resolver[v.lower()]
                        except: pass
                    else:
                        m_tr = re.search(r'trace_id[="]+([a-zA-Z0-9_-]+)', line)
                        if m_tr: tr_id = m_tr.group(1)
                        m_aud = re.search(r'resource_id[="]+(audit_record_\d+)', line)
                        if m_aud: aud = m_aud.group(1)
                        for pat in [r'subject_ref[="]+(user_\d+)', r'subject_reference[="]+(user_\d+)',
                                    r'lookup_key[="]+(user_\d+)', r'correlation_key[="]+(user_\d+)']:
                            m_u = re.search(pat, line)
                            if m_u: uid = m_u.group(1)
                        if not uid:
                            m_em = re.search(r'lookup_key[="]+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
                            if m_em and resolver.get(m_em.group(1).lower()):
                                uid = resolver[m_em.group(1).lower()]
                            
                    if tr_id:
                        tr = traces.setdefault(tr_id, {'uids': set(), 'audits': set()})
                        if aud: tr['audits'].add(aud)
                        if uid: tr['uids'].add(uid)
                        
            for tr_id, tr in traces.items():
                if tr['audits'] and tr['uids']:
                    for u in tr['uids']:
                        for a in tr['audits']:
                            if u not in audit_map:
                                audit_map[u] = (a, fid)
        except: pass

print(f"Total audit_map entries: {len(audit_map)}")
print("Audit map sample:", list(audit_map.items())[:10])
