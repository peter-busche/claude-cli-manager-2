# performance-auditor — gotchas under time pressure

Hard-won traps that are easy to miss when the clock is running:

- An index finding is only valid if it **matches the actual filter/order column AND
  direction** — a composite index in the wrong column order won't be used. Verify before
  flagging.
- The classic N+1 hides in **serializers**, not just explicit loops — walking
  `obj.relationship` while building a response is the same O(N) blow-up.
- `expire_on_commit=True` (the default) causes a surprise re-fetch when attributes are
  read after `commit()` — looks like a mystery N+1. Suspect it when queries spike post-commit.
- Quantify before flagging: "1 + N queries per N rows" is a finding; "this looks slow" is not.
- Confirm the path is actually **hot** (a list/read endpoint per request) — a one-time
  startup cost is rarely worth a finding under a 90-minute clock.

The full checklist lives in `.claude/conventions/audit/performance.md` (travels via bootstrap).
This file holds only the reminders; keep it short.
