# Phase 5E-A — Corrected v1-to-v2 Migration Map — Cycle #002

## Compatibility input to canonical v2

| Recovery/v1 input | Canonical v2 output |
|---|---|
| Missing/empty approved publication date plus legacy compatibility flag | Omit date input; set `publication_date_state: legacy_pending` |
| Approved date | Retain date; set `publication_date_state: recorded` |
| Empty article media | Omit `media`; set `media_state: none` |
| Approved decorative project visual | Retain `media.src` and `decorative: true`; omit empty alt; set `media_state: ready` |
| No structured claims under approved classification | Omit `claims`; set `claims_state: none` |
| Approved project narrative claims without structured array | Omit `claims`; set `claims_state: legacy_embedded` |
| Nonempty governed claim collection | Retain; set `claims_state: structured` |
| Approved migrated review without historical timestamp | Require reviewer, omit timestamp; set `review.timestamp_state: legacy_unrecorded` |
| New pending review without timestamp | Omit reviewer/notes when absent; set both review states pending and `timestamp_state: not_recorded` |
| Completed future review | Require reviewer and timezone-aware timestamp; set `timestamp_state: recorded` |

## Eight-record classification

| ID | Publication | Media | Claims | Review timestamp |
|---|---|---|---|---|
| AH-ART-001 | legacy_pending | none | none | legacy_unrecorded |
| AH-ART-002 | legacy_pending | none | none | legacy_unrecorded |
| AH-ART-003 | legacy_pending | none | none | legacy_unrecorded |
| AH-PRJ-001..005 | N/A | ready | legacy_embedded | legacy_unrecorded |

## Structured-claim migration governance

`baseline_approved` is allowed only for governed evidence from AH-PRJ-001..005 during a separately controlled conversion to structured claims. It requires `approved_by`, prohibits a fabricated approval timestamp, and remains prohibited for articles and new records.

No migration step may invent dates, media, claims, evidence, boundaries, reviewer identities, timestamps, IDs, URLs, order, navigation or professional content.

## Post-migration lifecycle validation

The deterministic migration still produces the same eight approved v2 runtime records. After migration, validation additionally rejects archived articles with `unassigned`, published articles with `planned`/`not_assessed`, published projects without `ready` media, and recorded reviews containing any pending decision state.
