---
name: plan-runs
description: Read an experiment's hypothesis.md + design.md (## DesignDraft) + experiment.json (for rigor_tier, seed_policy, compute.budget, quicklook); produce experiments/<exp>/runs.md as a best-first experiment TREE of node-tasks (Draft/Improve/Debug/Evaluate) with _Owns:_/_Depends:_/_Tier:_/(P) annotations, tier-scaled seed counts, quicklook-checkpoint pseudo-tasks, and a declared autonomous-search budget. Returns a ## RunPlan block.
whenToUse: Invoked after /design-experiment has produced design.md (with a ## DesignDraft block) and /data-audit has returned PASS, but before /conflicts and /execute. Triggered by the user saying "plan the runs", "build the experiment tree", "/plan-runs <exp>", or by /execute refusing because runs.md is missing. Do NOT fire if runs.md already has a populated node tree — that is an extend case (edit runs.md directly or append a sub-tree).
isEnabled: test -d experiments
---

# /plan-runs

## Static

### Summary
Take one experiment that has a registered hypothesis and a design but no run plan. Produce
`experiments/<exp>/runs.md` as an explicit **experiment tree** of node-tasks — operations
`Draft`/`Improve`/`Debug`/`Evaluate` borrowed from AIDE and AI-Scientist-v2 — ordered
**signal-first** (Task 1 is always the quicklook node, the analog of order-66's demo-visibility
ordering). Each node carries `_Owns:_` (the write contract), `_Depends:_`, `_Tier:_`, and `(P)`
where seed-parallel-safe, with status checkboxes. Seed count scales with the rigor tier;
quicklook-checkpoint pseudo-tasks are interleaved every N runs; and the autonomous tree-search
budget (`max_gpu_hours`/`max_usd`/`max_wallclock_min`) is declared so `/execute` can search
best-first and halt at the cap. This skill plans; it never launches a run.

### Preconditions
- `experiments/<exp>/hypothesis.md` exists with at least one `H-NNN` falsifiable hypothesis and a
  named primary metric (written by `/register`).
- `experiments/<exp>/design.md` exists and carries a `## DesignDraft` block with a populated
  `Quicklook:` field and a `Compute-plan:` field (written by `/design-experiment`).
- `experiments/<exp>/experiment.json` exists. Read **`rigor_tier`**, `seed_policy`,
  `compute.budget`, `compute.host_config`, and `quicklook` FIRST; the tier branches the whole plan.
- `/data-audit` has returned `## DataAudit … Verdict: PASS` for this experiment (the leakage/secret
  gate precedes run planning; do not plan runs over un-audited data).
- `experiments/<exp>/runs.md` does NOT exist, OR exists with only frontmatter and no node tasks
  (this is what guards against overwriting a live plan whose checkboxes `/execute` is mutating).

If `hypothesis.md` is missing, refuse with: `"No hypothesis found for <exp>. Run /register first."`

If `design.md` is missing or lacks a `## DesignDraft` block with a `Quicklook:` field, refuse with:
`"design.md missing or has no ## DesignDraft Quicklook. /plan-runs orders the tree signal-first and needs the quicklook node from /design-experiment."`

If `## DataAudit` for this experiment is absent or its `Verdict:` is not `PASS`, refuse with:
`"No PASS data audit for <exp>. Run /data-audit first — planning runs over un-audited data is a leakage/secret risk (RULE-10)."`

If `experiment.json` is missing or has no `rigor_tier`, **do not guess**: default the plan to
`publication` (strictest) AND emit `Tier-flag: MISSING-TIER-DEFAULTED-TO-PUBLICATION` in the
`## RunPlan` block as a blocking issue (RULE-0).

If `runs.md` already has ≥1 node task (a `## [` line), refuse with:
`"Experiment <exp> already has a run tree. Edit runs.md directly, or append a sub-tree under an existing node."`

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `notes` — optional. Free prose carrying user-supplied search-direction hints (e.g. "prioritise
  the layer sweep before the head sweep"). Treated as binding ordering hints, not as new
  hypotheses — a new hypothesis goes back through `/register`.

### Output format
Writes `experiments/<exp>/runs.md` using `${CLAUDE_PLUGIN_ROOT}/skills/plan-runs/templates/runs.md`.
Each node-task carries:
- A status checkbox prefix: `[ ]` pending · `[~]` running · `[x]` promoted · `[!]` halted
  (RERUN/REJECT/BLOCKED). All nodes start `[ ]` (CONVENTIONS §5).
- A node **operation** in the title — one of `Draft` (first attempt at a node), `Improve` (refine
  the current best node), `Debug` (fix a node whose run errored — only spawned under a parent),
  `Evaluate` (score a node against the primary metric / run the held-out fold).
- `_Owns:_` — the write contract: the exact paths/configs/datasets this node may write
  (`results/<exp>/<RUN-…>/`, a config file, a figure). A write outside this set is a hard `REJECT`
  at `/execute` time. NEVER list a frozen baseline, a test/held-out split, or another node's run dir
  in `_Owns:_` (CONVENTIONS §5; RULE-10).
- `_Depends:_` — predecessor `RUN-NNN`/node IDs, or `none`.
- `_Tier:_` — the effective tier for this node. Inherit `experiment.json:rigor_tier` unless the node
  explicitly down-tiers (a cheap exploratory probe inside a confirmatory experiment is allowed;
  **up-tiering a single node above the experiment default is not** — that re-creates tier bloat).
- `(P)` between the node ID and title where the node's `_Owns:_` set is disjoint from its peers
  (the canonical case is a seed sweep: each seed writes its own run dir).
- A `seeds:` line whose count is set by the tier (see seed policy below).
- An `Acceptance:` block tying the node to the primary metric and the parsed-metric key `/execute`
  greps from `metrics.json`.
- An empty `## Run Notes` block (populated by `/execute` as `## RunReport`s land).

The first emitted block is the `## RunPlan` RETURN FORMAT block. Its mechanical fields
(`hooks/block-schemas.tsv`) MUST appear verbatim:

```
## RunPlan
- Experiment: EXP-<slug>
- Nodes: <total node count> (<n_draft> Draft / <n_improve> Improve / <n_evaluate> Evaluate / <n_debug-budget> Debug-slots) ; tree-depth <d> ; <p> parallel-safe (P)
- Seed-policy: <tier> ⇒ <k> seed(s) per Evaluate node ; seeds=[<list>] ; variation-source=<seed|init|split> ; <power-justification or "n/a below confirmatory">
- Budget: max_gpu_hours=<h> · max_usd=<$> · max_wallclock_min=<m> ; search=best-first-by-<metric-key> ; max_debug_depth=<r> ; halt-at-cap=true
- Quicklook-task: T-001 — <quicklook node title> (signal-first; produces <design.json quicklook ref>)
- Checkpoints: T-<NNN>-ql every <N> runs (quicklook re-render + budget-burn report)
- Tier-flag: <none | MISSING-TIER-DEFAULTED-TO-PUBLICATION | down-tiered-nodes: <ids>>
```

`Budget`, `Seed-policy`, and `Quicklook-task` MUST be derivable from `experiment.json` /
`design.md`, never invented. If a budget field is absent in `experiment.json:compute.budget`, leave
the value as `<TBD: set compute.budget.<field> in experiment.json>` and add it to `Tier-flag` —
do NOT fabricate a number, because `/execute` treats `Budget` as a hard cap.

### Seed policy (tier-scaled)
The count of seeds per `Evaluate` node scales with the tier; tiers nest, so a higher tier inherits
the lower tier's floor and adds to it:

| Tier | Seeds per Evaluate node | Justification required |
|------|-------------------------|------------------------|
| `exploratory` | 1 | none (single seed is acceptable here) |
| `pilot` | 1–2 (held-out split must exist) | none, but `signal_confirmed` gate must precede expensive nodes |
| `confirmatory` | k ≥ 3, **k justified by a power analysis** | YES — write the target effect size, α, and desired power into the `seeds:` line's justification; a bare "3 seeds because that's standard" is rejected (RULE-7/RULE-8) |
| `publication` | confirmatory's k + seed×split grid for the reproducibility evidence | YES — power analysis + the seed/split grid that the NeurIPS 4–8 reproducibility items need |

Seeds come from `experiment.json:seed_policy.seeds` when present; if the tier needs more seeds than
are listed, extend the list deterministically (e.g. `[0,1,2]`) and note the extension in the
`seeds:` justification. Never reuse a single seed across nodes you intend to compare for variance.

### Quicklook-checkpoint pseudo-tasks
Interleave a `T-<NNN>-ql` pseudo-task after every **N** completed runs (N from
`design.md`'s checkpoint cadence, default **3**) and after the final Evaluate node. A checkpoint
pseudo-task:
- `_Owns:_ trace/<exp>/checkpoints/T-<NNN>-ql.{md,png,json}` (only the checkpoint artifacts).
- `_Depends:_` the prior N run nodes.
- Acceptance: the quicklook signal (`experiment.json:quicklook`) re-renders from the latest run, AND
  a budget-burn line reports `gpu_hours_used / max_gpu_hours`, `usd_used / max_usd`,
  `wallclock_used / max_wallclock_min`. It surfaces the signal + remaining budget to the user and
  CONTINUES (does not block on input) — the analog of order-66's clickable demo checkpoint. The user
  may interrupt if the signal looks wrong; otherwise the autonomous search proceeds until a budget
  cap or a leaf Evaluate node returns a promotable metric.

### Hard constraints
- **Task 1 MUST be the quicklook node.** The single inspectable signal from
  `experiment.json:quicklook` (a notebook cell, a figure, or a scalar metric) is produced first,
  before any expensive sweep. Signal-first ordering is non-negotiable — it is the direct analog of
  order-66's demo-visibility ordering and is what lets the `signal_confirmed` / quicklook checkpoint
  kill a doomed experiment cheaply. If Task 1 is "launch the 64-config layer sweep", the plan is
  wrong; Task 1 is "render the quicklook on one seed of one config so we can look at it".
- **Every node has all four annotations** — `_Owns:_`, `_Depends:_` (even if `none`), `_Tier:_`, and
  a status checkbox — plus a `seeds:` line on Evaluate nodes. A node missing `_Owns:_` cannot be
  boundary-checked by `/execute` and is invalid.
- **`_Owns:_` sets are disjoint between `(P)` peers.** If two `(P)` seed nodes both list the same run
  dir, the parallel executor collides and one will clobber the other's `metrics.json`. Give each
  seed its own `results/<exp>/RUN-NNN/` and keep `(P)`.
- **Seed count is tier-scaled and justified at confirmatory+.** Do not emit ≥3 seeds without the
  power-analysis justification on the `seeds:` line (RULE-7/RULE-8); do not emit a single seed at
  confirmatory+ (RULE-7). An underpowered comparison is flagged, not silently planned.
- **Declare the autonomous-search budget as a HARD cap.** The `Budget` field is the contract
  `/execute` halts on (D-003). It MUST carry `max_gpu_hours`, `max_usd`, `max_wallclock_min`,
  the best-first search key (the parsed metric), `max_debug_depth` (bounded debug recursion), and
  `halt-at-cap=true`. A plan with no budget is refused — autonomy without a cap is how you spend a
  GPU weekend on nothing.
- **Bounded debug recursion.** `Debug` nodes are spawned by `/execute` only as children of a node
  whose run errored, and only up to `max_debug_depth` (default 3) before the branch is abandoned and
  the failure is surfaced. Plan the debug *budget* (a `Debug-slots` count), not concrete debug nodes
  in advance — you cannot know which node will error.
- **Best-first, not breadth-first, by the parsed metric.** The tree-search policy is: expand the
  current best leaf (highest parsed primary metric) via an `Improve` node, fall back to a sibling
  `Draft` on a tie or a regression. State this policy in the `Budget` field's `search=` clause.
- **No absolute paths** anywhere in `runs.md` (RULE-2). Resolve project paths via
  `${CLAUDE_PROJECT_DIR}` and refer to remote paths only through `experiment.json:compute.host_config`
  (the harness owns the SSH loop; the plan never inlines a remote path or a credential).
- **Honor the prereg.** The primary metric and splits in every Evaluate `Acceptance:` MUST match the
  hash-locked values in `hypothesis.md`/prereg. At confirmatory+ a planned deviation HARD-BLOCKS
  PROMOTE downstream (RULE-5/D-005); if the design genuinely needs a different metric, send it back
  through `/register`, do not silently re-plan around it.
- **Plan only — do not launch.** This skill writes `runs.md` and the `## RunPlan` block. It never
  scps, never polls, never fetches; `/execute` owns the remote loop.

### Common mistakes (avoid)
1. **Ordering the tree by dependency graph instead of signal-first.** The temptation is "set up the
   data loader, then the model, then sweep, then look at a figure last". That is the order-66
   foundation-first anti-pattern. Task 1 is the quicklook node so a human (or the quicklook
   checkpoint) can kill the experiment after one cheap run instead of after the whole sweep.
2. **Padding seeds "to be safe" at exploratory/pilot.** A 5-seed sweep on an exploratory probe burns
   budget that buys no confirmatory power (the tier doesn't claim significance). Single seed is
   correct at exploratory. Conversely, **3 seeds with no power analysis at confirmatory** is the
   opposite failure — it looks rigorous but the k is unjustified (RULE-7).
3. **Overlapping `_Owns:_` between `(P)` seed peers.** Two parallel seeds writing
   `results/<exp>/sweep/metrics.json` will race. Each `(P)` node owns its own run dir.
4. **Planning concrete `Debug` nodes up front.** You cannot predict which node errors. Plan a debug
   *budget* (`max_debug_depth` + a `Debug-slots` count); `/execute` instantiates `Debug` children on
   demand under the failing parent.
5. **Omitting or fabricating the budget.** No `Budget` ⇒ unbounded autonomous spend; a fabricated
   `max_usd` ⇒ `/execute` halts at the wrong cap. Read it from `experiment.json:compute.budget`; if a
   field is absent, emit `<TBD: …>` and flag it — never invent the number.
6. **Putting the held-out / test split inside an `_Owns:_` set, or letting a fit touch it.** A node
   that owns (and therefore may write) the test split is a leakage hazard and an automatic
   DO-NOT-PROMOTE (RULE-10). The Evaluate node *reads* the held-out fold; it never owns it. Reducers
   and feature selection are fit on the train fold only.
7. **Quietly swapping the primary metric to whatever scored best.** That is HARKing. The Evaluate
   acceptance metric is the pre-registered one. A new metric is a `/register` round-trip, not a
   plan-time edit (RULE-5).
8. **Skipping quicklook checkpoints "to save runs".** The checkpoint is the cheap kill switch and the
   budget-burn read-out. Skipping it turns autonomous-within-budget search into autonomous-spend.

## Dynamic

Templates: `${CLAUDE_PLUGIN_ROOT}/skills/plan-runs/templates/runs.md`. Read it with the Read tool —
it lays out the frontmatter, the status legend, the annotation grammar, the signal-first Task-1
quicklook node, the Draft→Improve→Evaluate tree skeleton, the seed-sweep `(P)` peers, and the
`T-NNN-ql` checkpoint pseudo-task shape.

`experiments/<exp>/` already exists when this skill fires (gated by `isEnabled` after the experiment
was registered) — write `runs.md` directly without re-checking the directory (RR-014).

`experiments/<exp>/experiment.json` already exists — read `rigor_tier`, `seed_policy`,
`compute.budget`, `compute.host_config`, and `quicklook` FIRST and branch the whole plan on the tier.

`experiments/<exp>/design.md` and `experiments/<exp>/hypothesis.md` already exist — read them
directly for the quicklook reference, the primary metric, the checkpoint cadence, and the
compute plan. Do not re-derive the hypothesis; the prereg is authoritative.

Confirm inputs and read the tier + budget at runtime:

- `!{ls experiments/${exp:-.}/ 2>/dev/null}` — confirm hypothesis.md, design.md, experiment.json
  present and runs.md absent (or frontmatter-only) before generating.
- `!{grep -o '"rigor_tier"[^,}]*' experiments/${exp:-.}/experiment.json 2>/dev/null | head -1}` —
  the load-bearing tier (no jq; grep best-effort per RULE-2). Empty ⇒ default publication + flag.
- `!{grep -A6 '"budget"' experiments/${exp:-.}/experiment.json 2>/dev/null | grep -E 'max_(gpu_hours|usd|wallclock_min)'}` —
  the autonomous-search caps that populate the `Budget` field. Any missing field ⇒ `<TBD: …>` + flag.
- `!{grep -A4 '"quicklook"' experiments/${exp:-.}/experiment.json 2>/dev/null}` — the signal Task 1
  must produce.
- `!{grep -E '^- Verdict:' experiments/${exp:-.}/design.md results/${exp:-.}/*data-audit* 2>/dev/null | tail -3}` —
  confirm a PASS data audit precedes planning (refuse otherwise).
