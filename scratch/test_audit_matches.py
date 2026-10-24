import csv
from build_audit_record_map import audit_records_by_user
import sys, os
sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

cases_with_audit = [cid for cid, r in outputs.items() if 'audit_record' in r['steps_json']]
matched = 0
for cid in cases_with_audit:
    s = [x for x in samples if x['case_id'] == cid][0]
    u = resolver.resolve_user_by_email(s['email'])
    uid = u.user_id if u else "none"
    if uid in audit_records_by_user:
        matched += 1
    else:
        print(f"{cid} user={uid} email={s['email']} audit_record NOT found")
print(f"Sample audit records matched: {matched}/{len(cases_with_audit)}")
