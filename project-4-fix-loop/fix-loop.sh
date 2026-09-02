#!/usr/bin/env bash
# fix-loop.sh — Orchestrator for the maker-checker loop.
#
# Flow: BUG → branch → implementer → diff → reviewer → PASS|FAIL
#
# Usage:
#   ./fix-loop.sh <file> "<bug description>"
#
# Example:
#   ./fix-loop.sh utils.py "rolling_average misses the last window due to off-by-one"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

FILE="${1:?Usage: $0 <file> \"<bug description>\"}"
BUG_DESC="${2:?Usage: $0 <file> \"<bug description>\"}"

echo "=== Fix Loop: Maker-Checker ==="
echo "File: $FILE"
echo "Bug:  $BUG_DESC"
echo ""

# ── Step 1: Create branch ─────────────────────────────────
BRANCH="fix/$(date +%s)"
git checkout -b "$BRANCH" 2>/dev/null
echo "[1/5] Created branch: $BRANCH"

# ── Step 2: Run implementer ────────────────────────────────
echo "[2/5] Running implementer..."

IMPL_PROMPT="You are a code fix implementer. Read the file $FILE. It contains a bug: $BUG_DESC. Fix the bug in the file. Do not change unrelated code. Write the fix using the Edit tool."

IMPL_OUTPUT=$(echo "$IMPL_PROMPT" | opencode run --format default 2>&1)
echo "$IMPL_OUTPUT" | tail -5
echo ""

# ── Step 3: Capture diff ──────────────────────────────────
DIFF=$(git diff "$FILE")
if [ -z "$DIFF" ]; then
    echo "[!] No changes detected. Implementer did not modify $FILE."
    git checkout main 2>/dev/null
    git branch -D "$BRANCH" 2>/dev/null
    exit 1
fi
echo "[3/5] Fix diff captured:"
echo "$DIFF" | head -30
echo ""

# ── Step 4: Run reviewer ──────────────────────────────────
echo "[4/5] Running reviewer..."

REVIEW_PROMPT="You are a strict code reviewer. You receive a file path and a diff of a proposed fix.

File: $FILE
Bug: $BUG_DESC

Diff:
$DIFF

Read the file $FILE to verify the fix in context.

Review criteria:
1. Correctness: Does the fix actually solve the described bug?
2. Safety: Does the fix introduce new bugs or break existing behavior?
3. Scope: Does the fix stay within the minimum necessary scope?

IMPORTANT: You MUST begin your response with exactly one of these words on a line by itself:
PASS
or
FAIL

If PASS, briefly explain why (1-3 sentences).
If FAIL, list what is wrong and what a correct fix would look like."

REVIEW_OUTPUT=$(echo "$REVIEW_PROMPT" | opencode run --format default 2>&1)
echo "$REVIEW_OUTPUT" | tail -10
echo ""

# ── Step 5: Parse verdict from stdout ─────────────────────
VERDICT=$(echo "$REVIEW_OUTPUT" | grep -oE '(^PASS|^FAIL)' | head -1 || true)

if [ -z "$VERDICT" ]; then
    echo "[!] Could not parse verdict from reviewer output."
    echo "    Reviewer output (last 20 lines):"
    echo "$REVIEW_OUTPUT" | tail -20
    git checkout main 2>/dev/null
    git branch -D "$BRANCH" 2>/dev/null
    exit 1
fi

echo "Review verdict: $VERDICT"
echo ""

if [ "$VERDICT" = "PASS" ]; then
    echo "[5/5] PASS — Committing fix..."
    git add "$FILE"
    git commit -m "fix: $BUG_DESC" --quiet

    if git remote -v | grep -q origin; then
        git push -u origin "$BRANCH" 2>&1 | tail -3
        if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
            PR_URL=$(gh pr create --title "fix: $BUG_DESC" --body "Automated fix via maker-checker loop.

Bug: $BUG_DESC
Branch: $BRANCH
Verdict: PASS" 2>&1)
            echo "PR: $PR_URL"
        else
            echo "(gh not authenticated — push branch manually and create PR on GitHub)"
        fi
    else
        echo "(no remote — push branch manually and create PR on GitHub)"
    fi
    echo ""
    echo "=== RESULT: PASS → Branch committed ==="
else
    echo "[5/5] FAIL — Fix rejected."
    echo ""
    echo "--- Review reasons ---"
    echo "$REVIEW_OUTPUT" | grep -A 50 '^FAIL'
    echo "--- End review ---"
    echo ""
    echo "=== RESULT: FAIL → No PR ==="
    git checkout main 2>/dev/null
    git branch -D "$BRANCH" 2>/dev/null
    exit 1
fi
