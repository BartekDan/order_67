---
name: conflicts
description: Stateless cross-experiment INVARIANT scanner that runs before /execute commits a GPU run. Frontmatter-first reads of peer experiments/*/invariants.md and experiments/_global/invariants.md, plus a walk of the _Depends:_ retraction-cascade graph; emits a ## Conflicts block whose Verdict is CLEAR or BLOCKER. SKIPPED at exploratory tier. Direct analog of order-66 /contradict (RR-015).
whenToUse: Invoke when a user asks to "scan for cross-experiment conflicts", "run /conflicts <exp>", "check invariants before this run", "is anything I depend on retracted?", or when /execute begins its run loop and needs the precondition check. Do NOT fire if experiments/ does not exist; SKIP (return the SKIPPED status line) when the target experiment's rigor_tier is exploratory. If no invariants.md files exist anywhere and no retraction edges fire, exit successfully with the NO INVARIANTS DECLARED status line.
isEnabled: test -d experiments
---

# /conflicts

## Static

### Summary
Stateless precondition scanner — the research-world `/contradict`. Given a target experiment, it
(a) enumerates every peer `experiments/<exp>/invariants.md` plus `experiments/_global/invariants.md`,
reads each card's frontmatter only via the `run-reader` subagent (frontmatter-first per the budget
below), filters to invariants whose `applies_to` includes the target (or carries `[ALL]`), loads the
body for matches only, parses the structured `**INVARIANT:** <shape>: <body>` line, and checks it
against the target's `_Owns:_`/`_Depends:_` lines in `experiments/<target>/runs.md` (or the
`## Compute-plan` boundary table in `design.md` pre-`/plan-runs`); and (b) walks the
confound-contamination dependency graph — for every experiment the target `_Depends:_` on, if that
experiment is **RETRACTED** the dependency is a BLOCKER, because a retraction cascades to every
dependent (a dependent built on a retracted result inherits the same confound). It emits a
`## Conflicts` block with `Verdict: CLEAR` or `Verdict: BLOCKER`. The block is returned even when
zero invariants fire. It is **SKIPPED at exploratory tier** (RULE-0 tier-nesting: `/conflicts` is a
pilot+ gate; imposing it on exploratory work re-creates the bloat the tier system exists to prevent).

### Preconditions
- `experiments/` exists at the project root (`${CLAUDE_PROJECT_DIR}/experiments/`).
- The target experiment's `experiment.json` is readable so its `rigor_tier` can be determined. A
  missing/unknown `rigor_tier` does NOT silently pass: it defaults to `publication` (strictest) and
  the scan runs with a `tier_defaulted: publication` note in the block (RULE-0).
- The `run-reader` subagent is registered (frontmatter-first reads keep the scan under the budget).

No hard per-experiment file gate: `/conflicts` may run against any target, or the whole project (no
`exp` argument). If `experiments/<exp>/` does not exist for an explicit argument, return a
`## Conflicts` block with `Verdict: BLOCKER`, a single `UnknownTarget` finding, and exit — do NOT
crash. The consuming `/execute` must not die on a stale experiment name.

### Parameters
- `exp` — optional. Target experiment ID (the `EXP-<slug>` dir name under `experiments/`). If
  omitted, scan every non-`_` experiment as target against every peer's invariants and its own
  `_Depends:_` edges. If provided, scan only that experiment as target.

### Output format
A `## Conflicts` RETURN FORMAT block. The exact shape lives in
`${CLAUDE_PLUGIN_ROOT}/skills/conflicts/templates/conflicts-format.md` — read it once at skill
startup; it is the single source of truth for the block. The block heading is exactly `## Conflicts`
and the four mechanical top-level fields below MUST each appear as a `- <Field>:` line so
`hooks/block-lint.sh` validates it against `hooks/block-schemas.tsv`:

```
## Conflicts
- Experiment: <EXP-slug or ALL>
- Scanned: <n peers, n invariants, n _Depends:_ edges>
- Findings:
  ### Finding 1
  - severity: BLOCKER
  - invariant_id: <INV-NNN or RETRACTION-CASCADE>
  - declared_in: <experiment that declares the invariant, or "retraction graph">
  - violated_in: <target EXP-slug + offending path / RUN-ID / retracted dep>
  - description: <one line — why this is a violation>
  - suggested_resolution: <copied from the invariant card, or scanner-augmented>
  - evidence: <runs.md:line or experiment.json status field; omit if boundary-only>
- Verdict: CLEAR | BLOCKER
```

Required field per the ABI registry: `Experiment`, `Scanned`, `Findings`, `Verdict`. Per-finding
fields use lowercase keys (`severity`, `invariant_id`, …) so they never collide with the four
mechanical top-level field keys the linter greps for. `Verdict` is `BLOCKER` if at least one finding
is `severity: BLOCKER` whose `violated_in` names the **current target**; otherwise `CLEAR`. Findings
that violate a *peer's* boundary (not the target's) are reported but do NOT flip the target's verdict
to BLOCKER — see Hard constraints. The block ends with the mandatory summary line documented in
`conflicts-format.md`.

### Hard constraints
- **Budget (strict token/time cap).** A single invocation MUST stay under ~5000 additional input
  tokens and ~2 s wall-clock at typical scale (≤20 peer experiments, ≤5 invariants each). Achieve
  this by reading invariant frontmatter ONLY (via `run-reader`) and loading bodies ONLY for cards
  whose `applies_to` matches the target. Never read run logs, checkpoints, or dataset files —
  `/conflicts` reads invariant cards and `runs.md`/`design.md` boundaries, nothing heavier.
- **Halt on the first decisive BLOCKER.** Because this gates an expensive GPU run, stop scanning as
  soon as the first `BLOCKER` finding whose `violated_in` names the **current target** is confirmed,
  emit the block with `Verdict: BLOCKER`, and return. Do NOT keep enumerating to produce a "complete"
  list — the budget is for fast veto, not exhaustive audit. (Whole-project scans with no single
  target run to completion since there is no run to gate.)
- **SKIP at exploratory tier (RULE-0 / tier nesting).** If the target's `rigor_tier` is
  `exploratory`, emit a block with `Verdict: CLEAR` and `Status: SKIPPED (exploratory tier)`, the
  zeroed summary line, and exit successfully. `/conflicts` is a pilot+ precondition; never impose it
  on exploratory work. (A missing tier is NOT exploratory — it defaults to `publication` and the
  scan runs; RULE-0.)
- **Retraction cascade is a BLOCKER (RULE-6).** For every `_Depends:_` edge from the target to a
  prerequisite experiment whose `experiment.json` `status` is `retracted` (or whose latest `## Verdict`
  in `trace/<dep>.md` is `REJECT` with a retraction note), emit a `RETRACTION-CASCADE` finding,
  `severity: BLOCKER`, `declared_in: retraction graph`. A retraction propagates to dependents because
  the dependent's result rests on a confound the upstream already failed to clear. This is the edge
  that would have caught a follow-up built on proteus Eksperyment 1 after its self-retraction.
- **`applies_to: [ALL]` semantics.** A `_global` invariant with `applies_to: [ALL]` binds every
  experiment under `experiments/` whose dir name does NOT start with `_`, except the declarer. Skip
  every `experiments/_*/` directory when enumerating TARGETS; INCLUDE `experiments/_global/` only as
  an invariant SOURCE.
- **Peer-vs-target verdict scope.** A finding whose `violated_in` names a *peer* (not the target)
  is recorded with its real severity but is informational for THIS run — only a BLOCKER landing on
  the current target flips `Verdict` to `BLOCKER`. (Mirrors how order-66 `/implement` only halts on
  `violated_in` matching the current slice.) On a whole-project scan with no single target, ANY
  BLOCKER flips the block verdict.
- **Malformed invariant card.** If an `invariants.md` is missing any required frontmatter field
  (`experiment`, `version`, `applies_to`, `severity_default`), emit a `MalformedInvariant` finding,
  `severity: BLOCKER`, `declared_in: <path>`, naming the missing fields. Do NOT silently skip it — a
  silently-skipped invariant is exactly how a sealed-eval-path rule goes un-enforced and a GPU run
  contaminates the test set.
- **Scanner failure mode.** If a card fails to parse (YAML error, missing `INVARIANT:` line,
  unreadable file), do NOT emit a CLEAR that pretends the file is clean. Emit the `MalformedInvariant`
  BLOCKER (preferred) or, on a hard read error, `Verdict: BLOCKER` with a `ScannerFailure` finding
  naming the file. `/execute` halts on either signal.
- **No absolute paths (RULE-2).** Every path in any finding, evidence line, or note is
  project-relative or `${CLAUDE_PLUGIN_ROOT}`-relative. Never `/home/...`.
- **Stateless, no cache.** Every invocation is a fresh scan. There is no conflicts cache; do not
  read or write one.

### Common mistakes (avoid)
1. **Loading every `invariants.md` body up front.** Frontmatter-first is mandatory for the budget.
   Read each card's frontmatter (~10 lines via `run-reader`), filter by `applies_to`, THEN load
   bodies for matches only. Whole-file loads at scale blow the cap and the GPU run waits on you.
2. **Running `/conflicts` at exploratory tier "to be safe".** That inverts the tier system. Lower
   tiers must never inherit a higher tier's checks (CONVENTIONS §2). Exploratory work SKIPs the gate;
   the verdict is CLEAR with `Status: SKIPPED`. Imposing the scan anyway is the bloat the tiers exist
   to kill.
3. **Treating a retracted `_Depends:_` as a soft warning.** A retraction CASCADES — it is always a
   BLOCKER on the dependent (RULE-6), full stop. Letting a run proceed on a retracted upstream is how
   a debunked confound silently re-enters the literature. Never down-grade a `RETRACTION-CASCADE`
   finding.
4. **Mis-classifying `experiments/_global/` as a target experiment.** Leading-underscore dirs are
   infrastructure pseudo-experiments (invariant SOURCES only). Enumerating `experiments/*` and
   targeting every entry is wrong — filter out `_*` before targeting; keep `_global` as a source.
5. **Flipping the verdict to BLOCKER on a peer-only violation.** Only a BLOCKER whose `violated_in`
   names the CURRENT target gates this run. A peer's violation is reported but does not veto the
   target's `/execute` (it vetoes the peer's own run when that peer is scanned).

## Dynamic

Templates live under `${CLAUDE_PLUGIN_ROOT}/skills/conflicts/templates/`. Read both with the Read
tool at skill startup:
- `invariants-template.md` — declarer-facing canonical shape of an invariant card. The scanner's
  parser for the `**INVARIANT:** <shape>: <body>` line is defined by the four supported shapes
  documented there: `ForbiddenTestSetImport`, `RequiredSealedEvalPath`, `AllowedCheckpointGlob`,
  `RequiredSeedPolicy`.
- `conflicts-format.md` — the authoritative `## Conflicts` block exemplar; emit blocks that conform
  exactly (heading, the four mechanical fields, per-finding shape, summary line).

`experiments/` already exists. Enumerate candidate targets and invariant sources:

```
!{ ls -1 ${CLAUDE_PROJECT_DIR}/experiments 2>/dev/null | sed 's/^/  /' }
```

Filter the list: dir names starting with `_` are invariant SOURCES only (skip as targets); keep
`experiments/_global/` as a source.

Determine the target tier BEFORE scanning (the SKIP gate). Best-effort, jq-free (RULE-2):

```
!{ TGT="${1:-}"; F="${CLAUDE_PROJECT_DIR}/experiments/${TGT}/experiment.json"; \
   [ -n "$TGT" ] && [ -f "$F" ] && grep -o '"rigor_tier"[^,}]*' "$F" | head -1 || echo "rigor_tier: (unknown → defaults to publication per RULE-0)"; }
```

Locate every invariant source so you know what `run-reader` must read the frontmatter of:

```
!{ find ${CLAUDE_PROJECT_DIR}/experiments -maxdepth 2 -name invariants.md 2>/dev/null | sed "s#${CLAUDE_PROJECT_DIR}/##" }
```

`run-reader` is the registered frontmatter-first subagent (RR-035; the research analog of order-66's
`spec-reader`). Invoke it per `invariants.md` to read only the YAML frontmatter; load a card body
only when its `applies_to` matches the current target. This is the single largest cost-saver vs.
naive whole-file reads and is what keeps the scan inside the budget.

For each candidate target, the scanner needs the target's owned/depended boundaries:
- If `experiments/<target>/runs.md` exists: read its `_Owns:_` and `_Depends:_` lines (authoritative
  post-`/plan-runs`).
- Else if `experiments/<target>/design.md` has a `## Compute-plan` boundary table: read its path
  column (best-effort pre-`/plan-runs`).
- Else: skip the target with no findings (not enough authored state to scan).

For each loaded invariant, parse the `**INVARIANT:** <shape>: <body>` line by shape (full
definitions in `invariants-template.md`):
- `ForbiddenTestSetImport: <pattern>` — no run in the target's `_Owns:_` may import/read the sealed
  test set matching `<pattern>` (catches train/test leakage at the import level; RULE-10).
- `RequiredSealedEvalPath: <body>` — any run that evaluates MUST read held-out data only from the
  declared sealed path; an eval `_Owns:_` outside it is a finding (RULE-10 leakage-safe-by-construction).
- `AllowedCheckpointGlob: <body>` — checkpoints a run writes MUST match the allowed glob; a
  checkpoint path outside it is a finding (prevents one experiment clobbering another's frozen
  baseline — an `_Owns:_` collision).
- `RequiredSeedPolicy: <body>` — the target's declared `Seed-policy` (from its `## RunPlan` / `runs.md`)
  MUST satisfy the policy the invariant pins (e.g. "≥3 seeds at confirmatory"); a weaker policy is a
  finding (RULE-7 effect-size-needs-a-named-variation-source; under-seeded runs cannot carry a CI).

Then walk the retraction graph: for each `_Depends:_` edge, read the prerequisite's
`experiment.json` `status` (and, if ambiguous, the latest `## Verdict` in `trace/<dep>.md`). A
`retracted` status (or `REJECT`+retraction) is a `RETRACTION-CASCADE` BLOCKER on the target.

This skill writes no project state of its own; the `## Conflicts` block IS the entire return value.
No surrounding prose — `/execute` greps the `## Conflicts` heading and reads `Verdict:`.
