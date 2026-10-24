import csv
import json
from datetime import datetime

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

for s in samples[:6]:
    cid = s['case_id']
    req_at = s['requested_at']
    rep_at = s['reported_at']
    out = outputs[cid]
    steps = json.loads(out['steps_json'])
    expected_resources = set(st['resource_id'] for st in steps)
    
    # Filter activities in window
    window_acts = [a for a in activities if a['event_time'] >= req_at and a['event_time'] <= rep_at + 'Z']
    matching_acts = [a for a in window_acts if a['resource_id'] in expected_resources]
    
    print(f"\n[{cid}] Expected resources: {expected_resources}")
    print(f"Matched activities in window ({len(matching_acts)}):")
    for a in matching_acts:
        print(f"  {a['event_time']} | {a['event_type']} | {a['source_system']} -> {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
