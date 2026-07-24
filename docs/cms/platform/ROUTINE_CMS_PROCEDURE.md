# Routine Pages CMS Procedure — Phase 5E Cycle #002

## Status

Pages CMS remains closed until a separate reopening authorization.

When reopened, routine mode is limited to updating existing records and adding approved media on `cms-development-rc4.4`.

## Before save

1. Open the bookmarked URL containing `cms-development-rc4.4`.
2. Read the active branch label aloud.
3. Confirm the record ID and GitHub path.
4. Confirm no other save or GitHub edit is in progress.
5. Record the current branch head SHA.
6. Edit one record only.
7. Do not change IDs, slug, permalink, identity, navigation, schema version or layout fields.
8. Do not add a publication date.
9. Do not delete or replace media.
10. For a published record, first reopen it:
    - `status: under_review`
    - both review states `pending`
    - `review.timestamp_state: not_recorded`
    - omit `reviewed_by` and `reviewed_at`

## One-file rule

Each Pages CMS save commit must change exactly one approved path:

- one existing `_articles/*.md`; or
- one existing `_projects/*.md`; or
- one new raster file under `assets/uploads/articles/`; or
- one new raster file under `assets/uploads/projects/`.

Content creation, rename and deletion remain disabled.

## State-aware removal

Removal is permitted only when required by a valid transition.

Examples:

- `media_state: ready -> none/planned/not_assessed` requires removing `media` and reopening review.
- `claims_state: structured -> none/not_assessed` requires removing `claims`, reopening review and is prohibited for the five migrated governed projects.
- `review.timestamp_state: recorded/legacy_unrecorded -> not_recorded` permits removal of reviewer/timestamp only as part of a complete review reopen.
- Decorative conversion may remove stored alt only when `decorative` becomes `true` and review is reopened.

All other unexpected removals fail.

## Legacy embedded projects

Do not materially edit title, summary, status label, organization, period, built capability, context, method or evidence while retaining `claims_state: legacy_embedded`.

A material change requires a full structured-claim conversion and reopened review in the same content save.

## Media

Uploads must be:

- PNG, JPG, JPEG or WebP;
- at most 5 MiB;
- at most 4096 px in either dimension;
- lowercase kebab-case;
- valid signature matching extension.

SVG uploads, external URLs, data URIs, JavaScript URIs, traversal, deletion, rename and replacement are prohibited.

An uploaded file may be temporarily unreferenced on development while the next one-file content save references it. Promotion blocks orphan uploads.

## After save

1. Open the exact new GitHub commit.
2. Confirm one path changed.
3. Confirm branch is `cms-development-rc4.4`.
4. Review the semantic diff.
5. Wait for both stable checks.
6. Stop on any failure.
7. Revert the failed commit before another CMS save.
8. Record pre-save SHA, save SHA, path and check result.

## Promotion

Promotion is only through a reviewed PR from `cms-development-rc4.4` to `main`. Every commit in the range must independently satisfy routine mode. Added media must be referenced in the final head.

