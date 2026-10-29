# Performance Audit Checklist

Hunt list for the performance-auditor. Stack: Python gRPC + SQLAlchemy backend,
TypeScript/React frontend. For each item: what to look for → why it matters → the fix.
Quantify the scaling factor (e.g. "1 + N queries per N rows") for every finding.

## 1. N+1 query patterns (SQLAlchemy)
- **Look for:** accessing a relationship inside a loop without eager loading —
  `for u in users: u.orders`; serializers that walk relationships per row; default
  lazy-load relationships fetched in a list endpoint.
- **Why:** 1 query for the list + 1 per row = O(N) round trips; dominates latency and
  exhausts the DB under load.
- **Fix:** eager-load with `selectinload()` (separate IN query, good for collections) or
  `joinedload()` (single JOIN, good for to-one); select only needed columns.

## 2. Missing indexes
- **Look for:** columns used in `.filter()`, `.order_by()`, join conditions, or as
  foreign keys with no matching `Index(...)`/`index=True` in the model or migration.
- **Why:** full-table scans that grow linearly with table size; slow queries and lock
  contention at scale.
- **Fix:** add an index matching the actual filter/order column AND direction; for
  composite filters, a composite index in the right column order.

## 3. Unbounded queries
- **Look for:** list/search endpoints calling `.all()` with no `.limit()`; loading an
  entire table to count or aggregate in Python; gRPC unary returning unbounded sets.
- **Why:** memory blow-up and latency proportional to table growth; eventual OOM /
  `RESOURCE_EXHAUSTED`.
- **Fix:** enforce pagination (limit + offset, or keyset/cursor for large sets);
  aggregate in SQL; server-stream genuinely large results.

## 4. Blocking calls in async context
- **Look for:** `time.sleep`, blocking `open()`/file I/O, `requests.*`, or synchronous
  SQLAlchemy inside `async def`; CPU-bound work on the event loop.
- **Why:** blocks the whole event loop → all concurrent requests stall, not just one.
- **Fix:** `asyncio.sleep`, async DB/HTTP clients (`AsyncSession`, `httpx`), or offload
  blocking/CPU work to a thread/executor.

## 5. Connection pool & session lifecycle
- **Look for:** `create_engine` or `sessionmaker` called per request/handler; sessions
  never closed; pool size mismatched to concurrency.
- **Why:** new pools per request defeat pooling → connection exhaustion and handshake
  overhead on every call.
- **Fix:** one engine at module scope; a `sessionmaker` bound to it; one scoped session
  per request, closed in a finally/context manager.

## 6. Over-broad serialization
- **Look for:** returning whole ORM objects with all relationships when a few fields are
  needed; response models that trigger lazy loads during serialization;
  `expire_on_commit=True` (default) forcing re-fetch of attributes after commit.
- **Why:** extra queries + bytes per response; the post-commit expire causes surprise
  N+1 when attributes are read after `commit()`.
- **Fix:** explicit column selection / response schemas; eager-load before commit, or
  set `expire_on_commit=False` where appropriate.

## 7. gRPC streaming & message size
- **Look for:** unary RPCs used for bulk operations that buffer the whole result in
  memory; missing deadlines on stub calls (calls can hang forever).
- **Why:** memory pressure + `RESOURCE_EXHAUSTED`; missing deadlines turn one slow
  dependency into cascading hangs.
- **Fix:** server-streaming for bulk; set a `timeout=`/deadline on every client call.

## 8. Frontend (React) performance
- **Look for:** data fetching in a loop / per-item instead of batched; missing
  memoization causing render storms; fetching far more than rendered.
- **Why:** waterfalls and re-render churn degrade perceived latency.
- **Fix:** batch requests; memoize derived data; fetch only what's displayed.

## Severity guide
CRITICAL = unbounded growth / pool exhaustion that topples the service at scale.
HIGH = N+1 / full scan / blocking-in-async on a hot path. MEDIUM = degrades under load.
LOW = minor overhead. Diagnose only — propose the fix, hand it to the developer.
