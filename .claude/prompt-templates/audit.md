Audit this repository for issues. Run the four auditor subagents IN PARALLEL.
Each DIAGNOSES ONLY — it reports root cause with evidence and does NOT change code.
Every finding must cite `file:line`, rate severity and confidence, and be appended
as a row to `FINDINGS.md`.

Keep the auditor blocks you want; delete any you don't need this pass.

Use the security-auditor subagent to hunt security issues.       @"security-auditor (agent)"
Use the performance-auditor subagent to hunt performance issues.  @"performance-auditor (agent)"
Use the reliability-auditor subagent to hunt reliability issues.  @"reliability-auditor (agent)"
Use the tooling-auditor subagent to hunt developer-tooling issues. @"tooling-auditor (agent)"

## Scope
<!-- whole repo by default; narrow to a path/subsystem if recon flagged a hotspot -->

## Context (paste from recon)
<!-- the exact test/build commands and the risk surface, so auditors don't re-derive them -->

## Output
- One row per finding in `FINDINGS.md`:
  `| Domain | Severity | Title | file:line | Root cause | Trigger/Exploit | Fix approach | Confidence |`
- Separate each row with a newline
- After all auditors return, AGGREGATE into one table sorted by
  severity × confidence × impact. Collapse duplicates that point at the same root cause.

## Constraints
- Diagnose only — propose fixes, do NOT apply them.
- Root cause, not symptom. Every row needs a concrete `file:line` and a failure trigger.
- No vague "could be improved" findings. If you can't name the failure mode, drop it.
