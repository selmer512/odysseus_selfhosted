# Agentic Coding Stack

Agentic Coding is a review-first workflow for repository-aware coding inside Odysseus. It uses vetted workspaces, structured scaffolds, explicit approval, run history, and generated artifacts such as repository maps, test plans, commit message drafts, and pull request summary drafts.

## First slice in this branch

This branch adds the bounded backend package under `src/agentic_coding/` and mounts a health route at `/api/agentic-coding/health` through the existing companion route wrapper. The implementation is additive so it can be tested without changing the main app orchestrator.

The first slice includes:

- command risk classification
- untrusted repository context wrapping
- JSON-backed local feature storage
- workspace and scaffold services
- run artifact preparation helpers
- focused unit tests
- focused GitHub Actions workflow

## Intended workflow

1. Register a vetted workspace.
2. Scan the repository into a compact map.
3. Generate a scaffold from the map and the user goal.
4. Review the scaffold before any execution.
5. Approve the scaffold.
6. Create a run from the approved scaffold.
7. Prepare artifacts for review.
8. Run focused tests.
9. Commit, push, and open a pull request only through an explicit user-approved publishing workflow.

## Safety model

Repository text is treated as untrusted data. The system wraps repository-derived context so the model should inspect it, not obey instructions embedded inside it.

High-risk commands are classified separately from low-risk inspection and moderate-risk test commands. Destructive actions must require explicit approval before execution.

## Remaining expansion

The next patch should replace the JSON-backed first-slice store with database-backed tables, expose the full route surface, add model coding capability metadata, connect tool schemas, add frontend controls, and add Cookbook coding presets.
