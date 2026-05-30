// Package hello provides a TEMPORARY command for smoke-testing the CLI.
// Safe to delete once you have real commands — see the note in cmd/root.go.
package hello

import (
	"fmt"

	"github.com/peter-busche/claude-cli-manager-2/internal/lib"

	"github.com/spf13/cobra"
)

// HelloCmd is a temporary command used to verify the CLI builds, installs, and
// runs correctly.
var HelloCmd = &cobra.Command{
	Use:           "hello",
	Short:         "Temporary smoke-test command (prints a greeting)",
	Long:          `A temporary command to confirm claude-cli-manager-2 is built and installed correctly. Delete the cmd/hello package once you have real commands.`,
	Example:       `  ccm2 hello --name Peter`,
	SilenceErrors: true,
	SilenceUsage:  true,
	RunE: func(cmd *cobra.Command, args []string) error {
		name, _ := cmd.Flags().GetString("name")
		if name == "" {
			name = "world"
		}
		fmt.Printf("%s, %s! %s\n",
			lib.Green("Hello"),
			lib.Cyan(name),
			lib.Yellow("ccm2 is installed and working."),
		)
		return nil
	},
}

func init() {
	HelloCmd.Flags().StringP("name", "n", "", lib.FlagString(lib.Optional, "Who to greet", "", "world"))
}
