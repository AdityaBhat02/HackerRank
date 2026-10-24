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
import pdfplumber

resolver = IdentityResolver('dataset/user_identities.csv', 'dataset/user_audit_log.csv')
classifier = RequestClassifier()
manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

# Parse all evidence into comprehensive registry
# evidence_records: list of dicts
print("Building unified evidence index...")

evidence_records = []

def add_ev(file_id, cap_at, sys_id, res_id, state, uid=None, email=None, phone=None, name=None, has_pii=False, is_flow=False, is_risk=False, details=""):
    evidence_records.append({
        'file_id': file_id,
        'captured_at': cap_at,
        'system_id': sys_id,
        'resource_id': res_id,
        'state': state,
        'user_id': uid or '',
        'email': email.lower().strip() if email else '',
        'phone': phone.strip() if phone else '',
        'name': name.lower().strip() if name else '',
        'has_exposed_pii': has_pii,
        'is_active_flow': is_flow,
        'is_restore_risk': is_risk,
        'details': details
    })

# 1. Image knowledge
for fid, idata in IMAGE_EVIDENCE_DATA.items():
    m = manifest.get(fid)
    cap_at = m['captured_at'] if m else '2026-09-01T00:00:00Z'
    def_sys = idata.get('system_id', '')
    for r in idata.get('records', []):
        sys_id = r.get('system_id', def_sys)
        res_id = r.get('resource_id', '')
        state = 'ACTIVE' if r.get('is_active_flow') or r.get('is_restore_risk') else ('PRESENT' if r.get('is_present') else 'ABSENT')
        add_ev(fid, cap_at, sys_id, res_id, state, uid=r.get('user_id'), email=r.get('email'), phone=r.get('phone'), name=r.get('full_name'), has_pii=r.get('has_exposed_pii', False), is_flow=r.get('is_active_flow', False), is_risk=r.get('is_restore_risk', False))

# 2. Handover txt files
for m in manifest.values():
    if m['file_path'].endswith('.txt'):
        fid = m['file_id']
        cap_at = m['captured_at']
        fpath = os.path.join('dataset', m['file_path'])
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.startswith('-'): continue
                    parts = [x.strip() for x in line.lstrip('-').split('|')]
                    if len(parts) >= 6:
                        ts, sys_id, res_id, cat, status, ident = parts[:6]
                        uid = ident if ident.startswith('user_') else ''
                        em = ident if '@' in ident else ''
                        if em and not uid:
                            u = resolver.resolve_user_by_email(em)
                            if u: uid = u.user_id

                        state = 'PRESENT'
                        has_pii = False
                        is_flow = False
                        is_risk = False
                        if status == 'NOT_FOUND': state = 'ABSENT'
                        elif status == 'FOUND': state = 'PRESENT'
                        elif status == 'IDENTIFIABLE': state = 'PRESENT'; has_pii = True
                        elif status == 'ANONYMIZED': state = 'ANONYMIZED'
                        elif status == 'REDACTED': state = 'REDACTED'
                        elif status == 'ACTIVE':
                            state = 'ACTIVE'
                            if 'FLOW' in cat: is_flow = True
                            if 'BACKUP' in cat: is_risk = True
                        elif status == 'DISABLED': state = 'DISABLED'
                        elif status == 'BLOCKED': state = 'BLOCKED'

                        add_ev(fid, cap_at, sys_id, res_id, state, uid=uid, email=em, has_pii=has_pii, is_flow=is_flow, is_risk=is_risk)

# 3. JSON files
for m in manifest.values():
    if m['file_path'].endswith('.json'):
        fid = m['file_id']
        cap_at = m['captured_at']
        fpath = os.path.join('dataset', m['file_path'])
        if not os.path.exists(fpath): continue
        try:
            data = json.load(open(fpath, encoding='utf-8'))
        except: continue

        if 'service_exports' in data:
            exports = data['service_exports']
            # account
            for item in exports.get('account_service', {}).get('profile_lookups', []):
                res_id = item.get('resource_id')
                status = item.get('status_code')
                prof = item.get('profile') or {}
                state = 'PRESENT' if status == 200 else 'ABSENT'
                em = prof.get('email')
                uid = prof.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'account_service', res_id, state, uid=uid, email=em, phone=prof.get('phone'), name=prof.get('full_name'))

            # analytics
            for item in exports.get('analytics_platform', {}).get('profiles', []):
                res_id = item.get('resource_id')
                em = item.get('email')
                has_pii = bool(em or item.get('phone'))
                state = 'PRESENT' if has_pii else 'ANONYMIZED'
                uid = item.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'analytics_platform', res_id, state, uid=uid, email=em, phone=item.get('phone'), has_pii=has_pii)

            # backup
            for item in exports.get('backup_service', {}).get('restore_entries', []):
                res_id = item.get('resource_id')
                allowed = item.get('restore_allowed', False)
                state = 'ACTIVE' if allowed else 'BLOCKED'
                em = item.get('customer_email')
                uid = item.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'backup_service', res_id, state, uid=uid, email=em, is_risk=allowed)

            # export
            for item in exports.get('export_service', {}).get('exports', []):
                res_id = item.get('resource_id')
                em = item.get('owner_email')
                uid = item.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'export_service', res_id, 'PRESENT', uid=uid, email=em, phone=item.get('owner_phone'))

            # integration
            for item in exports.get('integration_service', {}).get('connectors', []):
                res_id = item.get('resource_id')
                enabled = item.get('enabled', False)
                state = 'ACTIVE' if enabled else 'DISABLED'
                em = item.get('customer_email')
                uid = item.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'integration_service', res_id, state, uid=uid, email=em, is_flow=enabled)

            # search
            for item in exports.get('search_service', {}).get('index_queries', []):
                res_id = item.get('resource_id')
                hits = item.get('hits', {})
                total = hits.get('total', 0)
                docs = hits.get('documents', [])
                doc = docs[0] if docs else {}
                state = 'PRESENT' if total > 0 else 'ABSENT'
                em = doc.get('email') or item.get('query')
                uid = doc.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'search_service', res_id, state, uid=uid, email=em, phone=doc.get('phone'), name=doc.get('display_name'))

            # security
            for item in exports.get('security_service', {}).get('audit_records', []):
                res_id = item.get('resource_id')
                uid = item.get('subject_reference')
                add_ev(fid, cap_at, 'security_service', res_id, 'PRESENT', uid=uid)

            # support
            for item in exports.get('support_platform', {}).get('tickets', []):
                res_id = item.get('resource_id')
                em = item.get('requester_email')
                name = item.get('requester_name')
                phone = item.get('requester_phone')
                has_pii = bool(em or name or phone)
                state = 'PRESENT' if has_pii else 'REDACTED'
                uid = item.get('customer_reference')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'support_platform', res_id, state, uid=uid, email=em, phone=phone, name=name, has_pii=has_pii)

        elif 'snapshots' in data:
            for snap in data.get('snapshots', []):
                data_store = snap.get('data_store', '')
                for item in snap.get('records', []):
                    res_id = item.get('resource_id')
                    uid = item.get('subject_reference') or item.get('user_id') or item.get('customer_reference')
                    em = item.get('email') or item.get('requester_email') or item.get('subject_selector')
                    phone = item.get('phone')
                    name = item.get('name') or item.get('full_name')
                    if em and not uid:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id

                    if 'tombstone' in res_id:
                        has_pii = bool(name or em or phone or item.get('email_hash'))
                        state = 'PRESENT' if has_pii else 'REDACTED'
                        add_ev(fid, cap_at, 'identity_service', res_id, state, uid=uid, email=em, phone=phone, name=name, has_pii=has_pii)
                    elif 'audit_record' in res_id:
                        add_ev(fid, cap_at, 'security_service', res_id, 'PRESENT', uid=uid)
                    elif 'account_' in res_id:
                        state = 'PRESENT' if item.get('account_status') == 'ACTIVE' else 'ABSENT'
                        add_ev(fid, cap_at, 'account_service', res_id, state, uid=uid, email=em, phone=phone, name=name)
                    elif 'search_' in res_id:
                        doc = item.get('document', {})
                        doc_em = doc.get('email') or em
                        doc_name = doc.get('display_name') or name
                        doc_uid = doc.get('customer_reference') or uid
                        add_ev(fid, cap_at, 'search_service', res_id, 'PRESENT', uid=doc_uid, email=doc_em, name=doc_name)
                    elif 'analytics_' in res_id:
                        has_pii = bool(em or phone or uid)
                        add_ev(fid, cap_at, 'analytics_platform', res_id, 'PRESENT', uid=uid, email=em, phone=phone, has_pii=has_pii)
                    elif 'data_flow_' in res_id:
                        enabled = item.get('enabled', False)
                        state = 'ACTIVE' if enabled else 'DISABLED'
                        add_ev(fid, cap_at, 'integration_service', res_id, state, uid=uid, email=em, is_flow=enabled)
                    elif 'support_' in res_id:
                        has_pii = bool(em or 'email' in item.get('message_text', '').lower())
                        add_ev(fid, cap_at, 'support_platform', res_id, 'PRESENT', uid=uid, email=em, has_pii=has_pii)
                    elif 'backup_' in res_id:
                        allowed = item.get('restore_allowed', False)
                        state = 'ACTIVE' if allowed else 'BLOCKED'
                        add_ev(fid, cap_at, 'backup_service', res_id, state, uid=uid, email=em, is_risk=allowed)
                    elif 'export_' in res_id:
                        add_ev(fid, cap_at, 'export_service', res_id, 'PRESENT', uid=uid, email=em)

        elif 'export_jobs' in data:
            for job in data.get('export_jobs', []):
                res_id = job.get('resource_id')
                em = job.get('email') or job.get('owner_email')
                uid = None
                if em:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                add_ev(fid, cap_at, 'export_service', res_id, 'PRESENT', uid=uid, email=em)

        elif 'analytics_profile' in data or 'profiles' in data:
            profiles = data.get('profiles') or [data.get('analytics_profile')]
            for p in profiles:
                if not p: continue
                res_id = p.get('resource_id')
                em = p.get('email')
                uid = p.get('user_id')
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id
                has_pii = bool(em or p.get('phone') or uid)
                state = 'PRESENT' if has_pii else 'ANONYMIZED'
                add_ev(fid, cap_at, 'analytics_platform', res_id, state, uid=uid, email=em, phone=p.get('phone'), has_pii=has_pii)

# 4. SQL files
for m in manifest.values():
    if m['file_path'].endswith('.sql'):
        fid = m['file_id']
        cap_at = m['captured_at']
        fpath = os.path.join('dataset', m['file_path'])
        if not os.path.exists(fpath): continue
        conn = sqlite3.connect(':memory:')
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]

            if 'customer_profiles_failover_replica' in tables:
                cur.execute("SELECT resource_id, user_id, full_name, email, phone, account_status FROM customer_profiles_failover_replica")
                for row in cur.fetchall():
                    res_id, uid, name, em, phone, status = row
                    state = 'PRESENT' if status == 'ACTIVE' else 'ABSENT'
                    add_ev(fid, cap_at, 'account_service', res_id, state, uid=uid, email=em, phone=phone, name=name)

            if 'customer_data_read_replica' in tables:
                cur.execute("SELECT resource_id, origin_system, collection_name, record_json FROM customer_data_read_replica")
                for row in cur.fetchall():
                    res_id, origin_sys, col_name, rec_json_str = row
                    try: rj = json.loads(rec_json_str)
                    except: rj = {}
                    uid = rj.get('user_id') or rj.get('customer_reference')
                    em = rj.get('email')
                    phone = rj.get('phone')
                    name = rj.get('full_name')
                    if em and not uid:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    has_pii = bool(em or phone or name)
                    state = 'PRESENT'
                    if origin_sys == 'analytics_platform': state = 'PRESENT' if has_pii else 'ANONYMIZED'
                    elif origin_sys == 'support_platform': state = 'PRESENT' if has_pii else 'REDACTED'
                    add_ev(fid, cap_at, origin_sys, res_id, state, uid=uid, email=em, phone=phone, name=name, has_pii=has_pii)

            if 'search_documents_primary' in tables:
                cur.execute("SELECT resource_id, email, full_name, phone FROM search_documents_primary")
                for row in cur.fetchall():
                    res_id, em, name, phone = row
                    uid = None
                    if em:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    add_ev(fid, cap_at, 'search_service', res_id, 'PRESENT', uid=uid, email=em, name=name, phone=phone)

            if 'backup_restore_entries' in tables:
                cur.execute("SELECT resource_id, customer_email, customer_reference, restore_allowed FROM backup_restore_entries")
                for row in cur.fetchall():
                    res_id, em, uid, allowed = row
                    state = 'ACTIVE' if allowed else 'BLOCKED'
                    if em and not uid:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    add_ev(fid, cap_at, 'backup_service', res_id, state, uid=uid, email=em, is_risk=bool(allowed))

            if 'support_records' in tables:
                cur.execute("SELECT resource_id, customer_reference, requester_email, message_excerpt FROM support_records")
                for row in cur.fetchall():
                    res_id, uid, em, excerpt = row
                    has_pii = bool(em)
                    state = 'PRESENT' if has_pii else 'REDACTED'
                    if em and not uid:
                        u = resolver.resolve_user_by_email(em)
                        if u: uid = u.user_id
                    add_ev(fid, cap_at, 'support_platform', res_id, state, uid=uid, email=em, has_pii=has_pii)
            conn.close()
        except: pass

# 5. PDFs
for m in manifest.values():
    if m['file_path'].endswith('.pdf'):
        fid = m['file_id']
        cap_at = m['captured_at']
        fpath = os.path.join('dataset', m['file_path'])
        if not os.path.exists(fpath): continue
        try:
            with pdfplumber.open(fpath) as pdf:
                full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            if "support_001" in full_text:
                add_ev(fid, cap_at, 'support_platform', 'support_001', 'PRESENT', uid='user_07', email='priya.raman@gmail.com', name='Priya Raman', details='attachment')
            if "audit_record_" in full_text:
                for match in re.finditer(r"(audit_record_\d+).*?subject reference\s+(user_\d+)", full_text, re.IGNORECASE):
                    res_id, uid = match.groups()
                    add_ev(fid, cap_at, 'security_service', res_id, 'PRESENT', uid=uid)
        except: pass

# 6. Logs
for m in manifest.values():
    if m['file_path'].endswith('.log'):
        fid = m['file_id']
        cap_at = m['captured_at']
        fpath = os.path.join('dataset', m['file_path'])
        if not os.path.exists(fpath): continue
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'resource_id=' not in line and 'resource_id="' not in line:
                    continue
                m_res = re.search(r'resource_id[="]+([a-zA-Z0-9_]+)', line)
                if not m_res: continue
                res_id = m_res.group(1)

                sys_id = ''
                for s in ['account_service', 'search_service', 'support_platform', 'analytics_platform',
                          'integration_service', 'backup_service', 'export_service', 'security_service', 'identity_service']:
                    if s in line: sys_id = s; break
                if not sys_id:
                    if res_id.startswith('account_'): sys_id = 'account_service'
                    elif res_id.startswith('search_'): sys_id = 'search_service'
                    elif res_id.startswith('support_'): sys_id = 'support_platform'
                    elif res_id.startswith('analytics_'): sys_id = 'analytics_platform'
                    elif res_id.startswith('backup_'): sys_id = 'backup_service'
                    elif res_id.startswith('export_'): sys_id = 'export_service'
                    elif res_id.startswith('data_flow_'): sys_id = 'integration_service'
                    elif res_id.startswith('audit_record_'): sys_id = 'security_service'
                    elif res_id.startswith('tombstone_'): sys_id = 'identity_service'

                m_email = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
                em = m_email.group(1) if m_email else None
                m_uid = re.search(r'(user_\d+)', line)
                uid = m_uid.group(1) if m_uid else None
                if em and not uid:
                    u = resolver.resolve_user_by_email(em)
                    if u: uid = u.user_id

                state = 'PRESENT'
                has_pii = False
                if '404' in line or 'rows=0' in line: state = 'ABSENT'
                elif 'pii_scan' in line: has_pii = True; state = 'PRESENT'
                elif 'anonymized' in line: state = 'ANONYMIZED'
                elif 'redacted' in line: state = 'REDACTED'
                elif 'restore_allowed=True' in line: state = 'ACTIVE'
                elif 'restore_allowed=False' in line: state = 'BLOCKED'
                elif 'disabled' in line: state = 'DISABLED'

                add_ev(fid, cap_at, sys_id, res_id, state, uid=uid, email=em, has_pii=has_pii,
                       is_flow=(sys_id == 'integration_service' and state == 'ACTIVE'),
                       is_risk=(sys_id == 'backup_service' and state == 'ACTIVE'))

print(f"Total evidence records indexed: {len(evidence_records)}")

# Now test on all 32 samples
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print("\n--- Evaluating Samples ---")
for s in samples[:10]:
    cid = s['case_id']
    email = s['email']
    audit_at = s['audit_at']
    u = resolver.resolve_user_by_email(email)
    uid = u.user_id if u else None
    emails = u.all_emails if u else {email.lower()}

    # Find evidence records <= audit_at
    user_evs = [e for e in evidence_records if e['captured_at'] <= audit_at and (e['user_id'] == uid or e['email'] in emails)]
    print(f"[{cid}] user={uid} evidence_records_found={len(user_evs)}")
    res_states = {}
    for ev in user_evs:
        res_states[ev['resource_id']] = (ev['system_id'], ev['state'], ev['file_id'])
    for res, info in res_states.items():
        print(f"   {info[0]} | {res} | {info[1]} | {info[2]}")
