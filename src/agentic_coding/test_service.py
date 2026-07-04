"""Test-plan helpers for Agentic Coding.

The initial slice records explicit test commands and produces a stable artifact
payload. Runtime execution can be wired through the existing Odysseus shell gate
after the scaffold approval flow is in place.
"""

from __future__ import annotations

from .security import classify_shell_risk, command_requires_approval

_TEST_PREFIXES = ("pytest", "python -m pytest", "npm test", "pnpm test", "yarn test")


def normalize_test_command(command: str | None) -> dict:
    text = (command or "").strip()
    lower = text.lower()
    is_test = bool(text) and any(lower.startswith(prefix) for prefix in _TEST_PREFIXES)
    return {
        "command": text,
        "is_supported_test_command": is_test,
        "risk": classify_shell_risk(text),
        "requires_approval": command_requires_approval(text),
    }
