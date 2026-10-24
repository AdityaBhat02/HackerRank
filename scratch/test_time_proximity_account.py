import csv
import json
from datetime import datetime

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

del_account_acts = [a for a in activities if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service']

for a in del_account_acts:
    # parse ISO time
    a['dt'] = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))

correct = 0
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_acc = [st['resource_id'] for st in gt_steps if st['system_id'] == 'account_service']
    gt_acc = gt_acc[0] if gt_acc else None

    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    req_dt = datetime.fromisoformat(s['requested_at'].replace('Z', '+00:00'))

    # Sort candidates by abs(dt - rep_dt)
    sorted_cands = sorted(del_account_acts, key=lambda a: abs((a['dt'] - rep_dt).total_seconds()))

    best_match = None
    min_diff = 9999999
    for c in sorted_cands[:10]:
        diff = abs((c['dt'] - rep_dt).total_seconds())
        # Check if in a reasonable window (e.g. within 2 hours of reported_at)
        if diff < 7200:
            best_match = c['resource_id']
            min_diff = diff
            break

    is_correct = (best_match == gt_acc)
    if is_correct:
        correct += 1
    print(f"[{cid}] GT={gt_acc:12} | Best={str(best_match):12} | diff={min_diff:6.0f}s | {'MATCH' if is_correct else 'MISS'}")

print(f"\nTime-proximity Account Match: {correct}/{len(samples)} ({correct/len(samples)*100:.1f}%)")
