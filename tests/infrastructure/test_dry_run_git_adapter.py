"""Tests for DryRunGitAdapter."""

from ai_me.domain.workspace.models import Branch, CommitLog, CommitLogEntry, Diff
from ai_me.domain.workspace.ports import GitPort
from ai_me.infrastructure.git.dry_run_git_adapter import DryRunGitAdapter


SAMPLE_DIFF = Diff(
    content="diff --git a/main.py b/main.py\n+print('hello')",
    files_changed=1,
    insertions=1,
    deletions=0,
)

SAMPLE_LOG = CommitLog(
    entries=[CommitLogEntry(hash="abc123", message="feat: init")]
)


class FakeInnerGitPort(GitPort):
    """Minimal inner adapter for testing delegation."""

    def __init__(self) -> None:
        self.stage_all_called = False
        self.commit_called_with: str | None = None

    def get_staged_diff(self) -> Diff | None:
        return SAMPLE_DIFF

    def stage_all(self) -> None:
        self.stage_all_called = True

    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        return SAMPLE_DIFF

    def get_commit_log(self, base: str, head: str = "HEAD") -> CommitLog:
        return SAMPLE_LOG

    def get_current_branch(self) -> Branch:
        return Branch(name="feature/test")

    def get_default_branch(self) -> Branch:
        return Branch(name="main", is_default=True)

    def commit(self, message: str):
        self.commit_called_with = message
        from ai_me.domain.workspace.models import CommitResult

        return CommitResult(hash="real123", message=message)


class TestReadOperationsDelegate:
    def test_get_staged_diff_delegates(self):
        inner = FakeInnerGitPort()
        adapter = DryRunGitAdapter(inner, on_skip=lambda _: None)
        assert adapter.get_staged_diff() == SAMPLE_DIFF

    def test_get_diff_delegates(self):
        inner = FakeInnerGitPort()
        adapter = DryRunGitAdapter(inner, on_skip=lambda _: None)
        assert adapter.get_diff("main") == SAMPLE_DIFF

    def test_get_commit_log_delegates(self):
        inner = FakeInnerGitPort()
        adapter = DryRunGitAdapter(inner, on_skip=lambda _: None)
        assert adapter.get_commit_log("main") == SAMPLE_LOG

    def test_get_current_branch_delegates(self):
        inner = FakeInnerGitPort()
        adapter = DryRunGitAdapter(inner, on_skip=lambda _: None)
        assert adapter.get_current_branch().name == "feature/test"

    def test_get_default_branch_delegates(self):
        inner = FakeInnerGitPort()
        adapter = DryRunGitAdapter(inner, on_skip=lambda _: None)
        branch = adapter.get_default_branch()
        assert branch.name == "main"
        assert branch.is_default is True


class TestWriteOperationsSkipped:
    def test_stage_all_calls_on_skip(self):
        inner = FakeInnerGitPort()
        skipped: list[str] = []
        adapter = DryRunGitAdapter(inner, on_skip=skipped.append)

        adapter.stage_all()

        assert inner.stage_all_called is False
        assert skipped == ["git add -A"]

    def test_commit_calls_on_skip_and_returns_stub(self):
        inner = FakeInnerGitPort()
        skipped: list[str] = []
        adapter = DryRunGitAdapter(inner, on_skip=skipped.append)

        result = adapter.commit("feat: add login")

        assert inner.commit_called_with is None
        assert result.hash == "dry-run"
        assert result.message == "feat: add login"
        assert skipped == ["git commit -m 'feat: add login'"]
