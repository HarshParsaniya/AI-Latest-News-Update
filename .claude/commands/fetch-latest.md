# fetch-latest

Run the AI news digest LangGraph in this repo (`python -m app.main`).

1. Read `CLAUDE.md` and `.env.example`. Do not print secrets from `.env`.
2. If `.venv` or dependencies are missing, create/install from `requirements.txt`.
3. If SMTP or LLM keys are missing, run a dry-run instead: `python -m app.main --dry-run`.
4. If `.env` has SMTP configured and the user wants a live send, run `python -m app.main`.
5. WhatsApp is optional. A CallMeBot failure must not be treated as a failed digest if email succeeded.
6. After the run, report item count, email status, WhatsApp status, and whether each summary is followed by its article URL.
7. Point at Langfuse if keys are configured.

Do not change RSS sources or delivery order unless the user asked.
