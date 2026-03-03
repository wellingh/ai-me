"""Claude CLI wrapper for invoking Claude commands and capturing output."""

import json
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Response from Claude CLI invocation."""

    result: str
    raw_output: str
    success: bool
    error: str | None = None


def invoke_claude(
    prompt: str,
    context: str = "",
    system_prompt: str | None = None,
    model: str | None = None,
    output_format: str = "text",
    allowed_tools: list[str] | None = None,
) -> ClaudeResponse:
    """
    Invoke Claude CLI with the given prompt and options.

    Args:
        prompt: The main prompt to send to Claude
        context: Additional context to prepend to the prompt
        system_prompt: Custom system prompt to override default
        model: Model to use (e.g., 'sonnet', 'opus', 'haiku')
        output_format: Output format ('text' or 'json')
        allowed_tools: Tools Claude may use (e.g. ['Read', 'Bash(git diff*)', 'Write'])

    Returns:
        ClaudeResponse with the result and metadata
    """
    cmd = ["claude", "-p"]

    if output_format == "json":
        cmd.extend(["--output-format", "json"])

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    if model:
        cmd.extend(["--model", model])

    if allowed_tools:
        cmd.extend(["--allowedTools", *allowed_tools])
        cmd.extend(["--permission-mode", "bypassPermissions"])

    full_prompt = f"{context}\n\n{prompt}" if context else prompt

    logger.debug("Running command: %s", " ".join(cmd) + " (prompt via stdin)")
    logger.debug("Prompt length: %d chars", len(full_prompt))

    try:
        timeout = 600 if allowed_tools else 300
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        logger.debug("Exit code: %d", result.returncode)
        logger.debug("Stdout (%d chars): %s", len(result.stdout), result.stdout[:500])

        if result.returncode != 0:
            error_detail = (
                f"Claude CLI exited with code {result.returncode}\n"
                f"stderr: {result.stderr[:1000]}\n"
                f"stdout: {result.stdout[:1000]}"
            )
            logger.error(error_detail)
            return ClaudeResponse(
                result="",
                raw_output=result.stderr,
                success=False,
                error=error_detail,
            )

        output = result.stdout.strip()

        if output_format == "json":
            try:
                parsed = json.loads(output)
                return ClaudeResponse(
                    result=parsed.get("result", output),
                    raw_output=output,
                    success=True,
                )
            except json.JSONDecodeError:
                return ClaudeResponse(
                    result=output,
                    raw_output=output,
                    success=True,
                )

        return ClaudeResponse(
            result=output,
            raw_output=output,
            success=True,
        )

    except subprocess.TimeoutExpired:
        limit = 600 if allowed_tools else 300
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error=f"Claude CLI timed out after {limit} seconds",
        )
    except FileNotFoundError:
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error="Claude CLI not found. Make sure 'claude' is installed and in PATH.",
        )
