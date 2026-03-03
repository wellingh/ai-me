"""Main CLI entrypoint for ai."""

import json as _json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ai_me import __version__
from ai_me.agents.commit import generate_commit_message
from ai_me.agents.pull_request import generate_pr_description, refine_pr_description
from ai_me.git import (
    add_all,
    commit,
    create_pr,
    get_changed_files,
    get_current_branch,
    get_default_branch,
    get_diff,
    get_diff_against_branch,
    get_existing_pr,
    get_log_against_branch,
    get_repo_info,
    get_status,
    push_branch,
    update_pr,
)

app = typer.Typer(
    name="ai",
    help="CLI tool for Claude integration and automated workflows",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ai version {__version__}")
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
    """ai: CLI tool for Claude integration and automated workflows."""
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


@app.command(name="pr")
def pr_cmd(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation and create PR immediately",
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
    base: Annotated[
        str | None,
        typer.Option(
            "--base",
            "-b",
            help="Base branch to target (defaults to the remote default branch)",
        ),
    ] = None,
) -> None:
    """Generate a pull request description using Claude and create or update a PR."""
    import json as _json

    # Detect current branch
    branch_result = get_current_branch()
    if not branch_result.success:
        console.print(f"[red]Error:[/red] {branch_result.error}")
        raise typer.Exit(1)

    current_branch = branch_result.output

    # Detect or use provided base branch
    if base:
        base_branch = base
    else:
        console.print("[dim]Detecting default branch...[/dim]")
        default_result = get_default_branch()
        if not default_result.success:
            console.print(
                f"[red]Error detecting default branch:[/red] {default_result.error}"
            )
            raise typer.Exit(1)
        base_branch = default_result.output

    # Refuse if on the default branch
    if current_branch == base_branch:
        console.print(
            f"[red]Error:[/red] You are on the base branch '{base_branch}'. "
            "Switch to a feature branch first."
        )
        raise typer.Exit(1)

    console.print(f"[dim]Branch:[/dim] {current_branch} -> {base_branch}")

    # Check if a PR already exists for this branch
    existing_pr_result = get_existing_pr(current_branch)
    existing_pr = None
    if existing_pr_result.success:
        try:
            existing_pr = _json.loads(existing_pr_result.output)
        except _json.JSONDecodeError:
            pass

    if existing_pr:
        console.print()
        console.print(
            Panel(
                f"[bold]{existing_pr['title']}[/bold]\n{existing_pr.get('url', '')}",
                title="Existing PR Found",
                border_style="yellow",
            )
        )
        if not yes:
            if not Confirm.ask(
                "A PR already exists. Update its title and description?"
            ):
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

    # Get commit log and diff against base
    console.print("[dim]Collecting commit history and diff...[/dim]")
    log_result = get_log_against_branch(base_branch)
    diff_result = get_diff_against_branch(base_branch)

    if not log_result.success and not diff_result.success:
        console.print(
            f"[red]Error getting changes:[/red] {log_result.error or diff_result.error}"
        )
        raise typer.Exit(1)

    log_output = log_result.output if log_result.success else ""
    diff_output = diff_result.output if diff_result.success else ""

    if not log_output.strip() and not diff_output.strip():
        console.print(
            f"[yellow]No changes found between '{current_branch}' and '{base_branch}'.[/yellow]"
        )
        raise typer.Exit(0)

    # Generate PR description
    console.print("[dim]Generating PR description with Claude...[/dim]")
    response = generate_pr_description(log_output, diff_output, model=model)

    if not response.success:
        console.print(f"[red]Error generating PR description:[/red] {response.error}")
        raise typer.Exit(1)

    pr_text = response.result

    # Parse title (first line) and body (rest)
    lines = pr_text.split("\n", 1)
    pr_title = lines[0].strip()
    pr_body = lines[1].strip() if len(lines) > 1 else ""

    # Display the generated PR
    console.print()
    console.print(Panel(pr_title, title="PR Title", border_style="cyan"))
    console.print()
    console.print(Panel(pr_body, title="PR Description", border_style="green"))
    console.print()

    # Interactive review loop (skipped with --yes)
    if not yes:
        while True:
            action = "Update" if existing_pr else "Create"
            choice = Prompt.ask(
                f"[bold]\\[a][/bold] Accept and {action.lower()}  "
                "[bold]\\[d][/bold] Decline  "
                "[bold]\\[r][/bold] Revise with instructions",
                choices=["a", "d", "r"],
                default="a",
            )

            if choice == "d":
                console.print("[yellow]Pull request cancelled.[/yellow]")
                raise typer.Exit(0)

            if choice == "a":
                break

            # choice == "r": ask for instructions and refine
            instructions = Prompt.ask("[bold]Instructions for Claude[/bold]")
            if not instructions.strip():
                console.print("[yellow]No instructions provided, try again.[/yellow]")
                continue

            console.print("[dim]Revising PR description with Claude...[/dim]")
            refine_response = refine_pr_description(
                current_description=pr_text,
                user_instructions=instructions,
                log=log_output,
                diff=diff_output,
                model=model,
            )

            if not refine_response.success:
                console.print(
                    f"[red]Error refining PR description:[/red] {refine_response.error}"
                )
                console.print("[yellow]Keeping previous version.[/yellow]")
                continue

            pr_text = refine_response.result
            lines = pr_text.split("\n", 1)
            pr_title = lines[0].strip()
            pr_body = lines[1].strip() if len(lines) > 1 else ""

            console.print()
            console.print(Panel(pr_title, title="PR Title", border_style="cyan"))
            console.print()
            console.print(Panel(pr_body, title="PR Description", border_style="green"))
            console.print()

    # Push branch
    console.print(f"[dim]Pushing branch '{current_branch}' to origin...[/dim]")
    push_result = push_branch(current_branch)
    if not push_result.success:
        console.print(f"[red]Error pushing branch:[/red] {push_result.error}")
        raise typer.Exit(1)

    if existing_pr:
        # Update existing PR
        console.print("[dim]Updating pull request...[/dim]")
        pr_result = update_pr(pr_title, pr_body)

        if not pr_result.success:
            console.print(f"[red]Error updating PR:[/red] {pr_result.error}")
            raise typer.Exit(1)

        console.print("[green]Pull request updated successfully![/green]")
        console.print(existing_pr.get("url", ""))
    else:
        # Create new PR
        console.print("[dim]Creating pull request...[/dim]")
        pr_result = create_pr(pr_title, pr_body, base_branch)

        if not pr_result.success:
            console.print(f"[red]Error creating PR:[/red] {pr_result.error}")
            raise typer.Exit(1)

        console.print("[green]Pull request created successfully![/green]")
        console.print(pr_result.output)


@app.command(name="review")
def review_cmd(
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Model to use (e.g., 'sonnet', 'opus', 'haiku')",
        ),
    ] = None,
    base: Annotated[
        str | None,
        typer.Option(
            "--base",
            "-b",
            help="Base branch to compare against (defaults to remote default branch)",
        ),
    ] = None,
    severity: Annotated[
        str | None,
        typer.Option(
            "--severity",
            "-s",
            help="Minimum severity to show: 'error', 'warning', or 'suggestion'",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Enable debug logging for troubleshooting",
        ),
    ] = False,
) -> None:
    """Review code changes against a base branch and suggest fixes."""
    import logging

    from ai_me.agents.code_review import review_diff

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s"
        )

    severity_colors = {"error": "red", "warning": "yellow", "suggestion": "blue"}
    severity_order = {"error": 0, "warning": 1, "suggestion": 2}

    # Determine base branch
    branch_result = get_current_branch()
    if not branch_result.success:
        console.print(f"[red]Error:[/red] {branch_result.error}")
        raise typer.Exit(1)
    current_branch = branch_result.output

    if base:
        base_branch = base
    else:
        console.print("[dim]Detecting default branch...[/dim]")
        default_result = get_default_branch()
        if not default_result.success:
            console.print(
                f"[red]Error detecting default branch:[/red] {default_result.error}"
            )
            raise typer.Exit(1)
        base_branch = default_result.output

    if current_branch == base_branch:
        console.print(
            f"[red]Error:[/red] You are on the base branch '{base_branch}'. "
            "Switch to a feature branch first."
        )
        raise typer.Exit(1)

    console.print(f"[dim]Reviewing:[/dim] {current_branch} against {base_branch}")

    # Get GitHub org/repo for the output path
    console.print("[dim]Getting repository info...[/dim]")
    repo_info_result = get_repo_info()
    if not repo_info_result.success:
        console.print(f"[red]Error getting repo info:[/red] {repo_info_result.error}")
        raise typer.Exit(1)
    try:
        repo_data = _json.loads(repo_info_result.output)
        org = repo_data["owner"]["login"]
        repo = repo_data["name"]
    except (KeyError, _json.JSONDecodeError) as e:
        console.print(f"[red]Error parsing repo info:[/red] {e}")
        raise typer.Exit(1)

    # Determine identifier: PR number if a PR exists, else sanitized branch name
    existing_pr_result = get_existing_pr(current_branch)
    existing_pr = None
    if existing_pr_result.success:
        try:
            existing_pr = _json.loads(existing_pr_result.output)
        except _json.JSONDecodeError:
            pass
    identifier = (
        str(existing_pr["number"]) if existing_pr else current_branch.replace("/", "-")
    )

    # Build output path and ensure parent dirs exist
    output_path = Path.home() / ".ai" / org / repo / f"{identifier}_review.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)

    # Get changed files
    console.print("[dim]Getting changed files...[/dim]")
    files_result = get_changed_files(base_branch)
    if not files_result.success:
        console.print(f"[red]Error getting changed files:[/red] {files_result.error}")
        raise typer.Exit(1)
    changed_files = [
        f.strip() for f in files_result.output.strip().splitlines() if f.strip()
    ]
    if not changed_files:
        console.print(
            f"[yellow]No changed files between '{current_branch}' and '{base_branch}'.[/yellow]"
        )
        raise typer.Exit(0)

    # Delegate review to Claude agent
    console.print("[dim]Reviewing changes with Claude (agent mode)...[/dim]")
    result = review_diff(changed_files, base_branch, str(output_path), model=model)

    if not result.success:
        console.print(f"[red]Error during review:[/red] {result.error}")
        raise typer.Exit(1)

    if not result.findings:
        console.print("[green]No issues found. Code looks good![/green]")
        console.print(f"[dim]Review saved to:[/dim] {output_path}")
        raise typer.Exit(0)

    # Filter by severity
    findings = result.findings
    if severity and severity in severity_order:
        min_level = severity_order[severity]
        findings = [
            f for f in findings if severity_order.get(f.severity, 2) <= min_level
        ]

    if not findings:
        console.print("[green]No issues at the requested severity level.[/green]")
        raise typer.Exit(0)

    # Summary
    counts: dict[str, int] = {"error": 0, "warning": 0, "suggestion": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    summary = (
        f"Found [bold]{len(findings)}[/bold] findings: "
        f"[red]{counts['error']} errors[/red], "
        f"[yellow]{counts['warning']} warnings[/yellow], "
        f"[blue]{counts['suggestion']} suggestions[/blue]"
    )
    console.print()
    console.print(Panel(summary, title="Review Summary", border_style="cyan"))
    console.print(f"[dim]Review saved to:[/dim] {output_path}")
    console.print()

    # Interactive loop
    applied = 0
    for i, finding in enumerate(findings, 1):
        color = severity_colors.get(finding.severity, "white")

        body = f"[bold]File:[/bold] {finding.file}:{finding.line_hint}\n\n"
        body += f"{finding.explanation}\n\n"
        body += f"[dim]--- Original ---[/dim]\n{finding.original}\n\n"
        body += f"[green]+++ Suggested fix +++[/green]\n{finding.replacement}"

        console.print(
            Panel(
                body,
                title=f"[{color}][{finding.severity.upper()}][/{color}] {finding.title}  ({i}/{len(findings)})",
                border_style=color,
            )
        )
        console.print()

        choice = Prompt.ask(
            "[bold]\\[a][/bold] Accept fix  "
            "[bold]\\[s][/bold] Skip  "
            "[bold]\\[q][/bold] Quit review",
            choices=["a", "s", "q"],
            default="s",
        )

        if choice == "q":
            console.print("[yellow]Review stopped.[/yellow]")
            break

        if choice == "a":
            file_path = Path(finding.file)
            if not file_path.exists():
                console.print(
                    f"[red]Could not apply fix:[/red] File not found: {finding.file}"
                )
            else:
                try:
                    content = file_path.read_text()
                    if finding.original not in content:
                        console.print(
                            "[red]Could not apply fix:[/red] "
                            "Exact text not found in file (may have already been modified)."
                        )
                    elif content.count(finding.original) > 1:
                        console.print(
                            "[red]Could not apply fix:[/red] "
                            "Multiple occurrences found. Fix is ambiguous."
                        )
                    else:
                        file_path.write_text(
                            content.replace(finding.original, finding.replacement, 1)
                        )
                        console.print("[green]Fix applied.[/green]")
                        applied += 1
                except OSError as e:
                    console.print(f"[red]Could not apply fix:[/red] {e}")

        console.print()

    # Final summary
    console.print()
    console.print(
        f"Applied [bold]{applied}[/bold] of [bold]{len(findings)}[/bold] fixes."
    )
    if applied > 0:
        console.print("[dim]Run 'git diff' to review the applied changes.[/dim]")


if __name__ == "__main__":
    app()
