import csv
import json
import glob

# Load all activities
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
act_by_res = {}
for a in activities:
    res = a['resource_id']
    act_by_res.setdefault(res, []).append(a)

outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Check all resources across sample outputs
all_res = set()
for cid, out in outputs.items():
    steps = json.loads(out['steps_json'])
    for st in steps:
        all_res.add(st['resource_id'])

print(f"Total distinct resources in sample outputs: {len(all_res)}")
in_activity = sum(1 for r in all_res if r in act_by_res)
print(f"Resources found in system_activity.csv: {in_activity} / {len(all_res)}")

missing_from_activity = [r for r in all_res if r not in act_by_res]
print(f"Resources not in system_activity.csv ({len(missing_from_activity)}):", missing_from_activity[:10])
