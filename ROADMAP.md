# Talk — Feature Roadmap

Last updated: 2026-06-15

---

## ✅ Shipped

- **Double-tap hotkey** — double-tap Right-Option to lock recording on; double-tap again to stop (in addition to existing hold mode)
- **iPhone PWA** — full Progressive Web App installable to iPhone home screen via Safari
- **Groq Whisper on iPhone** — replaced Web Speech API with `whisper-large-v3-turbo` via Groq (same model as Mac, same accuracy)
- **✨ Enhance writing** — post-transcription AI restructuring: detects lists, bullet points, paragraph breaks, run-on sentences
- **Editable result box** — iPhone transcript is fully editable in a native textarea before copying/sharing
- **Self-improvement loops** — edit capture → dynamic few-shot → Claude calibrates to user's style over time; startup sync pulls Supabase learnings to Mac on every launch
- **Cross-device stats** — Supabase-backed stats combining Mac + iPhone sessions
- **Rate limiting** — 20 req/hour per IP on Edge Function to prevent API abuse

---

## 🔴 High Impact, Low Effort

**1. Dictation History on Mac**
A searchable list of everything you've dictated — browse, copy, re-paste old dictations. Data is already in `talk.log` and Supabase but invisible unless you open the stats dashboard. One click from the menu bar.

**2. Notification Copy Button**
After dictating on Mac, the notification should have a **Copy** button. Useful when you dictated into the wrong window or just want to grab the text without it being auto-pasted.

**3. Auto-Copy on iPhone After Transcription**
Auto-copy to clipboard on completion and show "Copied!" toast. Removes one manual tap every single time.

---

## 🟠 High Impact, Medium Effort

**4. Custom Formatting Modes**
Trigger different Claude prompts with different hotkeys:
- `Right Option` = normal cleanup (current)
- `Right Option + Shift` = concise, remove filler
- `Right Option + Cmd` = bullet points / structured format

Each mode is a different system prompt sent to Claude. Biggest remaining gap vs WISPR Flow / SuperWhisper.

**5. Pause / Resume During Dictation**
Tap Right Option once to pause mid-dictation, hold again to continue. Needed for long dictations where you stop to think mid-sentence.

**6. Dictation History on iPhone**
Add a **History** tab to the PWA — scrollable list of past dictations with tap-to-copy. Pulls from Supabase, shows Mac + iPhone sessions together.

---

## 🟡 Medium Impact, Medium Effort

**7. Smart Snippet Expansion**
Say "my email" → expands to your email address. Say "my Phoenix pitch" → expands to a saved blurb. Store snippets in Supabase, sync across devices.

**8. Corrections Review UI**
A page or menu bar view to see, approve, or delete learned auto-corrections. Prevents bad corrections from compounding silently over time.

**9. Word-Level Confidence Filtering**
`mlx-whisper` returns per-word confidence scores. Flag low-confidence words in the notification so you know what to double-check before sending.

---

## 🟢 Lower Priority / Polish

**10. One-Click Installer**
An `install.sh` that sets up the venv, installs deps, creates the `.env` template, and loads the LaunchAgent. Makes Talk shareable without needing to read the README.

**11. Android / Chrome Support**
The PWA technically works on Android Chrome already. Needs testing and a few CSS tweaks.

**12. Multi-language**
Whisper supports 99 languages. A language selector in the menu bar and PWA, passing `language=` to both `mlx_whisper` and Groq.

**13. Export**
Download full dictation history as Markdown or CSV from the dashboard.
