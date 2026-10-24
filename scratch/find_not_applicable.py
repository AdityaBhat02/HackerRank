import csv

eval_requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))

non_del = []
for r in eval_requests:
    txt = r['request_text'].lower()
    # Check if request has NO mention of delete, erase, cancel, close, remove, exclusão, suppression, löschen, cancellare, etc.
    words = [
        "delet", "eras", "clos", "cancel", "remov", "exclu", "suppr", "lösch",
        "losch", "cancell", "elimina", "borra", "effac", "abschluss", "destroy",
        "purge", "wip", "vergessen", "oublier", "dimenticare", "esquecer", "olvidar", "terminat"
    ]
    if not any(w in txt for w in words):
        non_del.append(r)

print(f"Total without any deletion keywords: {len(non_del)}")
for r in non_del:
    print(f"[{r['case_id']}] {r['request_text']}\n")
