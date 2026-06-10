#!/usr/bin/env bash
# block-lint.sh — validate the named ## Block ABI (CONVENTIONS.md §4) in a markdown file.
#
# Dual-use:
#   • PostToolUse(Edit|Write|MultiEdit) hook → reads hook JSON on stdin, emits an advisory
#     additionalContext message (never blocks; D-007 makes this advisory at write-time).
#   • Direct precondition:  bash block-lint.sh <file.md>  → prints a ## BlockLint report and
#     exits 1 if any block is malformed. /execute calls this as a HARD precondition before a
#     run consumes an upstream block, so a silent field-drift can't waste a GPU run.
#
# Required fields per block live in hooks/block-schemas.tsv. Plugin discipline: no jq, no abs paths.

set -uo pipefail

HOOK_MODE=0
FILE_PATH="${1:-}"
if [[ -z "$FILE_PATH" ]]; then
  HOOK_MODE=1
  INPUT="$(cat)"
  FILE_PATH=$(printf '%s' "$INPUT" | grep -o '"file_path"[^,}]*' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

# In hook mode, only lint markdown experiment artifacts (reduce noise).
if [[ "$HOOK_MODE" -eq 1 ]]; then
  case "$FILE_PATH" in
    */experiments/*.md|*/results/*.md|*/trace/*.md) ;;
    *) printf '{}\n'; exit 0 ;;
  esac
fi

if [[ ! -f "$FILE_PATH" ]]; then
  [[ "$HOOK_MODE" -eq 1 ]] && printf '{}\n' || echo "block-lint: no such file: $FILE_PATH"
  exit 0
fi

SCHEMA="${CLAUDE_PLUGIN_ROOT:-.}/hooks/block-schemas.tsv"
if [[ ! -f "$SCHEMA" ]]; then
  [[ "$HOOK_MODE" -eq 1 ]] && printf '{}\n' || echo "block-lint: schema not found: $SCHEMA"
  exit 0
fi

PROBLEMS=""
CHECKED=0

# Columns split on first whitespace run: BLOCK (no spaces) then FIELDS (comma list).
while read -r BLOCK FIELDS; do
  [[ -z "${BLOCK:-}" || "${BLOCK:0:1}" == "#" ]] && continue
  grep -q "^## ${BLOCK}\$" "$FILE_PATH" || continue
  CHECKED=$((CHECKED + 1))

  # Section = lines after "## <BLOCK>" up to the next "## " heading or EOF.
  SECTION=$(awk -v b="## ${BLOCK}" '
    $0==b {f=1; next}
    f && /^## / {exit}
    f {print}
  ' "$FILE_PATH")

  IFS=',' read -ra REQ <<< "$FIELDS"
  for tok in "${REQ[@]}"; do
    # A field token may carry a value constraint: name=nonblank | name=enum:A|B|C
    fname="${tok%%=*}"
    constraint=""
    [[ "$tok" == *"="* ]] && constraint="${tok#*=}"

    fline=$(printf '%s\n' "$SECTION" | grep -m1 -E "^[[:space:]]*[-*]?[[:space:]]*${fname}:")
    if [[ -z "$fline" ]]; then
      PROBLEMS="${PROBLEMS}\n  - ${BLOCK}: missing required field '${fname}:'"
      continue
    fi
    [[ -z "$constraint" ]] && continue

    # Value = text after the first "name:" occurrence, trimmed.
    val=$(printf '%s' "$fline" | sed -E "s/^[[:space:]]*[-*]?[[:space:]]*${fname}:[[:space:]]*//; s/[[:space:]]+$//")
    case "$constraint" in
      nonblank)
        if [[ -z "$val" || "$val" == "<"*">" ]]; then
          PROBLEMS="${PROBLEMS}\n  - ${BLOCK}.${fname}: value must be non-blank (gate field; RULE-10)"
        fi
        ;;
      enum:*)
        allowed="${constraint#enum:}"
        first=$(printf '%s' "$val" | awk '{print $1}')
        ok=0
        IFS='|' read -ra OPTS <<< "$allowed"
        for o in "${OPTS[@]}"; do [[ "$first" == "$o" ]] && ok=1; done
        if [[ "$ok" -ne 1 ]]; then
          PROBLEMS="${PROBLEMS}\n  - ${BLOCK}.${fname}: value '${first}' not in {${allowed//|/, }}"
        fi
        ;;
    esac
  done
done < "$SCHEMA"

if [[ -z "$PROBLEMS" ]]; then
  if [[ "$HOOK_MODE" -eq 1 ]]; then
    if [[ "$CHECKED" -gt 0 ]]; then
      printf '{"additionalContext": "block-lint: %s ## Block(s) in %s conform to the ABI."}\n' \
        "$CHECKED" "$FILE_PATH"
    else
      printf '{}\n'
    fi
  else
    printf '## BlockLint\nPASS (%s block(s) checked)\n' "$CHECKED"
  fi
  exit 0
fi

MSG="block-lint: ## Block ABI violations in ${FILE_PATH}:${PROBLEMS}"
if [[ "$HOOK_MODE" -eq 1 ]]; then
  ESC=$(printf '%b' "$MSG" | sed ':a;N;$!ba;s/\\/\\\\/g;s/\n/\\n/g;s/"/\\"/g')
  printf '{"additionalContext": "%s"}\n' "$ESC"
  exit 0
else
  printf '## BlockLint\nFAIL\n'
  printf '%b\n' "$PROBLEMS"
  exit 1
fi
