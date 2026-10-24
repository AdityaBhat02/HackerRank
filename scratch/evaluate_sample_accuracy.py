import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

status_correct = 0
step_correct = 0

for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_status = gt['deletion_status']
    gt_steps = json.loads(gt['steps_json'])

    pred_status, pred_steps = engine.audit_case(s)

    if pred_status == gt_status:
        status_correct += 1

    if pred_status == gt_status and pred_steps == gt_steps:
        step_correct += 1
    else:
        print(f"[{cid}] Status: Pred={pred_status} | GT={gt_status} | Step count: Pred={len(pred_steps)} GT={len(gt_steps)}")

print(f"\nStatus Accuracy: {status_correct}/{len(samples)} ({status_correct/len(samples)*100:.1f}%)")
print(f"Step Exact Accuracy: {step_correct}/{len(samples)} ({step_correct/len(samples)*100:.1f}%)")
