import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

del_accs = [a for a in activities if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service']

for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_acc = [st['resource_id'] for st in gt_steps if st['system_id'] == 'account_service']
    gt_acc = gt_acc[0] if gt_acc else None

    # Check how gt_acc appears in del_accs
    matched_acts = [a for a in del_accs if a['resource_id'] == gt_acc]
    act_time = matched_acts[0]['event_time'] if matched_acts else "NO_ACT"
    act_res = matched_acts[0]['reported_result'] if matched_acts else ""

    print(f"[{cid}] GT={gt_acc:12} | req={s['requested_at']} | rep={s['reported_at']} | act_time={act_time} | res={act_res}")
