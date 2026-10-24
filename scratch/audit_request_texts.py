import csv, sys, os, collections
sys.path.insert(0, os.path.abspath('code'))
from request_classifier import RequestClassifier

clf = RequestClassifier()
rows = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
gt = {r['case_id']: r['deletion_status'] for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print("== SAMPLE NOT_APPLICABLE texts ==")
for s in samples:
    if gt[s['case_id']] == 'NOT_APPLICABLE':
        print(s['case_id'], '|', s['request_text'])
print("sample NA count:", sum(1 for v in gt.values() if v == 'NOT_APPLICABLE'))

texts = collections.Counter(r['request_text'] for r in rows)
print("\n== unique production texts:", len(texts), "rows:", len(rows))
out = open('scratch/request_text_audit.txt', 'w', encoding='utf-8')
for t, n in texts.most_common():
    flag = 'DEL' if clf.is_deletion_request(t) else 'NA '
    out.write(f"{flag} x{n} | {t}\n")
out.close()
print("NA predicted rows:", sum(n for t, n in texts.items() if not clf.is_deletion_request(t)))
print("reported_status counts:", collections.Counter(r['reported_status'] for r in rows))
