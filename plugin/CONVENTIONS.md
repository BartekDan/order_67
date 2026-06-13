# order-67 Research Harness — Conventions & `## Block` ABI

This file is the **single source of truth** for how skills and agents in this harness talk to
each other. Every skill author and agent author MUST conform to it. It is the analog of the
implicit conventions in `order-66-sdd-harness` (the `R-NNN` requirement IDs, the named return
blocks, the `_Boundary:_` annotations), made explicit here because expensive GPU runs make a
silent ABI drift far costlier than in software work.

---

## 1. Identifier schemes

| Prefix | Meaning | Lives in | Example |
|--------|---------|----------|---------|
| `H-NNN` | Falsifiable hypothesis | `experiments/<exp>/hypothesis.md` | `H-001` |
| `EXP-<slug>` | Experiment ID (stable, kebab-case ≤ 30 chars) | `experiments/<exp>/` | `EXP-spectral-length-bias` |
| `RUN-NNN` | A single run (one seed/config of a node) | `experiments/<exp>/runs/<RUN-NNN>/` | `RUN-007` |
| `C-NNN` | A claim derived from runs (what the verifier grades) | `trace/<exp>.md`, `analysis.md` | `C-003` |
| `RR-NNN` | Research-harness requirement (this plugin's own spec) | `spec/` | `RR-012` |
| `D-NNN` | Design decision (this plugin's own ADRs) | `spec/` | `D-004` |
| `RULE-N` | Interpretation rule (the research rulebook) | `templates/research-rulebook.md` | `RULE-7` |
| `RIGOR_DEBT(due:YYYY-MM-DD):` | Greppable rigor-debt marker | code/notes/analysis | — |

Dates are always ISO-8601 (`YYYY-MM-DD`) and **absolute** — never "today"/"last week".

---

## 2. Rigor tiers (the load-bearing enum — analog of order-66 `mode`)

`rigor_tier ∈ { exploratory, pilot, confirmatory, publication }`. It is carried in
`experiment.json` and propagates to every skill and the verifier. Tiers NEST: each adds to the
checks of the one below; **the top tier is never imposed on exploratory work** (that re-creates
the bloat the tier system exists to prevent).

| Tier | Adds (cumulative) |
|------|-------------------|
| `exploratory` | runs without error · no committed secret · single seed OK · no train/test leakage · **all run code committed in-repo — every step a named, versioned script; no inline `python -c`/ad-hoc/notebook execution (RULE-11)** |
| `pilot` | + a held-out split exists · `signal_confirmed` gate · label-permutation-null confound probe on any positive before scaling (RULE-6) |
| `confirmatory` | + N≥k seeds (k justified) · 95% CI w/ named variation source · effect size · FDR correction · mandatory confound-audit on positives · **prereg deviation HARD-BLOCKS PROMOTE** |
| `publication` | + full NeurIPS 16-item checklist (items 4–8 Yes-with-evidence) · datasheet · model card · ablation completeness · reproducibility evidence |

The pilot `signal_confirmed` gate is a *frozen* threshold object in `experiment.json`
(`{metric, threshold, baseline, direction}`) that the verifier reads as a pre-set value — not a
post-hoc bar. It is distinct from the triage `Signal-validated` routing field, which is a coarse
"is there any cheap evidence yet?" heuristic that only biases routing.

**Fail-loud rule (RULE-0):** a missing or unknown `rigor_tier` (or missing `seed`/`split`/
`prereg_hash` where required) defaults to **`publication` (strictest)** AND surfaces the gap as a
blocking issue. Never silently fall back to permissive. (Direct port of order-66's missing-mode
→ production-strict safety property; inverting it would let invalid runs masquerade as fine.)

---

## 3. SKILL.md authoring template

Every `skills/<name>/SKILL.md` follows this shape (matches order-66 exactly):

```
---
name: <skill-name>
description: <one sentence; what it does + what ## Block it returns>
whenToUse: <trigger phrases; when the orchestrator should fire this skill>
# Optional: isEnabled: <test command, e.g. test -d experiments> — gate the skill on filesystem state.
---

# /<skill-name>

## Static

### Summary
<2–4 sentences.>

### Preconditions
- <filesystem state that must hold before this skill runs>

### Parameters
- `<param>` — required|optional. <description>

### Output format
A `## <Block>` RETURN FORMAT block (see CONVENTIONS.md §4):
```
## <Block>
- Field: <value>
...
```

### Hard constraints
- <non-negotiable rules; cite RULE-N / RR-NNN where relevant>

### Common mistakes (avoid)
1. <the tempting wrong thing and why it's wrong>

## Dynamic
<template refs via ${CLAUDE_PLUGIN_ROOT}/...; runtime `!{bash}` interpolation;
 notes on what already exists so the skill doesn't re-check.>
```

Bash interpolation uses `!{...}` (e.g. `!{ls experiments/}`). Template reads use the Read tool on
`${CLAUDE_PLUGIN_ROOT}/skills/<name>/templates/<file>`.

---

## 4. The `## Block` ABI (return-format registry)

Skills/agents communicate by emitting a named markdown block whose first content line(s) are
**mechanical** (the consumer greps the heading and reads fixed fields). Field lines use
`- <Field>: <value>`. The machine-checkable required-field list lives in
`hooks/block-schemas.tsv` and is enforced by `hooks/block-lint.sh`. **If you add or rename a
field here, update `block-schemas.tsv` in the same change.**

| Block | Emitted by | Consumed by | Required fields (mechanical) |
|-------|-----------|-------------|------------------------------|
| `## ResearchRouting` | /triage | user → /register | `Path`, `Experiment`, `Rigor-tier`, `Rationale`, `Next action`, `Confidence`, `Signal-validated` |
| `## Preregistration` | /register | /design-experiment | `Experiment`, `Hypotheses`, `Primary-metric`, `Splits`, `Analysis-plan`, `Prereg-hash`, `Rigor-tier` |
| `## DesignDraft` | /design-experiment | /data-audit, /plan-runs | `Experiment`, `Quicklook`, `DDR-count`, `Datasets`, `Compute-plan`, `Threats` |
| `## DataAudit` | /data-audit, data-steward | /plan-runs, /execute | `Experiment`, `L1`, `L2`, `L3`, `Leakage-checks`, `Secret-scan`, `Verdict` (PASS/FAIL) |
| `## RunPlan` | /plan-runs | /execute | `Experiment`, `Nodes`, `Seed-policy`, `Budget`, `Quicklook-task` |
| `## Conflicts` | /conflicts | /execute | `Experiment`, `Scanned`, `Findings`, `Verdict` (CLEAR/BLOCKER) |
| `## RunReport` | /execute | /confound-audit, /analyze, results-verifier | `Run`, `Node`, `Status`, `Metrics`, `Seed`, `Artifacts`, `Trace` |
| `## ConfoundAudit` | /confound-audit | results-verifier, /analyze | `Claim`, `Permutation-null`, `Nuisance-screen`, `Statistic-swap`, `Alt-preprocessing`, `Survives` (YES/NO) |
| `## AnalysisReport` | /analyze | /paper, /brief | `Experiment`, `Primary-metric`, `Effect-size`, `CI`, `Correction`, `Figures` |
| `## Verdict` | results-verifier, /verify-claim | /execute, user | `Verdict` (PROMOTE/PROMOTE-WITH-CAVEAT/RERUN/REJECT/BLOCKED), `Tier applied`, `Claims`, `Required fixes` |
| `## PaperReport` | /paper | user | `Experiment`, `Artifact`, `Checklist`, `Citations-needed`, `Open-gaps` |
| `## BriefReport` | /brief | user (R&D mgmt) | `Experiment`, `Artifact`, `Bottom-line`, `Grade`, `Next-actions` |
| `## DriftReport` | /drift | user | `Scanned`, `Consolidated`, `Retractions`, `Rigor-debt-overdue`, `Pruned` |
| `## RunList` / `## RunStatus` / `## ArtifactOwnership` | run-reader | any skill | (see run-reader AGENT.md) |
| `## ReproReport` | reproducibility-checker | results-verifier, /paper | `Run`, `Seed-recorded`, `Config-snapshot`, `Env-pinned`, `NeurIPS-4-8`, `Verdict` |
| `## Review` | peer-reviewer | /paper | `Recommendation`, `Scores`, `Major-issues`, `Minor-issues` |
| `## NoveltyScan` | novelty-scout | /novelty | `Contribution`, `Verdict` (NOVEL/NOVEL-COMBINATION/INCREMENTAL/PRIOR-ART/UNVERIFIED), `Closest-prior-art`, `What-is-new`, `Defensible-claim`, `Reviewer-objection`, `Confidence` |
| `## NoveltyReport` | /novelty | user → /paper | `Experiment`, `Artifact`, `Contributions-scanned`, `Novel`, `Incremental`, `Prior-art`, `Open-gaps` |
| `## FigureReport` | figure-smith | /analyze, /paper | `Figure`, `Lint`, `Violations`, `Path` |

**The four+one mechanical verdict strings** (`## Verdict` line, one per line, nothing else):
`PROMOTE` · `PROMOTE-WITH-CAVEAT` · `RERUN` · `REJECT` · `BLOCKED`.
`BLOCKED` ≠ `REJECT`: BLOCKED means the metric was never logged so the claim is *unscorable*
(ported from order-66 uat-judge's BLOCKED≠FAIL distinction); REJECT means the metric was logged
but does not support the claim. **Never score an unobservable metric as success.**

**Preregistration persistence.** `/register` persists the `## Preregistration` block to the canonical
path `experiments/<exp>/preregistration.md` — the single location every consumer
(`/design-experiment`, `/analyze`, `/paper`, `/brief`) reads it from. The hashed plan *body* lives
separately in `prereg.lock` (snake_case keys `primary_metric` / `splits` / `analysis_plan` + git
commit + ISO timestamp + the sha256). **Do not conflate the two:** read frozen plan values from
`prereg.lock` by its keys; read the `## Preregistration` block (hyphenated mechanical fields) from
`preregistration.md`.

**What block-lint validates.** `hooks/block-lint.sh` checks field *presence* for every block above,
plus *value* constraints on the load-bearing fields: the `## Verdict` enum (the five strings), the
`## Conflicts` (CLEAR/BLOCKER), `## ConfoundAudit` (Survives YES/NO) and `## DataAudit`
(Verdict PASS/FAIL) enums, and **non-blank** `## DataAudit` `L1`/`L2`/`L3` (the RULE-10 leakage gate).
Free-text field values are not validated. Constraints are declared inline in `block-schemas.tsv`
(`Field=enum:A|B` or `Field=nonblank`).

---

## 5. Task annotations (in `runs.md`, analog of order-66 `_Boundary:_`/`_Depends:_`/`_Mode:_`)

- `_Owns:_ <paths/datasets/configs>` — the **data contract**. A run may only write inside this
  set. A write outside it is a hard `REJECT` (catches accidental writes to the test set,
  frozen-baseline edits, split contamination).
- `_Depends:_ <RUN-IDs / nodes>` — prerequisite runs.
- `_Tier:_ <exploratory|pilot|confirmatory|publication>` — overrides the experiment default for
  this node if present.
- `(P)` — node is embarrassingly-parallel-safe (e.g. a seed sweep).
- Status prefixes on node lines: `[ ]` pending · `[~]` running · `[x]` promoted · `[!]` halted
  (RERUN/REJECT/BLOCKED).

---

## 6. The never-self-grade law (RULE-1)

The agent or code that produced a result **never** issues its own verdict. The `results-verifier`
is a separate, write-disabled subagent run on a fresh context with an adversarial "try to break
it" prompt. `/execute` spawns it BEFORE recording any claim. This is the analog of order-66's
"implementer never self-grades" and is the harness's central integrity guarantee.

---

## 7. State tiers & caps

`trace/` (mechanical provenance, append-only) → `FINDINGS.md` (capped one-line-pointer index) →
`sessions/` (episodic narratives) → consolidated by `/drift`. `FINDINGS.md` and
`experiments/agenda.md` are dual-capped at **200 lines / 25 KB**, one-line pointers only, truncate
at a newline boundary. `/drift` enforces the caps and converts relative dates to absolute.

---

## 8. Plugin discipline (RULE-2)

No absolute paths in any skill/agent/hook (`/home/...`, `/Users/...` are forbidden). Resolve via
`${CLAUDE_PLUGIN_ROOT}` (plugin files) and `${CLAUDE_PROJECT_DIR}` (the project under study).
Hooks must not depend on `jq` (not guaranteed on every box) — parse JSON best-effort with
`grep`/`sed`, exactly as the order-66 hooks do.
