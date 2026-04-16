"""Workspace bounded context — ports (abstract interfaces) for git and GitHub."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_me.domain.workspace.models import (
    Branch,
    CommitLog,
    CommitResult,
    Diff,
    PullRequest,
    PullRequestResult,
)


class GitPort(ABC):
    """Abstract interface for git operations."""

    @abstractmethod
    def get_staged_diff(self) -> Diff | None:
        """Return the diff of staged changes, or None if nothing is staged."""

    @abstractmethod
    def stage_all(self) -> None:
        """Stage all changes (git add -A)."""

    @abstractmethod
    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        """Return the diff between base and head refs."""

    @abstractmethod
    def get_commit_log(self, base: str, head: str = "HEAD") -> CommitLog:
        """Return the commit log between base and head refs."""

    @abstractmethod
    def get_current_branch(self) -> Branch:
        """Return the current branch."""

    @abstractmethod
    def get_default_branch(self) -> Branch:
        """Return the default branch (e.g. main, master)."""

    @abstractmethod
    def commit(self, message: str) -> CommitResult:
        """Create a commit with the given message."""


class GitHubPort(ABC):
    """Abstract interface for GitHub pull request operations."""

    @abstractmethod
    def find_existing_pr(self, branch: str) -> PullRequest | None:
        """Find an open PR for the given branch, or None if none exists."""

    @abstractmethod
    def create_pr(
        self,
        title: str,
        body: str,
        base: str,
        head: str,
        draft: bool = False,
    ) -> PullRequestResult:
        """Create a new pull request."""

    @abstractmethod
    def update_pr(self, number: int, title: str, body: str) -> PullRequestResult:
        """Update an existing pull request's title and body."""
