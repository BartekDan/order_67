---
name: analyze
description: Compute report-grade statistics (mean ± 95% CI with a named variation source and CI method, an effect size, multiple-comparisons correction) from an experiment's runs/*/metrics.json, render Ten-Simple-Rules-linted multi-panel figures via the figure-smith agent, and write results/<exp>/stats.json + analysis.md. Returns a ## AnalysisReport block.
whenToUse: Invoked after /execute has recorded ≥1 promotable RUN (and, for any positive finding, after /confound-audit has run) and the experiment needs headline statistics before /paper or /brief. Triggered by "analyze the runs", "compute stats", "make the figures", "/analyze <exp>". Do NOT fire before metrics exist, and do NOT re-issue a verdict — /analyze summarizes, the results-verifier grades (RULE-1).
isEnabled: test -d experiments
---

# /analyze

## Static

### Summary
Turn one experiment's raw `runs/*/metrics.json` into report-grade statistics and figures. For the **pre-registered primary metric** (read from `prereg.lock`), compute mean ± 95% CI with an explicitly **named variation source** (seed / init / split) and a **named CI method** (bootstrap / closed-form), an **effect size** over the declared baseline (Cohen d / R² / balanced-accuracy delta — never a bare p), a **multiple-comparisons correction** (Holm / Benjamini–Hochberg) with the comparison count N stated, and — for any cross-model claim — an explicit **cross-model normalization** (relative depth / per-model z-score / Procrustes). Dispatch the **figure-smith** agent to render colorblind-safe, vector, multi-panel figures under its Ten-Simple-Rules linter. Write `results/<exp>/stats.json` (machine-readable) + `results/<exp>/analysis.md` (human-readable, English) and return a `## AnalysisReport` block. `/analyze` never issues a PROMOTE/REJECT verdict (RULE-1) — it hands the numbers to the verifier and to `/paper`/`/brief`.

### Preconditions
- `experiments/<exp>/experiment.json` exists and carries a `rigor_tier`. A missing/unknown tier ⇒ treat as `publication` (strictest) AND surface it as a blocking issue in the report (RULE-0). Never silently fall back to permissive.
- `experiments/<exp>/runs/<RUN-NNN>/metrics.json` exists for ≥1 run. If zero metrics files exist, refuse with: `"No metrics for <exp>. Run /execute first; nothing to analyze."`
- The frozen plan values exist: `experiments/<exp>/prereg.lock` (snake_case keys `primary_metric` / `splits` / `analysis_plan`) names the primary metric, and `experiments/<exp>/preregistration.md` carries the `## Preregistration` block (hyphenated fields `Primary-metric` / `Splits` / `Analysis-plan`). Read the frozen plan values from `prereg.lock` by its snake_case keys; read the `## Preregistration` block from `preregistration.md` — do not conflate the two (CONVENTIONS §4). If the primary metric cannot be read AND `rigor_tier` is `confirmatory`/`publication`, refuse with: `"No pre-registered primary metric for <exp> at tier <tier>. Re-run /register or down-tier (RULE-5)."` At `exploratory`/`pilot`, proceed but flag the analysis as post-hoc/exploratory in the report (RULE-5).
- For any positive finding to be presented as a result, the confound-audit must have screened it (RULE-6, tier-graded): at `pilot`, the corresponding `## ConfoundAudit` block must exist with `Permutation-null: PASS` (the minimum probe — pilot gates expensive confirmatory spend); at `confirmatory`+ it must exist with `Survives: YES` (the full four-probe screen). `exploratory` positives are reported flagged-not-audited. A positive claim missing the tier-required confound screen is reported as **unaudited** and may not be presented as a result.
- `${CLAUDE_PROJECT_DIR}/results/` is writable. `/analyze` writes ONLY inside `results/<exp>/` — it never edits `runs/`, `prereg.lock`, the test split, or any frozen baseline (a write outside `results/<exp>/` is a data-contract violation, CONVENTIONS §5).

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `metric` — optional. Override the metric to headline. Ignored at `confirmatory`+ where the primary metric is hash-locked in `prereg.lock` (an override there is a prereg deviation — see Hard constraints). At `exploratory`/`pilot` it selects a post-hoc metric, flagged as such.
- `baseline` — optional. RUN-ID or named constant the effect size is taken over (e.g. a random/majority/published baseline). Defaults to the baseline declared in the analysis plan; if none is declared, refuse rather than invent one.
- `ci_method` — optional. `bootstrap` (default; report n_resamples and that it is BCa or percentile) or `closed-form` (report the distributional assumption). Must be named in the output — an unnamed CI is rejected (RULE-7).

### Output format
Writes `results/<exp>/stats.json` and `results/<exp>/analysis.md` using `${CLAUDE_PLUGIN_ROOT}/skills/analyze/templates/stats-contract.md` (the required statistics for a headline claim) and `${CLAUDE_PLUGIN_ROOT}/skills/analyze/templates/figure-style-guide.md` (the Ten-Simple-Rules figure linter). Returns this exact `## AnalysisReport` RETURN FORMAT block (fields are mechanical — the heading and every `- <Field>:` line must match `hooks/block-schemas.tsv` verbatim or `block-lint.sh` rejects it):

```
## AnalysisReport
- Experiment: EXP-<slug>
- Primary-metric: <metric name> (source: prereg.lock | POST-HOC-flagged) · N_runs=<k seeds/inits/splits>
- Effect-size: <Cohen d|R²|bal-acc Δ> = <value> over baseline <RUN-NNN|name> [<effect-size 95% CI>]
- CI: <mean> ± <half-width> (95%; variation source: seed|init|split; method: bootstrap[BCa,n=<R>]|closed-form[<assumption>])
- Correction: <Holm|Benjamini-Hochberg|none> over N=<comparisons>; primary p_adj=<value> (or "n/a — single pre-registered comparison")
- Figures: <count> rendered → results/<exp>/figures/*.svg · figure-smith Lint: PASS|FAIL (Violations: <n>)
```

Additional lines MAY follow the required six (e.g. `- Cross-model-norm:`, `- Null-result:`, `- Scope:`, `- Tier-applied:`, `- Flags:`) but the six above MUST be present and spelled exactly. Multi-claim experiments emit one `## AnalysisReport` per pre-registered claim (`C-NNN`), each a self-contained block.

`stats.json` is the machine-readable twin: per-claim `{claim_id, metric, n, mean, ci_low, ci_high, ci_method, variation_source, effect_size_kind, effect_size, baseline_ref, correction, n_comparisons, p_adj, cross_model_norm, confound_audit_survives, post_hoc, null_result, scope}`. `analysis.md` is the English narrative: one section per claim, each citing its figure, its effect size in plain language (magnitude AND consistency, never significance alone — RULE-7), and its distribution scope (RULE-9).

### Hard constraints
- **Headline the pre-registered primary metric.** Read it from `prereg.lock`; do not silently switch metrics. At `confirmatory`+ a metric switch is a prereg deviation that **HARD-BLOCKS PROMOTE** (RULE-5) — record it as a deviation in the report and let the verifier act; do not paper over it. At `exploratory`/`pilot` a switch is free but the result is flagged post-hoc.
- **No bare p-values (RULE-7).** Every headline number carries (a) an effect size over the declared baseline, (b) a CI/std with a NAMED variation source, and (c) a NAMED CI method. A p-value alone is not a result and must not appear as the headline.
- **Name the variation source and the CI method (RULE-7).** "95% CI" with no stated source (seed vs init vs split) or method (bootstrap vs closed-form) is rejected — they answer different questions and a reader cannot interpret the interval without both.
- **Correct for multiple comparisons and state N (RULE-3).** When >1 comparison is made, apply Holm (FWER) or Benjamini–Hochberg (FDR), report the comparison count N explicitly, and report the adjusted statistic for the primary metric. A swept grid reported as a bag of unadjusted "significant" cells is forbidden.
- **Normalize before any cross-model claim (RULE-4).** A cross-model comparison requires an explicit normalization (relative depth / per-model z-score / PCA-to-common-dim / Procrustes) named in the report. A raw cross-model number is refused.
- **A null is a result (RULE-8).** A clean null after an adequately powered test is reported as a finding (`Null-result:` line + `null_result:true` in stats.json). An underpowered null (no power justification for N) is flagged as "not a clean null" — never silently dropped.
- **Scope every claim to its measured distribution (RULE-9).** State the (often heavily filtered) data distribution each effect was measured on; do not extrapolate beyond it.
- **Tiers nest; do not over-impose (CONVENTIONS §2).** `exploratory` needs no CI/effect-size/correction — descriptive stats + a figure suffice; demanding FDR there re-creates the bloat the tier system exists to remove. `pilot` adds a held-out split AND a label-permutation-null confound screen (`## ConfoundAudit` `Permutation-null: PASS`) on any positive before it may be presented as a result (RULE-6). CI + named-source + effect-size + FDR + the full four-probe confound-audit gate (`Survives: YES`) are required at `confirmatory`+; the full NeurIPS evidence at `publication`. Apply exactly the active tier's checks.
- **Figures go through figure-smith — do not hand-draw and self-pass.** Spawn the `figure-smith` agent with the panel spec; it runs the Ten-Simple-Rules linter and returns a `## FigureReport` (fields `Figure, Lint, Violations, Path`). `/analyze` records that report verbatim — it does NOT grade its own figures (RULE-1). If `Lint: FAIL`, fix the spec and re-dispatch; never ship a figure with open violations.
- **Plot the random/chance baseline as a dashed line (figure-style-guide).** Any performance figure shows the random-baseline reference as a dashed line so the reader sees "above chance" at a glance. No jet/rainbow colormap, no 3D, no pie, no dual-axis (figure-style-guide; figure-smith enforces).
- **No absolute paths (RULE-2).** Resolve plugin files via `${CLAUDE_PLUGIN_ROOT}` and project files via `${CLAUDE_PROJECT_DIR}`. `analysis.md`/`stats.json` reference figures by `results/<exp>/figures/<name>.svg`, never `/home/...`.
- **Never self-grade (RULE-1).** `/analyze` produces numbers and figures; it does not emit `PROMOTE`/`REJECT`/etc. The independent `results-verifier` reads the `## AnalysisReport` + `## ConfoundAudit` + `## ReproReport` and issues the `## Verdict`.

### Common mistakes (avoid)
1. **Reporting a p-value as the headline.** "p = 0.001" tells the reader nothing about magnitude or practical relevance. The headline is `Cohen d = 0.82 [0.41, 1.20]` (or R², or bal-acc delta) over a named baseline. A significant tiny effect on a huge N is not a finding; an effect-size + CI says so, a p-value hides it (RULE-7).
2. **An anonymous CI.** "mean 0.71 ± 0.04 (95% CI)" is unscorable: a CI over 5 seeds, over 5 random inits, and over 5 data splits answer three different scientific questions. Always write the source AND the method. The block is rejected without both.
3. **Reporting the best cell of a swept grid as if it were a single test.** Sweeping 20 hyperparameter cells and headlining the winner without Holm/BH over N=20 is p-hacking. Declare N, correct, and report the adjusted statistic for the *pre-registered* metric (RULE-3) — not the most flattering post-hoc cell.
4. **Comparing models on raw numbers.** "Model A layer 14 beats Model B layer 14" across models of different depth/width is meaningless without normalization. Use relative depth or per-model z-score or Procrustes and say which (RULE-4). A raw cross-model number is refused, not footnoted.
5. **Burying or discarding a null.** A clean, powered null is a real finding and must be reported as one (RULE-8). Hiding it biases the literature; reporting an *underpowered* null as clean is the opposite error — flag the lack of power, don't launder it.
6. **Forcing confirmatory machinery onto exploratory work.** Bootstrapping a CI and running BH on a one-seed exploratory smell-test is theater that wastes effort and falsely signals rigor. At `exploratory` a labeled descriptive summary + one honest figure is the correct deliverable. Apply the active tier, no more (CONVENTIONS §2).
7. **Self-passing a figure.** Hand-drawing a matplotlib jet-colormap 3D bar chart and writing "Lint: PASS" violates RULE-1 and the figure linter. Figures are dispatched to figure-smith; its `## FigureReport` is recorded as-is. A `FAIL` is fixed at the source, not overwritten.
8. **Switching the headline metric to the one that looks best.** At `confirmatory`+ the primary metric is hash-locked. Quietly headlining a different metric is HARKing and HARD-BLOCKS PROMOTE (RULE-5). Report the pre-registered metric; surface any deviation as a deviation.
9. **Writing outside `results/<exp>/`.** "Just touching up" a `metrics.json` or re-running a reducer over the combined train+test fold to "tidy" a number is a leakage/contract violation (RULE-10, CONVENTIONS §5). `/analyze` reads runs and writes only `results/<exp>/`.

## Dynamic

Templates (read with the Read tool — do not inline-guess their contents):
- `${CLAUDE_PLUGIN_ROOT}/skills/analyze/templates/stats-contract.md` — the required statistics for a headline claim, per tier; the checklist `stats.json`/`analysis.md` must satisfy and the verifier reads against.
- `${CLAUDE_PLUGIN_ROOT}/skills/analyze/templates/figure-style-guide.md` — the Ten-Simple-Rules linter (colorblind-safe palette; no jet/rainbow, no 3D, no pie, no dual-axis; dashed random-baseline line; declarative-sentence titles; vector output). Shared with the `figure-smith` agent, which enforces it; `/analyze` reads it to write panel specs figure-smith will accept.

Read the active tier and primary metric FIRST and branch on them — do not run confirmatory machinery on exploratory work (RULE-0 only forces strict on a *missing* tier, not a present low one):
`!{ test -f experiments/${exp:-}/experiment.json && grep -o '"rigor_tier"[^,}]*' experiments/${exp:-}/experiment.json | head -1 || echo 'NO experiment.json → treat as publication + FLAG (RULE-0)'; }`

The frozen plan values live in `prereg.lock` (snake_case keys `primary_metric` / `splits` / `analysis_plan`); the `## Preregistration` block (hyphenated `Primary-metric` / `Splits` / `Analysis-plan` fields) lives in `preregistration.md`. Read the frozen primary metric from `prereg.lock` by its `primary_metric` key — read it directly; do not re-derive the primary metric from the runs (that would be HARKing) and do not conflate `prereg.lock` with the `## Preregistration` block (CONVENTIONS §4):
`!{ ls experiments/${exp:-}/prereg.lock experiments/${exp:-}/preregistration.md 2>/dev/null || echo 'NO prereg → confirmatory+ refuses; exploratory proceeds POST-HOC-flagged (RULE-5)'; }`

Enumerate the metrics files and surface how many runs/seeds are available before computing N (the CI's denominator):
`!{ ls experiments/${exp:-}/runs/*/metrics.json 2>/dev/null | wc -l | sed 's/^/metrics.json files found: /'; ls -1 experiments/${exp:-}/runs/ 2>/dev/null; }`

Before presenting any positive finding, confirm the tier-required confound screen passed (RULE-6) — an unaudited positive is reported as unaudited, never as a result. At `pilot` the minimum is `Permutation-null: PASS`; at `confirmatory`+ the full `Survives: YES`:
`!{ grep -RHl -e 'Survives: YES' -e 'Permutation-null: PASS' experiments/${exp:-}/ results/${exp:-}/ 2>/dev/null || echo 'NO confound screen found → positives are UNAUDITED (RULE-6: pilot needs Permutation-null PASS, confirmatory+ needs Survives YES)'; }`

After writing `results/<exp>/analysis.md`, self-lint the emitted `## AnalysisReport` block against the ABI before handing off (the same check `/execute` runs as a hard precondition):
`!{ bash "${CLAUDE_PLUGIN_ROOT}/hooks/block-lint.sh" results/${exp:-}/analysis.md 2>/dev/null || echo 'block-lint not runnable here; verify the six required fields by hand against hooks/block-schemas.tsv'; }`

Figures are produced by the `figure-smith` agent (Task tool), not drawn inline. Pass it: the panel spec (what each panel shows, which is the primary), the dashed random-baseline value, the per-model normalization for any cross-model panel, and the output dir `results/<exp>/figures/`. Record its returned `## FigureReport` verbatim in the `Figures:` line; on `Lint: FAIL`, fix the spec and re-dispatch — figure-smith grades the figure, `/analyze` does not (RULE-1).
