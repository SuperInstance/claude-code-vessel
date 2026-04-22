#!/bin/bash
# Auto-update REBOOT-STATE.md on session end
# Usage: bash scripts/auto-reboot-state.sh "status" "last_task" "files_changed" "commits"

STATUS="${1:-paused}"
LAST_TASK="${2:-unknown}"
FILES="${3:-0}"
COMMITS="${4:-0}"

cat > REBOOT-STATE.md << EOF
# 🔄 Reboot State

Updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Status: $STATUS
Last task: $LAST_TASK
Files changed: $FILES
Commits this session: $COMMITS
Action: read CHARTER.md, check for-claude/ for next task, continue
EOF

echo "REBOOT-STATE.md updated"
