# Phase 3 — Local Build Evidence

## Intended Build Stack

The prepared `Gemfile` targets:

- `github-pages ~> 232`
- `webrick ~> 1.8`

The `_config.yml` uses no collections, custom plugins, Pages CMS configuration, or GitHub Actions.

## Commands Attempted

```bash
bundle install
bundle exec jekyll build --baseurl "" --destination _site_phase3
```

Because the Bundler executable was not placed on PATH, the packaged Bundler executable was invoked directly for the controlled attempt.

## Dependency Installation Result

```text
Don't run Bundler as root. Installing your bundle as root will break this
application for all non-root users on this machine.
Could not reach host index.rubygems.org. Check your network connection and try
again.
```

## Jekyll Build Result

```text
bundler: command not found: jekyll
Install missing gem executables with `bundle install`
```

## Formal Build Result

**Local Jekyll build = Not Executed Successfully**

Root cause: the isolated execution environment could not reach `index.rubygems.org`, and Jekyll was not preinstalled. Consequently, no `_site_phase3` build output was produced.

This is an environment dependency-access blocker, not a successful build and not evidence that the templates have passed Jekyll execution.

## Static Verification Completed

Independent source and scope verification completed successfully:

| Check group | Result |
|---|---|
| Required Phase 3 files | Pass |
| YAML parsing | Pass |
| Preview front matter parsing | Pass |
| Circular AH-PRJ-001 navigation | Pass |
| Legacy article date control | Pass |
| Canonical identity | Pass |
| Liquid block/include reference balance | Pass |
| HTML skeleton parsing | Pass |
| Local asset and navigation references | Pass |
| RC4.4 runtime file hashes unchanged | Pass |
| Prohibited paths absent | Pass |
| `.nojekyll` preserved | Pass |
| Existing `assets/main.js` syntax | Pass |
| Content Model Addendum corrections | Pass |
| `_config.yml` scope control | Pass |

**Static verification total: 38 passed, 0 failed, 0 warnings.**

## Required Build-Gate Recovery

Before Phase 3 can be approved as passed, run from the repository root in an environment with Ruby and RubyGems access:

```bash
bundle install
bundle exec jekyll build --baseurl "" --destination _site_phase3
```

Then verify that these files exist:

```text
_site_phase3/dev-preview/project-ah-prj-001.html
_site_phase3/dev-preview/article-ah-art-001.html
```

The resulting pages must be tested in Arabic/English, RTL/LTR, desktop/mobile, and for local links and images.
