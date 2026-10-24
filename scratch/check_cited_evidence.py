import csv
import json
import os
import sys

outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# For every cited evidence_id in sample_output, check which file it points to
cited_cases = {}
for cid, out in outputs.items():
    steps = json.loads(out['steps_json'])
    for st in steps:
        eid = st.get('evidence_id')
        if eid:
            cited_cases.setdefault(eid, []).append((cid, st['resource_id'], st['phase'], st['operation']))

for eid, occurrences in sorted(cited_cases.items()):
    m = manifest.get(eid, {})
    print(f"\n{eid} ({m.get('captured_at')}) -> {m.get('file_path')}")
    print(f"  Total occurrences: {len(occurrences)}")
    sample_occ = occurrences[:4]
    for c in sample_occ:
        print(f"    Case {c[0]}: res={c[1]}, phase={c[2]}, op={c[3]}")
