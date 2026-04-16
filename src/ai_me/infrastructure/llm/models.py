"""Pydantic output models for pydantic-ai structured responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CommitMessageOutput(BaseModel):
    """Structured output from the commit message agent."""

    type: str = Field(description="Conventional commit type: feat, fix, docs, style, refactor, perf, test, chore, ci, build")
    scope: str | None = Field(default=None, description="Optional scope of the change")
    description: str = Field(description="Imperative mood description, under 72 characters, no trailing period")

    def format(self) -> str:
        """Format as a conventional commit message string."""
        if self.scope:
            return f"{self.type}({self.scope}): {self.description}"
        return f"{self.type}: {self.description}"


class PullRequestOutput(BaseModel):
    """Structured output from the PR description agent."""

    title: str = Field(description="Conventional Commits title line, under 72 characters")
    summary: str = Field(description="High-level summary paragraph explaining what this PR does and why")
    notable_changes: list[str] = Field(description="List of notable changes with brief rationale")
    reasoning: str | None = Field(default=None, description="Non-obvious design choices, trade-offs, SOLID principles if applicable")
    testing: str | None = Field(default=None, description="Testing notes — what tests were added/changed and what they cover")

    def format_body(self) -> str:
        """Assemble the markdown body from sections, omitting empty ones."""
        sections: list[str] = [self.summary, ""]

        if self.notable_changes:
            sections.append("### Notable changes")
            for change in self.notable_changes:
                sections.append(f"- {change}")
            sections.append("")

        if self.reasoning:
            sections.append("### Reasoning")
            sections.append(self.reasoning)
            sections.append("")

        if self.testing:
            sections.append("### Testing")
            sections.append(self.testing)

        return "\n".join(sections)
