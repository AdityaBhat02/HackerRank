import sys, os, csv, json

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')
sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Test on complete cases
for cid in ['case_01', 'case_02', 'case_03', 'case_04', 'case_21', 'case_25', 'case_26', 'case_27', 'case_28', 'case_31']:
    req = next(r for r in sample_reqs if r['case_id'] == cid)
    gt_steps = json.loads(ground_truth[cid]['steps_json'])
    print(f"\n=== {cid} ===")
    print("GT:  ", [f"{s['resource_id']}({s['evidence_id']})" for s in gt_steps])
