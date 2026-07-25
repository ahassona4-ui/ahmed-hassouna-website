# Phase 5E Cycle #002 Security Acceptance Checklist

## Package integrity

- [ ] Normalized Engineering package SHA equals `58c28f66e649ee605e5750091f13549ed6d48d369b8c4e66221b7d5e9c86023c`.
- [ ] Canonical schema SHA equals `4f4a540fdca498616f4b2dd9a2a05e943a16ce0624dd434113c2ff31abefcef0`.
- [ ] Engineering path count is 42.
- [ ] `assets/main.js` is excluded.
- [ ] Member SHA manifest passes.

## Architecture

- [ ] Articles 001–003 use `claims_state: none`.
- [ ] Projects 001–005 use `claims_state: legacy_embedded`.
- [ ] No active `legacy_date_pending`.
- [ ] Canonical sparse values contain no null, empty string, empty array or empty object.
- [ ] One canonical schema only.

## Workflow

- [ ] Only `.github/workflows/cms-content-integrity.yml` remains active after bootstrap.
- [ ] `.github/workflows/cms-phase3-build.yml` deletion is in the exact manifest.
- [ ] Both required job names are exact and stable.
- [ ] Promotion tools load from protected base.
- [ ] Bootstrap candidate tools require exact approved head SHA.
- [ ] Workflow permissions are `contents: read`.
- [ ] External Actions are pinned to immutable commit SHAs.
- [ ] Build and logs are outside the tracked source checkout.
- [ ] Source checkout remains clean after execution.

## Routine controls

- [ ] One path per commit.
- [ ] Existing content modification only.
- [ ] Raster media addition only.
- [ ] Wrong branch fails.
- [ ] Prohibited path fails.
- [ ] Media deletion fails.
- [ ] State-aware required payload removal passes.
- [ ] Same removal without valid transition fails.
- [ ] Protected identity, ID, slug and permalink fail on change.
- [ ] Published semantic changes require review reopen.
- [ ] Publication-date introduction is blocked in routine mode.

## Claims

- [ ] Material claim-bearing edit with `legacy_embedded` fails.
- [ ] Complete structured conversion passes.
- [ ] Missing claims payload fails.
- [ ] Missing review reset fails.
- [ ] Missing evidence or required boundary fails.
- [ ] Current project downgrade to `none` fails.

## Media and rendered output

- [ ] MIME/signature, extension, size and dimension controls pass.
- [ ] SVG upload and active SVG tests fail.
- [ ] Decorative alt output is correct.
- [ ] Meaningful alt is bilingual.
- [ ] Local links resolve.
- [ ] RTL/LTR and bilingual markers pass.
- [ ] No unresolved Liquid.
- [ ] No empty OG image metadata.

## Rollback

- [ ] Integrated rollback package manifest passes.
- [ ] Dry run restores baseline hashes.
- [ ] Platform additions and new workflow are deleted.
- [ ] Old workflow is restored from the recovery Git object.
- [ ] Rollback Jekyll evidence passes.
- [ ] Protected main remains unchanged.

## Manual controls

- [ ] Ruleset `AH Main Production Protection` is reviewed but not yet applied.
- [ ] Bypass list is empty.
- [ ] Pages CMS App has no bypass.
- [ ] Hosted saves remain closed pending separate authorization.

