from src.agentic_coding.scaffold_service import build_repo_map, build_scaffold, rank_likely_files


def test_build_scaffold_is_review_first():
    scaffold = build_scaffold("Add the feature", {"important_files": ["app.py"]})

    assert scaffold["likely_files"] == ["app.py"]
    assert any("approval" in item.lower() for item in scaffold["implementation_plan"])
    assert scaffold["rollback_plan"]


def test_build_repo_map_prioritizes_source_over_static_bulk(tmp_path):
    src_dir = tmp_path / "src" / "agentic_coding"
    static_dir = tmp_path / "static" / "js"
    src_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)
    for idx in range(80):
        (static_dir / f"asset_{idx}.js").write_text("console.log('x')", encoding="utf-8")
    (src_dir / "run_service.py").write_text("# source", encoding="utf-8")
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")

    repo_map = build_repo_map(str(tmp_path))

    assert "src/agentic_coding/run_service.py" in repo_map["files"]
    assert "src/agentic_coding/run_service.py" in repo_map["important_files"]


def test_likely_files_rank_agentic_coding_surface_for_agentic_goal():
    repo_map = {
        "important_files": ["src/action_intents.py", "src/agent_loop.py", "src/agentic_coding/run_service.py"],
        "files": ["companion/agentic_coding_ui.py", "static/agentic-coding.js", "tests/test_agentic_coding_artifacts.py"],
    }

    likely = rank_likely_files("Improve Agentic Coding artifacts and workspace UX", repo_map, limit=4)

    assert set(likely[:4]) == {
        "companion/agentic_coding_ui.py",
        "static/agentic-coding.js",
        "tests/test_agentic_coding_artifacts.py",
        "src/agentic_coding/run_service.py",
    }
    assert "src/action_intents.py" not in likely[:4]
