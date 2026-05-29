package lib

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

// FlagErrors collects multiple flag-validation errors so they can be reported
// together rather than one at a time.
type FlagErrors struct {
	Errors []error
}

// Error joins all collected errors into a single error.
func (flagErrors *FlagErrors) Error() error {
	var errorStrings []string
	for _, err := range flagErrors.Errors {
		errorStrings = append(errorStrings, err.Error())
	}
	return fmt.Errorf("%s", strings.Join(errorStrings, "\n"))
}

// Append adds a non-nil error to the FlagErrors.
func (flagErrors *FlagErrors) Append(err error) {
	if err != nil {
		flagErrors.Errors = append(flagErrors.Errors, err)
	}
}

// isFlagSet checks whether a flag has been set, considering its type.
func isFlagSet(cmd *cobra.Command, flagName string) (bool, error) {
	flag := cmd.Flags().Lookup(flagName)
	if flag == nil {
		return false, fmt.Errorf("flag [%s] has not been added to cobra", Red(flagName))
	}

	switch flag.Value.Type() {
	case "bool":
		return cmd.Flags().GetBool(flagName)
	case "string":
		value, _ := cmd.Flags().GetString(flagName)
		return value != "", nil
	case "int":
		return flag.Changed, nil
	default:
		return flag.Changed, nil
	}
}

// CheckRequiredFlags returns an error listing any of the named flags that are
// not set.
func CheckRequiredFlags(cmd *cobra.Command, requiredFlags ...string) error {
	var missingFlags []string
	for _, flagName := range requiredFlags {
		isSet, err := isFlagSet(cmd, flagName)
		if err != nil {
			return err
		}
		if !isSet {
			missingFlags = append(missingFlags, fmt.Sprintf("--%v", flagName))
		}
	}
	if len(missingFlags) > 0 {
		return fmt.Errorf("required flags not set: [%s]", Green(strings.Join(missingFlags, ", ")))
	}
	return nil
}

// CheckMutuallyExclusiveFlags returns an error if more than one of the named
// flags is set.
func CheckMutuallyExclusiveFlags(cmd *cobra.Command, exclusiveFlags ...string) error {
	var setFlags []string
	for _, flagName := range exclusiveFlags {
		isSet, err := isFlagSet(cmd, flagName)
		if err != nil {
			return err
		}
		if isSet {
			setFlags = append(setFlags, fmt.Sprintf("--%v", flagName))
		}
	}
	if len(setFlags) > 1 {
		return fmt.Errorf("mutually exclusive flags cannot be set together: [%s]", Green(strings.Join(setFlags, ", ")))
	}
	return nil
}

// CheckAtLeastOneFlag ensures at least one of the named flags is set.
func CheckAtLeastOneFlag(cmd *cobra.Command, flags ...string) error {
	var unsetFlags []string
	anySet := false
	for _, flagName := range flags {
		isSet, err := isFlagSet(cmd, flagName)
		if err != nil {
			return err
		}
		if isSet {
			anySet = true
		} else {
			unsetFlags = append(unsetFlags, fmt.Sprintf("--%v", flagName))
		}
	}
	if !anySet {
		return fmt.Errorf("at least one of the following flags must be set: [%s]", Green(strings.Join(unsetFlags, ", ")))
	}
	return nil
}

// CheckEnumFlag validates that a string flag, when set, is one of the allowed
// values. It does not enforce that the flag is required.
func CheckEnumFlag(cmd *cobra.Command, flagName string, allowedValues ...string) error {
	value, err := cmd.Flags().GetString(flagName)
	if err != nil {
		return err
	}
	if value == "" {
		return nil
	}
	for _, allowed := range allowedValues {
		if strings.EqualFold(value, allowed) {
			return nil
		}
	}
	return fmt.Errorf("invalid value %s for %s: must be one of [%s]",
		Yellow(value), Green("--"+flagName), Green(strings.Join(allowedValues, ", ")))
}

// FlagPriority describes how necessary a flag is, used to colorize help text.
type FlagPriority int

const (
	Required    FlagPriority = iota // 0
	Conditional                     // 1
	Optional                        // 2
)

// FlagString builds a colorized, consistently formatted help string for a flag,
// e.g. "[Req] The thing to do (option-a, option-b) --- Defaults: (option-a)".
func FlagString(necessity FlagPriority, description string, options string, def string) string {
	var priorityString string
	switch necessity {
	case Required:
		priorityString = Magenta("[Req]")
	case Conditional:
		priorityString = Yellow("[Cond]")
	case Optional:
		priorityString = Cyan("[Opt]")
	}

	var optionsStr string
	if options != "" {
		optionsStr = Green("(%v)", options)
	}

	if def == "" {
		return fmt.Sprintf("%v %v %v", priorityString, description, optionsStr)
	}
	return fmt.Sprintf("%v %v %v --- Defaults: (%v)", priorityString, description, optionsStr, def)
}
