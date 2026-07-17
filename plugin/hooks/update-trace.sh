#!/usr/bin/env bash
# PostToolUse(Edit|Write|MultiEdit) handler for the order-67 research harness.
# Appends an append-only provenance line to trace/<exp>.md whenever a write
# touches an experiment artifact (experiments/<exp>/... or results/<exp>/...).
# Condition (test -d trace) is checked by Claude Code before invocation.
# Plugin discipline: no absolute paths (RULE-2); no jq dependency.
#
# Experiment-name normalization mirrors order-66's slice normalization: a write
# under results/<exp>/ or experiments/<exp>/ must log to ONE canonical trace file
# even if hyphen/underscore drift occurs, else provenance fragments into two files.

set -uo pipefail
INPUT="$(cat)"

TOOL_NAME=$(printf '%s' "$INPUT" | grep -o '"tool_name"[^,}]*' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
FILE_PATH=$(printf '%s' "$INPUT" | grep -o '"file_path"[^,}]*' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

case "$TOOL_NAME" in
  Edit|Write|MultiEdit) ;;
  *) printf '{}\n'; exit 0 ;;
esac

# Act only on experiment artifacts (experiments/ or results/).
DERIVED=""
case "$FILE_PATH" in
  */experiments/*) DERIVED=$(printf '%s' "$FILE_PATH" | sed -n 's|.*/experiments/\([^/]*\)/.*|\1|p') ;;
  */results/*)     DERIVED=$(printf '%s' "$FILE_PATH" | sed -n 's|.*/results/\([^/]*\)/.*|\1|p') ;;
  *) printf '{}\n'; exit 0 ;;
esac
[[ -z "$DERIVED" ]] && { printf '{}\n'; exit 0; }

# Normalize against experiments/ canonical dir to prevent hyphen/underscore drift.
HYPHENATED="${DERIVED//_/-}"
# Project root: env var (set for hooks) first; git toplevel guards a drifted-cwd fallback.
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
EXP_ROOT="$ROOT/experiments"
if [[ -d "${EXP_ROOT}/${DERIVED}" ]]; then
  EXP="$DERIVED"
elif [[ -d "${EXP_ROOT}/${HYPHENATED}" ]]; then
  EXP="$HYPHENATED"
else
  EXP="$HYPHENATED"
fi

TRACE_FILE="$ROOT/trace/${EXP}.md"
mkdir -p "$(dirname "$TRACE_FILE")"
printf '%s\n' "- $(date -Iseconds): ${TOOL_NAME} → ${FILE_PATH}" >> "$TRACE_FILE"

# additionalContext is surfaced as a system message in the next user turn.
printf '{"additionalContext": "trace updated for experiment %s (%s on %s)"}\n' \
  "$EXP" "$TOOL_NAME" "$FILE_PATH"
