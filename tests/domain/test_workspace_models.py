"""Tests for workspace domain models."""

from ai_me.domain.workspace.models import (
    Branch,
    CommitLog,
    CommitLogEntry,
    CommitResult,
    Diff,
    PullRequest,
    PullRequestResult,
)


class TestDiff:
    def test_frozen(self):
        diff = Diff(content="diff", files_changed=1, insertions=5, deletions=2)
        assert diff.content == "diff"
        assert diff.files_changed == 1

    def test_immutable(self):
        diff = Diff(content="diff", files_changed=1, insertions=5, deletions=2)
        try:
            diff.content = "other"
            assert False, "Should have raised"
        except Exception:
            pass


class TestCommitLog:
    def test_as_text(self):
        log = CommitLog(
            entries=[
                CommitLogEntry(hash="abc123", message="feat: add login"),
                CommitLogEntry(hash="def456", message="fix: typo"),
            ]
        )
        text = log.as_text()
        assert "abc123 feat: add login" in text
        assert "def456 fix: typo" in text

    def test_empty_log(self):
        log = CommitLog(entries=[])
        assert log.as_text() == ""


class TestBranch:
    def test_defaults(self):
        branch = Branch(name="feature/auth")
        assert branch.name == "feature/auth"
        assert branch.is_default is False

    def test_default_branch(self):
        branch = Branch(name="main", is_default=True)
        assert branch.is_default is True


class TestCommitResult:
    def test_creation(self):
        result = CommitResult(hash="abc1234", message="feat: add login")
        assert result.hash == "abc1234"
        assert result.message == "feat: add login"


class TestPullRequest:
    def test_creation(self):
        pr = PullRequest(
            number=42,
            title="feat: add auth",
            body="Some body",
            url="https://github.com/org/repo/pull/42",
            state="open",
        )
        assert pr.number == 42
        assert pr.state == "open"


class TestPullRequestResult:
    def test_created(self):
        result = PullRequestResult(
            url="https://github.com/org/repo/pull/42",
            number=42,
            created=True,
        )
        assert result.created is True

    def test_updated(self):
        result = PullRequestResult(
            url="https://github.com/org/repo/pull/42",
            number=42,
            created=False,
        )
        assert result.created is False
