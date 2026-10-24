import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
manifest = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Pre-read all evidence files text
ev_contents = {}
for m in manifest:
    fid = m['file_id']
    fpath = os.path.join('dataset', m['file_path'])
    if os.path.exists(fpath):
        ev_contents[fid] = (m['captured_at'], open(fpath, 'r', encoding='utf-8', errors='ignore').read())

print("Testing evidence file matching for all 32 samples...")

correct_eids = 0
for s in samples:
    cid = s['case_id']
    email = s['email']
    audit_at = s['audit_at']
    u = resolver.resolve_user_by_email(email)
    uid = u.user_id if u else None
    emails = u.all_emails if u else {email.lower()}

    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_eids = set(st['evidence_id'] for st in gt_steps if st.get('evidence_id'))

    # Find matching evidence files captured <= audit_at
    candidate_eids = set()
    for fid, (cap_at, text) in ev_contents.items():
        if cap_at <= audit_at:
            matched = False
            if uid and uid in text:
                matched = True
            if not matched:
                for em in emails:
                    if em in text.lower():
                        matched = True
                        break
            if matched:
                candidate_eids.add(fid)

    diff = gt_eids - candidate_eids
    if not diff:
        correct_eids += 1
    else:
        print(f"[{cid}] Exp: {gt_eids} | Matched: {candidate_eids} | Missing: {diff}")

print(f"\nEvidence File Recall: {correct_eids}/{len(samples)} ({correct_eids/len(samples)*100:.1f}%)")
