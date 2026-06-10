---
name: drift
description: DREAM 4-phase consolidation pass (Orient / Gather / Consolidate / Prune) over trace/, FINDINGS.md, experiments/agenda.md and sessions/, plus a retraction-citation sweep that flags orphan figures, claims whose dependency was RETRACTED, stale conclusions, and overdue RIGOR_DEBT markers. Returns a ## DriftReport block.
whenToUse: Invoked when the user wants a fresh consolidation of the harness's research state — typically after a batch of /execute or /analyze runs, before writing a /paper or /brief, after a confound-audit retraction, or when FINDINGS.md / experiments/agenda.md feels stale or over cap. Triggered by "/drift", "consolidate state", "what's drifted", "sweep for retractions". Do NOT auto-fire from a Stop hook.
isEnabled: test -d trace
---

# /drift

## Static

### Summary
Four phases — Orient, Gather, Consolidate, Prune — over `trace/` (append-only provenance), `FINDINGS.md` (the capped one-line-pointer index), `experiments/agenda.md`, and `sessions/` (episodic narratives + `metrics-*.jsonl`). On top of the order-66 consolidation pass, `/drift` runs a research-specific **retraction-citation sweep**: it walks the confound-contamination graph from every claim self-retracted by a failed confound-audit (RULE-6) and flags downstream claims, orphan figures, stale conclusions, and any `RIGOR_DEBT(due:)` marker past its 7-day SLA. It is a *consolidation* pass, not a fix-it pass — but it DOES delete contradicted findings at their source. Returns a `## DriftReport` block.

### Preconditions
- `trace/` exists at the project root (gated by `isEnabled: test -d trace`).
- `trace/` contains at least one entry. If `trace/` is empty: refuse with `"No trace entries. Run /execute at least once first."` — there is nothing to consolidate yet.
- `FINDINGS.md` and `experiments/agenda.md` may or may not exist yet; if absent, treat as empty (create on first consolidation, do not error).

### Parameters
- (none) — operates over the whole project under study (`${CLAUDE_PROJECT_DIR}`). Does not take an experiment argument; the sweep is global because a retraction in one experiment can contaminate citations in another.

### Output format
A `## DriftReport` RETURN FORMAT block (CONVENTIONS.md §4). The heading and every `- <Field>:` line are mechanical — they MUST match `hooks/block-schemas.tsv` verbatim or `block-lint.sh` rejects the block. Emit it ALWAYS, even when nothing changed.

```
## DriftReport
- Scanned: <N trace files> / <N experiments> / <N session logs> / <N metrics-*.jsonl> (window: <since-date> .. 2026-05-30)
- Consolidated: <count> finding(s) merged or rewritten; <count> relative→absolute date conversions; <count> contradicted finding(s) deleted at source
- Retractions: <count> RETRACTED claim(s); <list of downstream C-NNN / EXP-<slug> contaminated via confound-contamination graph>; <count> orphan figure(s); <count> stale conclusion(s)
- Rigor-debt-overdue: <count> RIGOR_DEBT(due:) marker(s) past 7-day SLA; <list: file:line — due:YYYY-MM-DD — N days overdue>
- Pruned: <list of files truncated and reason: line cap (200) | byte cap (25KB) | superseded pointer removed>; or "none — caps under threshold"
```

Side effects (the only writes `/drift` is allowed to make):
- Updates `trace/<exp>.md` files with consolidated provenance state and RETRACTED markers.
- Updates `FINDINGS.md` (≤200 lines, ≤25 KB; §7) — one-line pointers only.
- Updates `experiments/agenda.md` (≤200 lines, ≤25 KB; §7) — re-orders / prunes the live agenda.
- Annotates contaminated claims in `trace/` and `FINDINGS.md`; deletes contradicted finding lines at source.

### Hard constraints
- **No write outside `trace/`, `FINDINGS.md`, `experiments/agenda.md`, `sessions/`.** `/drift` consolidates and prunes; it never edits `experiments/<exp>/runs/`, never re-runs analysis, never issues a `## Verdict`. Retraction is recorded, not re-litigated.
- **Never self-grade (RULE-1).** `/drift` does NOT decide whether a claim survives a confound-audit — it only *propagates* a retraction that `results-verifier` / `/confound-audit` already recorded (`Survives: NO`). It reads the verdict; it does not author one.
- **Cap enforcement (§7).** Phase 4 truncates `FINDINGS.md` and `experiments/agenda.md` at 200 lines OR 25 KB, whichever hits first, **at a newline boundary** (never mid-line). State the file and the triggering cap in `Pruned`. These are one-line-pointer indexes, not content dumps.
- **Convert relative → absolute dates.** "yesterday" / "last week" / "recently" in any consolidated entry becomes an ISO-8601 absolute date (CONVENTIONS.md §1). Resolve against the run's `date -Iseconds` provenance line in `trace/`, not against the read time.
- **Delete contradicted findings at the source.** If today's sweep shows a `FINDINGS.md` / `trace/` line is disproved (e.g. its underlying claim was RETRACTED, or a newer run reversed its sign), fix it where it lives — do not leave a stale line with a "but see…" addendum.
- **RIGOR_DEBT 7-day SLA.** A `RIGOR_DEBT(due:YYYY-MM-DD):` marker whose `due` date is strictly before today (2026-05-30) is *overdue* and MUST appear in `Rigor-debt-overdue` with its file:line and days-overdue count. `/drift` flags it; it does not silently clear or extend it.
- **Tiers nest; never over-impose (CONVENTIONS.md §2).** The sweep applies the same checks at every tier — orphan figures and overdue debt are surfaced regardless — but does NOT manufacture confirmatory/publication obligations (CI method, FDR, datasheet) against an `exploratory` experiment. A missing/unknown `rigor_tier` defaults to `publication` and is itself surfaced as a finding (RULE-0).
- **Narrow-grep only; never `cat` a whole run log.** Keep context lean (Common mistake #1). Grep `metrics-*.jsonl` and session narratives for specific tokens; delegate any actual run-log reading to the `run-reader` agent.
- **No absolute paths (RULE-2).** Everything is relative to `${CLAUDE_PROJECT_DIR}`; template reads resolve via `${CLAUDE_PLUGIN_ROOT}`.

### Common mistakes (avoid)
1. **`cat`-ing whole `metrics-*.jsonl` or session transcripts.** They are large and blow the context budget that GPU-expensive work cannot afford to waste. Phase 2 greps narrowly (`grep -rn "<token>" sessions/ --include="*.md" | tail -50`) for terms you *already suspect matter*. To read a run's actual log, spawn `run-reader`, never inline it.
2. **Treating a retraction as a local edit.** When a claim's confound-audit recorded `Survives: NO`, the contamination flows *down* the dependency graph. You must walk `_Depends:_` edges from the retracted claim to every claim/figure that consumed it and flag them too — a one-line "RETRACTED" on the source alone leaves orphaned downstream conclusions standing.
3. **Adding to `FINDINGS.md` without pruning.** Phase 4 is BOTH addition and pruning. If the index is over 200 lines / 25 KB after merges, you must remove superseded pointers in the same pass. Truncating mid-line corrupts a pointer — always cut at a newline.
4. **Clearing or extending an overdue `RIGOR_DEBT(due:)` marker.** `/drift` reports the SLA breach; it has no authority to mark the debt paid (that is the owning skill's job on the next real run). Editing the `due:` date to hide the breach is forbidden.
5. **Over-imposing the top tier (RULE-0 inverted).** Flagging an `exploratory` experiment for a missing FDR correction or datasheet re-creates exactly the bloat the tier system exists to prevent. Apply only the checks the experiment's declared tier earns. (But a *missing* tier is itself the finding — default to `publication` and say so.)
6. **Emitting a partial `## DriftReport`.** All five fields (`Scanned`, `Consolidated`, `Retractions`, `Rigor-debt-overdue`, `Pruned`) are mechanical and required by the schema. Even a clean sweep emits all five — write "none" / "0", never drop the line.

## Dynamic

Template reads: this skill needs no template files. The state-tier contract and caps live in `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` (§7); the interpretation laws cited below live in `${CLAUDE_PLUGIN_ROOT}/templates/research-rulebook.md`.

What already exists (do NOT re-check): `trace/` exists (guaranteed by `isEnabled`). Read it directly — no `ls`/`mkdir` guard needed. `update-trace.sh` keeps `trace/<exp>.md` append-only and canonicalizes hyphen/underscore drift, so a single experiment maps to one trace file — trust that mapping; do not re-normalize names.

Orientation snapshot (cheap, bounded — read these, do not expand):

- experiments present: !{ls -1 ${CLAUDE_PROJECT_DIR}/experiments 2>/dev/null | grep -v '\.md$' | head -40}
- trace files: !{ls -1 ${CLAUDE_PROJECT_DIR}/trace 2>/dev/null | head -40}
- FINDINGS.md size: !{wc -l ${CLAUDE_PROJECT_DIR}/FINDINGS.md 2>/dev/null | awk '{print $1" lines"}'; wc -c ${CLAUDE_PROJECT_DIR}/FINDINGS.md 2>/dev/null | awk '{print $1" bytes (cap 25600)"}'}
- agenda.md size: !{wc -l ${CLAUDE_PROJECT_DIR}/experiments/agenda.md 2>/dev/null | awk '{print $1" lines"}'; wc -c ${CLAUDE_PROJECT_DIR}/experiments/agenda.md 2>/dev/null | awk '{print $1" bytes (cap 25600)"}'}
- last drift marker (consolidation window start): !{grep -h "drift consolidated" ${CLAUDE_PROJECT_DIR}/trace/*.md 2>/dev/null | tail -1 || echo "no prior drift — use last 50 trace lines as window"}
- RETRACTED claims (retraction-sweep seeds): !{grep -rn "Survives: NO\|RETRACTED" ${CLAUDE_PROJECT_DIR}/trace ${CLAUDE_PROJECT_DIR}/experiments 2>/dev/null --include="*.md" | head -40}
- overdue rigor-debt candidates (raw — you must compare each due: against 2026-05-30): !{grep -rn "RIGOR_DEBT(due:" ${CLAUDE_PROJECT_DIR} 2>/dev/null --include="*.md" --include="*.py" --include="*.json" | head -60}

— DREAM 4-PHASE PROMPT (retargeted from order-66 `/drift`: "research claims/findings" for "spec compliance," "verifier verdicts + confound-audits since last run" for "PRs/tests," "trace/ + FINDINGS.md" for "trace/ + MEMORY.md," with the retraction-citation sweep added) —

You are performing a drift pass — a reflective sweep over the harness's research state. Synthesize what has changed recently into durable, well-organized trace and index entries so future sessions orient quickly, and propagate any retraction through every claim that depended on it.

State tiers (CONVENTIONS.md §7): `trace/` (mechanical, append-only) → `FINDINGS.md` (capped one-line-pointer index) → `sessions/` (episodic narratives + `metrics-*.jsonl`). You consolidate *up* this chain and prune the index.

---

### Phase 1 — Orient

- Read `FINDINGS.md` to understand the current index and `experiments/agenda.md` for the live agenda. (If either is absent, it is empty — you may create it during Phase 4.)
- Read the orientation snapshot above (experiments, trace files, cap sizes, RETRACTED seeds, overdue-debt candidates). Do not re-`ls`.
- For each experiment with recent activity, skim its `experiments/<exp>/experiment.json` for the `rigor_tier` (a missing/unknown tier is a finding — RULE-0, default `publication`).
- If `sessions/` has recent entries, review the last 1–2 episodic narratives — narratives, not the `metrics-*.jsonl`.

### Phase 2 — Gather recent signal

Look for new research state worth persisting, in rough priority order. Grep narrowly; do not exhaustively read.

1. **Verifier verdicts since last drift** — grep `sessions/` and `trace/` for `## Verdict`, `RERUN`, `REJECT`, `BLOCKED`, `PROMOTE`. Which claims (`C-NNN`) and experiments (`EXP-<slug>`) were affected?
2. **Confound-audit retractions (RULE-6)** — every `## ConfoundAudit` with `Survives: NO` self-retracts its claim. These are the seeds of the retraction sweep (Phase 3).
3. **Metric movement** — narrow-grep `metrics-*.jsonl` for the *primary metric key only* (e.g. `grep -h '"balanced_acc"' sessions/metrics-*.jsonl | tail -20`). Never `cat` a full jsonl; if you need a run's full log, spawn `run-reader`.
4. **Trace lines that drifted** — a claim in `trace/` whose underlying run was superseded, reversed, or RETRACTED.
5. **Targeted narrative search** — for a specific question: `grep -rn "<C-NNN or token>" sessions/ --include="*.md" | tail -50`.

### Phase 3 — Consolidate (incl. the retraction-citation sweep)

For each thing worth remembering, write or update a `trace/<exp>.md` line or a `FINDINGS.md` pointer. Merge into existing entries rather than creating near-duplicates. Use this project's `RESEARCH_RULEBOOK.md` / `CLAUDE.md` conventions as the source of truth for formats and IDs.

Standard consolidation:
- Merge new signal into the existing trace file for that experiment (one canonical file per experiment — trust the hook's normalization).
- Convert every relative date to an absolute ISO-8601 date so it stays interpretable.
- Delete contradicted findings at the source — do not annotate-around them.

Retraction-citation sweep (the research-specific addition):
- **Seed set** = every claim with a recorded `Survives: NO` (RULE-6 self-retraction) plus any line already marked `RETRACTED`.
- **Walk the confound-contamination graph.** From each seed, follow `_Depends:_` edges *forward* to every claim, conclusion, and figure that consumed it. Mark each contaminated downstream claim `RETRACTED (contaminated via C-NNN)` at its source in `trace/` and remove its pointer from `FINDINGS.md`.
- **Orphan figures** — a figure asset referenced by no surviving claim (its claim was RETRACTED or deleted): flag it. Do not delete the asset; record the orphan so `/paper` does not cite it.
- **Stale conclusions** — a conclusion line whose every supporting claim is now RETRACTED or superseded: delete at source and count it.
- **Overdue rigor-debt** — for each `RIGOR_DEBT(due:YYYY-MM-DD):` candidate from the snapshot, compare `due:` against today (2026-05-30). If `due:` is strictly earlier, it is overdue — record file:line, the due date, and days overdue. Flag only; never edit the marker.

### Phase 4 — Prune and index

Keep `FINDINGS.md` and `experiments/agenda.md` under **200 lines AND 25 KB** (§7). They are INDEXES, not dumps. Each entry is one line under ~150 chars: `- [Title](trace/<exp>.md) — one-line hook`. Never write content directly into them.

- Remove pointers to claims/sessions now stale, RETRACTED, contaminated, or superseded.
- Demote verbose lines: a line over ~200 chars is carrying content that belongs in the trace file — shorten the pointer, move the detail.
- Add pointers to newly important findings.
- Resolve contradictions; reconcile the agenda ordering with what actually ran.
- If still over cap after merges, truncate at a **newline boundary** and name the file + triggering cap (line vs byte) in the report.

---

Return a `## DriftReport` block summarizing what was scanned, consolidated, retracted/contaminated, found overdue, and pruned. Emit all five fields even on a clean sweep (use "none" / "0"); if nothing changed at all, say so explicitly in `Consolidated` and `Pruned`.

```
## DriftReport
- Scanned: <N trace> / <N experiments> / <N session logs> / <N metrics-*.jsonl> (window: <since-date> .. 2026-05-30)
- Consolidated: <count> merged/rewritten; <count> date conversions; <count> contradicted finding(s) deleted at source
- Retractions: <count> RETRACTED; downstream contaminated: <C-NNN list / "none">; orphan figures: <count>; stale conclusions: <count>
- Rigor-debt-overdue: <count> past 7-day SLA — <file:line — due:YYYY-MM-DD — N days overdue; ...> | "none"
- Pruned: <file — line cap (200) | byte cap (25KB) | superseded pointer removed; ...> | "none — caps under threshold"
```
