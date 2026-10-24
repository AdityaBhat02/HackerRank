import csv
import json
import sys
import os

sys.path.insert(0, os.path.abspath('code'))
from identity import IdentityResolver

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')

# Load all evidence records into memory
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# Pre-parse all evidence with our updated logic
all_records = []

# 1. JSON
for fid, m in manifest.items():
    if m['file_path'].endswith('.json'):
        fpath = os.path.join('dataset', m['file_path'])
        cap_at = m['captured_at']
        try:
            data = json.load(open(fpath, encoding='utf-8'))
        except: continue
        
        # snapshots
        for snap in data.get('snapshots', []):
            for rec in snap.get('records', []):
                res_id = rec.get('resource_id')
                uid = rec.get('subject_reference') or rec.get('user_id') or rec.get('customer_reference')
                em = rec.get('email') or rec.get('requester_email')
                ehash = rec.get('email_hash')
                st = rec.get('account_status')
                state = 'PRESENT'
                has_pii = False
                is_flow = False
                is_risk = False
                sys_id = ''
                if 'tombstone' in res_id:
                    sys_id = 'identity_service'
                    has_pii = bool(rec.get('name') or em or rec.get('phone') or ehash)
                    state = 'PRESENT' if has_pii else 'REDACTED'
                elif 'audit_record' in res_id:
                    sys_id = 'security_service'
                    state = 'PRESENT'
                elif 'account_' in res_id:
                    sys_id = 'account_service'
                    state = 'PRESENT' if st == 'ACTIVE' else 'ABSENT'
                elif 'search_' in res_id:
                    sys_id = 'search_service'
                    state = 'PRESENT'
                elif 'analytics_' in res_id:
                    sys_id = 'analytics_platform'
                    has_pii = bool(em or rec.get('phone') or uid)
                    state = 'PRESENT' if has_pii else 'ANONYMIZED'
                elif 'data_flow_' in res_id:
                    sys_id = 'integration_service'
                    state = 'ACTIVE' if rec.get('enabled') else 'DISABLED'
                    is_flow = bool(rec.get('enabled'))
                elif 'backup_' in res_id:
                    sys_id = 'backup_service'
                    state = 'ACTIVE' if rec.get('restore_allowed') else 'BLOCKED'
                    is_risk = bool(rec.get('restore_allowed'))
                elif 'support_' in res_id:
                    sys_id = 'support_platform'
                    has_pii = bool(em)
                    state = 'PRESENT' if has_pii else 'REDACTED'
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': sys_id, 'resource_id': res_id,
                    'state': state, 'user_id': uid, 'email': em, 'hash': ehash, 'has_pii': has_pii,
                    'is_flow': is_flow, 'is_risk': is_risk
                })
                
        # service_exports
        if 'service_exports' in data:
            exp = data['service_exports']
            for item in exp.get('account_service', {}).get('profile_lookups', []):
                res_id = item.get('resource_id')
                prof = item.get('profile') or {}
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'account_service', 'resource_id': res_id,
                    'state': 'PRESENT' if item.get('status_code') == 200 else 'ABSENT',
                    'user_id': prof.get('customer_reference'), 'email': prof.get('email'), 'hash': prof.get('email_hash')
                })
            for item in exp.get('analytics_platform', {}).get('profiles', []):
                res_id = item.get('resource_id')
                has_pii = bool(item.get('email') or item.get('phone'))
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'analytics_platform', 'resource_id': res_id,
                    'state': 'PRESENT' if has_pii else 'ANONYMIZED',
                    'user_id': item.get('customer_reference'), 'email': item.get('email'), 'hash': item.get('email_hash'),
                    'has_pii': has_pii
                })
            for item in exp.get('backup_service', {}).get('restore_entries', []):
                res_id = item.get('resource_id')
                allowed = item.get('restore_allowed', False)
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'backup_service', 'resource_id': res_id,
                    'state': 'ACTIVE' if allowed else 'BLOCKED',
                    'user_id': item.get('customer_reference'), 'email': item.get('customer_email'),
                    'is_risk': allowed
                })
            for item in exp.get('integration_service', {}).get('connectors', []):
                res_id = item.get('resource_id')
                en = item.get('enabled', False)
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'integration_service', 'resource_id': res_id,
                    'state': 'ACTIVE' if en else 'DISABLED',
                    'user_id': item.get('customer_reference'), 'email': item.get('customer_email'),
                    'is_flow': en
                })
            for item in exp.get('search_service', {}).get('index_queries', []):
                res_id = item.get('resource_id')
                hits = item.get('hits', {})
                doc = (hits.get('documents') or [{}])[0]
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'search_service', 'resource_id': res_id,
                    'state': 'PRESENT' if hits.get('total', 0) > 0 else 'ABSENT',
                    'user_id': doc.get('customer_reference'), 'email': doc.get('email') or item.get('query')
                })
            for item in exp.get('security_service', {}).get('audit_records', []):
                res_id = item.get('resource_id')
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'security_service', 'resource_id': res_id,
                    'state': 'PRESENT', 'user_id': item.get('subject_reference')
                })
            for item in exp.get('support_platform', {}).get('tickets', []):
                res_id = item.get('resource_id')
                has_pii = bool(item.get('requester_email') or item.get('requester_name') or item.get('requester_phone'))
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'support_platform', 'resource_id': res_id,
                    'state': 'PRESENT' if has_pii else 'REDACTED',
                    'user_id': item.get('customer_reference'), 'email': item.get('requester_email'),
                    'has_pii': has_pii
                })
                
        # customer_export_jobs
        if data.get('collection') == 'customer_export_jobs' or 'export_jobs' in data:
            records = data.get('export_jobs') or data.get('records', [])
            for it in records:
                all_records.append({
                    'file_id': fid, 'captured_at': cap_at, 'system_id': 'export_service', 'resource_id': it.get('resource_id'),
                    'state': 'PRESENT' if it.get('download_available', True) else 'ABSENT',
                    'email': it.get('owner_email')
                })

print(f"Total parsed records: {len(all_records)}")
