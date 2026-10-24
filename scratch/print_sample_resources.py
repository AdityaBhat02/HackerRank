import csv
import json
import re
import os

outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
samples = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

for cid, out in sorted(outputs.items()):
    s = samples[cid]
    steps = json.loads(out['steps_json'])
    acc = [st['resource_id'] for st in steps if st['system_id'] == 'account_service']
    other_res = [st['resource_id'] for st in steps if st['system_id'] != 'account_service']
    eids = list(set(st['evidence_id'] for st in steps if st.get('evidence_id')))
    print(f"[{cid}] acc={acc} | eids={eids} | other={other_res}")
