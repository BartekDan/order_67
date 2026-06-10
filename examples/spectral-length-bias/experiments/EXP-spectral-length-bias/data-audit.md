<!--
## DataAudit block (CONVENTIONS §4), written by /data-audit from the model-info-sheet roll-up.
The point of this fixture: leakage is CLEAN ⇒ Verdict PASS. The finding still dies later at
/confound-audit on the answer-length confound — a confound is a validity threat, NOT a leakage
event. Keep that contrast intact. No absolute paths (RULE-2).
-->

# Data Audit — EXP-spectral-length-bias

Source: `experiments/EXP-spectral-length-bias/model-info-sheet.md` (Kapoor-Narayanan protocol).
The three section verdicts and pointers are copied verbatim into the block below.

## DataAudit
- Experiment: EXP-spectral-length-bias
- L1: PASS — train/test contamination clean: physically qid-disjoint train/held-out files, no qid straddles (tests/test_split.py::test_no_qid_straddle); all reducers/standardizers + the H-Neuron screen + the logistic C-search fit on the TRAIN fold only inside the CV loop (src/featurize.py, src/cv.py); held-out scored exactly once for the headline; 0 cross-fold duplicate rows; labels are per-answer, not from full-dataset statistics (RULE-10).
- L2: PASS — no illegitimate/label-leaking feature: features are wavelet-band energies, none a label proxy (max |r| with label ~0.34, well under the 0.95 tripwire); activations from frozen models that never saw the labels; no temporal/provenance leakage. Answer-length nuisance is PRESENT and confounded with the label, but it is a validity confound pre-named in hypothesis.md and DEFERRED to the mandatory /confound-audit nuisance screen (RULE-6) — not a leakage event.
- L3: PASS — sampling/scope hygiene clean: qid-disjoint with a hash-uniform fold assignment (no split-induced shift); label-independent filtering (~22% drop on missing-label/empty-trajectory, survivorship ruled out); variation/CI unit is the qid (bootstrap over qids), deflating effective N below the row count; cross-model claims use per-model z-score normalization (RULE-4); scope bounded to the labelled English proteus-QA distribution (RULE-9).
- Leakage-checks: qid-disjoint split (no straddle) [pass]; reducers fit train-fold-only inside CV [pass]; held-out used once [pass]; no near-duplicate rows across folds [pass, 0 found]; labels not from global statistics [pass]; activations from models blind to labels [pass]. No row-leakage path detected.
- Secret-scan: clean — no credentials/tokens/keys in committed config or run artifacts; host-config.json is gitignored and references creds by env name only; scanned RUN-001 bundle (config.resolved.json, env.lock, git.commit) — no secret material.
- Verdict: PASS
