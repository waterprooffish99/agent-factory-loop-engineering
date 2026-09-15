# Project 8 Agent Rules

These rules apply to everything under `project-8-daily-changelog/`.

- Projects 1–7 are frozen. Never modify, delete, move, rename, or clean their files.
- Never edit the repository-level `CHANGELOG.md` from the default working tree. Changelog drafting happens only in the temporary worktree created by `scripts/run_beat.py`.
- Never merge a pull request, push the default branch, rewrite history, or delete a branch that may contain user work.
- The only maker-writable repository file is `/CHANGELOG.md`.
- The independent checker may read but must not write.
- A deterministic check failure cannot be overruled by a model.
- Do not install `cron.example`; it is documentation until a human explicitly activates it.
- Preserve all beat logs, evidence, and spine entries. Never place credentials or tokens in them.
