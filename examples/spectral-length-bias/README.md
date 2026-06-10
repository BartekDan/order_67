# Fixture — `EXP-spectral-length-bias` (the proteus Eksperyment-1 self-retraction)

A **worked acceptance experiment** for the order-67 research harness. It faithfully reproduces the
proteus "Eksperyment 1" spectral length-bias self-retraction, end to end, so it exercises the full
pipeline and **proves the confound-audit gate works**. Every artifact is `fixture: true` and is
excluded from real findings.

## What it demonstrates

A spectral feature of H-Neuron activation trajectories *appears* to detect hallucination — and is
then correctly retracted because the signal is an **answer-length confound**, not a hallucination
detector. The fixture's whole point is the contrast between two gates:

- **/data-audit PASSES** — the split is clean. Train/held-out are qid-disjoint files (no qid
  straddles), every reducer/standardizer is fit on the train fold only inside the CV loop, the
  held-out fold is scored exactly once, there is no row leakage, and the secret-scan is clean. The
  failure is **NOT** a leakage event.
- **/confound-audit fails (`Survives: NO`)** — the positive does not survive the nuisance screen.
  This is a *validity* confound, caught by a different gate than leakage. That distinction is the
  reason this fixture exists.

## The finding (and why it dies)

- **H-001:** a Daubechies-4 (3-level) wavelet-band energy feature of fixed-length-32-resampled
  H-Neuron trajectories distinguishes HALLUCINATED from FAITHFUL answers. Prediction: held-out
  balanced_accuracy >= 0.65 (chance 0.50) on a qid-disjoint split.
- **The positive (looks real):** held-out balanced_accuracy = **0.71**, 95% CI [0.66, 0.76]
  (bootstrap BCa, n=2000, variation source = qid-split), effect size **+0.21** over chance,
  permutation-null **z = +6.2** (K=1000). Across 18 models, FDR-corrected (BH, N=3600, p_adj=4e-6).
- **The confound (why it dies):** hallucinated answers are systematically longer (median **142 vs 38**
  tokens, Mann-Whitney p < 1e-4). The wavelet DC/low-frequency band energy approximates mean signal
  magnitude and so tracks length (feature~length Spearman **rho = 0.79**). The fixed-length-32
  resampling further manufactures the artifact.

## The four-probe confound-audit (confirmatory ⇒ full screen, thresholds frozen first)

| Probe | Result | Verdict |
|-------|--------|---------|
| 1 · Permutation-null (K=1000) | true z = +6.2 vs the shuffled-label null | **PASS** (predicts *something* vs random labels) |
| 2 · Nuisance-screen (answer length) | length Mann-Whitney p < 1e-4; feature~length rho 0.79; length-regressed bal-acc collapses to **0.53** [0.49, 0.57] ≈ chance | **FAIL** |
| 3 · Statistic-swap (length-invariant scattering) | bal-acc 0.71 → **0.54** | **FAIL** |
| 4 · Alt-preprocessing (drop fixed-32 resampling) | bal-acc 0.71 → **0.55** (~24% retained) | **FAIL** |

**Survives: NO** — the finding is the length confound.

## Expected outcome (the harness reproduces the proteus retraction)

1. **/data-audit ⇒ `## DataAudit Verdict: PASS`** (leakage clean).
2. **/confound-audit ⇒ `## ConfoundAudit Survives: NO`** (the answer-length nuisance screen fails).
3. **results-verifier ⇒ `## Verdict REJECT`** — NOT `BLOCKED`: the balanced_accuracy WAS logged
   (RUN-001/metrics.json), so the claim is scorable; it is `REJECT` because the logged metric does
   not support the claim "detects hallucination" — the signal is the confound. (`BLOCKED` would mean
   the metric was never logged; that is not this case.)
4. **experiment.json status ⇒ `retracted`** (the verifier moves it from `audited`).

The independent verifier produces `verdict.md` next — it is intentionally NOT included here
(RULE-1: the side that produced the result never self-grades).

## Layout

```
experiments/EXP-spectral-length-bias/
  experiment.json        # state machine: status=audited (verifier → retracted), confirmatory, fixture:true
  hypothesis.md          # H-001 card; answer length is a PRE-NAMED confound
  prereg.lock            # hashed plan body (sha256 99469b25…); RULE-5 freeze
  preregistration.md     # the ## Preregistration block (Prereg-hash == prereg.lock)
  design.md              # ## Quicklook first, methods, Data & Compute Plan, Threats (pre-names length)
  model-info-sheet.md    # Kapoor–Narayanan L1/L2/L3 — all PASS, leakage clean
  data-audit.md          # ## DataAudit Verdict: PASS
  runs.md                # ## RunPlan tree; Evaluate node [x]; T-AUDIT confound-audit node [!]
  runs/RUN-001/          # metrics.json + repro bundle (seed.txt, config.resolved.json, git.commit, env.lock, dataset.hash) — D-004
  analysis.md            # ## AnalysisReport — the pre-audit positive (looks real)
  audit.md               # ## ConfoundAudit — frozen thresholds + 4 probes + Survives: NO
results/EXP-spectral-length-bias/
  stats.json             # machine twin of analysis.md; confound_audit_survives:false; status retracted
  figures/               # fig1_balacc_vs_chance.svg, C-001_perm_null.png
trace/EXP-spectral-length-bias.md   # append-only provenance: C-001 → metric:value → figure → audit → retraction
```
