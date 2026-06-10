# /triage — 7-path research-routing decision tree

Read top-to-bottom. **First match wins.**

**The bias is cheap-before-expensive.** This is the research-world analog of order-66's spike/wedge discipline: you do not authorize an expensive multi-seed `confirmatory-experiment` until a *cheap signal* — a replicated baseline or a single-seed probe — already says the effect is plausibly real. The whole tree is ordered so that the two cheap paths (`replicate-baseline`, `quick-probe`) are *considered before* the expensive one (`confirmatory-experiment`). The gate is the `Signal-validated` field: `NO` means no cheap evidence exists yet, which forces the route down to a probe. The failure mode this exists to prevent is burning a GPU/$/wallclock budget to "confirm" an effect that a 20-minute probe would have shown was noise.

Rigor tiers nest cumulatively (CONVENTIONS.md §2). At each path, recommend the **lowest tier that still answers the question** — never impose a higher tier's checks (FDR, N≥k seeds, NeurIPS checklist) on cheaper work. That re-creates the exact bloat the tier system kills.

---

## 1. `reject`

**Trigger:** ANY of:
- Out of scope — the question belongs to a different project/codebase/model, or asks for something the data on the remote host cannot answer.
- Duplicate of an experiment already in flight (`experiments/<exp>/experiment.json` with `status` ∈ {registered, running, audited} already covers it).
- Unanswerably vague — no measurable quantity, no scope, no candidate signal (e.g. "make the model more interpretable" with no metric, layer, or claim).

**Decision questions:**
- Can this be measured on the data/compute actually available at `${CLAUDE_PROJECT_DIR}`/the remote host?
- Is there already a live experiment that subsumes it?
- Is there *any* falsifiable quantity here, or only a vibe?

**Not a reject:** "is this *promoted* finding actually real?" — that is a re-test (→ §4 or §3), and a null result is a result (RULE-8). Reject is for out-of-scope / duplicate / unanswerable only.

**Rationale template:** `"Out of scope: <why>"` / `"Duplicate of EXP-<existing>"` / `"Ambiguous; need clarification on <specific question>."`

**Tier:** n/a. **Experiment:** `n/a`. **Signal-validated:** `N/A`.

**Next action:** confirm with the user; do not write anything.

---

## 2. `replicate-baseline`  (cheapest — establish the floor first)

**Trigger:** ALL of:
- The request hinges on a *delta over a baseline* (a metric beating a prior number, a paper's reported score, a previous run, or a "standard" model).
- That baseline has NOT been reproduced on *this* data + code + git commit (no replicated number lives in `results/<exp>/baseline.json`).

**Decision questions:**
- Does the claim take the form "X beats / differs-from baseline B"?
- Has B been reproduced here, or is it a number copied from a paper/README/someone's memory?
- Would a wrong baseline silently poison the effect size we are about to chase?

**Why before `quick-probe`:** an unreplicated baseline poisons every downstream effect size (RULE-7) — you cannot trust a *delta* until the *floor* reproduces. Lock the floor, then probe the delta.

**Rationale template:** `"Claim is a delta over baseline B which is unreplicated on this commit/data; reproduce the floor before measuring any effect (RULE-7)."`

**Tier:** `pilot` (a held-out split must exist for the baseline to mean anything; RULE-10). **Signal-validated:** `NO` (replicating a baseline is *establishing* signal, not consuming it).

**Next action:** `/register EXP-<slug> --tier=pilot` scoped to reproduce the baseline only — then `/data-audit` for leakage-safety before the number is trusted.

---

## 3. `quick-probe`  (cheap — validate the signal before any campaign)

**Trigger:** ALL of:
- A concrete, falsifiable hypothesis exists (a named effect, neuron, layer, metric).
- NO cheap signal yet exists that the effect is real (`Signal-validated: NO` — the cheap-signal scan found nothing on disk).
- The smallest falsifying measurement is runnable cheaply: one seed, one split, minutes-to-low-GPU-hours, well inside any budget.

**Decision questions:**
- Is there a single-seed, single-split measurement that could *kill* this idea fast?
- Has *any* prior artifact (a logged effect, a replicated baseline) already pointed at the effect being real? If no → this is a probe, not a confirmatory run.
- Is the user reaching for a multi-seed campaign on enthusiasm rather than evidence?

**This is the spike/wedge analog.** A probe is allowed to be throwaway: hardcoded config, single seed, no FDR, no CI ceremony — it answers exactly one question: *is there anything here at all?* Tiers nest, so an exploratory probe owes only: runs-without-error, no committed secret, no train/test leakage (§2).

**Mandatory exit:** after the probe, surface to the user — *"signal present? → graduate to a `confirmatory-experiment`, or kill it as noise, or iterate the probe."* Do NOT silently escalate a promising probe into a multi-seed campaign; that is the user's GO/PIVOT/KILL call.

**Rationale template:** `"Falsifiable hypothesis with no cheap signal yet (Signal-validated: NO); run the smallest single-seed probe that could falsify it before committing GPU budget — spike-before-confirm."`

**Tier:** `exploratory` (a curiosity) or `pilot` (if the probe needs a held-out split + the `signal_confirmed` gate before any scaling). **Signal-validated:** `NO`.

**Next action:** `/register EXP-<slug> --tier=exploratory` then `/design-experiment` for a one-seed quicklook — NOT `/plan-runs` for a sweep.

---

## 4. `confirmatory-experiment`  (expensive — ONLY once signal is validated)

**Trigger:** ALL of:
- A cheap signal already exists that the effect is real (`Signal-validated: YES` — a replicated baseline or a prior single-seed probe shows the effect on disk).
- The question now needs *defensible* statistics: a multi-seed estimate, a CI with a named variation source, an effect size, FDR correction across the comparisons made.
- The user wants a claim strong enough to promote, paper, or brief.

**Decision questions:**
- Has a probe or baseline already shown the effect is plausibly real? (If NO → you may NOT route here; drop to §3 `quick-probe`. This is the hard gate.)
- Does the stakes of the claim justify N≥k seeds, a frozen prereg, and a mandatory confound-audit on every positive?
- Is the user ready to hash-lock {hypothesis, primary metric, splits, analysis plan} *before* any result exists?

**Hard gate (cheap-before-expensive):** if `Signal-validated` is `NO`, this path is **forbidden** — reroute to `quick-probe` no matter how confident the request sounds.

**Tier obligations the Rationale MUST name:** at `confirmatory`+ a **prereg deviation HARD-BLOCKS PROMOTE** (RULE-5 / D-005 — re-register or down-tier), N≥k seeds need a power-analysis justification, and *every positive finding* triggers a confound-audit (permutation null + nuisance screen + statistic-swap, RULE-6). The user opts in with eyes open.

**Rationale template:** `"Cheap signal already validated (Signal-validated: YES); promote-grade claim needs N-seed CI + effect size + FDR (RULE-3/7). At confirmatory tier a prereg deviation hard-blocks PROMOTE (RULE-5) and every positive triggers a confound-audit (RULE-6)."`

**Tier:** `confirmatory` (or `publication` only if the artifact is a paper submission needing the full NeurIPS 16-item checklist + datasheet + model card; do not reach for `publication` reflexively). **Signal-validated:** `YES`.

**Next action:** `/register EXP-<slug> --tier=confirmatory` (hash-lock the prereg) → `/design-experiment` → `/data-audit` → `/plan-runs`.

---

## 5. `decompose-agenda`

**Trigger:** the user is asking *"what should we look at next?"* or *"break down the <X> research agenda"* without naming one concrete question. The work is a research direction that needs splitting into experiment-sized units.

**Decision questions:**
- Is the input an *agenda item / direction* rather than a single falsifiable hypothesis?
- Does `experiments/agenda.md` hold a line that needs unpacking into 1+ experiments?

**Not this path:** if the user already named a concrete question ("test whether neuron N tracks answer length"), route it directly (§3/§4) — decomposition is for directions, not questions.

**Rationale template:** `"User requested agenda progression; direction <X> needs decomposition into 1+ experiment-sized units, each with its own hypothesis + signal gate."`

**Tier:** n/a at the agenda level — each child experiment gets its own recommended tier when it is itself triaged/registered. **Experiment:** `n/a` (children are named on decomposition). **Signal-validated:** `N/A` (each child establishes its own).

**Next action:** `/register` the highest-priority child as its own `EXP-<slug>`, lowest-tier-first; the cheap children (probes/replications) come before any confirmatory child.

---

## 6. `extend-experiment`

**Trigger:** the work clearly belongs to an existing `experiments/<exp>/` — adds a seed, a node, an ablation, a follow-up measurement, or refines an annotation on a live experiment.

**Decision questions:**
- Does an `experiments/<exp>/` already own this hypothesis?
- Is this an *addition* to that tree (a new node / seed / ablation), not a fresh unit of inquiry?

**Examples:** "add 4 more seeds to EXP-spectral-length-bias", "also ablate the layernorm in the same experiment", "re-run that node with the alternative reducer".

**Rationale template:** `"Extends EXP-<existing>; adds <node/seed/ablation> to the existing tree. Tier inherits from that experiment's experiment.json unless a node-level _Tier:_ override is declared."`

**Tier:** inherit from the existing `experiment.json` (a per-node `_Tier:_` override may raise it for a single node, CONVENTIONS.md §5) — never silently lower an existing experiment's tier. **Experiment:** the existing `EXP-<slug>`. **Signal-validated:** inherit the experiment's current state (`YES` if it has a promoted/probed signal, else `NO`).

**Next action:** `/plan-runs EXP-<existing>` to add the node(s) within `_Owns:_`/`_Depends:_` boundaries — then `/conflicts` before the new node executes.

---

## 7. `new-campaign`

**Trigger:** none of §1–§6 match. A genuinely new line of inquiry with its own falsifiable hypothesis and its own (not-yet-established) signal — typically the *first* experiment against a fresh project, or a new direction unrelated to any live tree.

**Decision questions:**
- Is this a new unit of inquiry (new hypothesis, new `EXP-<slug>`) rather than an extension of a live one?
- Is there a cheap signal yet? (Almost always NO for a brand-new campaign — which means its *first* experiment should itself be a `quick-probe`/`replicate-baseline`, not a confirmatory run.)

**Anti-pattern (the spike/wedge lesson):** routing the FIRST experiment of a fresh campaign straight to a confirmatory multi-seed sweep. A new campaign ships the *cheap probe* first; the expensive confirmatory machinery (N seeds, FDR, prereg hard-lock, confound-audit) is deferred behind the `Signal-validated` gate. Pre-signal confirmatory work is days of GPU spend on an effect that may not exist.

**Rationale template:** `"New line of inquiry, no live experiment owns it; open a campaign whose first experiment is a cheap probe — confirmatory machinery deferred behind the Signal-validated gate."`

**Tier:** `exploratory` for the campaign's first probe (escalates per §4 once signal validates). **Signal-validated:** `NO`.

**Next action:** `/register EXP-<slug> --tier=exploratory` for the opening probe — NOT a confirmatory sweep.

---

## Disambiguation

When two paths plausibly fit, prefer the one **closer to cheap signal**:

- `quick-probe` over `confirmatory-experiment` whenever `Signal-validated: NO` — the hard cheap-before-expensive gate.
- `replicate-baseline` over `quick-probe` when the claim is a delta over an unreplicated baseline (lock the floor first).
- `extend-experiment` over `new-campaign` when a live experiment clearly owns the work.
- `confirmatory-experiment` over `quick-probe` ONLY when a cheap signal already exists *and* the claim's stakes justify the multi-seed/prereg/confound-audit cost.
- `reject` over guessing when scope is genuinely unclear — a wrong expensive route costs a GPU budget, a clarifying question costs a sentence.

When in doubt, lower `Confidence` (`MEDIUM`/`LOW`), name the runner-up path in the Rationale, and recommend the *cheaper* of the two. The tier you recommend should be the lowest that still answers the question — escalation is always available later; un-spent budget is not recoverable after a premature confirmatory run.
