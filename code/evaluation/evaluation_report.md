# Northstar Shop AI Deletion Audit Agent - Evaluation Report

## 1. Case-Level Status Accuracy

- **Evaluated Sample Cases:** 32
- **Correct Status Predictions:** 32 / 32
- **Status Accuracy:** 100.00%

| Case ID | Ground Truth Status | Predicted Status | Match |
| :--- | :--- | :--- | :--- |
| `case_01` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_02` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_03` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_04` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_05` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_06` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_07` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_08` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_09` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_10` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_11` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_12` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_13` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_14` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_15` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_16` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_17` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_18` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_19` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_20` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_21` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_22` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_23` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_24` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_25` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_26` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_27` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_28` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_29` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_30` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |
| `case_31` | `COMPLETE` | `COMPLETE` | ✅ PASS |
| `case_32` | `INCOMPLETE` | `INCOMPLETE` | ✅ PASS |

## 2. Step-Level and Field-Level Accuracy

- **Total Expected Ground Truth Steps:** 193
- **Overall Field-Level Alignment:** 100.00%

| Field | Matches | Comparisons | Accuracy |
| :--- | :--- | :--- | :--- |
| `phase` | 193 | 193 | 100.00% |
| `system_id` | 193 | 193 | 100.00% |
| `resource_id` | 193 | 193 | 100.00% |
| `operation` | 193 | 193 | 100.00% |
| `state` | 193 | 193 | 100.00% |
| `evidence_id` | 193 | 193 | 100.00% |

## 3. Sequence Accuracy

- **Exact Step Ordering Match Rate:** 100.00%
- All steps strictly follow the canonical 3-phase progression:
  1. `FINDING` (1. REPORT_REMAINING_RECORD, 2. REPORT_EXPOSED_PII, 3. REPORT_ACTIVE_DATA_FLOW, 4. REPORT_RESTORE_RISK)
  2. `REMEDIATION` (1. DISABLE_DATA_FLOW, 2. BLOCK_RESTORE, 3. DELETE_RECORD, 4. REDACT_RECORD, 5. ANONYMIZE_RECORD)
  3. `VERIFICATION` (1. VERIFY_RECORD_ABSENT, 2. VERIFY_RECORD_PRESENT, 3. VERIFY_RECORD_REDACTED, 4. VERIFY_RECORD_ANONYMIZED, 5. VERIFY_DATA_FLOW_DISABLED, 6. VERIFY_RESTORE_BLOCKED)
- Tie breaking: sorted deterministically by `system_id` ascending, then `resource_id` ascending.

## 4. Custom Evaluation Cases Created by Team

To test complex GDPR Article 17 edge cases, multi-lingual stems, and temporal boundaries, 11 custom cases were implemented and verified:

| Case ID | Expected Status | Predicted Status | Scenario Summary | Result |
| :--- | :--- | :--- | :--- | :--- |
| `custom_case_01` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | Please send me a download of all my purchase history and upd... | ✅ PASS |
| `custom_case_02` | `COMPLETE` | `COMPLETE` | Hi, I haven't used this account in years and would like it c... | ✅ PASS |
| `custom_case_03` | `INCOMPLETE` | `INCOMPLETE` | Por favor, elimine permanentemente mi cuenta de usuario y to... | ✅ PASS |
| `custom_case_04` | `INCOMPLETE` | `INCOMPLETE` | Bitte löschen Sie mein Kundenkonto und alle meine Daten unwi... | ✅ PASS |
| `custom_case_05` | `COMPLETE` | `COMPLETE` | Please erase my account (user_39, user_id > 10) and verify l... | ✅ PASS |
| `custom_case_06` | `INCOMPLETE` | `INCOMPLETE` | I am writing to formally request the erasure of my personal ... | ✅ PASS |
| `custom_case_07` | `INCOMPLETE` | `INCOMPLETE` | Please delete all account and telemetry profile records belo... | ✅ PASS |
| `custom_case_08` | `INCOMPLETE` | `INCOMPLETE` | Please delete my profile and redact any customer service con... | ✅ PASS |
| `custom_case_09` | `INCOMPLETE` | `INCOMPLETE` | 계정과 관련된 모든 개인정보를 삭제해 주십시오. (Please delete all personal data)... | ✅ PASS |
| `custom_case_10` | `INCOMPLETE` | `INCOMPLETE` | Please erase my account, including any previous email addres... | ✅ PASS |
| `custom_case_11` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | Please stop sending me marketing emails. I still use the sto... | ✅ PASS |

## 5. Failures Found During Development and Improvements Made

1. **Trace Correlation Grouping in Readback Logs:** In `evidence_94` (`resource_lookup_trace_*.log`), profile lookup start events contain the customer email while completion events contain HTTP status codes (200/404). Grouping by `trace_id` resolved fragmented lookups.
2. **Sanitizing String Literal 'null' Attributes:** In syslogs, unquoted or quoted `lookup_key=null` and `customer_reference=null` previously evaluated to truthy strings. Adding explicit `None` normalization prevented false identity matching.
3. **Cross-Batch Activity Windowing:** Fixed activity linking to restrict deletion worker operations within [-4 hours, +2 hours] around `reported_at`, preventing unrelated worker operations from contaminating adjacent user batches.
4. **Tombstone Deep Inspection:** Identity service tombstones often retain internal user references correctly but leak full names or emails. Implemented deep PII inspection verifying that `name`, `email`, `phone`, and `email_hash` are all null before marking as `REDACTED`.
5. **Eliminating Account Shortcut Heuristics:** Replaced early hardcoded ID assumptions with a unified two-tier lookup: prioritizing actual `deletion_worker` operations on `account_service` from `system_activity.csv`, with fallback to the database schema convention observed across profile tables.

## 6. Generalization Safeguards (Sample Set to Production Set)

- **Zero Case ID Hardcoding:** Logic operates strictly on user attributes, activity timestamps, and cryptographic hashes without any hardcoded case numbers.
- **5-Stage Negation-First Intent Classifier:** Evaluates inquiries across English, Spanish, German, French, Italian, Portuguese, Japanese, and Korean. Detects non-deletion requests (data portability, billing invoices, marketing unsubscribes, address updates, login resets) even when words like 'delete' appear in negative contexts.
- **Catalog Identity Mapping:** Dynamically links unattached storage objects (e.g., PDF delivery confirmations) and external marketing consoles to users via `LINK_RESOURCE_IDENTITY` activity records.
- **Transitive Closure Identity Resolution:** Multi-hop identity graphs trace historical email changes and SHA-256 hashes across `user_identities.csv` and `user_audit_log.csv`.
