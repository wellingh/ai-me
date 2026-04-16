"""Use case handler for the commit workflow."""

from __future__ import annotations

from ai_me.domain.agent.ports import CommitMessageLLMPort
from ai_me.domain.routine.errors import NothingStagedError
from ai_me.domain.routine.models import CommitCommand, CommitMessageResult
from ai_me.domain.workspace.models import CommitResult, Diff
from ai_me.domain.workspace.ports import GitPort


class CommitHandler:
    """Orchestrates the commit workflow: generate message, then execute commit."""

    def __init__(self, git_port: GitPort, llm_port: CommitMessageLLMPort) -> None:
        self._git = git_port
        self._llm = llm_port
        self._last_diff: Diff | None = None

    def generate(self, command: CommitCommand) -> CommitMessageResult:
        """Phase 1: Gather context and generate a commit message via LLM.

        Stores the diff internally for use in refine().
        """
        if command.stage_all:
            self._git.stage_all()

        diff = self._git.get_staged_diff()
        if diff is None or not diff.content.strip():
            raise NothingStagedError("No staged changes found.")

        self._last_diff = diff
        return self._llm.generate_commit_message(diff)

    def refine(self, feedback: str) -> CommitMessageResult:
        """Re-generate a commit message incorporating user feedback.

        Must be called after generate().
        """
        if self._last_diff is None:
            raise NothingStagedError("No diff available. Call generate() first.")

        return self._llm.refine_commit_message(
            diff=self._last_diff,
            previous_message="",
            feedback=feedback,
        )

    def execute(self, message: str) -> CommitResult:
        """Phase 2: Perform the actual git commit."""
        return self._git.commit(message)
