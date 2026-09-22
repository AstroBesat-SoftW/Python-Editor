"""
config.py
---------
Centralised application configuration.

The OpenAI API key is NEVER hard-coded in source. On first run you set it
once from inside the app (AI Assistant -> Add API Key), and it is saved
locally to a small settings file in your user folder so you are never
asked again. You can change it anytime the same way.

Lookup order for the key at startup:
  1. OPENAI_API_KEY environment variable / local .env file (if present)
  2. Previously saved key in the user settings file
"""

import os
import sys
import json

# Load a local .env file if python-dotenv is available. This is optional.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

APP_NAME = "Sotstech Python Editor"
APP_DISPLAY_TITLE = "Sotstech Python Editor 2023"
APP_VERSION = "2.0.34"

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = 700
AI_TEMPERATURE = 0.4

DEFAULT_WINDOW_SIZE = "1250x780"
MIN_WINDOW_SIZE = (950, 620)

# ---------------------------------------------------------------------------
# Workspace folder ("dosyam"): every file the editor creates or opens by
# default lives here, next to the application itself. Open/Save dialogs
# default to this folder, and the import auto-suggestion feature scans it
# to know which other files are available to import.
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Running as a PyInstaller-built .exe: __file__ would point inside the
    # temporary extraction folder (sys._MEIPASS), which is wiped every time
    # the app closes. Use the real folder the .exe itself lives in instead,
    # so "dosyam" persists across runs.
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(APP_DIR, "dosyam")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Persistent local settings (stores the OpenAI API key so the user is only
# ever asked for it once, no matter where the app is copied/run from).
# ---------------------------------------------------------------------------
_SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".sotstech_python_editor")
_SETTINGS_FILE = os.path.join(_SETTINGS_DIR, "settings.json")


def _read_settings() -> dict:
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _write_settings(data: dict) -> None:
    os.makedirs(_SETTINGS_DIR, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_saved_api_key() -> str:
    return _read_settings().get("openai_api_key", "")


def save_api_key(key: str) -> None:
    data = _read_settings()
    data["openai_api_key"] = key.strip()
    _write_settings(data)


def clear_saved_api_key() -> None:
    data = _read_settings()
    data.pop("openai_api_key", None)
    _write_settings(data)


# Resolve the active key once at startup: environment variable takes
# priority (useful for developers), otherwise fall back to the saved key.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "") or load_saved_api_key()
