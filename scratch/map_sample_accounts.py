import csv
import json
from datetime import datetime

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
del_acts = [r for r in csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')) if r['source_system'] == 'deletion_worker' and r['target_system'] == 'account_service']

print("Case ID | Reported At | Expected Account | Closest Worker Account | Diff Minutes | Match?")
for req in sample_reqs:
    cid = req['case_id']
    rep_at = req['reported_at']
    rep_dt = datetime.fromisoformat(rep_at.replace('Z', '+00:00'))
    
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    exp_acc = next((s['resource_id'] for s in gt_steps if s['resource_id'].startswith('account_')), None)
    
    # Find closest deletion_worker on account_service
    best_diff = 999999999
    best_act = None
    for a in del_acts:
        adt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        diff = abs((adt - rep_dt).total_seconds())
        # The worker event is usually BEFORE reported_at (or within a few hours)
        if diff < best_diff:
            best_diff = diff
            best_act = a
            
    closest_acc = best_act['resource_id'] if best_act else None
    diff_min = best_diff / 60
    is_match = (closest_acc == exp_acc)
    print(f"{cid:8} | {rep_at:20} | {str(exp_acc):16} | {str(closest_acc):22} | {diff_min:8.1f}m | {is_match}")
