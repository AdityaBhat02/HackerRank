import csv
import json
import os
import glob
import sqlite3
import re
import sys
from typing import Dict, List, Set, Optional, Any, Tuple

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from request_classifier import RequestClassifier
from image_knowledge import IMAGE_EVIDENCE_DATA
import pdfplumber

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
classifier = RequestClassifier()
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

print("Loading and parsing all evidence...")

# We will index evidence records and user resource links
# Let's see what each sample case needs
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"Loaded {len(samples)} sample cases.")
