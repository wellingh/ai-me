"""Commit message agent for generating conventional commit messages."""

from claude_me.claude import ClaudeResponse, invoke_claude

COMMIT_SYSTEM_PROMPT = """You are a git commit message generator. Generate commit messages following the Conventional Commits specification.

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

Return ONLY the commit message, no explanations, no markdown formatting, no quotes."""


def generate_commit_message(diff: str, model: str | None = None) -> ClaudeResponse:
    """
    Generate a conventional commit message from a git diff.

    Args:
        diff: The git diff output
        model: Optional model to use (defaults to Claude's default)

    Returns:
        ClaudeResponse with the generated commit message
    """
    if not diff.strip():
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error="No changes to commit",
        )

    prompt = "Generate a commit message for the following changes:"

    response = invoke_claude(
        prompt=prompt,
        context=f"```diff\n{diff}\n```",
        system_prompt=COMMIT_SYSTEM_PROMPT,
        model=model,
    )

    if response.success:
        # Clean up the response - remove any quotes or markdown
        message = response.result.strip()
        message = message.strip('"\'`')
        # Remove markdown code block if present
        if message.startswith("```"):
            lines = message.split("\n")
            message = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        response.result = message.strip()

    return response
