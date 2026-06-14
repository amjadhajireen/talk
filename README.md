# Talk

A personal AI dictation app for Mac and iPhone. Speak, and get a clean, punctuated transcript pasted wherever your cursor is — powered by Whisper and Claude. Gets smarter the more you use it.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20iOS-black)
![Model](https://img.shields.io/badge/whisper-large--v3--turbo-7c3aed)
![Claude](https://img.shields.io/badge/claude-haiku--4--5-7c3aed)
![Sync](https://img.shields.io/badge/sync-supabase-3ecf8e)

---

## What it does

**Mac** — Hold Right-Option to record (push-to-talk), or double-tap to lock recording on and double-tap again to stop. Cleaned text is pasted at your cursor in whatever app is focused.

**iPhone** — Tap the mic button, speak as long as you want, tap again to stop. Whisper transcribes, Claude cleans, result appears in an editable box ready to copy or share.

Both devices share a Supabase database — corrections learned on one device apply on the other.

---

## How it works

```
Mac:    hold/double-tap Right-Option
          → local Whisper (mlx-whisper, on-device, nothing leaves your Mac)
          → Claude Haiku cleanup
          → paste at cursor

iPhone: tap mic → record
          → MediaRecorder audio → Groq Whisper API (whisper-large-v3-turbo)
          → Claude Haiku cleanup (Supabase Edge Function)
          → editable result → copy / share
```

---

## Stack

| Layer | Mac | iPhone |
|---|---|---|
| Transcription | `mlx-whisper` — local, on-device | Groq API — `whisper-large-v3-turbo` |
| Cleanup | Claude Haiku — Anthropic API | Claude Haiku — Supabase Edge Function |
| UI | `rumps` menu bar app | Progressive Web App (Safari) |
| Cloud sync | Supabase (PostgreSQL) | Supabase (PostgreSQL) |
| Backend | — | Supabase Edge Functions (Deno/TypeScript) |
| Auto-start | macOS LaunchAgent | Installed to iPhone home screen |

---

## Features

### Transcription accuracy
- **Word boosting** — your vocabulary (`dictionary.txt`) is fed as Whisper's `initial_prompt`, biasing ASR toward your proper nouns and brand names
- **Spelling hints** — say "kick, K-I-C-K" and it writes `kick` and adds the word to your dictionary for future sessions
- **App-aware formatting** — detects the frontmost app (Slack, email, Notion, code editor, terminal) and adjusts Claude's output style to match

### Hotkey modes (Mac)
- **Hold** Right-Option → push-to-talk, transcribes on release
- **Double-tap** Right-Option → locks recording on; double-tap again to stop and transcribe

### AI writing tools (iPhone)
- **Cleanup** — removes filler words, fixes punctuation, applies corrections automatically
- **✨ Enhance** — tap to have Claude restructure the transcript: detects numbered lists, bullet points, paragraph breaks, and run-on sentences
- **Editable result** — tap anywhere in the result to edit before copying or sharing

### Self-improvement (all devices)
The app has three learning loops that run automatically:

1. **FIXES protocol** — when Claude corrects a Whisper mishearing (e.g. "cloud" → "Claude"), it appends a `FIXES:` line; Talk saves the pair to `corrections.txt` and applies it on every future recording
2. **Edit capture** — when you edit the iPhone transcript before copying, the before/after pair is stored in Supabase as a personalised example for Claude
3. **Dynamic few-shot** — before each cleanup, Claude sees your 5 most recent real edits as examples, calibrating to your exact style over time
4. **Startup sync** — on every Mac launch, Talk pulls latest corrections and vocabulary from Supabase, so learnings from iPhone immediately apply on Mac

### Stats & history
- **Stats dashboard** — `python dashboard.py` opens a browser page with 7-day word chart, streak, peak hour heatmap, time saved vs typing
- **Cross-device stats** — iPhone stats tab shows combined Mac + iPhone session totals from Supabase

### Security
- **Rate limiting** — Edge Function enforces 20 requests/hour per IP; prevents API cost abuse even if the endpoint is discovered
- **Single-instance lock** — `/tmp/talk.lock` prevents accidental double-paste from two running instances
- **Clipboard restore** — paste saves and restores your clipboard so your copied content is never overwritten

---

## Setup (Mac)

**Requirements:** macOS, Apple Silicon (M1+), Python 3.10+

```bash
git clone https://github.com/amjadhajireen/talk.git
cd talk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Run:
```bash
python talk.py
```

Grant **Accessibility** permission when prompted (System Settings → Privacy & Security → Accessibility → add your Python binary from `.venv/bin/python`).

**Auto-start on login:**
```bash
cp com.amjad.talk.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.amjad.talk.plist
```

---

## Setup (iPhone PWA)

1. Open Safari → `https://amjadhajireen.github.io/talk/`
2. Tap **Share → Add to Home Screen**
3. Talk icon appears on your home screen — no App Store needed

The Edge Function requires two secrets in your Supabase dashboard (Settings → Edge Functions → Secrets):
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY` — free at [console.groq.com](https://console.groq.com) (7,200 sec/day free tier)

Deploy the Edge Function:
```bash
brew install supabase/tap/supabase
cd talk
SUPABASE_ACCESS_TOKEN=your_token supabase link --project-ref your_project_ref
SUPABASE_ACCESS_TOKEN=your_token supabase functions deploy cleanup --no-verify-jwt
```

---

## Supabase schema

Run this in your Supabase SQL Editor:

```sql
CREATE TABLE sessions (
  id      BIGSERIAL PRIMARY KEY,
  ts      FLOAT NOT NULL,
  raw     TEXT,
  cleaned TEXT,
  words   INT,
  device  TEXT DEFAULT 'mac'
);

CREATE TABLE corrections (
  wrong   TEXT PRIMARY KEY,
  correct TEXT NOT NULL,
  source  TEXT
);

CREATE TABLE dictionary (
  word TEXT PRIMARY KEY
);

CREATE TABLE rate_limits (
  ip    TEXT NOT NULL,
  hour  BIGINT NOT NULL,
  count INT NOT NULL DEFAULT 1,
  PRIMARY KEY (ip, hour)
);

CREATE TABLE edit_corrections (
  id       BIGSERIAL PRIMARY KEY,
  ts       FLOAT NOT NULL,
  original TEXT,
  edited   TEXT,
  device   TEXT DEFAULT 'iphone'
);

CREATE OR REPLACE FUNCTION increment_rate_limit(p_ip TEXT, p_hour BIGINT)
RETURNS INT LANGUAGE sql AS $$
  INSERT INTO rate_limits (ip, hour, count)
  VALUES (p_ip, p_hour, 1)
  ON CONFLICT (ip, hour) DO UPDATE SET count = rate_limits.count + 1
  RETURNING count;
$$;

-- Disable RLS (personal app, no multi-user auth needed)
ALTER TABLE sessions         DISABLE ROW LEVEL SECURITY;
ALTER TABLE corrections      DISABLE ROW LEVEL SECURITY;
ALTER TABLE dictionary       DISABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limits      DISABLE ROW LEVEL SECURITY;
ALTER TABLE edit_corrections DISABLE ROW LEVEL SECURITY;
```

---

## Customisation

| File | Purpose |
|---|---|
| `corrections.txt` | Manual corrections: `wrong -> correct`, one per line |
| `dictionary.txt` | Known vocabulary for Whisper biasing and Claude spelling reference |
| `talk.py` → `_APP_STYLE_MAP` | Map app names to formatting style hints |
| `talk.py` → `FEW_SHOT` | Static few-shot examples for Claude cleanup |
| `talk.py` → `WHISPER_HALLUCINATIONS` | Strings to filter as Whisper silence artifacts |

---

## Stats dashboard (Mac)

```bash
python dashboard.py
```

Opens an HTML page in your browser showing:
- Words dictated today / this week / all time
- Time saved vs typing at 40 WPM
- 7-day bar chart
- Streak and peak usage hour
- Hourly activity heatmap
- Mac vs iPhone word counts
