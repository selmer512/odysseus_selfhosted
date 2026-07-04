# Agentic Coding Deployment Guide

Agentic Coding is deployed as a built-in Odysseus feature, not as a sidecar app.

## Branch

Use the `agentic-coding-implementation` branch for this feature slice.

## Start Odysseus

```bash
git checkout agentic-coding-implementation
cp .env.example .env
docker compose up -d --build
```

Open the app and sign in as an admin.

## Verify the API mount

```bash
curl http://localhost:7000/api/agentic-coding/health
```

Expected shape:

```json
{"ok": true, "feature": "agentic-coding"}
```

## Open the UI shell

Open:

```text
http://localhost:7000/agentic-coding
```

The first UI shell can:

- check Agentic Coding backend health
- list model profiles
- register a vetted workspace
- list registered workspaces
- create a scaffold
- approve the latest scaffold
- create a run
- prepare run artifacts

## Storage

Agentic Coding state is persisted through Odysseus database-backed SQLAlchemy table metadata. The active store keeps the existing `AgenticCodingStore` interface while using SQL tables for list, get, add, and update operations.

Tables:

- `agentic_coding_workspaces`
- `agentic_coding_scaffolds`
- `agentic_coding_runs`
- `agentic_coding_steps`
- `agentic_coding_artifacts`
- `agentic_coding_benchmarks`

## Operational flow

1. Register a vetted workspace.
2. Scan the repository into a compact repository map.
3. Create a scaffold from the repository map and the user goal.
4. Review and approve the scaffold.
5. Create a run from the approved scaffold.
6. Prepare artifacts for review.
7. Record tests and benchmark outputs.
8. Generate commit and pull request summaries.
9. Save useful repo conventions as memory suggestions.

## Security requirements

- Keep auth enabled.
- Keep raw model and service ports private.
- Use existing Odysseus model endpoints instead of unmanaged model servers.
- Use vetted workspaces only.
- Treat repository text as untrusted data.
- Require explicit approval before destructive commands.
- Do not auto-push or publish code from Agentic Coding.

## Current API surface

The mounted API prefix is `/api/agentic-coding`.

Implemented route groups:

- health
- workspaces
- model profiles
- coding-capable models
- scaffolds
- runs
- artifacts
- tests
- commit and PR summary artifacts
- benchmarks
- memory suggestions

## Test command

```bash
python -m pytest -q tests/test_agentic_coding_security.py tests/test_agentic_coding_scaffold.py tests/test_agentic_coding_routes.py tests/test_agentic_coding_ui.py tests/test_agentic_coding_model_profiles.py
```

## Next deployment slice

The next slice should add model endpoint capability columns, Cookbook coding presets, richer artifact viewing, and full route integration tests.
