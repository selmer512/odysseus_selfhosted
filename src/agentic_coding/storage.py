"""Agentic Coding storage."""

from __future__ import annotations

import importlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from core.database import engine
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


def table_registry():
    module = importlib.import_module("src.agentic_coding.sql_adapter")
    getattr(module, "AgenticCodingSqlStore")()
    return module.TABLES


def sql_rows(collection: str) -> list[dict]:
    table = table_registry()[collection]
    module = importlib.import_module("src.agentic_coding.sql_adapter")
    with engine.connect() as conn:
        rows = conn.execute(select(table)).mappings().all()
    return [getattr(module, "_decode")(dict(row)) for row in rows]


class AgenticCodingStore:
    def __init__(self) -> None:
        table_registry()

    def list_rows(self, collection: str, owner: str | None = None, **filters) -> list[dict]:
        rows = [row for row in sql_rows(collection) if visible(owner, row)]
        for key, value in filters.items():
            if value is not None:
                rows = [row for row in rows if row.get(key) == value]
        return rows

    def get_row(self, collection: str, row_id: str, owner: str | None = None) -> dict:
        for row in self.list_rows(collection, owner):
            if row.get("id") == row_id:
                return row
        raise KeyError(f"{collection} row not found")

    def add_row(self, collection: str, owner: str | None = None, **fields) -> dict:
        row = new_row(owner, **fields)
        table = table_registry()[collection]
        module = importlib.import_module("src.agentic_coding.sql_adapter")
        payload = getattr(module, "_encode")(row)
        payload = {key: value for key, value in payload.items() if key in table.c}
        with engine.begin() as conn:
            conn.execute(table.insert().values(**payload))
        return row

    def update_row(self, collection: str, row_id: str, owner: str | None = None, **fields) -> dict:
        existing = self.get_row(collection, row_id, owner)
        existing.update(fields)
        existing["updated_at"] = now_iso()
        table = table_registry()[collection]
        module = importlib.import_module("src.agentic_coding.sql_adapter")
        payload = getattr(module, "_encode")(existing)
        payload = {key: value for key, value in payload.items() if key in table.c}
        with engine.begin() as conn:
            conn.execute(table.update().where(table.c.id == row_id).values(**payload))
        return self.get_row(collection, row_id, owner)
