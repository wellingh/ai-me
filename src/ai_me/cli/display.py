"""Rich display helpers for previewing and confirming AI-generated content."""

from __future__ import annotations

import os
import tempfile
from enum import Enum

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt


class ReviewAction(str, Enum):
    """Actions available in the interactive review loop."""

    SUBMIT = "s"
    EDIT = "e"
    REFINE = "r"
    CANCEL = "c"


def preview_commit_message(console: Console, message: str) -> None:
    """Display a proposed commit message in a Rich panel."""
    console.print(Panel(message, title="Proposed Commit Message", border_style="cyan"))


def preview_pr_description(console: Console, title: str, body: str) -> None:
    """Display a proposed PR title and body in Rich panels."""
    console.print(Panel(title, title="PR Title", border_style="cyan"))
    console.print(Panel(Markdown(body), title="PR Description", border_style="cyan"))


def prompt_review_action(console: Console) -> ReviewAction:
    """Prompt the user to submit, edit, refine, or cancel."""
    console.print(
        "\n[bold][S][/bold]ubmit  /  "
        "[bold][E][/bold]dit  /  "
        "[bold][R][/bold]efine  /  "
        "[bold][C][/bold]ancel"
    )
    choice = Prompt.ask(
        "Choose an action",
        choices=["s", "e", "r", "c"],
        default="s",
    )
    return ReviewAction(choice)


def prompt_refinement_feedback(console: Console) -> str:
    """Ask the user for feedback to refine the AI output."""
    return Prompt.ask("[cyan]Describe what to change[/cyan]")


def edit_text_in_editor(text: str) -> str:
    """Open the text in the user's $EDITOR for manual editing."""
    editor = os.environ.get("EDITOR", "vim")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        f.flush()
        tmp_path = f.name

    os.system(f'{editor} "{tmp_path}"')

    with open(tmp_path) as f:
        edited = f.read()

    os.unlink(tmp_path)
    return edited


def display_dry_run_skip(console: Console, description: str) -> None:
    """Show a dry-run step that was skipped."""
    console.print(f"[yellow][DRY RUN][/yellow] Would execute: {description}")


def confirm_action(console: Console, prompt: str) -> bool:
    """Ask a yes/no confirmation question."""
    return Confirm.ask(prompt)


class PrAction(str, Enum):
    """Actions when an existing PR is found."""

    UPDATE = "update"
    CREATE = "create"
    CANCEL = "cancel"


def prompt_pr_action(console: Console, pr_number: int) -> PrAction:
    """Ask what to do when an existing PR is found."""
    console.print(f"\n[yellow]PR #{pr_number} already exists for this branch.[/yellow]")
    choice = Prompt.ask(
        "What would you like to do?",
        choices=["update", "create", "cancel"],
        default="update",
    )
    return PrAction(choice)
