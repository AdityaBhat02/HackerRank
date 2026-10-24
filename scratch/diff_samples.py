import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for s in samples:
    cid = s['case_id']
    gt = ground_truth[cid]
    gt_status = gt['deletion_status']
    gt_steps = json.loads(gt['steps_json'])

    pred_status, pred_steps = engine.audit_case(s)

    if pred_status != gt_status or pred_steps != gt_steps:
        print(f"\n==================== [{cid}] ====================")
        print(f"Status: Pred={pred_status} | GT={gt_status}")
        print("--- PRED STEPS ---")
        for st in pred_steps:
            print(f"  {st['phase']} | {st['system_id']} | {st['resource_id']} | {st['operation']} | {st['state']} | evid={st.get('evidence_id')}")
        print("--- GT STEPS ---")
        for st in gt_steps:
            print(f"  {st['phase']} | {st['system_id']} | {st['resource_id']} | {st['operation']} | {st['state']} | evid={st.get('evidence_id')}")
