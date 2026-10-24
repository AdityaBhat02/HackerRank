import glob, json, sqlite3, re, pdfplumber, os, csv

audit_records_by_user = {}

# 1. JSON
for p in glob.glob('dataset/evidence/**/*.json', recursive=True):
    try:
        data = json.load(open(p, encoding='utf-8'))
        for item in data.get('service_exports', {}).get('security_service', {}).get('audit_records', []):
            uid = item.get('subject_reference')
            rid = item.get('resource_id')
            if uid and rid: audit_records_by_user[uid] = rid
        for snap in data.get('snapshots', []):
            for item in snap.get('records', []):
                rid = item.get('resource_id', '')
                if 'audit_record' in rid:
                    uid = item.get('subject_reference') or item.get('user_id')
                    if uid: audit_records_by_user[uid] = rid
    except: pass

# 2. SQL
for p in glob.glob('dataset/evidence/**/*.sql', recursive=True):
    try:
        conn = sqlite3.connect(':memory:')
        with open(p, 'r', encoding='utf-8') as f: conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for t in [r[0] for r in cur.fetchall()]:
            if 'security_audit_records' in t or 'audit' in t:
                cur.execute(f"SELECT resource_id, subject_reference FROM {t}")
                for rid, uid in cur.fetchall():
                    if uid and rid: audit_records_by_user[uid] = rid
        conn.close()
    except: pass

# 3. TXT
for p in glob.glob('dataset/evidence/**/*.txt', recursive=True):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                if 'audit_record_' in line:
                    parts = [x.strip() for x in line.lstrip('-').split('|')]
                    if len(parts) >= 6:
                        res = parts[2]
                        ident = parts[5]
                        if ident.startswith('user_'):
                            audit_records_by_user[ident] = res
    except: pass

# 4. PDF
for p in glob.glob('dataset/evidence/**/*.pdf', recursive=True):
    try:
        with pdfplumber.open(p) as pdf:
            txt = '\n'.join([page.extract_text() or '' for page in pdf.pages])
            for m in re.finditer(r'(audit_record_\d+).*?(user_\d+)', txt):
                audit_records_by_user[m.group(2)] = m.group(1)
    except: pass

# 5. LOGS (correlated traces)
trace_map = {}
for p in glob.glob('dataset/evidence/logs/*.log'):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if '{' in line and '}' in line:
                json_part = line[line.find('{'):line.rfind('}')+1]
                try:
                    obj = json.loads(json_part)
                    tr_id = obj.get('trace_id')
                    if tr_id:
                        entry = trace_map.setdefault((p, tr_id), {})
                        for k, v in obj.items():
                            if v: entry[k] = v
                except: pass
            else:
                m_tr = re.search(r'trace_id=([a-zA-Z0-9_-]+)', line)
                if m_tr:
                    tr_id = m_tr.group(1)
                    entry = trace_map.setdefault((p, tr_id), {})
                    for m_kv in re.finditer(r'([a-zA-Z0-9_]+)=([^\s]+)', line):
                        k, v = m_kv.groups()
                        entry[k] = v.strip('"\'')

for (p, tr_id), data in trace_map.items():
    res = data.get('resource_id')
    uid = data.get('subject_ref') or data.get('subject_reference') or data.get('correlation_key') or data.get('customer_reference')
    if not uid:
        key = data.get('lookup_key') or data.get('match_key')
        if key and key.startswith('user_'): uid = key
    if res and res.startswith('audit_record_') and uid:
        audit_records_by_user[uid] = res

print(f"Total unique users with audit records: {len(audit_records_by_user)}")

# Check against 24 sample cases
import sys
sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

cases_with_audit = [cid for cid, r in outputs.items() if 'audit_record' in r['steps_json']]
matched = 0
for cid in cases_with_audit:
    s = [x for x in samples if x['case_id'] == cid][0]
    u = resolver.resolve_user_by_email(s['email'])
    uid = u.user_id if u else "none"
    if uid in audit_records_by_user:
        matched += 1
    else:
        print(f"  Missing: {cid} | user={uid} | {s['email']}")

print(f"Sample audit records matched: {matched}/{len(cases_with_audit)} ({matched/len(cases_with_audit)*100:.1f}%)")
