# Hypothesis card format (`H-NNN`)

One card per falsifiable hypothesis, appended to `experiments/<exp>/hypothesis.md` in `H-NNN`
order. The card is the research analog of an EARS requirement (order-66 `templates/ears.md`): a
hypothesis that cannot be cast into this shape is REFUSED at `/register`, exactly as a requirement
that is not EARS-shaped is refused at `/decompose`.

Every card MUST have all five fields below. A card missing **Falsification** or whose **Prediction**
rests on subjective / visual-only judgement ("looks clustered", "appears sharper", "monosemantic by
inspection") is non-registrable — there is no eyeballing (RULE-7).

---

## The EARS-shaped prediction (mandatory canonical form)

The prediction line is one of these two shapes. The falsification criterion is the negation made
explicit, so the verifier can grade it mechanically (RULE-1: the verifier grades, the proposer never
self-grades).

### A. Threshold (most hypotheses)

> **When** `<model + config>` **is evaluated on** `<held-out set, keyed by unit of interest>`,
> **it shall achieve** `<primary metric>` `>= <threshold>`.

- Falsification: `<primary metric> < <threshold>` on that held-out set ⇒ **H rejected**.

### B. Difference / effect (comparative hypotheses)

> **When** `<model + config A>` **and** `<config B>` **are evaluated on** `<held-out set>`,
> **the difference in** `<primary metric>` **shall be** `>= <effect-size threshold>` with the
> pre-registered CI excluding `<null value>`.

- Falsification: the CI for the difference includes `<null value>`, OR the effect size is below
  `<threshold>` ⇒ **H rejected**.

Both shapes name a *computable* metric and a *numeric* threshold. "Better", "clearer", "more
separable" are not metrics. Pick the metric, pick the threshold, or the card is refused.

---

## Card template

```markdown
### H-NNN — <one-line title>

- **Prediction (EARS):** When <model + config> is evaluated on <held-out set, keyed by unit>,
  it shall achieve <primary metric> >= <threshold>.
  - Variant B (difference form): … the difference in <metric> shall be >= <effect> with the
    pre-registered CI excluding <null>.

- **Falsification criterion:** <the exact observation that REJECTS this hypothesis>.
  Must be the mechanical negation of the prediction, gradable by the results-verifier without
  human judgement. E.g. "balanced-accuracy on the qid-disjoint held-out fold < 0.65" ⇒ reject.
  If you cannot write this line, the hypothesis is not registrable — REFUSE.

- **Named confounds:** <bullet list of the specific nuisance variables that could produce the
  predicted metric WITHOUT the claimed mechanism>. Each named confound must map to one leg of the
  RULE-6 confound-audit that /confound-audit will run on a positive:
  - label-permutation null — what shuffles, what the null distribution is.
  - nuisance screen — the concrete nuisance (e.g. answer length, token count, class prior).
  - statistic-swap — the alternative estimator that should agree.
  - alt-preprocessing — the preprocessing choice the result must survive.
  "None" is almost never correct; an empty confound list is a refusal-worthy smell.

- **Cost:** <GPU-hours · $ · wallclock> to test this card to the registered tier. Must fit inside
  the experiment's declared budget (experiment.json:compute.budget); a card that cannot be tested
  within budget is flagged, not registered.

- **Novelty:** <what this would establish that is not already known>, with the closest prior result
  it extends or contradicts (cite, or "no known prior" — never blank). Novelty is CONTEXT, not a
  score; /register never grades plausibility (RULE-1).

- **Tier:** <exploratory|pilot|confirmatory|publication> — defaults to the experiment tier; an
  explicit per-card override is honored only if it is <= the experiment tier (you may down-tier a
  card, never up-tier it past the registration).
```

---

## Tier-conditional strictness (do not over-impose — CONVENTIONS §2)

| Tier | What the card additionally requires |
|------|-------------------------------------|
| `exploratory` | Prediction + Falsification only. Metric/threshold may be coarse; no CI demanded. |
| `pilot` | + the held-out set in the prediction must be a real declared split (RULE-10); a cheap quicklook signal is named. |
| `confirmatory` | + threshold tied to an effect size (RULE-7); ≥ k seeds with justification; the named confounds populate the RULE-6 audit header; correction named if the card is one of several. |
| `publication` | + the card is mapped to the relevant NeurIPS checklist items (claims↔evidence, items 4–8). |

Never demand a CI method or seed-justification on an `exploratory` card. Never let a `confirmatory`
card ship with an empty confound list or an effect-size-free threshold.

---

## Refusal messages (emit verbatim, then stop)

- No falsification: `"H-NNN has no falsification criterion. State the exact observation that would
  REJECT it (the mechanical negation of the prediction), or it cannot be registered (RULE-5/7)."`
- Visual/subjective: `"H-NNN rests on visual/subjective judgement ('<quoted phrase>'). Rewrite as a
  computable metric with a numeric threshold — no eyeballing (RULE-7)."`
- Empty confounds at confirmatory+: `"H-NNN names no confounds. A confirmatory positive must survive
  a confound-audit; name the nuisance(s) the audit will screen (RULE-6), or down-tier."`
- Over-budget: `"H-NNN costs <X> GPU-h, exceeding the experiment budget <Y>. Down-scope, raise the
  budget explicitly, or split into a pilot card first."`
