"""Pydantic AI adapter for generating pull request descriptions."""

from __future__ import annotations

from pydantic_ai import Agent

from ai_me.domain.agent.ports import PullRequestLLMPort
from ai_me.domain.routine.models import PullRequestDescriptionResult
from ai_me.domain.workspace.models import Branch, CommitLog, Diff
from ai_me.infrastructure.llm.config import ModelConfig
from ai_me.infrastructure.llm.models import PullRequestOutput

PULL_REQUEST_SYSTEM_PROMPT = """\
You generate pull request descriptions that serve as meaningful historical records, \
following the principles outlined by Linus Torvalds for Linux kernel pull requests.

## Title (Conventional Commits)

The title must be a Conventional Commits line: <type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build
- Imperative mood: "add" not "added", "fix" not "fixed"
- Under 72 characters
- Scope is optional but recommended
- No trailing period

## Body

### Explain WHAT and WHY
The reader must understand what this set of changes does and why it matters. This is \
not a changelog — it is a narrative that justifies the merge. The description must \
make sense not just at review time, but as a historical record months or years later.

### Derive the WHY from the code itself
Analyze the actual diff: look at comments, docstrings, variable names, and function \
signatures to understand the intent behind the changes. Do not mechanically describe \
what changed — explain the motivation and reasoning that the code reveals.

### Call out anything unusual
If the changes touch files outside the normal scope, explain WHY. If there are risky \
changes or edge cases, name them explicitly.

### For refactoring, cite SOLID principles
When the change is a refactoring, explain the motivation using the relevant principle \
(Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, \
Dependency Inversion). Only reference principles that actually apply.

### Use the commit history
The commit log shows the evolution of the work. Use it to understand the sequence of \
decisions, group related commits into themes, and reference significant individual \
commits when they add context.

## Sections
Only include sections that have meaningful content:
1. High-level summary — one paragraph for someone who has never seen the code
2. Notable changes — bullet list of key modifications or non-obvious decisions
3. Reasoning — non-obvious design choices, trade-offs, constraints
4. Testing — what tests were added/changed and what they cover
"""


class PydanticAIPullRequestAgent(PullRequestLLMPort):
    """Implements PullRequestLLMPort using pydantic-ai."""

    def __init__(self, model_config: ModelConfig) -> None:
        self._agent = Agent(
            model=model_config.to_pydantic_ai_model(),
            output_type=PullRequestOutput,
            system_prompt=PULL_REQUEST_SYSTEM_PROMPT,
        )

    def generate_pr_description(
        self,
        diff: Diff,
        log: CommitLog,
        branch: Branch,
    ) -> PullRequestDescriptionResult:
        prompt = self._build_prompt(diff, log, branch)
        result = self._agent.run_sync(prompt)
        return PullRequestDescriptionResult(
            title=result.output.title,
            body=result.output.format_body(),
        )

    def refine_pr_description(
        self,
        diff: Diff,
        log: CommitLog,
        branch: Branch,
        previous_result: PullRequestDescriptionResult,
        feedback: str,
    ) -> PullRequestDescriptionResult:
        prompt = (
            self._build_prompt(diff, log, branch)
            + f"\n\nPrevious title: {previous_result.title}"
            + f"\n\nPrevious body:\n{previous_result.body}"
            + f"\n\nUser feedback: {feedback}"
            + "\n\nPlease generate an improved PR description incorporating the feedback."
        )
        result = self._agent.run_sync(prompt)
        return PullRequestDescriptionResult(
            title=result.output.title,
            body=result.output.format_body(),
        )

    def _build_prompt(self, diff: Diff, log: CommitLog, branch: Branch) -> str:
        return (
            f"Generate a pull request description for branch '{branch.name}'.\n\n"
            f"## Commit History\n{log.as_text()}\n\n"
            f"## Diff\n{diff.content}"
        )
