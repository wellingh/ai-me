"""Git operations for diff, commit, and status."""

import subprocess
from dataclasses import dataclass


@dataclass
class GitResult:
    """Result from a git operation."""

    output: str
    success: bool
    error: str | None = None


def get_diff(staged_only: bool = True) -> GitResult:
    """
    Get git diff of changes.

    Args:
        staged_only: If True, only get staged changes (--cached).
                     If False, get all uncommitted changes.

    Returns:
        GitResult with the diff output
    """
    cmd = ["git", "diff"]
    if staged_only:
        cmd.append("--cached")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return GitResult(
                output="",
                success=False,
                error=result.stderr or "Git diff failed",
            )

        return GitResult(output=result.stdout, success=True)

    except FileNotFoundError:
        return GitResult(
            output="",
            success=False,
            error="Git not found. Make sure 'git' is installed and in PATH.",
        )


def get_status() -> GitResult:
    """Get git status to check for uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return GitResult(
                output="",
                success=False,
                error=result.stderr or "Git status failed",
            )

        return GitResult(output=result.stdout, success=True)

    except FileNotFoundError:
        return GitResult(
            output="",
            success=False,
            error="Git not found. Make sure 'git' is installed and in PATH.",
        )


def commit(message: str) -> GitResult:
    """
    Create a git commit with the given message.

    Args:
        message: The commit message

    Returns:
        GitResult with the commit output
    """
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return GitResult(
                output="",
                success=False,
                error=result.stderr or "Git commit failed",
            )

        return GitResult(output=result.stdout, success=True)

    except FileNotFoundError:
        return GitResult(
            output="",
            success=False,
            error="Git not found. Make sure 'git' is installed and in PATH.",
        )


def add_all() -> GitResult:
    """Stage all changes for commit."""
    try:
        result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return GitResult(
                output="",
                success=False,
                error=result.stderr or "Git add failed",
            )

        return GitResult(output=result.stdout, success=True)

    except FileNotFoundError:
        return GitResult(
            output="",
            success=False,
            error="Git not found. Make sure 'git' is installed and in PATH.",
        )
