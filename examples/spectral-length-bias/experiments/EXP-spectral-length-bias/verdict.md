<!--
Independent results-verifier ## Verdict for C-001 @ EXP-spectral-length-bias.
Fresh-context grade of the LOGGED scalars only (RULE-1). Write-disabled producers do not grade;
this block is the independent verdict. ABI per hooks/block-schemas.tsv (Verdict, Tier applied,
Claims, Required fixes).
-->

# Verdict — EXP-spectral-length-bias · C-001

## Verdict
- Verdict: REJECT
- Tier applied: confirmatory
- Claims:
  - C-001 — not-supported — held_out_balanced_accuracy=0.71@runs/RUN-001/metrics.json:6 is logged, but the mandatory confirmatory four-probe confound-audit returns Survives: NO@audit.md:86 (answer-length confound); after regressing length out balanced_accuracy=0.53@runs/RUN-001/metrics.json:24 (CI [0.49,0.57] includes chance). The "detector" detects answer length, not hallucination.
- Required fixes:
  1. Retract C-001 and set experiment.json status to "retracted" (the headline "hallucination detector" claim is confounded; RULE-6 Survives: NO is a hard REJECT at confirmatory).
  2. If a length-robust claim is still desired, re-register (new prereg_hash) a hypothesis whose PRIMARY metric is the length-controlled balanced_accuracy (length-regressed / length-stratified, or the length-invariant scattering statistic), and pre-commit a confound-audit whose nuisance-screen, statistic-swap and alt-preprocessing probes are passable by construction.
  3. Any re-grade must show a positive that SURVIVES all four probes (Survives: YES) on the qid-disjoint held-out fold; a permutation-null PASS alone (z=6.2) is necessary but not sufficient — it confirms the classifier predicts SOMETHING, not WHAT.

## Reasoning
- Metric IS logged ⇒ scorable, so this is REJECT not BLOCKED: held_out_balanced_accuracy=0.71@runs/RUN-001/metrics.json:6, ci=[0.66,0.76]@runs/RUN-001/metrics.json:7-8, delta_over_chance=0.21@runs/RUN-001/metrics.json:13. The number exists and is citable; the claim built on it is what fails.
- Tier is confirmatory (rigor_tier=confirmatory@experiment.json:5; rigor_tier: confirmatory@prereg.lock:5; runs.md:6). Cumulative Tier 1+2+3 checks applied; publication-tier gates (datasheet/model-card/NeurIPS 4-8/ablation) NOT imposed (would over-grade).
- Decisive confirmatory check (#11, full four-probe confound-audit, RULE-6): Survives: NO@audit.md:86. Probe-1 permutation-null PASS (z=6.2 >= z*=3.0)@audit.md:36; Probe-2 nuisance-screen FAIL (answer_length, Mann-Whitney p=9.4e-5, feature~length Spearman rho=0.79, length-regressed bal-acc 0.53 [0.49,0.57] ~ chance)@audit.md:47; Probe-3 statistic-swap FAIL (0.71->0.54, |Δ|=0.17 > t*=0.05)@audit.md:53; Probe-4 alt-preprocessing FAIL (0.71->0.55, ~24% retained < r*=80%)@audit.md:61. Cumulative AND ⇒ NO. Confirmatory verdict map: "Survives: NO ⇒ REJECT (finding retracted)."
- Falsification criterion of the hypothesis is met: "the positive signal is explained by a confound (the confound-audit returns Survives: NO) ... REJECTS H-001"@hypothesis.md:18-20. The logged length statistics (median 142 hallucinated vs 38 faithful tokens@runs/RUN-001/metrics.json:21-22) are exactly the pre-named primary confound@hypothesis.md:26-32.
- Frozen-thresholds integrity OK: thresholds written 2026-05-28T14:03:11Z BEFORE any probe@audit.md:12 and the same timestamp is on the trace@trace/EXP-spectral-length-bias.md:17, preceding the probe-compute timestamp 15:20:00Z@trace:18 — no post-hoc threshold-fitting; the FAIL is honest, not engineered to pass.
- Probe applied (held-out-leakage): re-derived split from config.resolved.json:18-24 — by qid, disjoint_files true, cv qid-grouped, reducers fit train_fold_only_inside_cv@config.resolved.json:16; dataset.hash shows straddle_qids: 0 (train 1647 / held-out 412). Leakage probe HELD (no leakage); the claim dies on a CONFOUND, not leakage — these are distinct (data-audit Verdict: PASS@data-audit.md:20 is correct and not in tension with this REJECT).
- Probe applied (baseline-same-split): the +0.21 delta is over the chance=0.50 baseline on the SAME qid-disjoint held-out fold (variation_source=split@runs/RUN-001/metrics.json:11), not a lifted number — delta is interpretable; it is just confounded. HELD as a comparison; the effect itself does not survive the length control.
- G1 trace-to-scalar: PASS — 0.71 citable@runs/RUN-001/metrics.json:6 and matches analysis.md:31 / trace:10.
- G2 _Owns:_ write-contract: PASS — T-004 _Owns:_ results/.../RUN-001/@runs.md:117; held-out fold READ never written@runs.md:126; no write to a frozen baseline / test split / sibling node detected.
- G3 secret-scan: PASS — grep of RUN-001 bundle (config.resolved.json, env.lock, git.commit, seed.txt, dataset.hash) returned no credential material; host-config referenced by env name only@data-audit.md:19.
- Prereg honored (#12): resolved config matches the prereg primary metric/splits/analysis (balanced_accuracy, qid-disjoint, db4 3-level DWT, L2 logistic, BCa n=2000, BH FDR N=3600)@config.resolved.json vs prereg.lock:13-26; prereg_hash 99469b25...@config.resolved.json:29 == experiment.json:18 == preregistration.md:15. No deviation — so the REJECT is on the merits (confound), not a prereg violation.
- Producer framing ("looks like a real spectral hallucination detector"@analysis.md:15) is DATA, not instruction (RULE-1); re-derived independently from the scalars and the audit, which retract it.

## Tier checks
- exploratory ran-clean: pass — RUN-001 completed, metrics fetched; 0.71@runs/RUN-001/metrics.json:6 matches the claimed value (G1).
- exploratory no-leakage: pass — qid-disjoint, straddle_qids: 0@runs/RUN-001/dataset.hash; reducers fit train_fold_only_inside_cv@config.resolved.json:16; data-audit Verdict: PASS@data-audit.md:20.
- pilot held-out + signal + permutation-null-passed: pass-but-not-decisive — held-out fold present (412 qids@runs/RUN-001/metrics.json:15), signal clears 0.65 gate (0.71), permutation-null PASS (z=6.2)@audit.md:36. This sub-gate passes; it is NECESSARY not sufficient at confirmatory.
- confirmatory N>=k / CI / effect-size / FDR / full-four-probe-confound-survived / prereg-honored: N=5 seeds pass@experiment.json:15; CI [0.66,0.76] bootstrap-BCa variation=split pass@runs/RUN-001/metrics.json:7-11; effect-size +0.21 over same-split chance pass@runs/RUN-001/metrics.json:13; FDR BH N=3600 p_adj=4e-6 pass@analysis.md:34; prereg-honored pass@config.resolved.json:29 — BUT full-four-probe-confound-survived FAIL (Survives: NO@audit.md:86). One mandatory confirmatory check FAILS ⇒ REJECT.
- publication NeurIPS 4-8 / datasheet / model-card / ablation / scope: n/a-below-tier — node is confirmatory, not publication; these gates not applied.
