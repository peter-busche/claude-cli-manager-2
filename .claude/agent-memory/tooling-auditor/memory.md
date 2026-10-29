# tooling-auditor — gotchas under time pressure

Hard-won traps that are easy to miss when the clock is running:

- In moon, **declaring `outputs` is what makes caching work** — a task with no `outputs`
  silently rebuilds every time and looks fine. Missing `outputs`/`inputs` is the highest-
  value tooling finding, and it's invisible unless you read `moon.yml`.
- Missing `deps` shows up as flaky ordering (frontend builds before gRPC stub codegen).
  Trace cross-project dependencies, not just same-project ones.
- "CI runs tests but no lint/type-check" is a CRITICAL-class gap: a whole category of
  breakage ships undetected. Check the CI workflow, not just that tests exist.
- `command` supports task-inheritance merging; `script` does not — flag a `script` used
  where inheritance was clearly intended.
- Confirm the project hasn't **deliberately** chosen a pattern before flagging it (read
  CLAUDE.md/README first) — tooling findings are the easiest to false-positive on style.

The full checklist lives in `.claude/conventions/audit/tooling.md` (travels via bootstrap).
This file holds only the reminders; keep it short.
