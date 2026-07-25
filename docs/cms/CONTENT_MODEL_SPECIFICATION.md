# AH Website CMS — Unified Content Model Specification v2.0

## Status and authority

- Candidate: **AH Website CMS Schema v2.0 — Corrected Engineering Candidate #003**
- Architecture: Option B+ — canonical omission with typed state fields.
- Source recovery baseline: `262825767ee08e91e5410957686664f3ca6dde05`.
- Canonical JSON Schema owner: CMS Engineering.
- Decision authority: AH Personal Website Operations.

## Canonical serialization

Optional values and containers are omitted when they contain no meaningful value. Runtime records must not store `null`, empty strings, empty arrays, or empty objects. Meaningful `false` and numeric `0` remain valid.

Typed state fields govern ambiguous absence:

- Articles: `publication_date_state`, `media_state`, `claims_state`, `review.timestamp_state`.
- Projects: `media_state`, `claims_state`, `review.timestamp_state`.

## Article policy

- `publication_date_state`: `unassigned | legacy_pending | recorded`.
- `recorded` requires `published_at`; other states prohibit it.
- `legacy_pending` is limited to AH-ART-001..003 and never infers a date from files, Git or build metadata.
- `media_state: ready` requires structured accessible media; other states omit `media`.
- `claims_state: structured` requires nonempty claims; `none` and `not_assessed` omit claims.
- AH-ART-001..003 are `claims_state: none`.

## Project policy

- Existing AH-PRJ-001..005 use `media_state: ready` and `claims_state: legacy_embedded`.
- Existing visuals retain `media.src` and `decorative: true`, omit stored empty alt, and render HTML `alt=""`.
- Meaningful media requires nonempty Arabic and English alt text.
- `legacy_embedded` is migration-only and limited to the five approved current project IDs.

## Review lifecycle

Review objects always require:

- `content_review_state`
- `claim_review_state`
- `timestamp_state`

`reviewed_by`, `reviewed_at`, and `notes` are conditional/optional:

| timestamp_state | Required | Prohibited | Review-state rule |
|---|---|---|---|
| `not_recorded` | none | `reviewed_at` | both review states must remain `pending`; reviewer and notes may be absent |
| `legacy_unrecorded` | `reviewed_by` | `reviewed_at` | limited to the eight approved migrated records; both review states are `approved` |
| `recorded` | `reviewed_by`, timezone-aware `reviewed_at` | — | required for completed future approval or rejection |

Optional notes are omitted when no value exists.

## Structured claims

Every claim requires `claim_id`, `claim_type`, bilingual `text`, and `approval_state`.

- `quantitative` and `status` require nonempty `evidence_refs` and bilingual `boundary`.
- `credential` requires nonempty `evidence_refs`.
- `approval_state: approved` requires `approved_by` and timezone-aware `approved_at`.
- `approval_state: baseline_approved` is migration-only for governed evidence from AH-PRJ-001..005, requires `approved_by`, and prohibits a fabricated `approved_at`.
- `baseline_approved` is prohibited for articles and non-migrated records.

## Publication and accessibility

Published records require approved bilingual translation and approved content/claim review. Published projects require ready media. Published articles may deliberately use `media_state: none`.

Decorative images render `alt=""` and `aria-hidden="true"`. Meaningful images require Arabic and English alt. OG image renders only when a real repository-local path exists.

## Engineering and Platform boundary

Engineering owns the canonical schema, semantic validator, migration validator, fixtures and regression tests. Platform Security owns the final unified workflow, branch/ruleset enforcement and promotion implementation. This candidate adds no competing workflow.

## Correction Cycle #003 — Publication, media and review decision lifecycle

- `publication_date_state: unassigned` is valid only when article `status` is `draft` or `under_review`; it is invalid for `published` and `archived`.
- A published article permits `media_state: none`, or `media_state: ready` with a schema-valid media payload. `planned` and `not_assessed` block publication.
- A published project requires `media_state: ready` and a schema-valid project media payload. `none`, `planned` and `not_assessed` block publication.
- `review.timestamp_state: recorded` represents a completed decision. Both review states must be `approved` or `rejected`; neither may remain `pending`. Reviewer and timezone-aware `reviewed_at` remain mandatory.
- `not_recorded` remains pending-only. `legacy_unrecorded` remains limited to the eight approved migrated records.
