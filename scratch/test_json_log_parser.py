import glob
import json
import re

trace_map = {} # (log_file, trace_id) -> dict of accumulated keys

for p in glob.glob('dataset/evidence/logs/*.log'):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Check if line contains JSON
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
                        entry[k] = v

print(f"Total traces parsed: {len(trace_map)}")

# Count how many audit_records are linked to user_id
audit_links = {}
for (p, tr_id), data in trace_map.items():
    res = data.get('resource_id')
    uid = data.get('subject_ref') or data.get('subject_reference') or data.get('correlation_key') or data.get('customer_reference')
    if not uid:
        key = data.get('lookup_key') or data.get('match_key')
        if key and key.startswith('user_'): uid = key
    if res and res.startswith('audit_record_') and uid:
        audit_links[uid] = res

print(f"Audit records linked via log traces: {len(audit_links)}")
print("Sample audit links:", list(audit_links.items())[:10])
