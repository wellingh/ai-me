"""Tests for PullRequestHandler with mock ports."""

import pytest

from ai_me.application.pull_request_handler import PullRequestHandler
from ai_me.domain.agent.ports import PullRequestLLMPort
from ai_me.domain.routine.errors import NoChangesError
from ai_me.domain.routine.models import PullRequestCommand, PullRequestDescriptionResult
from ai_me.domain.workspace.models import (
    Branch,
    CommitLog,
    CommitLogEntry,
    CommitResult,
    Diff,
    PullRequest,
    PullRequestResult,
)
from ai_me.domain.workspace.ports import GitHubPort, GitPort


SAMPLE_DIFF = Diff(
    content="diff --git a/auth.py b/auth.py\n+def login():\n+    pass",
    files_changed=1,
    insertions=2,
    deletions=0,
)

SAMPLE_LOG = CommitLog(
    entries=[
        CommitLogEntry(hash="abc123", message="feat: add login"),
        CommitLogEntry(hash="def456", message="feat: add logout"),
    ]
)


class FakeGitPort(GitPort):
    def __init__(
        self,
        diff: Diff = SAMPLE_DIFF,
        log: CommitLog = SAMPLE_LOG,
        branch: str = "feature/auth",
        default_branch: str = "main",
    ):
        self._diff = diff
        self._log = log
        self._branch = branch
        self._default_branch = default_branch

    def get_staged_diff(self) -> Diff | None:
        return None

    def stage_all(self) -> None:
        pass

    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        return self._diff

    def get_commit_log(self, base: str, head: str = "HEAD") -> CommitLog:
        return self._log

    def get_current_branch(self) -> Branch:
        return Branch(name=self._branch)

    def get_default_branch(self) -> Branch:
        return Branch(name=self._default_branch, is_default=True)

    def commit(self, message: str) -> CommitResult:
        return CommitResult(hash="abc1234", message=message)


class FakeGitHubPort(GitHubPort):
    def __init__(self, existing_pr: PullRequest | None = None):
        self._existing_pr = existing_pr
        self.created_pr: dict | None = None
        self.updated_pr: dict | None = None

    def find_existing_pr(self, branch: str) -> PullRequest | None:
        return self._existing_pr

    def create_pr(self, title, body, base, head, draft=False) -> PullRequestResult:
        self.created_pr = {"title": title, "body": body, "base": base, "head": head, "draft": draft}
        return PullRequestResult(url="https://github.com/org/repo/pull/1", number=1, created=True)

    def update_pr(self, number, title, body) -> PullRequestResult:
        self.updated_pr = {"number": number, "title": title, "body": body}
        return PullRequestResult(url="https://github.com/org/repo/pull/1", number=number, created=False)


class FakeLLMPort(PullRequestLLMPort):
    def generate_pr_description(self, diff, log, branch) -> PullRequestDescriptionResult:
        return PullRequestDescriptionResult(
            title="feat(auth): add authentication system",
            body="This PR adds the authentication system.\n\n### Notable changes\n- Added login and logout",
        )

    def refine_pr_description(self, diff, log, branch, previous_result, feedback):
        return PullRequestDescriptionResult(
            title=f"refined: {feedback}",
            body="Refined body",
        )


class TestGatherContext:
    def test_gathers_context(self):
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        context = handler.gather_context(PullRequestCommand())
        assert context.branch.name == "feature/auth"
        assert context.base_branch.name == "main"
        assert context.diff == SAMPLE_DIFF
        assert context.log == SAMPLE_LOG
        assert context.existing_pr is None

    def test_uses_custom_base_branch(self):
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        context = handler.gather_context(PullRequestCommand(base_branch="develop"))
        assert context.base_branch.name == "develop"

    def test_finds_existing_pr(self):
        existing = PullRequest(
            number=42, title="old title", body="old body",
            url="https://github.com/org/repo/pull/42", state="open",
        )
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(existing_pr=existing),
            llm_port=FakeLLMPort(),
        )
        context = handler.gather_context(PullRequestCommand())
        assert context.existing_pr is not None
        assert context.existing_pr.number == 42

    def test_raises_when_no_changes(self):
        empty_diff = Diff(content="  ", files_changed=0, insertions=0, deletions=0)
        handler = PullRequestHandler(
            git_port=FakeGitPort(diff=empty_diff),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        with pytest.raises(NoChangesError):
            handler.gather_context(PullRequestCommand())


class TestGenerate:
    def test_generates_description(self):
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        context = handler.gather_context(PullRequestCommand())
        result = handler.generate(context)
        assert result.title == "feat(auth): add authentication system"
        assert "Notable changes" in result.body


class TestRefine:
    def test_refine_after_gather(self):
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        handler.gather_context(PullRequestCommand())
        result = handler.refine("shorter title")
        assert "refined: shorter title" in result.title

    def test_refine_without_context_raises(self):
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=FakeGitHubPort(),
            llm_port=FakeLLMPort(),
        )
        with pytest.raises(NoChangesError):
            handler.refine("some feedback")


class TestCreateAndUpdate:
    def test_create_pr(self):
        github = FakeGitHubPort()
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=github,
            llm_port=FakeLLMPort(),
        )
        result = handler.create("title", "body", "main", "feature/auth")
        assert result.created is True
        assert result.number == 1
        assert github.created_pr is not None
        assert github.created_pr["title"] == "title"

    def test_update_pr(self):
        github = FakeGitHubPort()
        handler = PullRequestHandler(
            git_port=FakeGitPort(),
            github_port=github,
            llm_port=FakeLLMPort(),
        )
        result = handler.update(42, "new title", "new body")
        assert result.created is False
        assert result.number == 42
        assert github.updated_pr is not None
        assert github.updated_pr["title"] == "new title"
