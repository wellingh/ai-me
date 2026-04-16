"""CLI entry point — Typer app with registered commands."""

import typer

from ai_me.cli.commit import commit_command
from ai_me.cli.pull_request import pr_command

app = typer.Typer(
    name="ai",
    help="AI-powered developer CLI — automate commit messages, pull requests, and more.",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate the full flow without executing mutations",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug output",
    ),
) -> None:
    """AI-powered developer CLI — automate commit messages, pull requests, and more."""
    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run
    ctx.obj["debug"] = debug


app.command(name="commit")(commit_command)
app.command(name="pr")(pr_command)
