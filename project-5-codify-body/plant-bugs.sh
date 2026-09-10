#!/usr/bin/env bash
# plant-bugs.sh — Plant all bugs from candidates.json into utils.py

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 -c "
import re
p = 'utils.py'
with open(p) as f:
    src = f.read()

# Bug 1: off-by-one in rolling_average (line 15)
src = src.replace(
    'for i in range(len(values) - window + 1):',
    'for i in range(len(values) - window):'
)

# Bug 2: find_duplicates - change to use set which loses order (lines 22-29)
old_find = '''def find_duplicates(items):
    \"\"\"Return a list of items that appear more than once, preserving first-occurrence order.\"\"\"
    seen = set()
    duplicates = []
    for item in items:
        if item in seen:
            duplicates.append(item)
        seen.add(item)
    return duplicates'''

new_find = '''def find_duplicates(items):
    \"\"\"Return a list of items that appear more than once, preserving first-occurrence order.\"\"\"
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)'''

src = src.replace(old_find, new_find)

# Bug 3: clamp - swap max/min arguments (lines 32-34)
old_clamp = '''def clamp(value, low, high):
    \"\"\"Clamp \`value\` between \`low\` and \`high\` inclusive.\"\"\"
    return max(low, min(value, high))'''

new_clamp = '''def clamp(value, low, high):
    \"\"\"Clamp \`value\` between \`low\` and \`high\` inclusive.\"\"\"
    return min(low, max(value, high))'''

src = src.replace(old_clamp, new_clamp)

with open(p, 'w') as f:
    f.write(src)
print('All bugs planted in utils.py')
"