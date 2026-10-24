import csv
import json

sample_reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
ground_truth = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

manifest = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))

# Find all account_service evidence files sorted by captured_at
acc_evidence = []
for m in manifest:
    fp = m['file_path']
    if any(k in fp for k in ['customer_accounts', 'customer_profiles', 'service_resource_export', 'snapshot_bundle', 'resource_lookup_trace']):
        acc_evidence.append(m)

acc_evidence.sort(key=lambda x: x['captured_at'])

print(f"Account evidence files count: {len(acc_evidence)}")
for req in sample_reqs:
    cid = req['case_id']
    gt = ground_truth[cid]
    if gt['deletion_status'] == 'COMPLETE':
        gt_steps = json.loads(gt['steps_json'])
        exp_acc_ev = next((s['evidence_id'] for s in gt_steps if s['resource_id'].startswith('account_')), None)
        
        # Find latest account evidence <= audit_at
        audit_at = req['audit_at']
        cands = [m['file_id'] for m in acc_evidence if m['captured_at'] <= audit_at]
        latest_ev = cands[-1] if cands else ""
        print(f"{cid} | audit={audit_at} | exp={exp_acc_ev} | latest={latest_ev} | match={exp_acc_ev == latest_ev}")
