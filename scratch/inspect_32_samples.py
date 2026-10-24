import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case':8} | {'Status':14} | {'Reported':14} | {'Evidence':25} | {'Steps'} | {'Email'}")
print("-" * 105)
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    steps = json.loads(gt['steps_json'])
    eids = sorted(list(set(st['evidence_id'] for st in steps if st.get('evidence_id'))))
    print(f"{cid:8} | {gt['deletion_status']:14} | {s['reported_status']:14} | {str(eids):25} | {len(steps):5} | {s['email']}")
