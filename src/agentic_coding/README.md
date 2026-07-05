# Agentic Coding

Backend package for the Odysseus-native Agentic Coding workflow.

## Current lifecycle

Agentic Coding is review-first. A normal run follows this sequence:

1. Register a vetted workspace.
2. Generate a scaffold from a user goal.
3. Rank likely files from the repository map.
4. Read and summarize the top safe source files.
5. Store source context in scaffold metadata.
6. Require explicit scaffold approval.
7. Create a run.
8. Prepare source-aware review artifacts.
9. Generate a patch proposal.
10. Require explicit patch approval.
11. Apply the approved patch inside the vetted workspace.

## Source-aware scaffolds

The scaffold generator performs two passes:

- Repository routing: scans first-class Odysseus areas such as `core/`, `src/`, `routes/`, `scripts/`, `tests/`, `docs/`, `companion/`, `.github/`, and `static/`.
- Source context: safely reads the top likely files inside the vetted workspace and extracts imports, functions, classes, route decorators, line counts, and short previews.

The source context is stored under `scaffold.metadata.source_context` and emitted as a `source_context` review artifact during run preparation.

## Patch proposals

Patch generation is explicit and conservative. The current deterministic patch generator supports the admin reset utility scenario and emits three create-or-replace operations:

- `scripts/reset-admin-password.py`
- `tests/test_reset_admin_password_script.py`
- `docs/admin-password-reset.md`

For unsupported goals, Agentic Coding creates a non-applicable patch proposal instead of pretending it can safely write files.

## Safety notes

- Source files are treated as untrusted repository data.
- Path traversal outside the vetted workspace is rejected.
- Only known text/code file extensions are summarized or written.
- Reading is byte-limited and preview-limited.
- Patch application requires explicit patch approval.
- Patch application writes only declared create-or-replace operations inside the vetted workspace.
- Existing files are backed up under `.agentic-coding/backups/` before replacement.
