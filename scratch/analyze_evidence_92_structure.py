import json

data = json.load(open('dataset/evidence/records/service_resource_export_20260915_114455.json', encoding='utf-8'))
exp = data['service_exports']

for svc, items in exp.items():
    print(f"\n--- Service: {svc} ---")
    if isinstance(items, dict):
        for subk, subitems in items.items():
            print(f"  Subkey: {subk} ({len(subitems)} items)")
            for it in subitems[:4]:
                print(f"    {it}")
