"""Use case handler for the pull request workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ai_me.domain.agent.ports import PullRequestLLMPort
from ai_me.domain.routine.errors import NoChangesError
from ai_me.domain.routine.models import PullRequestCommand, PullRequestDescriptionResult
from ai_me.domain.workspace.models import (
    Branch,
    CommitLog,
    Diff,
    PullRequest,
    PullRequestResult,
)
from ai_me.domain.workspace.ports import GitHubPort, GitPort


class PullRequestContext(BaseModel):
    """Intermediate data gathered before calling the LLM."""

    model_config = ConfigDict(frozen=True)

    diff: Diff
    log: CommitLog
    branch: Branch
    base_branch: Branch
    existing_pr: PullRequest | None = None


class PullRequestHandler:
    """Orchestrates the PR workflow: gather context, generate description, create/update."""

    def __init__(
        self,
        git_port: GitPort,
        github_port: GitHubPort,
        llm_port: PullRequestLLMPort,
    ) -> None:
        self._git = git_port
        self._github = github_port
        self._llm = llm_port
        self._last_context: PullRequestContext | None = None

    def gather_context(self, command: PullRequestCommand) -> PullRequestContext:
        """Phase 1: Collect all git and GitHub context."""
        branch = self._git.get_current_branch()
        base = (
            Branch(name=command.base_branch)
            if command.base_branch
            else self._git.get_default_branch()
        )
        diff = self._git.get_diff(base.name, "HEAD")

        if not diff.content.strip():
            raise NoChangesError(
                f"No changes between {base.name} and {branch.name}."
            )

        log = self._git.get_commit_log(base.name, "HEAD")
        existing_pr = self._github.find_existing_pr(branch.name)

        context = PullRequestContext(
            diff=diff,
            log=log,
            branch=branch,
            base_branch=base,
            existing_pr=existing_pr,
        )
        self._last_context = context
        return context

    def generate(self, context: PullRequestContext) -> PullRequestDescriptionResult:
        """Phase 2: Generate PR description via LLM."""
        return self._llm.generate_pr_description(
            context.diff, context.log, context.branch
        )

    def refine(self, feedback: str) -> PullRequestDescriptionResult:
        """Re-generate a PR description incorporating user feedback.

        Must be called after gather_context().
        """
        if self._last_context is None:
            raise NoChangesError("No context available. Call gather_context() first.")

        ctx = self._last_context
        return self._llm.refine_pr_description(
            diff=ctx.diff,
            log=ctx.log,
            branch=ctx.branch,
            previous_result=PullRequestDescriptionResult(title="", body=""),
            feedback=feedback,
        )

    def create(
        self,
        title: str,
        body: str,
        base: str,
        head: str,
        draft: bool = False,
    ) -> PullRequestResult:
        """Phase 3a: Create a new pull request."""
        return self._github.create_pr(title, body, base, head, draft)

    def update(self, pr_number: int, title: str, body: str) -> PullRequestResult:
        """Phase 3b: Update an existing pull request."""
        return self._github.update_pr(pr_number, title, body)
