# claude-cli-manager (`ccm`)

`claude-cli-manager` is a CLI tool for managing your Claude tooling. Commands
follow the format `ccm <object> <command> <flags>`.

## Installation

### Build from source

Requires [Go](https://go.dev/dl/) 1.21+.

```bash
git clone https://github.com/peter-busche/claude-cli-manager.git
cd claude-cli-manager
go build -o ccm .
```

### Put it on your PATH

```bash
mkdir -p "$HOME/bin"
mv ccm "$HOME/bin/ccm"

# Add this to your shell config (~/.zshrc, ~/.bashrc, etc.) if not already present:
echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
```

### Shell completion (optional)

```bash
# zsh — add to ~/.zshrc:
echo '[[ $commands[ccm] ]] && source <(ccm completion zsh)' >> "$HOME/.zshrc"

# bash — add to ~/.bashrc:
echo 'source <(ccm completion bash)' >> "$HOME/.bashrc"
```

## Configuration (optional)

`ccm` reads an optional config file at `~/.config/ccm/config.yaml`. A missing
file is not an error. Environment variables prefixed with `CCM_` are also read
automatically (e.g. `CCM_FOO` populates the `foo` config key).

```bash
mkdir -p "$HOME/.config/ccm"
cat > "$HOME/.config/ccm/config.yaml" << 'EOF'
# ~/.config/ccm/config.yaml
# Add configuration values here as commands begin to require them.
EOF
```

## Usage

```bash
ccm              # prints help
ccm --version    # prints the version
ccm <object> -h  # help text for an object command
```

There are no feature commands yet — this is the foundation. See
[Contributing](#contributing) to add some.

## Contributing

### Local development

```bash
# Build and run in one step
go run .

# Build a local executable for testing
go build -o ccm .

# Test the executable without installing it
./ccm --version
```

### Adding commands

Use the generator script to scaffold a new command. It creates the parent
(object) command if needed and registers everything in `cmd/root.go`:

```bash
# bash scripts/add-cmd.sh [package_name] [action] [action_alias](optional)
bash scripts/add-cmd.sh app list-sessions list
```

Package names cannot contain dashes (use `sessions`, not `my-sessions`).
Reference templates live in `templates/`.

### Versioning

Bump the `VERSION` file (semver) when cutting a release. The version is embedded
into the binary at build time and surfaced via `ccm --version`.

## Project layout

```
.
├── main.go              # entrypoint; embeds VERSION, calls cmd.Execute
├── VERSION              # semver string embedded into the binary
├── cmd/
│   └── root.go          # root command, Execute(), config init
├── internal/
│   └── lib/             # shared helpers (colors, flag validation, exec)
├── scripts/
│   └── add-cmd.sh       # command generator
└── templates/           # reference templates for new commands
```
