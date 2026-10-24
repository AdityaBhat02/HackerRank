import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from image_knowledge import IMAGE_EVIDENCE_DATA

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
sample_requests = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
sample_outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

print(f"Loaded {len(sample_requests)} sample requests.")
