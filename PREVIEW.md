# Preview Deployment System

This repo uses a "train track switcher" to deploy any branch to the preview site.

## How It Works

```
[source branch] --sync--> [preview branch] --deploy--> omarmy-preview (GitHub Pages)
```

1. **Config file** (`.github/preview-config.json`) on `main` specifies which branch is the preview source
2. **Sync workflow** (`sync-to-preview.yml`) copies the source branch to the `preview` branch
3. **Deploy workflow** (`deploy-preview.yml` on the `preview` branch) builds and deploys to GitHub Pages

## Switching Which Branch Is Previewed

Edit `.github/preview-config.json` on `main`:

```json
{
  "source_branch": "your-branch-name"
}
```

Commit and push to `main`. The sync workflow will automatically push the new source branch to `preview`, triggering a deploy.

## How Syncing Works

The sync workflow runs in three cases:

| Trigger | When |
|---------|------|
| **Config change** | You push a change to `.github/preview-config.json` on `main` |
| **Scheduled** | Every 15 minutes (picks up new commits on the source branch) |
| **Manual** | Go to Actions → "Sync Source Branch to Preview" → Run workflow |

The workflow compares the source branch HEAD with the preview branch HEAD. If they differ, it force-pushes the source to preview.

## Preview URL

The preview site is deployed to: **https://lsk567.github.io/omarmy-preview/**

## Quick Reference

| Task | How |
|------|-----|
| See current preview source | Check `.github/preview-config.json` on `main` |
| Switch preview to a different branch | Edit the config, push to `main` |
| Force an immediate sync | Go to Actions → "Sync Source Branch to Preview" → Run workflow |
| Check deploy status | Go to Actions → "Deploy Preview to GitHub Pages" |

## Notes

- The `preview` branch is managed by the sync workflow — don't push to it directly
- The source branch must exist on the remote (`origin`) for syncing to work
- Switching the config triggers an immediate sync; otherwise, new commits on the source branch are picked up within 15 minutes (or trigger a manual sync for instant updates)
