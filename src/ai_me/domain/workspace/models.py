"""Workspace bounded context — value objects for the local developer environment."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Diff(BaseModel):
    """Represents a git diff between two refs."""

    model_config = ConfigDict(frozen=True)

    content: str
    files_changed: int
    insertions: int
    deletions: int


class CommitLogEntry(BaseModel):
    """A single commit in the log."""

    model_config = ConfigDict(frozen=True)

    hash: str
    message: str


class CommitLog(BaseModel):
    """An ordered list of commit log entries."""

    model_config = ConfigDict(frozen=True)

    entries: list[CommitLogEntry]

    def as_text(self) -> str:
        """Format as 'hash message' lines for LLM consumption."""
        return "\n".join(f"{e.hash} {e.message}" for e in self.entries)


class Branch(BaseModel):
    """Represents a git branch."""

    model_config = ConfigDict(frozen=True)

    name: str
    is_default: bool = False


class CommitResult(BaseModel):
    """Result of a successful git commit."""

    model_config = ConfigDict(frozen=True)

    hash: str
    message: str


class PullRequest(BaseModel):
    """An existing pull request on the remote."""

    model_config = ConfigDict(frozen=True)

    number: int
    title: str
    body: str
    url: str
    state: str


class PullRequestResult(BaseModel):
    """Result of creating or updating a pull request."""

    model_config = ConfigDict(frozen=True)

    url: str
    number: int
    created: bool
