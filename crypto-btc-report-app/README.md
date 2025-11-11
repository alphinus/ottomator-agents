# Crypto BTC Daily Report App

A FastAPI + OpenAI powered web app that turns the original AI News Assistant concept into a daily, crypto-focused intelligence brief. Every day at 08:00 local time the app collects Bitcoin headlines from **free RSS feeds** (no paid API keys), pulls the last 24h BTC price action, generates a one-page (A4 length) analyst report, and publishes it as both JSON and HTML. A GitHub Actions workflow commits the fresh report and deploys it to GitHub Pages automatically.

## Key Features
- **Focused data pipeline** – CoinDesk / CoinTelegraph / Decrypt RSS (editable) for BTC/crypto headlines, Bitstamp ticker for price stats. Everything except the LLM is 100% free.
- **LLM-written brief** – OpenAI (or a built-in offline fallback if no key is configured) distills data into a ~450-word report with inline references.
- **Web + API** – FastAPI serves `/` (HTML report) and `/api/report` (machine-readable JSON).
- **Daily automation** – APScheduler for local cron-like execution plus a provided GitHub Actions workflow that runs every day at 06:00 UTC (≈08:00 Berlin).
- **Auto deploy** – Workflow pushes updated artifacts to the repo and publishes `public/index.html` to GitHub Pages.

## Project Structure
```
crypto-btc-report-app/
├── requirements.txt
├── .env.example
├── data/
│   └── latest_report.json          # populated by generator
├── public/
│   └── index.html                  # rendered report for deployment
├── templates/
│   └── report.html                 # Jinja2 template for HTML output
└── src/crypto_btc_report/
    ├── builder.py                  # Orchestrates fetch → summarize → persist
    ├── config.py                   # Pydantic settings + payload model
    ├── generate.py                 # CLI entrypoint
    ├── news.py                     # Free RSS aggregator for crypto headlines
    ├── price.py                    # Bitstamp ticker client
    ├── scheduler.py                # APScheduler cron helper
    ├── summarizer.py               # OpenAI wrapper
    └── web.py                      # FastAPI app
```

A companion workflow lives in `.github/workflows/daily-crypto-report.yml`.

## Prerequisites
- Python 3.9+ (3.11 recommended)
- OpenAI API key (only paid credential required; if omitted the app auto-generates a lightweight offline summary)

## Local Setup
1. Install deps:
   ```bash
   cd ottomator-agents/crypto-btc-report-app
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```
2. Configure environment:
   ```bash
   cp .env.example .env
   # fill in OPENAI_API_KEY (RSS feeds already configured by default)
   ```
3. Generate a report on demand:
   ```bash
   python -m crypto_btc_report.generate
   ```
   Outputs live under `data/latest_report.json` and `public/index.html`.
4. Serve the web app:
   ```bash
   uvicorn crypto_btc_report.web:app --reload --port 8000
   ```
5. Optional local cron replacement:
   ```bash
   python -m crypto_btc_report.scheduler
   ```
   Scheduler uses `REPORT_TIMEZONE` + `REPORT_HOUR` (defaults: Europe/Berlin @ 08:00).

## API Surface
- `GET /` – renders the latest HTML report.
- `GET /api/report` – returns the JSON payload (`ReportPayload` model).

## GitHub Automation & Deployment
1. Expose the necessary secrets in your repository settings:
   - `OPENAI_API_KEY`
2. Enable GitHub Pages → “GitHub Actions” as the source.
3. Keep the provided workflow (`.github/workflows/daily-crypto-report.yml`). It:
   - Runs daily at `0 6 * * *` (06:00 UTC ≈ 08:00 Berlin; adjust cron + `REPORT_TIMEZONE` as needed).
   - Installs dependencies, generates the report, commits changes back to the default branch, and uploads `public/` as a Pages artifact.
   - Deploys `public/index.html` to GitHub Pages so the latest report is reachable via https://{username}.github.io/{repo}/.
   - Works without any paid news/data APIs, making it ideal for quick prototyping.

## Customization Ideas
- Expand to multi-coin coverage by adjusting `COIN_SYMBOL` and `articles_per_report` in `.env`.
- Swap OpenAI for alternative LLM providers by modifying `summarizer.py`.
- Integrate Slack/Telegram delivery via additional workflow steps after report generation.

## Troubleshooting
- **No headlines found** – RSS feeds might be empty or rate-limited. Override `RSS_FEEDS` in `.env` with other free feeds (any standard RSS/Atom Crypto source works).
- **OpenAI errors** – double-check the key, model availability, and org quotas. The app fails fast so the workflow logs show the exception.
- **Pages not updating** – confirm Pages is set to “GitHub Actions” and the workflow has `pages: write` permission.

## License & Attribution
Built atop the AI News Assistant concept from the Live Agent Studio repo. Data sources remain subject to their own terms (RSS publishers, Bitstamp, OpenAI).
