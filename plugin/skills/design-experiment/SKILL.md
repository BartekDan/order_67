---
name: design-experiment
description: Read an experiment's hypothesis.md + experiment.json (for rigor_tier) and the prereg, then produce experiments/<exp>/design.md — Quicklook-first, then methods, tier-conditional DDRs, a Data & Compute Plan table, and Threats-to-Validity. Returns a ## DesignDraft block.
whenToUse: Invoked after /register has hash-locked the preregistration but before /data-audit and /plan-runs run. Triggered by the user saying "design the experiment", "draft design.md", "/design-experiment <exp>", or by /plan-runs refusing because design.md is missing. Do NOT fire if design.md already exists with a populated ## Data & Compute Plan — that is an edit-in-place case or a follow-up experiment via /triage.
isEnabled: test -d experiments
---

# /design-experiment

## Static

### Summary
Take one experiment that has a hash-locked hypothesis but no design. Produce `experiments/<exp>/design.md` that OPENS with a mandatory `## Quicklook` (the single inspectable number-or-plot Task 1 will emit within hours — the research analog of order-66's demo-first mandate), then methods prose, tier-conditional Design-Decision-Records, a mandatory `## Data & Compute Plan` table, and an explicit `## Threats-to-Validity / out-of-scope` section. The DDR floor is set by `rigor_tier`; tiers nest cumulatively and the top tier is never imposed on exploratory work. Returns a `## DesignDraft` block whose `DDR-count` reflects the tier.

### Preconditions
- `experiments/<exp>/hypothesis.md` exists and carries at least one `H-NNN` falsifiable hypothesis.
- `experiments/<exp>/experiment.json` exists and validates against `templates/experiment.schema.json`; it carries a `rigor_tier` field (one of `exploratory | pilot | confirmatory | publication`) and a `status` of `registered`.
- A `## Preregistration` block exists (from `/register`) at the canonical path `experiments/<exp>/preregistration.md`, carrying `Primary-metric`, `Splits`, `Analysis-plan`, and `Prereg-hash`. The design must be consistent with it (RULE-5). (Read the block from `preregistration.md`, never from `prereg.lock`; if you need the frozen plan values, read `prereg.lock` by its snake_case keys `primary_metric` / `splits` / `analysis_plan`.)
- `experiments/<exp>/design.md` does NOT exist, OR exists with only frontmatter and no populated `## Data & Compute Plan` (this guards against overwriting a completed design).

If `hypothesis.md` is missing, refuse with: `"No hypothesis for <exp>. Run /triage then /register first."`

If `experiment.json` is missing or has no `rigor_tier` field, do NOT guess: treat the tier as **`publication` (strictest)** per RULE-0, set `DDR-count` to the publication floor, and surface the missing tier as a blocking line in the `## DesignDraft` block (`Threats:` MUST name it). Never silently fall back to `exploratory`.

If the `## Preregistration` block is missing while `rigor_tier` is `confirmatory` or `publication`, refuse with: `"Prereg required at <tier> (RULE-5). Run /register to hash-lock {primary metric, splits, analysis plan} before designing."` At `exploratory`/`pilot`, proceed but flag the absent prereg in `Threats:`.

If `design.md` already has a populated `## Data & Compute Plan` (≥1 dataset row), refuse with: `"<exp> already has a design with a Data & Compute Plan. Edit design.md directly, or open a follow-up experiment via /triage."`

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `notes` — optional. Free prose carrying constraints the hypothesis does not express (e.g. "the host only has 1×A100 free until Friday"). Treated as binding hints, not as new hypotheses.

### Output format
Writes `experiments/<exp>/design.md` from `${CLAUDE_PLUGIN_ROOT}/skills/design-experiment/templates/design.md`, in this section order (some tier-conditional):

1. Frontmatter (`experiment`, `artifact: design`, `version: "1"`, `created`, `rigor_tier` inherited from `experiment.json`, `prereg_hash`, `hypotheses: [H-NNN, ...]`).
2. `# Design — <exp>` + the one-line falsifier.
3. **`## Quicklook` (mandatory in ALL tiers; FIRST after the heading)** — the single inspectable Task 1 emits within hours on a thin data slice, with its `Kind` (metric|figure|notebook-cell, mirroring `experiment.json:quicklook`), the artifact path under `${CLAUDE_PROJECT_DIR}`, what it reads (thin-slice dataset ref + version hash), what it shows (axes + signal direction), an explicit **signal line** and **kill line**, and a target wall-clock in hours. This becomes `RunPlan:Quicklook-task`.
4. `## Methods` — 2–5 paragraphs. Names the primary metric, the split unit (RULE-10), any cross-model normalization (RULE-4), the estimator and where it is fit. Cites RULE-N inline where a choice is law-driven.
5. `## Design-Decision-Records (DDR)` — **count is tier-conditional** (see Hard constraints). Each DDR at publication tier carries ≥1 named rejected alternative + the trade-off accepted.
6. **`## Data & Compute Plan`** — three tables: datasets+version-hashes+splits, seeds+N-justification, and the GPU-hours/USD/wall-clock **hard budget cap**.
7. `## Threats-to-Validity / out-of-scope` — threats (which seed the `/confound-audit` checklist, RULE-6) and the claims this experiment does NOT license, scoped to the measured distribution (RULE-9).
8. `## Risks` — optional; operational, not validity.

Then return this RETURN FORMAT block verbatim (fields per CONVENTIONS §4 / `block-schemas.tsv`):

```
## DesignDraft
- Experiment: EXP-<slug>
- Quicklook: <one line: the inspectable + its kind (metric|figure|notebook-cell) + signal/kill line>
- DDR-count: <integer> (tier <tier>; floor <0|1|1|3+>)
- Datasets: <name@hash, ...> (<n> rows in the Data & Compute Plan table)
- Compute-plan: <max_gpu_hours>h / $<max_usd> / <max_wallclock_min>min — HARD cap
- Threats: <count> threats; out-of-scope: <count> (+ any RULE-0 flag, e.g. "rigor_tier MISSING ⇒ publication-strict")
```

### Hard constraints
- **`## Quicklook` is mandatory in ALL tiers** and MUST be the FIRST section after the `# Design — <exp>` heading. Without it the output fails `/plan-runs`'s gate. It must name a within-HOURS inspectable on a thin slice — not the full run — and carry both a **signal line** and a **kill line** (the pre-stated values that say "keep going" vs "stop"). Prose alone ("we will look at accuracy") is insufficient; give the metric, the axes, and the thresholds.
- **DDR count is tier-conditional** (tiers nest; never impose a higher tier's floor on lower work — CONVENTIONS §2):
  - `exploratory`: 0 DDRs (write the section heading + "N/A — exploratory; decisions are cheap and reversible").
  - `pilot`: 1 DDR — the single methodological choice that gates scaling to expensive runs.
  - `confirmatory`: 1 DDR — same, and it MUST name the signal that would force re-registration or a down-tier (RULE-5).
  - `publication`: 3+ DDRs, EACH with ≥1 named rejected alternative + the trade-off accepted.
- **`## Data & Compute Plan` is mandatory in ALL tiers.** Every dataset row carries an immutable content hash (`name@<sha256/dvc-md5>`); a row without a hash is a defect. Splits are by the unit of scientific interest, never by row (RULE-10). The compute budget is a HARD cap (GPU-hours AND USD AND wall-clock) that the autonomous tree search halts at (D-003).
- **Be consistent with the prereg** — the design's primary metric, splits, and analysis plan must match the hash-locked `## Preregistration`. A divergence at confirmatory+ HARD-BLOCKS PROMOTE downstream (RULE-5); flag any intended change here so `/register` re-locks before runs start.
- **Missing/unknown `rigor_tier` ⇒ publication-strict + a blocking flag** (RULE-0). Never silently default to permissive.
- **No absolute paths** (`/home/`, `/Users/`, `/root/`, `/mnt/...`) anywhere in `design.md` (RULE-2). Use `${CLAUDE_PROJECT_DIR}` for project/experiment artifacts and `${CLAUDE_PLUGIN_ROOT}` for plugin files. Remote host paths live only in the gitignored `host-config.json`, referenced by name.
- **Do not generate run code or `runs.md`** — that is `/plan-runs`'s job. This skill produces only the design document and the `## DesignDraft` block.
- **Do not invent datasets or nodes the hypothesis does not imply.** If `H-001` only concerns one model's residual stream, the plan does not enumerate a cross-model sweep.
- **Never self-grade** (RULE-1): `## DesignDraft` reports the design's shape; it never asserts the hypothesis is supported.

### Common mistakes (avoid)
1. **Skipping `## Quicklook` because "the real result is the run."** The Quicklook is the contract that lets the harness fail cheap: it is the within-hours falsifier that, if flat, kills the experiment before it burns the GPU budget. Refuse to write `design.md` without it — exactly as order-66 refuses a design with no `## Demo`.
2. **A Quicklook that is just the full experiment shrunk.** "Run the whole pipeline on 10% of data" is not a Quicklook; it is a small run. The Quicklook is the ONE number/panel on a thin slice (one layer, a few hundred questions, single seed) you can stare at in hours. Name its axes and its kill line.
3. **Forcing 3 DDRs onto exploratory work "to be rigorous."** Exploratory has 0 DDRs by design — the decisions are cheap and reversible, and padding DDRs buries the work in ceremony the tier exists to avoid. More DDRs ≠ more rigor; the *right* DDR at the *right* tier is rigor.
4. **Thin DDRs at publication tier.** "We use a linear probe." is not a DDR. "We use a linear probe over an MLP probe because a non-linear probe can memorize the 200-question slice and inflate bal-acc; trade-off: we may miss a genuinely non-linear code, re-examine if the linear null is clean (RULE-8)." IS a DDR. Every publication DDR cites a rejected alternative + trade-off.
5. **A Data & Compute Plan with no version hashes.** A dataset row without an immutable content hash means a later run cannot prove it read the same bytes — the exact reproducibility gap (D-004) the harness exists to close. `name@<hash>` is mandatory, not decorative.
6. **No kill line / no budget cap.** A design that can only say "keep going" has no way to stop. Both the Quicklook kill line and the compute hard cap are what make the autonomous tree search safe (D-003). Omitting them is a blocking defect.
7. **Burying a real methods decision in prose.** A choice in `## Methods` that could have gone the other way and changes what the result MEANS (split unit, normalization, baseline, correction) is invisible to the reader and to `/confound-audit` unless it is a numbered DDR. If it is law-driven (RULE-N), cite the rule.
8. **Splitting by row.** Splitting the dataset by row instead of by the unit of scientific interest (e.g. question id) leaks information across train/test and is a DO-NOT-PROMOTE downstream (RULE-10). The Data & Compute Plan's split column must name the unit.

## Dynamic

Template: `${CLAUDE_PLUGIN_ROOT}/skills/design-experiment/templates/design.md`. Read it with the Read tool — it lays out the section order, the frontmatter shape, the Quicklook block, the tier-conditional DDR comment, and the three Data & Compute Plan tables.

Rulebook: `${CLAUDE_PLUGIN_ROOT}/templates/research-rulebook.md` — cite RULE-N by number; RULE-5 (honor the prereg), RULE-6 (threats seed the confound-audit), RULE-7 (effect size + named CI), RULE-9 (scope the claim), RULE-10 (split by unit of interest) are the load-bearing ones here.

The following already exist when this skill fires — read them directly, do NOT `ls` to check:

- `experiments/<exp>/hypothesis.md` — read the `H-NNN` lines and the falsifier prose.
- `experiments/<exp>/experiment.json` — read `rigor_tier` FIRST and branch the DDR floor on it; read `quicklook` (to mirror its `Kind`), `dataset_refs` (names + hashes + splits), `seed_policy`, and `compute.budget` (the hard cap) so the Data & Compute Plan tables reuse them rather than reinventing.
- `experiments/<exp>/preregistration.md` — read the `## Preregistration` block from this canonical path and reconcile the design's primary metric / splits / analysis plan against it. If you need the frozen plan values, read `experiments/<exp>/prereg.lock` by its snake_case keys (`primary_metric` / `splits` / `analysis_plan`) — never read the block from `prereg.lock`.

Read the tier once, up front:

```
!{tier=$(grep -o '"rigor_tier"[[:space:]]*:[[:space:]]*"[a-z]*"' experiments/${exp:-*}/experiment.json 2>/dev/null | grep -o '[a-z]*"$' | tr -d '"' | head -1); echo "rigor_tier=${tier:-MISSING(=>publication-strict, RULE-0)}"}
```

Surface the existing budget and dataset refs so the plan does not reinvent them (no `jq` — best-effort grep, RULE-2):

```
!{grep -oE '"(max_gpu_hours|max_usd|max_wallclock_min)"[[:space:]]*:[[:space:]]*[0-9.]+' experiments/${exp:-*}/experiment.json 2>/dev/null || echo "no compute.budget in experiment.json — design MUST set a hard cap"}
```

```
!{grep -oE '"(name|hash|split)"[[:space:]]*:[[:space:]]*"[^"]*"' experiments/${exp:-*}/experiment.json 2>/dev/null | head -30 || echo "no dataset_refs yet — Data & Compute Plan must declare them with content hashes"}
```

Confirm the design is not about to clobber a finished one (this is the only pre-write `ls` allowed):

```
!{ls experiments/${exp:-<exp>}/ 2>/dev/null; echo '---'; grep -c '^| ' experiments/${exp:-<exp>}/design.md 2>/dev/null || echo 'no design.md yet — OK to write'}
```
