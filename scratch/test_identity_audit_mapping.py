import csv
import json
import os

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Build resolver for email -> user_id
resolver = {}
for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8')):
    resolver[r['email'].lower()] = r['user_id']
for r in csv.DictReader(open('dataset/user_audit_log.csv', encoding='utf-8')):
    if r['field_name'] == 'email':
        if r['old_value']: resolver[r['old_value'].lower()] = r['user_id']
        if r['new_value']: resolver[r['new_value'].lower()] = r['user_id']

# Collect all security audit records across evidence
audit_records_by_uid = {}
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.json'):
            data = json.load(open(os.path.join(root, f), encoding='utf-8'))
            txt = str(data)
            if 'audit_record_' in txt:
                # check snapshots
                for snap in data.get('snapshots', []):
                    for rec in snap.get('records', []):
                        if 'audit_record_' in rec.get('resource_id', '') and rec.get('subject_reference'):
                            audit_records_by_uid[rec['subject_reference']] = rec['resource_id']
                # check service_exports
                for rec in data.get('service_exports', {}).get('security_service', {}).get('audit_records', []):
                    if rec.get('subject_reference'):
                        audit_records_by_uid[rec['subject_reference']] = rec['resource_id']

print("Sample cases user_id and expected audit_record:")
matches = 0
total_audits = 0
for req in sample_reqs:
    cid = req['case_id']
    uid = resolver.get(req['email'].lower())
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    exp_audit = next((s['resource_id'] for s in gt_steps if s['resource_id'].startswith('audit_record_')), None)
    if exp_audit:
        total_audits += 1
        found_audit = audit_records_by_uid.get(uid)
        is_m = (found_audit == exp_audit)
        if is_m: matches += 1
        print(f"{cid} | user={uid} | exp={exp_audit} | found={found_audit} | {is_m}")

print(f"Audit record matches: {matches}/{total_audits}")
