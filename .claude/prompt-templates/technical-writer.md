Use the technical-writer subagent to document the target described below.
@"technical-writer (agent)"

The technical-writer documents what EXISTS, optimized for LLM consumption — it
will not ask follow-up questions, so point it at a concrete target and say which
kind of doc you want. It reads project preferences from CLAUDE.md before writing.

## Target
<!-- <what to document — a file, directory, symbol, or feature; e.g. ccm2/commands/session/ or ccm2/lib/flags.py:flag_string> -->

## Doc type
<!-- <one or more: CLAUDE.md navigation index | README.md (the "why") | inline docstrings/comments> -->

## Scope / focus (optional)
<!-- <what matters most for readers — public API, gotchas, conventions, entry points> -->

## Constraints
- Document what the code DOES, not what it should do; do not invent rationale.
- Follow this repo's CLAUDE.md preferences (ASCII, emoji/markdown rules) and .claude/conventions/.
- Keep it lean — every word earns its tokens; no marketing or filler.
