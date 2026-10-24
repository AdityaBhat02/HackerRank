import csv
import json

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case':8} | {'User ID':8} | {'Email':25} | {'Reported At':20} | {'Expected Account'}")
print("-" * 80)
for req in sample_reqs:
    cid = req['case_id']
    email = req['email']
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    acc = next((s['resource_id'] for s in gt_steps if s['resource_id'].startswith('account_')), "NONE")
    print(f"{cid:8} | {email:30} | {req['reported_at']:20} | {acc}")
