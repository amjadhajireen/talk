"""
Launcher that warms up file access before running Talk.

macOS system services briefly lock files on first launchctl access,
causing EDEADLK. Warm-up pre-touches the critical files/modules so
those locks clear before talk.py runs.

Launched with `python -S` to skip site.py (which reads pyvenv.cfg from
~/Documents/ and hits EDEADLK before any of our code runs). We add
site-packages to sys.path manually below instead.

site-packages is symlinked to ~/Library/Application Support/Talk/site-packages/
so all imports resolve to ~/Library/ (XProtect-safe, no EDEADLK).

Uses runpy.run_path() so the same process/GUI session is reused (menu bar works).
"""
import os
import sys

# python -S skips site.py, so sys.path won't include the venv's site-packages.
# Add them now so all subsequent imports work normally.
# The symlink .venv/lib/python3.12/site-packages -> ~/Library/Application Support/Talk/site-packages/
# means all package files resolve to ~/Library/ which is EDEADLK-safe.
_here = os.path.dirname(os.path.abspath(__file__))
_site_packages = os.path.join(_here, ".venv", "lib", "python3.12", "site-packages")

if _site_packages not in sys.path:
    sys.path.insert(0, _site_packages)

import time
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.expanduser("~/Library/Application Support/Talk")
TALK = os.path.join(HERE, "talk.py")


def _try_read(path):
    with open(path) as f:
        f.read()


def warmup():
    """Touch critical files and imports. Raises OSError(11) if any are locked.

    Repeatedly reading venv files signals to macOS (XProtect/Spotlight) that
    this process is legitimate, eventually releasing the EDEADLK locks.
    """
    for fname in [".env", "dictionary.txt", "corrections.txt"]:
        p = os.path.join(DATA_DIR, fname)
        if os.path.exists(p):
            _try_read(p)

    import ssl
    ssl.create_default_context()

    import mlx_whisper  # noqa: F401 — reads many venv files, clearing the locks


for attempt in range(60):  # up to 3 minutes
    try:
        warmup()
        break
    except OSError as e:
        if e.errno == 11:
            print(f"[start_talk] warmup attempt {attempt + 1} hit EDEADLK, retrying in 3s...", flush=True)
            time.sleep(3)
        else:
            raise

# Run talk.py in this same process so GUI session and interpreter are preserved
try:
    runpy.run_path(TALK, run_name="__main__")
    sys.exit(0)
except SystemExit as e:
    sys.exit(e.code)
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
