package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/peter-busche/claude-cli-manager-2/cmd/hello"
	"github.com/peter-busche/claude-cli-manager-2/internal/lib"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// rootCmd represents the base command when called without any subcommands.
var rootCmd = &cobra.Command{
	Use:   "ccm2",
	Short: "claude-cli-manager-2 — a CLI to manage your Claude tooling",
	Long: `claude-cli-manager-2 (ccm2) is the one stop shop for managing your Claude tooling.
Commands follow the format 'ccm2 <object> <command> <flags>'.
Explore by passing the -h flag to any object or command to see its help text!
`,
	Example:       `  ccm2 --version`,
	SilenceErrors: true,
	SilenceUsage:  true,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Print help and exit if the base command is called with no flags.
		if cmd.Flags().NFlag() == 0 {
			if err := cmd.Help(); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to display help: %v\n", err)
			}
			os.Exit(0)
		}
		return nil
	},
}

// validateCommands checks if the provided args correspond to a valid command
// tree. Without this, flag parsing would run first and overshadow invalid
// command errors with confusing output.
func validateCommands(currentCmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return nil
	}
	arg := args[0]
	if strings.HasPrefix(arg, "-") || strings.HasPrefix(arg, "_") {
		return nil
	}

	for _, subCommand := range currentCmd.Commands() {
		if arg == subCommand.Name() {
			return validateCommands(subCommand, args[1:])
		}
		for _, alias := range subCommand.Aliases {
			if arg == alias {
				return validateCommands(subCommand, args[1:])
			}
		}
	}

	if len(currentCmd.Commands()) > 0 {
		fmt.Println("Available commands are:")
		for _, c := range currentCmd.Commands() {
			fmt.Printf("  %s\n", c.Name())
		}
	} else {
		fmt.Printf("Command %q does not have any subcommands\n", currentCmd.Name())
	}
	return fmt.Errorf("invalid subcommand %q for %q", arg, currentCmd.Name())
}

// Execute adds all child commands to the root command and sets flags
// appropriately. It is called by main.main() and only needs to happen once.
func Execute(version string) {
	rootCmd.Version = version
	os.Setenv("CLI_VERSION", version)

	// With no args, display help text.
	if len(os.Args) <= 1 {
		if err := rootCmd.Execute(); err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		os.Exit(0)
	}

	// Let cobra's built-in commands run without command-tree validation.
	cobraFlags := []string{"completion", "__complete", "-v", "--version", "-h", "--help", "help"}
	for _, cobraFlag := range cobraFlags {
		if cobraFlag == os.Args[1] {
			if err := rootCmd.Execute(); err != nil {
				fmt.Println(err)
				os.Exit(1)
			}
			os.Exit(0)
		}
	}

	if err := validateCommands(rootCmd, os.Args[1:]); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

// initConfig sets up Viper to read an optional config file at
// ~/.config/ccm2/config.yaml. A missing config file is not an error — commands
// that need specific values should validate them when they run.
func initConfig() error {
	home, err := os.UserHomeDir()
	if err != nil {
		return fmt.Errorf("trouble finding user's home directory: %w", err)
	}

	viper.AddConfigPath(fmt.Sprintf("%s/.config/ccm2", home))
	viper.SetConfigType("yaml")
	viper.SetConfigName("config")
	viper.SetEnvPrefix("ccm2")
	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		// A missing config file is fine; surface any other read error.
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("config file error: %w", err)
		}
	}
	return nil
}

func init() {
	if err := initConfig(); err != nil {
		fmt.Println(lib.Red(err))
		os.Exit(1)
	}

	// Register object (parent) commands here as the CLI grows, e.g.:
	// rootCmd.AddCommand(app.AppCmd)

	// TEMPORARY: smoke-test command. Remove this line and the cmd/hello
	// package once you have real commands.
	rootCmd.AddCommand(hello.HelloCmd)
}
