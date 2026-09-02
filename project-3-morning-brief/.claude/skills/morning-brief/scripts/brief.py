#!/usr/bin/env python3
"""brief.py — a MORNING BRIEF with a SPINE (memory between runs).

Every run scans this repo for work items — recent git commits and TODO/FIXME/BUG/
HACK markers — then reports ONLY the ones you have not been told about before. How
does it know which you've seen? It reads a file first — progress.md, the spine —
and writes to it last. That file is the memory.

    python3 brief.py --run       # one beat: scan, write today's brief, update the spine
    python3 brief.py --status    # show the current memory without running a beat

HOW TO READ THIS FILE (to learn the spine):
    The whole lesson is 3 steps, at the bottom in run_beat():
        1. READ the spine   -> read_spine()
        2. do the work       -> scan_repo(), then keep only the NEW items
        3. WRITE the spine   -> write_spine()
    read_spine() and write_spine() ARE the lesson — short, read those first.
    scan_repo() just looks at git + files; treat it as a black box that returns
    a list of work items.
"""

import argparse, hashlib, os, re, subprocess, sys
from datetime import datetime, timezone

# --- where the loop lives -------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # project-3 root
SPINE = os.path.join(REPO, "progress.md")   # the memory file — read first, written last
BRIEFS_DIR = os.path.join(REPO, "briefs")

# --- what counts as a work item, and what to ignore -----------------------
MARKERS = ("TODO", "FIXME", "BUG", "HACK")
CODE_EXT = (".py", ".js", ".ts", ".sh", ".rb", ".go", ".rs", ".java", ".c", ".cpp")
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
               "briefs", "_prev_agy_attempt", ".claude"}
MAX_SEEN = 500              # cap the memory so it can't grow forever (a "stop")
MAX_COMMITS = 30            # how far back a first run looks

# --- risky content -> never act, escalate to a human (the human gate) ------
RISKY = ("rm -rf", "drop table", "drop database", "git push --force",
         "git push -f", "secret_key", "private_key", "deploy --prod")

SECTIONS = ["## Checkpoints", "## Done", "## In Progress", "## Open / Needs a Human"]


# ══════════════════════════════════════════════════════════════════════════
#  THE SPINE  —  this is the lesson. Read it, then write it.
# ══════════════════════════════════════════════════════════════════════════

def read_spine():
    """Read the memory: which items have we already reported? (empty on first run)."""
    state = {"seen": set(), "checkpoints": [], "done": [], "in_progress": [], "open": []}
    if not os.path.exists(SPINE):
        return state                        # no file yet -> no memory -> everything is new
    section = None
    bucket = {"## Checkpoints": "checkpoints", "## Done": "done",
              "## In Progress": "in_progress", "## Open / Needs a Human": "open"}
    for line in open(SPINE, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.strip() in bucket:
            section = bucket[line.strip()]
        elif section and line.startswith("- "):
            state[section].append(line)
    for line in state["done"] + state["open"]:
        m = re.search(r"\[sig:([0-9a-f]+)\]", line)
        if m:
            state["seen"].add(m.group(1))   # remember every signature we've shown
    return state


def write_spine(state):
    """Write the memory: save every item reported, so the NEXT run remembers."""
    out = [
        "# progress.md — the SPINE (this loop's memory)",
        "# The morning brief reads this file first, so each run reports only what is",
        "# NEW. Delete it and every item looks new again — that is \"no spine, no loop\".",
        "",
    ]
    body = {
        "## Checkpoints": state["checkpoints"],
        "## Done": state["done"][-MAX_SEEN:],       # cap so the memory can't grow forever
        "## In Progress": state["in_progress"] or ["<!-- items a human is actively working -->"],
        "## Open / Needs a Human": state["open"] or ["<!-- risky items halted for a human decision -->"],
    }
    for header in SECTIONS:
        out.append(header)
        out.extend(body[header])
        out.append("")
    with open(SPINE, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


# ══════════════════════════════════════════════════════════════════════════
#  THE WORK  —  scan the repo for items. Treat as a black box: it returns a
#  list of work items, each with a stable signature so we can tell new from old.
# ══════════════════════════════════════════════════════════════════════════

def sig(text):
    """A stable signature for an item — same item, same signature, every run."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def git_commits():
    """Recent commits as items. Returns (items, error) — error is a string or None."""
    try:
        out = subprocess.run(
            ["git", "-C", REPO, "log", f"-n{MAX_COMMITS}", "--pretty=format:%h\x1f%s"],
            capture_output=True, text=True, timeout=20)
        if out.returncode != 0:
            return [], (out.stderr.strip() or "git log failed")
    except Exception as e:                       # git missing, not a repo, timeout...
        return [], str(e)
    items = []
    for line in out.stdout.splitlines():
        if "\x1f" not in line:
            continue
        short, subject = line.split("\x1f", 1)
        items.append(mk_item("COMMIT", short, subject, kind="commit"))
    return items, None


def marker_items():
    """TODO/FIXME/BUG/HACK annotations in code files (docs and infra are ignored)."""
    pat = re.compile(r"\b(" + "|".join(MARKERS) + r")\b[:\s-]*(.*)")
    items = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            if not name.endswith(CODE_EXT):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, REPO).replace("\\", "/")
            try:
                for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                    m = pat.search(line)
                    if m:
                        text = m.group(2).strip() or line.strip()
                        items.append(mk_item(m.group(1), f"{rel}:{n}", text, kind="marker"))
            except OSError:
                continue
    return items


def mk_item(mtype, loc, text, kind):
    """Build one work item and flag it if it contains risky content (human gate)."""
    low = f"{loc} {text}".lower()
    reason = next((f"destructive/secret pattern: {p}" for p in RISKY if p in low), None)
    key = f"{kind}:{loc}" if kind == "commit" else f"{mtype}:{loc.split(':')[0]}:{text}"
    return {"sig": sig(key), "type": mtype, "loc": loc, "text": text,
            "risky": reason is not None, "reason": reason}


def scan_repo():
    """All work items right now, plus any scan error to report honestly."""
    commits, git_err = git_commits()
    return commits + marker_items(), git_err


# ══════════════════════════════════════════════════════════════════════════
#  the brief on disk, and the loop's one beat
# ══════════════════════════════════════════════════════════════════════════

def write_brief(beat, now, scanned, seen_count, new_safe, new_risky, git_err):
    os.makedirs(BRIEFS_DIR, exist_ok=True)
    path = os.path.join(BRIEFS_DIR, f"{now.strftime('%Y-%m-%d')}-beat-{beat}.md")
    L = [f"# 🌅 Morning Brief — Beat {beat}",
         f"**Generated:** {now.strftime('%Y-%m-%dT%H:%M:%SZ')} · scheduled watch (weekday 09:00)",
         "", "## Summary",
         f"- Items scanned: {scanned}",
         f"- Already in the spine: {seen_count}",
         f"- New since last checkpoint: {len(new_safe) + len(new_risky)}"]
    if git_err:
        L.append(f"- ⚠️ git scan unavailable: {git_err} — commits skipped, nothing invented")
    L.append("")
    if not new_safe and not new_risky:
        L += ["## ✅ All clear",
              "No new commits or markers since the last checkpoint. The spine",
              "remembered everything already reported. (No spine, no loop.)"]
    else:
        if new_safe:
            L += ["## New items", "", "| Type | Location | What |", "| :--- | :--- | :--- |"]
            L += [f"| {i['type']} | `{i['loc']}` | {i['text'][:100]} |" for i in new_safe]
            L.append("")
        if new_risky:
            L.append("## 🚫 Needs a human (halted, not acted on)")
            L += [f"- `{i['loc']}` — {i['text'][:70]} — **{i['reason']}**" for i in new_risky]
            L.append("")
    L += ["---",
          "*Every item traces to a real commit or file:line in this repo. If the "
          "scan failed, this brief says so rather than inventing items.*"]
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return os.path.relpath(path, REPO).replace("\\", "/")


def run_beat():
    now = datetime.now(timezone.utc)
    state = read_spine()                                    # 1. READ THE SPINE
    beat = len(state["checkpoints"]) + 1
    items, git_err = scan_repo()                            # 2. DO THE WORK
    new = [i for i in items if i["sig"] not in state["seen"]]
    new_safe = [i for i in new if not i["risky"]]
    new_risky = [i for i in new if i["risky"]]
    brief = write_brief(beat, now, len(items), len(state["seen"]), new_safe, new_risky, git_err)
    for i in new_safe:                                      # 3. WRITE THE SPINE
        state["done"].append(f"- [sig:{i['sig']}] {i['type']} {i['loc']} — {i['text'][:80]}")
    for i in new_risky:
        state["open"].append(f"- [sig:{i['sig']}] {i['type']} {i['loc']} — {i['text'][:50]} "
                             f"| reason: {i['reason']} | action: human review required")
    status = "NEEDS_HUMAN" if new_risky else "SUCCESS"
    state["checkpoints"].append(
        f"- {now.strftime('%Y-%m-%dT%H:%M:%SZ')} | beat {beat} | new: {len(new_safe)} "
        f"| escalated: {len(new_risky)} | status: {status}")
    write_spine(state)
    print(f"  beat {beat}: scanned {len(items)}, {len(state['seen'])} known, "
          f"{len(new_safe)} new, {len(new_risky)} escalated -> {status}")
    print(f"  brief:  {brief}")
    print("  spine:  progress.md updated (read first, written last)")
    if not new:
        print("  all clear — nothing new since last checkpoint (the spine remembered).")
    return 0


def show_status():
    if not os.path.exists(SPINE):
        print("  no spine yet — run:  python3 .claude/skills/morning-brief/scripts/brief.py --run")
        return 0
    state = read_spine()
    print(f"  spine: progress.md — {len(state['seen'])} items remembered, "
          f"{len(state['checkpoints'])} beats, {len(state['open'])} open for a human")
    if state["checkpoints"]:
        print("  last:  " + state["checkpoints"][-1][2:])
    return 0


def main():
    p = argparse.ArgumentParser(description="Morning brief with a spine (memory between runs).")
    p.add_argument("--run", action="store_true", help="run one beat (scan, write brief, update spine)")
    p.add_argument("--status", action="store_true", help="show the current memory, no beat")
    args = p.parse_args()
    if args.status:
        return show_status()
    if args.run:
        return run_beat()
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())



