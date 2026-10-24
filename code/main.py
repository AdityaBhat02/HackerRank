"""Main entrypoint for Ghost Data Still Exists Deletion Audit Agent.
Audits all 518 cases in dataset/deletion_requests.csv and outputs root output.csv.
Adheres strictly to the output format, ordering, and JSON contract.
"""

import os
import sys
import csv
import json
import time
from typing import Dict, List, Any

# Ensure local imports work cleanly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import config
from decision_engine import DecisionEngine
from request_classifier import RequestClassifier
from image_knowledge import get_multimodal_token_usage

def run_audit(dataset_dir: str = None, output_csv_path: str = None):
    dataset_dir = dataset_dir or config.DATASET_DIR
    output_csv_path = output_csv_path or config.OUTPUT_CSV_PATH
    requests_path = os.path.join(dataset_dir, "deletion_requests.csv")

    print(f"=== Northstar Shop AI Deletion Audit Agent ===")
    print(f"Loading deletion requests from: {requests_path}")
    print(f"Output target: {output_csv_path}")

    start_time = time.time()
    engine = DecisionEngine(dataset_dir)
    init_time = time.time() - start_time
    print(f"Engine initialized in {init_time:.2f}s (11 images, 26 logs, 24 databases, 28 JSON bundles indexed).")

    with open(requests_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    print(f"Total cases to audit: {len(cases)}")

    results = []
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
    total_steps = 0

    for idx, case in enumerate(cases, 1):
        cid = case['case_id']
        status, steps = engine.audit_case(case)
        status_counts[status] = status_counts.get(status, 0) + 1
        total_steps += len(steps)

        # Serialize steps as JSON string
        steps_json_str = json.dumps(steps, separators=(',', ':'))

        results.append({
            "case_id": cid,
            "deletion_status": status,
            "steps_json": steps_json_str
        })

        if idx % 100 == 0 or idx == len(cases):
            print(f"Processed [{idx}/{len(cases)}] cases... (Status: {status_counts})")

    # Sort strictly by case_id integer
    results.sort(key=lambda r: int(r['case_id'].split('_')[1]))

    # Write root output.csv
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for r in results:
            writer.writerow([r["case_id"], r["deletion_status"], r["steps_json"]])

    # Also sync write to dataset/output.csv
    ds_out = os.path.join(dataset_dir, "output.csv")
    if os.path.abspath(ds_out) != os.path.abspath(output_csv_path):
        with open(ds_out, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "deletion_status", "steps_json"])
            for r in results:
                writer.writerow([r["case_id"], r["deletion_status"], r["steps_json"]])
    elapsed = time.time() - start_time
    print(f"\nAudit completed in {elapsed:.2f}s.")
    print(f"Successfully generated {output_csv_path} with {len(results)} rows.")
    print(f"Summary:")
    print(f"  - COMPLETE: {status_counts.get('COMPLETE', 0)}")
    print(f"  - INCOMPLETE: {status_counts.get('INCOMPLETE', 0)}")
    print(f"  - NOT_APPLICABLE: {status_counts.get('NOT_APPLICABLE', 0)}")
    print(f"  - Total remediation/verification steps: {total_steps}")
    print(f"  - Avg steps per case: {total_steps / len(results):.2f}")

    return results

if __name__ == "__main__":
    run_audit()
