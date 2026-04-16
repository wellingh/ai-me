"""CLI command for ai commit."""

from __future__ import annotations

import typer
from rich.console import Console

from ai_me.cli.display import (
    ReviewAction,
    display_dry_run_skip,
    edit_text_in_editor,
    preview_commit_message,
    prompt_refinement_feedback,
    prompt_review_action,
)
from ai_me.cli.factory import create_commit_handler
from ai_me.domain.routine.errors import NothingStagedError
from ai_me.domain.routine.models import CommitCommand

console = Console()


def commit_command(
    ctx: typer.Context,
    all: bool = typer.Option(  # noqa: A002
        False,
        "-a",
        "--all",
        help="Stage all changes before committing",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="LLM model to use (e.g. openai:gpt-4o, anthropic:claude-sonnet-4-20250514)",
    ),
) -> None:
    """Generate an AI-powered commit message and commit staged changes."""
    dry_run: bool = ctx.obj.get("dry_run", False)
    on_skip = lambda desc: display_dry_run_skip(console, desc)

    handler = create_commit_handler(model, dry_run=dry_run, on_dry_run_skip=on_skip)
    command = CommitCommand(stage_all=all)

    try:
        result = handler.generate(command)
    except NothingStagedError:
        console.print("[red]No staged changes found.[/red] Stage files first or use the -a flag.")
        raise typer.Exit(1)

    message = result.message

    while True:
        preview_commit_message(console, message)
        action = prompt_review_action(console)

        if action == ReviewAction.SUBMIT:
            break
        elif action == ReviewAction.EDIT:
            message = edit_text_in_editor(message)
            break
        elif action == ReviewAction.REFINE:
            feedback = prompt_refinement_feedback(console)
            refined = handler.refine(feedback)
            message = refined.message
            continue
        elif action == ReviewAction.CANCEL:
            console.print("[yellow]Commit cancelled.[/yellow]")
            raise typer.Exit(0)

    commit_result = handler.execute(message)

    if dry_run:
        console.print("[yellow][DRY RUN][/yellow] Commit simulation complete.")
    else:
        console.print(f"[green]Committed:[/green] {commit_result.hash} {commit_result.message}")
