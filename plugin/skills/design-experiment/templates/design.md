---
experiment: <EXP-slug>
artifact: design
version: "1"
created: <YYYY-MM-DD>
rigor_tier: <exploratory | pilot | confirmatory | publication>   # inherited from experiment.json
prereg_hash: <hash from ## Preregistration, or "none — exploratory">
hypotheses: [<H-001, ...>]
---

# Design — `<EXP-slug>`

> One falsifiable line: if `<H-001>` is true we will see `<the Quicklook number move past the line>`;
> if false we will see `<the null shape>`. The rest of this document is how we look without fooling ourselves.

## Quicklook

<!--
MANDATORY in ALL tiers. FIRST section after the heading. The research analog of order-66's
demo-first mandate: name the SINGLE inspectable number-or-plot that Task 1 (the Quicklook task in
the RunPlan) will emit within HOURS, on a thin slice of data, before any expensive run is launched.
It is the cheapest possible falsifier — the thing that, if it comes back flat/NaN/degenerate, kills
the experiment before it burns the GPU budget. If you cannot name a within-hours inspectable, the
experiment is not yet designed; stop and decompose further.
-->

`<one paragraph: the single number or one-panel plot Task 1 produces, the thin-slice it runs on
(e.g. 1 model layer × 200 questions, single seed), and the wall-clock it should take (target: hours,
not days). State what the plot's AXES are and which way is "signal".>`

**The inspectable:**

```
Kind:        metric | figure | notebook-cell        (exactly one; mirrors experiment.json:quicklook)
Artifact:    ${CLAUDE_PROJECT_DIR}/experiments/<EXP-slug>/runs/RUN-001/quicklook.{json|png|ipynb}
Reads:       <thin-slice dataset ref + version hash; e.g. proteus-qa@<hash>, layers [12], n=200>
Shows:       <e.g. balanced-accuracy of the length-probe vs the 0.50 chance line, single seed>
Signal line: <the pre-stated threshold that says "keep going" — e.g. bal-acc > 0.60 over 5 perms>
Kill line:   <the value that says "stop, the wedge is dead" — e.g. bal-acc ≤ 0.52 ⇒ null, write it up>
Wall-clock:  <target hours; this is NOT the full run>
```

## Methods

<!--
2–5 paragraphs of real methods prose. What is measured, on what, how. Reference the hypothesis IDs
and the pre-registered primary metric by name. Name the unit of scientific interest (the thing you
split on — RULE-10). State any cross-model normalization up front (RULE-4) if the design compares
models. Cite RULE-N inline where a methodological choice is law-driven. Do NOT bury a real design
decision here that should be a DDR below — if it could have gone the other way, it is a DDR.
-->

`<measurement>` — `<what signal, in what representation, extracted how>`.

`<estimator / model>` — `<the probe/classifier/statistic and where it is fit (train fold only,
inside CV — RULE-10)>`.

`<primary metric>` — `<the single pre-registered metric the verifier will grade, with its CI method
and named variation source (RULE-7)>`.

## Design-Decision-Records (DDR)

<!--
DDR count is TIER-CONDITIONAL (the research analog of order-66's mode-conditional ADRs). Tiers nest;
do NOT impose a higher tier's DDR floor on a lower tier — that re-creates the bloat the tier system
exists to prevent (RULE-0 / CONVENTIONS §2).
  - exploratory : 0 DDRs required (skip this section, or write "N/A — exploratory; decisions are cheap and reversible")
  - pilot       : 1 DDR required  (the single load-bearing methodological choice that gates scaling)
  - confirmatory: 1 DDR required  (same; plus it must name how a flip would force re-registration — RULE-5)
  - publication : 3+ DDRs required, EACH with ≥1 named rejected alternative + the trade-off accepted

A DDR is a methods choice that could have gone the other way and that affects what the result MEANS:
split unit, probe family, normalization scheme, baseline, correction method, seed count. A tooling
choice (which plotting lib) is NOT a DDR.
-->

### D-001 — `<decision title>`

`<2–5 sentences. State the choice, the alternative(s) considered, and the trade-off accepted. For
pilot/confirmatory the single DDR is the one that gates scaling to the expensive runs. For
confirmatory, name the signal that would force re-registration or a down-tier (RULE-5).>`

<!-- publication tier adds D-002, D-003, ... each with a named rejected alternative + trade-off -->

## Data & Compute Plan

<!--
MANDATORY in ALL tiers. The table is the contract /data-audit and /plan-runs read. Every dataset
row carries an IMMUTABLE content hash (closes the no-checksum gap; mirrors experiment.json
dataset_refs). Split is by the unit of scientific interest, never by row (RULE-10). The budget is
the HARD cap the autonomous tree search halts at (D-003) — GPU-hours AND dollars AND wall-clock.
-->

**Datasets & splits**

| Dataset | Version hash | Role | Split (by unit) | Rows / size |
|---|---|---|---|---|
| `<name>` | `<sha256/dvc-md5>` | train \| held-out \| eval | `<by qid, disjoint files>` | `<n>` |
| ... | ... | ... | ... | ... |

**Seeds**

| Tier | Seeds | N-justification |
|---|---|---|
| `<this experiment's tier>` | `<[0] | [0,1,2,3,4]>` | `<exploratory: single seed OK · confirmatory+: power analysis required>` |

**Compute budget (hard cap — /execute halts here)**

| Resource | Cap | Notes |
|---|---|---|
| GPU-hours | `<N>` | `<gpu type; remote host owned by harness via host-config.json>` |
| USD | `<$N>` | `<derived from GPU-hours × rate>` |
| Wall-clock (min) | `<N>` | `<for the whole tree, including reruns/seeds>` |

Remote execution: harness owns the `scp → launch → poll → fetch` loop via
`${CLAUDE_PROJECT_DIR}/experiments/<EXP-slug>/host-config.json` (gitignored; creds by env name only).

## Threats-to-Validity / out-of-scope

<!--
MANDATORY in ALL tiers. Two lists. Threats = the ways this design could produce a result that LOOKS
real but is not (these become the /confound-audit checklist — RULE-6). Out-of-scope = the claims
this experiment does NOT license, scoped to the actual (often heavily filtered) data distribution
(RULE-9). Be specific: "confound" is not a threat; "answer-length correlates with the label so the
probe may read length not content" is a threat.
-->

**Threats to validity** (seed the confound-audit; RULE-6):

- `<leakage / contamination threat; how the split or the audit guards it>`
- `<nuisance variable, e.g. answer-length; the planned nuisance-screen>`
- `<statistic-fragility threat; the planned statistic-swap>`
- `<dataset-distribution / selection threat; the scope it bounds the claim to (RULE-9)>`

**Out of scope** (claims this experiment does NOT license):

- `<generalization beyond the measured distribution>`
- `<cross-model claim deferred — needs explicit normalization (RULE-4)>`
- `<mechanism vs correlation: this experiment shows X, not why X>`

## Risks

<!-- Optional but recommended. Operational risks for /plan-runs and /execute (not validity threats). -->

- `<risk; mitigation — e.g. "remote host preempted mid-run → checkpoint every N steps, resume by seed">`
- ...
