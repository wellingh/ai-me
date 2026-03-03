"""Shell wrapper to execute CLI commands."""

import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class ShellCommandResult:
    """Result from a git operation."""

    output: str
    success: bool
    error: str | None = None


def shell_command(cmd: List[str]) -> ShellCommandResult:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return ShellCommandResult(
                output="",
                success=False,
                error=result.stderr,
            )

        return ShellCommandResult(output=result.stdout, success=True)

    except FileNotFoundError:
        return ShellCommandResult(
            output="",
            success=False,
            error=f"{cmd[0]} not found. Make sure '{cmd[0]}' is installed and in PATH.",
        )
