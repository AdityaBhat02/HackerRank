import csv

reqs = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
gt = {r['case_id']: r['deletion_status'] for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for r in reqs:
    cid = r['case_id']
    print(f"{cid} | GT: {gt.get(cid, 'UNKNOWN')} | {r['request_text']}")
