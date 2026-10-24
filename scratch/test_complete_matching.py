import csv
import json
import glob
import os
import sqlite3
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from request_classifier import RequestClassifier
from image_knowledge import IMAGE_EVIDENCE_DATA

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
classifier = RequestClassifier()
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Parse all evidence into structured records
print("Parsing all evidence files...")

# Let's inspect how close we get to 32/32 sample GT
