"""Code review agent for reviewing PR diffs and suggesting fixes."""

import json
from dataclasses import dataclass, field

from ai_me.claude import invoke_claude

REVIEW_SYSTEM_PROMPT = """You are a senior code reviewer. You review code changes (diffs) and the full source files to find issues and suggest concrete fixes.

## Your Task

Analyze the code changes and identify:
1. **Bugs**: Logic errors, off-by-one errors, null/None handling, race conditions, missing error handling
2. **Code quality**: Code smells, duplication, unclear naming, overly complex logic
3. **Improvements**: Better patterns, missing type hints, performance improvements

## Rules

- ONLY review code that was CHANGED in the diff. Do not review unchanged code.
- Each finding MUST include a concrete fix (original + replacement text).
- The `original` field must be an EXACT substring of the current file content. Copy it precisely including whitespace and indentation.
- The `replacement` field is what should replace the original text.
- Keep fixes minimal and focused. One finding = one logical change.
- Explain WHY the change is better, not just what it does.
- Use severity levels appropriately:
  - "error": Bugs, crashes, security issues, data loss risks
  - "warning": Code quality issues, missing error handling, potential edge cases
  - "suggestion": Style improvements, better patterns, minor enhancements
- If you find no issues, return an empty findings array.
- Do NOT suggest changes that are purely stylistic preferences with no functional benefit.

## Output Format

Return a JSON object with this exact structure:
{
    "findings": [
        {
            "file": "path/to/file.py",
            "severity": "error|warning|suggestion",
            "title": "Short description of the issue",
            "explanation": "Clear explanation of what is wrong and why the fix is better",
            "original": "exact text from the file to replace",
            "replacement": "the corrected text",
            "line_hint": 42
        }
    ]
}

Return ONLY the JSON object. No markdown fences, no explanations outside the JSON."""


@dataclass
class ReviewFinding:
    """A single code review finding with a suggested fix."""

    file: str
    severity: str
    title: str
    explanation: str
    original: str
    replacement: str
    line_hint: int = 0


@dataclass
class ReviewResult:
    """Result of a code review containing multiple findings."""

    findings: list[ReviewFinding] = field(default_factory=list)
    success: bool = True
    error: str | None = None


def review_diff(
    diff: str,
    file_contents: dict[str, str],
    model: str | None = None,
) -> ReviewResult:
    """
    Review a diff and return structured findings with suggested fixes.

    Args:
        diff: The git diff output (changes against base branch)
        file_contents: Dict mapping file paths to their full contents
        model: Optional model to use

    Returns:
        ReviewResult with list of findings
    """
    if not diff.strip():
        return ReviewResult(
            success=False,
            error="No changes to review",
        )

    context_parts = [f"## Diff\n\n```diff\n{diff}\n```"]

    for path, content in file_contents.items():
        context_parts.append(f"## File: {path}\n\n```\n{content}\n```")

    context = "\n\n".join(context_parts)
    prompt = "Review the following code changes and identify issues. Return your findings as JSON."

    response = invoke_claude(
        prompt=prompt,
        context=context,
        system_prompt=REVIEW_SYSTEM_PROMPT,
        model=model,
    )

    if not response.success:
        return ReviewResult(
            success=False,
            error=response.error,
        )

    return _parse_review_response(response.result)


def _parse_review_response(raw: str) -> ReviewResult:
    """Parse Claude's JSON response into ReviewResult."""
    text = raw.strip().strip("\"'`")
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ReviewResult(
            success=False,
            error=f"Failed to parse review response as JSON: {raw[:200]}",
        )

    if not isinstance(data, dict) or "findings" not in data:
        return ReviewResult(
            success=False,
            error="Response missing 'findings' key",
        )

    findings = []
    for item in data["findings"]:
        try:
            findings.append(
                ReviewFinding(
                    file=item["file"],
                    severity=item.get("severity", "suggestion"),
                    title=item["title"],
                    explanation=item["explanation"],
                    original=item["original"],
                    replacement=item["replacement"],
                    line_hint=item.get("line_hint", 0),
                )
            )
        except KeyError:
            continue

    return ReviewResult(findings=findings, success=True)
