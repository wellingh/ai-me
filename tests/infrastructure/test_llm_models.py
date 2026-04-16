"""Tests for LLM output models."""

from ai_me.infrastructure.llm.models import CommitMessageOutput, PullRequestOutput


class TestCommitMessageOutput:
    def test_format_with_scope(self):
        output = CommitMessageOutput(type="feat", scope="auth", description="add login endpoint")
        assert output.format() == "feat(auth): add login endpoint"

    def test_format_without_scope(self):
        output = CommitMessageOutput(type="fix", scope=None, description="correct typo in readme")
        assert output.format() == "fix: correct typo in readme"


class TestPullRequestOutput:
    def test_format_body_full(self):
        output = PullRequestOutput(
            title="feat(auth): add login",
            summary="This PR adds login functionality.",
            notable_changes=["Added login endpoint", "Added JWT handling"],
            reasoning="Used JWT for stateless auth.",
            testing="Added unit tests for login handler.",
        )
        body = output.format_body()
        assert "This PR adds login functionality." in body
        assert "### Notable changes" in body
        assert "- Added login endpoint" in body
        assert "- Added JWT handling" in body
        assert "### Reasoning" in body
        assert "Used JWT for stateless auth." in body
        assert "### Testing" in body
        assert "Added unit tests for login handler." in body

    def test_format_body_minimal(self):
        output = PullRequestOutput(
            title="fix: typo",
            summary="Fixed a typo.",
            notable_changes=[],
            reasoning=None,
            testing=None,
        )
        body = output.format_body()
        assert "Fixed a typo." in body
        assert "### Notable changes" not in body
        assert "### Reasoning" not in body
        assert "### Testing" not in body
