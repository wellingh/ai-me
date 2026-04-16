"""Tests for CommitHandler with mock ports."""

import pytest

from ai_me.application.commit_handler import CommitHandler
from ai_me.domain.agent.ports import CommitMessageLLMPort
from ai_me.domain.routine.errors import NothingStagedError
from ai_me.domain.routine.models import CommitCommand, CommitMessageResult
from ai_me.domain.workspace.models import Branch, CommitResult, Diff
from ai_me.domain.workspace.ports import GitPort


class FakeGitPort(GitPort):
    """Fake GitPort for testing."""

    def __init__(self, staged_diff: Diff | None = None):
        self._staged_diff = staged_diff
        self.staged_all = False
        self.committed_message: str | None = None

    def get_staged_diff(self) -> Diff | None:
        return self._staged_diff

    def stage_all(self) -> None:
        self.staged_all = True

    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        raise NotImplementedError

    def get_commit_log(self, base, head="HEAD"):
        raise NotImplementedError

    def get_current_branch(self) -> Branch:
        return Branch(name="feature/test")

    def get_default_branch(self) -> Branch:
        return Branch(name="main", is_default=True)

    def commit(self, message: str) -> CommitResult:
        self.committed_message = message
        return CommitResult(hash="abc1234", message=message)


class FakeLLMPort(CommitMessageLLMPort):
    """Fake LLM port for testing."""

    def __init__(self, message: str = "feat(auth): add login endpoint"):
        self._message = message

    def generate_commit_message(self, diff: Diff) -> CommitMessageResult:
        return CommitMessageResult(message=self._message)

    def refine_commit_message(self, diff, previous_message, feedback):
        return CommitMessageResult(message=f"refined: {feedback}")


SAMPLE_DIFF = Diff(
    content="diff --git a/main.py b/main.py\n+print('hello')",
    files_changed=1,
    insertions=1,
    deletions=0,
)


class TestCommitHandlerGenerate:
    def test_generates_message(self):
        handler = CommitHandler(
            git_port=FakeGitPort(staged_diff=SAMPLE_DIFF),
            llm_port=FakeLLMPort(),
        )
        result = handler.generate(CommitCommand())
        assert result.message == "feat(auth): add login endpoint"

    def test_raises_when_nothing_staged(self):
        handler = CommitHandler(
            git_port=FakeGitPort(staged_diff=None),
            llm_port=FakeLLMPort(),
        )
        with pytest.raises(NothingStagedError):
            handler.generate(CommitCommand())

    def test_raises_when_empty_diff(self):
        empty_diff = Diff(content="  ", files_changed=0, insertions=0, deletions=0)
        handler = CommitHandler(
            git_port=FakeGitPort(staged_diff=empty_diff),
            llm_port=FakeLLMPort(),
        )
        with pytest.raises(NothingStagedError):
            handler.generate(CommitCommand())

    def test_stages_all_when_requested(self):
        git = FakeGitPort(staged_diff=SAMPLE_DIFF)
        handler = CommitHandler(git_port=git, llm_port=FakeLLMPort())
        handler.generate(CommitCommand(stage_all=True))
        assert git.staged_all is True

    def test_does_not_stage_all_by_default(self):
        git = FakeGitPort(staged_diff=SAMPLE_DIFF)
        handler = CommitHandler(git_port=git, llm_port=FakeLLMPort())
        handler.generate(CommitCommand())
        assert git.staged_all is False


class TestCommitHandlerRefine:
    def test_refine_after_generate(self):
        handler = CommitHandler(
            git_port=FakeGitPort(staged_diff=SAMPLE_DIFF),
            llm_port=FakeLLMPort(),
        )
        handler.generate(CommitCommand())
        result = handler.refine("make it shorter")
        assert "refined: make it shorter" in result.message

    def test_refine_without_generate_raises(self):
        handler = CommitHandler(
            git_port=FakeGitPort(staged_diff=SAMPLE_DIFF),
            llm_port=FakeLLMPort(),
        )
        with pytest.raises(NothingStagedError):
            handler.refine("some feedback")


class TestCommitHandlerExecute:
    def test_executes_commit(self):
        git = FakeGitPort(staged_diff=SAMPLE_DIFF)
        handler = CommitHandler(git_port=git, llm_port=FakeLLMPort())
        result = handler.execute("feat: test commit")
        assert result.hash == "abc1234"
        assert result.message == "feat: test commit"
        assert git.committed_message == "feat: test commit"
