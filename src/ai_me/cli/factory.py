"""Composition root — wires infrastructure adapters into application handlers."""

from __future__ import annotations

from collections.abc import Callable

from ai_me.application.commit_handler import CommitHandler
from ai_me.application.pull_request_handler import PullRequestHandler
from ai_me.config import resolve_model_config
from ai_me.infrastructure.git.dry_run_git_adapter import DryRunGitAdapter
from ai_me.infrastructure.git.git_adapter import SubprocessGitAdapter
from ai_me.infrastructure.github.dry_run_github_adapter import DryRunGitHubAdapter
from ai_me.infrastructure.github.github_adapter import GhCliGitHubAdapter
from ai_me.infrastructure.llm.commit_agent import PydanticAICommitAgent
from ai_me.infrastructure.llm.pull_request_agent import PydanticAIPullRequestAgent


def create_commit_handler(
    model: str | None = None,
    *,
    dry_run: bool = False,
    on_dry_run_skip: Callable[[str], None] | None = None,
) -> CommitHandler:
    """Build a CommitHandler with real adapters (or dry-run wrappers)."""
    model_config = resolve_model_config("commit", cli_override=model)
    git_port = SubprocessGitAdapter()

    if dry_run:
        callback = on_dry_run_skip or (lambda msg: None)
        git_port = DryRunGitAdapter(git_port, on_skip=callback)

    return CommitHandler(
        git_port=git_port,
        llm_port=PydanticAICommitAgent(model_config),
    )


def create_pull_request_handler(
    model: str | None = None,
    *,
    dry_run: bool = False,
    on_dry_run_skip: Callable[[str], None] | None = None,
) -> PullRequestHandler:
    """Build a PullRequestHandler with real adapters (or dry-run wrappers)."""
    model_config = resolve_model_config("pr", cli_override=model)
    git_port = SubprocessGitAdapter()
    github_port = GhCliGitHubAdapter()

    if dry_run:
        callback = on_dry_run_skip or (lambda msg: None)
        git_port = DryRunGitAdapter(git_port, on_skip=callback)
        github_port = DryRunGitHubAdapter(github_port, on_skip=callback)

    return PullRequestHandler(
        git_port=git_port,
        github_port=github_port,
        llm_port=PydanticAIPullRequestAgent(model_config),
    )
