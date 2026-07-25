# Phase 5E-C Platform Policy and Validator Integration Contract — Cycle #002

## Authority

This contract consumes the exact Normalized Engineering Candidate #003 package with SHA-256:

`58c28f66e649ee605e5750091f13549ed6d48d369b8c4e66221b7d5e9c86023c`

The canonical schema is consumed byte-for-byte at:

`docs/cms/schemas/content-model.schema.json`

Required SHA-256:

`4f4a540fdca498616f4b2dd9a2a05e943a16ce0624dd434113c2ff31abefcef0`

Platform must not regenerate, substitute, patch or reinterpret that schema.

## Trust boundary

There is one authoritative workflow:

`.github/workflows/cms-content-integrity.yml`

For routine development pushes, validators, policy, schema, classification and Engineering tests are loaded from the push parent commit.

For promotion pull requests to `main`, the same control surface is loaded from the protected PR base commit. The candidate therefore cannot weaken its own validator.

Candidate-side controls execute only during the one-time bootstrap when:

- `CMS_BOOTSTRAP_ENABLED = true`;
- `CMS_BOOTSTRAP_APPROVED_HEAD_SHA` equals the exact bootstrap commit SHA;
- the source recovery baseline is an ancestor;
- the exact integrated operation manifest matches.

## Validation layers

1. **Repository policy**
   - Exact branch context.
   - One file per routine commit.
   - Content modifications only.
   - Media additions only.
   - No media deletion, rename or replacement.
   - No workflow, schema, Pages CMS configuration, template or validator changes in routine mode.

2. **Engineering semantic validation**
   - Exact v2 schema.
   - Canonical sparse serialization.
   - Typed state/payload conditions.
   - Approved eight-record classifications.
   - Unique IDs, slugs, permalinks and published order.
   - Bilingual completeness.
   - Claim/evidence governance.
   - Media path and accessibility rules.

3. **State-aware transition validation**
   - No blanket key-removal prohibition.
   - Payload removal is accepted only when required by a valid governing-state transition.
   - Old state, new state, record status and review lifecycle are evaluated together.
   - Orphan payloads and missing required payloads fail.

4. **Legacy embedded claim protection**
   - Material edits to configured claim-bearing project paths fail while `claims_state` remains `legacy_embedded`.
   - Conversion must be complete in one record change:
     - `claims_state: structured`;
     - nonempty claims payload;
     - `status: under_review`;
     - content and claim review states reset to `pending`;
     - `review.timestamp_state: not_recorded`;
     - historical reviewer/timestamp removed;
     - each new claim reset to `approval_state: pending`;
     - required evidence references and bilingual boundaries supplied.

5. **Rendered output**
   - Jekyll runs outside the tracked source checkout.
   - All eight runtime routes are inspected.
   - Dates render only for `publication_date_state: recorded`.
   - Decorative images render `alt=""` and `aria-hidden="true"`.
   - Meaningful images retain bilingual alt attributes.
   - No empty OG image metadata.
   - Internal links resolve.
   - Arabic/English markers, initial RTL and unresolved Liquid are checked.

## Date policy

Routine Pages CMS mode cannot introduce, remove or rewrite `published_at`. Recording a publication date requires a later separately authorized controlled operation with evidence. This closes the invented-date risk.

Review timestamps may be created only through the valid `not_recorded -> recorded` lifecycle with completed review decisions, reviewer and timezone-aware timestamp.

## Workflow replacement decision

The proposed workflow replaces `.github/workflows/cms-phase3-build.yml` only inside the exact bootstrap operation set.

The replacement retains the former isolated Jekyll build, identity, bilingual, link, unresolved-Liquid and source-integrity checks, and adds schema v2, classification, transition, media, branch, path, rollback-manifest and protected-base trust controls. Coverage is therefore equal or higher.

## Stable required checks

These names are governance-stable:

- `Validate CMS content and repository policy`
- `Build and validate rendered output`

Changing either name requires a later controlled authorization because GitHub Ruleset required checks depend on them.

