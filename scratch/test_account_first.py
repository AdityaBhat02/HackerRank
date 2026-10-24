import sys, os, csv, json

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')
sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Test if analytics_901 is in evidence_records
e901 = [e for e in engine.evidence_records if e['resource_id'] == 'analytics_901']
print("analytics_901 in evidence_records:", e901)
