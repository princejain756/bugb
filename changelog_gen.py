#!/usr/bin/env python3
"""
Structured CHANGELOG.md generator from git history.
Supports Conventional Commits and freeform commit messages, grouping changes into
Added, Fixed, Changed, and Removed sections following Keep a Changelog 1.1.0.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)


def run_git(repo_path: str, args: List[str]) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def get_latest_tag(repo_path: str) -> Optional[str]:
    try:
        tag = run_git(repo_path, ["describe", "--tags", "--abbrev=0"]).strip()
        return tag or None
    except RuntimeError:
        return None


def classify_commit(subject: str, body: str = "") -> Tuple[str, str]:
    """Return (category, formatted_entry) where category is one of Added/Fixed/Changed/Removed."""
    clean_subject = subject.strip()
    match = CONVENTIONAL_RE.match(clean_subject)
    is_breaking = "BREAKING CHANGE:" in (body or "")

    if match:
        ctype = match.group("type").lower()
        scope = match.group("scope")
        if match.group("breaking"):
            is_breaking = True
        desc = match.group("desc").strip()
        prefix = f"**{scope}**: " if scope else ""
        if is_breaking:
            prefix = f"**BREAKING** {prefix}"
        formatted = f"{prefix}{desc}"

        if ctype in ("feat", "feature", "add"):
            return "Added", formatted
        if ctype in ("fix", "bugfix", "hotfix", "sec", "security"):
            return "Fixed", formatted
        if ctype in ("remove", "drop", "del", "delete", "revert", "deprecate"):
            return "Removed", formatted
        return "Changed", formatted

    lower = clean_subject.lower()
    prefix = "**BREAKING**: " if is_breaking else ""
    if re.match(r"^(add|added|adding|implement|implemented|introduce|introduced|create|created|new|feat)\b", lower):
        return "Added", f"{prefix}{clean_subject}"
    if re.match(r"^(fix|fixed|fixing|resolve|resolved|bug|patch|patched|repair|repaired|hotfix)\b", lower):
        return "Fixed", f"{prefix}{clean_subject}"
    if re.match(r"^(remove|removed|removing|delete|deleted|drop|dropped|deprecate|deprecated|revert)\b", lower):
        return "Removed", f"{prefix}{clean_subject}"
    return "Changed", f"{prefix}{clean_subject}"


def fetch_commits(repo_path: str, since_ref: Optional[str] = None, until_ref: str = "HEAD") -> List[Dict[str, str]]:
    rev_range = f"{since_ref}..{until_ref}" if since_ref else until_ref
    fmt = "%H%x1f%h%x1f%ad%x1f%an%x1f%s%x1f%b%x1e"
    raw = run_git(
        repo_path,
        ["log", rev_range, "--no-merges", f"--format={fmt}", "--date=short"],
    )
    commits: List[Dict[str, str]] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        fields = record.split("\x1f")
        if len(fields) < 5:
            continue
        full_hash, short_hash, date_str, author, subject = fields[:5]
        body = fields[5].strip() if len(fields) > 5 else ""
        commits.append(
            {
                "hash": full_hash.strip(),
                "short_hash": short_hash.strip(),
                "date": date_str.strip(),
                "author": author.strip(),
                "subject": subject.strip(),
                "body": body,
            }
        )
    return commits


def render_changelog_section(
    commits: List[Dict[str, str]],
    version_label: str = "Unreleased",
    release_date: Optional[str] = None,
    since_tag: Optional[str] = None,
) -> str:
    grouped: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}
    for commit in commits:
        cat, formatted = classify_commit(commit["subject"], commit.get("body", ""))
        entry = f"- {formatted} (`{commit['short_hash']}`)"
        if entry not in grouped[cat]:
            grouped[cat].append(entry)

    date_part = release_date or datetime.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version_label}] - {date_part}",
    ]
    if since_tag:
        lines.append(f"")
        lines.append(f"_Changes since `{since_tag}`_")

    has_entries = False
    for cat in CATEGORIES:
        entries = grouped[cat]
        if not entries:
            continue
        has_entries = True
        lines.append("")
        lines.append(f"### {cat}")
        lines.extend(entries)

    if not has_entries:
        lines.append("")
        lines.append("_No user-facing changes recorded in this range._")

    lines.append("")
    return "\n".join(lines)


def generate_changelog(
    repo_path: str = ".",
    since_tag: Optional[str] = None,
    until_ref: str = "HEAD",
    version_label: str = "Unreleased",
    release_date: Optional[str] = None,
) -> str:
    resolved_tag = since_tag if since_tag is not None else get_latest_tag(repo_path)
    commits = fetch_commits(repo_path, since_ref=resolved_tag, until_ref=until_ref)
    return render_changelog_section(
        commits,
        version_label=version_label,
        release_date=release_date,
        since_tag=resolved_tag,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git commit history."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository (default: current directory).",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Git tag or commit ref to start from (default: latest git tag).",
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help="Target git ref (default: HEAD).",
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="Version heading label (default: Unreleased).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated changelog to stdout instead of writing to a file.",
    )
    args = parser.parse_args(argv)

    content = generate_changelog(
        repo_path=args.repo,
        since_tag=args.since,
        until_ref=args.until,
        version_label=args.version,
    )
    if args.stdout:
        sys.stdout.write(content)
    else:
        out_path = os.path.abspath(args.output)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"Wrote structured changelog to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
