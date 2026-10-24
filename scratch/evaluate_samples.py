import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"Running evaluation on {len(samples)} sample cases...\n")

status_matches = 0
total_steps_matches = 0
exact_matches = 0

for s in samples:
    cid = s['case_id']
    gt = ground_truth[cid]
    gt_status = gt['deletion_status']
    gt_steps = json.loads(gt['steps_json'])

    pred_status, pred_steps = engine.audit_case(s)

    status_ok = (pred_status == gt_status)
    if status_ok:
        status_matches += 1

    steps_ok = (pred_steps == gt_steps)
    if steps_ok:
        exact_matches += 1
    else:
        print(f"[{cid}] status: {pred_status} (gt: {gt_status}) | steps: {len(pred_steps)} (gt: {len(gt_steps)})")
        if not status_ok:
            print(f"   STATUS MISMATCH: pred={pred_status}, gt={gt_status}")
        else:
            print("   Pred steps:")
            for st in pred_steps:
                print("     ", st)
            print("   GT steps:")
            for st in gt_steps:
                print("     ", st)

print(f"\nResults on Sample Dataset:")
print(f"Status Accuracy: {status_matches}/{len(samples)} ({status_matches/len(samples)*100:.1f}%)")
print(f"Exact Steps Accuracy: {exact_matches}/{len(samples)} ({exact_matches/len(samples)*100:.1f}%)")
