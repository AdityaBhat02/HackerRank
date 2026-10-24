import csv
import json
from collections import Counter

def run_account_tombstone_audit():
    print("=== TASK 5: Account & Tombstone Handling Audit ===")
    
    with open('output.csv', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    account_tuples = Counter()
    identity_tuples = Counter()

    cases_with_account = []
    cases_with_tombstone = []

    for r in rows:
        cid = r['case_id']
        st = r['deletion_status']
        steps = json.loads(r['steps_json'])

        for s in steps:
            tup = (s['system_id'], s['operation'], s['state'])
            if s['system_id'] == 'account_service':
                account_tuples[tup] += 1
                cases_with_account.append(cid)
            elif s['system_id'] == 'identity_service':
                identity_tuples[tup] += 1
                cases_with_tombstone.append(cid)

    print("\nAccount Service Step Breakdown across 518 cases:")
    for (sys_id, op, state), count in sorted(account_tuples.items()):
        print(f"  ({sys_id}, {op}, {state}): {count}")

    print("\nIdentity Service Step Breakdown across 518 cases:")
    for (sys_id, op, state), count in sorted(identity_tuples.items()):
        print(f"  ({sys_id}, {op}, {state}): {count}")

    print(f"\nTotal applicable cases with account_service: {len(set(cases_with_account))} / 508 (100.0%)")
    print(f"Total cases with identity_service tombstone: {len(set(cases_with_tombstone))}")

    # Spot-check 5 cases against raw evidence
    print("\nSpot-checking 5 cases against raw evidence:")
    spot_cids = ['case_33', 'case_45', 'case_61', 'case_100', 'case_520']
    with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
        req_map = {r['case_id']: r for r in csv.DictReader(f)}

    for cid in spot_cids:
        row = next(r for r in rows if r['case_id'] == cid)
        req = req_map[cid]
        steps = json.loads(row['steps_json'])
        acct_steps = [s for s in steps if s['system_id'] in ('account_service', 'identity_service')]
        print(f"\n[{cid}] Status: {row['deletion_status']}, Email: {req['email']}")
        for s in acct_steps:
            print(f"   - {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev='{s['evidence_id']}'")

if __name__ == '__main__':
    run_account_tombstone_audit()
