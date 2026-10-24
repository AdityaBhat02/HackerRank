import csv
import json
import os
import re

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

resolver = {}
for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')):
    resolver[r['email'].lower()] = r['user_id']
for r in csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')):
    if r['field_name'] == 'email':
        if r['old_value']: resolver[r['old_value'].lower()] = r['user_id']
        if r['new_value']: resolver[r['new_value'].lower()] = r['user_id']

audit_map = {}

# 1. JSON Files
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.json'):
            try:
                data = json.load(open(os.path.join(root, f), encoding='utf-8'))
            except: continue
            for snap in data.get('snapshots', []):
                for rec in snap.get('records', []):
                    if rec.get('resource_id', '').startswith('audit_record_') and rec.get('subject_reference'):
                        audit_map[rec['subject_reference']] = rec['resource_id']
            for rec in data.get('service_exports', {}).get('security_service', {}).get('audit_records', []):
                if rec.get('subject_reference'):
                    audit_map[rec['subject_reference']] = rec['resource_id']

# 2. Logs with both JSON and KV trace correlation
for root, dirs, files in os.walk('dataset/evidence/logs'):
    for f in files:
        if f.endswith('.log'):
            traces = {}
            with open(os.path.join(root, f), encoding='utf-8', errors='ignore') as logf:
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
                                if str(obj.get(k, '')).startswith('user_'):
                                    uid = obj[k]
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
                            
                    if tr_id:
                        tr = traces.setdefault(tr_id, {'uids': set(), 'audits': set()})
                        if aud: tr['audits'].add(aud)
                        if uid: tr['uids'].add(uid)
                        
            for tr_id, tr in traces.items():
                if tr['audits'] and tr['uids']:
                    for u in tr['uids']:
                        for a in tr['audits']:
                            audit_map[u] = a

print("Checking audit_record matches for all 32 sample cases:")
matches = 0
total = 0
for req in sample_reqs:
    cid = req['case_id']
    uid = resolver.get(req['email'].lower())
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    exp_audit = next((s['resource_id'] for s in gt_steps if s['resource_id'].startswith('audit_record_')), None)
    if exp_audit:
        total += 1
        found = audit_map.get(uid)
        is_ok = (found == exp_audit)
        if is_ok: matches += 1
        print(f"  {cid:8} | user={uid:8} | exp={exp_audit:18} | found={str(found):18} | {is_ok}")

print(f"Total audit_record matches: {matches}/{total}")
