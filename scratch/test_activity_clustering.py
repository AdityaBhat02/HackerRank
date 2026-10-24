import csv
import json
import re
from datetime import datetime

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Filter deletion worker activities
del_acts = [a for a in activities if a['source_system'] == 'deletion_worker']
for a in del_acts:
    a['dt'] = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))

print(f"Total deletion worker activities: {len(del_acts)}")

# Group activities by clustering in time:
# In Northstar shop, a deletion job runs tasks for one user in rapid succession (within a few minutes of each other)!
# Let's inspect the time gaps between operations
for cid in ['case_27', 'case_28', 'case_29', 'case_30', 'case_03', 'case_11', 'case_18']:
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)
    matching_acts = [a for a in del_acts if a['resource_id'] in gt_res]
    print(f"\n[{cid}] GT resources in activity ({len(matching_acts)}/{len(gt_res)}):")
    for a in matching_acts:
        print(f"  {a['event_time']} | {a['target_system']:20} | {a['resource_id']:18} | {a['event_type']:18} | {a['reported_result']}")
