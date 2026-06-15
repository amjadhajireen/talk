"""
Launcher that warms up file access before running Talk.

macOS system services (Spotlight, XProtect) briefly lock files on first
access by a new launchctl process, causing EDEADLK. Warm-up pre-touches
the critical files/modules so those locks clear before talk.py runs.
"""
import os
import sys
import time

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.expanduser("~/Library/Application Support/Talk")
PYTHON = sys.executable
TALK = os.path.join(HERE, "talk.py")


def _try_read(path):
    with open(path) as f:
        f.read()


def warmup():
    """Touch critical files and imports. Raises OSError(11) if any are locked."""
    # Runtime files live in ~/Library — accessible by LaunchAgent without TCC restriction
    for fname in [".env", "dictionary.txt", "corrections.txt"]:
        p = os.path.join(DATA_DIR, fname)
        if os.path.exists(p):
            _try_read(p)

    # SSL context (uses system trust store via SSL_CERT_FILE env var in plist)
    import ssl
    ssl.create_default_context()

    # mlx_whisper triggers the hf metadata scan
    import mlx_whisper  # noqa: F401


for attempt in range(30):
    try:
        warmup()
        break
    except OSError as e:
        if e.errno == 11:
            print(f"[start_talk] warmup attempt {attempt + 1} hit EDEADLK, retrying in 3s...", flush=True)
            time.sleep(3)
        else:
            raise

# Replace this process with talk.py so it inherits the launchctl GUI session
# (subprocess.run() child doesn't get menu bar / window server access).
# launchctl's KeepAlive handles restarts if talk.py crashes.
os.execv(PYTHON, [PYTHON, TALK])
