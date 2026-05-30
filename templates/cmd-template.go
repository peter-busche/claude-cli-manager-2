package {{.PackageName}}

import (
	"fmt"

	"github.com/peter-busche/claude-cli-manager-2/internal/lib"

	"github.com/spf13/cobra"
)

// {{.UpperFunctionName}}Options holds the validated inputs for the command.
type {{.UpperFunctionName}}Options struct {
	// Add fields for the flags this command needs.
}

// build{{.UpperFunctionName}} reads flags, validates them, and populates the
// options object.
func (o *{{.UpperFunctionName}}Options) build{{.UpperFunctionName}}(cmd *cobra.Command, args []string) error {
	// -------------- Get Flags --------------

	// -------------- Check for missing flags --------------
	var flagErrors lib.FlagErrors
	// flagErrors.Append(lib.CheckRequiredFlags(cmd, "some-flag"))
	if len(flagErrors.Errors) > 0 {
		return flagErrors.Error()
	}

	// -------------- Build Options Object --------------

	return nil
}

// run{{.UpperFunctionName}} contains the main command functionality.
func (o *{{.UpperFunctionName}}Options) run{{.UpperFunctionName}}() error {
	fmt.Println(lib.Yellow("TODO: Implement {{.UserFunctionName}}"))
	return nil
}

// {{.FunctionName}}Cmd represents the {{.UserFunctionName}} command.
var {{.FunctionName}}Cmd = &cobra.Command{
	Use:     "{{.UserFunctionName}}",
	Aliases: []string{{{.Alias}}},
	Short:   "TODO: Short description of {{.UserFunctionName}}",
	Long: `Description:
  TODO: Long description of the {{.UserFunctionName}} command
  and what it does.`,
	Example:       `  ccm2 {{.PackageName}} {{.UserFunctionName}}`,
	SilenceErrors: true,
	SilenceUsage:  true,
	RunE: func(cmd *cobra.Command, args []string) error {
		o := new({{.UpperFunctionName}}Options)
		if err := o.build{{.UpperFunctionName}}(cmd, args); err != nil {
			return err
		}
		return o.run{{.UpperFunctionName}}()
	},
}

func init() {
	{{.UpperPackageName}}Cmd.AddCommand({{.FunctionName}}Cmd)

	// Define this command's flags here, e.g.:
	// {{.FunctionName}}Cmd.Flags().StringP("name", "n", "", lib.FlagString(lib.Required, "The name", "", ""))
}
