import csv
import json

sample_outputs = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))

print(f"Total sample outputs: {len(sample_outputs)}")

complete_cases = [r for r in sample_outputs if r['deletion_status'] == 'COMPLETE']
incomplete_cases = [r for r in sample_outputs if r['deletion_status'] == 'INCOMPLETE']
not_app_cases = [r for r in sample_outputs if r['deletion_status'] == 'NOT_APPLICABLE']

print(f"COMPLETE: {len(complete_cases)}, INCOMPLETE: {len(incomplete_cases)}, NOT_APPLICABLE: {len(not_app_cases)}")

print("\n=== COMPLETE CASES PATTERN ===")
for r in complete_cases[:5]:
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    print(f"\n{cid}: ({len(steps)} steps)")
    for s in steps:
        print(f"  [{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")

print("\n=== INCOMPLETE CASES PATTERN ===")
for r in incomplete_cases[:5]:
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    print(f"\n{cid}: ({len(steps)} steps)")
    for s in steps:
        print(f"  [{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
