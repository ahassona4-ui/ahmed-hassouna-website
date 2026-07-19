# AH Website CMS — Unified Content Model v2.0 — Candidate #003

This directory contains the single canonical schema, state classification, deterministic migration tools, lifecycle fixtures, regression tests and Platform validator interface.

## Normative sources

- `CONTENT_MODEL_SPECIFICATION.md`
- `CONTENT_MODEL_ADDENDUM.md`
- `schemas/content-model.schema.json`
- `state-classification-v2.json`
- `STATE_CLASSIFICATION_V2.md`
- `MIGRATION_MAP.md`
- `V1_TO_V2_MAPPING.md`

## Engineering interface

- `tools/validate_content_model_v2.py`
- `tools/migrate_content_model_v1_to_v2.py`
- `tools/validate_v1_to_v2_migration.py`
- `tools/simulate_pages_serializer.py`
- `tests/test_content_model_v2.py`
- `tests/fixtures/review-claim-lifecycle-cases.yml`
- `VALIDATOR_INTEGRATION_CONTRACT.md`

No competing workflow and no `assets/main.js` change are included. GitHub write, Pages CMS save, upload, PR, merge, promotion and Phase 6 remain prohibited.

## Candidate #003 correction scope

Corrected Engineering Candidate #003 closes publication-date, published-media and recorded-review lifecycle gaps without changing the eight runtime records, current routes, workflows or `assets/main.js`.
