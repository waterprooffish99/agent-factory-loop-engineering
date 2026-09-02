---
name: morning-brief
description: Show what is NEW in this repository since the last morning brief — new git commits, newly added TODO/FIXME/BUG/HACK markers, and freshly changed files — by running this skill's bundled script, never from memory. The script reads progress.md (the spine) first to learn what was already reported, scans the repo fresh, prints only the genuinely new items as a dated brief in briefs/, and writes progress.md last. Use it whenever the user asks for the morning brief, what changed since yesterday, what is new in the repo, or runs a scheduled daily summary job. Only new-since-last-time counts — reporting the same item twice defeats the point of a watch.
allowed-tools: Bash, Read
---

# Morning brief

A morning brief is only useful if it tells you what is **new**. Repeating
yesterday's list is noise. So this skill remembers what it has already reported —
in a file, `progress.md`, the loop's **spine** — and each run reports only what
changed since then.

The repo's state is not guessable from memory: commits land, markers get added,
files change between runs. So the brief always comes from the bundled script, run
fresh, every time — never from memory.

## Running today's brief

Run the script. It reads `progress.md` first, scans the repo, writes a dated brief
to `briefs/`, then updates `progress.md`:

```bash
python3 .claude/skills/morning-brief/scripts/brief.py --run
```

See the current memory without running a beat:

```bash
python3 .claude/skills/morning-brief/scripts/brief.py --status
```

## The spine is the whole point of this project

- The script **reads `progress.md` first** ("what have I already reported?") and
  **writes it last** ("remember what I reported this time"). That file is the
  memory that survives between runs.
- The repo changes about **once a day or less** for a solo project, so a **daily
  schedule** is the natural heartbeat: run it each morning and get only that day's
  new work. Run it twice in a row and the second says "all clear" — the memory
  worked.
- If the scan fails (e.g. `git` is unavailable), **say so** — never invent
  commits or files. A made-up "here's what's new" is the one answer a watch must
  never give.

## "No new items since last checkpoint" is correct, not broken

A scheduled watch **speaks even when nothing happened** — most mornings it reports
"all clear." That is the spine working: it remembered. To show a beginner **why**
the spine matters, delete it and run again — every item comes back as new:

```bash
rm progress.md      # erase the memory... now every item looks new again. No spine, no loop.
```

## Safety — the human gate

Before reporting, the script checks each new item for risky content (destructive
commands like `rm -rf` / `DROP TABLE` / `git push --force`, or exposed secrets).
Any such item is **not** acted on: it is written to `## Open / Needs a Human` in
`progress.md` and left for a person. The loop never pushes to `main`.
