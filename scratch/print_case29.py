import csv
import json

for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')):
    if r['case_id'] in ['case_29', 'case_26', 'case_18']:
        print(f"\n=== {r['case_id']} ===")
        for s in json.loads(r['steps_json']):
            print(f"[{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
