---
name: daily-changelog
description: Draft a concise, evidence-grounded repository changelog from a bounded Git commit range.
---

# Daily Changelog Skill

## Meaningful changes

Include reader-visible milestones: a project or substantial feature completed, important behavior added or changed, a significant defect fixed, safety or workflow guarantees changed, or documentation that materially changes how the repository is understood or used.

Exclude mechanical churn, formatting-only edits, generated artifacts, raw file inventories, implementation trivia, and commits whose only effect is maintaining this changelog. Group related commits into a single useful statement when appropriate.

## Required format

- Preserve an existing repository-level `CHANGELOG.md` format when one exists.
- If none exists, create a short Markdown document headed `# Changelog`, followed by a one-sentence purpose statement and newest-first dated sections.
- Use a `## YYYY-MM-DD` section for the covered update.
- Write concise bullets describing outcomes for a human reader, not raw Git-log output.
- End the section with `Commits:` and commit hashes in chronological order for traceability. Human-readable abbreviations of at least seven hexadecimal characters are allowed, but each must resolve unambiguously in Git to the exact covered commit.
- Every claim must be supported by the supplied commit range. Do not infer unsupported results.

## Allowed files

The maker may create or edit exactly one repository file: `/CHANGELOG.md`.

## Forbidden actions

- Do not change any Project 1–7 file or any Project 8 implementation/state/evidence file.
- Do not commit, push, merge, switch branches, create another worktree, rewrite history, or contact GitHub.
- Do not include secrets, credentials, personal contact details, or authentication material.
- Do not grade or approve your own work.

## Verification expectations

Before reporting `UPDATED`, compare every bullet with the actual diff and commit metadata, confirm the commit trace is complete, ensure Markdown is readable UTF-8 text, and confirm `git status` names only `CHANGELOG.md`. Report `NO_WORK` and leave the tree unchanged if the commits contain no meaningful reader-facing change.
