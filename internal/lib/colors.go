package lib

import (
	"fmt"

	"github.com/fatih/color"
)

// Cached color functions for performance.
var (
	redFunc     = color.New(color.FgRed).SprintfFunc()
	greenFunc   = color.New(color.FgGreen).SprintfFunc()
	blueFunc    = color.New(color.FgBlue).SprintfFunc()
	yellowFunc  = color.New(color.FgYellow).SprintfFunc()
	magentaFunc = color.New(color.FgMagenta).SprintfFunc()
	cyanFunc    = color.New(color.FgCyan).SprintfFunc()
	whiteFunc   = color.New(color.FgWhite).SprintfFunc()
	// Orange and pink use 256-color codes from the fatih/color library.
	orangeFunc = color.New(color.Attribute(214)).SprintfFunc()
	pinkFunc   = color.New(color.Attribute(213)).SprintfFunc()
)

// The functions below take arguments just like fmt.Sprintf and return a
// colorized string, for printing colored output to the terminal.

func Red(strObj interface{}, subs ...interface{}) string {
	return redFunc(fmt.Sprint(strObj), subs...)
}

func Green(strObj interface{}, subs ...interface{}) string {
	return greenFunc(fmt.Sprint(strObj), subs...)
}

func Blue(strObj interface{}, subs ...interface{}) string {
	return blueFunc(fmt.Sprint(strObj), subs...)
}

func Yellow(strObj interface{}, subs ...interface{}) string {
	return yellowFunc(fmt.Sprint(strObj), subs...)
}

func Magenta(strObj interface{}, subs ...interface{}) string {
	return magentaFunc(fmt.Sprint(strObj), subs...)
}

func Cyan(strObj interface{}, subs ...interface{}) string {
	return cyanFunc(fmt.Sprint(strObj), subs...)
}

func White(strObj interface{}, subs ...interface{}) string {
	return whiteFunc(fmt.Sprint(strObj), subs...)
}

func Orange(strObj interface{}, subs ...interface{}) string {
	return orangeFunc(fmt.Sprint(strObj), subs...)
}

func Pink(strObj interface{}, subs ...interface{}) string {
	return pinkFunc(fmt.Sprint(strObj), subs...)
}
