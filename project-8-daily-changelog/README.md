# Project 8 — Daily Changelog Loop

This capstone automates a real recurring chore: inspect newly accepted default-branch commits, draft a concise evidence-grounded changelog when meaningful work exists, verify the draft independently, and open a GitHub pull request for human review. It never pushes to the default branch or merges a pull request.

The supervised lifecycle is complete. The example daily heartbeat remains intentionally uninstalled until a human separately approves activation.

## Loop architecture

```text
HEARTBEAT → READ SPINE → DISCOVER COMMITS → BUDGET GUARDS
→ ISOLATED WORKTREE → MAKER → CHANGELOG SKILL
→ DETERMINISTIC CHECKS → INDEPENDENT CHECKER
→ GITHUB CONNECTOR → OPEN PR → HUMAN GATE
→ RECONCILE MERGE → UPDATE SPINE → NEXT BEAT
```

The six implementation parts are:

1. **Heartbeat:** `cron.example` documents a proposed daily 07:17 Asia/Karachi run. It is an example, not an installed schedule.
2. **Worktree isolation:** `scripts/run_beat.py` creates a temporary worktree on a generated `project-8/changelog-beat-NNNN-YYYYMMDD` branch. Only that isolated worktree is writable by the maker.
3. **Changelog skill:** `skills/changelog/SKILL.md` defines meaningful changes, output format, allowed scope, prohibitions, and evidence expectations.
4. **Maker-checker:** a fresh ephemeral Codex process may edit only `/CHANGELOG.md`; a second fresh process runs read-only and must inspect actual Git history and diffs. `scripts/check.py` is the deterministic gate between them.
5. **GitHub connector:** only after both gates pass, the loop pushes the generated branch and opens one pull request. There is no merge command.
6. **Persistent spine:** local state records checkpoints, beats, pending review, evidence, and observable metrics across independent runs.

## Tracking and runtime policy

Reusable source and documentation are version-controlled: this README, `AGENTS.md`, `.gitignore`, `cron.example`, `scripts/`, `tests/`, `skills/`, `prompts/`, and `state.example.json`.

Operational files are deliberately local and ignored:

- `state.json` — canonical live machine state and checkpoint history.
- `progress.md` — append-only human-readable beat ledger.
- `.beat.lock` — non-blocking concurrent-run guard.
- `logs/` — timestamped JSON-lines operational events.
- `evidence/` — per-beat discovery, model, diff, and checker artifacts.
- Python bytecode caches.

Ignoring these paths does not make the loop stateless. The files remain on the machine, are read and updated normally on every beat, and survive across runs; they simply do not turn routine operation into Git changes. Existing supervised evidence is preserved locally. `state.example.json` is a bootstrap contract, not live state.

For a fresh clone, copy the template to `state.json`, replace `successful_checkpoint` with the intended full Git commit SHA, and review that boundary before the first run:

```bash
cp project-8-daily-changelog/state.example.json project-8-daily-changelog/state.json
```

Do not initialize the checkpoint speculatively: it defines the exclusive start of the first changelog range.

## Budget guards

- Hard total beat timeout: 900 seconds.
- Maker attempts: exactly 1.
- Checker attempts: exactly 1.
- Automatic retry after checker failure: 0.
- Maker file cap: 1 file, exactly repository-root `CHANGELOG.md`.
- Open generated Project 8 PR cap: 1.
- Concurrent local beats: 1, enforced with a non-blocking file lock.
- Metrics: model invocations, maker/checker attempts, subprocess exit codes, and wall-clock runtime.

An exceeded guard produces `NEEDS_HUMAN`. A deterministic failure cannot be overruled by a model, and a failed independent checker cannot trigger an automatic retry.

## Checkpoint and human-gate lifecycle

`successful_checkpoint` is the latest accepted default-branch integration point.

- No new commits: record `NO_WORK`; no model is invoked.
- Meaningless inspected commits: record `NO_WORK` and advance to the inspected tip.
- Passing draft and open PR: record `PASS` plus `pending_review`; do not advance the checkpoint.
- Pending PR still open: record `NEEDS_HUMAN` with `WAITING_HUMAN`; do no maker work.
- Pending PR merged: fetch, verify that the covered source tip is an ancestor of the merge, advance to the default-branch merge commit, clear pending review, and discover only later commits.
- PR closed without merge, unverifiable merge, pushed branch without a PR, or connector failure: record `NEEDS_HUMAN` and preserve state for manual investigation.

Generated work, checker approval, an open PR, human acceptance, and a merged PR are distinct states. Only the verified human merge advances a pending reviewed range.

## Deterministic and independent verification

Before the independent checker may run, `scripts/check.py` proves worktree isolation, unchanged default-branch HEAD and tracked diff, unchanged frozen Projects 1–7, one-file scope, bounded clean Markdown, a non-empty diff, valid branch naming, no conservative secret-pattern matches, and a successful maker process.

Commit trace validation extracts only the intentional added `Commits:` field. Plain, backtick-wrapped, and mixed hexadecimal references are accepted as candidates. Each candidate must contain at least seven characters, resolve unambiguously through Git to a commit object, and resolve to exactly the expected full commit set. Missing, invalid, ambiguous, duplicate-in-place-of-missing, non-commit, and unexpected references fail.

The independent checker receives a fresh read-only context and must inspect the actual checkpoint-to-tip Git history, commit diffs, relevant files, deterministic report, and proposed changelog diff. Commit subjects or maker confidence alone are insufficient.

## Supervised proof: Beats 1–7

Failures were preserved as evidence and followed by infrastructure repairs; no historical beat was rewritten to look successful.

- **Beats 1–2:** preserved preflight implementation failures exposed Git missing-ref handling and Codex CLI global-flag ordering.
- **Beat 3:** maker and deterministic checks ran, but the independent checker rejected claims that were not sufficiently verified from real commit diffs. Result: `NEEDS_HUMAN`, no push or PR.
- **Beat 4:** deterministic checking exposed a false negative caused by textual comparison of different valid abbreviations of the same commit. Canonical Git identity resolution and nine focused tests followed.
- **Beat 5:** valid plain hexadecimal references were missed because extraction recognized only backtick-wrapped SHAs. The scoped parser was repaired and the suite expanded to 17 tests.
- **Beat 6:** maker, deterministic checks, and independent checker passed. The connector opened PR #2 and stopped at the human gate.
- **Human gate:** Salman manually reviewed and merged PR #2; the automation did not merge it.
- **Beat 7:** the next normal beat detected the human merge, verified covered-commit ancestry, advanced the checkpoint to merge commit `b3d7e5d3a377ee36bf555265b2ecc17d0d11ca57`, cleared `pending_review`, discovered no later commits, and recorded `NO_WORK` with zero model invocations.

Raw supervised logs and evidence remain in the local ignored runtime directories. They are summarized here without publishing credentials, private model reasoning, or environment-specific artifacts.

## Run and verify manually

Prerequisites are Python 3, Git, authenticated `codex` and `gh` CLIs, and permission to push a generated branch. From the repository root:

```bash
python3 -m unittest discover -s project-8-daily-changelog/tests -v
python3 project-8-daily-changelog/scripts/run_beat.py
```

`--skip-fetch` exists only for supervised offline diagnostics; scheduled beats must fetch. Exit code 0 means `PASS` or `NO_WORK`, 2 means a safe `NEEDS_HUMAN` stop, and 1 means an unexpected failure. Every started beat writes initial spine state before substantive work and finalizes its evidence in a `finally` block.

The implementation was proven with `codex-cli 0.154.0`, using global `--ask-for-approval` before `exec`, plus `--ephemeral`, explicit maker/checker sandboxes, output schemas, and separate last-message files.

## Future heartbeat

`cron.example` is documentation for a future human-approved schedule. Before activation, review its repository path, execution account, environment, logging destination, authenticated CLI availability, and one-PR guard. Installing or changing crontab is outside the loop itself.

**Daily heartbeat is not yet activated.**

## Human gate

Every generated changelog PR must remain open for a human to compare its claims with the covered commits and checker evidence. A human alone decides whether and when to merge. The loop contains no auto-merge or auto-approval path.
