"""Dry-run decorator for GitHubPort — delegates reads, logs-and-skips writes."""

from __future__ import annotations

from collections.abc import Callable

from ai_me.domain.workspace.models import PullRequest, PullRequestResult
from ai_me.domain.workspace.ports import GitHubPort


class DryRunGitHubAdapter(GitHubPort):
    """Wraps a real GitHubPort. Read methods delegate; write methods log and return stubs."""

    def __init__(self, inner: GitHubPort, on_skip: Callable[[str], None]) -> None:
        self._inner = inner
        self._on_skip = on_skip

    # --- Read operations: delegate ---

    def find_existing_pr(self, branch: str) -> PullRequest | None:
        return self._inner.find_existing_pr(branch)

    # --- Write operations: log and return stubs ---

    def create_pr(
        self,
        title: str,
        body: str,
        base: str,
        head: str,
        draft: bool = False,
    ) -> PullRequestResult:
        draft_flag = " --draft" if draft else ""
        self._on_skip(
            f"gh pr create --title '{title}' --base {base} --head {head}{draft_flag}"
        )
        return PullRequestResult(url="https://dry-run", number=0, created=True)

    def update_pr(self, number: int, title: str, body: str) -> PullRequestResult:
        self._on_skip(f"gh pr edit {number} --title '{title}'")
        return PullRequestResult(url="https://dry-run", number=number, created=False)
