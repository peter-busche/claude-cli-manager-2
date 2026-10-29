# Security Audit Checklist

Hunt list for the security-auditor. Stack: Python gRPC + SQLAlchemy backend,
TypeScript/React frontend. For each item: what to look for → why it matters → the fix.
Cite `file:line` and name the input source + attacker gain for every finding.

## 1. SQL injection / ORM misuse
- **Look for:** raw SQL via `text()`, `engine.execute()`, or `session.execute()` with
  string formatting/f-strings; filters built from user input, e.g.
  `query.filter(text(f"name = '{name}'"))`; `LIKE` patterns concatenated from input.
- **Why:** attacker-controlled input reaches the SQL string → data exfiltration,
  auth bypass, or data destruction.
- **Fix:** parameterized queries — ORM column expressions (`User.name == name`) or
  bound params (`text("... = :name").bindparams(name=name)`). Never interpolate.

## 2. Secrets in code / config
- **Look for:** hardcoded API keys, DB URLs with passwords, JWT/signing secrets in
  source; committed `.env` files; secrets with defaults (`getenv("SECRET", "dev")`);
  env vars read but never validated at startup.
- **Why:** secrets in VCS leak permanently (history); empty/default secrets mean the
  app boots insecure and signs tokens anyone can forge.
- **Fix:** load from env; validate presence/format at boot (fail fast); keep `.env` out
  of git; rotate anything already committed.

## 3. gRPC authentication & authorization
- **Look for:** no server-side interceptor validating credentials; a token read from
  metadata but never verified; an auth check that always returns `True`/stub; no token
  expiry or signature verification; authorization missing (any caller can hit any RPC).
- **Why:** the canonical "auth is wired but not enforced" bug — every RPC is effectively
  public.
- **Fix:** a server interceptor that validates the token (signature + expiry + claims)
  on every call and rejects with `UNAUTHENTICATED`/`PERMISSION_DENIED`. See the
  reliability checklist for phased rollout if clients exist.

## 4. Input / field validation
- **Look for:** RPC handlers that trust request fields directly — negative or zero IDs,
  empty/oversized strings, out-of-range numbers, unbounded list/page sizes; proto
  scalar defaults treated as "present" (`if request.field:` fails for `0`/`""`).
- **Why:** missing bounds → logic errors, resource abuse, or downstream injection;
  proto default confusion → wrong behavior on legitimately-zero values.
- **Fix:** validate every incoming field (bounds, non-empty, max length, page caps);
  use `HasField()` for genuinely-optional fields; reject with `INVALID_ARGUMENT`.

## 5. CORS / frontend token handling
- **Look for:** `allow_origins=["*"]` combined with `allow_credentials=True`; wildcard
  CORS on any credentialed endpoint; JWT/refresh tokens stored in `localStorage`.
- **Why:** wildcard + credentials lets any origin make authenticated requests;
  `localStorage` tokens are stealable via any XSS.
- **Fix:** explicit origin allowlist; prefer `httpOnly` + `Secure` cookies for tokens.
  Note any client that relied on the wildcard (migration impact).

## 6. Path traversal / file handling
- **Look for:** file paths built from request input via `os.path.join`/`open()` without
  resolving + checking against a base dir; archive extraction without member checks.
- **Why:** `../../etc/passwd`-style escapes read or overwrite arbitrary files.
- **Fix:** `os.path.realpath` the result and assert it starts with the allowed base
  directory before any I/O.

## 7. Unsafe deserialization
- **Look for:** `pickle.loads`, `yaml.load` (non-safe), `eval`/`exec`, or `__reduce__`
  paths on untrusted data.
- **Why:** arbitrary code execution from attacker-controlled bytes.
- **Fix:** `yaml.safe_load`; never unpickle untrusted data; use structured formats.

## 8. Dependency vulnerabilities
- **Look for:** old pins in `requirements*.txt` / `pyproject.toml` / `package.json`;
  lockfile drift; transitively-pulled CVEs.
- **Why:** known-exploitable versions are free wins for attackers.
- **Fix:** `pip-audit` / `npm audit`; bump the specific vulnerable pins (minimal, not a
  blanket upgrade).

## 9. gRPC exposure surface
- **Look for:** server reflection enabled in production; verbose error messages leaking
  internals/stack traces to clients; missing message-size limits.
- **Why:** reflection + verbose errors hand attackers the schema and internals.
- **Fix:** disable reflection in prod; map errors to safe status messages; set
  `max_message_length`.

## Severity guide
CRITICAL = remote unauth exploit (injection, auth bypass, secret disclosure).
HIGH = exploitable with one precondition / low privilege. MEDIUM = unusual conditions.
LOW = defense-in-depth. Diagnose only — propose the fix, hand it to the developer.
