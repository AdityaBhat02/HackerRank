import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

print(f"Total samples: {len(samples)}")

for s in samples:
    cid = s['case_id']
    out = outputs[cid]
    steps = json.loads(out['steps_json'])
    # Find account_id in steps
    account_ids = [st['resource_id'] for st in steps if st['system_id'] == 'account_service']
    expected_account = account_ids[0] if account_ids else None
    
    # Check activities around reported_at (+- 10 minutes)
    reported_at = s['reported_at']
    matched_acts = []
    for a in activities:
        # Check event_time close to reported_at
        if a['event_time'][:16] == reported_at[:16] or (expected_account and a['resource_id'] == expected_account):
            matched_acts.append(a)
            
    print(f"[{cid}] Exp Account: {expected_account} | ReportedAt: {reported_at}")
    for a in matched_acts:
        print(f"   act_id={a['activity_id']} time={a['event_time']} type={a['event_type']} target={a['target_system']} res={a['resource_id']}")
