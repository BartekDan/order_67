# Confound audit — C-001 @ EXP-spectral-length-bias

- **Finding under audit:** C-001: a logistic classifier on Daubechies-4 (fixed-length-32) wavelet-band energy features of H-Neuron activation trajectories detects HALLUCINATED vs FAITHFUL answers at held-out balanced_accuracy 0.71 (+0.21 over chance=0.50).
- **Rigor tier:** confirmatory
- **Primary statistic:** balanced_accuracy (matches prereg primary metric)
- **Split (leakage-safe per ## DataAudit PASS):** qid-disjoint files, qid-grouped CV, reducers fit on train fold only
- **Source runs:** RUN-001 (the T-004 confirmatory seed sweep that produced the positive)
- **Auditor:** /confound-audit · **Independent verdict owner:** results-verifier (this report does NOT grade — RULE-1)

---

## 1. FROZEN THRESHOLDS  (written 2026-05-28T14:03:11Z — BEFORE any probe was computed)

> Commit to "what counts as surviving" while blind to the outcomes. This timestamp precedes every
> per-probe section below.

| Probe | Frozen threshold to SURVIVE | Value chosen | Rationale (pre-outcome) |
|-------|------------------------------|--------------|--------------------------|
| 1 · Permutation-null | true statistic must lie `|z| >= z*` vs the shuffle null | `z* = 3.0`, `K = 1000` | confirmatory floor; z*=3.0 (~3 sigma) is the minimum to claim the classifier predicts anything beyond random labels |
| 2 · Nuisance-screen | confound must NOT be separable: `p >= alpha*` (fail to reject "distributions equal"); AND length-controlled bal-acc CI must exclude chance+margin | `alpha* = 0.05`, test = Mann-Whitney U, nuisance = answer_length_tokens | answer length is the pre-named primary threat: longer hallucinated answers + DC-band-energy~length means the classifier could read length, not hallucination |
| 3 · Statistic-swap | conclusion (sign + direction) holds under the alt statistic, `|Δ| <= t*` | `alt = length-invariant wavelet-scattering features`, `t* = 0.05` (bal-acc) | scattering is the same spectral construct WITHOUT the fixed-32 length entanglement; a real signal survives it |
| 4 · Alt-preprocessing | finding reproduces under the alternative pipeline, effect retained `>= r*%` | `alt pipeline = drop the fixed-length-32 resampling (use native-length DWT)`, `r* = 80` | the fixed-32 resampling is the step suspected of manufacturing the length artifact; a real effect survives dropping it |

- **Gate rule (frozen):** `Survives = YES` iff probes 1 AND 2 AND 3 AND 4 all PASS. No majority vote. An UNSCORABLE probe ⇒ NOT a PASS ⇒ `Survives = NO` + RERUN.
- **Multiple comparisons (RULE-3):** N = 1 nuisance screened x 1 statistic swapped = the screen is a single pre-registered family per probe; correction = Benjamini-Hochberg on the upstream 3600-test feature family (declared in analysis.md), none needed within this 4-probe gate (each probe is one pre-registered test).
- **Permutation grouping (RULE-10):** labels shuffled WITHIN the qid-disjoint fold, never across the test boundary.

---

## 2. PROBE 1 — Label-permutation null

- True statistic: balanced_accuracy = 0.71
- Null distribution over K=1000 shuffles: mean 0.500 ± sd 0.034  (2.5/97.5 percentiles: [0.434, 0.566])
- z = (0.71 − 0.500) / 0.034 = +6.2 · empirical p_perm = (#null >= true + 1)/(K + 1) = 1/1001 ≈ 1.0e-3
- Null histogram: `results/EXP-spectral-length-bias/figures/C-001_perm_null.png`
- **Threshold (frozen):** `|z| >= 3.0` · **Observed:** `|z| = 6.2` · **Verdict: PASS**
- Notes: the true statistic sits far above the shuffled-label null — the classifier predicts SOMETHING real vs random labels. (This is necessary but NOT sufficient: it does not say WHAT is predicted. Probe 2 answers that.)

## 3. PROBE 2 — Nuisance-variable screen

- Nuisance variable(s): answer_length_tokens
- Test: Mann-Whitney U on answer length across HALLUCINATED vs FAITHFUL
- Statistic: medians 142 (hallucinated) vs 38 (faithful) tokens · U-test p = 9.4e-5 (< alpha* = 0.05) — the length distributions ARE strongly separable between the classes
- Feature~length association: Spearman rho = 0.79 between the wavelet DC/low-frequency band energy and answer length
- Effect explained by confound? **yes** — after regressing answer length out (and confirmed by length-stratified scoring), balanced_accuracy collapses to 0.53, 95% CI [0.49, 0.57] ≈ chance
- Optional control: length-regressed re-run → bal-acc 0.53 [0.49, 0.57]; the CI INCLUDES chance+margin, so the controlled effect is indistinguishable from chance
- **Threshold (frozen):** `p >= 0.05` (confound NOT separable) · **Observed:** `p = 9.4e-5` (confound IS separable) AND length-controlled bal-acc CI includes chance · **Verdict: FAIL**

## 4. PROBE 3 — Statistic-swap

- Primary statistic: fixed-32 Daubechies-4 wavelet-band energy → balanced_accuracy 0.71
- Alternative statistic: length-invariant wavelet-scattering features → balanced_accuracy 0.54
- Sign / direction of conclusion holds? **no** · `|Δ| = 0.17` vs frozen tolerance `t* = 0.05` (far exceeds tolerance; the effect vanishes under the length-invariant statistic)
- **Verdict: FAIL** — swapping to the length-invariant scattering statistic drops bal-acc from 0.71 to 0.54 (≈ chance); the effect was an artifact of the length-entangled fixed-32 statistic.

## 5. PROBE 4 — Alternative-preprocessing re-run

- Pipeline A (primary): fixed-length-32 resampling → Daubechies-4 DWT → effect bal-acc 0.71 (delta +0.21)
- Pipeline B (alternative): drop the fixed-length-32 resampling (native-length DWT, no length-normalizing resample) → effect bal-acc 0.55 (delta +0.05)
- Effect retained: (0.55 − 0.50) / (0.71 − 0.50) = 0.05 / 0.21 ≈ 24% vs frozen `r* = 80%`
- **Verdict: FAIL** — dropping the fixed-32 resampling retains only ~24% of the effect; the resampling step manufactures most of the apparent signal (the length artifact).

---

## 6. OVERALL VERDICT

- Probe 1 (permutation-null): PASS
- Probe 2 (nuisance-screen): FAIL
- Probe 3 (statistic-swap): FAIL
- Probe 4 (alt-preprocessing): FAIL
- **Survives (cumulative AND): NO**

> NO: this finding is REJECTED / retracted. The signal is real vs random labels (Probe 1) but it is
> the ANSWER-LENGTH confound, not a hallucination detector (Probes 2–4). trace/EXP-spectral-length-bias.md
> records the retraction (RULE-8 — a retracted finding is still a finding). The downstream
> results-verifier will see this and issue the REJECT `## Verdict` (RULE-1 — this report does not grade).

---

## ConfoundAudit
- Claim: C-001 @ EXP-spectral-length-bias — wavelet-band energy of H-Neuron trajectories "detects" hallucination at held-out balanced_accuracy 0.71 (+0.21 over chance)
- Permutation-null: true stat=0.71; null=0.500±0.034 over K=1000; z=6.2; p_perm=1.0e-3; THRESHOLD |z|>=3.0 (frozen) — PASS
- Nuisance-screen: nuisance=answer_length_tokens; test=Mann-Whitney; U-test medians 142 vs 38, p=9.4e-5; feature~length Spearman rho=0.79; explained-by-confound=yes (length-regressed bal-acc 0.53 [0.49,0.57] ≈ chance); THRESHOLD p>=0.05 (frozen) — FAIL
- Statistic-swap: fixed-32 DWT band energy→length-invariant scattering; conclusion holds=no; |Δ|=0.17 > t*=0.05 (bal-acc 0.71→0.54) — FAIL
- Alt-preprocessing: A=fixed-length-32 resampling→B=drop-resampling (native-length DWT); reproduces=no; retained ≈24% < r*=80% (bal-acc 0.71→0.55) — FAIL
- Survives: NO
