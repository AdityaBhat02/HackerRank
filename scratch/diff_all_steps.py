import csv
import json
import sys
import os

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case':8} | {'Status':8} | {'SeqMatch':8} | {'GT Count':8} | {'Pred Count':10} | {'Mismatched Steps'}")
print("=" * 90)

exact_matches = 0
status_matches = 0

for req in sample_reqs:
    cid = req['case_id']
    gt = ground_truth[cid]
    gt_status = gt['deletion_status']
    gt_steps = json.loads(gt['steps_json'])
    
    pred_status, pred_steps = engine.audit_case(req)
    
    is_status_ok = (pred_status == gt_status)
    is_seq_ok = (is_status_ok and pred_steps == gt_steps)
    
    if is_status_ok: status_matches += 1
    if is_seq_ok: exact_matches += 1
    
    mismatches = []
    if not is_seq_ok:
        # Compare step by step
        for i in range(max(len(gt_steps), len(pred_steps))):
            g_step = gt_steps[i] if i < len(gt_steps) else None
            p_step = pred_steps[i] if i < len(pred_steps) else None
            if g_step != p_step:
                g_str = f"{g_step['phase']}:{g_step['system_id']}:{g_step['resource_id']}:{g_step['operation']}:{g_step['evidence_id']}" if g_step else "MISSING"
                p_str = f"{p_step['phase']}:{p_step['system_id']}:{p_step['resource_id']}:{p_step['operation']}:{p_step['evidence_id']}" if p_step else "EXTRA"
                mismatches.append(f"[{i+1}] GT({g_str}) != PRED({p_str})")
    
    mism_summary = " | ".join(mismatches[:3])
    if len(mismatches) > 3:
        mism_summary += f" (+{len(mismatches)-3} more)"
    print(f"{cid:8} | {str(is_status_ok):8} | {str(is_seq_ok):8} | {len(gt_steps):8} | {len(pred_steps):10} | {mism_summary}")

print(f"\nStatus Accuracy: {status_matches}/32 ({status_matches/32*100:.2f}%)")
print(f"Sequence Accuracy: {exact_matches}/32 ({exact_matches/32*100:.2f}%)")
