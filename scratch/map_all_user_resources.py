import csv
import json
import glob
import os
import sqlite3
import re
import sys

sys.path.insert(0, os.path.abspath('code'))
from image_knowledge import IMAGE_EVIDENCE_DATA

# Build comprehensive user resource registry
user_resources = {} # user_id -> dict of (system_id, resource_id) -> metadata

def add_user_res(uid, sys_id, res_id, meta=None):
    if not uid or not res_id:
        return
    user_resources.setdefault(uid, {})[res_id] = {
        'system_id': sys_id,
        'resource_id': res_id,
        'metadata': meta or {}
    }

# 1. Map from system_activity.csv
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
for a in activities:
    res = a['resource_id']
    details = a['details']
    m_uid = re.search(r'user_\d+', details)
    if m_uid:
        uid = m_uid.group(0)
        target_sys = a['target_system']
        add_user_res(uid, target_sys, res)

# 2. Map from customer_data_snapshot_bundle_*.json
for p in glob.glob('dataset/evidence/records/customer_data_snapshot_bundle_*.json'):
    try:
        data = json.load(open(p, encoding='utf-8'))
        for snap in data.get('snapshots', []):
            sys_id = snap.get('data_store', '')
            for r in snap.get('records', []):
                res_id = r.get('resource_id')
                uid = r.get('subject_reference') or r.get('user_id') or r.get('customer_reference')
                if uid and res_id:
                    add_user_res(uid, sys_id, res_id, r)
    except Exception as e:
        pass

# 3. Map from service_resource_export_*.json
for p in glob.glob('dataset/evidence/records/service_resource_export_*.json'):
    try:
        data = json.load(open(p, encoding='utf-8'))
        exports = data.get('service_exports', {})
        for sys_id, items in exports.items():
            if isinstance(items, dict):
                for sublist in items.values():
                    if isinstance(sublist, list):
                        for item in sublist:
                            res_id = item.get('resource_id')
                            uid = item.get('customer_reference') or item.get('subject_reference') or item.get('user_id')
                            if uid and res_id:
                                add_user_res(uid, sys_id, res_id, item)
    except Exception:
        pass

# 4. Map from SQL files
for p in glob.glob('dataset/evidence/databases/*.sql'):
    try:
        conn = sqlite3.connect(':memory:')
        with open(p, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        
        if 'customer_profiles_failover_replica' in tables:
            cur.execute("SELECT resource_id, user_id FROM customer_profiles_failover_replica")
            for res_id, uid in cur.fetchall():
                add_user_res(uid, 'account_service', res_id)
                
        if 'customer_data_read_replica' in tables:
            cur.execute("SELECT resource_id, origin_system, record_json FROM customer_data_read_replica")
            for res_id, origin_sys, rjson_str in cur.fetchall():
                try:
                    rj = json.loads(rjson_str)
                    uid = rj.get('user_id') or rj.get('customer_reference')
                    if uid:
                        add_user_res(uid, origin_sys, res_id, rj)
                except:
                    pass
        conn.close()
    except Exception:
        pass

# 5. Map from images
for eid, idata in IMAGE_EVIDENCE_DATA.items():
    sys_id = idata.get('system_id', '')
    for r in idata.get('records', []):
        uid = r.get('user_id')
        res_id = r.get('resource_id')
        if uid and res_id:
            add_user_res(uid, r.get('system_id', sys_id), res_id, r)

print(f"Users with mapped resources: {len(user_resources)}")
# Check sample cases
sample_outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
sample_reqs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

for cid, out in list(sample_outputs.items())[:10]:
    s = sample_reqs[cid]
    steps = json.loads(out['steps_json'])
    expected_resources = set(st['resource_id'] for st in steps)
    print(f"\n[{cid}] Expected resources: {expected_resources}")
    # find user
    # print what we mapped
