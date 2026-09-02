#!/usr/bin/env bash
# bad-fix.sh — Introduce a deliberately wrong fix into utils.py
# This is NOT a fix for the rolling_average bug. It changes unrelated code.
# The reviewer should reject this.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Bad "fix": clamp the window parameter instead of fixing the range
python3 -c "
p = 'utils.py'
with open(p) as f:
    src = f.read()

# This is NOT the right fix. The bug is in the range, not the window parameter.
# Adding a clamp to window does nothing for the off-by-one.
bad = '''
    if window > len(values):
        window = len(values)
'''

src = src.replace(
    '    result = []',
    bad + '    result = []'
)

with open(p, 'w') as f:
    f.write(src)
print('Bad fix applied: added unrelated window clamp (does NOT fix the off-by-one)')
"
