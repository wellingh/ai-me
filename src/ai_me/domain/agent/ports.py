"""Agent bounded context — ports for LLM interactions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_me.domain.routine.models import CommitMessageResult, PullRequestDescriptionResult
from ai_me.domain.workspace.models import Branch, CommitLog, Diff


class CommitMessageLLMPort(ABC):
    """Abstract interface for generating commit messages via LLM."""

    @abstractmethod
    def generate_commit_message(self, diff: Diff) -> CommitMessageResult:
        """Generate a conventional commit message from a diff."""

    @abstractmethod
    def refine_commit_message(
        self,
        diff: Diff,
        previous_message: str,
        feedback: str,
    ) -> CommitMessageResult:
        """Refine a previously generated commit message based on user feedback."""


class PullRequestLLMPort(ABC):
    """Abstract interface for generating PR descriptions via LLM."""

    @abstractmethod
    def generate_pr_description(
        self,
        diff: Diff,
        log: CommitLog,
        branch: Branch,
    ) -> PullRequestDescriptionResult:
        """Generate a PR title and body from diff, commit log, and branch info."""

    @abstractmethod
    def refine_pr_description(
        self,
        diff: Diff,
        log: CommitLog,
        branch: Branch,
        previous_result: PullRequestDescriptionResult,
        feedback: str,
    ) -> PullRequestDescriptionResult:
        """Refine a previously generated PR description based on user feedback."""
