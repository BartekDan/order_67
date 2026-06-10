# Hypotheses — EXP-spectral-length-bias

Domain: H-Neurons (proteus). Falsifiable cards in `H-NNN` order. Card shape per
`skills/register/templates/hypothesis-card.md`.

---

### H-001 — Wavelet-band energy of H-Neuron activation trajectories detects hallucination

- **Prediction (EARS):** When an L2-regularized logistic classifier on the Daubechies-4 (3-level)
  wavelet-band energy features of H-Neuron activation trajectories is evaluated on the qid-disjoint
  held-out fold (keyed by question id, the unit of scientific interest), it shall achieve
  balanced_accuracy >= 0.65 (chance = 0.50).
  - Variant B (difference form): the balanced-accuracy delta over the 0.50 chance baseline shall be
    >= 0.15 with the pre-registered 95% CI (bootstrap BCa over qids, n=2000) excluding 0.

- **Falsification criterion:** balanced_accuracy on the qid-disjoint held-out fold <= chance + margin
  (i.e. <= 0.55), OR the positive signal is explained by a confound (the confound-audit returns
  `Survives: NO`). Either observation REJECTS H-001. This is the mechanical negation of the
  prediction, gradable by the results-verifier without human judgement.

- **Named confounds** (each maps to one leg of the RULE-6 confound-audit):
  - **label-permutation null** — shuffle hallucinated/faithful labels WITHIN the qid-disjoint fold,
    K=1000 times; the null is the distribution of held-out balanced-accuracy under random labels. A
    true z below z* means the classifier predicts nothing beyond chance.
  - **nuisance screen — ANSWER LENGTH (the pre-named primary confound):** hallucinated answers are
    suspected to be systematically LONGER than faithful ones. The wavelet DC / low-frequency band
    energy approximates mean signal magnitude, which scales with answer length; the fixed-length-32
    resampling further entangles length with the spectral features. Screen: Mann-Whitney U on answer
    length across hallucinated vs faithful, and the feature~length Spearman rho; then regress length
    out / length-stratify and re-score. If balanced-accuracy collapses to chance after the control,
    the "detector" is a length detector, not a hallucination detector.
  - **statistic-swap** — recompute with length-invariant wavelet-scattering features instead of the
    fixed-32-resampled DWT band energies. A real hallucination signal survives the swap; a
    length artifact vanishes.
  - **alt-preprocessing** — drop the fixed-length-32 resampling step (which manufactures the length
    artifact) and re-run. A real effect reproduces; a preprocessing-specific effect does not.

- **Cost:** ~10 GPU-hours (activation extraction + DWT featurization across 18 models) + ~2 GPU-hours
  for the seed sweep and confound-audit re-runs = ~12 GPU-h / ~$36 / ~720 wall-clock min. Fits inside
  the experiment budget (experiment.json:compute.budget).

- **Novelty:** would establish a cheap spectral hallucination detector from internal H-Neuron
  dynamics, not from output text. Closest prior: proteus-internal length/perplexity-based
  hallucination heuristics (which this must beat to be interesting) — the open question is precisely
  whether a spectral feature adds signal BEYOND answer length. No known published spectral-DWT
  hallucination detector on H-Neuron trajectories.

- **Tier:** confirmatory (inherits experiment.json:rigor_tier).
