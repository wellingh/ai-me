"""Tests for DryRunGitHubAdapter."""

from ai_me.domain.workspace.models import PullRequest, PullRequestResult
from ai_me.domain.workspace.ports import GitHubPort
from ai_me.infrastructure.github.dry_run_github_adapter import DryRunGitHubAdapter


EXISTING_PR = PullRequest(
    number=42,
    title="feat: auth",
    body="Adds auth",
    url="https://github.com/org/repo/pull/42",
    state="open",
)


class FakeInnerGitHubPort(GitHubPort):
    """Minimal inner adapter for testing delegation."""

    def __init__(self, existing_pr: PullRequest | None = None) -> None:
        self._existing_pr = existing_pr
        self.create_called = False
        self.update_called = False

    def find_existing_pr(self, branch: str) -> PullRequest | None:
        return self._existing_pr

    def create_pr(self, title, body, base, head, draft=False) -> PullRequestResult:
        self.create_called = True
        return PullRequestResult(url="https://real", number=1, created=True)

    def update_pr(self, number, title, body) -> PullRequestResult:
        self.update_called = True
        return PullRequestResult(url="https://real", number=number, created=False)


class TestReadOperationsDelegate:
    def test_find_existing_pr_delegates(self):
        inner = FakeInnerGitHubPort(existing_pr=EXISTING_PR)
        adapter = DryRunGitHubAdapter(inner, on_skip=lambda _: None)

        result = adapter.find_existing_pr("feature/auth")

        assert result is not None
        assert result.number == 42

    def test_find_existing_pr_returns_none(self):
        inner = FakeInnerGitHubPort(existing_pr=None)
        adapter = DryRunGitHubAdapter(inner, on_skip=lambda _: None)

        assert adapter.find_existing_pr("feature/new") is None


class TestWriteOperationsSkipped:
    def test_create_pr_calls_on_skip_and_returns_stub(self):
        inner = FakeInnerGitHubPort()
        skipped: list[str] = []
        adapter = DryRunGitHubAdapter(inner, on_skip=skipped.append)

        result = adapter.create_pr("feat: auth", "body", "main", "feature/auth")

        assert inner.create_called is False
        assert result.url == "https://dry-run"
        assert result.number == 0
        assert result.created is True
        assert len(skipped) == 1
        assert "--base main" in skipped[0]
        assert "--head feature/auth" in skipped[0]

    def test_create_pr_includes_draft_flag(self):
        inner = FakeInnerGitHubPort()
        skipped: list[str] = []
        adapter = DryRunGitHubAdapter(inner, on_skip=skipped.append)

        adapter.create_pr("feat: auth", "body", "main", "feature/auth", draft=True)

        assert "--draft" in skipped[0]

    def test_create_pr_omits_draft_flag_when_false(self):
        inner = FakeInnerGitHubPort()
        skipped: list[str] = []
        adapter = DryRunGitHubAdapter(inner, on_skip=skipped.append)

        adapter.create_pr("feat: auth", "body", "main", "feature/auth", draft=False)

        assert "--draft" not in skipped[0]

    def test_update_pr_calls_on_skip_and_returns_stub(self):
        inner = FakeInnerGitHubPort()
        skipped: list[str] = []
        adapter = DryRunGitHubAdapter(inner, on_skip=skipped.append)

        result = adapter.update_pr(42, "new title", "new body")

        assert inner.update_called is False
        assert result.url == "https://dry-run"
        assert result.number == 42
        assert result.created is False
        assert len(skipped) == 1
        assert "gh pr edit 42" in skipped[0]
