"""Main CLI entrypoint for claude-me."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from claude_me import __version__
from claude_me.agents.commit import generate_commit_message
from claude_me.git import add_all, commit, get_diff, get_status

app = typer.Typer(
    name="claude-me",
    help="CLI tool for Claude integration and automated workflows",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"claude-me version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Claude-Me: CLI tool for Claude integration and automated workflows."""
    pass


@app.command(name="commit")
def commit_cmd(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation and commit immediately",
        ),
    ] = False,
    all_changes: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Include all changes (staged + unstaged), default is staged only",
        ),
    ] = False,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Model to use (e.g., 'sonnet', 'opus', 'haiku')",
        ),
    ] = None,
) -> None:
    """Generate a commit message using Claude and commit changes."""
    # Check git status
    status = get_status()
    if not status.success:
        console.print(f"[red]Error:[/red] {status.error}")
        raise typer.Exit(1)

    if not status.output.strip():
        console.print("[yellow]No changes to commit.[/yellow]")
        raise typer.Exit(0)

    # If using all changes, stage everything first
    if all_changes:
        console.print("[dim]Staging all changes...[/dim]")
        add_result = add_all()
        if not add_result.success:
            console.print(f"[red]Error staging changes:[/red] {add_result.error}")
            raise typer.Exit(1)

    # Get the diff
    staged_only = not all_changes
    console.print("[dim]Getting diff...[/dim]")
    diff_result = get_diff(staged_only=staged_only)

    if not diff_result.success:
        console.print(f"[red]Error getting diff:[/red] {diff_result.error}")
        raise typer.Exit(1)

    if not diff_result.output.strip():
        if staged_only:
            console.print(
                "[yellow]No staged changes. Use --all to include unstaged changes.[/yellow]"
            )
        else:
            console.print("[yellow]No changes to commit.[/yellow]")
        raise typer.Exit(0)

    # Generate commit message
    console.print("[dim]Generating commit message with Claude...[/dim]")
    response = generate_commit_message(diff_result.output, model=model)

    if not response.success:
        console.print(f"[red]Error generating commit message:[/red] {response.error}")
        raise typer.Exit(1)

    commit_message = response.result

    # Display the generated message
    console.print()
    console.print(
        Panel(commit_message, title="Generated Commit Message", border_style="green")
    )
    console.print()

    # Confirm and commit
    if not yes:
        if not Confirm.ask("Proceed with this commit?"):
            console.print("[yellow]Commit cancelled.[/yellow]")
            raise typer.Exit(0)

    # Execute commit
    console.print("[dim]Committing...[/dim]")
    commit_result = commit(commit_message)

    if not commit_result.success:
        console.print(f"[red]Error committing:[/red] {commit_result.error}")
        raise typer.Exit(1)

    console.print("[green]Commit successful![/green]")
    console.print(commit_result.output)


if __name__ == "__main__":
    app()
