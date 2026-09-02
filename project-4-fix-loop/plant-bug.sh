#!/usr/bin/env bash
# plant-bug.sh — Introduce a deliberate off-by-one bug into utils.py
# This is the "bad code" that the fix-loop will fix (or fail to fix).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Plant off-by-one: range(len(values) - window) misses the last window position
python3 -c "
import re
p = 'utils.py'
with open(p) as f:
    src = f.read()

# Replace the correct loop range with the buggy one
src = src.replace(
    'for i in range(len(values) - window + 1):',
    'for i in range(len(values) - window):'
)

with open(p, 'w') as f:
    f.write(src)
print('Bug planted: rolling_average now misses the last window position')
"
