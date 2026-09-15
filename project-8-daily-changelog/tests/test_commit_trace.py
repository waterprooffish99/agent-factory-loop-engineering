#!/usr/bin/env python3
"""Regression tests for canonical commit identity validation."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check import extract_commit_references, resolve_commit_reference, validate_commit_trace  # noqa: E402


class CommitTraceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="project-8-trace-test-")
        self.repo = Path(self.temp.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Project 8 Test")
        self.git("config", "user.email", "project8-test@example.invalid")
        for index in range(3):
            self.git("commit", "--quiet", "--allow-empty", "-m", f"test commit {index}")
        self.shas = self.git("rev-list", "--reverse", "HEAD").splitlines()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str, stdin: str | None = None, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout.strip()

    @staticmethod
    def diff(*references: str) -> str:
        rendered = ", ".join(f"`{reference}`" for reference in references)
        return f"diff --git a/CHANGELOG.md b/CHANGELOG.md\n+Commits: {rendered}\n"

    @staticmethod
    def raw_diff(trace: str | None, *other_added_lines: str) -> str:
        lines = ["diff --git a/CHANGELOG.md b/CHANGELOG.md"]
        lines.extend(f"+{line}" for line in other_added_lines)
        if trace is not None:
            lines.append(f"+Commits: {trace}")
        return "\n".join(lines) + "\n"

    def assert_trace(self, expected: list[str], references: list[str], wanted: bool) -> dict[str, object]:
        result = validate_commit_trace(self.repo, self.diff(*references), expected)
        self.assertEqual(wanted, result["valid"], result)
        return result

    def test_extracts_plain_sha_list(self) -> None:
        diff = self.raw_diff("12eff69, cf8d7e5")
        self.assertEqual(["12eff69", "cf8d7e5"], extract_commit_references(diff))

    def test_extracts_backtick_sha_list(self) -> None:
        diff = self.raw_diff("`12eff69`, `cf8d7e5`")
        self.assertEqual(["12eff69", "cf8d7e5"], extract_commit_references(diff))

    def test_extracts_mixed_plain_and_backtick_sha_list(self) -> None:
        diff = self.raw_diff("12eff69, `cf8d7e5`, e2b27a4")
        self.assertEqual(["12eff69", "cf8d7e5", "e2b27a4"], extract_commit_references(diff))

    def test_extracts_full_sha(self) -> None:
        diff = self.raw_diff(self.shas[0])
        self.assertEqual([self.shas[0]], extract_commit_references(diff))

    def test_extracts_longer_abbreviation(self) -> None:
        reference = self.shas[0][:12]
        diff = self.raw_diff(reference)
        self.assertEqual([reference], extract_commit_references(diff))

    def test_ignores_hexadecimal_text_outside_commits_field(self) -> None:
        diff = self.raw_diff(self.shas[0][:12], "Build identifier: deadbeefcafebabe")
        self.assertEqual([self.shas[0][:12]], extract_commit_references(diff))

    def test_missing_commits_field_fails(self) -> None:
        diff = self.raw_diff(None, f"Build identifier: {self.shas[0][:12]}")
        result = validate_commit_trace(self.repo, diff, [self.shas[0]])
        self.assertFalse(result["valid"], result)
        self.assertEqual([], result["references"])
        self.assertEqual([self.shas[0]], result["missing_expected_shas"])

    def test_short_reference_under_seven_characters_fails(self) -> None:
        reference = self.shas[0][:6]
        diff = self.raw_diff(reference)
        result = validate_commit_trace(self.repo, diff, [self.shas[0]])
        self.assertFalse(result["valid"], result)
        self.assertEqual([reference], result["invalid_references"])

    def test_exact_git_short_hash_passes(self) -> None:
        short = self.git("rev-parse", "--short=7", self.shas[0])
        self.assert_trace([self.shas[0]], [short], True)

    def test_longer_unique_abbreviation_passes(self) -> None:
        self.assert_trace([self.shas[0]], [self.shas[0][:12]], True)

    def test_full_sha_passes(self) -> None:
        self.assert_trace([self.shas[0]], [self.shas[0]], True)

    def test_different_valid_commit_fails(self) -> None:
        result = self.assert_trace([self.shas[0]], [self.shas[1][:12]], False)
        self.assertEqual([self.shas[0]], result["missing_expected_shas"])
        self.assertEqual([self.shas[1]], result["unexpected_shas"])

    def test_nonexistent_hash_fails(self) -> None:
        reference = "fffffff"
        while resolve_commit_reference(self.repo, reference) is not None:
            reference = f"{int(reference, 16) - 1:07x}"
        result = self.assert_trace([self.shas[0]], [reference], False)
        self.assertEqual([reference], result["invalid_references"])

    def test_missing_required_commit_fails(self) -> None:
        result = self.assert_trace(self.shas[:2], [self.shas[0][:12]], False)
        self.assertEqual([self.shas[1]], result["missing_expected_shas"])

    def test_duplicate_does_not_compensate_for_missing_commit(self) -> None:
        reference = self.shas[0][:12]
        result = self.assert_trace(self.shas[:2], [reference, reference], False)
        self.assertEqual([self.shas[1]], result["missing_expected_shas"])

    def test_non_commit_object_fails(self) -> None:
        blob = self.git("hash-object", "-w", "--stdin", stdin="not a commit\n")
        result = self.assert_trace([self.shas[0]], [blob], False)
        self.assertEqual([blob], result["invalid_references"])

    def test_ambiguous_abbreviation_fails(self) -> None:
        empty_tree = self.git("mktree", stdin="")
        seen: dict[str, tuple[str, str]] = {}
        collision: tuple[str, str, str, str] | None = None
        for index in range(120_000):
            body = (
                f"tree {empty_tree}\n"
                "author Project 8 Test <project8-test@example.invalid> 0 +0000\n"
                "committer Project 8 Test <project8-test@example.invalid> 0 +0000\n\n"
                f"collision candidate {index}\n"
            )
            raw = body.encode()
            oid = hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            prefix = oid[:7]
            previous = seen.get(prefix)
            if previous and previous[0] != oid:
                collision = (prefix, previous[0], previous[1], body)
                break
            seen[prefix] = (oid, body)
        self.assertIsNotNone(collision, "could not generate an ambiguous seven-character prefix")
        prefix, first_oid, first_body, second_body = collision  # type: ignore[misc]
        self.assertEqual(first_oid, self.git("hash-object", "-t", "commit", "-w", "--stdin", stdin=first_body))
        self.git("hash-object", "-t", "commit", "-w", "--stdin", stdin=second_body)
        self.assertIsNone(resolve_commit_reference(self.repo, prefix))
        result = self.assert_trace([first_oid], [prefix], False)
        self.assertEqual([prefix], result["invalid_references"])


if __name__ == "__main__":
    unittest.main()
