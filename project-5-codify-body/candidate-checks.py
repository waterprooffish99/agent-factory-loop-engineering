#!/usr/bin/env python3
"""Deterministic checks for Project 5 candidate worktrees."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path


TARGET_FUNCTION = {
    "rolling_average": "rolling_average",
    "find_duplicates": "find_duplicates",
    "clamp": "clamp",
}


def fail(message: str) -> None:
    print(f"CHECK FAIL: {message}")
    raise SystemExit(1)


def normalized_without_function(source: str, function_name: str) -> str:
    tree = ast.parse(source)
    tree.body = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        or node.name != function_name
    ]
    return ast.dump(tree, include_attributes=False)


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def verify_scope(file_name: str, source: str, function_name: str) -> None:
    changed = run_git("diff", "--name-only", "main", "--").stdout.splitlines()
    if changed != [file_name]:
        fail(f"scope violation; changed files are {changed!r}, expected only {file_name!r}")

    diff_check = run_git("diff", "--check", "main", "--", file_name)
    if diff_check.returncode:
        fail(f"git diff --check failed: {diff_check.stdout or diff_check.stderr}")

    baseline = run_git("show", f"main:{file_name}")
    if baseline.returncode:
        fail(f"could not read baseline main:{file_name}: {baseline.stderr.strip()}")

    try:
        current_rest = normalized_without_function(source, function_name)
        baseline_rest = normalized_without_function(baseline.stdout, function_name)
    except SyntaxError as exc:
        fail(f"syntax error: {exc}")

    if current_rest != baseline_rest:
        fail(f"scope violation; code outside {function_name} changed")


def load_namespace(file_name: str, source: str) -> dict[str, object]:
    namespace: dict[str, object] = {"__name__": "candidate_utils"}
    try:
        exec(compile(source, file_name, "exec"), namespace)
    except Exception as exc:  # The checker must turn any load failure into FAIL.
        fail(f"could not execute {file_name}: {type(exc).__name__}: {exc}")
    return namespace


def verify_behavior(check_name: str, namespace: dict[str, object]) -> None:
    try:
        if check_name == "rolling_average":
            rolling_average = namespace["rolling_average"]
            assert rolling_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
            assert rolling_average([2, 4, 8], 3) == [14 / 3]
            assert rolling_average([2, 4], 5) == [3.0]
            assert rolling_average([], 3) == []
            assert rolling_average([1, 2], 0) == []
            print("CHECK PASS: rolling_average includes the final window and handles boundaries")
        elif check_name == "find_duplicates":
            find_duplicates = namespace["find_duplicates"]
            assert find_duplicates(["b", "a", "b", "c", "a"]) == ["b", "a"]
            assert find_duplicates([3, 1, 3, 2, 1, 3]) == [3, 1]
            assert find_duplicates([1, 2, 3]) == []
            print("CHECK PASS: find_duplicates returns unique duplicates in discovery order")
        elif check_name == "clamp":
            clamp = namespace["clamp"]
            assert clamp(-4, 0, 10) == 0
            assert clamp(6, 0, 10) == 6
            assert clamp(14, 0, 10) == 10
            assert clamp(0, 0, 10) == 0
            assert clamp(10, 0, 10) == 10
            print("CHECK PASS: clamp handles below, inside, above, and boundary values")
        else:
            fail(f"unknown check {check_name!r}")
    except (AssertionError, KeyError, TypeError) as exc:
        detail = str(exc) or "an expected behavior assertion failed"
        fail(f"{check_name} behavior is incorrect: {detail}")


def verify_candidate(check_name: str, file_name: str) -> None:
    if check_name not in TARGET_FUNCTION:
        fail(f"unknown check {check_name!r}")

    path = Path(file_name)
    if not path.is_file():
        fail(f"candidate file {file_name!r} does not exist")

    source = path.read_text()
    function_name = TARGET_FUNCTION[check_name]
    verify_scope(file_name, source, function_name)
    namespace = load_namespace(file_name, source)
    verify_behavior(check_name, namespace)


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def extract_review_text(raw: str) -> str:
    chunks: list[str] = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        part = event.get("part") if isinstance(event, dict) else None
        if isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
        elif isinstance(event, dict) and event.get("type") == "text":
            text = event.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return ANSI.sub("", "".join(chunks)).replace("\r", "").strip()


def extract_verdict(raw: str) -> None:
    review_text = extract_review_text(raw)
    verdicts = [
        line.strip()
        for line in review_text.splitlines()
        if line.strip() in {"PASS", "FAIL"}
    ]
    if len(verdicts) != 1:
        print("INVALID")
        return
    print(verdicts[0])


def usage() -> None:
    print(
        "Usage: candidate-checks.py verify <check> <file> | "
        "review-text | review-verdict",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "verify":
        verify_candidate(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2 and sys.argv[1] == "review-text":
        print(extract_review_text(sys.stdin.read()))
    elif len(sys.argv) == 2 and sys.argv[1] == "review-verdict":
        extract_verdict(sys.stdin.read())
    else:
        usage()


if __name__ == "__main__":
    main()
