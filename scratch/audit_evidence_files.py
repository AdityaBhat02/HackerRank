import csv, os, sys
sys.path.insert(0, os.path.abspath('code'))
from decision_engine import DecisionEngine
from identity import IdentityResolver

manifest = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))
print(f"Total evidence files to check: {len(manifest)}")

errors = []
missing_files = []
file_types = {}

for row in manifest:
    fid = row['file_id']
    fpath = os.path.join('dataset', row['file_path'])
    ext = os.path.splitext(fpath)[1].lower()
    file_types[ext] = file_types.get(ext, 0) + 1
    
    if not os.path.exists(fpath):
        missing_files.append((fid, fpath))
        continue

print(f"File extensions distribution: {file_types}")
if missing_files:
    print(f"WARNING: {len(missing_files)} files missing: {missing_files}")
else:
    print("All 94 evidence files exist on disk.")

# Check identity resolver closure
resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
print(f"Resolved users: {len(resolver.profiles_by_user_id)}")
multi_hop = 0
for uid, prof in resolver.profiles_by_user_id.items():
    if len(prof.all_emails) > 1 or len(prof.all_phones) > 1:
        multi_hop += 1
print(f"Users with historical email/phone changes: {multi_hop}")

# Check engine initialization and parsing
try:
    engine = DecisionEngine('dataset')
    print(f"DecisionEngine initialized successfully.")
    print(f"Total parsed evidence records: {len(engine.evidence_records)}")
    print(f"Total catalog identity links: {len(engine.catalog_identity_map)}")
    print(f"Total mapped accounts: {len(engine.account_map)}")
    print(f"Total mapped audit records: {len(engine.audit_map)}")
except Exception as ex:
    print(f"ERROR during DecisionEngine initialization: {ex}")
