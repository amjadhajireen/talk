# Talk

A personal AI dictation app for Mac and iPhone. Press a key, speak, and get a clean, punctuated transcript pasted wherever your cursor is — powered by Whisper and Claude.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20iOS-black)
![Model](https://img.shields.io/badge/whisper-large--v3--turbo-7c3aed)
![Claude](https://img.shields.io/badge/claude-haiku--4--5-7c3aed)

---

## What it does

- **Hold Right Option** on Mac → speak → release → cleaned text is pasted at your cursor
- **Tap mic** on iPhone (PWA) → speak → tap stop → cleaned text ready to copy/share
- Whisper transcribes, Claude cleans: fixes punctuation, removes filler words, applies corrections
- Learns your vocabulary — proper nouns, brand names, and spelling hints you teach it persist across sessions
- Stats dashboard shows words dictated, time saved, streak, and peak hour — across both devices

## How it works

```
Mac:    Right Option held → local Whisper (mlx-whisper) → Claude Haiku cleanup → paste
iPhone: tap mic → MediaRecorder audio → Groq Whisper → Claude Haiku cleanup → copy/share
                                               ↑
                                     same model, same quality
```

Both pipelines share a Supabase database for corrections, vocabulary, and session history — so the app gets smarter on all devices at once.

## Stack

| Layer | Mac | iPhone |
|---|---|---|
| Transcription | `mlx-whisper` (local, on-device) | Groq API (`whisper-large-v3-turbo`) |
| Cleanup | Claude Haiku via Anthropic API | Claude Haiku via Supabase Edge Function |
| UI | `rumps` menu bar app | Progressive Web App (Safari) |
| Sync | Supabase (PostgreSQL) | Supabase (PostgreSQL) |
| Auto-start | LaunchAgent | Installed to iPhone home screen |

## Features

- **Word boosting** — custom vocabulary fed as Whisper `initial_prompt` biases transcription toward your terms
- **Auto-corrections** — `corrections.txt` maps mishearings (`Cloud -> Claude`); Claude learns new ones automatically and syncs them
- **Spelling hints** — say "kick, K-I-C-K" and it writes `kick`, saving the word to your dictionary
- **App-aware cleanup** — detects the frontmost app (Slack, email, notes, code) and adjusts formatting style
- **Self-learning** — when Claude spots a pronunciation-based mishearing, it saves the correction for next time
- **Stats dashboard** — `python dashboard.py` opens an HTML page with a 7-day chart, streak, and hourly activity heatmap
- **Rate limiting** — Edge Function enforces 20 requests/hour per IP to prevent API abuse

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
ANTHROPIC_API_KEY=your_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

Run:
```bash
python talk.py
```

Grant **Accessibility** permission when prompted (System Settings → Privacy & Security → Accessibility → add your Python binary).

**Auto-start on login:**
```bash
cp com.amjad.talk.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.amjad.talk.plist
```

## Setup (iPhone PWA)

The iPhone app is hosted on GitHub Pages and backed by a Supabase Edge Function.

1. Open Safari → `https://amjadhajireen.github.io/talk/`
2. Tap Share → **Add to Home Screen**
3. Done — Talk icon on your home screen, no App Store needed

The Edge Function needs two secrets set in your Supabase dashboard (Settings → Edge Functions → Secrets):
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY` (free tier at [console.groq.com](https://console.groq.com))

## Supabase schema

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

CREATE OR REPLACE FUNCTION increment_rate_limit(p_ip TEXT, p_hour BIGINT)
RETURNS INT LANGUAGE sql AS $$
  INSERT INTO rate_limits (ip, hour, count)
  VALUES (p_ip, p_hour, 1)
  ON CONFLICT (ip, hour) DO UPDATE SET count = rate_limits.count + 1
  RETURNING count;
$$;
```

## Customisation

| File | Purpose |
|---|---|
| `corrections.txt` | Manual corrections: `wrong -> correct`, one per line |
| `dictionary.txt` | Known vocabulary for Whisper biasing and Claude spelling reference |
| `talk.py` → `_APP_STYLE_MAP` | Add apps to the style hint map |
| `talk.py` → `FEW_SHOT` | Add cleanup examples to improve Claude output |

## Stats

```bash
python dashboard.py
```

Opens an HTML dashboard in your browser with words dictated, time saved vs typing, streak, and hourly activity heatmap — combining Mac and iPhone sessions via Supabase.
