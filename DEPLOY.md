# Deploying the CCQS web terminal

The `web/` directory is a build-less static terminal (vanilla JS + AG Grid +
lightweight-charts + ECharts, all from CDN). This document covers how it gets
hosted and auto-updated. It is **independent of the Streamlit app** — both read
the same data, so you can run them in parallel and cut over when ready.

## How it works (one picture)

```
4:00 PM ET (weekdays)
  pipeline.yml  ── refreshes data, runs hard-gate tests ──▶ commits
                   data/cache/dashboard/ to main   (UNCHANGED — Streamlit reads this)
                        │
                        │ "Daily CCQS Pipeline" run completes
                        ▼
  deploy-web.yml ── checks out main, runs web/export_data.py against the
                   committed slim cache, builds web/data/*.json ──▶ GitHub Pages
```

- `deploy-web.yml` **never re-runs the heavy pipeline** and **never writes to
  the repo.** It only reads the already-committed slim dashboard cache (the same
  files the Streamlit app ships with) and republishes the static site.
- It also redeploys whenever you push front-end changes under `web/**`, and you
  can trigger it by hand from the **Actions** tab ("Deploy Web Terminal" →
  *Run workflow*).
- `web/data/` (~18 MB/day, mostly per-ticker history) is **generated in CI**, never
  committed — so the repo stays slim.

## One-time setup: turn on GitHub Pages

The workflow tries to enable Pages automatically (`configure-pages` with
`enablement: true`). If the first run's **Configure Pages** step succeeds, you're
done. If it errors (some org policies / plans block self-enablement), enable it
once by hand:

1. Repo **Settings → Pages**.
2. **Build and deployment → Source:** select **GitHub Actions**.
3. Re-run the failed "Deploy Web Terminal" workflow (Actions tab).

> **Can't see Settings → Pages, or it's locked?** You don't have admin on the
> repo, or it's a **private repo on the GitHub Free plan** (Pages from private
> repos needs Pro/Team/Enterprise). Either ask the repo/org owner to flip the
> switch above, or use the **Cloudflare fallback** below — no repo admin needed.

Once enabled, the site is published at:

```
https://adfundmgmt.github.io/Composite-Chart-Quality-Score/
```

(The app uses relative asset/data paths, so it works correctly at this subpath.)

## Optional: custom domain

In **Settings → Pages → Custom domain**, set e.g. `ccqs.adfundmgmt.com`, then add
a `CNAME` DNS record pointing that host at `adfundmgmt.github.io`. GitHub
provisions HTTPS automatically.

## Fallback: Cloudflare Pages (no repo admin required)

If GitHub Pages isn't available to you, host on Cloudflare Pages — you connect it
with **your own** Cloudflare login (exactly like Streamlit Cloud is connected to
this repo), so it needs no repo-admin rights:

1. Cloudflare dash → **Workers & Pages → Create → Pages → Connect to Git** →
   pick this repo.
2. Build settings: **Framework preset:** None. **Build command:**
   `pip install -r requirements.txt && python web/export_data.py`.
   **Build output directory:** `web`.
3. Cloudflare rebuilds on every push to `main` — including the pipeline's daily
   `data/cache/dashboard/` commit — so the site stays fresh automatically.

(GitHub Pages is preferred because the deploy is in the same CI as the data and
never commits the 18 MB feed. Cloudflare is the zero-admin alternative.)

## Running locally

```
python -m http.server 8780 --directory web
# then open http://localhost:8780
```

`web/data/` must already exist locally (run `python web/export_data.py` from the
repo root once, with the cache present, to generate it).

## Migrating off Streamlit (when ready)

Nothing here removes Streamlit — they run side by side on the same daily data.
When you're confident in the web terminal:

1. Point users / links at the Pages (or Cloudflare) URL.
2. Optionally retire the Streamlit Cloud app and drop its deploy artifacts
   (`streamlit_app.py` entrypoint, `requirements.txt` Streamlit pin, the
   `.streamlit/` theme configs). Keep them until you've fully cut over.
