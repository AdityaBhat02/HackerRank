"""Strict output.csv contract validator + baseline verification coverage audit."""
import csv, json, sys, collections
PHASE = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
OPS = {"FINDING": ["REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"],
       "REMEDIATION": ["DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"],
       "VERIFICATION": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED",
                        "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"]}
STATE = {"REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT", "REPORT_ACTIVE_DATA_FLOW": "ACTIVE",
         "REPORT_RESTORE_RISK": "ACTIVE", "DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED",
         "DELETE_RECORD": "ABSENT", "REDACT_RECORD": "REDACTED", "ANONYMIZE_RECORD": "ANONYMIZED",
         "VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT", "VERIFY_RECORD_REDACTED": "REDACTED",
         "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED"}
REM_TO_VER = {"DISABLE_DATA_FLOW": "VERIFY_DATA_FLOW_DISABLED", "BLOCK_RESTORE": "VERIFY_RESTORE_BLOCKED",
              "DELETE_RECORD": "VERIFY_RECORD_ABSENT", "REDACT_RECORD": "VERIFY_RECORD_REDACTED",
              "ANONYMIZE_RECORD": "VERIFY_RECORD_ANONYMIZED"}
path = sys.argv[1] if len(sys.argv) > 1 else 'output.csv'
lines = open(path, encoding='utf-8').read().splitlines()
rows = list(csv.DictReader(open(path, encoding='utf-8')))
req = [r['case_id'] for r in csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8'))]
errs = []
if len(rows) != 518: errs.append(f"row count {len(rows)}")
if [r['case_id'] for r in rows] != req: errs.append("case_id order differs from deletion_requests.csv")
if list(rows[0].keys()) != ['case_id', 'deletion_status', 'steps_json']: errs.append("bad header")
dist = collections.Counter(); ver_cov = collections.Counter(); low_ver = []
for r in rows:
    cid, st = r['case_id'], r['deletion_status']; dist[st] += 1
    try: steps = json.loads(r['steps_json'])
    except Exception as ex: errs.append(f"{cid} bad json {ex}"); continue
    if st == 'NOT_APPLICABLE':
        if steps != []: errs.append(f"{cid} NA with steps")
        continue
    if not steps: errs.append(f"{cid} {st} with no steps")
    keys = [(s['phase'], s['operation'], s['system_id'], s['resource_id']) for s in steps]
    if len(keys) != len(set(keys)): errs.append(f"{cid} duplicate step tuples")
    if [s['step_no'] for s in steps] != list(range(1, len(steps) + 1)): errs.append(f"{cid} step_no not 1..N")
    sk = [(PHASE[s['phase']], OPS[s['phase']].index(s['operation']), s['system_id'], s['resource_id']) for s in steps]
    if sk != sorted(sk): errs.append(f"{cid} not canonically sorted")
    for s in steps:
        if s['operation'] not in OPS[s['phase']]: errs.append(f"{cid} op/phase mismatch {s}")
        if STATE[s['operation']] != s['state']: errs.append(f"{cid} op/state mismatch {s['operation']} {s['state']}")
    if st == 'COMPLETE':
        if any(s['phase'] != 'VERIFICATION' for s in steps): errs.append(f"{cid} COMPLETE with non-verification")
        if any(not s['evidence_id'] for s in steps): errs.append(f"{cid} COMPLETE missing evidence_id")
    if st == 'INCOMPLETE':
        f = [s for s in steps if s['phase'] == 'FINDING']
        if not f: errs.append(f"{cid} INCOMPLETE without FINDING")
        if any(not s['evidence_id'] for s in f): errs.append(f"{cid} FINDING missing evidence_id")
        if any(s['evidence_id'] for s in steps if s['phase'] != 'FINDING'): errs.append(f"{cid} INCOMPLETE rem/ver with evidence_id")
        vers = {(s['operation'], s['resource_id']) for s in steps if s['phase'] == 'VERIFICATION'}
        for s in steps:
            if s['phase'] == 'REMEDIATION' and (REM_TO_VER[s['operation']], s['resource_id']) not in vers:
                errs.append(f"{cid} remediation {s['operation']} {s['resource_id']} has no matching verification")
    systems = {s['system_id'] for s in steps if s['phase'] == 'VERIFICATION'}
    for sysname in ('account_service', 'identity_service', 'security_service'):
        if sysname in systems: ver_cov[sysname] += 1
    nver = sum(1 for s in steps if s['phase'] == 'VERIFICATION')
    if 'account_service' not in systems: low_ver.append((cid, st, nver))
applicable = dist['COMPLETE'] + dist['INCOMPLETE']
print(f"file={path} lines={len(lines)} rows={len(rows)} dist={dict(dist)}")
print(f"baseline coverage over {applicable} applicable cases: {dict(ver_cov)}")
print(f"cases WITHOUT account_service verification: {len(low_ver)} e.g. {low_ver[:15]}")
print(f"CONTRACT ERRORS: {len(errs)}")
for e in errs[:40]: print("  ", e)
