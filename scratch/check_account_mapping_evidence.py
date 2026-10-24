import csv
import json
import glob
import re

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
manifest = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))

# Build a map from account_id -> user/email across ALL evidence files
account_to_user = {}

# 1. Check all log files for profile_lookup or account_
for m in manifest:
    if m['file_path'].endswith('.log'):
        with open('dataset/' + m['file_path'], 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'account_' in line:
                    m_acc = re.search(r'account_\d+', line)
                    m_em = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
                    m_uid = re.search(r'user_\d+', line)
                    if m_acc:
                        acc = m_acc.group(0)
                        if m_em:
                            account_to_user.setdefault(acc, set()).add(m_em.group(1).lower())
                        if m_uid:
                            account_to_user.setdefault(acc, set()).add(m_uid.group(0))

# 2. Check all JSON files
for m in manifest:
    if m['file_path'].endswith('.json'):
        try:
            data = json.load(open('dataset/' + m['file_path'], encoding='utf-8'))
            text = json.dumps(data)
            # search for account_
            for m_acc in re.finditer(r'account_\d+', text):
                acc = m_acc.group(0)
                # find nearby context
                start = max(0, m_acc.start() - 200)
                end = min(len(text), m_acc.end() + 200)
                ctx = text[start:end]
                for m_em in re.finditer(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', ctx):
                    account_to_user.setdefault(acc, set()).add(m_em.group(1).lower())
                for m_uid in re.finditer(r'user_\d+', ctx):
                    account_to_user.setdefault(acc, set()).add(m_uid.group(0))
        except: pass

print(f"Mapped accounts: {len(account_to_user)}")

# Check against sample GT
correct = 0
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_acc = [st['resource_id'] for st in gt_steps if st['system_id'] == 'account_service']
    gt_acc = gt_acc[0] if gt_acc else None

    em = s['email'].lower()
    matched_accs = [acc for acc, users in account_to_user.items() if em in users]
    print(f"[{cid}] em={em} GT={gt_acc} | Matched={matched_accs}")
    if gt_acc and gt_acc in matched_accs:
        correct += 1

print(f"Direct email->account match: {correct}/{len(samples)}")
