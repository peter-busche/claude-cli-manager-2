package lib

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

// ExecuteCommand runs a shell command and returns its stdout, stderr, and any
// error.
func ExecuteCommand(command string) (string, string, error) {
	cmd := exec.Command("bash", "-c", command)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	output, err := cmd.Output()
	if err != nil {
		return string(output), stderr.String(), fmt.Errorf("command error: %w", err)
	}
	return string(output), stderr.String(), nil
}

// ExecuteCommandLive runs a shell command and streams its output to the user's
// terminal in real time.
func ExecuteCommandLive(command string) error {
	cmd := exec.Command("bash", "-c", command)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}
