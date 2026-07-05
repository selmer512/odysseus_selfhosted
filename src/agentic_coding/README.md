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
8. Prepare review artifacts.

## Source-aware scaffolds

The scaffold generator now performs two passes:

- Repository routing: scans first-class Odysseus areas such as `core/`, `src/`, `routes/`, `scripts/`, `tests/`, `docs/`, `companion/`, `.github/`, and `static/`.
- Source context: safely reads the top likely files inside the vetted workspace and extracts imports, functions, classes, route decorators, line counts, and short previews.

The source context is stored under `scaffold.metadata.source_context` and emitted as a `source_context` review artifact during run preparation.

## Safety notes

- Source files are treated as untrusted repository data.
- Path traversal outside the vetted workspace is rejected.
- Only known text/code file extensions are summarized.
- Reading is byte-limited and preview-limited.
- Patch execution remains behind the next explicit approval slice.
