"""Tests for routine domain models."""

from ai_me.domain.routine.models import (
    CommitCommand,
    CommitMessageResult,
    PullRequestCommand,
    PullRequestDescriptionResult,
)


class TestCommitCommand:
    def test_defaults(self):
        cmd = CommitCommand()
        assert cmd.stage_all is False

    def test_stage_all(self):
        cmd = CommitCommand(stage_all=True)
        assert cmd.stage_all is True


class TestCommitMessageResult:
    def test_message(self):
        result = CommitMessageResult(message="feat(auth): add JWT refresh")
        assert result.message == "feat(auth): add JWT refresh"


class TestPullRequestCommand:
    def test_defaults(self):
        cmd = PullRequestCommand()
        assert cmd.base_branch is None
        assert cmd.draft is False

    def test_with_base(self):
        cmd = PullRequestCommand(base_branch="develop", draft=True)
        assert cmd.base_branch == "develop"
        assert cmd.draft is True


class TestPullRequestDescriptionResult:
    def test_creation(self):
        result = PullRequestDescriptionResult(
            title="feat(auth): add JWT refresh",
            body="This PR adds JWT token refresh.",
        )
        assert result.title == "feat(auth): add JWT refresh"
        assert result.body == "This PR adds JWT token refresh."
