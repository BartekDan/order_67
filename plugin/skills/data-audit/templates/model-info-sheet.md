# Model Info Sheet — Leakage Protocol (Kapoor–Narayanan)

> Copy to `experiments/<exp>/data-audit/model-info-sheet.md` and fill **every** blank.
> An unanswered question is **not** neutral — a blank L1/L2/L3 justification is an automatic
> `Verdict: FAIL` in `## DataAudit` (RULE-10). Each question wants a *positive demonstration*
> of hygiene with a `file:line` or split-spec pointer, not "looks fine" / "N/A".
>
> Source: Kapoor & Narayanan, "Leakage and the Reproducibility Crisis in ML-based Science"
> (the model-info-sheet, condensed to the ~21 load-bearing questions). Adapted for the
> proteus-h-neurons QA-derived, qid-grouped, mech-interp setting.

- **Experiment:** EXP-______________________
- **Dataset(s) under audit:** ______________________  (name @ content-hash)
- **Rigor tier:** ⬚ exploratory ⬚ pilot ⬚ confirmatory ⬚ publication   *(missing ⇒ publication, RULE-0)*
- **Filled by:** ______________________   **Date (ISO-8601):** 20____-____-____
- **Split unit of scientific interest:** ⬚ qid ⬚ group/subject ⬚ session ⬚ row *(row ⇒ justify why no grouping is needed; default-suspect)*

---

## L1 — Train / test contamination
*(No information from the test/held-out partition may enter training, directly or via fitted state.)*

- **L1.1 — Does a separate held-out partition exist, defined before any model touched the data?**
  Answer / evidence: ______________________________________________

- **L1.2 — Is every preprocessing step (scaler, PCA, feature-selector, dim-reducer, normalizer) fit on the *training fold only*, never on combined or test data?**
  Answer / `file:line`: ______________________________________________

- **L1.3 — Is feature selection / hyperparameter search performed *inside* the CV loop (on train folds), not once on the full dataset before splitting?**
  Answer / `file:line`: ______________________________________________

- **L1.4 — Are there duplicate or near-duplicate rows that appear in *both* train and test? (count + dedup evidence)**
  Answer / count: ______________________________________________

- **L1.5 — For grouped data, are all rows sharing a `qid` (or group/subject) confined to a single partition? (no straddling)**
  Answer / evidence: ______________________________________________

- **L1.6 — Was any target/label computed using statistics of the full dataset (e.g. a global mean, a global threshold) that bleed test info into train?**
  Answer: ______________________________________________

- **L1.7 — Is the test partition used *exactly once*, at the end, for the headline metric — not for model/feature/threshold selection?**
  Answer: ______________________________________________

**L1 section verdict:** ⬚ PASS ⬚ FAIL   — *FAIL if any of L1.1–L1.7 is blank or fails.*

---

## L2 — No illegitimate / label-leaking features
*(No feature may stand in for the label or encode information unavailable at the modeled decision time.)*

- **L2.1 — Is any feature a proxy for, or deterministically derived from, the label? (list the screened features)**
  Answer: ______________________________________________

- **L2.2 — Label-correlation screen: which features exceed the pre-set |r| (or MI) threshold, and is each one legitimately available at decision time?**
  Threshold |r| ≥ ______   Flagged feature(s): ______________________________________________

- **L2.3 — Are any features computed *after* the event the label describes (temporal leakage of a future signal)?**
  Answer: ______________________________________________

- **L2.4 — Does any feature encode the data-collection process / provenance (e.g. file index, ordering, batch id) rather than the phenomenon?**
  Answer: ______________________________________________

- **L2.5 — For activation/representation features (mech-interp): are they extracted from a model/layer/run that did not itself see the test labels?**
  Answer / source run: ______________________________________________

- **L2.6 — Is a nuisance variable (e.g. answer length, token count, prompt template id) confounded with the label, and is it controlled or screened?**
  Nuisance var(s): ______   Control: ______________________________________________

- **L2.7 — Is the baseline a *legitimate* comparator (same features-minus-the-claimed-signal), not an artificially weak one?**
  Answer: ______________________________________________

**L2 section verdict:** ⬚ PASS ⬚ FAIL   — *FAIL if any of L2.1–L2.7 is blank or fails.*

---

## L3 — Sampling / population-scope hygiene
*(The evaluation distribution must match the claim's intended scope; filtering and sampling must not manufacture the result.)*

- **L3.1 — Temporal / group disjointness: is there an explicit flag confirming train precedes test in time (or groups are disjoint)? Where is it set?**
  Flag + `file:line`: ______________________________________________

- **L3.2 — How was the sample drawn, and does the train/test draw share the *same* distribution (no distribution shift introduced by the split itself)?**
  Answer: ______________________________________________

- **L3.3 — What filtering was applied (drop-rate, inclusion criteria), and is the surviving distribution representative of the population the claim addresses? (state the scope, RULE-9)**
  Drop-rate: ______   Surviving scope: ______________________________________________

- **L3.4 — Is the test set drawn from the same population as the deployment/claim target, not an easier or differently-distributed subset?**
  Answer: ______________________________________________

- **L3.5 — Is the data complete enough that selection-on-the-outcome (survivorship) is ruled out?**
  Answer: ______________________________________________

- **L3.6 — Are there dependencies across "independent" samples (shared prompt, shared source document, autocorrelation) that inflate effective N?**
  Effective N vs nominal N: ______________________________________________

- **L3.7 — Is the cross-model normalization (if any cross-model claim) explicit — relative depth / per-model z-score / PCA-to-common-dim / Procrustes (RULE-4)?**
  Normalization: ______________________________________________

**L3 section verdict:** ⬚ PASS ⬚ FAIL   — *FAIL if any of L3.1–L3.7 is blank or fails.*

---

## Roll-up (feeds the `## DataAudit` block)

| Section | Verdict | Justification pointer |
|---------|---------|------------------------|
| L1 | PASS / FAIL | this file #L1 (or one-liner) |
| L2 | PASS / FAIL | this file #L2 |
| L3 | PASS / FAIL | this file #L3 |

> Any blank cell above ⇒ `Verdict: FAIL`. The auditor copies these three verdicts and pointers
> verbatim into the `L1` / `L2` / `L3` lines of the `## DataAudit` return block.
