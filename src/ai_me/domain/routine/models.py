"""Routine bounded context — command and result value objects for developer workflows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CommitCommand(BaseModel):
    """Input for the commit workflow."""

    model_config = ConfigDict(frozen=True)

    stage_all: bool = False


class CommitMessageResult(BaseModel):
    """The generated commit message from the LLM."""

    model_config = ConfigDict(frozen=True)

    message: str


class PullRequestCommand(BaseModel):
    """Input for the pull request workflow."""

    model_config = ConfigDict(frozen=True)

    base_branch: str | None = None
    draft: bool = False


class PullRequestDescriptionResult(BaseModel):
    """The generated PR title and body from the LLM."""

    model_config = ConfigDict(frozen=True)

    title: str
    body: str
