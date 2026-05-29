package {{.PackageName}}

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// {{.UpperPackageName}}Cmd represents the {{.PackageName}} object command.
var {{.UpperPackageName}}Cmd = &cobra.Command{
	Use:   "{{.PackageName}}",
	Short: "TODO: Short description of {{.PackageName}} commands",
	Long: `Description:
  TODO: Long description of {{.PackageName}} commands. Use by running
  one of the available subcommands.`,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) < 1 {
			if err := cmd.Help(); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to display help: %v\n", err)
			}
			os.Exit(0)
		}
	},
}

func init() {
	// Define flags and configuration settings for this object command here.
	//
	// Persistent flags apply to this command and all of its subcommands:
	//   {{.UpperPackageName}}Cmd.PersistentFlags().String("foo", "", "A help for foo")
	//
	// Local flags only apply when this command is called directly:
	//   {{.UpperPackageName}}Cmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
