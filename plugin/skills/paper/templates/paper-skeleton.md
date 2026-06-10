# IMRaD paper skeleton (order-67 /paper)

This is the section skeleton `/paper` fills from the **verified substrate** of a PROMOTEd
experiment. It is authoring guidance, not a string-substitution template: replace each `<…>`
slot with model-authored prose grounded in the `## AnalysisReport` / `## Verdict` /
`## ConfoundAudit` / `## ReproReport`. English only (D-006). No absolute paths (RULE-2) — refer to
project artifacts as `${CLAUDE_PROJECT_DIR}`-relative.

The same content is rendered twice: `paper.tex` (compilable, venue `\documentclass`) and
`paper.md` (GitHub-readable). Keep them in lockstep — one source of sentences, two renderers.

---

## The claims-carry-stats rule (RULE-7 — applies to EVERY Results sentence)

Before a quantitative sentence may ship in a Results subsection, it must carry **all five**:

| Slot | Source | Example fragment |
|------|--------|------------------|
| effect size | `## AnalysisReport` `Effect-size` | `balanced-accuracy +0.18 over the length-only baseline` |
| test statistic | `## AnalysisReport` | `(permutation t = 4.1)` |
| p-value | `## AnalysisReport` | `p = 0.002` |
| n | `## AnalysisReport` / prereg `Splits` | `n = 24 held-out qids` |
| correction | `## AnalysisReport` `Correction` (RULE-3) | `Holm-corrected over 6 comparisons` |

A sentence missing any slot **fails the linter**: either rewrite it to carry all five, or demote
it to qualitative prose / Limitations. A bare p-value ("X was significant, p<0.05") is NOT a
result. Report magnitude AND consistency (a CI/std with a *named* variation source — seed / init /
split — and a *named* CI method — bootstrap / closed-form), never significance alone.

Worked pattern (good):
> The H-neuron probe separates long- from short-answer items at **balanced-accuracy 0.78**
> (**+0.18** over the length-only baseline, 95% bootstrap-over-seeds CI [0.71, 0.84],
> permutation t = 4.1, **p = 0.002**, **n = 24** held-out qids, **Holm-corrected over 6
> comparisons**), surviving the label-permutation null and the answer-length nuisance screen.

Anti-pattern (rejected):
> The probe was significantly better than baseline (p < 0.05).

---

## 0. Title + author block
`<title — names the mechanism + the scoped distribution, not the hype>`
Authors / affiliations as supplied; never invent. Footnote the experiment ID `<EXP-slug>` and the
`prereg_hash` so the manuscript is traceable to its lock.

## 1. Abstract
**4–6 sentences, ONE paragraph.** Shape: (1) the question/gap; (2) what we did (method in one
line, with the scoped distribution per RULE-9); (3) the headline confirmatory result *with its
effect size and CI* (claims-carry-stats applies here too); (4) one sentence of scope/limitation;
(5–6) the contribution and why it matters. No citations in the abstract. No forward refs to figure
numbers. If the headline finding is a null (RULE-8), say so plainly and state the power.

## 2. Introduction (contribution-first; related work is LATE)
- Open with the gap and the **explicit research questions** as a short enumerated list:
  - **RQ1.** `<question>` — answered in §4.1.
  - **RQ2.** `<question>` — answered in §4.2.
  - (one forward ref per RQ to the Results subsection that answers it)
- State the contributions as a bullet list, each a single declarative claim, each tagged
  **(confirmatory)** or **(exploratory)** so the reader knows which carry the prereg's weight
  (RULE-5). Confirmatory = in-prereg + confound-audit-surviving; everything else is exploratory.
- Do **not** survey prior work here beyond the one or two refs needed to frame the gap. The full
  related-work section is §6.

## 3. Methods
- **Data & scope (RULE-9).** Name the dataset(s) and their content `hash` (from
  `experiment.json` `dataset_refs`), the split unit (qid-level, disjoint files — RULE-10), and the
  *exact distribution* every claim is scoped to (e.g. "items filtered to single-token answers,
  length ≤ 8"). Every downstream claim inherits this scope; do not generalize past it.
- **Metrics — one numbered equation each.** For every metric reported, give a numbered display
  equation and a one-line operational definition. Example:
  $$\text{bal-acc} = \tfrac{1}{2}\!\left(\tfrac{TP}{TP+FN} + \tfrac{TN}{TN+FP}\right) \tag{1}$$
  $$d = \frac{\bar{x}_1 - \bar{x}_0}{s_{\text{pooled}}} \tag{2}$$
  Reference equations by number in Results ("by Eq. 1").
- **Statistical protocol.** State the pre-registered **primary metric**, the number of comparisons,
  and the **correction** (Holm or Benjamini–Hochberg — RULE-3); the variation source for every CI
  (seed / init / split) and the CI method (bootstrap / closed-form — RULE-7); the confound-audit
  thresholds *as frozen in the audit header* (RULE-6). Secondary metrics are labelled secondary.
- **Cross-model normalization (RULE-4, only if applicable).** If any claim compares across models,
  name the normalization (relative depth / per-model z-score / PCA-to-common-dim / Procrustes). A
  raw cross-model number is not reported.
- **Reproducibility.** Per-run seed, full config, git commit, env/lockfile, dataset content-hash —
  cite the `## ReproReport`. This paragraph is the evidence pointer for NeurIPS items 7–8.

## 4. Results (ONE subsection per finding; each LED by its headline stat)
For each promoted finding, a subsection whose **first sentence is the headline stat** (full
claims-carry-stats five-slot sentence), then:
- the confound-audit outcome (which nulls/screens it survived — RULE-6),
- the figure (only if `figure-smith` reported `Violations: none`; otherwise omit and note in
  Limitations),
- secondary/supporting metrics, each labelled secondary.
Null findings get their own subsection and are reported as findings (RULE-8), with the power that
makes the null clean. **Do not** place any prereg-deviating / post-hoc result here as a confirmatory
finding — those live in §5 exploratory.

### 4.1 `<RQ1 finding — headline-stat-first>`
### 4.2 `<RQ2 finding — headline-stat-first>`
### 4.x `<null result, if any — headline + power>`

## 5. Limitations (confirmatory vs exploratory — RULE-5)
Two explicit subsections. This split is mandatory.
- **5.1 Confirmatory limitations.** Caveats on the in-prereg, audit-surviving findings: scope
  bounds, N, seed count, CI width, any `PROMOTE-WITH-CAVEAT` caveat from the `## Verdict`.
- **5.2 Exploratory findings & deviations.** Every prereg deviation and post-hoc analysis lands
  here, explicitly framed as exploratory (hypothesis-generating, not confirmed). State what would
  be needed to confirm it (re-register + a fresh confirmatory run). Never launder these as results.

## 6. Related work (LATE — after Results/Discussion)
Position the contribution against prior art now that the reader knows what it is. Group by what the
prior work establishes vs. what this experiment adds. Pull citation slots from §7; do not invent
references — every uncited assertion becomes a `citations_needed.txt` entry.

## 7. Citations-needed backlog → citations_needed.txt
Every assertion that needs a reference but lacks one becomes a line in `citations_needed.txt`,
**grouped by role**:
- `background:` — framing/motivation claims.
- `method-prior-art:` — the technique's lineage (probing, SAE, causal-mediation, etc.).
- `baseline:` — the comparison method(s) the effect size is measured against.
- `contrasting-result:` — prior findings this result agrees or disagrees with.
Format: one `role: <claim or sentence locus> — <what citation is needed>` per line. The
`## PaperReport` `Citations-needed` field reports the total and this per-role tally.

## Appendix (optional)
Full hyperparameters, additional seeds, extended confound-audit tables, datasheet/model-card
pointers (publication tier). None of this relaxes the main-text claims-carry-stats rule.
