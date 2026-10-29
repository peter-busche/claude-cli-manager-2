Fix ONE issue with a minimal, surgical change: diagnose the root cause, then implement
the fix with tests, then commit it atomically. Exactly one issue per run.

## Issue
<!-- the given task (its direction + its definition of done), OR a FINDINGS.md row
     (title, file:line, root cause, severity) -->

## Diagnose (keep the ONE that matches the issue's domain; delete the others before running)
The matching domain auditor finds root cause fastest — each carries its checklist. Skip
this step only if the root cause is already proven.
- Security issue    -> Use the security-auditor subagent.    @"security-auditor (agent)"
- Performance issue -> Use the performance-auditor subagent.  @"performance-auditor (agent)"
- Reliability issue -> Use the reliability-auditor subagent.  @"reliability-auditor (agent)"
- Tooling issue     -> Use the tooling-auditor subagent.      @"tooling-auditor (agent)"
- Unclear / cross-cutting -> Use the debugger subagent.       @"debugger (agent)"

## Implement
Use the developer subagent to apply the fix and its tests.  @"developer (agent)"

## Required workflow
1. Restate the ROOT CAUSE in one sentence (the cause, not the symptom).
2. Make the SMALLEST change that fixes that cause. Touch nothing unrelated — do not
   refactor the neighborhood, rename things, or reformat surrounding code.
3. Run the relevant tests (use the exact command from recon). They MUST pass. If the task
   states acceptance criteria (its "definition of done"), satisfy them exactly. Add or
   adjust a test only if it directly proves this fix.
4. Write the justification with this template, then stage everything as ONE atomic commit:
   ```
   fix(area): short description of what was wrong

   Problem: what's wrong and why it matters — severity, how it's triggered/exploited
   Root cause: why it existed
   Fix: what changed and why this approach (vs. alternatives considered)
   Backwards compatible: yes/no — if no, the migration path
   ```

## Constraints
- Minimal diff. One issue = one commit. Prefer 1-3 files.
- If the fix can't be applied safely in one step (NOT NULL column, auth scheme change,
  index on a hot table), describe the PHASED migration in the justification rather than
  forcing a risky one-shot.
- If tests go red and you can't get them green in ~5 minutes, `git restore` the change,
  mark the issue diagnosed-only in FINDINGS.md, and stop — never leave the tree broken.
