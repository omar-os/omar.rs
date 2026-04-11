# Preview Deployment System

This repo can deploy any branch of `omarmy.ai` to a preview site on GitHub Pages.

## How It Works

```
[source branch] --build & deploy--> omarmy-preview/gh-pages --> GitHub Pages
```

One workflow (`.github/workflows/deploy-preview.yml`) in `omarmy.ai`:

1. Reads the source branch from `.github/preview-config.json` on `main`
2. Checks out that branch
3. Skips if `omarmy-preview/gh-pages` HEAD already references the source SHA
4. Builds with `astro build --base /omarmy-preview/`
5. Force-pushes `dist/` to the `gh-pages` branch of `lsk567/omarmy-preview`

GitHub Pages on `omarmy-preview` serves that branch.

## Switching Which Branch Is Previewed

### Option 1: Persistent — edit the config file

Edit `.github/preview-config.json` on `main`:

```json
{ "source_branch": "your-branch-name" }
```

Commit and push to `main`. The workflow fires on config-file changes and also every 15 minutes.

### Option 2: Ad-hoc — workflow dispatch

One-off preview of any branch without touching the config:

```bash
gh workflow run deploy-preview.yml -f branch=feat/my-experiment
```

Or via the UI: Actions → "Deploy Preview" → Run workflow → enter branch name.

Note: this does not change the configured source branch. The next scheduled run reverts to whatever is in `preview-config.json`.

## Triggers

| Trigger | When |
|---------|------|
| **Scheduled** | Every 15 minutes (picks up new commits on the source branch) |
| **Config change** | Push to `.github/preview-config.json` or the workflow file on `main` |
| **Manual** | Actions → "Deploy Preview" → Run workflow (optional branch override) |

Each run skips the build+push if `omarmy-preview/gh-pages` already carries the current source SHA, so idle ticks are cheap (one API call).

## Preview URL

**https://lsk567.github.io/omarmy-preview/**

## Secrets

`PREVIEW_DEPLOY_TOKEN` — a PAT with `contents:write` on `lsk567/omarmy-preview`. Rotate in repo settings when it expires. Symptoms of an expired token: workflow fails with `Invalid username or token. Password authentication is not supported for Git operations.`

## Notes

- The source branch must exist on `origin` for checkout to succeed.
- The old `preview` branch on this repo (from the previous two-workflow setup) is no longer used and can be deleted.
