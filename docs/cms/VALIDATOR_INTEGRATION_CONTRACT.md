# Validator Integration Contract for Platform Security — Candidate #003

## Ownership

CMS Engineering owns the canonical schema, semantic validator, deterministic migration, fixtures and regression tests. Platform Security owns the one final workflow, branch/ruleset policy and promotion enforcement. No workflow is included in this Engineering package.

## Canonical command

```bash
python3 docs/cms/tools/validate_content_model_v2.py   --root .   --schema docs/cms/schemas/content-model.schema.json   --classification docs/cms/state-classification-v2.json   --report-json build-logs/content-model-v2.json
```

Regression and migration checks:

```bash
python3 -m unittest docs/cms/tests/test_content_model_v2.py
python3 docs/cms/tools/validate_v1_to_v2_migration.py   --v1-root <recovery-record-root>   --v2-root .   --classification docs/cms/state-classification-v2.json   --migrator docs/cms/tools/migrate_content_model_v1_to_v2.py   --report-json build-logs/v1-v2-migration.json
```

## Exit contract

Exit `0` means runtime records and samples satisfy Draft 2020-12 schema, typed review lifecycle, structured-claim evidence/boundary/approval rules, approved classifications, canonical omission, media security, accessibility source rules, circular navigation and template-state controls. Any nonzero exit must fail promotion closed.

## Dependency contract

Platform must use a standards-compliant `jsonschema` implementation with format checking enabled. The schema byte SHA recorded in the candidate manifest is authoritative.

## Required Platform assertions

- Use the exact canonical schema bytes and SHA.
- Run in an isolated workspace.
- Do not add a competing schema or Engineering validator.
- Verify branch/event/promotion boundaries separately.
- Keep repository permissions read-only for validation.

## Cycle #003 mandatory lifecycle probes

Platform must consume the exact canonical schema bytes and run the Engineering validator. Required probes include archived+unassigned failure, published article media gates, published project ready-media gate, pending+recorded failure, completed approved/rejected recorded success, and under-review pending+not_recorded success.
