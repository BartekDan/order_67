<!--
Canonical persisted ## Preregistration block (CONVENTIONS §4). Written by /register, read by
/design-experiment, /analyze, /paper, /brief. The hashed plan BODY lives separately in prereg.lock;
this block carries the hyphenated mechanical fields. Prereg-hash == prereg.lock prereg_sha256.
-->

# Preregistration — EXP-spectral-length-bias

## Preregistration
- Experiment: EXP-spectral-length-bias
- Hypotheses: H-001 — wavelet-band energy of H-Neuron activation trajectories detects HALLUCINATED vs FAITHFUL answers
- Primary-metric: balanced_accuracy (held-out, qid-disjoint fold; chance baseline = 0.50)
- Splits: by qid, disjoint files (train and held-out share no question id; no row straddles a fold); n=18 models is the cross-model unit; reducers/standardizers fit on the train fold only, inside the CV loop (RULE-10)
- Analysis-plan: Per H-Neuron, resample activation trajectory x[1..T] to fixed length 32, Daubechies-4 DWT (3 levels) -> 4 wavelet-band energies per (sample, layer, neuron). L2-regularized logistic classifier on those features; score balanced_accuracy on the qid-disjoint held-out fold. 95% CI by bootstrap BCa over qids (n_resamples=2000), variation source = qid-split; effect size = balanced-accuracy delta over chance=0.50. Multiple comparisons ~50 neurons x 4 bands x 18 models = ~3600 tests; correction = Benjamini-Hochberg (FDR), N=3600. Seeds=[0,1,2,3,4]. Mandatory RULE-6 confound-audit on any positive: label-permutation null (K=1000) + answer-length nuisance screen + length-invariant scattering statistic-swap + drop-fixed-length-32 alt-preprocessing; thresholds frozen before any probe.
- Prereg-hash: 99469b2541cfa06a7607e32d1e392264b8a228cf6405d22c7ae0a69c04736b80
- Rigor-tier: confirmatory
