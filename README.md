# AI Latest News

A Python-based daily AI news digest. The job reads public RSS feeds, filters out previously sent and duplicate articles, summarizes the newest items, and delivers the digest by email. WhatsApp delivery and Langfuse tracing are optional.

The workflow is built with LangGraph. It targets 10 articles by default; the actual count can be lower or higher depending on available qualifying news. Each included article has a summary followed by its URL.

## Features

- Fetches AI news from multiple public RSS feeds in parallel.
- Continues when an individual feed fails.
- Normalizes article URLs and removes tracking parameters.
- Skips URLs already sent in a previous successful email.
- Removes near-duplicate headlines and selects the newest articles.
- Summarizes articles with Google Gemini or Groq when configured.
- Falls back to RSS snippets if no LLM key is configured or summarization fails.
- Sends a plain-text and HTML email through SMTP.
- Optionally sends a shorter digest through CallMeBot WhatsApp.
- Stores sent URLs and run history in SQLite.
- Supports dry runs that print the message bodies without sending or marking articles as sent.
- Optionally traces LangGraph runs with Langfuse.

## Workflow

Each run follows this LangGraph sequence:

```text
fetch_sources
  -> normalize_and_dedup
  -> select_latest
  -> summarize_items
  -> compose_digest
  -> send_email
  -> send_whatsapp
  -> persist_sent
```

1. **Fetch:** Reads the configured RSS feeds concurrently, up to 40 entries per feed.
2. **Normalize and deduplicate:** Canonicalizes URLs, removes tracking parameters, ignores previously sent URLs, and collapses identical URLs.
3. **Select:** Sorts candidates newest-first and skips near-duplicate titles.
4. **Summarize:** Uses Gemini or Groq when configured. Otherwise, uses the RSS snippet. If an LLM call fails, the run falls back to snippets.
5. **Compose:** Builds the email subject, HTML and plain-text email bodies, and WhatsApp message.
6. **Deliver:** Sends email first. WhatsApp is optional; a WhatsApp failure does not undo a successful email.
7. **Persist:** Records URLs as sent only after the email reports success. Run statuses are stored in SQLite.

The digest date uses `DIGEST_TZ`, which defaults to `Asia/Kolkata`. The default target count is 10 and can be configured from 1 to 30.

## RSS sources

The built-in feeds are defined in `app/sources.py`:

- Google News AI
- TechCrunch AI
- The Verge AI
- OpenAI News
- Hugging Face Blog
- Google DeepMind
- MIT Technology Review
- VentureBeat AI
- arXiv cs.AI

A feed error is logged and recorded in the run’s error list; other feeds continue to be processed.

## Requirements

- Python 3.12 recommended. The Docker image uses Python 3.12.
- Internet access to retrieve RSS feeds and, when enabled, call the LLM and delivery services.
- SMTP credentials for live email delivery.
- An API key for Gemini or Groq if you want LLM-generated summaries. This is optional; RSS snippets are used without a key.
- CallMeBot credentials only if WhatsApp delivery is enabled.
- Langfuse keys only if tracing is desired.

## Local setup

From the project directory, create and activate a virtual environment, install dependencies, and copy the example environment file:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with the credentials and settings you want to use. Do not commit `.env`.

Run a dry run first:

```powershell
python -m app.main --dry-run
```

A dry run fetches and processes news, then prints the email subject, email text, and WhatsApp message. It does not send either message or mark article URLs as sent. Run the job normally to deliver the digest:

```powershell
python -m app.main
```

The command prints a JSON status summary including the item count, delivery statuses, overall result, and any errors. It exits with a non-zero status if the digest run is not successful.

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Configuration

The application reads settings from environment variables and `.env`. Unknown environment variables are ignored.

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | Empty | Gemini API key. Preferred LLM provider when both provider keys are set. |
| `GROQ_API_KEY` | Empty | Groq API key, used if a Gemini key is not set. |
| `MODEL_NAME` | `gemini-2.0-flash` | Model name. For Groq, set a Groq-supported model name; a Gemini-prefixed default is mapped to `llama-3.3-70b-versatile`. |
| `LANGFUSE_PUBLIC_KEY` | Empty | Langfuse public key. |
| `LANGFUSE_SECRET_KEY` | Empty | Langfuse secret key. |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse host. |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server hostname. |
| `SMTP_PORT` | `587` | SMTP server port; the client uses STARTTLS. |
| `SMTP_USER` | Empty | SMTP login and default sender address. |
| `SMTP_APP_PASSWORD` | Empty | SMTP password. For Gmail, use an App Password. |
| `DIGEST_FROM_EMAIL` | Empty | Optional sender address; defaults to `SMTP_USER`. |
| `DIGEST_TO_EMAIL` | Empty | Required for live email. Supports comma-separated recipients. |
| `WHATSAPP_ENABLED` | `false` | Enables CallMeBot delivery when required credentials are present. |
| `CALLMEBOT_PHONE` | Empty | CallMeBot phone value. |
| `CALLMEBOT_APIKEY` | Empty | CallMeBot API key. |
| `CALLMEBOT_MAX_CHARS` | `1500` | Maximum WhatsApp message length. The digest includes fewer items if needed. |
| `DIGEST_TZ` | `Asia/Kolkata` | Time zone used for the digest date. |
| `TARGET_ITEM_COUNT` | `10` | Desired number of articles, from 1 to 30. |
| `SQLITE_PATH` | `./data/digest.db` | Path to the SQLite database. |
| `DRY_RUN` | `false` | Runs without sending messages or marking URLs as sent. |
| `EXTRACT_ARTICLE_TEXT` | `false` | Attempts to extract article text for summaries instead of relying only on feed snippets. |

Live email requires `SMTP_USER`, `SMTP_APP_PASSWORD`, and at least one address in `DIGEST_TO_EMAIL`. WhatsApp and Langfuse are optional. Keep credentials in `.env` locally or in a secrets manager in production.

## Delivery format

The email subject is:

```text
AI Daily Digest — {date} ({n} updates)
```

Each email item contains its title, source, published time, summary, and article URL. The HTML email is rendered from `templates/digest.html`.

Each WhatsApp item contains a numbered title and short blurb, followed by the article URL on the next line. The message ends with `Full digest is in email.` If the message reaches the configured character limit, fewer items are included; URLs for included items are retained.

## Run with Docker Compose

Build and run the digest using Docker Compose:

```bash
docker compose run --rm digest
```

Run a dry run:

```bash
docker compose run --rm digest python -m app.main --dry-run
```

Compose loads environment variables from `.env` and mounts a named volume for the SQLite database at `/data/digest.db`.

## Kubernetes

The `k8s/` directory includes:

- `cronjob.yaml`: runs the digest daily at 08:00 in `Asia/Kolkata`.
- `configmap.yaml`: non-secret runtime configuration.
- `pvc.yaml`: persistent storage for the SQLite database.
- `secret.yaml.example`: example secret manifest. Supply real credentials through a Kubernetes Secret; do not commit secrets.

Build and publish the container image for your cluster, then update the image reference in `k8s/cronjob.yaml` if necessary. Create the secret from a protected environment file, then apply the manifests:

```bash
kubectl create secret generic ai-news-digest-secrets --from-env-file=.env
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/cronjob.yaml
```

The CronJob uses `concurrencyPolicy: Forbid`, retains a limited history of successful and failed jobs, and stores the SQLite database on the PVC. Ensure the cluster has access to the image and that the configured storage class supports the PVC.

## Agent commands

The `.claude/commands/` directory contains repository-specific commands:

- `digest-dry-run`: fetches and prints the digest without sending it.
- `fetch-latest`: runs the digest, using a dry run if live-send credentials are missing.

These commands follow the project guidance in `CLAUDE.md`.

## Tests

Run the test suite with:

```bash
pytest
```

Tests are in `tests/` and cover graph compilation, feed fetching, URL canonicalization, selection and deduplication, digest composition, and delivery behavior.

## Project structure

```text
app/
  graph.py          LangGraph workflow definition
  llm.py            Gemini, Groq, and Langfuse setup
  main.py           Command-line entry point
  settings.py       Environment and .env configuration
  sources.py        Built-in RSS feed list
  state.py          Workflow state and article types
  store.py          SQLite schema and persistence helpers
  urls.py           URL canonicalization and tracking cleanup
  nodes/
    fetch.py        RSS retrieval and parsing
    select.py       Deduplication and newest-item selection
    summarize.py   LLM summarization and snippet fallback
    compose.py      Email and WhatsApp body composition
    deliver.py      SMTP and CallMeBot delivery
    persist.py      Delivery result and sent-item persistence
templates/
  digest.html       HTML email template
tests/              Automated tests
k8s/                Kubernetes CronJob, ConfigMap, PVC, and Secret example
.claude/commands/   Agent-driven run and dry-run instructions
Dockerfile          Container image definition
docker-compose.yml  Local container configuration
requirements.txt    Python dependencies
CLAUDE.md           Additional project instructions
```

## Data and privacy

SQLite stores sent article URLs and titles, along with run timestamps and delivery statuses. By default, the database is `./data/digest.db`; Docker and Kubernetes configure it under `/data`.

Article content is sent to the configured LLM provider when an API key is enabled. Enable `EXTRACT_ARTICLE_TEXT` only if you want the application to attempt retrieving article text from publishers. Review the policies of the RSS sources, LLM provider, SMTP provider, CallMeBot, and Langfuse before using them.

Never commit `.env`, `k8s/secret.yaml`, or any file containing live credentials.