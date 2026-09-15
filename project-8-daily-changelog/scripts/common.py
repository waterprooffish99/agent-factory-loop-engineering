#!/usr/bin/env python3
"""Shared, standard-library helpers for the daily changelog loop."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PROJECT_DIR.parent
STATE_PATH = PROJECT_DIR / "state.json"
PROGRESS_PATH = PROJECT_DIR / "progress.md"
LOG_DIR = PROJECT_DIR / "logs"
EVIDENCE_DIR = PROJECT_DIR / "evidence"

FROZEN_DIRS = (
    "project-1-iss-loop",
    "project-2-goal-driven-portfolio",
    "project-3-morning-brief",
    "project-4-fix-loop",
    "project-5-codify-body",
    "project-7-break-it-on-purpose",
)

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s<]{8,}"),
)


class BeatError(RuntimeError):
    """A safe stopping condition that requires human attention."""


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("<REDACTED>", redacted)
    return redacted


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(
    args: Iterable[str],
    *,
    cwd: Path = REPO_DIR,
    timeout: float | None = None,
    stdin: str | None = None,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> CommandResult:
    command = list(args)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise BeatError(f"command timed out: {command[0]}") from exc
    result = CommandResult(
        args=command,
        returncode=completed.returncode,
        stdout=redact(completed.stdout),
        stderr=redact(completed.stderr),
        elapsed_seconds=round(time.monotonic() - started, 3),
    )
    if result.returncode not in allowed_returncodes:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise BeatError(f"command failed ({result.returncode}): {' '.join(command[:3])}: {detail[:500]}")
    return result


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="surrogateescape")).hexdigest()


def frozen_manifest_digest() -> str:
    digest = hashlib.sha256()
    for directory_name in FROZEN_DIRS:
        directory = REPO_DIR / directory_name
        if not directory.exists():
            continue
        for path in sorted(p for p in directory.rglob("*") if p.is_file() and ".git" not in p.parts):
            relative = path.relative_to(REPO_DIR).as_posix().encode()
            digest.update(relative + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def added_lines(diff_text: str) -> str:
    return "\n".join(
        line[1:]
        for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)
