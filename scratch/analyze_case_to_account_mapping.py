import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

del_account_acts = [a for a in activities if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service']

print(f"Total del_account_acts: {len(del_account_acts)}")

# Check each sample case
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_acc = [st['resource_id'] for st in gt_steps if st['system_id'] == 'account_service']
    gt_acc = gt_acc[0] if gt_acc else None

    req_at = s['requested_at']
    rep_at = s['reported_at']

    # Find candidates near reported_at
    cands = [a for a in del_account_acts if a['event_time'] <= rep_at and a['event_time'] >= req_at]
    cands_res = [c['resource_id'] for c in cands]

    print(f"[{cid}] rep={rep_at} GT_acc={gt_acc} | cands={cands_res}")
