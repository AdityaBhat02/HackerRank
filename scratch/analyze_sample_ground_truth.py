import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

samples = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
identities = {r['email']: r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
audit_log = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
evidence_manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# Map historical emails
user_by_email = dict(identities)
for al in audit_log:
    if al['field_name'] == 'email':
        user_by_email[al['old_value']] = {'user_id': al['user_id'], 'email': al['old_value'], 'name': '', 'phone': '', 'email_hash': ''}
        user_by_email[al['new_value']] = {'user_id': al['user_id'], 'email': al['new_value'], 'name': '', 'phone': '', 'email_hash': ''}

print(f"Total samples: {len(samples)}")

for cid, out in sorted(outputs.items()):
    s = samples[cid]
    u = user_by_email.get(s['email'])
    uid = u['user_id'] if u else 'UNKNOWN'
    steps = json.loads(out['steps_json'])
    audit_at = s['audit_at']
    
    # Check cited evidence files
    ev_ids = [st['evidence_id'] for st in steps if st.get('evidence_id')]
    ev_files = [evidence_manifest.get(eid, {}).get('file_path') for eid in ev_ids]
    
    # Check resources mentioned
    res_ids = [st['resource_id'] for st in steps]
    
    print(f"\n[{cid}] Status: {out['deletion_status']} | User: {uid} | AuditAt: {audit_at}")
    print(f"  Cited Evidence: {list(zip(ev_ids, ev_files))}")
    print(f"  Resources: {res_ids}")
