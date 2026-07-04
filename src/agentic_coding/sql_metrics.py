"""Metric table metadata."""

from sqlalchemy import Column, MetaData, String, Table, Text

metadata = MetaData()

metrics_table = Table(
    "agentic_coding_benchmarks",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("workspace_id", String, index=True),
    Column("endpoint_id", String),
    Column("model", String),
    Column("task", Text, nullable=False),
    Column("status", String, default="recorded"),
    Column("metrics", Text),
    Column("summary", Text),
    Column("metadata_json", Text),
)
