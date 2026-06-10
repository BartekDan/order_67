---
exp: EXP-spectral-length-bias
artifact: runs
version: "1"
created: 2026-05-19
rigor_tier: confirmatory
node_count: 6
parallel_safe_count: 1
checkpoint_count: 2
status: audited
---

# Run Tree — `EXP-spectral-length-bias`

**Rigor tier:** `confirmatory` — drives seed count (k=5, power-justified), the FDR-correction
requirement, the mandatory confound-audit on positives (RULE-6), and `/execute` verifier strictness.

**Hypothesis:** `H-001 — wavelet-band energy of H-Neuron activation trajectories detects HALLUCINATED
vs FAITHFUL answers (held-out balanced_accuracy >= 0.65, chance 0.50)`
**Primary metric (pre-registered):** `balanced_accuracy` — every Evaluate node scores THIS; swapping
it is a `/register` round-trip, not a plan-time edit (RULE-5).

Search order is signal-first: T-001 is the quicklook node and produces the single inspectable signal
(held-out balanced_accuracy on a thin 1-model slice) before the 18-model sweep. Best-first by
balanced_accuracy within the 12-GPU-h budget.

Status legend (CONVENTIONS §5): `[ ]` pending · `[~]` running · `[x]` promoted · `[!]` halted.

---

## RunPlan
- Experiment: EXP-spectral-length-bias
- Nodes: 6 (2 Draft / 1 Improve / 1 Evaluate / 2 Debug-slots) ; tree-depth 3 ; 1 parallel-safe (P) ; + 2 quicklook checkpoints + 1 confound-audit gate node
- Seed-policy: confirmatory ⇒ 5 seeds per Evaluate node ; seeds=[0,1,2,3,4] ; variation-source=split (qid-split; bootstrap over qids) ; power: detect bal-acc delta 0.10 over chance at alpha=0.05, power=0.8 ⇒ k>=4, k=5 for margin (RULE-7/8)
- Budget: max_gpu_hours=12 · max_usd=36 · max_wallclock_min=720 ; search=best-first-by-balanced_accuracy ; max_debug_depth=3 ; halt-at-cap=true
- Quicklook-task: T-001 — Draft+Evaluate quicklook: held-out balanced_accuracy of the wavelet classifier on a 1-model x n=200 thin slice (signal-first; produces RUN-001/metrics.json:held_out_balanced_accuracy)
- Checkpoints: T-NNN-ql every 3 runs (quicklook re-render + budget-burn report)
- Tier-flag: none

---

# Node tree

## [x] T-001 — Draft+Evaluate quicklook: held-out balanced_accuracy on a 1-model thin slice
**_Owns:_** `results/EXP-spectral-length-bias/RUN-001/, trace/EXP-spectral-length-bias/quicklook.ipynb`
**_Depends:_** none
**_Tier:_** exploratory (the quicklook is a one-seed look, regardless of the experiment tier)
**seeds:** `[0]` — quicklook is a one-seed look, not a power claim.

Signal-first node. Extract H-Neuron trajectories for ONE model, resample to length 32, Daubechies-4
DWT (3 levels), fit one L2 logistic on the wavelet-band energies, and render the held-out
balanced_accuracy on a 200-question qid-disjoint slice so a human / the next checkpoint can kill the
experiment before the full sweep.

**Acceptance:**
- The quicklook scalar `held_out_balanced_accuracy` renders from `RUN-001/metrics.json`.
- The pre-registered primary metric `balanced_accuracy` is parsed from `RUN-001/metrics.json`.
- No write outside `_Owns:_` (held-out split is READ, never written).

## Run Notes
- RUN-001 returned held_out_balanced_accuracy=0.69 on the thin slice (above the 0.60 signal line) ⇒ scale.

---

## [x] T-002 — Draft: full 18-model wavelet-band-energy logistic baseline
**_Owns:_** `results/EXP-spectral-length-bias/RUN-002/, configs/EXP-spectral-length-bias/baseline.json`
**_Depends:_** T-001
**_Tier:_** confirmatory

First real config across all 18 models: per-model z-scored wavelet-band energies (RULE-4), L2
logistic, qid-disjoint CV. Best-first will Improve on this.

**Acceptance:**
- `RUN-002/metrics.json` carries `balanced_accuracy`, parsed by /execute.
- Reducers / H-Neuron selection / C-search fit on the TRAIN fold only (RULE-10).

## Run Notes
- RUN-002 held-out balanced_accuracy=0.70 pooled across 18 models; promising, expand.

---

## [x] T-003 — Improve: C-regularization + per-band feature weighting
**_Owns:_** `results/EXP-spectral-length-bias/RUN-003/, configs/EXP-spectral-length-bias/improve-1.json`
**_Depends:_** T-002
**_Tier:_** confirmatory

Best-first expansion of T-002: tune the logistic C inside the train folds and weight the four wavelet
bands. Highest-scoring leaf so far.

**Acceptance:**
- `RUN-003/metrics.json` carries `balanced_accuracy`; compared against T-002.

## Run Notes
- RUN-003 held-out balanced_accuracy=0.71; best leaf ⇒ promote to the confirmatory seed-sweep Evaluate.

---

## [x] T-003-ql — Quicklook checkpoint after T-003
**_Owns:_** `trace/EXP-spectral-length-bias/checkpoints/T-003-ql.md, trace/EXP-spectral-length-bias/checkpoints/T-003-ql.png, trace/EXP-spectral-length-bias/checkpoints/T-003-ql.json`
**_Depends:_** T-001, T-002, T-003
**_Tier:_** confirmatory

Re-render the held-out balanced_accuracy vs the 0.50 chance line from the latest run and report
budget burn.

**Acceptance:**
- Quicklook signal re-renders from RUN-003 → `T-003-ql.png` / `T-003-ql.json` (bal-acc ~0.71).
- Budget-burn: `gpu_hours_used/max_gpu_hours`, `usd_used/max_usd`, `wallclock_used/max_wallclock_min`.
- Trend: best balanced_accuracy improving T-002 (0.70) → T-003 (0.71).

## Run Notes
- Signal holding above chance; budget burn ~7.5/12 GPU-h. Continue to the Evaluate seed sweep.

---

## [x] T-004 (P) — Evaluate seed sweep: held-out balanced_accuracy across seeds [0,1,2,3,4]
**_Owns:_** `results/EXP-spectral-length-bias/RUN-001/` *(RUN-001 is the headline confirmatory run; one run dir per seed is disjoint across (P) peers)*
**_Depends:_** T-003
**_Tier:_** confirmatory
**seeds:** `[0,1,2,3,4]` — confirmatory, k=5 — **justification:** target effect size bal-acc delta
  0.10 over chance, alpha=0.05, power=0.8 ⇒ k>=4; k=5 for margin (RULE-7/8); variation-source=split
  (95% CI is bootstrap-BCa over qids, seeds confirm stability).

Score the current best config (T-003) against the pre-registered `balanced_accuracy` on the
qid-disjoint held-out fold across the five seeds. THIS produced the positive (held-out bal-acc 0.71,
95% CI [0.66, 0.76]). The held-out fold is READ, never written (RULE-10).

**Acceptance:**
- The headline `RUN-001/metrics.json` carries `balanced_accuracy` (+ CI bounds, n, chance, the raw
  length stats for the nuisance screen), parsed by /execute.
- A positive here triggers a MANDATORY `/confound-audit` before any claim is recorded (RULE-6) —
  the T-AUDIT node below.

## Run Notes
- POSITIVE: held-out balanced_accuracy=0.71, 95% CI [0.66, 0.76] (bootstrap BCa n=2000, qid-split),
  z=+6.2 vs the permutation null. Looks like a real detector ⇒ hand to /confound-audit (RULE-6).

---

## [x] T-004-ql — Final quicklook checkpoint
**_Owns:_** `trace/EXP-spectral-length-bias/checkpoints/T-004-ql.md, trace/EXP-spectral-length-bias/checkpoints/T-004-ql.png, trace/EXP-spectral-length-bias/checkpoints/T-004-ql.json`
**_Depends:_** T-004
**_Tier:_** confirmatory

Final signal render + total budget burn. Hands off to `/confound-audit` (positive) → `/analyze` →
results-verifier.

**Acceptance:**
- Quicklook re-renders from the best seed of T-004 (bal-acc 0.71).
- Total budget burn reported; search halted within 12 GPU-h / $36 / 720 min (used ~9.5 GPU-h).

## Run Notes
- Search halted within budget. Positive confirmed; routing to the mandatory confound-audit gate.

---

## [!] T-AUDIT — Confound-audit gate (RULE-6, mandatory on the confirmatory positive)
**_Owns:_** `experiments/EXP-spectral-length-bias/audit.md, results/EXP-spectral-length-bias/figures/C-001_perm_null.png`
**_Depends:_** T-004
**_Tier:_** confirmatory

NOT a GPU sweep node — the mandatory four-probe confound-audit on the positive C-001, thresholds
frozen BEFORE any probe (RULE-6). Probes: label-permutation null (K=1000) + answer-length nuisance
screen + length-invariant scattering statistic-swap + drop-fixed-length-32 alt-preprocessing.

**Acceptance:**
- `## ConfoundAudit` block written to `audit.md` with `Survives:` populated.
- On `Survives: NO` the branch is HALTED `[!]` and the finding is routed to the results-verifier for
  the REJECT/retraction `## Verdict` (RULE-1 — this node does NOT self-grade).

## Run Notes
- Survives: NO. Nuisance screen FAILED — answer length is systematically longer for hallucinated
  (median 142 vs 38 tokens, Mann-Whitney p<1e-4); feature~length Spearman rho=0.79; after
  regressing length out, balanced_accuracy collapsed to 0.53 [0.49, 0.57] ≈ chance. The "detector"
  is a length detector. Branch halted; routed to results-verifier (expected REJECT → status
  retracted).
