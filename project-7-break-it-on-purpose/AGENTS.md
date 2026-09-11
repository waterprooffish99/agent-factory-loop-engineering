# Morning Brief

This project has one job: each morning, tell you what is **new** in this repo
since the last time it looked — new commits, new `TODO`/`FIXME` markers, freshly
changed files — and **nothing you have already been told**.

**Any request for the morning brief — "what's new", "what changed since
yesterday", the daily brief, a scheduled morning summary — is answered by running
this project's script, never from memory:**

    python3 .claude/skills/morning-brief/scripts/brief.py --run

(In Claude Code this runs through the `morning-brief` skill; any other agent runs
the script directly.) The script owns the repo scan, the delta, and — most
importantly — the **spine**: it reads `progress.md` first to learn what was
already reported, and writes it last.

The one thing to hold onto: this loop has a **memory**. `progress.md` is the
spine. Reading it first is what lets each run report only what is **new** instead
of repeating yesterday's list. Delete `progress.md` and the loop forgets
everything — every item looks new again. **No spine, no loop.**

This is a **scheduled** watch (Concept 6): it looks forward to *today*, and it
**speaks even when nothing happened** — most mornings it just says "all clear."

If the scan fails, say so — never invent work items. A brief that reports a file
or commit that does not exist is the one answer a watch must never give.

## Safety (the human gate)

The loop never acts on risky items. If a delta item contains a destructive
command (`rm -rf`, `DROP TABLE`, `git push --force`) or a secret, it is written
to `## Open / Needs a Human` in `progress.md` and left for a person to decide.
The loop never pushes to `main`.
