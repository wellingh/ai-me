"""Pydantic AI adapter for generating commit messages."""

from __future__ import annotations

from pydantic_ai import Agent

from ai_me.domain.agent.ports import CommitMessageLLMPort
from ai_me.domain.routine.models import CommitMessageResult
from ai_me.domain.workspace.models import Diff
from ai_me.infrastructure.llm.config import ModelConfig
from ai_me.infrastructure.llm.models import CommitMessageOutput

COMMIT_SYSTEM_PROMPT = """\
You are a git commit message generator. Generate commit messages following the Conventional Commits specification.

Format: <type>(<scope>): <description>

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code (formatting, etc)
- refactor: A code change that neither fixes a bug nor adds a feature
- perf: A code change that improves performance
- test: Adding missing tests or correcting existing tests
- chore: Changes to the build process or auxiliary tools
- ci: Changes to CI configuration files and scripts
- build: Changes that affect the build system or external dependencies

Rules:
- Use imperative mood in the description ("add" not "added", "fix" not "fixed")
- Keep the first line under 72 characters
- Be specific and concise
- The scope is optional but recommended when applicable
- Do not end the description with a period
"""


class PydanticAICommitAgent(CommitMessageLLMPort):
    """Implements CommitMessageLLMPort using pydantic-ai."""

    def __init__(self, model_config: ModelConfig) -> None:
        self._agent = Agent(
            model=model_config.to_pydantic_ai_model(),
            output_type=CommitMessageOutput,
            system_prompt=COMMIT_SYSTEM_PROMPT,
        )

    def generate_commit_message(self, diff: Diff) -> CommitMessageResult:
        result = self._agent.run_sync(
            f"Generate a commit message for the following staged changes:\n\n{diff.content}"
        )
        return CommitMessageResult(message=result.output.format())

    def refine_commit_message(
        self,
        diff: Diff,
        previous_message: str,
        feedback: str,
    ) -> CommitMessageResult:
        prompt = (
            f"Generate a commit message for the following staged changes:\n\n{diff.content}"
            f"\n\nPrevious message: {previous_message}"
            f"\n\nUser feedback: {feedback}"
            "\n\nPlease generate an improved commit message incorporating the feedback."
        )
        result = self._agent.run_sync(prompt)
        return CommitMessageResult(message=result.output.format())
