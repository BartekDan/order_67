---
name: triage
description: Classify a free-form research request into one of seven paths — reject, replicate-baseline, quick-probe, confirmatory-experiment, decompose-agenda, extend-experiment, new-campaign — and recommend a rigor_tier. Returns a ## ResearchRouting block; the user confirms the path before any experiment artifact is written.
whenToUse: Invoked when the user describes a research question, hypothesis, idea, or finding-to-chase and it is unclear where it goes. Triggered by "does X cause Y?", "can we detect Z from activations?", "I think neuron N encodes ...", "should we run an experiment on ...", "let's investigate ...", "is this finding real?", "what should we look at next?", or any prompt that sounds like a new line of inquiry without a referenced experiment. ALWAYS prefer this over assuming a path or starting a run.
---

# /triage

## Static

### Summary
Take a free-form research request and run it through a 7-path decision tree (first-match-wins), then recommend a `rigor_tier`. Bias hard toward the two cheap paths — `replicate-baseline` and `quick-probe` — before authorizing an expensive `confirmatory-experiment`: a result is only worth a confirmatory GPU campaign once a *cheap signal* says the effect is plausibly real. This is the research-world analog of order-66's spike/wedge discipline. Return a `## ResearchRouting` block; **no experiment, hypothesis, prereg, or run artifact is written until the user confirms the path.**

### Preconditions
- `${CLAUDE_PROJECT_DIR}` is the project under study (e.g. `proteus-h-neurons`); the research-rulebook has been installed there as `CLAUDE.md`/`RESEARCH_RULEBOOK.md`.
- `${CLAUDE_PROJECT_DIR}/experiments/` may or may not exist yet — its absence is itself signal (routes toward `new-campaign`/`decompose-agenda`, never toward an in-flight path).
- This skill is **read-only**. It does not create `experiments/<exp>/`, `hypothesis.md`, `experiment.json`, or any trace entry.

### Parameters
- `request` — required. Free-prose description of the research question, hypothesis, idea, or finding the user wants to pursue.
- `rigor_tier` — optional. An explicit caller override (`exploratory|pilot|confirmatory|publication`). If omitted, /triage *recommends* one; it never silently assumes the strictest the way RULE-0 governs a *missing-where-required* tier on an existing experiment.

### Output format
A `## ResearchRouting` RETURN FORMAT block (CONVENTIONS.md §4; fields verbatim from `hooks/block-schemas.tsv`):

```
## ResearchRouting
- Path: <reject | replicate-baseline | quick-probe | confirmatory-experiment | decompose-agenda | extend-experiment | new-campaign>
- Experiment: <EXP-<slug> suggested-or-existing | "n/a">   # n/a only for reject
- Rigor-tier: <exploratory | pilot | confirmatory | publication>   # the RECOMMENDED tier for this path
- Rationale: <2-4 sentences: why THIS path beats the cheaper neighbour, and why THIS tier>
- Next action: <one concrete next command, e.g. "/register EXP-spectral-length-bias --tier=pilot" or "no run — inspect results/<exp>/baseline.json first">
- Confidence: <HIGH | MEDIUM | LOW>
- Signal-validated: <YES | NO | N/A>   # NO ⇒ no cheap signal yet that the effect is real ⇒ bias toward quick-probe
```

### Hard constraints
- **Exactly one path.** Never `quick-probe OR confirmatory-experiment, depending on...`. Pick one. If genuinely uncertain which line of inquiry the user means, return `reject` with rationale `"ambiguous; need clarification on <specific question>"` — do not guess into an expensive path.
- **Cheap-before-expensive (the spike/wedge analog).** `confirmatory-experiment` is only legal when a cheap signal already exists that the effect is real. If `Signal-validated: NO`, you MUST route to `quick-probe` (or `replicate-baseline`) instead, regardless of how confident the *user* sounds. The failure mode this prevents is burning a multi-seed GPU budget to confirm an effect that a 20-minute probe would have shown was noise.
- **`Signal-validated` is mandatory and is the gate.** Set `YES` only when a prior cheap artifact exists in `${CLAUDE_PROJECT_DIR}/results/<exp>/` or `experiments/<exp>/runs/` — a single-seed quick-probe, a replicated baseline, a logged effect — that already points at the effect being real. Set `N/A` only for `reject` and for `decompose-agenda` (whose children inherit/establish their own signal). Otherwise `NO`.
- **Rigor-tier is RECOMMENDED, never silently strictest.** RULE-0's fail-loud-to-`publication` governs an *existing* experiment whose tier metadata is missing where a check requires it — that is `/register`'s and the verifier's job, not routing. At triage you recommend the *lowest tier that still answers the question*: tiers nest cumulatively and imposing a higher tier's checks on cheap exploratory work re-creates the exact bloat the tier system exists to kill (CONVENTIONS.md §2). If the caller passed an explicit `rigor_tier`, echo it and note any mismatch with your recommendation in the Rationale.
- **No files written.** /triage emits the block and stops. Creating `experiments/<exp>/`, an `experiment.json`, a hypothesis card, or a trace line before the user confirms the path is a hard violation (RULE-2 plugin discipline does not relax this).
- **Suggested experiment IDs match the scheme:** `EXP-<slug>`, kebab-case, ≤ 30 chars (CONVENTIONS.md §1). `EXP-spectral-length-bias` ✓; `EXP-Does Spectral Energy Predict Answer Length?` ✗.
- **Read frontmatter / index lines only when scanning** the agenda and existing experiments (state-tier caps, CONVENTIONS.md §7). Do not load full `hypothesis.md` or `analysis.md` bodies during routing — routing is cheap by construction.
- **Confirmatory implies prereg.** When you do route to `confirmatory-experiment`, the Rationale must name that a prereg deviation will HARD-BLOCK PROMOTE at this tier (RULE-5 / D-005), so the user opts in with eyes open.

### Common mistakes (avoid)
1. **Routing an exciting-sounding-but-unprobed hypothesis straight to `confirmatory-experiment`.** This is the #1 budget-burner — the analog of order-66's "we built production plumbing for an unvalidated wedge." If no cheap signal exists yet (`Signal-validated: NO`), the correct route is `quick-probe`: one seed, one split, the smallest measurement that could falsify the idea. Confirm the signal *first*, then spend the multi-seed budget.
2. **Skipping `replicate-baseline` and trusting a number from a paper/README/prior run.** Before you measure a *delta* over a baseline, the baseline must reproduce on *this* data + code + commit. An unreplicated baseline silently poisons every downstream effect size (RULE-7). When the request hinges on "X beats the baseline," route to `replicate-baseline` first.
3. **Recommending `publication` (or `confirmatory`) tier for a one-off curiosity.** Tiers nest; a quick "is there anything here?" probe is `exploratory`. Imposing FDR correction, N≥k seeds, and a NeurIPS checklist on a throwaway probe is exactly the bloat §2 forbids. Match the tier to the *question's stakes*, not to ambient anxiety about rigor.
4. **Routing a request that clearly extends a live experiment to `new-campaign`.** If the work adds a seed, a node, an ablation, or a follow-up measurement to an existing `experiments/<exp>/`, it is `extend-experiment` (mode/tier inherits from that experiment's `experiment.json`). `new-campaign` is for a genuinely new unit of inquiry with its own hypothesis.
5. **Picking `decompose-agenda` when the user already named the question.** `decompose-agenda` answers "what should we look at next?" by breaking a research agenda item into experiment-sized units. If the user said "let's test whether neuron N tracks length," that is a concrete question — route it directly (`quick-probe`/`confirmatory-experiment`), not through decomposition.
6. **Treating a null or a self-retraction as `reject`.** "Is this finding actually real?" about a *promoted* claim is a first-class research question — route it to `confirmatory-experiment` (with a mandatory confound-audit, RULE-6) or `quick-probe`, not `reject`. `reject` is for out-of-scope, duplicate-in-flight, or unanswerably-vague requests only. Null results are results (RULE-8).
7. **Marking `Signal-validated: YES` off the user's confidence rather than an artifact.** The gate is evidentiary, not rhetorical. "I'm sure this is real" is not a signal; a logged single-seed effect in `results/<exp>/` is. When no such artifact exists, the honest value is `NO`, and that pushes the route cheap.

## Dynamic

Templates: `${CLAUDE_PLUGIN_ROOT}/skills/triage/templates/path-decision-tree.md`. Read it with the Read tool and walk it **top-to-bottom, first-match-wins** — it lays out all 7 paths in priority order with the decision questions and the cheap-before-expensive bias baked into the ordering.

The project under study lives at `${CLAUDE_PROJECT_DIR}`. /triage is read-only — do not write anything until the user confirms the returned `Path`.

Does an experiment tree exist yet? (its absence biases toward `new-campaign`/`decompose-agenda`, never an in-flight path):
!{ls -d ${CLAUDE_PROJECT_DIR}/experiments/ 2>/dev/null && ls ${CLAUDE_PROJECT_DIR}/experiments/ 2>/dev/null | grep -v '^agenda.md$' || echo "(no experiments/ yet — fresh project)"}

Existing experiment IDs (to detect `extend-experiment` and to avoid suggesting a duplicate `EXP-<slug>`):
!{for d in ${CLAUDE_PROJECT_DIR}/experiments/*/; do [ -f "$d/experiment.json" ] && grep -o '"id"[^,}]*' "$d/experiment.json" | head -1; done 2>/dev/null || echo "(none)"}

Research agenda (frontmatter / one-line pointers only — drives `decompose-agenda`; capped per CONVENTIONS.md §7):
!{head -40 ${CLAUDE_PROJECT_DIR}/experiments/agenda.md 2>/dev/null || echo "(no agenda.md — nothing to decompose)"}

Cheap-signal scan — `Signal-validated` evidence. A prior quicklook/baseline/single-seed effect already on disk lets you set `Signal-validated: YES`; an empty scan forces `NO` (⇒ route toward `quick-probe`/`replicate-baseline`):
!{ls ${CLAUDE_PROJECT_DIR}/results/*/baseline.json ${CLAUDE_PROJECT_DIR}/results/*/quicklook.* ${CLAUDE_PROJECT_DIR}/experiments/*/runs/*/metrics.json 2>/dev/null | head -20 || echo "(no cheap-signal artifacts on disk → Signal-validated: NO)"}

Promoted/retracted claims already in the trace (so "is this finding real?" routes to confirmatory re-test, not `reject`):
!{grep -rhE 'PROMOTE|RETRACT|REJECT' ${CLAUDE_PROJECT_DIR}/trace/*.md ${CLAUDE_PROJECT_DIR}/FINDINGS.md 2>/dev/null | head -15 || echo "(no prior claims)"}
