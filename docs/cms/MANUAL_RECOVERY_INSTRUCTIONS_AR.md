# Phase 2 — Controlled Manual Recovery Instructions

## Why manual recovery is required

The connected GitHub integration can read `ahassona4-ui/ahmed-hassouna-website` but returned:

```text
403 — Resource not accessible by integration
```

for both file creation and Git blob creation. No repository write succeeded.

## Target

- Repository: `ahassona4-ui/ahmed-hassouna-website`
- Branch: `cms-development-rc4.4`
- Expected branch parent before upload: `558932e7eee1b55309a13e15a3bef11517850709`
- Protected main: `3b6841377276fc82c80fee2c69015e73ae497532`

## Upload Procedure

1. Download and extract the delivery ZIP locally.
2. Open the repository on GitHub.
3. Confirm the branch selector shows **`cms-development-rc4.4`**, not `main`.
4. Do **not** click **Compare & pull request**.
5. Choose **Add file → Upload files**.
6. Drag the extracted `docs` folder so the final repository paths begin with:
   - `docs/cms/README.md`
   - `docs/cms/CONTENT_MODEL_SPECIFICATION.md`
   - `docs/cms/schemas/content-model.schema.json`
   - `docs/cms/MIGRATION_MAP.md`
   - `docs/cms/samples/non-runtime-samples.yml`
   - `docs/cms/PHASE2_REPORT.md`
   - `docs/cms/PHASE2_EVIDENCE_MANIFEST.json`
7. Use commit message:
   `docs(cms): add Phase 2 content model specification`
8. Commit directly to **`cms-development-rc4.4`** only.

## Verification

After upload:

- `main` remains `3b6841377276fc82c80fee2c69015e73ae497532`.
- Branch diff contains the Phase 1 manifest changes plus `docs/cms/**` only.
- No HTML, CSS, JavaScript, images, `.nojekyll`, Pages settings, workflow, `_config.yml`, `_layouts`, `_includes`, collection, or `.pages.yml` changes exist.
- No Pull Request is opened.
- Record the new branch commit SHA.
- Return the verification screenshot and SHA to AH Personal Website Operations.

## Rollback

If an incorrect commit is made on the development branch:

1. Do not merge.
2. Revert only the incorrect Phase 2 documentation commit, or reset the branch to `558932e7eee1b55309a13e15a3bef11517850709` using an approved controlled procedure.
3. Never force-update `main`.
