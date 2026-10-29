Use the debugger subagent to investigate the bug described below.
@"debugger (agent)"

The debugger diagnoses and reports the root cause with evidence — it does NOT
implement the fix. Hand it everything it needs to reproduce and localize the
failure, then let it report back.

## Bug
<!-- <one sentence: what is broken> -->

## Symptoms
<!-- <the observable failure — error message, stack trace, wrong output, crash, or hang> -->

## Reproduction
<!-- <exact steps, command, or input that triggers it; note if intermittent> -->

## Expected vs. actual
<!-- - Expected: <what should happen>
- Actual:   <what happens instead> -->

- Expected:
- Actual:

## Suspects / scope (optional, but speeds things up)
<!-- <files, functions, modules, or recent changes you suspect — e.g. path/to/file.py:120> -->

## Constraints
- Diagnose only; do not modify code.
- Report the root cause backed by evidence (cite `file:line`).
- Finish with a recommended fix and any follow-ups worth checking.
