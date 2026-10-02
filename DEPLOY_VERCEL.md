# Deploying to Vercel

The repo is configured for it: [`api/index.py`](api/index.py) exposes the Flask
app, [`vercel.json`](vercel.json) serves `static/` as real static files and
sends everything else to the function, and `.vercelignore` keeps the virtualenv,
`instance/` and local documents out of the bundle.

## 1. Before you start — two things to decide

**Plan.** Vercel's Hobby (free) plan is for non-commercial use. A client's
marketing site that collects leads is commercial, so the free tier is fine for a
demo or staging URL, but production belongs on Pro.

**E-mail.** Outbound SMTP from serverless functions is unreliable and is blocked
on some networks. If briefs stop arriving after deploying, that is the cause:
switch `services/mailer.py` to an HTTP mail API (Resend, SendGrid, Postmark) and
keep everything else as it is. The local archive fallback means nothing is lost
in the meantime.

## 2. Environment variables

Add these in **Project → Settings → Environment Variables** (nothing is read
from `.env`; that file is not deployed):

| Variable | Notes |
|---|---|
| `FLASK_SECRET_KEY` | Required. A fixed random string — admin sessions break if it changes. |
| `FLASK_DEBUG` | Leave unset (off). |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | The chat assistant (Ask Caraïbes + Project Assistant), via OpenRouter. Never point `OPENROUTER_MODEL` at a `:batch` model id. |
| `ANTHROPIC_API_KEY` | Optional fallback answers if OpenRouter is unset. |
| `MAIL_*`, `INQUIRY_RECIPIENT` | See `.env.example`. |
| `SELLSY_*` | Pipeline, step, source ids. |
| `DATABASE_URL` | The Supabase **transaction pooler** URI (port 6543) — see below. Leave `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD` unset here. |
| `SUPABASE_S3_*`, `SUPABASE_BUCKET` | RFP document storage. Required in production: `/tmp` does not survive. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Blank disables the admin sign-in. |
| `SERVERLESS` | Not needed — Vercel sets `VERCEL=1`, which the app already detects. |

## 2b. The database URL

Supabase dashboard → **Connect** → *Direct connection string* → **Transaction
pooler** → Type **URI**, then copy the string. It has this shape:

```
postgresql://postgres.<project-ref>:<password>@aws-1-<region>.pooler.supabase.com:6543/postgres
```

- The username is `postgres.<project-ref>`, not plain `postgres`.
- Replace `[YOUR-PASSWORD]` with the real database password, URL-encoded
  (`@` → `%40`, `#` → `%23`, `/` → `%2F`).
- Keep port **6543**. Port 5432 on the same host is the session pooler; the
  direct `db.<ref>.supabase.co` host is IPv6-only and Vercel cannot reach it.

Nothing in the code needs changing: psycopg2 uses the simple query protocol and
no session state, which is all the transaction pooler asks. The connection pool
is already sized down to two slots per instance when running serverless
(`services/store.py`).

## 3. Deploy

```bash
npm i -g vercel
vercel          # preview
vercel --prod   # production
```

## 4. What the serverless switch changes

A Vercel function is frozen the moment it returns a response, and its filesystem
is read-only. [`services/runtime.py`](services/runtime.py) detects that and the
app adapts:

- **Instance folder** → `/tmp/instance`. The local fallbacks (`submissions.jsonl`,
  `rfps/`, `whatsapp_outbox.jsonl`) still work but are **ephemeral** — treat the
  database, e-mail and Sellsy as the real record.
- **Sellsy push** runs inline instead of on a thread, so a brief submission waits
  for it (a few seconds) rather than losing it.
- **Visitor tracking** writes inline for the same reason. Every tracked page view
  costs one database round trip (~400 ms). If that shows in page timings, set
  `DATABASE_URL` empty to turn tracking off, or move it to a queue.
- **Sellsy snapshot** in `/admin/sellsy` refreshes inline when stale, so that one
  page can take a few seconds after a cold start.

## 5. Known limits on the free tier

- **Function timeout** (60 s on Hobby). The slowest path is a confirmed chat
  brief: two Gemini calls + SMTP + Sellsy + database, normally 10–20 s.
- **Cold starts** — the first request after idle re-imports Flask, LangChain,
  anthropic and psycopg2 and rebuilds the knowledge index (~1–3 s).
- **In-memory state resets** per instance: chat rate limits, the knowledge index
  and the Sellsy snapshot. Rate limiting is therefore per-instance, not global.
- **Knowledge documents** in `knowledge/` are deployed with the code, so adding a
  PDF means a new deployment — you cannot upload one to the live server.
- **RFP uploads** must go to Supabase Storage; `/tmp` does not survive. Keep
  `SUPABASE_S3_*` configured in production.

## 6. After deploying, check

1. `/` renders with images and fonts (static routing works).
2. `/lets-connect` — submit a test brief; confirm the e-mail arrives and the row
   appears in `/admin`.
3. The chat widget in both modes (Ask and Project assistant).
4. `/admin` sign-in persists across page loads (`FLASK_SECRET_KEY` is set).
