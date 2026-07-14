# Phase 3 — Controlled Manual Recovery Instructions

## Package Purpose

This package contains Phase 3 additions only. It does not contain replacements for existing RC4.4 pages, CSS, JavaScript, media, or `.nojekyll`.

## Target

- Repository: `ahassona4-ui/ahmed-hassouna-website`
- Branch only: `cms-development-rc4.4`
- Protected `main`: `3b6841377276fc82c80fee2c69015e73ae497532`

## Upload Procedure

1. Extract `AH_WEB_CMS_PHASE3_MANUAL_RECOVERY_PACKAGE.zip`.
2. Open the repository and confirm the branch selector visibly shows:
   `cms-development-rc4.4`
3. Confirm it does **not** show `main`.
4. Do not click **Compare & pull request**.
5. Select **Add file → Upload files**.
6. Upload all extracted files and folders while preserving their root paths.
7. Confirm the upload includes `_config.yml`, `Gemfile`, `_layouts`, `_includes`, `_data`, `dev-preview`, and the new `docs/cms` files.
8. Use this commit message:
   `feat(cms): add Phase 3 template migration preview`
9. Commit directly to `cms-development-rc4.4` only.

## Mandatory Pre-Commit Check

The changed-file list must not contain modifications or deletions to:

- `.nojekyll`
- `index.html`
- `articles/*.html`
- `projects/*.html`
- `assets/**`
- `.github/**`
- `.pages.yml`

No `_projects` or `_articles` directory may be created.

## Post-Upload Verification

1. Verify `main` still points to:
   `3b6841377276fc82c80fee2c69015e73ae497532`
2. Verify no Pull Request was opened.
3. Verify GitHub Pages settings were not changed.
4. Verify the Phase 3 commit contains only the 24 additions listed in `PHASE3_BEFORE_AFTER_TREE.md`.
5. Record the new development-branch commit SHA.
6. Run the local Jekyll build gate in an environment with RubyGems access:
   `bundle install`
   `bundle exec jekyll build --baseurl "" --destination _site_phase3`
7. Return the branch SHA, changed-file screenshot, and build log to AH Personal Website Operations.

## Rollback

If the manual upload is incorrect:

1. Do not merge.
2. Revert the single Phase 3 commit on `cms-development-rc4.4`.
3. Confirm the branch returns to its Phase 2R state.
4. Never reset, force-push, or modify `main`.
