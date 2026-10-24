import csv
import json

acts = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for cid in ['case_28', 'case_29', 'case_30', 'case_31', 'case_32']:
    s = samples[cid]
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)
    req_at = s['requested_at']
    rep_at = s['reported_at']

    print(f"\n================ [{cid}] ==================")
    print(f"req: {req_at} | rep: {rep_at} | {s['email']}")
    print(f"GT resources: {sorted(list(gt_res))}")

    # Find all deletion_worker activities around reported_at
    worker_acts = [a for a in acts if a['source_system'] == 'deletion_worker' and req_at <= a['event_time'] <= rep_at + 'Z']
    print(f"Deletion worker activities in window ({len(worker_acts)}):")
    for a in worker_acts:
        is_gt = "*** GT ***" if a['resource_id'] in gt_res else ""
        print(f"  {a['event_time']} | {a['target_system']:20} | {a['resource_id']:20} | {a['reported_result']} {is_gt}")
