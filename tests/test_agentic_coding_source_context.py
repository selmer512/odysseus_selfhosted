import pytest

from src.agentic_coding.scaffold_service import ScaffoldService
from src.agentic_coding.source_context import summarize_file, summarize_likely_files
from src.agentic_coding.storage import now_iso


class MemoryStore:
    def __init__(self):
        self.rows = {"workspaces": [], "scaffolds": []}

    def list_rows(self, collection, owner=None, **filters):
        rows = list(self.rows.get(collection, []))
        for key, value in filters.items():
            rows = [row for row in rows if row.get(key) == value]
        return rows

    def get_row(self, collection, row_id, owner=None):
        for row in self.rows[collection]:
            if row["id"] == row_id:
                return row
        raise KeyError(row_id)

    def add_row(self, collection, owner=None, **fields):
        row = {"id": f"{collection}-{len(self.rows[collection])}", "owner": owner, "created_at": now_iso(), "updated_at": now_iso(), **fields}
        self.rows[collection].append(row)
        return row

    def update_row(self, collection, row_id, owner=None, **fields):
        row = self.get_row(collection, row_id, owner)
        row.update(fields)
        return row


def test_source_context_extracts_python_symbols(tmp_path):
    auth = tmp_path / "core"
    auth.mkdir()
    (auth / "auth.py").write_text(
        "import json\n"
        "from passlib.context import CryptContext\n\n"
        "class AuthManager:\n    pass\n\n"
        "def hash_password(password):\n    return password\n",
        encoding="utf-8",
    )

    summary = summarize_file(str(tmp_path), "core/auth.py")

    assert summary["path"] == "core/auth.py"
    assert "json" in summary["symbols"]["imports"]
    assert {item["name"] for item in summary["symbols"]["classes"]} == {"AuthManager"}
    assert {item["name"] for item in summary["symbols"]["functions"]} == {"hash_password"}


def test_source_context_rejects_path_traversal(tmp_path):
    assert summarize_file(str(tmp_path), "../outside.py") is None
    assert summarize_likely_files(str(tmp_path), ["../outside.py"])["count"] == 0


@pytest.mark.asyncio
async def test_scaffold_generation_attaches_source_context(tmp_path, monkeypatch):
    (tmp_path / "core").mkdir()
    (tmp_path / "routes").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "core" / "auth.py").write_text("def hash_password(password):\n    return password\n", encoding="utf-8")
    (tmp_path / "routes" / "auth_routes.py").write_text("def login():\n    pass\n", encoding="utf-8")
    (tmp_path / "scripts" / "reset-admin-password.py").write_text("# planned\n", encoding="utf-8")
    monkeypatch.setattr("src.agentic_coding.scaffold_service.vet_workspace", lambda path: str(tmp_path))

    service = ScaffoldService(MemoryStore())
    workspace = service.create_workspace("admin", str(tmp_path), "fixture")
    scaffold = await service.generate_scaffold("admin", workspace["id"], "Add admin password reset script")

    context = scaffold["metadata"]["source_context"]
    paths = [item["path"] for item in context["files"]]

    assert context["count"] >= 2
    assert "core/auth.py" in paths
    assert any("source-aware" in item.lower() or "auth storage" in item.lower() for item in scaffold["implementation_plan"])
