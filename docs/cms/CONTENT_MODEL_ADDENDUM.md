# Content Model Addendum — Phase 2R Mandatory Corrections

This addendum is normative and overrides conflicting statements in `CONTENT_MODEL_SPECIFICATION.md` and non-runtime samples.

## A. Circular Project Navigation

The approved RC4.4 behavior is circular:

- The Previous link on the first published project points to the last published project.
- The Next link on the last published project points to the first published project.
- All intermediate projects link to adjacent projects according to approved published order.
- The Back link returns to Selected Work.
- Arabic/English state remains preserved.

For the current order:

`AH-PRJ-001 → AH-PRJ-002 → AH-PRJ-003 → AH-PRJ-004 → AH-PRJ-005 → AH-PRJ-001`

The reverse Previous sequence follows the same circular set. Links are generated from the approved published order; they are not editorial free-text fields.

## B. Legacy Article Date Control

Existing RC4.4 articles have no approved publication dates in the baseline. Therefore:

```yaml
published_at: null
legacy_date_pending: true
order: <explicit positive integer>
```

Rules:

1. No date may be inferred from file timestamps, Git commits, upload dates, or migration dates.
2. Legacy articles are temporarily ordered by explicit `order`.
3. `legacy_date_pending` remains true until AH Personal Website Operations approves a documented publication date.
4. New articles may use an approved `published_at` after the relevant workflow is implemented.
5. The absence of a date does not authorize displaying a fabricated date.

## C. Phase 3 Preview Rule

The Phase 3 article dev preview uses `published_at: null`, `legacy_date_pending: true`, and explicit `order: 1`. The project preview uses the existing circular neighbors for AH-PRJ-001: Previous = AH-PRJ-005 and Next = AH-PRJ-002.
