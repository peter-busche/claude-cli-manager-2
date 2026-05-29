#!/usr/bin/env bash
set -euo pipefail

# Script to generate new claude-cli-manager (ccm) commands.
# Usage:   bash scripts/add-cmd.sh [package_name] [action] [action_alias](optional)
# Example: bash scripts/add-cmd.sh app list-sessions list

MODULE_PATH="github.com/peter-busche/claude-cli-manager"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$#" -lt 2 ]]; then
    echo "Usage: bash scripts/add-cmd.sh [package_name] [action] [action_alias](optional)"
    echo "Example: bash scripts/add-cmd.sh app list-sessions list"
    exit 1
fi

PACKAGE_NAME=$1
USER_FUNCTION_NAME=$2
ALIAS=${3:-}

# Validate package name (no dashes allowed in Go package names).
if [[ "$PACKAGE_NAME" =~ - ]]; then
    echo "Error: Package name cannot contain dashes. Use a single word or underscores."
    echo "Example: 'sessions' or 'my_pkg' instead of 'my-pkg'"
    exit 1
fi

# Convert USER_FUNCTION_NAME (kebab-case) to FUNCTION_NAME (camelCase).
FUNCTION_NAME=$(echo "$USER_FUNCTION_NAME" | sed 's/-/ /g' | awk '{ for(i=1;i<=NF;i++) $i=(i==1)? $i : toupper(substr($i,1,1)) tolower(substr($i,2)); }1' | sed 's/ //g')

# Uppercase the first letter of the package name (for exported variables).
UPPER_PACKAGE_NAME=$(echo "$PACKAGE_NAME" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')

# Uppercase the first letter of the function name (for exported variables).
UPPER_FUNCTION_NAME=$(echo "$FUNCTION_NAME" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')

# Paths
NEW_PACKAGE_PATH="$PROJECT_ROOT/cmd/$PACKAGE_NAME"
NEW_PARENT_PATH="$NEW_PACKAGE_PATH/$PACKAGE_NAME.go"
NEW_CMD_PATH="$NEW_PACKAGE_PATH/$USER_FUNCTION_NAME.go"
CMD_ROOT_PATH="$PROJECT_ROOT/cmd/root.go"

# Create the parent (object) command if it doesn't exist yet.
if [[ ! -f "$NEW_PARENT_PATH" ]]; then
    echo "Creating parent command: $PACKAGE_NAME"
    mkdir -p "$NEW_PACKAGE_PATH"

    cat > "$NEW_PARENT_PATH" << EOF
package $PACKAGE_NAME

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// ${UPPER_PACKAGE_NAME}Cmd represents the $PACKAGE_NAME object command.
var ${UPPER_PACKAGE_NAME}Cmd = &cobra.Command{
	Use:   "$PACKAGE_NAME",
	Short: "TODO: Short description of $PACKAGE_NAME commands",
	Long: \`Description:
  TODO: Long description of $PACKAGE_NAME commands. Use by running
  one of the available subcommands.\`,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) < 1 {
			if err := cmd.Help(); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to display help: %v\n", err)
			}
			os.Exit(0)
		}
	},
}
EOF
    echo "Created $NEW_PARENT_PATH"

    # Register the new object command in cmd/root.go.
    echo "Adding import and registration to cmd/root.go"

    if grep -q "$MODULE_PATH/cmd/$PACKAGE_NAME" "$CMD_ROOT_PATH"; then
        echo "Import already exists in root.go"
    else
        sed -i '' "/$(printf '%s' "$MODULE_PATH/internal/lib" | sed 's/\//\\\//g')/a\\
	\"$MODULE_PATH/cmd/$PACKAGE_NAME\"
" "$CMD_ROOT_PATH"
    fi

    if grep -q "rootCmd.AddCommand($PACKAGE_NAME.${UPPER_PACKAGE_NAME}Cmd)" "$CMD_ROOT_PATH"; then
        echo "Command already registered in root.go"
    else
        sed -i '' "/\/\/ rootCmd.AddCommand(app.AppCmd)/a\\
	rootCmd.AddCommand($PACKAGE_NAME.${UPPER_PACKAGE_NAME}Cmd)
" "$CMD_ROOT_PATH"
    fi

    echo "Registered $PACKAGE_NAME in root.go"
else
    echo "Parent command $PACKAGE_NAME already exists"
fi

# Create the subcommand file if it doesn't exist yet.
if [[ ! -f "$NEW_CMD_PATH" ]]; then
    echo "Creating command: $USER_FUNCTION_NAME"

    ALIAS_LINE=""
    if [[ -n "$ALIAS" ]]; then
        ALIAS_LINE="	Aliases: []string{\"$ALIAS\"},"
    fi

    cat > "$NEW_CMD_PATH" << EOF
package $PACKAGE_NAME

import (
	"fmt"

	"$MODULE_PATH/internal/lib"

	"github.com/spf13/cobra"
)

// ${UPPER_FUNCTION_NAME}Options holds the validated inputs for the command.
type ${UPPER_FUNCTION_NAME}Options struct {
	// Add fields for the flags this command needs.
}

// build${UPPER_FUNCTION_NAME} reads flags, validates them, and populates the options object.
func (o *${UPPER_FUNCTION_NAME}Options) build${UPPER_FUNCTION_NAME}(cmd *cobra.Command, args []string) error {
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

// run${UPPER_FUNCTION_NAME} contains the main command functionality.
func (o *${UPPER_FUNCTION_NAME}Options) run${UPPER_FUNCTION_NAME}() error {
	fmt.Println(lib.Yellow("TODO: Implement $USER_FUNCTION_NAME"))
	return nil
}

// ${FUNCTION_NAME}Cmd represents the $USER_FUNCTION_NAME command.
var ${FUNCTION_NAME}Cmd = &cobra.Command{
	Use:   "$USER_FUNCTION_NAME",
$ALIAS_LINE
	Short: "TODO: Short description of $USER_FUNCTION_NAME",
	Long: \`Description:
  TODO: Long description of the $USER_FUNCTION_NAME command
  and what it does.\`,
	Example:       \`  ccm $PACKAGE_NAME $USER_FUNCTION_NAME\`,
	SilenceErrors: true,
	SilenceUsage:  true,
	RunE: func(cmd *cobra.Command, args []string) error {
		o := new(${UPPER_FUNCTION_NAME}Options)
		if err := o.build${UPPER_FUNCTION_NAME}(cmd, args); err != nil {
			return err
		}
		return o.run${UPPER_FUNCTION_NAME}()
	},
}

func init() {
	${UPPER_PACKAGE_NAME}Cmd.AddCommand(${FUNCTION_NAME}Cmd)

	// Define this command's flags here, e.g.:
	// ${FUNCTION_NAME}Cmd.Flags().StringP("name", "n", "", lib.FlagString(lib.Required, "The name", "", ""))
}
EOF
    echo "Created $NEW_CMD_PATH"
else
    echo "Command $USER_FUNCTION_NAME already exists at $NEW_CMD_PATH"
fi

echo "Done. Run 'go build -o ccm .' to compile."
