import csv, sys, os, json
sys.path.insert(0, os.path.abspath('code'))
from request_classifier import RequestClassifier
c = RequestClassifier()
rows = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
na = [r['case_id'] for r in rows if not c.is_deletion_request(r['request_text'])]
print("production NA:", len(na), na)
print("sample NA (expect 0):", [s['case_id'] for s in samples if not c.is_deletion_request(s['request_text'])])
custom = json.load(open('code/evaluation/custom_cases.json', encoding='utf-8'))
for cc in custom:
    got = c.is_deletion_request(cc['request_text'])
    print(cc['case_id'], cc['expected_status'], 'DEL' if got else 'NA')
# adversarial probes
probes = {
 "Please unsubscribe me from the newsletter.": False,
 "Delete my saved card please, keep everything else.": False,
 "Please delete my last order review.": False,
 "Can I pause my account for a month?": False,
 "Please delete my account and all my personal data.": True,
 "I want to exercise my right to erasure.": True,
 "Bitte löschen Sie mein Konto.": True,
 "Vorrei la cancellazione del mio account.": True,
 "退会したいです。": True,
}
for t, exp in probes.items():
    got = c.is_deletion_request(t)
    print('OK ' if got == exp else 'BAD', got, '|', t)
