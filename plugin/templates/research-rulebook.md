# Research Rulebook

The interpretation laws every skill and agent in this harness obeys. Copied into a project as
`CLAUDE.md` (or `RESEARCH_RULEBOOK.md`) when the harness is first run against it; skills cite these
by number. Adapted from the proteus-h-neurons rulebook + the reproducibility/leakage/stats prior art.

> **RULE-0 — Fail loud on missing rigor metadata.** A missing/unknown `rigor_tier`, or a missing
> `seed`/`split`/`prereg_hash` where the tier requires it, defaults to **`publication` (strictest)**
> and is surfaced as a *blocking* issue. Never silently fall back to permissive.

> **RULE-1 — Never self-grade.** The agent or code that produced a result never issues its own
> verdict. The independent `results-verifier` (fresh context, write-disabled) grades it.

> **RULE-2 — Plugin discipline.** No absolute paths anywhere; resolve via `${CLAUDE_PLUGIN_ROOT}`
> and `${CLAUDE_PROJECT_DIR}`. Hooks never depend on `jq`.

> **RULE-3 — Correct for multiple comparisons; always report N.** When more than one comparison is
> made, declare a correction (Holm or Benjamini–Hochberg) and the *pre-registered primary metric*.
> Report the number of comparisons explicitly.

> **RULE-4 — Normalize before comparing across models.** Any cross-model claim requires an explicit
> normalization (relative depth, per-model z-score, PCA-to-common-dim, or Procrustes). A raw
> cross-model comparison is refused.

> **RULE-5 — Pre-register, then honor it.** {hypothesis, primary metric, splits, analysis plan} are
> hash-locked before any result exists. At confirmatory+ tiers a deviation HARD-BLOCKS PROMOTE
> (re-register or down-tier); at exploratory it is free but flagged. Post-hoc choices are
> exploratory, never confirmatory (anti-HARKing, anti-p-hacking).

> **RULE-6 — Confound-audit every positive at pilot tier and above.** A positive at **pilot** must
> pass at minimum the **label-permutation-null** probe (the cheapest, at the exploratory K floor)
> before it may be claimed or PROMOTED — pilot is the gate to expensive confirmatory spend, so the
> Eksperyment-1 length-confound must be screened *here*. At **confirmatory+** the full four-probe
> screen is mandatory: label-permutation null + nuisance-variable screen (e.g. answer-length) +
> statistic-swap + alternative-preprocessing re-run, with thresholds frozen in the audit header
> *first*. **Exploratory** positives are flagged, not audited. A finding that does not survive is
> retracted. (This is the gate that self-retracted proteus Eksperyment 1.)

> **RULE-7 — Effect size over bare significance.** Every headline metric carries an effect size
> (Cohen d / R² / balanced-accuracy delta over baseline) AND a CI/std with a *named* variation
> source (seed / init / split) and a *named* CI method (bootstrap / closed-form). A bare p-value is
> not a result. In briefs, communicate magnitude AND consistency, never significance alone.

> **RULE-8 — Null results are results.** A solid null after an adequately-powered test is a finding,
> recorded, not discarded. An underpowered null is flagged (no power analysis ⇒ not a clean null).

> **RULE-9 — Don't overclaim beyond the distribution scope.** Every detection/generalization claim
> is scoped to the actual (often heavily-filtered) data distribution it was measured on; paper and
> brief must state that scope.

> **RULE-10 — Leakage-safe by construction.** Split by the unit of scientific interest (e.g.
> question id), never by row. All reducers/preprocessing/feature-selection fit on the train fold
> only, inside CV. A fit on combined or test data is a DO-NOT-PROMOTE.

> **RULE-11 — Every step is committed code; no inline or ad-hoc execution.** Each experiment must
> carry, in the repo, the COMPLETE set of scripts that produced its result — every generation,
> capture, feature build, probe, eval, fusion, and post-hoc transform. A step run as an inline
> `python -c "..."`, a one-off shell snippet, a notebook cell, or any command that is not a
> committed, named script does NOT exist for reproduction purposes and is a DO-NOT-PROMOTE.
> `experiments/<exp>/runs.md` must name the exact committed script(s) and command(s) for every node;
> a runs.md that points at a result with no committed code behind it is a hard gap. The bar is
> blunt on purpose: "the code is on the box / in my shell history" is not reproducible. This applies
> at EVERY tier (it is part of the exploratory baseline — `runs without error` is meaningless if the
> run cannot be re-issued from versioned code).
