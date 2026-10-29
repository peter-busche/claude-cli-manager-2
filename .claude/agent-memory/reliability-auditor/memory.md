# reliability-auditor — gotchas under time pressure

Hard-won traps that are easy to miss when the clock is running:

- A `NOT NULL` / `nullable=False` migration column **needs a `server_default` (or a
  nullable→backfill→enforce sequence)** or it fails on existing prod rows. This is the
  migration finding interviewers look for — and the fix is a phased migration, not one-shot.
- Tests using `create_all()` instead of running migrations is a CRITICAL reliability gap:
  the migration path is never exercised, so it only breaks in production.
- Swallowed exceptions that **return success** (empty value / False / log-and-continue)
  are silent data loss — worse than a crash. Trace whether the caller believes it succeeded.
- For races, look for **read-then-write** (counter/balance/check-then-create). The tell is
  no `with_for_update()`, no version column, no unique constraint.
- "All errors become gRPC `UNKNOWN`" is real: callers can't tell retryable from fatal.
  Worth a finding even though it's not data loss.

The full checklist lives in `.claude/conventions/audit/reliability.md` (travels via bootstrap).
This file holds only the reminders; keep it short.
