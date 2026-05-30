package main

import (
	_ "embed"
	"strings"

	"github.com/peter-busche/claude-cli-manager-2/cmd"
)

//go:embed VERSION
var version string

func main() {
	cmd.Execute(strings.TrimSpace(version))
}
