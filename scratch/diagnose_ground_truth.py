import csv
import json
import sys
import os

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print("=== PART 1: DUMP GROUND TRUTH DIFFS FOR STATUS MISSES ===")
for cid in ['case_08', 'case_12', 'case_19']:
    req = next(r for r in sample_reqs if r['case_id'] == cid)
    gt = ground_truth[cid]
    gt_status = gt['deletion_status']
    gt_steps = json.loads(gt['steps_json'])
    
    pred_status, pred_steps = engine.audit_case(req)
    
    print(f"\n--- {cid} ---")
    print(f"Request: {req['request_text']}")
    print(f"Email: {req['email']}, Requested: {req['requested_at']}, Reported: {req['reported_at']}, Audit: {req['audit_at']}")
    print(f"GT Status: {gt_status} | Pred Status: {pred_status}")
    print("\nGround Truth Steps:")
    for s in gt_steps:
        print(f"  [{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
    print("\nPredicted Steps:")
    for s in pred_steps:
        print(f"  [{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
