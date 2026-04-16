"""Dry-run decorator for GitPort — delegates reads, logs-and-skips writes."""

from __future__ import annotations

from collections.abc import Callable

from ai_me.domain.workspace.models import Branch, CommitLog, CommitResult, Diff
from ai_me.domain.workspace.ports import GitPort


class DryRunGitAdapter(GitPort):
    """Wraps a real GitPort. Read methods delegate; write methods log and return stubs."""

    def __init__(self, inner: GitPort, on_skip: Callable[[str], None]) -> None:
        self._inner = inner
        self._on_skip = on_skip

    # --- Read operations: delegate to the real adapter ---

    def get_staged_diff(self) -> Diff | None:
        return self._inner.get_staged_diff()

    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        return self._inner.get_diff(base, head)

    def get_commit_log(self, base: str, head: str = "HEAD") -> CommitLog:
        return self._inner.get_commit_log(base, head)

    def get_current_branch(self) -> Branch:
        return self._inner.get_current_branch()

    def get_default_branch(self) -> Branch:
        return self._inner.get_default_branch()

    # --- Write operations: log and return stubs ---

    def stage_all(self) -> None:
        self._on_skip("git add -A")

    def commit(self, message: str) -> CommitResult:
        self._on_skip(f"git commit -m '{message}'")
        return CommitResult(hash="dry-run", message=message)
