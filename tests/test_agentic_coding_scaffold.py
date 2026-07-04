from src.agentic_coding.scaffold_service import build_scaffold


def test_build_scaffold_is_review_first():
    scaffold = build_scaffold("Add the feature", {"important_files": ["app.py"]})

    assert scaffold["likely_files"] == ["app.py"]
    assert any("approval" in item.lower() for item in scaffold["implementation_plan"])
    assert scaffold["rollback_plan"]
