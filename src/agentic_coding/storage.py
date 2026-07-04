"""Agentic Coding storage."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.constants import DATA_DIR

STORE_PATH = Path(DATA_DIR) / "agentic_coding.json"
COLLECTIONS = ("workspaces", "scaffolds", "runs", "steps", "artifacts", "benchmarks")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_store() -> dict:
    if STORE_PATH.exists():
        try:
            with STORE_PATH.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = {}
    else:
        data = {}
    for key in COLLECTIONS:
        data.setdefault(key, [])
    return data


def save_store(data: dict) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
    tmp.replace(STORE_PATH)


def visible(owner: str | None, row: dict) -> bool:
    return not owner or row.get("owner") in (None, owner)


def new_row(owner: str | None, **fields) -> dict:
    ts = now_iso()
    return {"id": str(uuid.uuid4()), "owner": owner, "created_at": ts, "updated_at": ts, **fields}


class AgenticCodingStore:
    def list_rows(self, collection: str, owner: str | None = None, **filters) -> list[dict]:
        rows = [row for row in load_store()[collection] if visible(owner, row)]
        for key, value in filters.items():
            if value is not None:
                rows = [row for row in rows if row.get(key) == value]
        return rows

    def get_row(self, collection: str, row_id: str, owner: str | None = None) -> dict:
        for row in load_store()[collection]:
            if row.get("id") == row_id and visible(owner, row):
                return row
        raise KeyError(f"{collection} row not found")

    def add_row(self, collection: str, owner: str | None = None, **fields) -> dict:
        data = load_store()
        row = new_row(owner, **fields)
        data[collection].append(row)
        save_store(data)
        return row

    def update_row(self, collection: str, row_id: str, owner: str | None = None, **fields) -> dict:
        data = load_store()
        for row in data[collection]:
            if row.get("id") == row_id and visible(owner, row):
                row.update(fields)
                row["updated_at"] = now_iso()
                save_store(data)
                return row
        raise KeyError(f"{collection} row not found")
