import json, sys
sys.path.insert(0, 'code')
from decision_engine import DecisionEngine

engine = DecisionEngine('dataset')

cases = [
    {
        'case_id': 'custom_case_01',
        'email': 'elena.rostova@gmail.com',
        'requested_at': '2026-09-18T10:15:00Z',
        'reported_status': 'NOT_STARTED',
        'reported_at': '2026-09-18T12:00:00Z',
        'audit_at': '2026-09-25T12:00:00Z',
        'request_text': 'Please send me a download of all my purchase history and update my billing email, but leave the account active so I can keep placing orders.',
        'expected_status': 'NOT_APPLICABLE'
    },
    {
        'case_id': 'custom_case_02',
        'email': 'amina.elmasri@gmail.com',
        'requested_at': '2026-08-19T10:00:00Z',
        'reported_status': 'COMPLETE',
        'reported_at': '2026-08-20T16:42:00Z',
        'audit_at': '2026-09-01T12:00:00Z',
        'request_text': 'Hi, I haven\'t used this account in years and would like it closed. Please remove the profile and the personal details attached to it.',
        'expected_status': 'COMPLETE'
    },
    {
        'case_id': 'custom_case_03',
        'email': 'leila.haddad@yahoo.com',
        'requested_at': '2026-08-27T08:00:00Z',
        'reported_status': 'COMPLETE',
        'reported_at': '2026-08-28T09:03:00Z',
        'audit_at': '2026-09-05T12:00:00Z',
        'request_text': 'Por favor, elimine permanentemente mi cuenta de usuario y todos los datos asociados en sus sistemas.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_04',
        'email': 'jonas.berg@outlook.com',
        'requested_at': '2026-08-29T06:51:00Z',
        'reported_status': 'PARTIALLY_COMPLETE',
        'reported_at': '2026-08-30T17:12:00Z',
        'audit_at': '2026-09-10T09:15:00Z',
        'request_text': 'Bitte löschen Sie mein Kundenkonto und alle meine Daten unwiderruflich aus allen Datenbanken und Suchindizes.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_05',
        'email': 'lucas-souza95@gmail.com',
        'requested_at': '2026-09-02T12:00:00Z',
        'reported_status': 'PARTIALLY_COMPLETE',
        'reported_at': '2026-09-03T12:00:00Z',
        'audit_at': '2026-10-01T12:00:00Z',
        'request_text': 'Please erase my account (user_39, user_id > 10) and verify legal retention holds on compliance security logs.',
        'expected_status': 'COMPLETE'
    },
    {
        'case_id': 'custom_case_06',
        'email': 'k.appiah88@gmail.com',
        'requested_at': '2026-09-01T04:22:00Z',
        'reported_status': 'NOT_STARTED',
        'reported_at': '2026-09-01T20:22:00Z',
        'audit_at': '2026-09-17T09:22:00Z',
        'request_text': 'I am writing to formally request the erasure of my personal data under GDPR Article 17.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_07',
        'email': 'darwish.omar@icloud.com',
        'requested_at': '2026-09-05T08:14:00Z',
        'reported_status': 'NOT_STARTED',
        'reported_at': '2026-09-05T20:14:00Z',
        'audit_at': '2026-09-17T09:14:00Z',
        'request_text': 'Please delete all account and telemetry profile records belonging to my email.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_08',
        'email': 'e.varga90@yahoo.com',
        'requested_at': '2026-08-17T12:00:00Z',
        'reported_status': 'PARTIALLY_COMPLETE',
        'reported_at': '2026-08-19T12:00:00Z',
        'audit_at': '2026-09-15T12:00:00Z',
        'request_text': 'Please delete my profile and redact any customer service conversations.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_09',
        'email': 'minjun.kim@gmail.com',
        'requested_at': '2026-08-24T12:00:00Z',
        'reported_status': 'COMPLETE',
        'reported_at': '2026-08-25T12:00:00Z',
        'audit_at': '2026-09-15T12:00:00Z',
        'request_text': '계정과 관련된 모든 개인정보를 삭제해 주십시오. (Please delete all personal data).',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_10',
        'email': 'thandiwe.m6866@zoho.com',
        'requested_at': '2026-09-06T08:00:00Z',
        'reported_status': 'NOT_STARTED',
        'reported_at': '2026-09-06T18:00:00Z',
        'audit_at': '2026-09-17T09:00:00Z',
        'request_text': 'Please erase my account, including any previous email addresses and hashes.',
        'expected_status': 'INCOMPLETE'
    },
    {
        'case_id': 'custom_case_11',
        'email': 'marketing.unsubscribe@example.com',
        'requested_at': '2026-09-18T10:00:00Z',
        'reported_status': 'NOT_STARTED',
        'reported_at': '2026-09-18T12:00:00Z',
        'audit_at': '2026-09-25T12:00:00Z',
        'request_text': 'Please stop sending me marketing emails. I still use the store and need my account open.',
        'expected_status': 'NOT_APPLICABLE'
    }
]

passed = 0
for c in cases:
    st, steps = engine.audit_case(c)
    ok = (st == c['expected_status'])
    if ok:
        passed += 1
    c['expected_steps'] = steps
    print(f"{c['case_id']}: expected={c['expected_status']}, pred={st}, steps={len(steps)} -> {'PASS' if ok else 'FAIL'}")

print(f"Total passed: {passed}/{len(cases)}")

# Save to custom_cases.json
with open('code/evaluation/custom_cases.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, indent=2)
print("Updated code/evaluation/custom_cases.json with 11 custom cases.")
