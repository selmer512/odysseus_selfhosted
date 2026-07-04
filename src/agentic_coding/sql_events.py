"""Step table metadata."""

from sqlalchemy import Column, MetaData, String, Table, Text

metadata = MetaData()

events_table = Table(
    "agentic_coding_steps",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("run_id", String, index=True, nullable=False),
    Column("step_type", String),
    Column("status", String),
    Column("title", String),
    Column("content", Text),
)
