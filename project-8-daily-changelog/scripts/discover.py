#!/usr/bin/env python3
"""Discover default-branch commits after the durable checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import BeatError, REPO_DIR, run


def discover(checkpoint: str, default_ref: str, *, repo: Path = REPO_DIR, timeout: float = 30) -> dict[str, Any]:
    run(["git", "cat-file", "-e", f"{checkpoint}^{{commit}}"], cwd=repo, timeout=timeout)
    tip = run(["git", "rev-parse", "--verify", f"{default_ref}^{{commit}}"], cwd=repo, timeout=timeout).stdout.strip()
    ancestor = run(
        ["git", "merge-base", "--is-ancestor", checkpoint, tip],
        cwd=repo,
        timeout=timeout,
        allowed_returncodes=(0, 1),
    )
    if ancestor.returncode != 0:
        raise BeatError("checkpoint is not an ancestor of the default-branch tip; history may have changed")

    output = run(
        ["git", "log", "--reverse", "--format=%H%x1f%h%x1f%cI%x1f%s", f"{checkpoint}..{tip}"],
        cwd=repo,
        timeout=timeout,
    ).stdout
    commits = []
    for line in output.splitlines():
        full, short, date, subject = line.split("\x1f", 3)
        commits.append({"sha": full, "short_sha": short, "date": date, "subject": subject})
    return {
        "checkpoint_exclusive": checkpoint,
        "default_ref": default_ref,
        "tip": tip,
        "commit_count": len(commits),
        "commits": commits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--default-ref", default="refs/remotes/origin/main")
    args = parser.parse_args()
    print(json.dumps(discover(args.checkpoint, args.default_ref), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
