Map this unfamiliar repository fast, then stop. This is read-only orientation —
no code changes. Launch Explore subagents IN PARALLEL (one per area below) and
synthesize their findings into one short brief; do not read every file yourself.

The goal is to know the architecture, the data flow, and EXACTLY how to build and
test before any auditing or fixing begins.

## Architecture & data flow
<!-- components and how they fit; the request path end to end:
     client (React/TS) -> gRPC service -> SQLAlchemy/ORM -> DB.
     Note the moon project graph (moon query projects) and where each project lives. -->

## Build & test commands (EXACT — these get pinned at the top of FINDINGS.md)
<!-- the precise commands for:
     - backend unit tests
     - E2E tests
     - lint + type-check (ruff / mypy / eslint / tsc --noEmit, if present)
     - the moon targets that run them (moon ci, moon check, moon run <project>:<task>)
     Capture how to run ONE test file/case too — you'll want the fast loop while fixing. -->

## Test & migration infrastructure
<!-- how tests get a DB and fixtures; transaction isolation per test?
     Are Alembic migrations run, or is create_all() used? Where do fixtures live? -->

## Risk surface (where to point the auditors next)
<!-- name concrete files/dirs: ORM query sites, the gRPC service impl + any interceptors,
     migrations dir, auth/secrets/config loading, moon.yml task graph, CI config.
     Cite file:line for anything notable. -->

## Constraints
- Read-only recon. Do not modify code or config.
- Confirm the test baseline is GREEN and record the exact commands to reproduce it.
- Keep the brief lean — bullets and file:line refs, no prose padding.
