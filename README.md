# UniPulse

> The single, hashtag-driven feed for NUS campus life.

Students miss events because they're buried in 100+ muted Telegram channels. UniPulse fixes that: post any event with `#unipulse` in any group chat, and it lands in a single, searchable, personalised feed that every NUS student can follow.

---

## How It Works

```
Group chat                    UniPulse Bot                  Student
──────────                    ────────────                  ───────
Post message                  Detects #unipulse             /events
with #unipulse  ──────────►  Gemini AI parses  ──────────► /find #sports
(+ optional                   title, date,                  /trending
 image poster)                location                      personalised
                              Saves to DB                   newsletter
                              Sends event card ◄────────────────────────
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Smart event parsing** | Paste any event announcement (or image poster) with `#unipulse` — Gemini AI extracts title, date, location, description automatically |
| **Personalised feed** | Subscribe to categories (#sports, #ai, #general, …) and get a daily digest at your chosen time |
| **RSVP & reminders** | Mark "Going" or "Interested"; automatic 24h and 1h reminders for events you're attending |
| **Search** | `/find pizza` (keyword) or `/find #sports` (category) |
| **Trending** | `/trending` shows events ranked by RSVP count |
| **Google Calendar** | One-tap "Add to Calendar" button on every event card |
| **Moderation panel** | `/manage` lists your events with Edit and Delete buttons — no UUID hunting required |
| **Event editing** | Correct AI parsing errors field-by-field without re-posting |
| **NUS identity gate** | Email verification via Supabase magic links (NUS domain only) |

---

## Tech Stack

- **Runtime**: Python 3.11+
- **Web framework**: [FastAPI](https://fastapi.tiangolo.com/) + uvicorn
- **Bot SDK**: [python-telegram-bot](https://python-telegram-bot.org/) v21 (webhook mode)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Storage**: Supabase Storage (event poster images)
- **Auth**: Supabase Auth (magic link OTP)
- **AI**: [Google Gemini](https://ai.google.dev/) (event text + image OCR)
- **Scheduler**: APScheduler (reminders, daily digest, weekly newsletter)
- **Deploy**: Render / Heroku (Procfile included)

---

## Prerequisites

- Python 3.11+
- A [Telegram bot token](https://core.telegram.org/bots/tutorial#obtain-your-bot-token) from @BotFather
- A [Supabase](https://supabase.com/) project
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini)
- A public HTTPS URL for the webhook (e.g. a Render deploy, or `ngrok` locally)

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/your-org/unipulse.git
cd unipulse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env.local
# Fill in the values — see Environment Variables below

# 4. Run the database migrations
# Open your Supabase project → SQL Editor → paste and run migration.sql

# 5. Create the event-posters storage bucket in Supabase
# Dashboard → Storage → New bucket → name: event-posters → Public: on

# 6. Start the server
uvicorn app.main:app --reload --port 8000
```

For local testing, expose port 8000 with ngrok:

```bash
ngrok http 8000
# Copy the HTTPS URL and set it as WEBHOOK_URL in .env.local
```

---

## Environment Variables

Create `.env.local` (copy from `.env.example`):

| Variable | Description |
|----------|-------------|
| `TOKEN` | Telegram bot token from @BotFather |
| `WEBHOOK_URL` | Public HTTPS base URL (e.g. `https://your-app.onrender.com`) |
| `WEBHOOK_SECRET` | Any random secret string — used to validate incoming Telegram requests |
| `SUPABASE_URL` | Your Supabase project URL (`https://xxxxx.supabase.co`) |
| `SUPABASE_SECRET_KEY` | Supabase service role key (server-side only, never expose to clients) |
| `GEMINI_API_KEY` | Google AI Studio API key |

---

## Deploying to Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com/).
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all six environment variables in the Render dashboard.
6. After the first deploy, set `WEBHOOK_URL` to your Render service URL and redeploy (the bot registers its own webhook on startup).

---

## Supabase Setup

1. Run `migration.sql` in the Supabase SQL Editor. This creates:
   - `pending_verifications` table (persistent magic-link state)
   - `upsert_rsvp` RPC function (atomic RSVP toggle)
   - `created_at` column on `events` (for DB-backed rate limiting)
2. Create a Storage bucket named `event-posters` with **Public** access.
3. The following tables must exist (create them via the Supabase Table Editor or your own migration):
   - `accounts`, `events`, `categories`, `event_categories`, `event_images`, `rsvps`, `reminders`, `account_categories`

---

## Bot Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Welcome screen; shows onboarding on first login |
| `/verify` | Verify NUS identity via email magic link (DM only) |
| `/events` | Browse upcoming events (chronological) |
| `/trending` | Browse events by RSVP popularity |
| `/find <query>` | Search by keyword or `#category` |
| `/subscribe` | Manage category subscriptions |
| `/newslettertime HH:MM` | Set your daily digest delivery time (SGT) |
| `/manage` | View, edit, and delete your own events |
| `/edit <event_id>` | Edit a specific event field-by-field |
| `/delete <event_id>` | Soft-delete an event |

---

## Posting an Event

In any Telegram group where the bot is a member:

```
Hackathon Night — come build something cool!

Date: 15 March 2026, 6 PM
Venue: UTown Auditorium
Open to all NUS students.

#unipulse #tech #hackathon
```

The bot will:
1. Detect `#unipulse`
2. Extract category from the other hashtags (`tech`)
3. Parse event details with Gemini AI
4. Post a formatted event card with RSVP buttons back to the group

Attach an image poster and the bot will OCR it for any details missing from the text.

**Requirements**: you must be a verified NUS user (run `/verify` in a DM first). Limit: 5 posts per hour.

---

## Architecture Overview

```
app/
├── main.py              FastAPI app — webhook endpoint, auth callback
├── bot.py               python-telegram-bot setup, handler registration
├── config.py            Settings (env vars), timezone constant
├── handlers/
│   ├── start.py         /start — welcome + first-login onboarding
│   ├── onboarding.py    Post-verification welcome flow
│   ├── verify.py        /verify — NUS email verification conversation
│   ├── parser.py        #unipulse group message handler (AI parsing)
│   ├── browse.py        /events, /trending
│   ├── find.py          /find
│   ├── subscribe.py     /subscribe — category subscription keyboard
│   ├── rsvp.py          RSVP inline button callbacks
│   ├── remind.py        Reminder inline button + creation
│   ├── moderation.py    /manage — event list with edit/delete
│   ├── edit.py          /edit — field-by-field event editing
│   ├── admin.py         /delete command
│   └── newslettertime.py /newslettertime
├── services/
│   ├── supabase_client.py  All database operations
│   ├── user_service.py     Account & subscription queries
│   ├── event_card.py       Event message formatting
│   ├── gemini.py           Gemini AI event parsing
│   ├── calendar.py         Google Calendar deep-link builder
│   └── scheduler.py        APScheduler initialisation
├── jobs/
│   ├── reminders.py     Send due reminders (every minute)
│   ├── digest.py        Daily personalised newsletter
│   └── newsletter.py    Weekly top-10 roundup (Sunday 6 PM SGT)
├── middleware/
│   └── rate_limit.py    DB-backed rate limiting (5 posts/hour)
└── models/
    └── schemas.py       Pydantic models (ParsedEvent)
```

---

## Contributing

1. Fork the repo and create a branch.
2. Run the server locally with `uvicorn app.main:app --reload`.
3. Test bot interactions via a test bot token pointing to your ngrok URL.
4. Open a pull request with a clear description of the change.
