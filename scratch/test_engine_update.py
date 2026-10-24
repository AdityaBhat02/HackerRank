import sys
import os
import csv
import json

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

# Test current decision engine on case_08, 12, 19
engine = DecisionEngine('dataset')
sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

print("Testing case_08, 12, 19:")
for cid in ['case_08', 'case_12', 'case_19']:
    req = next(r for r in sample_reqs if r['case_id'] == cid)
    st, steps = engine.audit_case(req)
    print(cid, st, len(steps))
