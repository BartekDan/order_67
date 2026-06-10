---
experiment: EXP-spectral-length-bias
artifact: design
version: "1"
created: 2026-05-18
rigor_tier: confirmatory
prereg_hash: 99469b2541cfa06a7607e32d1e392264b8a228cf6405d22c7ae0a69c04736b80
hypotheses: [H-001]
---

# Design — `EXP-spectral-length-bias`

> One falsifiable line: if `H-001` is true we will see `held-out balanced_accuracy cross the 0.65
> line and stay above chance after the answer-length control`; if false we will see `balanced
> accuracy at or near 0.50 (chance), or a positive that collapses to ~0.53 once answer length is
> screened out`. The rest of this document is how we look without fooling ourselves.

## Quicklook

The single inspectable number Task 1 emits is the **held-out balanced_accuracy of the wavelet-band
energy logistic classifier** on a thin slice: 1 model's H-Neurons x a 200-question qid-disjoint
held-out slice, single seed (0). Axes for the companion one-panel figure: x = decision threshold,
y = balanced accuracy, with the 0.50 chance line dashed; "signal" is the operating point sitting
clearly above the dashed line. It should take ~1-2 wall-clock hours (activation extraction for one
model + DWT featurization + a single logistic fit), not the full 18-model sweep. If it comes back at
or below 0.52 the wedge is dead and we write the null before burning GPU budget.

**The inspectable:**

```
Kind:        metric
Artifact:    ${CLAUDE_PROJECT_DIR}/experiments/EXP-spectral-length-bias/runs/RUN-001/metrics.json:held_out_balanced_accuracy
Reads:       proteus-hneurons-qa@sha256:7c1d3e9a... , 1 model, qid-disjoint held-out slice n=200, single seed 0
Shows:       held-out balanced_accuracy of the wavelet-band-energy logistic classifier vs the 0.50 chance line
Signal line: balanced_accuracy > 0.60 on the thin slice ⇒ keep going (scale to 18 models, seed sweep)
Kill line:   balanced_accuracy <= 0.52 ⇒ null, write it up, do not scale
Wall-clock:  ~1-2 hours (one-model thin slice; NOT the full run)
```

## Methods

**Measurement** — For each H-Neuron, its activation trajectory `x[1..T]` across the tokens of an
answer is the raw signal. Trajectories vary in length T (answers differ in token count), so each is
resampled to a fixed length of 32 samples; a Daubechies-4 discrete wavelet transform (3 levels) then
yields 4 wavelet-band energies (one approximation/DC band + three detail bands) per
`(sample, layer, neuron)`. The feature vector for a sample concatenates these band energies across
the screened H-Neurons and layers.

**Estimator / model** — An L2-regularized logistic classifier predicting HALLUCINATED vs FAITHFUL
from the wavelet-band energy features. It is fit on the TRAIN fold only; every reducer/standardizer
is fit inside the cross-validation loop on train folds, never on combined or held-out data
(RULE-10). The held-out fold is qid-disjoint and read exactly once for the headline metric.

**Primary metric** — `balanced_accuracy` on the qid-disjoint held-out fold (the single
pre-registered metric the verifier grades; chance baseline = 0.50). The 95% CI is taken over the
qid-split (the named variation source) by bootstrap BCa with n_resamples=2000; the effect size is the
balanced-accuracy delta over chance (RULE-7). Because ~50 neurons x 4 bands x 18 models = ~3600
hypotheses are screened, the family is FDR-corrected (Benjamini-Hochberg, N=3600) and the adjusted
primary statistic is reported (RULE-3). n=18 models is the cross-model unit; per-model balanced
accuracies are aggregated after per-model standardization (RULE-4).

## Design-Decision-Records (DDR)

### D-001 — Fixed-length-32 resampling of variable-length trajectories (the choice that gates scaling)

To put every answer's H-Neuron trajectory on a common spectral basis, trajectories of variable token
length T are resampled to a fixed length of 32 before the DWT. The alternative considered was a
length-invariant wavelet-scattering transform (no resampling). We accepted fixed-32 resampling for
its simplicity and cheap DWT, while explicitly noting the trade-off: **resampling to a constant
length can entangle the DC/low-frequency band energy with the original answer length**, which is the
exact threat the confound-audit must screen. A flip here — adopting the length-invariant scattering
transform as primary — would force a `/register` round-trip (it changes the primary feature
definition, RULE-5). This is the load-bearing methodological choice that gates scaling to the
expensive 18-model confirmatory sweep, and it is deliberately mirrored as the statistic-swap and
alt-preprocessing legs of the confound-audit.

## Data & Compute Plan

**Datasets & splits**

| Dataset | Version hash | Role | Split (by unit) | Rows / size |
|---|---|---|---|---|
| `proteus-hneurons-qa` | `sha256:7c1d3e9a...` | train | by qid, disjoint files | ~14k answers / 18 models |
| `proteus-hneurons-qa` | `sha256:7c1d3e9a...` | held-out | by qid, disjoint files (no qid straddles) | ~3.5k answers / 18 models |

**Seeds**

| Tier | Seeds | N-justification |
|---|---|---|
| confirmatory | `[0,1,2,3,4]` | k=5: to detect a balanced-accuracy delta of 0.10 over chance at alpha=0.05, power=0.8 on the qid-split, k>=4 required; k=5 for margin (RULE-7/RULE-8). Headline CI variation source is the qid-split; seeds confirm stability. |

**Compute budget (hard cap — /execute halts here)**

| Resource | Cap | Notes |
|---|---|---|
| GPU-hours | `12` | A100-class; remote host owned by harness via host-config.json |
| USD | `$36` | ~12 GPU-h x ~$3/GPU-h |
| Wall-clock (min) | `720` | whole tree incl. seed sweep + confound-audit re-runs |

Remote execution: harness owns the `scp → launch → poll → fetch` loop via
`${CLAUDE_PROJECT_DIR}/experiments/EXP-spectral-length-bias/host-config.json` (gitignored; creds by
env name only).

## Threats-to-Validity / out-of-scope

**Threats to validity** (these seed the confound-audit; RULE-6):

- **Leakage / contamination** — a qid could straddle the train/held-out boundary, or a
  reducer could be fit on combined data, manufacturing apparent skill. Guarded by the qid-disjoint
  split (files are physically disjoint by qid) and by fitting all reducers on the train fold inside
  the CV loop. (This is checked by /data-audit and is expected to PASS — the failure mode here is
  NOT leakage.)
- **ANSWER LENGTH (pre-named primary confound)** — hallucinated answers are suspected to be
  systematically longer than faithful ones (longer answers drift, hallucinate more). The wavelet
  DC/low-frequency band energy approximates mean signal magnitude and so correlates with answer
  length; the fixed-length-32 resampling (D-001) further entangles length with the spectral
  features. A classifier could therefore detect LENGTH, not hallucination. **Planned nuisance
  screen:** Mann-Whitney U on answer length across hallucinated vs faithful; feature~length Spearman
  rho; then regress length out / length-stratify and re-score balanced accuracy. If it collapses to
  chance, the finding is the length confound.
- **Statistic fragility** — the effect may exist only for the fixed-32 DWT band-energy statistic.
  **Planned statistic-swap:** recompute with length-invariant wavelet-scattering features; the
  conclusion must hold under the swap.
- **Dataset-distribution / selection** — answers are heavily filtered (only QA pairs with a clean
  hallucinated/faithful label survive). Any detection claim is scoped to that filtered distribution
  (RULE-9); the planned alt-preprocessing re-run (drop the fixed-32 resampling) bounds how much the
  effect depends on the resampling artifact.

**Out of scope** (claims this experiment does NOT license):

- Generalization beyond the labelled, filtered proteus QA distribution (no claim about open-ended
  generation or other domains).
- A mechanistic claim that H-Neuron spectra *cause* hallucination — this experiment can at most show
  a correlation between a spectral feature and the label.
- Any raw cross-model comparison without the declared per-model normalization (RULE-4).

## Risks

- Remote host preempted mid-extraction → checkpoint activation dumps per model; resume by model id.
- DWT featurization OOM on long trajectories → cap T before resampling; logged in config.

---

## DesignDraft
- Experiment: EXP-spectral-length-bias
- Quicklook: held_out_balanced_accuracy of the wavelet-band-energy logistic classifier on a 1-model x n=200 qid-disjoint thin slice, single seed (RUN-001/metrics.json) vs the 0.50 chance line; signal>0.60, kill<=0.52
- DDR-count: 1 (D-001 — fixed-length-32 resampling; the scaling-gating choice, mirrored by the statistic-swap/alt-preprocessing audit legs)
- Datasets: proteus-hneurons-qa @ sha256:7c1d3e9a... ; train + held-out, split by qid (disjoint files), 18 models
- Compute-plan: max_gpu_hours=12 · max_usd=36 · max_wallclock_min=720 ; seeds=[0,1,2,3,4] (confirmatory, k=5 power-justified)
- Threats: answer-length confound (DC-band energy ~ length; pre-named primary nuisance screen) · statistic-fragility (length-invariant scattering swap) · alt-preprocessing (drop fixed-32 resampling) · leakage guarded by qid-disjoint split + train-fold-only reducers (expected PASS)
