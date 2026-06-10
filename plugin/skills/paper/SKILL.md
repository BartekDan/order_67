---
name: paper
description: Generate the paper-grade IMRaD deliverable (paper.tex + paper.md + neurips-checklist.md + citations_needed.txt) from the VERIFIED substrate of a PROMOTEd experiment; returns a ## PaperReport block.
whenToUse: Auto-dispatched when an experiment reaches a PROMOTE / PROMOTE-WITH-CAVEAT ## Verdict (the research-world analog of order-66's end-of-slice /showcase dispatch). Also fire on "/paper <EXP-slug>", "write the paper", "draft the manuscript", "IMRaD writeup", "NeurIPS submission for <exp>". Do NOT fire on RERUN / REJECT / BLOCKED verdicts, or on any experiment whose status is not `audited`/`complete`.
isEnabled: test -d experiments
---

# /paper

## Static

### Summary
Synthesize the publication-grade manuscript for one experiment from its **already-verified** substrate — never from raw runs. Read `experiments/<exp>/{experiment.json, prereg.lock}`, the verifier's `## Verdict`, the `## AnalysisReport`, every surviving `## ConfoundAudit`, the `## ReproReport`, and the linted `## FigureReport`s, then write an IMRaD document obeying the **claims-carry-stats** linter (RULE-7) and the contribution-first / related-work-late structure. Before shipping, dispatch the `peer-reviewer` (red-team) subagent as an internal filter and auto-run the NeurIPS 16-item checklist as a self-audit. Emit `paper.tex`, `paper.md`, `neurips-checklist.md`, and `citations_needed.txt` under `results/<exp>/paper/`, then return the `## PaperReport` block. English only (D-006). This skill **never grades** the science (RULE-1) — it presents what the verifier already promoted, and flags every place the substrate is too thin to support a paper-grade claim.

### Preconditions
- `experiments/<exp>/experiment.json` exists, has a `rigor_tier`, and `status ∈ {audited, complete}`. A missing/unknown `rigor_tier` ⇒ treat as **publication** and surface it as a blocking `Open-gaps` entry (RULE-0).
- A `## Verdict` for `<exp>` exists in `trace/<exp>.md` with verdict line `PROMOTE` or `PROMOTE-WITH-CAVEAT`. If the latest verdict is `RERUN`/`REJECT`/`BLOCKED`, refuse with the exact message in Hard constraints. **The paper is a consequence of promotion, not a way to argue for it.**
- A `## AnalysisReport` for `<exp>` exists (this is the only legitimate source of effect sizes, CIs, and corrections — `/paper` must not recompute statistics).
- For every PROMOTEd *positive* finding, a `## ConfoundAudit` with `Survives: YES` exists (RULE-6). A positive claim with no surviving audit is demoted to Limitations as exploratory, never stated as a result.
- `results/<exp>/figures/` may contain figures already linted by `figure-smith` (`## FigureReport` with `Violations: none`). Unlinted figures are NOT embedded.

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `venue` — optional. Target venue label for the checklist header and `\documentclass` hints (default `neurips`). Only `neurips` triggers the ship-blocking 16-item gate; other values still run the checklist advisorily.
- `reviewer_rounds` — optional. How many peer-reviewer red-team passes to run before shipping (default `1`). The reviewer's accept is a **weak** signal, not ground truth (see Hard constraints).

### Output format
Writes four files under `results/<exp>/paper/`: `paper.tex`, `paper.md`, `neurips-checklist.md`, `citations_needed.txt`. Then RETURNS the following block to the orchestrator (and appends it to `trace/<exp>.md` so the block-lint hook and `/drift` can see it):

```
## PaperReport
- Experiment: EXP-spectral-length-bias
- Artifact: results/EXP-spectral-length-bias/paper/{paper.tex, paper.md, neurips-checklist.md, citations_needed.txt}
- Checklist: 14/16 Yes · items 4-8 = 5/5 Yes-with-evidence (PASS) · venue=neurips
- Citations-needed: 9 (background=4, method-prior-art=3, baseline=2)
- Open-gaps: prereg deviation in §Results.2 carried to Limitations as EXPLORATORY (RULE-5); rigor_tier=confirmatory so PROMOTE held, paper ships; item-15 (compute) not logged → flagged
```

Field semantics (mechanical — `hooks/block-schemas.tsv` greps these exact keys):
- **Experiment** — the `EXP-<slug>` ID.
- **Artifact** — the four written paths (always relative; RULE-2). If a file was intentionally skipped, name it and say why.
- **Checklist** — `<n>/16 Yes` overall, THEN the items-4–8 sub-tally as `items 4-8 = <m>/5 Yes-with-evidence (PASS|GATED)`, THEN the venue. `GATED` here mirrors a held paper, not a verdict on the science.
- **Citations-needed** — total count, then the per-role breakdown matching `citations_needed.txt` groupings.
- **Open-gaps** — every place the substrate could not support a paper-grade claim: prereg deviations carried to Limitations, missing checklist evidence, unlinted figures dropped, thin-N findings down-weighted, RULE-0 tier defaults. One clause each; this is the honest-debt ledger, not a self-grade.

### Hard constraints
- **Verified-substrate only.** `/paper` reads `## AnalysisReport`, `## Verdict`, `## ConfoundAudit`, `## ReproReport`, `## FigureReport` — it does **not** open `results/<exp>/runs/` to recompute a statistic. If a number isn't in the analysis substrate, it cannot appear in the paper. (Recomputing here would re-introduce the self-grade RULE-1 forbids.)
- **Refuse non-promoted experiments.** If the latest `## Verdict` for `<exp>` is not `PROMOTE`/`PROMOTE-WITH-CAVEAT`, refuse with exactly: `Experiment <exp> has no PROMOTE verdict (latest: <V>); /paper ships only promoted science.` Never write a paper to argue a claim past its verifier.
- **Claims-carry-stats (RULE-7).** Every quantitative sentence in a Results subsection MUST carry the mandatory core: effect size + CI (named variation source + named CI method) + n + the multiple-comparison correction used; PLUS a test statistic / p-value WHERE one was computed (a significance test was actually run). The RULE-7 triple (effect size, CI with named source+method, n) is required on every results sentence; the p-value is required only when a significance test was run — a bare p-value is not a result. A sentence asserting a number without the mandatory core is a lint failure — rewrite it or move it to Limitations as qualitative. The paper-skeleton template encodes this as the per-sentence checklist; run it over every Results paragraph before shipping.
- **Confirmatory vs exploratory split (RULE-5).** The Limitations section MUST separate confirmatory findings (in-prereg, audit-surviving) from exploratory ones. **Any prereg deviation is exploratory by definition** — it may be reported, but only in the exploratory half, never framed as a confirmatory result. At confirmatory/publication tiers the deviation already HARD-BLOCKED PROMOTE upstream, so if you are writing a paper the deviation was either re-registered or down-tiered; record which in `Open-gaps`.
- **Scope every claim (RULE-9).** Detection/generalization claims are scoped to the measured (often heavily-filtered) data distribution. Methods must state the distribution; Results must not over-generalize beyond it.
- **Cross-model claims need normalization (RULE-4).** If the paper makes any cross-model comparison, the Methods must name the normalization (relative depth / per-model z-score / PCA-to-common-dim / Procrustes). A raw cross-model number is refused, not softened.
- **Report N and correction (RULE-3).** Every Results subsection states the number of comparisons and the declared correction (Holm or BH) and the pre-registered primary metric. Secondary metrics are labelled secondary.
- **Null results are results (RULE-8).** A solid, adequately-powered null finding gets its own Results subsection. An underpowered null is reported as such and flagged in Limitations — never silently dropped.
- **Related work is LATE.** Intro is contribution-first (research questions + forward refs to the section that answers each); the related-work section sits after Results/Discussion, not before the contributions.
- **Peer-reviewer is a filter, not an oracle.** Run the `peer-reviewer` red-team subagent (`## Review`) `reviewer_rounds` times as an internal pass: address its `Major-issues` before shipping. Its `Recommendation: accept` is a **weak positive signal only** — it does NOT certify the science and never substitutes for the verifier's `## Verdict` (RULE-1). A reviewer reject on a Major issue you cannot fix from the substrate becomes an `Open-gaps` entry, not a silent edit.
- **NeurIPS items 4–8 are ship-blocking.** Auto-run the 16-item checklist as a self-audit. Items 4–8 (claims/limitations/theory-assumptions/experimental-reproducibility/compute) require **Yes-with-evidence** (a concrete pointer into the paper or substrate). If any of 4–8 is `No` or `Yes` without evidence, the paper is **GATED**: still write the files, but set `Checklist` to `GATED` and add the failing item to `Open-gaps`. Do not fabricate evidence to clear a gate.
- **No absolute paths** anywhere in the four output files or this skill (RULE-2). Use `${CLAUDE_PROJECT_DIR}`-relative paths in prose and `${CLAUDE_PLUGIN_ROOT}` for template reads. The `.tex` must compile without machine-specific paths.
- **English only** (D-006), regardless of the project-under-study's working language.

### Common mistakes (avoid)
1. **Writing the paper to win the argument the verifier already lost.** The paper presents promoted science; it is downstream of `## Verdict`, never a lever to overturn `RERUN`/`REJECT`/`BLOCKED`. Refuse on a non-promote verdict — this is RULE-1's never-self-grade law applied at the deliverable layer, not a heuristic.
2. **Recomputing statistics from the runs to "double-check" or fill a hole.** `/paper` is presentation; it reads `## AnalysisReport`. Re-deriving an effect size here forks the number of record and re-introduces self-grading. If the analysis substrate lacks a stat, the claim does not get stated — it goes to `Open-gaps`.
3. **Reporting a prereg deviation as a confirmatory result.** A post-hoc choice is exploratory forever (RULE-5/anti-HARKing). Putting it in a normal Results subsection with confirmatory framing launders exploratory work as confirmed. It belongs in the exploratory half of Limitations, full stop.
4. **Letting a bare p-value stand as a finding.** "X was significant (p<0.05)" fails the claims-carry-stats linter: no effect size, no CI (named variation source + method), no n, no correction — the mandatory RULE-7 core is absent. RULE-7 makes magnitude+consistency the result; significance alone is not.
5. **Treating peer-reviewer `accept` as a green light to skip the checklist gate.** The reviewer is one weak adversarial signal. Items 4–8 gate independently; a reviewer accept does not clear a missing-compute (item 15) or missing-reproducibility (item 8) evidence pointer.
6. **Embedding an unlinted figure to make the paper look complete.** Only figures with a `## FigureReport` `Violations: none` are embedded. An unlinted or violating figure is dropped and named in `Open-gaps` — a pretty unverified plot is worse than a missing one.
7. **Front-loading related work.** Burying the contributions under a survey inverts the contribution-first structure. Related work sits after Results; the Intro leads with the research questions and forward refs.

## Dynamic

Templates live under `${CLAUDE_PLUGIN_ROOT}/skills/paper/templates/`:
- `paper-skeleton.md` — the IMRaD section skeleton (abstract shape, contribution-first intro, numbered-equation Methods, per-finding Results, Limitations split, late related work, citations backlog) WITH the per-sentence claims-carry-stats rule inlined. Read it before drafting any prose.
- `neurips-checklist.md` — the 16 items, with items 4–8 marked ship-blocking and the Yes-with-evidence requirement. Read it before the self-audit.

The substrate this skill consumes already exists when it fires (gated by the preconditions); `/paper` does not re-derive it:
- `experiments/<exp>/experiment.json` (tier, dataset hashes, seed policy, prereg_hash)
- `experiments/<exp>/preregistration.md` — the `## Preregistration` block (hyphenated fields: Experiment, Hypotheses, Primary-metric, Splits, Analysis-plan, Prereg-hash, Rigor-tier) — and `experiments/<exp>/prereg.lock` — the frozen plan body (snake_case keys `primary_metric` / `splits` / `analysis_plan` + git commit + ISO timestamp + sha256). Read the `## Preregistration` block from `preregistration.md`; read frozen plan values for deviation detection from `prereg.lock` by its snake_case keys — never conflate the two (CONVENTIONS §4).
- `trace/<exp>.md` (`## Verdict`, `## AnalysisReport`, `## ConfoundAudit`(s), `## ReproReport`, `## FigureReport`(s))
- `results/<exp>/figures/` (only `Violations: none` figures are embeddable)

`peer-reviewer` is dispatched via the Task tool (subagent) and returns a `## Review` block; `reproducibility-checker`'s `## ReproReport` (already in trace) supplies the evidence pointer for NeurIPS items 7–8.

Algorithm:

1. Resolve `<exp>` from the `exp` parameter. Read `experiments/<exp>/experiment.json` with the Read tool. Capture `rigor_tier` (if missing/unknown ⇒ set `tier = publication`, append a RULE-0 gap to `open_gaps`). Capture `id`, `status`, `dataset_refs[].hash`, `seed_policy`, `prereg_hash`. If `status ∉ {audited, complete}`, refuse.
2. Locate the latest `## Verdict` for `<exp>` in `trace/<exp>.md`. If its verdict line is not `PROMOTE`/`PROMOTE-WITH-CAVEAT`, refuse with the exact message in Hard constraints. Capture `Tier applied`, `Claims`, `Required fixes`. A `PROMOTE-WITH-CAVEAT` caveat becomes a Limitations entry and an `Open-gaps` clause.
3. Read the `## AnalysisReport` (primary metric, effect size, CI + named variation source, correction, figure list) and every `## ConfoundAudit` (`Survives` flag per claim) for `<exp>`. Read the `## ReproReport` (seed-recorded, config-snapshot, env-pinned, NeurIPS-4-8 line). Partition the verifier's `Claims` into **confirmatory** (in-prereg + `Survives: YES`) and **exploratory** (post-hoc, prereg-deviating, or no surviving audit).
4. Read `${CLAUDE_PLUGIN_ROOT}/skills/paper/templates/paper-skeleton.md` with the Read tool. Draft, in order: abstract (4–6 sentences, single paragraph) → contribution-first Intro (explicit research questions + forward refs) → Methods (one numbered equation per metric; state the distribution scope per RULE-9; name any cross-model normalization per RULE-4) → one Results subsection per finding, each LED by its headline stat → Limitations (confirmatory half, then exploratory half holding every prereg deviation per RULE-5) → LATE related work → citations backlog.
5. Run the claims-carry-stats linter over every Results sentence: each quantitative sentence must carry the mandatory core — effect size + CI (named variation source + named CI method) + n + correction (RULE-7/3) — plus a test statistic / p-value where one was computed. Rewrite or demote any failing sentence. Build `citations_needed.txt` grouped by role (background / method-prior-art / baseline / contrasting-result).
6. Read `${CLAUDE_PLUGIN_ROOT}/skills/paper/templates/neurips-checklist.md`. Fill all 16 items into `neurips-checklist.md`; items 4–8 demand a Yes-with-evidence pointer (into the paper or the `## ReproReport`). Compute the overall `<n>/16` and the items-4–8 sub-tally. If any of 4–8 lacks evidence, mark the paper `GATED` and add the item to `open_gaps`.
7. Dispatch the `peer-reviewer` subagent (Task tool) `reviewer_rounds` time(s) over the drafted `paper.md`; it returns `## Review`. Address `Major-issues` you can fix from the substrate; record un-fixable Major issues in `open_gaps`. The reviewer `Recommendation` is logged but is a weak signal only — it never overrides the gate or the verdict.
8. Render `paper.tex` (compilable, no machine paths) and `paper.md` (same content, GitHub-readable) from the drafted sections. Write all four files to `results/<exp>/paper/`. Overwrite if present — paper artifacts are generated output.
9. Emit the `## PaperReport` block (Output format above) and append it to `trace/<exp>.md`.

Substrate freshness probe (advisory, before drafting):
`!{ls -1 experiments/${exp:-}/ 2>/dev/null; echo '---verdict/analysis in trace---'; grep -nE '^## (Verdict|AnalysisReport|ConfoundAudit|ReproReport|FigureReport)$' trace/${exp:-}.md 2>/dev/null; echo '---embeddable figures---'; ls -1 results/${exp:-}/figures/ 2>/dev/null}`

After running, `/brief` (the layman R&D-management sibling deliverable) typically fires on the same promoted experiment, consuming the same `## AnalysisReport` and this `## PaperReport`.
