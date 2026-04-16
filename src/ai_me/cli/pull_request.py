"""CLI command for ai pr."""

from __future__ import annotations

import typer
from rich.console import Console

from ai_me.cli.display import (
    PrAction,
    ReviewAction,
    display_dry_run_skip,
    edit_text_in_editor,
    preview_pr_description,
    prompt_pr_action,
    prompt_refinement_feedback,
    prompt_review_action,
)
from ai_me.cli.factory import create_pull_request_handler
from ai_me.domain.routine.errors import NoChangesError
from ai_me.domain.routine.models import PullRequestCommand

console = Console()


def pr_command(
    ctx: typer.Context,
    base: str | None = typer.Option(
        None,
        "--base",
        help="Base branch for the PR (defaults to repo default branch)",
    ),
    draft: bool = typer.Option(
        False,
        "--draft",
        help="Create the PR as a draft",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="LLM model to use (e.g. openai:gpt-4o, anthropic:claude-sonnet-4-20250514)",
    ),
) -> None:
    """Generate an AI-powered PR description and create/update a pull request."""
    dry_run: bool = ctx.obj.get("dry_run", False)
    on_skip = lambda desc: display_dry_run_skip(console, desc)

    handler = create_pull_request_handler(model, dry_run=dry_run, on_dry_run_skip=on_skip)
    command = PullRequestCommand(base_branch=base, draft=draft)

    try:
        context = handler.gather_context(command)
    except NoChangesError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    description = handler.generate(context)
    title = description.title
    body = description.body

    while True:
        preview_pr_description(console, title, body)
        action = prompt_review_action(console)

        if action == ReviewAction.SUBMIT:
            break
        elif action == ReviewAction.EDIT:
            full_text = f"{title}\n\n{body}"
            edited = edit_text_in_editor(full_text)
            parts = edited.split("\n", 1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""
            break
        elif action == ReviewAction.REFINE:
            feedback = prompt_refinement_feedback(console)
            refined = handler.refine(feedback)
            title = refined.title
            body = refined.body
            continue
        elif action == ReviewAction.CANCEL:
            console.print("[yellow]PR creation cancelled.[/yellow]")
            raise typer.Exit(0)

    if context.existing_pr:
        pr_action = prompt_pr_action(console, context.existing_pr.number)

        if pr_action == PrAction.CANCEL:
            console.print("[yellow]PR creation cancelled.[/yellow]")
            raise typer.Exit(0)
        elif pr_action == PrAction.UPDATE:
            result = handler.update(context.existing_pr.number, title, body)
            if dry_run:
                console.print("[yellow][DRY RUN][/yellow] PR update simulation complete.")
            else:
                console.print(f"[green]Updated PR #{result.number}:[/green] {result.url}")
            return
        # PrAction.CREATE falls through to create below

    result = handler.create(
        title, body,
        context.base_branch.name, context.branch.name,
        command.draft,
    )

    if dry_run:
        console.print("[yellow][DRY RUN][/yellow] PR creation simulation complete.")
    else:
        console.print(f"[green]Created PR #{result.number}:[/green] {result.url}")
