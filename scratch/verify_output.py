import os
import csv
import json

output_path = "output.csv"
assert os.path.exists(output_path), "output.csv does not exist!"

with open(output_path, "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))

print(f"Total rows: {len(reader)}")
assert len(reader) == 518, f"Expected 518 rows, got {len(reader)}"

case_ids = [r['case_id'] for r in reader]
sorted_case_ids = sorted(case_ids, key=lambda x: int(x.split('_')[1]))
assert case_ids == sorted_case_ids, "Rows are not sorted by case_id!"

status_counts = {}
for idx, r in enumerate(reader):
    st = r['deletion_status']
    status_counts[st] = status_counts.get(st, 0) + 1
    assert st in ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"], f"Invalid status: {st} at row {idx}"
    
    steps = json.loads(r['steps_json'])
    assert isinstance(steps, list), f"steps_json is not a list at {r['case_id']}"
    if st == "NOT_APPLICABLE":
        assert len(steps) == 0, f"NOT_APPLICABLE must have empty steps_json at {r['case_id']}"
    else:
        for s in steps:
            assert "phase" in s
            assert "system_id" in s
            assert "resource_id" in s
            assert "operation" in s
            assert "state" in s
            assert "evidence_id" in s
            assert "step_no" in s

print("Status counts:", status_counts)
print("ALL 518 ROWS FULLY VALIDATED AND STRICTLY FORMATTED!")
