Analyze THIS directory — your current working directory — which is one subproject within a larger monorepo, and create or refresh a single file named CLAUDE.md in this directory.

Goal: a SHORT, focused CLAUDE.md scoped to THIS directory only. It loads when a session works in this subtree, ON TOP OF the repo-root CLAUDE.md, so do not repeat repo-wide rules.

Discover this subproject with bounded, read-only commands (scope to this directory):
- `git ls-files . | head -200`
- Inspect this directory's own manifests/config (package.json, go.mod, pyproject.toml, etc.)

Write CLAUDE.md with ONLY content specific to THIS directory:
- What this subproject is and its responsibility.
- Its tech stack and key files / entry points.
- How to build / test / run JUST this area (only commands that differ from repo-wide).
- Local conventions and gotchas unique to this subtree.

HARD CONSTRAINTS:
- Keep it UNDER 150 lines and ruthlessly pruned. If Claude would not need a line to avoid a mistake here, omit it.
- Assume a root CLAUDE.md already covers repo-wide rules — do NOT restate them.
- Modify ONLY this directory's CLAUDE.md. Do not touch any other file.
