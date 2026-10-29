# Developer-Tooling Audit Checklist

Hunt list for the tooling-auditor. Stack: moonrepo-orchestrated polyglot monorepo
(Python backend + TypeScript/React frontend). For each item: what to look for → why it
matters → the fix. State who it hits and how often (every build / every PR / at scale).

## 1. moon task graph & caching
- **Look for:** `moon.yml` tasks missing `outputs` (caching can't work → silent
  rebuilds), missing `inputs` or globs too broad (unrelated changes bust the cache),
  missing `deps` (a task runs before its prerequisite, e.g. frontend builds before gRPC
  stub codegen).
- **Why:** broken caching wastes every developer's time on every build; missing deps
  cause flaky/ordering build failures.
- **Fix:** declare precise `inputs` (only files that affect the task) and `outputs`
  (artifacts to cache); add cross-project `deps` (e.g. `web` deps `api:codegen`).
  Remember: `command` supports task inheritance merging; `script` does not.

## 2. CI gates
- **Look for:** CI that runs only tests — no lint (`ruff`/`eslint`), no type-check
  (`mypy`/`tsc --noEmit`); no `moon ci` (affected detection) usage; migrations not run
  in CI; no coverage floor.
- **Why:** whole classes of breakage (type errors, lint regressions, migration failures)
  ship undetected; every PR is under-verified.
- **Fix:** add lint + type-check + migration steps as CI gates; prefer `moon ci` for
  affected-only, parallel, continue-on-failure runs.

## 3. Dependency hygiene
- **Look for:** prod and dev deps not separated; loose ranges (`*`, unpinned) in
  `package.json`/`requirements.txt`; lockfile missing or stale; conflicting versions
  across monorepo packages; pnpm workspace `*` ranges.
- **Why:** non-reproducible builds; "works on my machine"; surprise breakage from a
  transitive bump.
- **Fix:** split prod/dev requirements; pin with a committed lockfile; align shared
  versions across the workspace.

## 4. Logging & observability
- **Look for:** `print(` in backend code instead of `logging`; no log levels/structure;
  no correlation/request id propagated through gRPC metadata; secrets logged.
- **Why:** unstructured logs are unsearchable; no correlation id means no distributed
  tracing across services; print bypasses level/route control.
- **Fix:** stdlib `logging` (or `structlog`) with levels and JSON output; propagate an
  `x-request-id` through metadata; scrub secrets.

## 5. Type annotations & static checks
- **Look for:** public functions with no return types / `Any` everywhere; SQLAlchemy
  models without typed columns (`Mapped[...]`); type-checker not run anywhere.
- **Why:** missing types let avoidable bugs through and erode the safety the stack
  affords; un-run checkers provide false confidence.
- **Fix:** add return types on public functions at minimum; type model columns; wire
  `mypy`/`tsc --noEmit` into the task graph + CI.

## 6. Test quality
- **Look for:** tests asserting on internal implementation details instead of observable
  behavior; only mocked unit tests with no gRPC integration test; fixtures doing real
  network calls; tests that can't run in isolation.
- **Why:** brittle tests break on safe refactors; missing integration coverage means the
  wire contract is untested; real-I/O fixtures are flaky and slow.
- **Fix:** assert behavior/contracts; add at least one real gRPC integration test;
  mock external I/O; make each test independent.

## Severity guide
CRITICAL = CI can't catch a class of breakage, or builds are non-reproducible.
HIGH = broken caching (silent rebuilds/stale) or a missing lint/type gate. MEDIUM =
dependency/logging/test-quality gaps. LOW = ergonomics. Confirm the project hasn't
deliberately chosen a pattern before flagging it. Diagnose only — hand the fix to the
developer.
