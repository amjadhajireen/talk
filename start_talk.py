"""
Launcher for Talk.

Launched with `python -S` to skip site.py (which would try to read pyvenv.cfg
from ~/Documents/ and hit EDEADLK at launchctl startup). We add site-packages
to sys.path manually instead.

site-packages is symlinked to ~/Library/Application Support/Talk/site-packages/
so all imports resolve to ~/Library/ — outside ~/Documents/, XProtect-safe.

Uses runpy.run_path() so the same process/GUI session is reused (menu bar works).
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_site_packages = os.path.join(_here, ".venv", "lib", "python3.12", "site-packages")

if _site_packages not in sys.path:
    sys.path.insert(0, _site_packages)

import runpy

TALK = os.path.join(_here, "talk.py")

try:
    runpy.run_path(TALK, run_name="__main__")
    sys.exit(0)
except SystemExit as e:
    sys.exit(e.code)
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
