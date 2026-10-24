import sys
import os
import csv

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')

req = next(r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')) if r['case_id'] == 'case_29')
st, steps = engine.audit_case(req)

print(f"case_29 steps count: {len(steps)}")
for s in steps:
    print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']}")
