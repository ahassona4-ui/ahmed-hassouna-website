# Bootstrap / Migration Procedure — Phase 5E Cycle #002

## Scope

Bootstrap is a one-time coordinated registration of the exact Engineering Candidate #003 files plus the final Platform files and deletion of the superseded workflow.

It is not routine CMS operation.

## Preconditions

1. Development branch target is `cms-development-rc4.4`.
2. Exact source recovery baseline is:
   `262825767ee08e91e5410957686664f3ca6dde05`
3. Protected `main` remains:
   `3b6841377276fc82c80fee2c69015e73ae497532`
4. Canonical schema SHA is:
   `4f4a540fdca498616f4b2dd9a2a05e943a16ce0624dd434113c2ff31abefcef0`
5. Integrated operation manifest has been independently reviewed.
6. `assets/main.js` is absent from the operation set.

## Controlled sequence

1. Create one non-merge migration commit from the exact recovery baseline.
2. Apply exactly the 42 Engineering operations byte-for-byte.
3. Add exactly the final Platform files listed in the integrated manifest.
4. Delete only `.github/workflows/cms-phase3-build.yml`.
5. Do not delete, rename or modify media.
6. Record the resulting commit SHA.
7. Set repository variables temporarily:
   - `CMS_BOOTSTRAP_ENABLED = true`
   - `CMS_BOOTSTRAP_APPROVED_HEAD_SHA = <exact migration commit SHA>`
8. Run the single authoritative workflow.
9. Confirm both stable jobs pass.
10. Disable bootstrap immediately:
    - `CMS_BOOTSTRAP_ENABLED = false`
    - clear `CMS_BOOTSTRAP_APPROVED_HEAD_SHA`
11. Preserve workflow artifacts, commit SHA and operation-manifest verification output.

## Failure rule

Any path, status, hash, schema byte or commit topology difference is a stop condition. Do not repair the migration by ad hoc follow-up commits. Revert to the recovery baseline and regenerate the controlled package.

## Bootstrap stop point

Bootstrap preparation does not authorize upload, GitHub write, pull request, merge, Ruleset change, promotion, Pages CMS save or Phase 6.

