# security-auditor — gotchas under time pressure

Hard-won traps that are easy to miss when the clock is running:

- The highest-value security bug in a gRPC service is usually the **auth interceptor that
  exists but doesn't enforce** (reads the token, never verifies it / always returns True).
  Check enforcement, not just presence.
- After proposing a SQL-parameterization fix, remind the developer to **re-run tests** —
  bound params can subtly change results/plans vs. a string-built query.
- An empty/default secret (`getenv("X", "")`) is a CRITICAL finding, not a nit: the app
  boots and signs forgeable tokens. Validate-at-boot is the fix.
- `if request.field:` is a security bug when `0`/`""` are valid — proto scalar defaults.
  Use `HasField()`.
- Don't flag CORS `*` as critical unless `allow_credentials=True` — wildcard alone on a
  public, non-credentialed API may be intended.

The full checklist lives in `.claude/conventions/audit/security.md` (travels via bootstrap).
This file holds only the reminders; keep it short.
