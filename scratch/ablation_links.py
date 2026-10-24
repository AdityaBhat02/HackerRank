"""Ablation: sample accuracy and production diff with vs without sample-derived link tables."""
import csv, json, sys, os, subprocess
mode = sys.argv[1] if len(sys.argv) > 1 else None
if mode is None:
    for m in ('1', '0'):
        env = dict(os.environ, GHOST_USE_SAMPLE_LINKS=m, PYTHONIOENCODING='utf-8')
        subprocess.run([sys.executable, __file__, m], env=env)
    a = {r['case_id']: r for r in csv.DictReader(open('scratch/ablation_1.csv', encoding='utf-8'))}
    b = {r['case_id']: r for r in csv.DictReader(open('scratch/ablation_0.csv', encoding='utf-8'))}
    sd = [c for c in a if a[c]['deletion_status'] != b[c]['deletion_status']]
    stp = [c for c in a if a[c]['steps_json'] != b[c]['steps_json']]
    print(f"\nPRODUCTION: status differs in {len(sd)} cases, steps differ in {len(stp)} cases")
    print("status diffs:", [(c, a[c]['deletion_status'], b[c]['deletion_status']) for c in sd][:20])
    sys.exit()

sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine
e = DecisionEngine('dataset')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
gt = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
st = sq = 0
for s in samples:
    ps, steps = e.audit_case(s)
    st += ps == gt[s['case_id']]['deletion_status']
    sq += ps == gt[s['case_id']]['deletion_status'] and steps == json.loads(gt[s['case_id']]['steps_json'])
print(f"[links={mode}] sample status {st}/32  sequence {sq}/32")
rows = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
with open(f'scratch/ablation_{mode}.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(['case_id', 'deletion_status', 'steps_json'])
    for r in rows:
        ps, steps = e.audit_case(r)
        w.writerow([r['case_id'], ps, json.dumps(steps, separators=(',', ':'))])
