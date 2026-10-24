import csv
import json

samples = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for cid, out in sorted(outputs.items()):
    s = samples[cid]
    steps = json.loads(out['steps_json'])
    print(f"\n[{cid}] Status: {out['deletion_status']} | Rep: {s['reported_at']} | Audit: {s['audit_at']} | Email: {s['email']}")
    for st in steps:
        print(f"  {st['phase']:12} | {st['system_id']:20} | {st['resource_id']:18} | {st['operation']:25} | {st['state']:10} | evid={st.get('evidence_id')}")
