import csv, re, collections, sys, os
sys.path.insert(0, os.path.abspath('code'))
from request_classifier import RequestClassifier
clf = RequestClassifier()
rows = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
sent = collections.Counter()
for r in rows:
    for s in re.split(r'(?<=[.!?。])\s*', r['request_text'].strip()):
        if s.strip(): sent[s.strip()] += 1
print("unique sentences:", len(sent))
for s, n in sent.most_common():
    print(f"x{n:3d} | {s}")
print("\n== FULL TEXT OF NA-PREDICTED ROWS ==")
for r in rows:
    if not clf.is_deletion_request(r['request_text']):
        print(r['case_id'], r['reported_status'], '|', r['request_text'])
print("\n== NON-ASCII TEXTS ==")
for r in rows:
    if any(ord(c) > 127 for c in r['request_text']):
        print(r['case_id'], '|', r['request_text'][:200])
