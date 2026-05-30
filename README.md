# claude-cli-manager-2 (`ccm2`)

`claude-cli-manager-2` is a CLI tool for managing your Claude tooling. Commands
follow the format `ccm2 <object> <command> <flags>`.

## Installation

### Build from source

Requires [Go](https://go.dev/dl/) 1.21+.

```bash
git clone https://github.com/peter-busche/claude-cli-manager-2.git
cd claude-cli-manager-2
go build -o ccm2 .
```

### Put it on your PATH

```bash
mkdir -p "$HOME/bin"
mv ccm2 "$HOME/bin/ccm2"

# Add this to your shell config (~/.zshrc, ~/.bashrc, etc.) if not already present:
echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
```

### Shell completion (optional)

```bash
# zsh — add to ~/.zshrc:
echo '[[ $commands[ccm2] ]] && source <(ccm2 completion zsh)' >> "$HOME/.zshrc"

# bash — add to ~/.bashrc:
echo 'source <(ccm2 completion bash)' >> "$HOME/.bashrc"
```

## Configuration (optional)

`ccm2` reads an optional config file at `~/.config/ccm2/config.yaml`. A missing
file is not an error. Environment variables prefixed with `ccm2_` are also read
automatically (e.g. `ccm2_FOO` populates the `foo` config key).

```bash
mkdir -p "$HOME/.config/ccm2"
cat > "$HOME/.config/ccm2/config.yaml" << 'EOF'
# ~/.config/ccm2/config.yaml
# Add configuration values here as commands begin to require them.
EOF
```

## Usage

```bash
ccm2              # prints help
ccm2 --version    # prints the version
ccm2 <object> -h  # help text for an object command
```

There are no feature commands yet — this is the foundation. See
[Contributing](#contributing) to add some.

## Contributing

### Local development

```bash
# Build and run in one step
go run .

# Build a local executable for testing
go build -o ccm2 .

# Test the executable without installing it
./ccm2 --version
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
into the binary at build time and surfaced via `ccm2 --version`.

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
