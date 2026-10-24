import csv

sample_requests = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
eval_requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))

print(f"Sample requests count: {len(sample_requests)}")
print(f"Evaluation requests count: {len(eval_requests)}")

# Let's inspect some sample request texts
print("\n--- First 10 Sample Request Texts ---")
for r in sample_requests[:10]:
    print(f"[{r['case_id']}] {r['request_text'][:90]}...")

# Let's check non-deletion request words in eval requests
non_deletion_keywords = [
    "export", "download my data", "access my data", "copy of my data",
    "rectify", "correction", "update my email", "change my password",
    "marketing", "newsletter", "unsubscribe", "opt out", "opt-out",
    "accs", "tlcharger", "desuscribir", "dar de baja", "actualizar"
]

print("\n--- Checking for potentially non-deletion requests in evaluation set ---")
candidate_not_applicable = []
for r in eval_requests:
    txt = r['request_text'].lower()
    # Check if request specifically asks for export or marketing only without deletion
    is_deletion = any(w in txt for w in ["delete", "remove", "erasure", "suppression", "eliminar", "lschen", "borrar", "chiusura", "supprimer", "löschen", "cerrar mi cuenta", "close my account", "cancel my account"])
    if not is_deletion:
        candidate_not_applicable.append(r)

print(f"Candidates without explicit deletion verbs: {len(candidate_not_applicable)}")
for r in candidate_not_applicable[:15]:
    print(f"[{r['case_id']}] {r['request_text']}")
