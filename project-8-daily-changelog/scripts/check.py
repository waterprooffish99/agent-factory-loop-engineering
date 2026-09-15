#!/usr/bin/env python3
"""Deterministic gate for a proposed changelog diff."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import REPO_DIR, added_lines, contains_secret, frozen_manifest_digest, run


BRANCH_PATTERN = re.compile(r"^project-8/changelog-beat-\d{4}-\d{8}$")
ALLOWED_FILES = {"CHANGELOG.md"}
MAX_FILES_CHANGED = 1
MAX_CHANGELOG_BYTES = 50_000
MIN_COMMIT_ABBREVIATION = 7
MAX_OBJECT_ID_LENGTH = 64
TRACE_LINE_PATTERN = re.compile(r"^\s*Commits:\s*(.*)$", re.IGNORECASE)
HEX_OBJECT_ID_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


def changed_files(worktree: Path) -> list[str]:
    tracked = run(["git", "diff", "--name-only", "HEAD"], cwd=worktree).stdout.splitlines()
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=worktree).stdout.splitlines()
    return sorted(set(filter(None, tracked + untracked)))


def proposed_diff(worktree: Path, files: list[str]) -> str:
    if not files:
        return ""
    target = worktree / "CHANGELOG.md"
    tracked = run(["git", "ls-files", "--error-unmatch", "CHANGELOG.md"], cwd=worktree, allowed_returncodes=(0, 1))
    if tracked.returncode == 0:
        return run(["git", "diff", "--no-ext-diff", "--", "CHANGELOG.md"], cwd=worktree).stdout
    return run(
        ["git", "diff", "--no-index", "--no-ext-diff", "--", "/dev/null", str(target)],
        cwd=worktree,
        allowed_returncodes=(0, 1),
    ).stdout


def extract_commit_references(diff_text: str) -> list[str]:
    """Extract human-facing commit references from added `Commits:` lines."""
    references: list[str] = []
    for line in added_lines(diff_text).splitlines():
        match = TRACE_LINE_PATTERN.match(line)
        if match:
            for item in match.group(1).split(","):
                reference = item.strip()
                if len(reference) >= 2 and reference.startswith("`") and reference.endswith("`"):
                    reference = reference[1:-1].strip()
                references.append(reference)
    return references


def resolve_commit_reference(repo: Path, reference: str) -> str | None:
    """Resolve an unambiguous hexadecimal commit reference to its full object ID."""
    if not (
        MIN_COMMIT_ABBREVIATION <= len(reference) <= MAX_OBJECT_ID_LENGTH
        and HEX_OBJECT_ID_PATTERN.fullmatch(reference)
    ):
        return None
    result = run(
        ["git", "rev-parse", "--verify", "--quiet", f"{reference}^{{commit}}"],
        cwd=repo,
        allowed_returncodes=(0, 1, 128),
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.strip().splitlines()
    if len(lines) != 1 or not HEX_OBJECT_ID_PATTERN.fullmatch(lines[0]):
        return None
    return lines[0].lower()


def validate_commit_trace(repo: Path, diff_text: str, expected_full_shas: list[str]) -> dict[str, Any]:
    """Compare changelog references with expected commits by canonical Git identity."""
    expected = [sha.lower() for sha in expected_full_shas]
    invalid_expected = [sha for sha in expected if resolve_commit_reference(repo, sha) != sha]
    references = extract_commit_references(diff_text)
    resolved: list[dict[str, str]] = []
    invalid_references: list[str] = []
    for reference in references:
        canonical = resolve_commit_reference(repo, reference)
        if canonical is None:
            invalid_references.append(reference)
        else:
            resolved.append({"reference": reference, "sha": canonical})

    expected_set = set(expected)
    resolved_set = {item["sha"] for item in resolved}
    missing = sorted(expected_set - resolved_set)
    unexpected = sorted(resolved_set - expected_set)
    valid = bool(expected) and bool(references) and not invalid_expected and not invalid_references and not missing and not unexpected
    return {
        "valid": valid,
        "expected_full_shas": expected,
        "references": references,
        "resolved_references": resolved,
        "invalid_expected_shas": invalid_expected,
        "invalid_references": invalid_references,
        "missing_expected_shas": missing,
        "unexpected_shas": unexpected,
        "minimum_abbreviation_length": MIN_COMMIT_ABBREVIATION,
    }


def check_proposal(
    *,
    worktree: Path,
    branch: str,
    default_branch: str,
    default_head_before: str,
    default_diff_digest_before: str,
    frozen_digest_before: str,
    maker_exit_code: int,
    expected_full_shas: list[str],
) -> dict[str, Any]:
    files = changed_files(worktree)
    diff_text = proposed_diff(worktree, files)
    worktrees = run(["git", "worktree", "list", "--porcelain"], cwd=REPO_DIR).stdout
    default_head_after = run(["git", "rev-parse", f"refs/heads/{default_branch}"], cwd=REPO_DIR).stdout.strip()
    default_diff = run(["git", "diff", "HEAD", "--binary"], cwd=REPO_DIR).stdout
    frozen_after = frozen_manifest_digest()

    markdown_valid = False
    markdown_reason = "CHANGELOG.md is absent"
    content = ""
    target = worktree / "CHANGELOG.md"
    if target.is_file():
        try:
            content = target.read_text(encoding="utf-8")
            markdown_valid = (
                "\x00" not in content
                and len(content.encode("utf-8")) <= MAX_CHANGELOG_BYTES
                and content.lstrip().startswith("# Changelog")
                and not any(line.endswith((" ", "\t")) for line in content.splitlines())
            )
            markdown_reason = "valid UTF-8 Markdown" if markdown_valid else "invalid heading, NUL, or size"
        except (UnicodeDecodeError, OSError) as exc:
            markdown_reason = str(exc)

    commit_trace = validate_commit_trace(worktree, diff_text, expected_full_shas)

    checks = {
        "isolated_worktree_registered": f"worktree {worktree}\n" in worktrees and worktree.resolve() != REPO_DIR.resolve(),
        "default_branch_head_unchanged": default_head_after == default_head_before,
        "default_worktree_tracked_diff_unchanged": __import__("hashlib").sha256(default_diff.encode()).hexdigest() == default_diff_digest_before,
        "projects_1_to_7_untouched": frozen_after == frozen_digest_before,
        "only_allowed_files_changed": set(files).issubset(ALLOWED_FILES),
        "file_count_within_cap": 0 < len(files) <= MAX_FILES_CHANGED,
        "valid_markdown_text": markdown_valid,
        "markdown_diff_check": run(
            ["git", "diff", "--check", "--", "CHANGELOG.md"],
            cwd=worktree,
            allowed_returncodes=(0, 1, 2, 128),
        ).returncode == 0,
        "non_empty_diff": bool(diff_text.strip()),
        "complete_commit_trace": commit_trace["valid"],
        "branch_name_valid": bool(BRANCH_PATTERN.fullmatch(branch)),
        "no_secrets_in_added_lines": not contains_secret(added_lines(diff_text)),
        "maker_process_succeeded": maker_exit_code == 0,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "changed_files": files,
        "diff": diff_text,
        "markdown_detail": markdown_reason,
        "commit_trace": commit_trace,
        "default_head_before": default_head_before,
        "default_head_after": default_head_after,
        "frozen_digest_before": frozen_digest_before,
        "frozen_digest_after": frozen_after,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--default-head-before", required=True)
    parser.add_argument("--default-diff-digest-before", required=True)
    parser.add_argument("--frozen-digest-before", required=True)
    parser.add_argument("--maker-exit-code", type=int, required=True)
    parser.add_argument("--expected-sha", action="append", default=[])
    parser.add_argument("--expected-short-sha", action="append", default=[], help=argparse.SUPPRESS)
    args = parser.parse_args()
    values = vars(args)
    values["expected_full_shas"] = values.pop("expected_sha") + values.pop("expected_short_sha")
    report = check_proposal(**values)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
