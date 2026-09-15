#!/usr/bin/env python3
"""Run one bounded, observable daily changelog beat."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check import changed_files, check_proposal
from common import (
    EVIDENCE_DIR,
    LOG_DIR,
    PROGRESS_PATH,
    PROJECT_DIR,
    REPO_DIR,
    STATE_PATH,
    BeatError,
    atomic_write_json,
    frozen_manifest_digest,
    load_json,
    redact,
    run,
    sha256_text,
    utc_now,
)
from discover import discover


TOTAL_TIMEOUT_SECONDS = 900
MAX_MAKER_ATTEMPTS = 1
MAX_CHECKER_ATTEMPTS = 1
MAX_FILES_CHANGED = 1
DEFAULT_BRANCH = "main"
DEFAULT_REF = "refs/remotes/origin/main"
BRANCH_PREFIX = "project-8/changelog-beat-"


class BeatLogger:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def log(self, event: str, **fields: Any) -> None:
        record = {"timestamp": utc_now(), "event": event, **fields}
        safe = redact(json.dumps(record, sort_keys=True, default=str))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(safe + "\n")


def remaining(started: float) -> float:
    left = TOTAL_TIMEOUT_SECONDS - (time.monotonic() - started)
    if left <= 0:
        raise BeatError(f"hard beat timeout exceeded ({TOTAL_TIMEOUT_SECONDS}s)")
    return left


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise BeatError("state.json is missing; initialize it deliberately before running")
    state = load_json(STATE_PATH)
    if state.get("schema_version") != 1 or not state.get("successful_checkpoint"):
        raise BeatError("state.json is invalid")
    return state


def save_state(state: dict[str, Any]) -> None:
    atomic_write_json(STATE_PATH, state)


def append_progress(beat: dict[str, Any]) -> None:
    commits = ", ".join(item.get("short_sha", item.get("sha", "")[:7]) for item in beat["discovered_commits"]) or "none"
    branch_display = f"`{beat['branch']}`" if beat.get("branch") else "none"
    lines = [
        f"\n## Beat {beat['beat_number']} — {beat['timestamp']}\n",
        f"- Starting checkpoint: `{beat['starting_checkpoint']}`\n",
        f"- Discovered commits: {commits}\n",
        f"- Result: **{beat['result']}**\n",
        f"- Branch: {branch_display}\n",
        f"- PR: {beat.get('pr_url') or 'none'}\n",
        f"- Checker: {beat.get('checker_result') or 'NOT_RUN'}\n",
        f"- Runtime: {beat.get('runtime_seconds', 0)} seconds\n",
        f"- Failure reason: {beat.get('failure_reason') or 'none'}\n",
        f"- Evidence: `evidence/beat-{beat['beat_number']:04d}/beat.json`\n",
    ]
    with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
        handle.writelines(lines)


def record_final(state: dict[str, Any], beat: dict[str, Any], evidence: Path, started: float, logger: BeatLogger) -> None:
    beat["runtime_seconds"] = round(time.monotonic() - started, 3)
    state["beats"][-1] = beat
    state["updated_at"] = utc_now()
    save_state(state)
    atomic_write_json(evidence / "beat.json", beat)
    append_progress(beat)
    logger.log("beat_finished", result=beat["result"], runtime_seconds=beat["runtime_seconds"], failure_reason=beat.get("failure_reason"))


def parse_remote_repo() -> str:
    url = run(["git", "remote", "get-url", "origin"], cwd=REPO_DIR).stdout.strip()
    match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise BeatError("origin is not a recognizable GitHub repository URL")
    return match.group(1)


def reconcile_pending(state: dict[str, Any], beat: dict[str, Any], started: float, logger: BeatLogger) -> bool:
    pending = state.get("pending_review")
    if not pending:
        return False
    beat["branch"] = pending.get("branch")
    beat["pr_url"] = pending.get("pr_url")
    if not pending.get("pr_number"):
        beat["result"] = "NEEDS_HUMAN"
        beat["failure_reason"] = "a Project 8 branch was pushed but no PR was created; resolve it manually"
        return True
    response = run(
        ["gh", "pr", "view", str(pending["pr_number"]), "--json", "state,mergedAt,mergeCommit,url,headRefName"],
        cwd=REPO_DIR,
        timeout=remaining(started),
    )
    info = json.loads(response.stdout)
    logger.log("pending_pr_inspected", pr=info)
    if info["state"] == "OPEN":
        beat["result"] = "NEEDS_HUMAN"
        beat["failure_reason"] = "WAITING_HUMAN: the previous Project 8 PR remains open"
        return True
    if info["state"] != "MERGED" or not info.get("mergeCommit", {}).get("oid"):
        beat["result"] = "NEEDS_HUMAN"
        beat["failure_reason"] = "the previous Project 8 PR closed without a verifiable merge"
        return True
    merge_sha = info["mergeCommit"]["oid"]
    run(["git", "merge-base", "--is-ancestor", pending["covered_through"], merge_sha], cwd=REPO_DIR, timeout=remaining(started))
    state["successful_checkpoint"] = merge_sha
    state["pending_review"] = None
    beat["starting_checkpoint"] = merge_sha
    logger.log("checkpoint_advanced_after_merge", checkpoint=merge_sha)
    return False


def codex_invocation(
    *,
    role: str,
    worktree: Path,
    prompt: str,
    output_schema: Path,
    output_file: Path,
    events_file: Path,
    sandbox: str,
    started: float,
) -> tuple[int, str, str]:
    args = [
        "codex", "--ask-for-approval", "never", "exec", "--ephemeral", "--sandbox", sandbox,
        "--cd", str(worktree),
        "--output-schema", str(output_schema), "--output-last-message", str(output_file),
        "--json", "-",
    ]
    result = run(args, cwd=worktree, timeout=remaining(started), stdin=prompt, allowed_returncodes=tuple(range(0, 256)))
    events_file.write_text(redact(result.stdout), encoding="utf-8")
    (events_file.parent / f"{role}.stderr.txt").write_text(redact(result.stderr), encoding="utf-8")
    final = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
    return result.returncode, final, result.stderr


def make_prompt(discovery: dict[str, Any]) -> str:
    template = (PROJECT_DIR / "prompts/maker.md").read_text(encoding="utf-8")
    skill = (PROJECT_DIR / "skills/changelog/SKILL.md").read_text(encoding="utf-8")
    commits = "\n".join(f"- {c['sha']} | {c['date']} | {c['subject']}" for c in discovery["commits"])
    return (
        f"{template}\n\n## Embedded skill\n\n{skill}\n\n"
        f"## Exact scope\n\nCheckpoint (exclusive): {discovery['checkpoint_exclusive']}\n"
        f"Tip (inclusive): {discovery['tip']}\nCommit range: {discovery['checkpoint_exclusive']}..{discovery['tip']}\n"
        f"Covered commits, chronological:\n{commits}\n"
        "Use local Git commands to inspect the actual commits and diffs. Do not use network access.\n"
    )


def checker_prompt(discovery: dict[str, Any], report: dict[str, Any]) -> str:
    template = (PROJECT_DIR / "prompts/checker.md").read_text(encoding="utf-8")
    skill = (PROJECT_DIR / "skills/changelog/SKILL.md").read_text(encoding="utf-8")
    evidence = {key: value for key, value in report.items() if key != "diff"}
    commits = json.dumps(discovery["commits"], indent=2)
    return (
        f"{template}\n\n## Embedded skill\n\n{skill}\n\n"
        f"## Covered commits\n\n```json\n{commits}\n```\n\n"
        f"## Exact local range\n\nCheckpoint (exclusive): `{discovery['checkpoint_exclusive']}`\n\n"
        f"Tip (inclusive): `{discovery['tip']}`\n\n"
        f"Run `git log` and `git diff {discovery['checkpoint_exclusive']}..{discovery['tip']}` read-only to verify every substantive claim.\n\n"
        f"## Deterministic report\n\n```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
        f"## Proposed diff\n\n```diff\n{report['diff']}\n```\n"
    )


def cleanup_worktree(worktree: Path | None, branch: str | None, *, keep_branch: bool, logger: BeatLogger) -> None:
    if worktree and worktree.exists():
        result = run(["git", "worktree", "remove", "--force", str(worktree)], cwd=REPO_DIR, allowed_returncodes=tuple(range(0, 256)))
        logger.log("worktree_cleanup", returncode=result.returncode, stderr=result.stderr)
        parent = worktree.parent
        if parent.name.startswith("project-8-beat-"):
            shutil.rmtree(parent, ignore_errors=True)
    if branch and not keep_branch:
        tip = run(["git", "rev-parse", branch], cwd=REPO_DIR, allowed_returncodes=(0, 128))
        if tip.returncode == 0:
            result = run(["git", "branch", "-D", branch], cwd=REPO_DIR, allowed_returncodes=tuple(range(0, 256)))
            logger.log("generated_branch_cleanup", returncode=result.returncode, stderr=result.stderr)


def list_open_project_prs(repo_name: str, started: float) -> list[dict[str, Any]]:
    result = run(
        ["gh", "pr", "list", "--repo", repo_name, "--state", "open", "--limit", "100", "--json", "number,url,headRefName,title"],
        cwd=REPO_DIR,
        timeout=remaining(started),
    )
    return [pr for pr in json.loads(result.stdout) if pr.get("headRefName", "").startswith(BRANCH_PREFIX)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fetch", action="store_true", help="supervised/offline diagnostics only")
    args = parser.parse_args()

    started = time.monotonic()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = PROJECT_DIR / ".beat.lock"
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit("another Project 8 beat is already running") from exc

        state = load_state()
        beat_number = int(state["next_beat_number"])
        state["next_beat_number"] = beat_number + 1
        timestamp = utc_now()
        date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
        evidence = EVIDENCE_DIR / f"beat-{beat_number:04d}"
        evidence.mkdir(parents=True, exist_ok=False)
        logger = BeatLogger(LOG_DIR / f"beat-{beat_number:04d}.log")
        beat: dict[str, Any] = {
            "timestamp": timestamp,
            "beat_number": beat_number,
            "starting_checkpoint": state["successful_checkpoint"],
            "discovered_commits": [],
            "result": "NEEDS_HUMAN",
            "branch": None,
            "pr_number": None,
            "pr_url": None,
            "checker_result": "NOT_RUN",
            "deterministic_result": "NOT_RUN",
            "worktree_path": None,
            "files_changed": [],
            "runtime_seconds": 0,
            "failure_reason": "beat started but did not finish",
            "metrics": {
                "maker_attempts": 0,
                "checker_attempts": 0,
                "model_invocations": 0,
                "subprocess_exit_codes": [],
            },
        }
        state.setdefault("beats", []).append(beat)
        save_state(state)
        logger.log("beat_started", beat_number=beat_number, checkpoint=beat["starting_checkpoint"])

        worktree: Path | None = None
        branch: str | None = None
        keep_branch = False
        exit_code = 1
        try:
            if not args.skip_fetch:
                fetched = run(["git", "fetch", "--prune", "origin", DEFAULT_BRANCH], cwd=REPO_DIR, timeout=remaining(started))
                beat["metrics"]["subprocess_exit_codes"].append({"name": "git_fetch", "code": fetched.returncode})
                logger.log("fetch_complete", returncode=fetched.returncode)

            if reconcile_pending(state, beat, started, logger):
                beat["failure_reason"] = beat["failure_reason"]
                exit_code = 2
                return exit_code

            discovery = discover(state["successful_checkpoint"], DEFAULT_REF, timeout=remaining(started))
            beat["starting_checkpoint"] = discovery["checkpoint_exclusive"]
            beat["discovered_commits"] = discovery["commits"]
            atomic_write_json(evidence / "discovery.json", discovery)
            logger.log("discovery_complete", count=discovery["commit_count"], tip=discovery["tip"])
            if not discovery["commits"]:
                beat["result"] = "NO_WORK"
                beat["failure_reason"] = None
                state["successful_checkpoint"] = discovery["tip"]
                exit_code = 0
                return exit_code

            repo_name = parse_remote_repo()
            existing_project_prs = list_open_project_prs(repo_name, started)
            if existing_project_prs:
                beat["pr_number"] = existing_project_prs[0]["number"]
                beat["pr_url"] = existing_project_prs[0]["url"]
                raise BeatError(f"open Project 8 PR already exists: {existing_project_prs[0]['url']}")

            if MAX_MAKER_ATTEMPTS != 1 or MAX_CHECKER_ATTEMPTS != 1 or MAX_FILES_CHANGED != 1:
                raise BeatError("compiled budget guard constants are invalid")

            branch = f"{BRANCH_PREFIX}{beat_number:04d}-{date_tag}"
            beat["branch"] = branch
            existing = run(
                ["git", "show-ref", "--verify", f"refs/heads/{branch}"],
                cwd=REPO_DIR,
                allowed_returncodes=(0, 1, 128),
            )
            if existing.returncode == 0:
                raise BeatError(f"generated branch already exists: {branch}")

            default_head_before = run(["git", "rev-parse", f"refs/heads/{DEFAULT_BRANCH}"], cwd=REPO_DIR).stdout.strip()
            default_diff_before = run(["git", "diff", "HEAD", "--binary"], cwd=REPO_DIR).stdout
            frozen_before = frozen_manifest_digest()
            temp_root = Path(tempfile.mkdtemp(prefix=f"project-8-beat-{beat_number:04d}-"))
            worktree = temp_root / "worktree"
            created = run(["git", "worktree", "add", "-b", branch, str(worktree), discovery["tip"]], cwd=REPO_DIR, timeout=remaining(started))
            beat["metrics"]["subprocess_exit_codes"].append({"name": "git_worktree_add", "code": created.returncode})
            beat["worktree_path"] = str(worktree)
            logger.log("worktree_created", path=str(worktree), branch=branch)

            beat["metrics"]["maker_attempts"] = 1
            beat["metrics"]["model_invocations"] += 1
            maker_output = evidence / "maker.final.json"
            maker_code, maker_final, maker_stderr = codex_invocation(
                role="maker",
                worktree=worktree,
                prompt=make_prompt(discovery),
                output_schema=PROJECT_DIR / "prompts/maker.schema.json",
                output_file=maker_output,
                events_file=evidence / "maker.events.jsonl",
                sandbox="workspace-write",
                started=started,
            )
            beat["metrics"]["subprocess_exit_codes"].append({"name": "codex_maker", "code": maker_code})
            if maker_code != 0:
                raise BeatError(f"maker process failed ({maker_code}): {maker_stderr[:500]}")
            try:
                maker = json.loads(maker_final)
            except json.JSONDecodeError as exc:
                raise BeatError("maker did not return valid schema-conforming JSON") from exc
            atomic_write_json(evidence / "maker.result.json", maker)
            logger.log("maker_complete", decision=maker.get("decision"), returncode=maker_code)

            files_now = changed_files(worktree)
            if maker.get("decision") == "NO_WORK":
                if files_now:
                    raise BeatError("maker claimed NO_WORK but changed files")
                beat["result"] = "NO_WORK"
                beat["failure_reason"] = None
                beat["files_changed"] = []
                state["successful_checkpoint"] = discovery["tip"]
                exit_code = 0
                return exit_code
            if maker.get("decision") != "UPDATED":
                raise BeatError("maker returned an unsupported decision")

            report = check_proposal(
                worktree=worktree,
                branch=branch,
                default_branch=DEFAULT_BRANCH,
                default_head_before=default_head_before,
                default_diff_digest_before=sha256_text(default_diff_before),
                frozen_digest_before=frozen_before,
                maker_exit_code=maker_code,
                expected_full_shas=[commit["sha"] for commit in discovery["commits"]],
            )
            beat["files_changed"] = report["changed_files"]
            beat["deterministic_result"] = "PASS" if report["passed"] else "FAIL"
            atomic_write_json(evidence / "deterministic-check.json", {k: v for k, v in report.items() if k != "diff"})
            (evidence / "proposed.diff").write_text(redact(report["diff"]), encoding="utf-8")
            logger.log("deterministic_check_complete", passed=report["passed"], checks=report["checks"])
            if not report["passed"]:
                raise BeatError("deterministic checker failed; model checker was not allowed to overrule it")

            beat["metrics"]["checker_attempts"] = 1
            beat["metrics"]["model_invocations"] += 1
            checker_output = evidence / "checker.final.json"
            checker_code, checker_final, checker_stderr = codex_invocation(
                role="checker",
                worktree=worktree,
                prompt=checker_prompt(discovery, report),
                output_schema=PROJECT_DIR / "prompts/checker.schema.json",
                output_file=checker_output,
                events_file=evidence / "checker.events.jsonl",
                sandbox="read-only",
                started=started,
            )
            beat["metrics"]["subprocess_exit_codes"].append({"name": "codex_checker", "code": checker_code})
            if checker_code != 0:
                raise BeatError(f"checker process failed ({checker_code}): {checker_stderr[:500]}")
            try:
                checker = json.loads(checker_final)
            except json.JSONDecodeError as exc:
                raise BeatError("checker did not return valid schema-conforming JSON") from exc
            atomic_write_json(evidence / "checker.result.json", checker)
            beat["checker_result"] = checker.get("verdict", "INVALID")
            logger.log("checker_complete", verdict=beat["checker_result"], returncode=checker_code)
            if beat["checker_result"] != "PASS":
                raise BeatError("independent checker returned FAIL; no retry is permitted")

            run(["git", "add", "--", "CHANGELOG.md"], cwd=worktree, timeout=remaining(started))
            committed = run(
                ["git", "commit", "-m", f"docs(changelog): summarize changes through {discovery['tip'][:7]}"],
                cwd=worktree,
                timeout=remaining(started),
            )
            beat["metrics"]["subprocess_exit_codes"].append({"name": "git_commit", "code": committed.returncode})
            keep_branch = True
            branch_head = run(["git", "rev-parse", "HEAD"], cwd=worktree).stdout.strip()
            logger.log("changelog_committed", branch_head=branch_head)

            open_project_prs = list_open_project_prs(repo_name, started)
            if open_project_prs:
                raise BeatError(f"open Project 8 PR already exists: {open_project_prs[0]['url']}")

            pushed = run(["git", "push", "--set-upstream", "origin", branch], cwd=worktree, timeout=remaining(started))
            beat["metrics"]["subprocess_exit_codes"].append({"name": "git_push", "code": pushed.returncode})
            state["pending_review"] = {
                "status": "PUSHED_NO_PR",
                "branch": branch,
                "branch_head": branch_head,
                "pr_number": None,
                "pr_url": None,
                "covered_from_exclusive": discovery["checkpoint_exclusive"],
                "covered_through": discovery["tip"],
            }
            save_state(state)

            body = (
                "## Daily changelog beat\n\n"
                f"- Beat: {beat_number}\n"
                f"- Covered: `{discovery['checkpoint_exclusive'][:12]}..{discovery['tip'][:12]}`\n"
                "- Deterministic checks: PASS\n"
                "- Independent checker: PASS\n\n"
                "Human gate: review and merge manually if the changelog is accurate. This automation never merges PRs.\n"
            )
            created_pr = run(
                ["gh", "pr", "create", "--repo", repo_name, "--base", DEFAULT_BRANCH, "--head", branch,
                 "--title", f"docs: daily changelog through {discovery['tip'][:7]}", "--body", body],
                cwd=worktree,
                timeout=remaining(started),
            )
            beat["metrics"]["subprocess_exit_codes"].append({"name": "gh_pr_create", "code": created_pr.returncode})
            info_result = run(
                ["gh", "pr", "view", branch, "--repo", repo_name, "--json", "number,url,state,headRefName"],
                cwd=worktree,
                timeout=remaining(started),
            )
            info = json.loads(info_result.stdout)
            if info.get("state") != "OPEN":
                raise BeatError("created PR is not open")
            beat["pr_number"] = info["number"]
            beat["pr_url"] = info["url"]
            beat["result"] = "PASS"
            beat["failure_reason"] = None
            state["pending_review"].update({"status": "OPEN", "pr_number": info["number"], "pr_url": info["url"]})
            save_state(state)
            logger.log("pull_request_opened", number=info["number"], url=info["url"], branch=branch)
            exit_code = 0
            return exit_code
        except BeatError as exc:
            beat["result"] = "NEEDS_HUMAN"
            beat["failure_reason"] = str(exc)
            logger.log("safe_stop", reason=str(exc))
            exit_code = 2
            return exit_code
        except Exception as exc:  # last-resort evidence for an unexpected failure
            beat["result"] = "FAIL"
            beat["failure_reason"] = f"unexpected {type(exc).__name__}: {exc}"
            logger.log("unexpected_failure", reason=beat["failure_reason"])
            exit_code = 1
            return exit_code
        finally:
            cleanup_worktree(worktree, branch, keep_branch=keep_branch, logger=logger)
            record_final(state, beat, evidence, started, logger)


if __name__ == "__main__":
    raise SystemExit(main())
