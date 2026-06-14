#!/usr/bin/env python3
"""Talk stats dashboard — generates an HTML page and opens it in the browser."""

import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

LOG_PATH = os.path.join(os.path.dirname(__file__), "talk.log")


def _load_env():
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _load_supabase_sessions():
    """Pull all sessions from Supabase (includes iPhone sessions)."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            return []
        sb = create_client(url, key)
        result = sb.table("sessions").select("ts,cleaned,words,device").execute()
        return result.data or []
    except Exception as e:
        print(f"Supabase load error: {e}")
        return []


def load_entries():
    _load_env()
    # Local entries keyed by rounded timestamp (dedup with Supabase)
    seen: set = set()
    entries = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            for line in f:
                try:
                    e = json.loads(line.strip())
                    ts = e.get("ts")
                    if ts:
                        key = round(float(ts), 0)
                        seen.add(key)
                        entries.append(e)
                except Exception:
                    pass
    # Merge remote sessions (iPhone + any Mac sessions not yet in local log)
    for e in _load_supabase_sessions():
        ts = e.get("ts")
        if ts and round(float(ts), 0) not in seen:
            entries.append(e)
    return entries


def word_count(text):
    return len(text.split()) if text and text.strip() else 0


def fmt_number(n):
    return f"{n:,}"


def fmt_time(minutes):
    if minutes < 1:
        return f"{int(minutes * 60)}s"
    if minutes < 60:
        return f"{minutes:.0f}m"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}m" if m else f"{h}h"


def generate_html(entries):
    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())  # Monday

    daily_words = defaultdict(int)
    daily_sessions = defaultdict(int)
    hourly_buckets = defaultdict(int)
    active_days = set()

    words_today = words_week = words_all = 0
    sessions_today = sessions_week = sessions_all = 0

    for e in entries:
        cleaned = e.get("cleaned", "")
        words = word_count(cleaned)
        words_all += words
        sessions_all += 1

        ts = e.get("ts")
        if ts is None:
            continue
        dt = datetime.fromtimestamp(ts)
        d = dt.date()
        active_days.add(d)
        daily_words[d] += words
        daily_sessions[d] += 1
        hourly_buckets[dt.hour] += 1

        if d == today:
            words_today += words
            sessions_today += 1
        if d >= week_start:
            words_week += words
            sessions_week += 1

    # Streak: consecutive days ending today, or yesterday if not yet used today
    streak = 0
    check = today if today in active_days else today - timedelta(days=1)
    while check in active_days:
        streak += 1
        check -= timedelta(days=1)

    # Peak hour
    if hourly_buckets:
        peak_h = max(hourly_buckets, key=hourly_buckets.get)
        peak_str = f"{peak_h}:00–{(peak_h + 1) % 24}:00"
    else:
        peak_str = "—"

    avg_words = round(words_all / sessions_all) if sessions_all else 0

    # Time saved: assume 40 WPM typing speed
    saved_today = words_today / 40
    saved_week = words_week / 40
    saved_all = words_all / 40

    # Last 7 days chart
    chart_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    chart_vals = [daily_words[d] for d in chart_days]
    chart_max = max(chart_vals) if any(chart_vals) else 1
    BAR_MAX_H = 100

    def bar_h(v):
        return max(3, int(v / chart_max * BAR_MAX_H)) if chart_max > 0 else 3

    bars_html = ""
    for d, v in zip(chart_days, chart_vals):
        lbl = "Today" if d == today else d.strftime("%-d %b")
        cls = "bar today" if d == today else "bar"
        val_str = str(v) if v else ""
        bars_html += f"""
            <div class="bar-col">
                <div class="bar-val">{val_str}</div>
                <div class="{cls}" style="height:{bar_h(v)}px"></div>
                <div class="bar-lbl">{lbl}</div>
            </div>"""

    # Top hours heatmap (last row: 0–23)
    hour_max = max(hourly_buckets.values()) if hourly_buckets else 1
    hours_html = ""
    for h in range(24):
        v = hourly_buckets.get(h, 0)
        opacity = max(0.06, v / hour_max) if v else 0.06
        lbl = f"{h:02d}"
        hours_html += f'<div class="hour" style="background:rgba(124,58,237,{opacity:.2f})" title="{v} sessions at {lbl}:00"><span>{lbl}</span></div>'

    generated = now.strftime("%-d %b %Y, %-I:%M %p")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Talk — Stats</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0d0d0d;
    color: #e8e8e8;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    min-height: 100vh;
    padding: 40px 32px;
  }}
  header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 36px;
  }}
  header h1 {{ font-size: 22px; font-weight: 600; }}
  header .sub {{ color: #555; font-size: 13px; }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }}
  .card {{
    background: #181818;
    border: 1px solid #252525;
    border-radius: 16px;
    padding: 24px;
  }}
  .card-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 12px;
  }}
  .stat-row {{
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin-bottom: 6px;
  }}
  .stat-big {{
    font-size: 40px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f0f0f0;
    line-height: 1;
  }}
  .stat-unit {{
    font-size: 14px;
    color: #555;
  }}
  .stat-periods {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-top: 10px;
  }}
  .period {{
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: #666;
  }}
  .period span:last-child {{ color: #999; }}

  .accent {{ color: #7c3aed; }}

  /* Chart */
  .chart-wrap {{
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 130px;
    padding-top: 24px;
    margin-top: 8px;
  }}
  .bar-col {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    height: 100%;
    justify-content: flex-end;
  }}
  .bar-val {{
    font-size: 10px;
    color: #555;
    height: 14px;
    line-height: 14px;
  }}
  .bar {{
    width: 100%;
    background: #2a2a2a;
    border-radius: 4px 4px 0 0;
    min-height: 3px;
    transition: background 0.2s;
  }}
  .bar.today {{ background: #7c3aed; }}
  .bar-lbl {{
    font-size: 10px;
    color: #444;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }}

  /* Hour heatmap */
  .hours {{
    display: flex;
    gap: 3px;
    margin-top: 8px;
  }}
  .hour {{
    flex: 1;
    height: 28px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: default;
  }}
  .hour span {{
    font-size: 8px;
    color: rgba(255,255,255,0.25);
  }}

  .meta {{
    margin-top: 32px;
    font-size: 11px;
    color: #333;
    text-align: center;
  }}

  @media (max-width: 640px) {{
    .grid {{ grid-template-columns: 1fr; }}
    .grid-2 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<header>
  <h1>🎙 Talk</h1>
  <span class="sub">Voice stats</span>
</header>

<div class="grid">
  <div class="card">
    <div class="card-label">Words dictated</div>
    <div class="stat-row">
      <div class="stat-big accent">{fmt_number(words_today)}</div>
      <div class="stat-unit">today</div>
    </div>
    <div class="stat-periods">
      <div class="period"><span>This week</span><span>{fmt_number(words_week)}</span></div>
      <div class="period"><span>All time</span><span>{fmt_number(words_all)}</span></div>
    </div>
  </div>

  <div class="card">
    <div class="card-label">Time saved</div>
    <div class="stat-row">
      <div class="stat-big">{fmt_time(saved_today)}</div>
    </div>
    <div class="stat-periods">
      <div class="period"><span>This week</span><span>{fmt_time(saved_week)}</span></div>
      <div class="period"><span>All time</span><span>{fmt_time(saved_all)}</span></div>
      <div class="period"><span style="color:#333;font-size:11px">vs typing at 40 WPM</span><span></span></div>
    </div>
  </div>

  <div class="card">
    <div class="card-label">Sessions</div>
    <div class="stat-row">
      <div class="stat-big">{sessions_today}</div>
      <div class="stat-unit">today</div>
    </div>
    <div class="stat-periods">
      <div class="period"><span>This week</span><span>{sessions_week}</span></div>
      <div class="period"><span>All time</span><span>{fmt_number(sessions_all)}</span></div>
    </div>
  </div>
</div>

<div class="grid-2">
  <div class="card">
    <div class="card-label">Last 7 days</div>
    <div class="chart-wrap">{bars_html}
    </div>
  </div>

  <div class="card">
    <div class="card-label">Quick stats</div>
    <div class="stat-periods" style="gap:12px;margin-top:4px">
      <div class="period">
        <span>🔥 Streak</span>
        <span style="color:#f97316;font-weight:600">{streak} day{"s" if streak != 1 else ""}</span>
      </div>
      <div class="period">
        <span>⚡ Avg per session</span>
        <span>{fmt_number(avg_words)} words</span>
      </div>
      <div class="period">
        <span>🕐 Peak hour</span>
        <span>{peak_str}</span>
      </div>
      <div class="period">
        <span>📅 Active days</span>
        <span>{len(active_days)}</span>
      </div>
    </div>
    <div class="card-label" style="margin-top:20px;margin-bottom:6px">Activity by hour</div>
    <div class="hours">{hours_html}</div>
  </div>
</div>

<div class="meta">Generated {generated} · <a href="" onclick="location.reload();return false" style="color:#333">Refresh</a></div>

</body>
</html>"""


if __name__ == "__main__":
    entries = load_entries()
    html = generate_html(entries)
    out = "/tmp/talk_dashboard.html"
    with open(out, "w") as f:
        f.write(html)
    subprocess.run(["open", out])
