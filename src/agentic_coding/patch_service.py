"""Patch proposal and application helpers for Agentic Coding.

The service intentionally supports a conservative operation model instead of raw
shell execution. Patch proposals are persisted as artifacts, must be approved,
and are applied only inside the vetted workspace.
"""

from __future__ import annotations

import difflib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_TEXT_EXTS = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".sh", ".js", ".ts", ".tsx", ".html", ".css"}


def _terms(goal: str) -> set[str]:
    import re

    return {term for term in re.split(r"[^a-z0-9]+", (goal or "").lower()) if len(term) >= 4}


def _is_auth_reset_goal(goal: str) -> bool:
    terms = _terms(goal)
    return bool({"auth", "admin", "password", "reset", "login"} & terms) and bool({"script", "utility", "reset"} & terms)


def _inside_base(base: Path, path: Path) -> bool:
    try:
        return os.path.commonpath([str(base), str(path)]) == str(base)
    except Exception:
        return False


def _safe_target(base: Path, rel: str) -> Path:
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError(f"Unsafe patch path: {rel}")
    target = (base / rel).resolve()
    if not _inside_base(base, target):
        raise ValueError(f"Patch path escapes workspace: {rel}")
    if target.suffix.lower() not in _TEXT_EXTS:
        raise ValueError(f"Unsupported patch file type: {rel}")
    return target


def _script_content() -> str:
    return r'''#!/usr/bin/env python3
"""Reset an Odysseus admin password from inside the container.

Usage examples:
  python scripts/reset-admin-password.py admin --password 'new-password'
  python scripts/reset-admin-password.py admin --prompt
  printf '%s\n' 'new-password' | python scripts/reset-admin-password.py admin --stdin
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.auth import AuthManager, RESERVED_USERNAMES, _hash_password  # noqa: E402
from src.constants import AUTH_FILE, PASSWORD_MIN_LENGTH  # noqa: E402


def reset_admin_password(username: str, password: str, auth_file: str = AUTH_FILE) -> dict:
    username = (username or "").strip().lower()
    if not username:
        raise ValueError("Username is required")
    if username in RESERVED_USERNAMES:
        raise ValueError(f"Username {username!r} is reserved and cannot be reset")
    if not password:
        raise ValueError("Password must not be blank")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")

    auth = AuthManager(str(auth_file))
    if not auth.is_configured:
        raise ValueError(f"Auth config is not configured or was not found at {auth_file}")
    user = auth.users.get(username)
    if not user:
        raise ValueError(f"User {username!r} does not exist")
    if not user.get("is_admin"):
        raise ValueError(f"User {username!r} is not an admin account")

    with auth._config_lock:  # Use AuthManager's existing atomic persistence path.
        auth._config.setdefault("users", {})[username]["password_hash"] = _hash_password(password)
        auth._save()
    revoked = auth.revoke_user_sessions(username)
    return {"username": username, "auth_file": str(auth_file), "revoked_sessions": revoked}


def _read_password(args: argparse.Namespace) -> str:
    provided = [bool(args.password), bool(args.stdin), bool(args.prompt)]
    if sum(provided) > 1:
        raise ValueError("Choose only one password input mode: --password, --stdin, or --prompt")
    if args.password is not None:
        return args.password
    if args.stdin:
        return sys.stdin.readline().rstrip("\n")
    return getpass.getpass("New admin password: ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely reset an existing Odysseus admin password.")
    parser.add_argument("username", help="Existing admin username to reset")
    parser.add_argument("--password", help="New password. Prefer --prompt or --stdin on shared terminals.")
    parser.add_argument("--stdin", action="store_true", help="Read the new password from stdin")
    parser.add_argument("--prompt", action="store_true", help="Prompt interactively for the new password")
    parser.add_argument("--auth-file", default=AUTH_FILE, help=f"Auth file path. Default: {AUTH_FILE}")
    args = parser.parse_args(argv)

    try:
        password = _read_password(args)
        result = reset_admin_password(args.username, password, args.auth_file)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Password reset for admin user '{result['username']}'.")
    print(f"Auth file: {result['auth_file']}")
    print(f"Revoked sessions: {result['revoked_sessions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _test_content() -> str:
    return r'''import importlib.util
from pathlib import Path

from core.auth import AuthManager
from src.constants import PASSWORD_MIN_LENGTH


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "reset-admin-password.py"


def load_script():
    spec = importlib.util.spec_from_file_location("reset_admin_password_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reset_admin_password_rejects_blank_password(tmp_path):
    module = load_script()
    auth_file = tmp_path / "auth.json"
    auth = AuthManager(str(auth_file))
    assert auth.setup("admin", "initial-password")

    try:
        module.reset_admin_password("admin", "", str(auth_file))
    except ValueError as exc:
        assert "blank" in str(exc).lower()
    else:
        raise AssertionError("blank password was accepted")


def test_reset_admin_password_updates_existing_admin(tmp_path):
    module = load_script()
    auth_file = tmp_path / "auth.json"
    auth = AuthManager(str(auth_file))
    assert auth.setup("admin", "initial-password")
    new_password = "x" * max(PASSWORD_MIN_LENGTH, 12)

    result = module.reset_admin_password("admin", new_password, str(auth_file))
    updated = AuthManager(str(auth_file))

    assert result["username"] == "admin"
    assert updated.verify_password("admin", new_password)
    assert updated.is_admin("admin")
'''


def _docs_content() -> str:
    return """# Admin password reset

Use `scripts/reset-admin-password.py` from inside the Odysseus container when an existing admin password must be reset without deleting `auth.json`.

Examples:

```bash
python scripts/reset-admin-password.py admin --prompt
python scripts/reset-admin-password.py admin --password 'new-password'
printf '%s\n' 'new-password' | python scripts/reset-admin-password.py admin --stdin
```

The script uses the existing Odysseus `AuthManager`, preserves the current auth configuration, rejects blank/short passwords, updates only the named admin account, and revokes that user's active sessions.
"""


def _operation(path: str, content: str) -> dict[str, Any]:
    return {"action": "create_or_replace", "path": path, "content": content}


def build_patch_proposal(scaffold: dict[str, Any]) -> dict[str, Any]:
    goal = scaffold.get("user_goal") or ""
    if not _is_auth_reset_goal(goal):
        content = (
            "# Patch proposal\n\n"
            "This goal is source-aware but does not have a safe deterministic patch generator yet.\n"
            "Review the scaffold, source context, and implementation plan before requesting manual patch generation.\n"
        )
        return {"content": content, "metadata": {"can_apply": False, "reason": "unsupported_goal", "operations": []}}

    operations = [
        _operation("scripts/reset-admin-password.py", _script_content()),
        _operation("tests/test_reset_admin_password_script.py", _test_content()),
        _operation("docs/admin-password-reset.md", _docs_content()),
    ]
    patch = render_unified_diff(scaffold.get("workspace_path"), operations)
    content = (
        "# Patch proposal\n\n"
        "Creates a safe admin password reset utility, focused tests, and usage docs.\n\n"
        "## Files\n"
        + "".join(f"- `{op['path']}`\n" for op in operations)
        + "\n## Unified diff\n\n```diff\n"
        + patch
        + "\n```\n"
    )
    return {"content": content, "metadata": {"can_apply": True, "approved": False, "operations": operations, "operation_count": len(operations)}}


def render_unified_diff(workspace: str | None, operations: list[dict[str, Any]]) -> str:
    base = Path(workspace).resolve() if workspace else None
    chunks: list[str] = []
    for op in operations:
        rel = op["path"]
        new = (op.get("content") or "").splitlines(keepends=True)
        old: list[str] = []
        if base:
            try:
                target = _safe_target(base, rel)
                if target.exists():
                    old = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            except Exception:
                old = []
        chunks.extend(difflib.unified_diff(old, new, fromfile=f"a/{rel}", tofile=f"b/{rel}"))
    return "".join(chunks)


def approve_patch_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    if not metadata.get("can_apply"):
        raise ValueError("Patch proposal cannot be applied for this goal")
    out = dict(metadata)
    out["approved"] = True
    out["approved_at"] = datetime.now(timezone.utc).isoformat()
    return out


def apply_operations(workspace: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
    base = Path(workspace).resolve()
    changed: list[dict[str, Any]] = []
    backup_root = base / ".agentic-coding" / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for op in operations:
        action = op.get("action")
        rel = op.get("path") or ""
        if action != "create_or_replace":
            raise ValueError(f"Unsupported patch action: {action}")
        target = _safe_target(base, rel)
        previous = None
        existed = target.exists()
        if existed:
            previous = target.read_text(encoding="utf-8", errors="replace")
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(previous, encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(op.get("content") or "", encoding="utf-8")
        if target.name.endswith(".py") or target.name.endswith(".sh"):
            try:
                mode = target.stat().st_mode
                target.chmod(mode | 0o755)
            except Exception:
                pass
        changed.append({"path": rel, "action": action, "existed": existed})
    return {"changed": changed, "backup_dir": str(backup_root.relative_to(base)) if backup_root.exists() else None}
