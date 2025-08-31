# Morning Brief (Automated, Free, GitHub Actions)

This repo generates a daily MP3 and an RSS feed, then publishes both via **GitHub Pages**.
Submit the RSS URL to Spotify as a *new podcast* (Spotify will auto‑ingest your feed).

**Stack**
- GitHub Actions (cron at 04:00 UTC)
- Python 3.11
- Content: basic headlines from public sources (can be upgraded later)
- TTS: Coqui XTTS (open‑source, en‑GB capable)
- Hosting: GitHub Pages (served from `/docs`)

**Outputs**
- `docs/episodes/YYYY-MM-DD-morning-brief.mp3`
- `docs/feed.xml` (podcast RSS)
- `https://<your-username>.github.io/<repo>/feed.xml`

**One-time setup**
1. Create a new repo from this template.
2. Enable **Pages**: Settings → Pages → Branch: `main` → Folder: `/docs` → Save.
3. Add the repository secret `GH_PAGES_URL` with your final Pages base URL (e.g. `https://username.github.io/morning-brief`).
4. Push to `main`. The workflow will run at 04:00 UTC and also on each push.
5. Submit the RSS URL (`<GH_PAGES_URL>/feed.xml`) to Spotify as a *new* show.
