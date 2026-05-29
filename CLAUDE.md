# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Build and Development Commands

- **Build**: `go build -o ccm .` — creates the local `ccm` executable
- **Run**: `go run .` — builds and runs the CLI directly
- **Test local build**: `./ccm --version` — runs the built executable
- **Tidy deps**: `go mod tidy`

## Maintenance Scripts

Scripts live in the `scripts/` directory.

### Adding new commands

```bash
bash scripts/add-cmd.sh [package_name] [action] [action_alias](optional)
```

Examples:
- `bash scripts/add-cmd.sh app list`
- `bash scripts/add-cmd.sh app list-sessions list`

Package names cannot contain dashes (use `sessions`, not `my-sessions`).

This script automatically:
- Creates the package directory under `cmd/` if needed
- Generates a parent (object) command and/or a subcommand file
- Registers the import and `rootCmd.AddCommand(...)` call in `cmd/root.go`

## Architecture

### CLI structure

- Built using the [Cobra](https://github.com/spf13/cobra) framework.
- Hierarchical commands: `ccm <object> <command> <flags>`.
- Each object (e.g. `app`) is its own package under `cmd/`.
- The root command and `Execute()` live in `cmd/root.go`.
- The module path is `github.com/peter-busche/claude-cli-manager`; internal
  packages are imported relative to it (e.g.
  `github.com/peter-busche/claude-cli-manager/internal/lib`).

### Command pattern

Each leaf command follows an Options-struct pattern:
1. **`XOptions` struct** — holds validated inputs.
2. **`buildX` method** — reads flags, validates them (via `internal/lib`
   helpers), and populates the struct.
3. **`runX` method** — the main command logic.
4. **`cobra.Command`** — wires `Use`, `Short`, `Long`, `Example`, and `RunE`.
5. **`init`** — registers the command on its parent and defines flags.

See `templates/cmd-template.go` and `templates/parent-cmd-template.go`.

### Configuration

- Uses [Viper](https://github.com/spf13/viper).
- Optional config file at `~/.config/ccm/config.yaml` (a missing file is not an
  error — see `initConfig` in `cmd/root.go`).
- Environment variables prefixed with `CCM_` are read automatically.

### Shared helpers (`internal/lib`)

- `colors.go` — colorized output helpers (`Red`, `Green`, `Cyan`, etc.).
- `flags.go` — flag-validation system: `FlagErrors`, `CheckRequiredFlags`,
  `CheckMutuallyExclusiveFlags`, `CheckAtLeastOneFlag`, `CheckEnumFlag`, and
  `FlagString` for consistent, colorized help text (`Required` / `Conditional`
  / `Optional`).
- `exec.go` — `ExecuteCommand` (captured) and `ExecuteCommandLive` (streamed).

### Versioning

- The `VERSION` file is embedded into the binary via `//go:embed` in `main.go`
  and surfaced through `ccm --version`. Bump it (semver) when releasing.
