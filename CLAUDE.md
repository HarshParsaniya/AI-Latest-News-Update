# AI Latest News

Python LangGraph job that fetches free AI RSS feeds, summarizes about 10 latest items, traces the run in Langfuse, and sends a digest by Gmail SMTP plus optional CallMeBot WhatsApp.

Item count is flexible: target 10, send fewer or slightly more if that is what qualifies. Every item is **summary first, then the article URL**.

## LangGraph sequence

`fetch_sources` → `normalize_and_dedup` → `select_latest` → `summarize_items` → `compose_digest` → `send_email` → `send_whatsapp` → `persist_sent`

- One RSS source failing does not fail the run.
- Already-sent URLs live in SQLite (`SQLITE_PATH`, default `./data/digest.db`).
- WhatsApp is optional. If CallMeBot is off or returns an error, email still sends.
- Dry-run prints bodies and does not mark URLs as sent.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main --dry-run
python -m app.main
```

Docker:

```bash
docker compose run --rm digest
```

Production trigger is the Kubernetes CronJob in `k8s/cronjob.yaml` (08:00 Asia/Kolkata). Agent-driven runs use `.claude/commands/`.

## Environment

Copy `.env.example`. Never commit `.env` or `k8s/secret.yaml`.

Required for a live email send: `SMTP_USER`, `SMTP_APP_PASSWORD`, `DIGEST_TO_EMAIL` (Gmail App Password).

Optional: `GEMINI_API_KEY` or `GROQ_API_KEY` (snippet fallback if missing), Langfuse keys, `WHATSAPP_ENABLED` + CallMeBot phone/API key.

## Delivery rules

- Email subject: `AI Daily Digest — {date} ({n} updates)`
- Email item order: title, source, time, summary, then link
- WhatsApp item order: `N. Title — blurb` then URL on the next line, then `Full digest is in email.`
- If WhatsApp is too long, include fewer items; never drop the URL of an included item

## Layout

- `app/` pipeline code (`graph.py`, `nodes/`, `sources.py`, `store.py`)
- `templates/digest.html` email template
- `k8s/` CronJob, PVC, ConfigMap, Secret example
- `.claude/commands/fetch-latest.md` live or env-gated run
- `.claude/commands/digest-dry-run.md` fetch + print without sending

Langfuse traces appear at `LANGFUSE_HOST` (default https://cloud.langfuse.com) when public/secret keys are set.
