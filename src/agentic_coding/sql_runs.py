"""Agentic Coding run table metadata."""

from sqlalchemy import Column, MetaData, String, Table, Text

metadata = MetaData()

runs_table = Table(
    "agentic_coding_runs",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("workspace_id", String, index=True, nullable=False),
    Column("scaffold_id", String, index=True, nullable=False),
    Column("status", String, default="pending"),
    Column("summary", Text),
)
