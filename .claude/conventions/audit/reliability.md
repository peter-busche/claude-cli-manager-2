# Reliability Audit Checklist

Hunt list for the reliability-auditor. Stack: Python gRPC + SQLAlchemy backend,
TypeScript/React frontend. For each item: what to look for → why it matters → the fix.
Name the concrete failure mode (what state, what's lost) for every finding.

## 1. Missing transaction handling
- **Look for:** multiple `session.add`/writes across a logical operation with no
  surrounding transaction; commits without a `try/except` + `rollback`; partial writes
  that can succeed independently.
- **Why:** a failure mid-operation leaves the DB in an inconsistent state (some rows
  written, some not) with no recovery.
- **Fix:** wrap the unit of work in `with session.begin():` (or explicit
  commit/rollback) so it's all-or-nothing.

## 2. Race conditions / lost updates
- **Look for:** read-modify-write without locking — e.g. read a balance/counter, compute,
  write back; check-then-act (`if not exists: create`); no `with_for_update()` or
  version column.
- **Why:** concurrent callers interleave → lost updates, double-creates, oversold
  inventory.
- **Fix:** `SELECT ... FOR UPDATE` (`with_for_update()`), optimistic locking
  (`version_id_col`), or a DB unique constraint + upsert.

## 3. Swallowed exceptions
- **Look for:** `except: pass`, `except Exception: log.warning(...)` then continue,
  broad catches that hide failures, returning a success/empty value on error.
- **Why:** failures vanish silently; callers believe work succeeded → silent data loss
  and undiagnosable bugs.
- **Fix:** catch narrowly, handle or re-raise; never report success on a failed write.

## 4. gRPC error mapping & deadlines
- **Look for:** all errors surfacing as `UNKNOWN`; exceptions leaking raw; no mapping
  from domain errors to status codes; client stubs with no deadline.
- **Why:** callers can't distinguish retryable from fatal; missing deadlines cause hangs
  and cascading failures.
- **Fix:** map exceptions to specific `grpc.StatusCode` (`NOT_FOUND`, `INVALID_ARGUMENT`,
  `ALREADY_EXISTS`, ...); set deadlines on calls; consider health checks.

## 5. Migration safety
- **Look for:** Alembic migrations adding a `NOT NULL` / `nullable=False` column with no
  `server_default`; type changes that rewrite/lock large tables; data migrations with no
  backfill; tests using `create_all()` instead of running migrations.
- **Why:** a `NOT NULL` add fails on existing rows in production; `create_all()` means
  the migration path is never exercised → prod-only failures.
- **Fix:** add nullable + `server_default`, backfill, then enforce `NOT NULL` in a later
  step; run migrations in CI/test setup, not `create_all()`.

## 6. Idempotency & retries
- **Look for:** non-idempotent mutations that can be double-submitted (no idempotency
  key/dedup); external calls with no retry/timeout; at-least-once delivery assumed
  exactly-once.
- **Why:** retries or double clicks create duplicate side effects (double charge, double
  insert).
- **Fix:** idempotency keys / natural unique constraints on mutations; bounded retries
  with backoff (`tenacity`) + timeouts on external calls.

## 7. Test isolation
- **Look for:** tests sharing a module-level session/DB and leaving dirty state; tests
  that depend on execution order; fixtures doing real network/DB calls; no rollback/
  teardown between tests.
- **Why:** flaky, order-dependent suites; passing tests that mask real breakage.
- **Fix:** transaction-per-test that rolls back on teardown; isolated fixtures; mock
  external I/O.

## 8. React error boundaries & effects
- **Look for:** async data-fetching components with no error boundary; `useEffect`
  promises with no `.catch`; unhandled rejections; setState after unmount.
- **Why:** one failed fetch blanks/crashes the UI with no recovery; noisy console
  rejections hide real errors.
- **Fix:** wrap async subtrees in an `ErrorBoundary`; `.catch` (or try/catch in async
  effects); guard against unmounted updates.

## Severity guide
CRITICAL = silent data loss/corruption, or a migration that fails on prod data.
HIGH = inconsistent state on failure, lost updates, masked errors. MEDIUM = recoverable
but incorrect / flaky tests. LOW = robustness gap. Diagnose only — hand the fix to the
developer.
