"""
claude-companion-persona — mitmproxy addon that overrides Claude Code's companion personality.

Reads a persona file (default: persona.txt next to this script) and injects it
into the buddy_react API payload so the companion speaks however you want.

Environment variables:
    KNURL_PERSONA   Path to persona file (default: ./persona.txt)
    KNURL_NAME      Override companion name (optional)
    KNURL_VERBOSE   Set to "1" to print interception logs (default: quiet)
"""

import json
import os
import time
from pathlib import Path

from mitmproxy import http

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_STATE_FILE = Path(os.environ.get(
    "KNURL_STATE", "/tmp/companion-persona-state.json"
))

PERSONA_PATH = Path(os.environ.get("KNURL_PERSONA", _SCRIPT_DIR / "persona.txt"))
OVERRIDE_NAME = os.environ.get("KNURL_NAME", "")
VERBOSE = os.environ.get("KNURL_VERBOSE", "0") == "1"


def _load_persona() -> str:
    """Load persona text, truncated to the 200-char API limit."""
    try:
        text = PERSONA_PATH.read_text().strip()
    except FileNotFoundError:
        text = "A mysterious creature. (persona file not found)"
    return text[:200]


# Pre-load once; persona.txt is small, no need for hot-reload
_persona = _load_persona()

# In-memory state for the last interception
_last_state: dict = {}


def _log(msg: str) -> None:
    if VERBOSE:
        print(msg)


def _save_state() -> None:
    """Write last interception state to a JSON file for external tools."""
    try:
        _STATE_FILE.write_text(json.dumps(_last_state, ensure_ascii=False, indent=2))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# mitmproxy hooks
# ---------------------------------------------------------------------------

def request(flow: http.HTTPFlow) -> None:
    if not (flow.request.pretty_url.endswith("/buddy_react")
            and flow.request.method == "POST"):
        return

    try:
        data = json.loads(flow.request.get_text())

        orig_name = data.get("name", "")
        orig_personality = data.get("personality", "")

        # Update state
        _last_state["original_name"] = orig_name
        _last_state["original_personality"] = orig_personality
        _last_state["injected_personality"] = _persona
        _last_state["injected_name"] = OVERRIDE_NAME or orig_name
        _last_state["reason"] = data.get("reason", "")
        _last_state["addressed"] = data.get("addressed", False)
        _last_state["species"] = data.get("species", "")
        _last_state["rarity"] = data.get("rarity", "")
        _last_state["stats"] = data.get("stats", {})
        _last_state["timestamp"] = time.strftime("%H:%M:%S")
        _last_state["persona_file"] = str(PERSONA_PATH)

        # Inject
        data["personality"] = _persona
        if OVERRIDE_NAME:
            data["name"] = OVERRIDE_NAME[:32]

        flow.request.set_text(json.dumps(data))
        _save_state()

        _log(f"[companion-persona] intercepted: {orig_name}")
        _log(f"  original: {orig_personality[:80]}…")
        _log(f"  injected: {_persona[:80]}…")
        _log(f"  reason={data.get('reason')}  addressed={data.get('addressed')}")

    except Exception as e:
        _log(f"[companion-persona] parse error: {e}")


def response(flow: http.HTTPFlow) -> None:
    if not (flow.request.pretty_url.endswith("/buddy_react")
            and flow.request.method == "POST"):
        return

    try:
        data = json.loads(flow.response.get_text())
        reaction = data.get("reaction", "(empty)")
        _last_state["last_reaction"] = reaction
        _save_state()
        _log(f"[companion-persona] reaction: {reaction}")
    except Exception:
        pass
