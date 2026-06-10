# Trace — EXP-spectral-length-bias  (append-only provenance; RULE-1/RULE-8; no absolute paths RULE-2)

Mechanical provenance for the spectral length-bias fixture. Each line is append-only. Claims (C-NNN)
point at the run metric, the figure, and the confound-audit that grades them.

- 2026-05-18T09:12:04Z: register → prereg.lock sha256=99469b2541cfa06a7607e32d1e392264b8a228cf6405d22c7ae0a69c04736b80 ; rigor_tier=confirmatory ; H-001
- 2026-05-19T10:40:00Z: data-audit → experiments/EXP-spectral-length-bias/data-audit.md ## DataAudit Verdict=PASS (qid-disjoint, train-fold-only reducers, no row leakage, secret-scan clean)
- 2026-05-22T16:05:00Z: Write → results/EXP-spectral-length-bias/RUN-001/metrics.json (T-004 confirmatory seed sweep)
- 2026-05-22T16:05:00Z: claim C-001 ASSERTED (pre-audit positive)
    - metric: results/EXP-spectral-length-bias/RUN-001/metrics.json:held_out_balanced_accuracy = 0.71
    - ci: [0.66, 0.76] bootstrap-BCa n=2000, variation_source=split (qid-split), n=18 models / 412 held-out qids
    - effect_size: balanced_accuracy_delta_over_chance = +0.21 (baseline chance=0.50)
    - figure: results/EXP-spectral-length-bias/figures/fig1_balacc_vs_chance.svg
    - permutation_null_z: 6.2 (K=1000)
    - correction: benjamini-hochberg, N=3600, p_adj=4e-6
    - analysis: experiments/EXP-spectral-length-bias/analysis.md ## AnalysisReport
- 2026-05-28T14:03:11Z: confound-audit FROZEN thresholds written (before any probe) → experiments/EXP-spectral-length-bias/audit.md
- 2026-05-28T15:20:00Z: confound-audit → experiments/EXP-spectral-length-bias/audit.md ## ConfoundAudit
    - probe1 permutation-null: PASS (z=6.2 >= z*=3.0)
    - probe2 nuisance-screen (answer_length): FAIL (median 142 vs 38 tokens, Mann-Whitney p=9.4e-5; feature~length Spearman rho=0.79; length-regressed bal-acc 0.53 [0.49,0.57] ≈ chance)
    - probe3 statistic-swap (length-invariant scattering): FAIL (bal-acc 0.71→0.54)
    - probe4 alt-preprocessing (drop fixed-32 resampling): FAIL (bal-acc 0.71→0.55, ~24% retained)
    - figure: results/EXP-spectral-length-bias/figures/C-001_perm_null.png
    - Survives: NO
- 2026-05-28T15:25:00Z: claim C-001 RETRACTED — the signal is the ANSWER-LENGTH confound, not a hallucination detector (RULE-6). Routed to results-verifier for the REJECT ## Verdict (RULE-1). experiment.json status: audited → (verifier) retracted.
