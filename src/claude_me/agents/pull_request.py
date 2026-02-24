"""Pull request description agent following Linus Torvalds' kernel PR guidelines."""

from claude_me.claude import ClaudeResponse, invoke_claude

PR_SYSTEM_PROMPT = """You are a pull request description generator. Generate PR descriptions that serve as meaningful historical records, following the principles outlined by Linus Torvalds for Linux kernel pull requests.

## Title Format (Conventional Commits)

The FIRST line of your output MUST be a Conventional Commits title:

    <type>(<scope>): <description>

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

Rules for the title:
- Use imperative mood ("add" not "added", "fix" not "fixed")
- Keep under 72 characters
- The scope is optional but recommended when applicable
- Do not end the description with a period

## Body (after a blank line)

Write the body following Linus Torvalds' pull request philosophy:

### 1. Explain WHAT you are pulling and WHY it should be merged

The reader must understand what this set of changes does and why it matters. This is not a changelog — it is a narrative that justifies the merge. The description must make sense not just at review time, but as a historical record months or years later.

### 2. Derive the WHY from the code itself

- Analyze the actual code diff: look at comments, docstrings, variable names, and function signatures to understand the intent behind the changes.
- If the code adds comments explaining a decision, surface that reasoning in the PR description.
- Do not just describe what changed mechanically — explain the motivation and reasoning that the code reveals.

### 3. Explain anything unusual

- If the changes touch files outside the normal scope, explain WHY.
- If there are risky changes or edge cases, call them out explicitly.
- If the timing is unusual (e.g., late changes, post-freeze fixes), explain what happened and why it could not wait.

### 4. For refactoring changes, use SOLID principles to explain WHY

When the change is a refactoring, explain the motivation using the applicable SOLID principles:
- Single Responsibility Principle: a class/module had too many responsibilities and was split
- Open/Closed Principle: code was restructured to be extensible without modification
- Liskov Substitution Principle: subtype contracts were being violated and were corrected
- Interface Segregation Principle: a fat interface was broken into focused ones
- Dependency Inversion Principle: concrete dependencies were replaced with abstractions

Only reference the specific principles that actually apply. Do not force-fit principles that are not relevant.

### 5. Use the commit history to tell the story

- The commit log shows the evolution of the work. Use it to understand the sequence of decisions.
- Group related commits into coherent themes or sections.
- Reference significant individual commits when they add important context.

### 6. Structure

Use clear sections in the body as needed:
- A high-level summary paragraph
- Notable changes or new components (use bullet points or indented lists)
- Reasoning for non-obvious decisions
- Testing or validation notes if visible in the changes

## Output Format

Return ONLY the PR description. No explanations, no markdown fences around the output.
First line is the title, then a blank line, then the body."""


def generate_pr_description(
    log: str, diff: str, model: str | None = None
) -> ClaudeResponse:
    """
    Generate a pull request description from the commit log and diff.

    Args:
        log: The git log output (commits between base and HEAD)
        diff: The git diff output (changes between base and HEAD)
        model: Optional model to use (defaults to Claude's default)

    Returns:
        ClaudeResponse with the generated PR description
    """
    if not diff.strip() and not log.strip():
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error="No changes found between the current branch and the base branch",
        )

    context = f"## Commit History\n\n```\n{log}\n```\n\n## Combined Diff\n\n```diff\n{diff}\n```"
    prompt = "Generate a pull request description for the following changes:"

    response = invoke_claude(
        prompt=prompt,
        context=context,
        system_prompt=PR_SYSTEM_PROMPT,
        model=model,
    )

    if response.success:
        response.result = _clean_response(response.result)

    return response


def refine_pr_description(
    current_description: str,
    user_instructions: str,
    log: str,
    diff: str,
    model: str | None = None,
) -> ClaudeResponse:
    """
    Refine an existing PR description based on user instructions.

    Args:
        current_description: The previously generated PR description
        user_instructions: Free-text instructions from the user on what to change
        log: The git log output (for context)
        diff: The git diff output (for context)
        model: Optional model to use

    Returns:
        ClaudeResponse with the refined PR description
    """
    context = (
        f"## Current PR Description\n\n{current_description}\n\n"
        f"## User Instructions\n\n{user_instructions}\n\n"
        f"## Commit History\n\n```\n{log}\n```\n\n"
        f"## Combined Diff\n\n```diff\n{diff}\n```"
    )
    prompt = (
        "Revise the PR description above according to the user's instructions. "
        "Keep the same Conventional Commits title format and Linus Torvalds style. "
        "Apply only the changes the user asked for — preserve everything else."
    )

    response = invoke_claude(
        prompt=prompt,
        context=context,
        system_prompt=PR_SYSTEM_PROMPT,
        model=model,
    )

    if response.success:
        response.result = _clean_response(response.result)

    return response


def _clean_response(text: str) -> str:
    """Strip markdown fences and quotes from Claude's response."""
    text = text.strip().strip("\"'`")
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return text.strip()
