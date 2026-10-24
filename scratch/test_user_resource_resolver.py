import csv
import json
import re
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from request_classifier import RequestClassifier
from image_knowledge import IMAGE_EVIDENCE_DATA

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
classifier = RequestClassifier()
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Let's map each sample case's ground truth resources to see how they can be retrieved
for s in samples:
    cid = s['case_id']
    email = s['email'].lower()
    u = resolver.resolve_user_by_email(email)
    uid = u.user_id if u else "NO_UID"
    all_emails = u.all_emails if u else {email}

    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)

    print(f"\n[{cid}] user={uid} email={email}")
    print(f"  GT resources ({len(gt_res)}): {sorted(list(gt_res))}")
