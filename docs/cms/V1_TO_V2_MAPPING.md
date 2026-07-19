# Corrected Engineering Candidate #003 — v1-to-v2 Mapping

The migration tool reads recovery-baseline v1.0 records, applies `state-classification-v2.json`, and writes a separate v2 output directory.

- Runtime accepts only string `schema_version: "2.0"`.
- Compatibility input accepts v1.0/v1.1 only inside isolated migration tests.
- A v2 input returns unchanged.
- Unknown versions fail closed.
- Second-pass migration is byte-identical.
- AH-ART-001..003 map to `claims_state: none`.
- AH-PRJ-001..005 map to `claims_state: legacy_embedded`.
- Migrated approved reviews map to `legacy_unrecorded`, require the existing reviewer and omit timestamp.
- No date, reviewer, approval timestamp, claim, evidence or boundary is inferred.

## Cycle #003 validation note

The source-to-target mapping is unchanged. Candidate #003 strengthens only the post-migration lifecycle constraints and test coverage.
