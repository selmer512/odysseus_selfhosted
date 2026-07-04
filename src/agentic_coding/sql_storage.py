"""SQL-backed Agentic Coding storage adapter."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Column, MetaData, String, Table, Text

from core.database import engine


metadata = MetaData()

workspaces_table = Table(
    "agentic_coding_workspaces",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("title", String),
    Column("path", String, nullable=False),
    Column("is_active", String, default="true"),
)

scaffolds_table = Table(
    "agentic_coding_scaffolds",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("workspace_id", String, index=True, nullable=False),
    Column("session_id", String),
    Column("endpoint_id", String),
    Column("model", String),
    Column("status", String, default="draft"),
    Column("title", String),
    Column("user_goal", Text, nullable=False),
    Column("repo_map", Text),
    Column("likely_files", Text),
    Column("inspection_commands", Text),
    Column("implementation_plan", Text),
    Column("test_plan", Text),
    Column("rollback_plan", Text),
    Column("risk_notes", Text),
    Column("metadata_json", Text),
)
