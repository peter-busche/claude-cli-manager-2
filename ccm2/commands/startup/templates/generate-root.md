Analyze THIS directory, which is the ROOT of a large repository, and create or refresh a single file named CLAUDE.md in this directory.

Goal: CLAUDE.md is a LEAN navigation index that orients any future Claude Code session working anywhere in this repo. It is loaded into EVERY session, so every line must earn its place.

Discover the repo structure with bounded, read-only commands only (do NOT dump the whole tree):
- `git ls-files | head -400` and `git ls-files | cut -d/ -f1 | sort -u` for the top-level areas
- Inspect the key manifests at the root (package.json, go.mod, pyproject.toml, Makefile, etc.)

Write CLAUDE.md with ONLY repository-wide content:
- One short paragraph: what this repo is.
- Repository structure: a brief list of the top-level areas and what each is for.
- Build / test / run / commit conventions that apply repo-wide.
- Repo-wide rules and gotchas every contributor must know.

HARD CONSTRAINTS:
- Keep CLAUDE.md UNDER 200 lines. Shorter is better. If it grows past that, cut detail, not sections.
- Do NOT include stack-specific details for individual subprojects — those belong in per-directory CLAUDE.md files. Point to them instead.
- Modify ONLY this directory's CLAUDE.md. Do not touch any other file.
