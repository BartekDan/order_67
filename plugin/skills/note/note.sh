#!/usr/bin/env bash
# /note — append a timestamped line to sessions/notes-YYYY-MM-DD.md without engaging.
# No argument → print today's notes. Plugin discipline: no absolute paths (RULE-2).
set -uo pipefail

DAY="$(date -I)"
NOTE_FILE="sessions/notes-${DAY}.md"
mkdir -p sessions

TEXT="$*"
if [[ -z "$TEXT" ]]; then
  if [[ -f "$NOTE_FILE" ]]; then cat "$NOTE_FILE"; else echo "(no notes for ${DAY})"; fi
  exit 0
fi

[[ -f "$NOTE_FILE" ]] || printf '# Notes %s\n\n' "$DAY" > "$NOTE_FILE"
printf -- '- %s — %s\n' "$(date -Iseconds)" "$TEXT" >> "$NOTE_FILE"
echo "noted → ${NOTE_FILE}"
