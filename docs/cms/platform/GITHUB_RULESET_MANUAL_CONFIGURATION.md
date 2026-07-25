# Manual GitHub Ruleset Configuration

Do not apply these settings without a separate authorization.

## Ruleset

Name:

`AH Main Production Protection`

Enforcement:

`Active`

Target:

- Branch name pattern exactly `main`

## Required rules

Enable:

1. Restrict deletions.
2. Block force pushes.
3. Require a pull request before merging.
4. Require branches to be up to date before merging.
5. Require conversation resolution before merging.
6. Require status checks to pass.
7. Require the following exact check names:
   - `Validate CMS content and repository policy`
   - `Build and validate rendered output`

Recommended:

- Require at least one approval.
- Dismiss stale approvals when new commits are pushed.
- Require linear history.
- Apply rules to administrators where the account UI supports it.

## Bypass

Bypass list must be empty.

Do not add:

- Pages CMS GitHub App;
- repository owner;
- administrators;
- Actions;
- any integration.

The Pages CMS App must have no Ruleset or branch-protection bypass.

## Production source

Confirm GitHub Pages production source does not point to `cms-development-rc4.4`.

## Bootstrap variables

Only during the separately authorized bootstrap:

- `CMS_BOOTSTRAP_ENABLED = true`
- `CMS_BOOTSTRAP_APPROVED_HEAD_SHA = <exact approved bootstrap commit SHA>`

After the bootstrap checks pass:

- set `CMS_BOOTSTRAP_ENABLED = false`;
- clear `CMS_BOOTSTRAP_APPROVED_HEAD_SHA`.

## Manual acceptance evidence

Capture:

- Ruleset name and target;
- required check names;
- empty bypass list;
- force-push and deletion blocking;
- PR/update/conversation requirements;
- Pages CMS App absent from bypass;
- production source branch.

