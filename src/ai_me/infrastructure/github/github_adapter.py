"""GitHub CLI adapter implementing GitHubPort."""

from __future__ import annotations

import json
import subprocess

from ai_me.domain.workspace.models import PullRequest, PullRequestResult
from ai_me.domain.workspace.ports import GitHubPort


class GhCliGitHubAdapter(GitHubPort):
    """Implements GitHubPort using the GitHub CLI (gh)."""

    def find_existing_pr(self, branch: str) -> PullRequest | None:
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--head", branch,
                "--state", "open",
                "--json", "number,title,body,url,state",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None

        prs = json.loads(result.stdout)
        if not prs:
            return None

        pr = prs[0]
        return PullRequest(
            number=pr["number"],
            title=pr["title"],
            body=pr["body"],
            url=pr["url"],
            state=pr["state"],
        )

    def create_pr(
        self,
        title: str,
        body: str,
        base: str,
        head: str,
        draft: bool = False,
    ) -> PullRequestResult:
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base,
            "--head", head,
        ]
        if draft:
            cmd.append("--draft")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        url = result.stdout.strip()

        pr_info = self._get_pr_from_url(url)
        return PullRequestResult(
            url=url,
            number=pr_info.get("number", 0),
            created=True,
        )

    def update_pr(self, number: int, title: str, body: str) -> PullRequestResult:
        subprocess.run(
            [
                "gh", "pr", "edit", str(number),
                "--title", title,
                "--body", body,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        pr_info = self._get_pr_info(number)
        return PullRequestResult(
            url=pr_info.get("url", ""),
            number=number,
            created=False,
        )

    def _get_pr_from_url(self, url: str) -> dict:
        """Get PR info from a PR URL."""
        result = subprocess.run(
            ["gh", "pr", "view", url, "--json", "number,url"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}

    def _get_pr_info(self, number: int) -> dict:
        """Get PR info by number."""
        result = subprocess.run(
            ["gh", "pr", "view", str(number), "--json", "number,url"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
