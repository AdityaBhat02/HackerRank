"""Independent spot-check and dangling ID validator across all 518 cases."""
import csv
import json
import random
import sys

def run_spot_check():
    print("=== TASK 8: Spot-Check and Dangling ID Audit ===")
    
    # Load manifest and valid IDs
    with open('dataset/evidence_files.csv', encoding='utf-8') as f:
        file_ids = set(r['file_id'] for r in csv.DictReader(f))
    with open('dataset/system_activity.csv', encoding='utf-8') as f:
        act_ids = set(r['activity_id'] for r in csv.DictReader(f))
    with open('dataset/user_audit_log.csv', encoding='utf-8') as f:
        audit_ids = set(r['audit_id'] for r in csv.DictReader(f))
    
    valid_ids = file_ids | act_ids | audit_ids
    print(f"Valid Evidence Reference IDs indexed: {len(valid_ids)} (Files: {len(file_ids)}, Activities: {len(act_ids)}, Audits: {len(audit_ids)})")

    # Load output.csv
    with open('output.csv', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"Total rows in output.csv: {len(rows)}")

    # 1. Dangling ID Check across ALL 518 rows
    dangling_ids = []
    citation_invariant_errors = []

    for r in rows:
        cid = r['case_id']
        st = r['deletion_status']
        steps = json.loads(r['steps_json'])

        for idx, s in enumerate(steps, 1):
            eid = s.get('evidence_id', '')
            phase = s['phase']

            if st == 'COMPLETE':
                if not eid:
                    citation_invariant_errors.append(f"{cid} COMPLETE step {idx} ({s['system_id']}) has empty evidence_id")
                elif eid not in valid_ids:
                    dangling_ids.append((cid, idx, eid, phase, s['system_id']))
            elif st == 'INCOMPLETE':
                if phase == 'FINDING':
                    if not eid:
                        citation_invariant_errors.append(f"{cid} FINDING step {idx} has empty evidence_id")
                    elif eid not in valid_ids:
                        dangling_ids.append((cid, idx, eid, phase, s['system_id']))
                else:
                    if eid != "":
                        citation_invariant_errors.append(f"{cid} INCOMPLETE {phase} step {idx} has non-empty evidence_id: '{eid}'")

    print(f"Dangling IDs across all 518 cases: {len(dangling_ids)}")
    if dangling_ids:
        for d in dangling_ids[:10]:
            print(f"  [FAIL] DANGLING ID: {d}")
        sys.exit(1)
    else:
        print("  [OK] ZERO dangling IDs found across all 518 cases!")

    print(f"Citation invariant errors: {len(citation_invariant_errors)}")
    if citation_invariant_errors:
        for e in citation_invariant_errors[:10]:
            print(f"  [FAIL] INVARIANT ERROR: {e}")
        sys.exit(1)
    else:
        print("  [OK] ZERO citation invariant errors found across all 518 cases!")

    # 2. Pick 15 random cases with fixed seed + all 10 NOT_APPLICABLE cases
    random.seed(42)
    na_cases = [r for r in rows if r['deletion_status'] == 'NOT_APPLICABLE']
    other_cases = [r for r in rows if r['deletion_status'] != 'NOT_APPLICABLE']
    sample_15 = random.sample(other_cases, 15)

    spot_cases = na_cases + sample_15
    print(f"\nSpot-checking {len(spot_cases)} cases (10 NOT_APPLICABLE + 15 Random production cases):")
    print(f"{'Case ID':<10} | {'Status':<15} | {'Steps':<6} | {'Summary'}")
    print("-" * 80)
    for sc in spot_cases:
        cid = sc['case_id']
        st = sc['deletion_status']
        steps = json.loads(sc['steps_json'])
        step_summary = f"{len(steps)} steps"
        if steps:
            systems = list(dict.fromkeys(s['system_id'] for s in steps))
            step_summary += f" ({', '.join(systems[:3])})"
        print(f"{cid:<10} | {st:<15} | {len(steps):<6} | {step_summary}")

    print("\n[OK] TASK 8 Spot-Check & Dangling ID Audit Completed Successfully!")

if __name__ == '__main__':
    run_spot_check()
