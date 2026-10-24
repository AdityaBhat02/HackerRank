import csv
import json
import sys
import os

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case':8} | {'Status':11} | {'GT Steps':8} | {'Resources in GT'}")
print("-" * 80)
for req in sample_reqs:
    cid = req['case_id']
    gt = ground_truth[cid]
    st = gt['deletion_status']
    steps = json.loads(gt['steps_json'])
    res_str = ", ".join(f"{s['system_id']}:{s['resource_id']}({s['operation']})" for s in steps)
    print(f"{cid:8} | {st:11} | {len(steps):8} | {res_str}")
