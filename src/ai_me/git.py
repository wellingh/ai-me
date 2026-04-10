"""Git operations for diff, commit, and status."""

from ai_me.shell import ShellCommandResult, shell_command


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


def get_current_branch() -> ShellCommandResult:
    """Get the name of the current git branch."""
    cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    result = shell_command(cmd)
    if result.success:
        result.output = result.output.strip()
    return result


def get_default_branch() -> ShellCommandResult:
    """Detect the default branch of the remote origin."""
    cmd = ["git", "remote", "show", "origin"]
    result = shell_command(cmd)
    if result.success:
        for line in result.output.splitlines():
            if "HEAD branch:" in line:
                result.output = line.split(":")[-1].strip()
                return result
        # Fallback if parsing fails
        result.output = "main"
    return result


def get_diff_against_branch(base_branch: str) -> ShellCommandResult:
    """Get the diff between the current branch and a base branch."""
    cmd = ["git", "diff", f"{base_branch}...HEAD"]
    return shell_command(cmd)


def get_log_against_branch(base_branch: str) -> ShellCommandResult:
    """Get the full commit log with patches between a base branch and HEAD."""
    cmd = ["git", "log", "-p", f"{base_branch}...HEAD"]
    return shell_command(cmd)


def get_changed_files(base_branch: str) -> ShellCommandResult:
    """Get the list of files changed between a base branch and HEAD.

    Returns file paths one per line (only added/modified, not deleted).
    """
    cmd = ["git", "diff", "--name-only", "--diff-filter=ACM", f"{base_branch}...HEAD"]
    return shell_command(cmd)


def push_branch(branch: str) -> ShellCommandResult:
    """Push the current branch to origin with upstream tracking."""
    cmd = ["git", "push", "-u", "origin", branch]
    return shell_command(cmd)


def create_pr(title: str, body: str, base: str) -> ShellCommandResult:
    """Create a pull request using the GitHub CLI."""
    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    return shell_command(cmd)


def get_existing_pr(branch: str) -> ShellCommandResult:
    """Check if an open PR already exists for the given branch."""
    cmd = ["gh", "pr", "view", branch, "--json", "url,title,body,number"]
    return shell_command(cmd)


def update_pr(title: str, body: str) -> ShellCommandResult:
    """Update the title and body of the current branch's PR."""
    cmd = ["gh", "pr", "edit", "--title", title, "--body", body]
    return shell_command(cmd)


def get_all_files() -> ShellCommandResult:
    """Get all files tracked by git in the current repository."""
    return shell_command(["git", "ls-files"])


def get_repo_info() -> ShellCommandResult:
    """Get the GitHub repository owner (org) and name via gh CLI.

    Output JSON shape: {"owner": {"login": "<org>"}, "name": "<repo>"}
    """
    return shell_command(["gh", "repo", "view", "--json", "owner,name"])
