import csv
import json

samples = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Build user identities map by email and also check audit log
users_by_email = {r['email']: r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
audit_log = list(csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')))

# Check if any sample emails are in audit log
for al in audit_log:
    if al['field_name'] == 'email':
        users_by_email[al['old_value']] = {'user_id': al['user_id'], 'email': al['old_value'], 'from_audit': True}

print(f"Total samples: {len(samples)}")
for cid, out in sorted(outputs.items()):
    s = samples[cid]
    u = users_by_email.get(s['email'])
    uid = u['user_id'] if u else 'UNKNOWN'
    steps = json.loads(out['steps_json'])
    print(f"\n{cid} | Status: {out['deletion_status']} | User: {uid} | Email: {s['email']} | Steps: {len(steps)}")
    for st in steps:
        print(f"  [{st['phase']}] {st['system_id']} | {st['resource_id']} | {st['operation']} | {st['state']} | evid: {st.get('evidence_id')}")
