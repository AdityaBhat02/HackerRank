import csv
import json
import glob
import os
import sqlite3
import re
import sys

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver
from request_classifier import RequestClassifier
from activity_tracker import ActivityTracker
from evidence_parser import EvidenceParser
from image_knowledge import IMAGE_EVIDENCE_DATA

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
classifier = RequestClassifier()
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# Build global user resources map
user_resources = {} # uid -> dict of res_id -> {system_id, resource_id, metadata}

def add_user_res(uid, sys_id, res_id, meta=None):
    if not uid or not res_id:
        return
    user_resources.setdefault(uid, {})[res_id] = {
        'system_id': sys_id,
        'resource_id': res_id,
        'metadata': meta or {}
    }

# Map from system_activity.csv
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
for a in activities:
    res = a['resource_id']
    details = a['details']
    m_uid = re.search(r'user_\d+', details)
    if m_uid:
        uid = m_uid.group(0)
        target_sys = a['target_system']
        add_user_res(uid, target_sys, res)

# Map from snapshot bundles
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
    except: pass

# Map from service resource exports
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
    except: pass

# Map from handover text files
for p in glob.glob('dataset/evidence/records/*.txt'):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('-'): continue
                parts = [x.strip() for x in line.lstrip('-').split('|')]
                if len(parts) >= 6:
                    sys_id = parts[1]
                    res_id = parts[2]
                    ident = parts[5]
                    if ident.startswith('user_'):
                        add_user_res(ident, sys_id, res_id)
                    elif '@' in ident:
                        u = resolver.resolve_user_by_email(ident)
                        if u: add_user_res(u.user_id, sys_id, res_id)
    except: pass

# Map from SQL replicas
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
                    if uid: add_user_res(uid, origin_sys, res_id, rj)
                except: pass
        conn.close()
    except: pass

# Map from images
for eid, idata in IMAGE_EVIDENCE_DATA.items():
    sys_id = idata.get('system_id', '')
    for r in idata.get('records', []):
        uid = r.get('user_id')
        res_id = r.get('resource_id')
        if uid and res_id:
            add_user_res(uid, r.get('system_id', sys_id), res_id, r)

print(f"Total mapped users: {len(user_resources)}")

# Test on 32 samples
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

exact = 0
for s in samples:
    cid = s['case_id']
    gt = outputs[cid]
    gt_steps = json.loads(gt['steps_json'])
    gt_res = set(st['resource_id'] for st in gt_steps)

    email = s['email']
    user = resolver.resolve_user_by_email(email)
    uid = user.user_id if user else "UNKNOWN"

    pred_res = set(user_resources.get(uid, {}).keys())
    # Also find account from activity
    rep_at = s['reported_at']
    for a in activities:
        if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service':
            if abs((len(a['event_time']) - len(rep_at))) < 20 and a['event_time'][:13] == rep_at[:13]:
                pred_res.add(a['resource_id'])

    diff = gt_res - pred_res
    if diff:
        print(f"[{cid}] User: {uid} Missing resources: {diff}")
    else:
        exact += 1

print(f"Resource recall: {exact}/{len(samples)} ({exact/len(samples)*100:.1f}%)")
