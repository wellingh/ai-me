"""Subprocess-based git adapter implementing GitPort."""

from __future__ import annotations

import re
import subprocess

from ai_me.domain.workspace.models import Branch, CommitLog, CommitLogEntry, CommitResult, Diff
from ai_me.domain.workspace.ports import GitPort


class SubprocessGitAdapter(GitPort):
    """Implements GitPort using subprocess calls to the git CLI."""

    def __init__(self, repo_path: str = ".") -> None:
        self._cwd = repo_path

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self._cwd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout

    def get_staged_diff(self) -> Diff | None:
        stat_output = self._run("diff", "--cached", "--stat")
        if not stat_output.strip():
            return None
        content = self._run("diff", "--cached")
        return self._parse_diff(content, stat_output)

    def stage_all(self) -> None:
        self._run("add", "-A")

    def get_diff(self, base: str, head: str = "HEAD") -> Diff:
        content = self._run("diff", f"{base}...{head}")
        stat_output = self._run("diff", f"{base}...{head}", "--stat")
        return self._parse_diff(content, stat_output)

    def get_commit_log(self, base: str, head: str = "HEAD") -> CommitLog:
        output = self._run("log", f"{base}..{head}", "--oneline")
        entries = []
        for line in output.strip().splitlines():
            if not line.strip():
                continue
            hash_, _, message = line.partition(" ")
            entries.append(CommitLogEntry(hash=hash_, message=message))
        return CommitLog(entries=entries)

    def get_current_branch(self) -> Branch:
        name = self._run("branch", "--show-current").strip()
        return Branch(name=name)

    def get_default_branch(self) -> Branch:
        try:
            ref = self._run("symbolic-ref", "refs/remotes/origin/HEAD").strip()
            name = ref.replace("refs/remotes/origin/", "")
        except subprocess.CalledProcessError:
            name = "main"
        return Branch(name=name, is_default=True)

    def commit(self, message: str) -> CommitResult:
        self._run("commit", "-m", message)
        hash_ = self._run("rev-parse", "--short", "HEAD").strip()
        return CommitResult(hash=hash_, message=message)

    def _parse_diff(self, content: str, stat_output: str) -> Diff:
        files_changed = 0
        insertions = 0
        deletions = 0

        for line in stat_output.strip().splitlines():
            summary_match = re.search(
                r"(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?",
                line,
            )
            if summary_match:
                files_changed = int(summary_match.group(1))
                insertions = int(summary_match.group(2) or 0)
                deletions = int(summary_match.group(3) or 0)

        return Diff(
            content=content,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        )
