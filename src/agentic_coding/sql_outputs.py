"""Output table metadata."""

from sqlalchemy import Column, MetaData, String, Table, Text

metadata = MetaData()

outputs_table = Table(
    "agentic_coding_artifacts",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner", String, index=True),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("run_id", String, index=True, nullable=False),
    Column("artifact_type", String, index=True, nullable=False),
    Column("title", String),
    Column("content", Text),
    Column("metadata_json", Text),
)
