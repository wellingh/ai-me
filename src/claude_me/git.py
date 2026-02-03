"""Git operations for diff, commit, and status."""

from claude_me.shell import ShellCommandResult, shell_command


def get_diff(staged_only: bool = True) -> ShellCommandResult:
    """
    Get git diff of changes.

    Args:
        staged_only: If True, only get staged changes (--cached).
                     If False, get all uncommitted changes.

    Returns:
        ShellCommandResult with the diff output
    """
    cmd = ["git", "diff"]
    if staged_only:
        cmd.append("--cached")

    return shell_command(cmd)


def get_status() -> ShellCommandResult:
    """Get git status to check for uncommitted changes."""
    cmd = ["git", "status", "--porcelain"]
    return shell_command(cmd)


def commit(message: str) -> ShellCommandResult:
    """
    Create a git commit with the given message.

    Args:
        message: The commit message

    Returns:
        ShellCommandResult with the commit output
    """

    cmd = ["git", "commit", "-am", message]
    return shell_command(cmd)


def add_all() -> ShellCommandResult:
    """Stage all changes for commit."""
    cmd = ["git", "add", "-A"]
    return shell_command(cmd)


def get_log() -> ShellCommandResult:
    """Get the git log comparing from base branch."""
    cmd = ["git", "log", "-p", "origin/main...HEAD"]
    return shell_command(cmd)
