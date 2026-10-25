# digest-dry-run

Fetch, rank, summarize, and print the digest without sending email or WhatsApp.

1. Follow `CLAUDE.md`.
2. Run `python -m app.main --dry-run`.
3. Confirm the printed email and WhatsApp bodies put the article URL immediately after each summary/blurb.
4. Do not persist items as sent in a way that blocks a later live send (dry-run already skips `record_sent`).
5. Summarize the printed digest for the user, including titles and links.
