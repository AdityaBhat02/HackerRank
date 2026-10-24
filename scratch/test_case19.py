import sys
import os
import csv
import json

sys.path.insert(0, os.path.abspath('code'))
from evidence_parser import EvidenceParser
from identity import IdentityResolver

ep = EvidenceParser('dataset')
resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')

prof = resolver.resolve_user_by_email('e.varga90@yahoo.com')
print("Profile:", prof.user_id if prof else None, prof.all_emails if prof else None)

matching = [r for r in ep.records if r.email == 'e.varga90@yahoo.com' or (prof and r.user_id == prof.user_id)]
print(f"Total matching records in ep.records: {len(matching)}")
for r in matching:
    print(f"  file={r.file_id} sys={r.system_id} res={r.resource_id} state={r.state} pii={r.has_exposed_pii} cap={r.captured_at}")
