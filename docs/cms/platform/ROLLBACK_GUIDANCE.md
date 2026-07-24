# Integrated Rollback Guidance — Phase 5E Cycle #002

## Preferred recovery

Revert the single integrated bootstrap commit. A Git revert restores the exact parent tree atomically, including `.github/workflows/cms-phase3-build.yml`, and removes the new workflow and Platform additions.

Do not force-reset protected `main`.

## Packaged fallback

The external integrated rollback package contains:

- the exact Engineering Candidate #003 rollback package;
- a Platform rollback configuration;
- a rollback script;
- hashes and instructions.

The script:

1. verifies the expected integrated paths;
2. restores Engineering baseline files from the embedded Engineering rollback package;
3. deletes all Engineering v2-only and Platform-added files;
4. removes `.github/workflows/cms-content-integrity.yml`;
5. restores `.github/workflows/cms-phase3-build.yml` from the configured recovery Git object;
6. checks baseline hashes;
7. confirms protected-main evidence supplied by the operator is unchanged.

## Workflow restoration

The old workflow is restored from:

`262825767ee08e91e5410957686664f3ca6dde05:.github/workflows/cms-phase3-build.yml`

This avoids reconstructing or normalizing its bytes.

## Verification after rollback

Required:

- all Engineering baseline hashes match;
- every v2-only and Platform file is absent;
- new workflow is absent;
- old workflow exists and matches the recovery Git object;
- no media path changed;
- Jekyll rollback build passes;
- protected `main` remains unchanged.

Engineering Candidate #003 already supplies a successful rollback Jekyll build log. The integrated dry run additionally proves Platform deletion and workflow restoration mechanics.

## Failure

If any hash or deletion check fails, stop. Do not continue with partial recovery or manually edit the restored files.

