---
name: note
description: Append a timestamped research thought to sessions/notes-YYYY-MM-DD.md WITHOUT engaging with it, so an idea can be parked mid-sweep without derailing the active run. Emits NO ## Block (silent append). No argument dumps today's notes.
whenToUse: Triggered ONLY by explicit "/note" invocation. Never auto-triggered. Non-disruptive capture only — do not interpret, expand, answer, run, or act on the captured text. The whole point is that the researcher can queue a hypothesis, a confound to check, or a follow-up run idea while a GPU sweep or analysis is in flight, without you breaking the current task. Append and acknowledge in one line, then return to whatever you were doing.
---

# /note

## Static

### Summary
Append a single timestamped line to today's notes file at `sessions/notes-$(date -I).md`. The note is a scratchpad for the researcher to return to later (or for you to read on demand) — typically a hypothesis, a confound worth auditing, a "try this seed/dataset next" idea, or a question that surfaced mid-sweep. DO NOT answer, expand, paraphrase, classify, or act on the note's content. Capture only. The capture IS the whole job.

### Preconditions
- None on the experiment state — `/note` works whether or not any `experiments/<exp>/` exists, and whether or not a run is in flight. It deliberately reads nothing about the active experiment.
- The helper script `${CLAUDE_PLUGIN_ROOT}/skills/note/note.sh` exists and is executable; it creates `sessions/` (relative to `${CLAUDE_PROJECT_DIR}`, the current working dir) on first write. No other filesystem state is required or inspected.

### Parameters
- `text` — optional. The note content, free prose. Passed verbatim to the script as a single quoted argument. When absent, the skill runs in dump mode and prints today's notes file instead of appending.

### Output format
This skill emits **NO `## Block`** — it is a silent append, not a hand-off to another skill, so there is nothing in the `## Block` ABI (CONVENTIONS.md §4) for a consumer to grep. The entire response is the one line the script prints on stdout:

```
## n/a

noted → sessions/notes-2026-05-30.md
```

In dump mode (no `text`) the entire response is the raw file contents the script prints, or `(no notes for <date>)` if today's file does not exist yet. Do not wrap, summarise, or annotate that output.

### Hard constraints
- **Never engage with the note's content.** The reason `/note` exists is to NOT break the current task. A GPU run may be polling, an analysis may be half-written — capture, confirm, and return to exactly what you were doing. Engaging defeats the skill's only purpose.
- **Never ask clarifying questions about the note.** An ambiguous note is fine — it is a thought for later, not a request for action now.
- **Do not paraphrase, summarise, categorise, expand, or "tidy up" the note in your reply.** The single line of script output is the entire response.
- **Do not append follow-up promises** like "I'll address this next" or "noted, I'll get back to you after the run". The capture is the whole job; do not promise follow-up.
- **Do not edit, reorder, or deduplicate prior entries.** Append-only. Duplicates are the researcher's prerogative — a thought logged twice on different days is signal, not noise.
- **Never run, register, or schedule anything the note describes.** A note reading `re-run RUN-007 with seed 13 and a permutation null` is a parked idea, not a `/execute` or `/confound-audit` invocation. Treat it as inert text. (RULE-1 in spirit: the note is not a graded action, and you do not get to silently promote it into one.)
- **Plugin discipline (RULE-2).** The skill resolves the script via `${CLAUDE_PLUGIN_ROOT}` and writes under the project cwd (`${CLAUDE_PROJECT_DIR}`); the script contains no absolute paths. Do not hand-roll an `echo >> /abs/path` substitute.

### Common mistakes (avoid)
1. **Answering the note's question.** The researcher typed `/note does the spectral length-bias survive a per-question split, or is RUN-007 leaking via row-level CV?` precisely because they did NOT want you to drop the current run and investigate it now — they want it parked so they can come back to it after the sweep. Answering breaks the very thing the skill protects.
2. **Acknowledging with prose instead of running the script.** The one-line script output (`noted → sessions/notes-…`) IS the acknowledgement. Do not add a paragraph explaining what you captured or why.
3. **Treating dump mode as "now let's work through the notes".** When the researcher types `/note` with no argument, just print the file contents. Do not start triaging, registering, or executing the notes unless they explicitly ask.
4. **Silently acting on an actionable-sounding note.** A note that names a run, a confound, or a dataset is still just a note. Promoting it into a real `/execute`, `/register`, or `/confound-audit` call without an explicit instruction spends real GPU/$ budget on an un-vetted idea — exactly the derailment `/note` exists to prevent.
5. **Reformatting the timestamp or rotating the file yourself.** The script owns directory creation, ISO-8601 timestamping, and daily rotation. Do not pre-create `sessions/` or massage the date — pass the text through and let the script do its one job.

### When the researcher asks you to address the notes
Trigger phrases (and only these, or an explicit equivalent): "check notes", "what's in my notes", "address the notes", "go through my notes", "let's go through my notes", "open my notes". At that point — and only then — run the script in dump mode (no argument), then engage with each entry in order, treating each as a question or task to handle now (which may legitimately route into `/triage`, `/register`, `/execute`, etc.). Until the researcher explicitly asks, do not open the notes file.

## Dynamic

Templates: none — this skill needs no template files.

Append mode (the user supplied note text). Pass the researcher's full note as a single quoted argument; the script timestamps, rotates by date, creates `sessions/` if needed, and prints the one-line confirmation that is your entire reply:

!{bash ${CLAUDE_PLUGIN_ROOT}/skills/note/note.sh "<the researcher's note text>"}

Dump mode (no argument supplied). The script prints today's notes file contents, or `(no notes for <date>)` if it does not exist; that output is your entire reply — do not engage with the entries:

!{bash ${CLAUDE_PLUGIN_ROOT}/skills/note/note.sh}

`sessions/` is the harness convention for daily-rotated artifact files — it sits alongside the episodic narratives that `/drift` later consolidates (CONVENTIONS.md §7: `trace/` → `FINDINGS.md` → `sessions/`). Notes follow the same daily-rotation naming (`notes-YYYY-MM-DD.md`) so a week of parked ideas is easy to scroll through after the sweep finishes. The script already handles directory creation, ISO-8601 timestamping (`date -Iseconds`), per-day file rotation, and the confirmation message — do not re-implement any of that, and do not pre-check whether `sessions/` exists.
