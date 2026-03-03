"""Claude CLI wrapper for invoking Claude commands and capturing output."""

import json
import subprocess
from dataclasses import dataclass


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
) -> ClaudeResponse:
    """
    Invoke Claude CLI with the given prompt and options.

    Args:
        prompt: The main prompt to send to Claude
        context: Additional context to prepend to the prompt
        system_prompt: Custom system prompt to override default
        model: Model to use (e.g., 'sonnet', 'opus', 'haiku')
        output_format: Output format ('text' or 'json')

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

    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    cmd.append(full_prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return ClaudeResponse(
                result="",
                raw_output=result.stderr,
                success=False,
                error=result.stderr or "Claude CLI returned non-zero exit code",
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
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error="Claude CLI timed out after 300 seconds",
        )
    except FileNotFoundError:
        return ClaudeResponse(
            result="",
            raw_output="",
            success=False,
            error="Claude CLI not found. Make sure 'claude' is installed and in PATH.",
        )
