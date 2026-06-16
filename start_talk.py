"""
Launcher that warms up file access before running Talk.

macOS system services briefly lock files on first launchctl access,
causing EDEADLK. Warm-up pre-touches the critical files/modules so
those locks clear before talk.py runs.

Uses runpy.run_path() instead of os.execv() so that:
  - The same Python interpreter process is reused (no fresh startup EDEADLK)
  - The launchctl GUI session is preserved (menu bar icon works)
"""
import os
import sys
import time
import runpy

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.expanduser("~/Library/Application Support/Talk")
TALK = os.path.join(HERE, "talk.py")


def _try_read(path):
    with open(path) as f:
        f.read()


def warmup():
    """Verify DATA_DIR files are readable. Raises OSError(11) if locked."""
    for fname in [".env", "dictionary.txt", "corrections.txt"]:
        p = os.path.join(DATA_DIR, fname)
        if os.path.exists(p):
            _try_read(p)

    import ssl
    ssl.create_default_context()


for attempt in range(10):
    try:
        warmup()
        break
    except OSError as e:
        if e.errno == 11:
            print(f"[start_talk] warmup attempt {attempt + 1} hit EDEADLK, retrying in 3s...", flush=True)
            time.sleep(3)
        else:
            raise

# Run talk.py in this same process so GUI session and interpreter are preserved.
# Retry on EDEADLK from venv imports — locks usually clear within 60s.
for _attempt in range(10):
    try:
        runpy.run_path(TALK, run_name="__main__")
        sys.exit(0)
    except SystemExit as e:
        sys.exit(e.code)
    except OSError as e:
        if e.errno == 11 and _attempt < 9:
            print(f"[start_talk] talk.py import EDEADLK on attempt {_attempt + 1}, retrying in 30s...", flush=True)
            time.sleep(30)
        else:
            import traceback
            traceback.print_exc()
            sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
