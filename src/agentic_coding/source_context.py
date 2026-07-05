"""Source-aware context extraction for Agentic Coding scaffolds."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

_MAX_FILES = 10
_MAX_BYTES = 80_000
_MAX_PREVIEW_LINES = 80
_TEXT_EXTS = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".sh", ".js", ".ts", ".tsx", ".html", ".css"}


def _inside_base(base: Path, path: Path) -> bool:
    try:
        return os.path.commonpath([str(base), str(path)]) == str(base)
    except Exception:
        return False


def _safe_path(base: Path, rel: str) -> Path | None:
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return None
    candidate = (base / rel).resolve()
    if not _inside_base(base, candidate):
        return None
    if not candidate.is_file():
        return None
    if candidate.suffix.lower() not in _TEXT_EXTS:
        return None
    return candidate


def _read_preview(path: Path) -> tuple[str, int, bool]:
    raw = path.read_bytes()[:_MAX_BYTES + 1]
    truncated = len(raw) > _MAX_BYTES
    if truncated:
        raw = raw[:_MAX_BYTES]
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    preview = "\n".join(lines[:_MAX_PREVIEW_LINES])
    return preview, len(lines), truncated or len(lines) > _MAX_PREVIEW_LINES


def _python_symbols(text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"parse_error": str(exc), "imports": [], "functions": [], "classes": [], "routes": []}
    imports: list[str] = []
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names[:8])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.extend(f"{module}.{alias.name}" if module else alias.name for alias in node.names[:8])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = [_decorator_name(d) for d in node.decorator_list]
            item = {"name": node.name, "line": node.lineno, "decorators": [d for d in decorators if d]}
            functions.append(item)
            route_decorators = [d for d in item["decorators"] if any(method in d.lower() for method in (".get", ".post", ".put", ".patch", ".delete"))]
            if route_decorators:
                routes.append({"name": node.name, "line": node.lineno, "decorators": route_decorators})
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
    return {"imports": sorted(set(imports))[:30], "functions": functions[:40], "classes": classes[:30], "routes": routes[:30]}


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ""


def _js_symbols(text: str) -> dict[str, Any]:
    functions = re.findall(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", text)
    classes = re.findall(r"(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", text)
    imports = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", text)
    return {"imports": sorted(set(imports))[:30], "functions": sorted(set(functions))[:40], "classes": sorted(set(classes))[:30], "routes": []}


def summarize_file(workspace: str, rel: str) -> dict[str, Any] | None:
    base = Path(workspace).resolve()
    path = _safe_path(base, rel)
    if not path:
        return None
    preview, line_count, truncated = _read_preview(path)
    suffix = path.suffix.lower()
    symbols = _python_symbols(preview) if suffix == ".py" else (_js_symbols(preview) if suffix in {".js", ".ts", ".tsx"} else {})
    return {
        "path": rel,
        "line_count": line_count,
        "truncated": truncated,
        "symbols": symbols,
        "preview": preview,
    }


def summarize_likely_files(workspace: str, likely_files: list[str], limit: int = _MAX_FILES) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    skipped: list[str] = []
    for rel in likely_files[:limit]:
        summary = summarize_file(workspace, rel)
        if summary:
            summaries.append(summary)
        else:
            skipped.append(rel)
    return {"files": summaries, "skipped": skipped, "count": len(summaries)}


def context_bullets(source_context: dict[str, Any]) -> list[str]:
    bullets: list[str] = []
    for item in source_context.get("files", [])[:8]:
        symbols = item.get("symbols") or {}
        names: list[str] = []
        names.extend(f"class {cls.get('name')}" for cls in symbols.get("classes", [])[:3] if cls.get("name"))
        names.extend(f"function {fn.get('name')}" for fn in symbols.get("functions", [])[:5] if fn.get("name"))
        if names:
            bullets.append(f"{item.get('path')}: " + ", ".join(names[:6]))
        else:
            bullets.append(f"{item.get('path')}: inspect file content and nearby callers")
    return bullets
