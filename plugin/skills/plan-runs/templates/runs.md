---
exp: <EXP-slug>
artifact: runs
version: "1"
created: <YYYY-MM-DD>
rigor_tier: <inherited from experiment.json — exploratory | pilot | confirmatory | publication>
node_count: 0
parallel_safe_count: 0
checkpoint_count: 0
status: not-started
---

# Run Tree — `<EXP-slug>`

**Rigor tier:** `<exploratory | pilot | confirmatory | publication>` — drives seed count, the
power-analysis requirement, and `/execute` verifier strictness. A missing tier defaults to
`publication` (strictest) and is flagged in `## RunPlan: Tier-flag` (RULE-0).

**Hypothesis:** `<H-NNN — the falsifiable claim from hypothesis.md>`
**Primary metric (pre-registered):** `<metric-key>` — every Evaluate node scores THIS; swapping it
is a `/register` round-trip, not a plan-time edit (RULE-5).

Search order is **signal-first**: Task 1 (`T-001`) is the quicklook node and produces the single
inspectable signal from `experiment.json:quicklook` before any expensive sweep. The autonomous
search is **best-first** by the parsed primary metric within the declared budget; `/execute` expands
the current best leaf via `Improve`, falls back to a sibling `Draft` on a tie/regression, spawns
`Debug` children (bounded by `max_debug_depth`) under a node whose run errored, and HALTS at the
budget cap (D-003).

`(P)` annotations mark seed-parallel-safe nodes whose `_Owns:_` sets are disjoint; the Phase-1
executor still runs serially but the annotation is read by the budgeted parallel executor.

Status legend (CONVENTIONS §5):
- `[ ]` pending
- `[~]` running (a `RUN-NNN` is live on the remote host)
- `[x]` promoted (results-verifier returned `PROMOTE` / `PROMOTE-WITH-CAVEAT`)
- `[!]` halted (verifier returned `RERUN` / `REJECT` / `BLOCKED`; surfaced, branch abandoned)

<!--
ANNOTATION GRAMMAR (CONVENTIONS §5 — the data contract, analog of order-66 _Boundary:_):
- _Owns:_ <comma-separated paths/configs/datasets> — the closed write set for this node. A write
    OUTSIDE this set at /execute time is a hard REJECT (catches writes to the test set, frozen
    baselines, or a sibling's run dir). NEVER list a held-out/test split, a frozen baseline, or
    another node's run dir here (RULE-10).
- _Depends:_ <RUN-IDs / node IDs or "none"> — prerequisite runs.
- _Tier:_ <exploratory|pilot|confirmatory|publication> — inherit experiment.json:rigor_tier; a node
    may DOWN-tier (cheap probe inside a strict experiment) but NEVER up-tier above the default.
- (P) — between node ID and title; node is seed-parallel-safe (its _Owns:_ is disjoint from peers).
- seeds: <list> — REQUIRED on Evaluate nodes. Count scales with tier:
    exploratory=1 · pilot=1–2 · confirmatory=k≥3 (power-justified) · publication=k + seed×split grid.
    At confirmatory+ the line MUST carry the power justification (effect size, α, power) — a bare
    "3 seeds, standard" is rejected (RULE-7/RULE-8).

NODE OPERATIONS (AIDE / AI-Scientist-v2):
- Draft     — first attempt at a node (a config / approach).
- Improve   — refine the current best node (best-first expansion).
- Evaluate  — score a node against the pre-registered primary metric on the held-out fold.
- Debug     — fix a node whose run errored. NOT planned up front; /execute spawns it on demand under
              the failing parent, bounded by max_debug_depth. Plan a Debug-SLOTS budget instead.

REQUIREMENTS for each node:
1. Status checkbox prefix.
2. _Owns:_ line (the write contract).
3. _Depends:_ line (even if "none").
4. _Tier:_ line.
5. seeds: line on Evaluate nodes (tier-scaled, justified at confirmatory+).
6. Acceptance tying the node to the pre-registered primary metric + the metrics.json key /execute parses.
7. Empty `## Run Notes` block (populated by /execute as ## RunReport(s) land).

CHECKPOINT PSEUDO-TASKS (`T-NNN-ql`):
Interleaved after every N completed runs (N = design.md checkpoint cadence, default 3) and after the
final Evaluate node. _Owns:_ is trace/<exp>/checkpoints/T-NNN-ql.{md,png,json}. Acceptance: the
quicklook signal re-renders from the latest run AND a budget-burn line reports
gpu_hours_used/max_gpu_hours, usd_used/max_usd, wallclock_used/max_wallclock_min. Surfaces signal +
remaining budget and CONTINUES (does not block on user input — the user may interrupt if the signal
looks wrong). This is the cheap kill switch + the autonomous-spend governor.

NO ABSOLUTE PATHS (RULE-2). Project paths via ${CLAUDE_PROJECT_DIR}; the remote host loop is owned by
/execute via experiment.json:compute.host_config — never inline a remote path or credential here.
-->

---

## RunPlan
- Experiment: `<EXP-slug>`
- Nodes: `<total>` (`<n_draft>` Draft / `<n_improve>` Improve / `<n_evaluate>` Evaluate / `<n>` Debug-slots) ; tree-depth `<d>` ; `<p>` parallel-safe (P)
- Seed-policy: `<tier>` ⇒ `<k>` seed(s) per Evaluate node ; seeds=`[<list>]` ; variation-source=`<seed|init|split>` ; `<power-justification or "n/a below confirmatory">`
- Budget: max_gpu_hours=`<h>` · max_usd=`<$>` · max_wallclock_min=`<m>` ; search=best-first-by-`<metric-key>` ; max_debug_depth=`<r>` ; halt-at-cap=true
- Quicklook-task: T-001 — `<quicklook node title>` (signal-first; produces `<experiment.json quicklook ref>`)
- Checkpoints: `T-NNN-ql` every `<N>` runs (quicklook re-render + budget-burn report)
- Tier-flag: `<none | MISSING-TIER-DEFAULTED-TO-PUBLICATION | down-tiered-nodes: <ids>>`

---

# Node tree

## [ ] T-001 — Draft+Evaluate quicklook: `<the single inspectable signal>`
**_Owns:_** `results/<exp>/RUN-001/, trace/<exp>/quicklook.ipynb` *(project-relative; resolved under ${CLAUDE_PROJECT_DIR} by /execute)*
**_Depends:_** none
**_Tier:_** `<inherited — usually exploratory for the quicklook regardless of experiment tier>`
**seeds:** `[<single seed, e.g. 0>]` — quicklook is a one-seed look, not a power claim.

Signal-first node. Run ONE seed of ONE cheap config and render the quicklook
(`experiment.json:quicklook` — a notebook cell / figure / scalar) so a human or the next checkpoint
can kill the experiment before any sweep. This is the analog of order-66's demo-visibility Task 1.

**Acceptance:**
- The quicklook artifact (`<notebook cell | figure path | scalar>`) renders from `RUN-001`.
- The pre-registered primary metric `<metric-key>` is parsed from `RUN-001/metrics.json` (even if
  the value is uninteresting — the point is the signal exists and is inspectable).
- No write outside `_Owns:_` (no touch of the held-out split).

## Run Notes
*(populated by /execute as ## RunReport(s) land)*

---

## [ ] T-002 — Draft: `<baseline / first real config>`
**_Owns:_** `results/<exp>/RUN-002/, configs/<exp>/baseline.json`
**_Depends:_** T-001
**_Tier:_** `<inherited>`

`<First real approach the search expands from. Best-first will Improve on this if it scores well.>`

**Acceptance:**
- `RUN-002/metrics.json` carries `<metric-key>` parsed by /execute.
- Reducers / feature selection fit on the TRAIN fold only (RULE-10).

## Run Notes
*(populated by /execute)*

---

## [ ] T-003 — Improve: `<refine the current best leaf>`
**_Owns:_** `results/<exp>/RUN-003/, configs/<exp>/improve-1.json`
**_Depends:_** T-002
**_Tier:_** `<inherited>`

`<Best-first expansion of the highest-scoring leaf. On a tie or regression, /execute falls back to a
sibling Draft instead.>`

**Acceptance:**
- `RUN-003/metrics.json` carries `<metric-key>`; compared against T-002's parsed metric.

## Run Notes
*(populated by /execute)*

---

<!-- QUICKLOOK CHECKPOINT — every N runs (default 3) and after the final Evaluate node. -->

## [ ] T-003-ql — Quicklook checkpoint after T-003
**_Owns:_** `trace/<exp>/checkpoints/T-003-ql.md, trace/<exp>/checkpoints/T-003-ql.png, trace/<exp>/checkpoints/T-003-ql.json`
**_Depends:_** T-001, T-002, T-003
**_Tier:_** `<inherited>`

Re-render the quicklook signal from the latest run and report budget burn. Surfaces signal +
remaining budget to the user and CONTINUES the autonomous search (does not block on input).

**Acceptance:**
- Quicklook signal re-renders from the latest run → `T-003-ql.png` / `T-003-ql.json`.
- Budget-burn line in `T-003-ql.md`: `gpu_hours_used/max_gpu_hours`, `usd_used/max_usd`,
  `wallclock_used/max_wallclock_min`.
- Trend note: is the best parsed `<metric-key>` improving across T-002→T-003? (kill-switch prompt).

## Run Notes
*(populated by /execute after the checkpoint render)*

---

## [ ] T-004 (P) — Evaluate seed sweep: `<the comparison run on the held-out fold>`
**_Owns:_** `results/<exp>/RUN-004-s{seed}/` *(one run dir PER seed — disjoint across (P) peers)*
**_Depends:_** T-003
**_Tier:_** `<inherited>`
**seeds:** `<tier-scaled list>` —
  - exploratory: `[0]` (single seed; no power claim)
  - pilot: `[0,1]` (held-out split exists; signal_confirmed gate passed)
  - confirmatory: `[0,1,2,…]`, k≥3 — **justification:** target effect size `<d/Δ>`, α=`<0.05>`,
    power=`<0.8>` ⇒ k=`<computed>` (RULE-7/RULE-8); variation-source=`<seed|init|split>`
  - publication: confirmatory k + seed×split grid for NeurIPS 4–8 reproducibility evidence

Score the current best config against the **pre-registered** primary metric on the held-out fold,
across the tier-scaled seeds. Each seed is a separate `RUN-004-s{seed}` (the `(P)` disjoint
`_Owns:_` that makes seed-parallel execution safe).

**Acceptance:**
- Each `RUN-004-s{seed}/metrics.json` carries `<metric-key>` parsed by /execute.
- The held-out fold is READ, never written (it is NOT in `_Owns:_`) (RULE-10).
- At confirmatory+: a positive result here triggers a MANDATORY `/confound-audit` before any
  claim is recorded (RULE-6) — that is a downstream gate, not a node here.

## Run Notes
*(populated by /execute)*

---

<!-- FINAL CHECKPOINT — always after the last Evaluate node. -->

## [ ] T-004-ql — Final quicklook checkpoint
**_Owns:_** `trace/<exp>/checkpoints/T-004-ql.md, trace/<exp>/checkpoints/T-004-ql.png, trace/<exp>/checkpoints/T-004-ql.json`
**_Depends:_** T-004
**_Tier:_** `<inherited>`

Final signal render + total budget burn. Hands off to `/confound-audit` (on a positive) → `/analyze`
→ results-verifier (the never-self-grade `## Verdict`).

**Acceptance:**
- Quicklook re-renders from the best seed of T-004.
- Total budget burn reported; confirm the search halted within `max_gpu_hours/max_usd/max_wallclock_min`.

## Run Notes
*(populated by /execute)*

---

<!--
DEBUG BUDGET (not concrete nodes — /execute instantiates these on demand):
A node whose RUN errored gets a Debug child:
    ## [ ] T-00X-dbg1 — Debug: <parent node title>
    **_Owns:_** results/<exp>/RUN-00X-dbg1/
    **_Depends:_** T-00X
    **_Tier:_** <inherited>
…up to max_debug_depth (default 3). After that the branch is ABANDONED ([!]) and the failure is
surfaced. Do NOT pre-plan Debug nodes — you cannot know which node errors. Plan the Debug-slots
COUNT in the ## RunPlan: Nodes field instead.

Continue with T-005 (Improve), T-006 (Draft sibling on regression), T-006-ql (checkpoint), … until a
leaf Evaluate node returns a promotable metric OR a budget cap halts the search.
NO ABSOLUTE PATHS (RULE-2). Seeds parallel-safe ⇒ disjoint _Owns:_ per (P) peer.
-->
