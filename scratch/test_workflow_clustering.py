import csv
import json
from datetime import datetime

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

del_acts = [r for r in csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')) if r['source_system'] == 'deletion_worker']

print("Case ID | Expected Resources | Worker Resources in Workflow Window")
print("=" * 80)

for req in sample_reqs[:10]:
    cid = req['case_id']
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    exp_res = set(s['resource_id'] for s in gt_steps)
    
    req_dt = datetime.fromisoformat(req['requested_at'].replace('Z', '+00:00'))
    rep_dt = datetime.fromisoformat(req['reported_at'].replace('Z', '+00:00'))
    
    cands = []
    for a in del_acts:
        adt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        # Activity within 2 hours of reported_at
        if -7200 <= (adt - rep_dt).total_seconds() <= 1800:
            cands.append(a['resource_id'])
            
    print(f"{cid:8} | exp={sorted(list(exp_res))} | worker={cands}")
