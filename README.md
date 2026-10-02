# Caribbean Incentive — caribbean-incentive.com

Flask + Bootstrap 5 build for Caribbean Incentive, a boutique Caribbean DMC.
See `CLAUDE_CODE_BUILD_PROMPT.md` for the full build spec.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python app.py
```

App runs at http://127.0.0.1:5000

## .env keys

| Key | Purpose | Fallback if unset |
|---|---|---|
| `FLASK_SECRET_KEY` | Session / CSRF signing | insecure dev key |
| `FLASK_DEBUG` | Debug mode (`1`/`0`) | off |
| `SELLSY_CLIENT_ID` / `SELLSY_CLIENT_SECRET` | Sellsy CRM for event briefs | logs + writes to `instance/submissions.jsonl` |
| `MAIL_SERVER` / `MAIL_PORT` / `MAIL_USE_TLS` / `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_DEFAULT_SENDER` | RFP email delivery | saves upload to `instance/rfps/` |
| `TEAMS_BOOKING_URL` | Microsoft Bookings iframe on Let's Connect | shows a styled placeholder card |
| `WHATSAPP_NUMBER` | WhatsApp CTA on Let's Connect | button is hidden |

## Swapping in real photography / video

Everything image- and video-related is registered in one place: `content/media.py`.
Replace the paths in the `MEDIA` dict (and drop matching files under `static/img` /
`static/video`) — no template changes required.

For demo purposes, `scripts/fetch_placeholders.py` can pull free Caribbean stock
photography from Pexels to populate `static/img` before a client walkthrough.

**For the real build, the client will need to supply ~95 images:**
54 experience gallery images (9 categories × 6), 21 destination panel images
(7 islands × 3 panels), 7 destination hero images, 7 homepage island cards,
and 5 itinerary day images.

## Project structure

See `CLAUDE_CODE_BUILD_PROMPT.md` §2 for the full annotated tree.
