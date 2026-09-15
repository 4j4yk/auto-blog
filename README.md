# Auto Blog

A small AI engineering blog. Three CrewAI roles work in sequence: **researcher → writer → editor**. A daily GitHub workflow saves an approved article and publishes a static website.

## Run locally

Requires Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --frozen
cp .env.example .env
# Add your Gemini API key to .env. Never commit it.
uv run python blog.py generate
uv run python blog.py build
uv run python -m http.server 8000 --directory _site
```

Open http://localhost:8000. Generation and publishing are separate commands: inspect or edit the JSON article in `posts/` before building if you want a review step locally. The daily workflow publishes automatically.

## Daily publishing

1. Push this project to a **public GitHub repository**, on `main`.
2. Add `GEMINI_API_KEY` in **Settings → Secrets and variables → Actions**.
3. Set **Settings → Pages → Source** to **GitHub Actions**.
4. Under **Actions → Publish blog**, select **Run workflow**.

The workflow runs at **13:17 UTC daily** (9:17 a.m. Detroit during daylight saving, 8:17 a.m. in winter). A push rebuilds existing posts without calling AI. A scheduled or manual run generates at most one new article per UTC date, commits it, then deploys Pages explicitly in the same run. GitHub schedules may be delayed; inactive public repositories can have schedules disabled after 60 days.

`BLOG_MODEL` is an optional Actions variable. Locally, `BLOG_MODEL` overrides `MODEL` in `.env`. The default is `gemini/gemini-3.5-flash-lite`. Confirm your selected model is available within your account's free quota. There is no automatic paid-model fallback. Provider quotas can interrupt generation; a failed run does not publish a new article. A free-tier architecture does not establish that an existing API account has billing disabled.

## Keep it yours

- `knowledge/user_preference.txt`: audience and writing preferences. Add your own notes; do not ask the model to invent experiences.
- `desk.json`: the three roles and their editorial responsibilities.
- `blog.json`: RSS feeds, allowed source hosts, and the freshness window. Starts with Hugging Face's blog feed; this is a source-linked digest, not a comprehensive news service.
- `posts/`: editable articles and their source URLs. The history is also the duplicate tracker.
- `blog.py`: source fetching, CrewAI handoffs, validation, and saving.
- `blog_site.py`: static HTML rendering. No database, frontend framework, or always-on server.

The researcher receives fetched article text. The writer drafts from it, and the editor checks the draft against that same source. Publication requires the editor's approval, valid fields, a bounded word count, and the exact retrieved source link. This catches structural errors; it cannot prove every sentence is correct. Published pages disclose AI assistance. No social media, email, or other external posting is configured.

If there is no fresh unused source, the workflow skips generation. If source retrieval, the model, or validation fails, it stops with a failed run. Review that run in Actions. No placeholder article is published.

## Checks

```sh
uv run python -m unittest discover -s tests -v
```

Tests cover freshness, duplicate prevention, rejection, source failures, safe rendering, and navigation on GitHub project Pages. The workflow runs them before generation or deployment.
