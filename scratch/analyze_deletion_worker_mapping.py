import csv
import json
from datetime import datetime

requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

del_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

print(f"Total deletion requests: {len(requests)}")
print(f"Total deletion_worker activities: {len(del_acts)}")

# Let's check how many deletion_worker activities exist per day
by_date = {}
for a in del_acts:
    d = a['event_time'][:10]
    by_date.setdefault(d, []).append(a)

print(f"Distinct dates with deletion worker activity: {len(by_date)}")

# Let's test matching each sample case to its deletion_worker activities
for s in samples[:15]:
    cid = s['case_id']
    req_at = s['requested_at']
    rep_at = s['reported_at']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)
    
    # Check all deletion_worker activities between requested_at and reported_at + 2 hours
    cand_acts = [a for a in del_acts if req_at <= a['event_time'] <= rep_at + 'Z']
    
    print(f"\n[{cid}] req={req_at} rep={rep_at} gt_res={gt_res}")
    for a in cand_acts:
        if a['resource_id'] in gt_res:
            print(f"  MATCH: {a['event_time']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
        else:
            print(f"  other: {a['event_time']} | {a['target_system']} | {a['resource_id']}")
