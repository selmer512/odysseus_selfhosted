from sqlalchemy import Column, MetaData, String, Table, create_engine

from src.agentic_coding import storage


def test_agentic_coding_store_round_trips_sql(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    workspaces = Table(
        "agentic_coding_workspaces",
        metadata,
        Column("id", String, primary_key=True),
        Column("owner", String),
        Column("created_at", String),
        Column("updated_at", String),
        Column("title", String),
        Column("path", String),
        Column("is_active", String),
    )
    metadata.create_all(engine)
    monkeypatch.setattr(storage, "engine", engine)
    monkeypatch.setattr(storage, "table_registry", lambda: {"workspaces": workspaces})

    store = storage.AgenticCodingStore()
    row = store.add_row("workspaces", "owner-1", title="Repo", path="/repo", is_active=True)

    assert store.get_row("workspaces", row["id"], "owner-1")["title"] == "Repo"
    updated = store.update_row("workspaces", row["id"], "owner-1", title="Repo Updated")
    assert updated["title"] == "Repo Updated"
    assert store.list_rows("workspaces", "owner-1", title="Repo Updated")
