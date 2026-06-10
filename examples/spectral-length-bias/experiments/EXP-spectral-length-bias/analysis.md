<!--
## AnalysisReport for the PRE-AUDIT positive (C-001). This is the finding as it looked BEFORE the
confound-audit — it appears to be a real detector. The /confound-audit (audit.md) and the
results-verifier (verdict.md, produced next) are what retract it. /analyze emits NUMBERS, never a
verdict (RULE-1). No absolute paths (RULE-2).
-->

# Analysis — EXP-spectral-length-bias (claim C-001, pre-audit positive)

The wavelet-band energy logistic classifier reaches held-out balanced_accuracy 0.71 on the
qid-disjoint fold (+0.21 over the 0.50 chance baseline), 95% CI [0.66, 0.76] (bootstrap BCa,
n_resamples=2000, variation source = qid-split). The point estimate is stable across the five seeds.
Against a K=1000 label-permutation null the true statistic sits at z=+6.2 — the classifier clearly
predicts SOMETHING beyond random labels. On its face this looks like a real spectral hallucination
detector.

Scope (RULE-9): measured only on the labelled, ~22%-filtered English proteus-QA distribution with
non-empty H-Neuron trajectories; no claim beyond it. Cross-model pooling uses per-model z-score
normalization (RULE-4). Multiple comparisons: ~50 H-neurons x 4 bands x 18 models = 3600 tests;
Benjamini-Hochberg FDR demands roughly p<1e-5 for the family; the pre-registered primary comparison
(the pooled held-out balanced_accuracy) clears it with p_adj=4e-6.

CAVEAT (carried forward to the audit, NOT resolved here): the answer-length confound was pre-named in
hypothesis.md and the raw length statistics were logged in RUN-001/metrics.json (median length 142
hallucinated vs 38 faithful; feature~length Spearman rho 0.79). RULE-6 makes the four-probe
confound-audit MANDATORY on this positive before it can be claimed. /analyze hands these numbers to
the audit and the results-verifier; it does not grade them.

## AnalysisReport
- Experiment: EXP-spectral-length-bias
- Primary-metric: balanced_accuracy = 0.71 (held-out, qid-disjoint fold; chance baseline = 0.50; read from prereg.lock, post_hoc=false)
- Effect-size: balanced-accuracy delta over chance = +0.21 (95% CI [0.18, 0.24]); baseline_ref = chance=0.50
- CI: [0.66, 0.76] ; method: bootstrap-BCa, n_resamples=2000 ; variation source: split (qid-split, bootstrap over qids) ; n=18 models / 412 held-out qids
- Correction: benjamini-hochberg (FDR) ; N=3600 comparisons (~50 H-neurons x 4 bands x 18 models) ; adjusted primary statistic p_adj=4e-6 (clears the ~1e-5 FDR threshold)
- Figures: results/EXP-spectral-length-bias/figures/fig1_balacc_vs_chance.svg ; results/EXP-spectral-length-bias/figures/C-001_perm_null.png
