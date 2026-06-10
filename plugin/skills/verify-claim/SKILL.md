---
name: verify-claim
description: Manually re-spawn the independent results-verifier on a finished experiment/claim and return its `## Verdict` block unmodified. Same agent /execute spawns automatically, but user-triggered for re-checks and pre-/paper audits.
whenToUse: Invoked when the user wants to re-grade a specific claim or run after the fact — "/verify-claim C-003", "double-check EXP-spectral-length-bias", "audit RUN-007 before I write the paper", "is this result really PROMOTE?". Do NOT fire as part of /execute's loop — /execute spawns the results-verifier directly per RR (never self-grade, RULE-1). Fire when grading happens OUTSIDE that loop.
---

# /verify-claim

## Static

### Summary
Thin pass-through wrapper, the research-world analog of order-66 `/verify`. Take an experiment or a
single claim, gather the run artifacts + analysis + confound-audit + trace that bear on it, spawn the
independent `results-verifier` subagent on a fresh write-disabled context, and return its `## Verdict`
block **unmodified**. This skill grades nothing itself (RULE-1) and writes nothing — it is purely a
query. It is the way a human re-checks a verdict without re-running the expensive `/execute` loop.

### Preconditions
- The experiment exists: `${CLAUDE_PROJECT_DIR}/experiments/<exp>/` with an `experiment.json` (for
  `rigor_tier`) and a `runs.md`.
- The claim is observable: the run(s) backing it have a `## RunReport` (in `trace/<exp>.md` or under
  `experiments/<exp>/runs/<RUN-NNN>/`) and, if a positive finding, a `## ConfoundAudit` and an
  `## AnalysisReport`. If the metric was never logged, the verifier returns `BLOCKED` — that is a
  valid outcome, not an error.
- `agents/results-verifier/AGENT.md` exists.

### Parameters
- `claim` — required. A claim ID (`C-NNN`), a run ID (`RUN-NNN`), or an experiment ID
  (`EXP-<slug>`). A bare experiment ID means "verify every not-yet-graded claim in this experiment,"
  emitting one `## Verdict` block per claim.
- `exp` — optional. Disambiguate when the same `C-NNN`/`RUN-NNN` exists under more than one
  experiment. Required if `claim` is ambiguous; otherwise inferred.

### Output format
The `results-verifier`'s `## Verdict` block, passed through verbatim (see CONVENTIONS.md §4). Do not
reformat, summarize, or re-order it. Its required mechanical fields:

```
## Verdict
- Verdict: <PROMOTE | PROMOTE-WITH-CAVEAT | RERUN | REJECT | BLOCKED>
- Tier applied: <exploratory | pilot | confirmatory | publication>
- Claims: <C-NNN — held|caveated|not-supported|unscorable; one per line under this field>
- Required fixes: <numbered fixes the user must address before re-grading; "none" iff Verdict=PROMOTE>
```

The verifier may emit additional sections it owns (e.g. a `## Reasoning` block with per-claim
evidence). Pass those through too; never strip them. The four-plus-one verdict strings are mechanical
and load-bearing — `BLOCKED` ≠ `REJECT` (BLOCKED = metric never logged ⇒ unscorable; REJECT = metric
logged but does not support the claim).

### Hard constraints
- **Pass-through only.** This skill does not interpret, soften, escalate, summarize, or modify the
  verifier's output. Whatever block the verifier returns is what the user sees. (Exact analog of
  order-66 `/verify`'s pass-through rule.)
- **No re-prompting the verifier.** If the returned `## Verdict` block is malformed (missing a
  required field, an unknown verdict string, or no block at all), surface *that* as an error to the
  user — do not ask the verifier to clarify, retry, or "fix its output." A malformed verdict is a
  bug in the agent, reported as-is. The downstream `block-lint` hook is what enforces the schema; do
  not pre-empt it by patching the block.
- **Reads, never writes (RULE-1 + locked decision).** `/verify-claim` does not edit `runs.md` status
  prefixes (`[ ]`/`[~]`/`[x]`/`[!]`), does not append to `trace/`, and does not touch
  `experiment.json`. Recording the verdict and flipping the node status is `/execute`'s job, not
  this skill's. `/verify-claim` is a re-check, not a state transition.
- **Never grade in main context (RULE-1).** Always invoke the `results-verifier` subagent. The main
  context that ran (or read) the experiment must never issue the verdict itself — that is the
  never-self-grade law and the harness's central integrity guarantee.
- **Tier comes from the experiment, the verifier applies it (RULE-0).** Pass `rigor_tier` from
  `experiment.json` through to the verifier; do not pick a tier here. If `rigor_tier` is
  missing/unknown, do not silently default — the verifier itself defaults to `publication` (strictest)
  and flags it; pass the raw value (or its absence) faithfully so that fail-loud fires.
- **Plugin discipline (RULE-2).** No absolute paths in anything this skill writes or references;
  resolve via `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}`.

### Common mistakes (avoid)
1. **Spawning a fresh verifier with a hand-written prompt.** Use the existing
   `agents/results-verifier/AGENT.md` via the Agent tool (`subagent_type: results-verifier`). Don't
   reinvent the audit; the gate logic lives in the agent, not here.
2. **Inferring a verdict from the user's phrasing** ("this looks solid, right?"). Always invoke the
   subagent. The user's framing is never the verdict — RULE-1 forbids grading in main context.
3. **Re-prompting on a malformed block.** A broken `## Verdict` is reported as an error, not
   massaged into a valid one. Re-prompting would let the wrapper launder a buggy verdict.
4. **Mutating `runs.md` or `trace/` after a re-grade.** Even if a claim that was `RERUN` is now
   `PROMOTE`, this skill does NOT promote the node. State transitions belong to `/execute`. Tell the
   user to re-run `/execute` (or accept the verdict) if they want the status updated.
5. **Upgrading `BLOCKED` to `REJECT` (or vice versa) "to be clearer."** They are distinct mechanical
   outcomes (CONVENTIONS §4). Never collapse them; never score an unobservable metric as success or
   failure — that is exactly what `BLOCKED` exists to prevent.
6. **Choosing or overriding the rigor tier.** Imposing a higher tier's checks "to be safe" re-creates
   the bloat the tier system exists to prevent (RULE-0, tiers nest cumulatively). Pass the
   experiment's declared tier through untouched.

## Dynamic

`agents/results-verifier/AGENT.md` already exists when this skill fires — invoke it via the Agent
tool with `subagent_type: results-verifier`. Do not Read it to "preview the logic"; just dispatch.

Resolve the experiment for `claim` (and `exp` if given), then gather the inputs the verifier needs
and hand them over **as references, read by the subagent** — do not paste digested summaries (the
verifier reads fresh and adversarially; a pre-chewed summary would defeat the independence the
never-self-grade law buys, RULE-1):

- `experiments/<exp>/experiment.json` — the `rigor_tier` to apply (RULE-0).
- `experiments/<exp>/hypothesis.md` — the falsifiable `H-NNN` card(s) the claim is tested against.
- `experiments/<exp>/runs.md` — the node's `_Owns:_` data contract and status.
- The backing `## RunReport`(s) for the run(s) under the claim, plus the `## ConfoundAudit` and
  `## AnalysisReport` if the claim is a positive finding.
- `trace/<exp>.md` — the append-only provenance the claim was derived from.

Existing-state probe (so the skill does not re-derive what is already on disk):

- Experiments present: `!{ls -1 "${CLAUDE_PROJECT_DIR}/experiments" 2>/dev/null || echo '(none — wrong project root?)'}`
- The target experiment's tree (artifacts + trace location): `!{ls -1 "${CLAUDE_PROJECT_DIR}/experiments/<exp>/" 2>/dev/null}` and `!{ls -1 "${CLAUDE_PROJECT_DIR}/experiments/<exp>/runs/" 2>/dev/null}`
- Declared rigor tier (pass through; do NOT default here — the verifier owns RULE-0): `!{grep -o '"rigor_tier"[^,}]*' "${CLAUDE_PROJECT_DIR}/experiments/<exp>/experiment.json" 2>/dev/null || echo '(no experiment.json / no rigor_tier — verifier will fail loud to publication)'}`

If the experiment directory, the backing artifacts, or `agents/results-verifier/AGENT.md` cannot be
found, surface that as a precondition error and stop — do not fabricate a verdict and do not down-rank
the missing data into a quiet pass.
