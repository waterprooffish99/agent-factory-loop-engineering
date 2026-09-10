#!/usr/bin/env bash
# fix-loop-body.sh — Codified maker-checker body for parallel fix candidates.
# This is an ENGINE: one command fans candidates out, checks them, and stops.
# It has NO heartbeat and writes NO persistent state between runs.
# Usage: ./fix-loop-body.sh <candidates.json>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CANDIDATES_FILE="${1:?Usage: $0 <candidates.json>}"
CHECKER="$SCRIPT_DIR/candidate-checks.py"

if [ ! -f "$CANDIDATES_FILE" ]; then
    echo "Error: $CANDIDATES_FILE not found"
    exit 1
fi

if [ ! -f "$CHECKER" ]; then
    echo "Error: executable checker $CHECKER not found"
    exit 1
fi

# Parse candidates with Python so the engine has no jq dependency.
readarray -t CANDIDATES < <(python3 -c '
import json, sys
with open(sys.argv[1]) as stream:
    for item in json.load(stream):
        print(json.dumps(item))
' "$CANDIDATES_FILE")

TOTAL=${#CANDIDATES[@]}
if [ "$TOTAL" -eq 0 ]; then
    echo "No candidates in $CANDIDATES_FILE"
    exit 0
fi

json_field() {
    python3 -c 'import json, sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$1" "$2"
}

IMPL_SKILL=$(<"$SCRIPT_DIR/.claude/skills/fix-impl/SKILL.md")
REVIEW_SKILL=$(<"$SCRIPT_DIR/.claude/skills/fix-review/SKILL.md")
RUN_ID="$(date +%s)-$$"
RESULTS_DIR=$(mktemp -d)
trap 'rm -rf -- "$RESULTS_DIR"' EXIT

PIDS=()
BRANCHES=()
WORKTREES=()
PURPOSES=()

echo "=== Fix Loop Body: $TOTAL candidates ==="
echo "Run: $RUN_ID"
echo "Launching candidates in parallel..."

for i in "${!CANDIDATES[@]}"; do
    CANDIDATE="${CANDIDATES[$i]}"
    ID=$(json_field "$CANDIDATE" id)
    PURPOSE=$(json_field "$CANDIDATE" purpose)
    FILE=$(json_field "$CANDIDATE" file)
    BUG=$(json_field "$CANDIDATE" bug)
    CHECK=$(json_field "$CANDIDATE" check)
    IMPLEMENTATION=$(json_field "$CANDIDATE" implementation)
    BRANCH="p5-$RUN_ID-$ID"
    WORKTREE_DIR="../worktree-$BRANCH"

    BRANCHES[$i]="$BRANCH"
    WORKTREES[$i]="$WORKTREE_DIR"
    PURPOSES[$i]="$PURPOSE"

    (
        RESULT_FILE="$RESULTS_DIR/$i.report"
        STATUS_FILE="$RESULTS_DIR/$i.status"

        cleanup_candidate() {
            cd "$SCRIPT_DIR"
            git worktree remove -f "$WORKTREE_DIR" >/dev/null 2>&1 || true
            git branch -D "$BRANCH" >/dev/null 2>&1 || true
        }
        trap cleanup_candidate EXIT

        if ! git worktree add "$WORKTREE_DIR" -b "$BRANCH" main >/dev/null 2>&1; then
            {
                echo "Candidate $ID — $PURPOSE"
                echo "Worktree creation: FAIL"
                echo "Verdict: FAIL"
                echo "Verdict exit code: 1"
            } > "$RESULT_FILE"
            echo "FAIL" > "$STATUS_FILE"
            exit 1
        fi

        cd "$WORKTREE_DIR"
        ISOLATED_ROOT=$(git rev-parse --show-toplevel)

        IMPL_PROMPT="$IMPL_SKILL

File: $FILE
Real bug: $BUG
Candidate implementation instruction: $IMPLEMENTATION

Apply the candidate instruction now. Read the actual file and use the Edit tool."

        set +e
        IMPL_RAW=$(printf '%s\n' "$IMPL_PROMPT" | opencode run --auto --format json 2>&1)
        IMPL_PROCESS_EXIT=$?
        set -e

        DIFF=$(git diff --no-ext-diff -- "$FILE" || true)
        if [ -z "$DIFF" ]; then
            {
                echo "Candidate $ID — $PURPOSE"
                echo "Isolated worktree: YES ($ISOLATED_ROOT, branch $BRANCH)"
                echo "Implementer process exit: $IMPL_PROCESS_EXIT"
                echo "Implementer change: NONE"
                echo "Objective checks: NOT RUN"
                echo "Reviewer verdict: NOT RUN"
                echo "Verdict: FAIL"
                echo "Verdict exit code: 1"
            } > "$RESULT_FILE"
            echo "FAIL" > "$STATUS_FILE"
            exit 1
        fi

        set +e
        CHECK_OUTPUT=$(python3 "$CHECKER" verify "$CHECK" "$FILE" 2>&1)
        CHECK_EXIT=$?
        set -e

        REVIEW_COMMAND="python3 $CHECKER verify $CHECK $FILE"
        REVIEW_PROMPT="$REVIEW_SKILL

File: $FILE
Real bug: $BUG
Candidate purpose: $PURPOSE
Candidate implementation instruction: $IMPLEMENTATION

Actual diff:
$DIFF

Deterministic checker command:
$REVIEW_COMMAND

First checker run (exit $CHECK_EXIT):
$CHECK_OUTPUT

Read the ACTUAL resulting file, inspect scope and regression risk, and run the
checker command yourself. Do not trust the implementer or its explanation.
The executable check result is authoritative: a failing check requires FAIL.

Your response must contain exactly one standalone verdict line, PASS or FAIL,
followed by a concise explanation."

        set +e
        REVIEW_RAW=$(printf '%s\n' "$REVIEW_PROMPT" | opencode run --auto --format json 2>&1)
        REVIEW_PROCESS_EXIT=$?
        set -e

        REVIEW_TEXT=$(printf '%s\n' "$REVIEW_RAW" | python3 "$CHECKER" review-text)
        REVIEW_VERDICT=$(printf '%s\n' "$REVIEW_RAW" | python3 "$CHECKER" review-verdict)

        FINAL_VERDICT="FAIL"
        VERDICT_EXIT=1
        if [ "$IMPL_PROCESS_EXIT" -eq 0 ] \
            && [ "$CHECK_EXIT" -eq 0 ] \
            && [ "$REVIEW_PROCESS_EXIT" -eq 0 ] \
            && [ "$REVIEW_VERDICT" = "PASS" ]; then
            FINAL_VERDICT="PASS"
            VERDICT_EXIT=0
        fi

        {
            echo "Candidate $ID — $PURPOSE"
            echo "Isolated worktree: YES ($ISOLATED_ROOT, branch $BRANCH)"
            echo "Implementer process exit: $IMPL_PROCESS_EXIT"
            echo "Implementer change:"
            printf '%s\n' "$DIFF"
            echo "Objective checks (exit $CHECK_EXIT):"
            printf '%s\n' "$CHECK_OUTPUT"
            echo "Reviewer process exit: $REVIEW_PROCESS_EXIT"
            echo "Reviewer response:"
            if [ -n "$REVIEW_TEXT" ]; then
                printf '%s\n' "$REVIEW_TEXT"
            else
                echo "No parseable reviewer text"
            fi
            echo "Reviewer verdict: $REVIEW_VERDICT"
            echo "Verdict: $FINAL_VERDICT"
            echo "Verdict exit code: $VERDICT_EXIT"
        } > "$RESULT_FILE"
        echo "$FINAL_VERDICT" > "$STATUS_FILE"
        exit "$VERDICT_EXIT"
    ) &

    PIDS[$i]=$!
done

# Synchronization barrier: no summary is printed until every candidate finishes.
for i in "${!PIDS[@]}"; do
    wait "${PIDS[$i]}" || true
done

PASS_COUNT=0
FAIL_COUNT=0

echo
echo "=== Candidate Evidence ==="
for i in "${!CANDIDATES[@]}"; do
    if [ -f "$RESULTS_DIR/$i.report" ]; then
        cat "$RESULTS_DIR/$i.report"
    else
        echo "Candidate $i — ${PURPOSES[$i]}"
        echo "Result capture: FAIL (worker exited before writing evidence)"
        echo "Verdict: FAIL"
        echo "Verdict exit code: 1"
        echo "FAIL" > "$RESULTS_DIR/$i.status"
    fi

    CLEANED="YES"
    if [ -e "${WORKTREES[$i]}" ] || git show-ref --verify --quiet "refs/heads/${BRANCHES[$i]}"; then
        CLEANED="NO"
    fi
    echo "Cleanup: $CLEANED (worktree and temporary branch removed)"

    STATUS=$(<"$RESULTS_DIR/$i.status")
    if [ "$STATUS" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo
done

echo "=== Summary: $PASS_COUNT PASS, $FAIL_COUNT FAIL ==="
echo "This ENGINE has parallel fan-out, isolated worktrees, an implementer, an"
echo "independent reviewer, executable checks, verdict exit codes, wait, and cleanup."
echo "It has NO heartbeat and NO persistent state, so it is NOT yet a loop."

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
