"""Dry-run-capable GitHub adapter.

Per iam-review-agent-design.md's Local vs. remote section: a single
entrypoint, with the one thing that genuinely differs between local and
remote (talking to GitHub) isolated behind a flag - real API calls in one
implementation, logging-only in another. Dry-run is the default: real
writes require explicit opt-in (GITHUB_WRITE_MODE=real), not opt-out,
since an accidental write is harder to undo than a missed one.

Same env var name (GITHUB_TOKEN) whether it's a local PAT or a GitHub
Actions secret - the code never knows which source it came from.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from github import Auth, Github, UnknownObjectException


@dataclass
class IssueResult:
    number: int | None  # None in dry-run mode
    html_url: str | None
    title: str
    body: str
    labels: list[str]
    dry_run: bool


@dataclass
class ReportCommitResult:
    path: str
    commit_sha: str | None  # None in dry-run mode
    html_url: str | None
    dry_run: bool


@dataclass
class ReleaseResult:
    tag: str
    html_url: str | None
    asset_names: list[str]
    dry_run: bool


@dataclass
class IssueInfo:
    """A live GitHub Issue's current state - read-only summary used by
    report rendering (resolution-status rollups, Escalations, etc.).
    """

    number: int
    title: str
    body: str
    state: str  # "open" | "closed"
    labels: list[str]
    created_at: str
    closed_at: str | None
    html_url: str


class GitHubAdapter(Protocol):
    def create_issue(
        self, repo_full_name: str, title: str, body: str, labels: list[str]
    ) -> IssueResult: ...

    def commit_report(
        self, repo_full_name: str, path: str, content: str, message: str
    ) -> ReportCommitResult: ...

    def close_issue(self, repo_full_name: str, issue_number: int) -> None: ...

    def apply_label(self, repo_full_name: str, issue_number: int, label: str) -> None: ...

    def add_comment(self, repo_full_name: str, issue_number: int, body: str) -> None: ...

    def create_release(
        self,
        repo_full_name: str,
        tag: str,
        title: str,
        body: str,
        target_commitish: str,
        assets: dict[str, bytes],
    ) -> ReleaseResult: ...


class DryRunAdapter:
    """Logs what would happen. Never touches the network."""

    def create_issue(
        self, repo_full_name: str, title: str, body: str, labels: list[str]
    ) -> IssueResult:
        print(f"[DRY RUN] Would open Issue on {repo_full_name}:")
        print(f"  Title:  {title}")
        print(f"  Labels: {labels}")
        print(f"  Body:\n{body}")
        return IssueResult(
            number=None, html_url=None, title=title, body=body, labels=labels, dry_run=True
        )

    def commit_report(
        self, repo_full_name: str, path: str, content: str, message: str
    ) -> ReportCommitResult:
        preview = content[:500] + ("..." if len(content) > 500 else "")
        print(f"[DRY RUN] Would commit report to {repo_full_name}:{path}")
        print(f"  Message: {message}")
        print(f"  Content ({len(content)} chars):\n{preview}")
        return ReportCommitResult(path=path, commit_sha=None, html_url=None, dry_run=True)

    def close_issue(self, repo_full_name: str, issue_number: int) -> None:
        print(f"[DRY RUN] Would close Issue #{issue_number} on {repo_full_name}")

    def apply_label(self, repo_full_name: str, issue_number: int, label: str) -> None:
        print(f"[DRY RUN] Would apply label {label!r} to Issue #{issue_number} on {repo_full_name}")

    def add_comment(self, repo_full_name: str, issue_number: int, body: str) -> None:
        print(f"[DRY RUN] Would comment on Issue #{issue_number} on {repo_full_name}:\n{body}")

    def create_release(
        self,
        repo_full_name: str,
        tag: str,
        title: str,
        body: str,
        target_commitish: str,
        assets: dict[str, bytes],
    ) -> ReleaseResult:
        print(f"[DRY RUN] Would create Release {tag!r} on {repo_full_name} at {target_commitish}:")
        print(f"  Title: {title}")
        print(f"  Body:\n{body}")
        print(f"  Assets: {list(assets.keys())} ({sum(len(v) for v in assets.values())} bytes total)")
        return ReleaseResult(tag=tag, html_url=None, asset_names=list(assets.keys()), dry_run=True)


class RealAdapter:
    """Makes real GitHub API calls via PyGithub."""

    def __init__(self, token: str):
        self._client = Github(auth=Auth.Token(token))

    def create_issue(
        self, repo_full_name: str, title: str, body: str, labels: list[str]
    ) -> IssueResult:
        repo = self._client.get_repo(repo_full_name)
        issue = repo.create_issue(title=title, body=body, labels=labels)
        return IssueResult(
            number=issue.number,
            html_url=issue.html_url,
            title=title,
            body=body,
            labels=labels,
            dry_run=False,
        )

    def commit_report(
        self, repo_full_name: str, path: str, content: str, message: str
    ) -> ReportCommitResult:
        """Create or update one file via the Contents API - no PR, no
        review gate, per SPEC.md §3. Same adapter/token as create_issue,
        rather than a second write path through local git commands.
        """
        repo = self._client.get_repo(repo_full_name)
        try:
            existing = repo.get_contents(path)
            result = repo.update_file(path, message, content, existing.sha)
        except UnknownObjectException:
            result = repo.create_file(path, message, content)
        return ReportCommitResult(
            path=path,
            commit_sha=result["commit"].sha,
            html_url=result["content"].html_url,
            dry_run=False,
        )

    def close_issue(self, repo_full_name: str, issue_number: int) -> None:
        repo = self._client.get_repo(repo_full_name)
        repo.get_issue(issue_number).edit(state="closed")

    def apply_label(self, repo_full_name: str, issue_number: int, label: str) -> None:
        repo = self._client.get_repo(repo_full_name)
        repo.get_issue(issue_number).add_to_labels(label)

    def add_comment(self, repo_full_name: str, issue_number: int, body: str) -> None:
        repo = self._client.get_repo(repo_full_name)
        repo.get_issue(issue_number).create_comment(body)

    def create_release(
        self,
        repo_full_name: str,
        tag: str,
        title: str,
        body: str,
        target_commitish: str,
        assets: dict[str, bytes],
    ) -> ReleaseResult:
        """Tags target_commitish (the commit commit_report just wrote the
        reports in, per SPEC.md §6's sequencing), then uploads each asset.
        PyGithub's upload_asset needs a real file path, not bytes, so each
        asset is written to a temp file first and cleaned up after.
        """
        repo = self._client.get_repo(repo_full_name)
        release = repo.create_git_release(
            tag=tag, name=title, message=body, target_commitish=target_commitish
        )
        with tempfile.TemporaryDirectory() as tmp:
            for name, content in assets.items():
                asset_path = Path(tmp) / name
                asset_path.write_bytes(content)
                release.upload_asset(str(asset_path), name=name)
        return ReleaseResult(
            tag=tag, html_url=release.html_url, asset_names=list(assets.keys()), dry_run=False
        )


def _resolve_token() -> str | None:
    """GITHUB_TOKEN env var first (works locally via .env or a GitHub
    Actions secret, same name either way). Falls back to `gh auth token`
    for local dev convenience only - CI always has GITHUB_TOKEN set
    directly, this fallback never runs there.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def list_issues(repo_full_name: str, label: str | None = None) -> list[IssueInfo]:
    """Live GitHub read - not gated by GITHUB_WRITE_MODE, since reading
    has no side effect to guard against, unlike create_issue/commit_report.
    Always makes a real API call (there's no "dry run" of a read).
    """
    token = _resolve_token()
    client = Github(auth=Auth.Token(token)) if token else Github()
    repo = client.get_repo(repo_full_name)
    kwargs = {"state": "all"}
    if label:
        kwargs["labels"] = [label]
    return [
        IssueInfo(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            labels=[l.name for l in issue.labels],
            created_at=issue.created_at.isoformat(),
            closed_at=issue.closed_at.isoformat() if issue.closed_at else None,
            html_url=issue.html_url,
        )
        for issue in repo.get_issues(**kwargs)
    ]


def get_escalation_comment_date(repo_full_name: str, issue_number: int) -> str | None:
    """The escalation comment's own timestamp for one Issue - the real
    "when did this escalate" moment, distinct from the Issue's created_at.
    escalate_overdue_issues (lifecycle.py) posts a comment starting
    "**Escalated:**" at escalation time; this reads that comment back.
    None if the Issue has no such comment (shouldn't happen for an Issue
    that carries the escalated label, but a caller filters on the label
    first regardless).

    Always a real API call, same "reading has no side effect to guard"
    reasoning as list_issues - called only for Issues that already carry
    the escalated label, so call volume stays low by construction
    (ADR-0005's "fires once" keeps escalated Issues rare by design).
    """
    token = _resolve_token()
    client = Github(auth=Auth.Token(token)) if token else Github()
    repo = client.get_repo(repo_full_name)
    issue = repo.get_issue(issue_number)
    for comment in issue.get_comments():
        if comment.body.startswith("**Escalated:**"):
            return comment.created_at.isoformat()
    return None


def get_adapter() -> GitHubAdapter:
    """Select the adapter based on GITHUB_WRITE_MODE. Anything other than
    "real" (including unset) is dry-run - the safe default.
    """
    if os.environ.get("GITHUB_WRITE_MODE") != "real":
        return DryRunAdapter()

    token = _resolve_token()
    if not token:
        raise RuntimeError(
            "GITHUB_WRITE_MODE=real requires GITHUB_TOKEN (or a working `gh` "
            "auth session for local dev) to be available"
        )
    return RealAdapter(token)
