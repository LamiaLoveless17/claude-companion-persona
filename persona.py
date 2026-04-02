"""
knurl-persona — mitmproxy addon that hijacks Claude Code's companion personality.

Reads a persona file (default: persona.txt next to this script) and injects it
into the buddy_react API payload so the companion speaks however you want.

Environment variables:
    KNURL_PERSONA   Path to persona file (default: ./persona.txt)
    KNURL_NAME      Override companion name (optional)
    KNURL_VERBOSE   Set to "1" to print interception logs (default: quiet)
"""

import json
import os
from pathlib import Path

from mitmproxy import http

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent

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


def _log(msg: str) -> None:
    if VERBOSE:
        print(msg)


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

        data["personality"] = _persona

        if OVERRIDE_NAME:
            data["name"] = OVERRIDE_NAME[:32]

        flow.request.set_text(json.dumps(data))

        _log(f"[knurl-persona] intercepted: {orig_name}")
        _log(f"  original: {orig_personality[:80]}…")
        _log(f"  injected: {_persona[:80]}…")
        _log(f"  reason={data.get('reason')}  addressed={data.get('addressed')}")

    except Exception as e:
        _log(f"[knurl-persona] parse error: {e}")


def response(flow: http.HTTPFlow) -> None:
    if not (flow.request.pretty_url.endswith("/buddy_react")
            and flow.request.method == "POST"):
        return

    try:
        data = json.loads(flow.response.get_text())
        reaction = data.get("reaction", "(empty)")
        _log(f"[knurl-persona] reaction: {reaction}")
    except Exception:
        pass
