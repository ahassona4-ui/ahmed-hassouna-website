# Content Model Addendum — v2.0 Corrected Engineering Candidate #003

## Normative supersession

This addendum supersedes the v1 explicit-empty contract. The active v2 publication field is `publication_date_state`. A compatibility adapter may read the old v1 field only in isolated migration fixtures and must never write it to v2 runtime output.

## Canonical classifications

- AH-ART-001, AH-ART-002, AH-ART-003: `claims_state: none`.
- AH-PRJ-001..005: `claims_state: legacy_embedded`.
- All eight migrated records: `review.timestamp_state: legacy_unrecorded`, approved review states, an identified reviewer, and no stored review timestamp.

## Review correction cycle #002

- `reviewed_by` is not globally required.
- `notes` is optional and omitted when empty.
- `recorded` requires reviewer and timezone-aware timestamp.
- `legacy_unrecorded` is migration-only, requires reviewer, and prohibits timestamp.
- `not_recorded` prohibits timestamp and is valid only while both review states are pending.

## Structured-claim correction cycle #002

- Quantitative/status claims require evidence and bilingual boundary.
- Credential claims require evidence.
- Approved claims require approver and timezone-aware approval timestamp.
- Baseline-approved claims are limited to governed migrated project evidence, require an approver, and do not fabricate a historical timestamp.

## Canonical schema

`docs/cms/schemas/content-model.schema.json` is the single normative JSON Schema v2.0 source. Every distributed copy must be byte-identical and use the recorded SHA-256.

## Cycle #003 normative lifecycle closure

This correction closes the remaining conditional gaps in the canonical schema. The publication, media-publication and review-decision rules in the specification are normative and are enforced by both Draft 2020-12 schema validation and the semantic validator.
