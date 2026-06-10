# Model Info Sheet — Leakage Protocol (Kapoor-Narayanan)

> Filled for EXP-spectral-length-bias. The point of this fixture: the split is CLEAN (no leakage),
> so this audit PASSES. The finding nonetheless dies later at /confound-audit on the ANSWER-LENGTH
> confound (L2.6 flags the nuisance as present-but-screened-downstream, which is legitimate at audit
> time — a confound is a validity threat, not a leakage event).

- **Experiment:** EXP-spectral-length-bias
- **Dataset(s) under audit:** proteus-hneurons-qa @ sha256:7c1d3e9a4b86f0d2a55e1c47b9f0a2d6e8c41f73b2a9d05e6c8147af3b0d9e2c
- **Rigor tier:** [x] confirmatory
- **Filled by:** research-harness (fixture)   **Date (ISO-8601):** 2026-05-19
- **Split unit of scientific interest:** [x] qid

---

## L1 — Train / test contamination

- **L1.1 — Does a separate held-out partition exist, defined before any model touched the data?**
  Answer / evidence: Yes. `proteus-hneurons-qa` ships as physically disjoint train/held-out files
  partitioned by qid; the partition was fixed at dataset build time, recorded in `dataset.hash`,
  and frozen in prereg.lock before any classifier was fit.

- **L1.2 — Is every preprocessing step fit on the training fold only?**
  Answer / `file:line`: Yes. The StandardScaler and the DWT-energy normalizer are fit on train-fold
  rows only, inside the CV loop (`src/featurize.py:make_pipeline` constructs `Pipeline([scaler,
  logreg])` and calls `.fit(X_train)` per fold; never `.fit(X_all)`).

- **L1.3 — Is feature selection / hyperparameter search performed inside the CV loop?**
  Answer / `file:line`: Yes. The H-Neuron screen and the logistic C-search run inside each train
  fold (`src/cv.py:nested_cv`, inner loop on train only); no selection touches the held-out fold.

- **L1.4 — Duplicate / near-duplicate rows in both train and test?**
  Answer / count: 0. Dedup by (qid, answer-hash) before splitting; the qid grouping guarantees no
  answer's qid appears in both partitions (verified: train∩held-out qids = empty set).

- **L1.5 — For grouped data, are all rows sharing a qid confined to a single partition?**
  Answer / evidence: Yes — no straddling. Partition is BY qid, so every answer of a given question
  lives entirely in one fold (`tests/test_split.py::test_no_qid_straddle` asserts disjointness).

- **L1.6 — Was any label computed using full-dataset statistics?**
  Answer: No. The hallucinated/faithful label is per-answer, assigned at dataset build time from the
  reference QA judgement; no global mean/threshold feeds it.

- **L1.7 — Is the test partition used exactly once, at the end, for the headline metric?**
  Answer: Yes. Held-out is scored once for the headline balanced_accuracy; model/feature/threshold
  selection all happen on train folds (L1.3).

**L1 section verdict:** [x] PASS

---

## L2 — No illegitimate / label-leaking features

- **L2.1 — Is any feature a proxy for, or derived from, the label?**
  Answer: No. Features are wavelet-band energies of H-Neuron activation trajectories; none is derived
  from the hallucinated/faithful label.

- **L2.2 — Label-correlation screen: which features exceed the pre-set |r| threshold?**
  Threshold |r| >= 0.95 (a proxy-for-label tripwire): none. The strongest single feature reaches
  |r| ~ 0.34 with the label — no feature is a deterministic label proxy. (NOTE: the DC-band energy
  correlates strongly with answer LENGTH, not the label directly — that is the downstream confound,
  screened by /confound-audit, not a leakage event here.)

- **L2.3 — Features computed after the event the label describes (temporal leakage)?**
  Answer: No. Activations are recorded during the answer generation the label scores; no future
  signal enters the feature.

- **L2.4 — Does any feature encode the collection process (file index, ordering, batch id)?**
  Answer: No. Features are activation-derived only; sample/file order is shuffled before featurizing.

- **L2.5 — For activation features: extracted from a model/layer/run that did not see the test labels?**
  Answer / source run: Yes — clean. Activations come from the frozen proteus models doing inference;
  the models never trained on the hallucinated/faithful labels (source: `runs/RUN-001/dataset.hash`).

- **L2.6 — Is a nuisance variable confounded with the label, and is it controlled or screened?**
  Nuisance var(s): ANSWER LENGTH (token count). Control: PRESENT and confounded — hallucinated
  answers are systematically longer than faithful ones, and the DC/low-frequency band energy tracks
  length. This is a *validity* confound, not a leakage event: it is explicitly pre-named in
  hypothesis.md and is SCREENED downstream by the mandatory /confound-audit nuisance probe (RULE-6),
  not by the split. Flagged here, deferred to the audit by design.

- **L2.7 — Is the baseline a legitimate comparator?**
  Answer: Yes. Baseline = 0.50 balanced-accuracy chance on the balanced held-out fold; the
  length-only logistic baseline is computed in the audit (it reaches the same ~0.71, which is the
  whole point).

**L2 section verdict:** [x] PASS  *(answer-length confound noted; it is a confound-audit matter, not leakage)*

---

## L3 — Sampling / population-scope hygiene

- **L3.1 — Group disjointness flag: where is it set?**
  Flag + `file:line`: `tests/test_split.py::test_no_qid_straddle` asserts train and held-out qid sets
  are disjoint; the partition manifest sets `split_by: qid, disjoint: true`.

- **L3.2 — Same distribution across the train/test draw?**
  Answer: Yes. qids assigned to folds by a fixed hash of the qid (uniform), so the train and held-out
  draws share the same answer-type and label-prior distribution; no distribution shift introduced by
  the split itself.

- **L3.3 — What filtering was applied, and is the surviving distribution representative?**
  Drop-rate: ~22% of raw QA pairs dropped (no clean label, or empty trajectory). Surviving scope:
  labelled proteus QA answers with a non-empty H-Neuron trajectory, English subset. Claims are scoped
  to THIS distribution (RULE-9), stated in design.md Out-of-scope.

- **L3.4 — Test set from the same population as the claim target?**
  Answer: Yes. Held-out qids are drawn from the same labelled QA pool, not an easier subset.

- **L3.5 — Is selection-on-the-outcome (survivorship) ruled out?**
  Answer: Yes. The drop criteria (L3.3) are label-independent (missing label OR empty trajectory),
  applied before the split, so survivorship does not select on the hallucinated/faithful outcome.

- **L3.6 — Dependencies across "independent" samples that inflate effective N?**
  Answer: Effective N vs nominal N: answers sharing a qid are dependent, so the variation unit for
  the CI is the qid (bootstrap over qids), NOT the answer row — this deflates the effective N to the
  number of held-out qids and is honored by the qid-bootstrap CI (RULE-7/RULE-10).

- **L3.7 — Cross-model normalization explicit (RULE-4)?**
  Normalization: per-model z-score of the wavelet-band energies before pooling across the 18 models;
  per-model balanced accuracies aggregated after standardization. No raw cross-model number is used.

**L3 section verdict:** [x] PASS

---

## Roll-up (feeds the `## DataAudit` block)

| Section | Verdict | Justification pointer |
|---------|---------|------------------------|
| L1 | PASS | this file #L1 — qid-disjoint files, reducers fit train-fold-only, held-out scored once |
| L2 | PASS | this file #L2 — no label-proxy feature; answer-length confound noted + deferred to /confound-audit |
| L3 | PASS | this file #L3 — qid-disjoint, label-independent filtering, qid-bootstrap unit, per-model z-score |
