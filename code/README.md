# Northstar Shop AI Deletion Audit Agent

Autonomous agent pipeline for auditing GDPR Article 17 / CCPA personal data deletion requests across distributed microservices, databases, backups, search indexes, analytics platforms, and support archives for the HackerRank Orchestrate challenge:
https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

---

## 1. Modular Architecture

The submission package is organized into modular decoupled components following clean separation of concerns:

```
.
├── config.py                 # Central configuration for paths, models, thresholds, and fallbacks
├── identity.py               # Multi-identifier resolution (historical emails, phones, SHA-256 hashes)
├── request_classifier.py     # Multilingual intent classification & 5-stage non-deletion filtering
├── evidence_parser.py        # Multi-format parser (JSON, SQL, TXT, LOG, PDF)
├── image_knowledge.py        # Multimodal Vision LLM extraction with disk caching
├── activity_tracker.py       # Temporal correlation of deletion worker operations
├── decision_engine.py        # State reasoning, policy rule enforcement, and step synthesis
├── main.py                   # Main CLI entry point producing root output.csv
├── requirements.txt          # Production dependencies
├── README.md                 # System overview and operational guide
├── prompts/                  # Externalized system and task prompt templates
│   ├── request_classifier_prompt.txt
│   └── image_extraction_prompt.txt
├── cache/                    # Pre-warmed multimodal cache for deterministic latency
│   └── multimodal_cache.json
└── evaluation/               # Comprehensive evaluation runner & reports
    ├── main.py               # Evaluation script
    ├── custom_cases.json     # Custom adversarial and multilingual evaluation cases
    ├── evaluation_report.md  # 6-section benchmark accuracy & regression report
    ├── usage_report.md       # Token usage and cost accounting report (Table A & Table B)
    └── usage_log.jsonl       # Audit call metadata log (strictly no keys or prompt bodies)
```

### Component Data Flow

1. **Request Ingestion & Intent Filtering (`request_classifier.py`):**
   Evaluates user inquiries against Article 17 deletion mandates. Inquiries asking for data portability exports, billing invoices, or explicitly requesting to keep the account active are marked `NOT_APPLICABLE` with `steps_json = []`.

2. **Identity Resolution (`identity.py`):**
   Traces the requester's email through `user_identities.csv` and `user_audit_log.csv` to reconstruct the complete identity profile, including historical email addresses, phone numbers, and pseudonymized hashes.

3. **Multimodal & Heterogeneous Evidence Ingestion (`evidence_parser.py` & `image_knowledge.py`):**
   Extracts evidence states from 94 files across SQL dumps, JSON analytics snapshots, shift handover logs, support ticket attachments, and OCR/Vision console screenshots. Image evidence uses a two-tier pipeline: checking `cache/multimodal_cache.json` first, then falling back to dynamic Vision LLM inference.

4. **Activity Correlation (`activity_tracker.py`):**
   Matches `deletion_worker` operations recorded in `system_activity.csv` within the case timeline window to track downstream resource deletion, redaction, and verification events.

5. **Decision & Step Synthesis (`decision_engine.py`):**
   Applies deletion policy rules under strict temporal cutoff (`captured_at <= audit_at`).
   - If residual data is detected -> `INCOMPLETE`, generating `FINDING`, `REMEDIATION`, and `VERIFICATION` steps.
   - If all systems are verified clean -> `COMPLETE`, generating `VERIFICATION` steps with cited evidence.
   - Sorts steps strictly by `phase` -> `operation` -> `system_id` -> `resource_id`.

---

## 2. Installation & Prerequisites

Python 3.10+ is required. Install required dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables (Optional)

The agent automatically discovers the dataset directory and output paths, but the following standard environment variable overrides are supported:

- `DATASET_DIR`: Path to the directory containing dataset files (e.g. `deletion_requests.csv`). Defaults to auto-discovery.
- `OUTPUT_CSV_PATH`: Destination path for the generated output CSV. Defaults to `output.csv`.
- `GEMINI_API_KEY`: API key for live LLM invocations when running in live uncached environments (optional; offline cache is included).

---

## 4. Execution Instructions

### A. Run Full Audit (Generate `output.csv`)

To audit all 518 cases from `dataset/deletion_requests.csv` and output the submission file:

```bash
python main.py
```

Output:
- Generates `output.csv` with exactly 518 data rows.
- Matches the exact `case_id` sequence of `dataset/deletion_requests.csv`.
- Columns: `case_id,deletion_status,steps_json`.

### B. Run Evaluation Suite

To run benchmark evaluation against sample ground truth and custom test cases:

```bash
python evaluation/main.py
```

Output:
- Runs evaluation against `dataset/sample_output.csv` and `evaluation/custom_cases.json`.
- Updates `evaluation/evaluation_report.md` (100.00% status and sequence accuracy).
- Updates `evaluation/usage_report.md` (Table A cold-start and Table B cached runs).
- Updates `evaluation/usage_log.jsonl` with structured call metadata.

---

## 5. Policy Ordering & Step Sequencing Specification

Steps within `steps_json` adhere strictly to the following 3-phase lifecycle:

1. **`FINDING` Phase:**
   - `REPORT_REMAINING_RECORD`
   - `REPORT_EXPOSED_PII`
   - `REPORT_ACTIVE_DATA_FLOW`
   - `REPORT_RESTORE_RISK`
2. **`REMEDIATION` Phase:**
   - `DISABLE_DATA_FLOW`
   - `BLOCK_RESTORE`
   - `DELETE_RECORD`
   - `REDACT_RECORD`
   - `ANONYMIZE_RECORD`
3. **`VERIFICATION` Phase:**
   - `VERIFY_RECORD_ABSENT`
   - `VERIFY_RECORD_PRESENT`
   - `VERIFY_RECORD_REDACTED`
   - `VERIFY_RECORD_ANONYMIZED`
   - `VERIFY_DATA_FLOW_DISABLED`
   - `VERIFY_RESTORE_BLOCKED`

Deterministic tie-breaking: Within each operation, steps are sorted alphabetically by `system_id` ascending, then `resource_id` ascending. Step numbering (`step_no`) starts at 1 and increments sequentially.
