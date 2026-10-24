import csv
import json
import glob
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

# pyrefly: ignore[missing-import]
from identity import IdentityResolver


resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
sample_outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Check for each sample case:
# What identifiers do they have?
for s in samples[:10]:
    cid = s['case_id']
    email = s['email']
    user = resolver.resolve_user_by_email(email)
    uid = user.user_id if user else "UNKNOWN"
    emails = user.all_emails if user else {email.lower()}
    out = sample_outputs[cid]
    steps = json.loads(out['steps_json'])
    res_list = [st['resource_id'] for st in steps]
    print(f"[{cid}] user={uid} email={email} res={res_list}")
