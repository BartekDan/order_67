#!/usr/bin/env bash
# Stop hook for the order-67 research harness (M1). Logs session-stop only;
# auto-/drift consolidation is deferred (see ROADMAP "Deferred / open"). order-66's
# lesson: do NOT silently rely on a stub to keep state indexed — run /drift
# manually until auto-consolidation is proven, so missing consolidation is visible.
# Condition: test -d sessions. Plugin discipline: no absolute paths (RULE-2).

set -uo pipefail

# Anchor to the project root, NEVER the caller's cwd: hooks inherit the session shell's
# persisted cwd, which scattered stray sessions/ fragments around the tree when it drifted.
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
LOG="$ROOT/sessions/stop-events-$(date -I).log"
mkdir -p "$(dirname "$LOG")"
printf '%s session stopped (M1 logger; auto-/drift deferred — run /drift manually)\n' \
  "$(date -Iseconds)" >> "$LOG"

# No additionalContext to inject in M1. Empty JSON keeps the hook contract clean.
printf '{}\n'
