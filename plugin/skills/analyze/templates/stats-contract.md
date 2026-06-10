# Stats contract — what a headline claim must carry (`/analyze`)

Read by `/analyze` when it writes `results/<exp>/stats.json` + `results/<exp>/analysis.md`, and by the **results-verifier** when it grades the `## AnalysisReport`. This is the checklist a headline claim (`C-NNN`) must satisfy before it can be reported as a *result*. It operationalizes RULE-3, RULE-4, RULE-7, RULE-8, RULE-9. The contract is **tier-cumulative** (CONVENTIONS §2): each tier adds to the one below; the top tier is never imposed on exploratory work. A claim that fails its tier's contract is reported as a candidate, never a finding — and `/analyze` never grades it (RULE-1); it hands the numbers to the verifier.

---

## The six required statistics for a confirmatory+ headline claim

A claim presented as a result at `confirmatory` or `publication` MUST carry all six. Each maps to a `## AnalysisReport` field and a `stats.json` key.

| # | Statistic | Rule | `## AnalysisReport` field | `stats.json` keys |
|---|-----------|------|---------------------------|-------------------|
| 1 | **Pre-registered primary metric**, read from `prereg.lock` (not re-derived from runs) | RULE-5 | `Primary-metric:` | `metric`, `post_hoc:false` |
| 2 | **Point estimate + 95% CI** | RULE-7 | `CI:` | `mean`, `ci_low`, `ci_high` |
| 3 | **Named variation source** the CI is taken over (seed / init / split) | RULE-7 | `CI:` (`variation source: …`) | `variation_source`, `n` |
| 4 | **Named CI method** (bootstrap[BCa/percentile, n_resamples] or closed-form[assumption]) | RULE-7 | `CI:` (`method: …`) | `ci_method` |
| 5 | **Effect size over a declared baseline** (Cohen d / R² / balanced-accuracy Δ) — NOT a bare p | RULE-7 | `Effect-size:` | `effect_size_kind`, `effect_size`, `effect_size_ci`, `baseline_ref` |
| 6 | **Multiple-comparisons correction** (Holm / BH) with N stated + adjusted primary statistic | RULE-3 | `Correction:` | `correction`, `n_comparisons`, `p_adj` |

**Plus, conditionally:**
- **Cross-model normalization** — required for ANY claim that compares across models (RULE-4). Name it (relative depth / per-model z-score / PCA-to-common-dim / Procrustes). `## AnalysisReport` `Cross-model-norm:` line; `stats.json` `cross_model_norm`. A raw cross-model number is not a result.
- **Confound-audit survival** — required for any POSITIVE claim (RULE-6). The `## ConfoundAudit` for the claim must read `Survives: YES`. `stats.json` `confound_audit_survives:true`. A positive without it is reported as *unaudited*.
- **Scope** — every claim states the (often filtered) data distribution it was measured on (RULE-9). `stats.json` `scope`; `analysis.md` prose.
- **Null handling** — a null is a result (RULE-8). A clean null needs a power justification (the achieved N detects the minimum effect of interest); an underpowered null is flagged "not a clean null". `stats.json` `null_result`, `powered`.

---

## What counts as each statistic (so the verifier and `/analyze` agree)

**Effect size (pick the one the metric implies; never report a bare p as the effect):**
- **Cohen's d** — standardized mean difference between condition and baseline; report with its 95% CI. Rough reading: 0.2 small / 0.5 medium / 0.8 large — but interpret in context, not by the cutoff.
- **R²** — variance explained, for regression/probing-by-regression claims; report adjusted R² when predictors were selected.
- **Balanced-accuracy Δ** — (balanced) accuracy of the model minus the *named* baseline (chance / majority / published). Use balanced accuracy, not raw accuracy, on imbalanced labels.

**CI method (name exactly one):**
- **bootstrap** — resample the *variation unit* (e.g. seeds, or qids for a by-question split), report BCa or percentile and `n_resamples` (≥ 2000 for a 95% interval). The bootstrap unit MUST be the variation source named in stat #3.
- **closed-form** — t-interval / normal approximation; state the distributional assumption and why it holds (e.g. "n=12 seeds, metric approx. normal by Q-Q").

**Variation source (name exactly one; they answer different questions):**
- **seed** — run-to-run stochasticity at fixed data/init.
- **init** — sensitivity to weight/probe initialization.
- **split** — sensitivity to the train/test partition (cross-validation folds; split by the unit of scientific interest, never by row — RULE-10).
Mixing sources into one undifferentiated "± 0.04" is rejected.

**Correction (when N_comparisons > 1):**
- **Holm** — controls family-wise error; conservative, use when any false positive is costly.
- **Benjamini–Hochberg** — controls false-discovery rate; use for a screen where some false positives are tolerable.
State N (the number of comparisons in the family), and report the adjusted statistic for the pre-registered primary comparison. For a single pre-registered comparison, `Correction: n/a — single pre-registered comparison` is correct (no correction needed).

---

## Tier-cumulative contract (apply exactly the active tier — RULE-0 forces strict only on a MISSING tier)

| Tier | Required for a headline claim |
|------|-------------------------------|
| `exploratory` | Descriptive stats (mean/spread) + ≥1 honest figure with a dashed chance baseline. A single seed is OK. **No CI / effect-size / correction required** — demanding them here is the bloat the tier system removes. Any cross-tier number is labeled candidate/post-hoc. |
| `pilot` | + a held-out split exists and is used; + a `signal_confirmed` note before scaling to expensive runs. CI/effect-size still optional but encouraged. |
| `confirmatory` | + all SIX required statistics above; + N≥k seeds with k justified (power); + FDR/FWER correction with N stated; + confound-audit survival on positives; + cross-model normalization where applicable. **A prereg deviation HARD-BLOCKS PROMOTE here.** |
| `publication` | + everything in confirmatory, plus: full reproducibility evidence (the `## ReproReport` exists and passes), an ablation-completeness note, and the figure provenance (script + commit) recorded for every figure. The NeurIPS items 4–8 must be answerable Yes-with-evidence. |

A **missing/unknown tier** ⇒ apply the `publication` contract AND flag it as a blocking gap (RULE-0). A present *lower* tier is honored as-is — never silently upgraded.

---

## `stats.json` shape (one object per claim)

```json
{
  "experiment": "EXP-<slug>",
  "claims": [
    {
      "claim_id": "C-001",
      "metric": "balanced_accuracy",
      "post_hoc": false,
      "n": 12,
      "variation_source": "seed",
      "mean": 0.713,
      "ci_low": 0.689,
      "ci_high": 0.741,
      "ci_method": "bootstrap-BCa",
      "n_resamples": 5000,
      "effect_size_kind": "bal_acc_delta",
      "effect_size": 0.213,
      "effect_size_ci": [0.181, 0.244],
      "baseline_ref": "chance=0.5",
      "correction": "benjamini-hochberg",
      "n_comparisons": 8,
      "p_adj": 0.004,
      "cross_model_norm": "relative_depth",
      "confound_audit_survives": true,
      "null_result": false,
      "powered": true,
      "scope": "qids with answer_len in [5,40] tokens; English subset only",
      "tier_applied": "confirmatory",
      "figure": "results/EXP-<slug>/figures/fig1_depth_curve.svg"
    }
  ]
}
```

A null result keeps the same shape with `null_result:true`, `effect_size` near 0 with a CI that contains the null, and `powered:true|false` (false ⇒ flag "not a clean null", RULE-8).

---

## Verifier-facing self-check (before `/analyze` hands off)

1. The primary metric came from `prereg.lock`, not from scanning the runs for the best one (RULE-5).
2. The CI line names BOTH a variation source AND a method; the bootstrap unit == the variation source (RULE-7).
3. The headline is an effect size over a *named* baseline, never a bare p (RULE-7).
4. If >1 comparison: a correction is applied, N is stated, the adjusted primary statistic is reported (RULE-3).
5. Any cross-model claim names its normalization; no raw cross-model number appears (RULE-4).
6. Every positive claim has a `Survives: YES` confound-audit, else it is marked unaudited (RULE-6).
7. Every claim states its distribution scope (RULE-9); nulls carry a power judgment (RULE-8).
8. The active tier's contract — and only that tier's — was applied; a missing tier was treated as publication AND flagged (RULE-0).
9. `stats.json` and `analysis.md` agree number-for-number; every figure value traces to a `stats.json` field.
10. `/analyze` emitted numbers, not a verdict (RULE-1).
