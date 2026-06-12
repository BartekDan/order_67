<!--
  Template-rev: 3.0   (bump on ANY structural change; /atlas escalates to --full on mismatch)
  ATLAS.md template for order-67 /atlas v3 — THE deep single-place dossier for a research
  project (the science + the mechanics + the LAYMAN TRACK). Sits beside STATUS.md (the thin board atlas.py renders
  from atlas.yaml) and is rendered to ATLAS.html by skills/atlas/render_html.py.
  Placeholders in {{DOUBLE_BRACES}}; repeat {{#EXPERIMENTS}}...{{/EXPERIMENTS}} per experiment,
  ordered by the exploration tree (parents before children, then ledger order).
  Generated output — do not hand-edit; re-run /atlas.

  THE DEPTH BAR (binding — the research translation of order-66's):
  a competent researcher NEW to this project, reading ONLY this document, must be able to answer:
    (1) what each experiment ACTUALLY computes, end to end (data → method → metric → claim);
    (2) where every reported number comes from — which runs, which code/symbol, which CI method;
    (3) what was FROZEN at pre-registration vs decided post-hoc;
    (4) what data/compute artifacts exist (runs bundles, stats, figures), who writes/reads them,
        their shape;
    (5) why each load-bearing design decision was made and what evidence would flip it — and,
        for every dead-end, WHY it died (the lesson kept).
  If a section can't answer these for its experiment, it is too shallow — go back to the sources
  (Run Notes, DDR full text, prereg.lock, the actual code, the run bundles) and extract more.

  SOURCING (what each part is built FROM — see SKILL.md):
  science    ← hypothesis.md (FULL falsifiable H-NNN cards) + experiment.json + the campaign README
  mechanics  ← design.md methods (full) + runs.md incl. ALL Run Notes + THE ACTUAL CODE the runs
               executed (cite path · symbol() · line) + runs/RUN-*/ bundles (config.resolved.json,
               metrics.json, seed.txt, env.lock, dataset.hash) + results/stats.json + figures
  decisions  ← design.md DDRs FULL TEXT (decision + alternative + trade-off + flip trigger)
  thresholds ← preregistration.md + prereg.lock (FROZEN values, marked as such) vs anything
               post-hoc (marked POST-HOC — this distinction is load-bearing, RULE-3/RULE-6)
  verdicts   ← verdict.md (results-verifier), audit.md (confound audit, Survives: YES/NO),
               data-audit.md (leakage gate)
  gotchas    ← Run Notes + verifier/auditor catches + trace/<exp>.md

  CITATION RULE: every mechanical claim cites `path` + symbol (+ line as of generation; symbol
  primary). Every NUMBER cites its artifact (stats.json key, metrics.json field, prereg.lock
  hash). No citation -> no claim. HONESTY: never invent; unverifiable -> "unverified — inferred
  from <source>"; unknown -> "(unknown)". Numbers come from artifacts, never from memory.

  THE LAYMAN BAR (v3, binding, enforced by the layman-judge agent): every "In plain words"
  section must let an intelligent reader with ZERO scientific or technical background genuinely
  follow the SAME ground the expert sections cover: what question was asked, what was actually
  done step by step (mirroring the pipeline walk's numbering 1:1), what every reported number
  means and where it comes from — including, in plain words, whether each pass/fail rule was
  promised BEFORE the data was seen or chosen after — and why a result was believed, doubted, or
  thrown out. Rules: no unexplained term, ever — any unavoidable scientific or technical word
  gets an everyday explanation in parentheses at FIRST use; analogies must carry the actual
  step, not just the vibe; never reference the expert sections; as DETAILED as the mechanics —
  a translation, not a teaser. Headings MUST start with "In plain words" (the renderer keys its
  panel styling on that prefix; the layman-judge locates sections by it). A retraction story is
  layman GOLD — tell it straight: what looked true, what test caught it, what the lesson was.

  THE PAPER BAR (v3, binding, enforced by the paper-author agent): the "For the paper" track must
  let an ML engineer who is fluent in ML/statistics but has NEVER seen this project draft every
  IMRaD section of a research paper from this document ALONE. It is NOT a plain-words translation
  (that is the layman bar) and NOT a reference walk (that is the mechanics) — it is the RESEARCH
  STORY: the project head's "For the paper" gives the program's narrative arc (the question, why
  this line of work, the chronological journey EXP→EXP with what each result implied for the next,
  the through-line findings, the one-sentence contribution, the scope). Each experiment's "For the
  paper" gives: WHY this experiment was run and what the prior result/gap motivated it (the
  journey link), the hypothesis in publication terms, a bare-bones methods recap that names every
  project-specific method (pointing into the mechanics/tables for exact symbols, never restating
  them), a reading-guide to the artifacts a paper would CITE (which result file/key/commit backs
  which claim), what a paper would CLAIM here and the limits. Assume ML literacy (AUROC, logistic
  probe, permutation null need no gloss); explain only what is specific to THIS project. After
  assembling ATLAS.md, /atlas MUST spawn the paper-author agent (subagent type
  order-67-research-harness:paper-author:paper-author; returns ## PaperReadinessReport with a draft
  skeleton, findings, and detailed author-questions) and revise the flagged sections to answer its
  questions IN the text, looping until the agent returns READY-TO-DRAFT (convergence); hard cap 10
  rounds; ship after 10 carrying residual findings into AtlasReport.
  Headings MUST start with "For the paper" (the renderer styles the panel and the paper-author
  locates the sections by that prefix). The paper-author judges COMPLETENESS-OF-THE-RECORD, never
  correctness (results-verifier/peer-reviewer) and never plain-language (layman-judge).

  DIAGRAMS (v3): declarative ```flow / ```graph DSL blocks (grammar + binding authoring rules in
  templates/diagram-dsl.md) — render_html.py lays them out deterministically as SVG. One idea
  per diagram, <= ~15 nodes, EVERY edge labeled with what moves. ASCII art is retired for
  diagrams; plain ``` blocks remain for genuinely textual content. EXCEPTION: the exploration
  tree stays the VERBATIM ASCII block copied from the freshly regenerated STATUS.md (single
  source = atlas.yaml) — never re-drawn, never converted.

  LENGTH: per-experiment section target 130–350 lines including the layman section.
-->
---
generated: atlas
artifact: atlas-deep
generated_at: {{GENERATED_AT}}
project: {{PROJECT}}
git_anchor: {{GIT_ANCHOR}}
regen_mode: {{REGEN_MODE}}
template_rev: "3.0"
---

# {{PROJECT}} — ATLAS (deep dossier)

> **What this document is:** the single place holding everything — the science AND the
> mechanics — for every experiment in this research project, including the dead-ends and why
> they died. Generated by `/atlas` from the ledger, the experiment files (hypothesis cards, DDR
> full text, ALL Run Notes, prereg locks, verdicts, audits), the actual run code, and the run
> bundles. The thin "where are we" board is [STATUS.md](STATUS.md) (rendered from `atlas.yaml`).
> Generated {{GENERATED_AT}} at commit {{GIT_ANCHOR}}. Do not hand-edit — re-run `/atlas`
> (incremental per experiment, `--full` for a complete rebuild).

## In plain words — what this research project is doing and finding

{{PROGRAM_LAYMAN}}
<!-- THE LAYMAN ENTRY POINT (judged by layman-judge — see LAYMAN BAR above). For a reader with
     zero background: what question this program is trying to answer and why anyone cares; a
     numbered walk of how an answer gets made here (data collected -> method applied -> runs ->
     checks designed to kill false positives -> a claim that survives or is retracted),
     mirroring the program data-flow below in everyday words; then "The numbers you will meet
     in this document:" — every recurring headline number explained in words, including whether
     its pass/fail rule was promised in advance. Where the program's story is a retraction,
     tell it straight — what looked true, what test caught it, what lesson was kept. -->

## For the paper — the research story of this program

{{PROGRAM_PAPER_NARRATIVE}}
<!-- THE PAPER ENTRY POINT (judged by paper-author — see PAPER BAR above). For an ML engineer
     fluent in ML/stats but NEW to this project, tasked to write the paper: (1) the research
     question and why it matters, in publication terms; (2) the one-sentence CONTRIBUTION claim;
     (3) the JOURNEY — a chronological arc across the experiments, each link stating what the
     previous result/gap implied that made the next experiment necessary ("X showed Y, so we ran
     Z to test W"); (4) the through-line findings that recur across experiments (the paper's
     Discussion spine); (5) the scope and the headline limits. Assume ML literacy; explain only
     project-specific names/choices. Point forward to the inventories/tables for specifics; do not
     restate them. This is the program's Introduction + Discussion spine, not a summary of numbers. -->

## The program at a glance

{{PROGRAM_PARAGRAPH}}
<!-- 1 paragraph: the research question(s) this project attacks, in plain scientific terms,
     and where the program currently stands (you-are-here, from the ledger). -->

### The exploration tree (every path, including the dead ones)

```
{{EXPLORATION_TREE_VERBATIM}}
```
<!-- COPIED VERBATIM from the freshly regenerated STATUS.md tree block (source: atlas.yaml).
     Includes lifecycle glyphs and each dead-end/superseded node's `why`. Never re-draw it. -->

### Program data-flow (how a claim gets made)

```flow
{{PROGRAM_DATAFLOW_DSL}}
```

{{PROGRAM_DATAFLOW_LEGEND}}
<!-- ONE ```flow DSL block (grammar: templates/diagram-dsl.md): data sources → preprocessing →
     method/model → runs (seeds × configs) → metrics.json → /analyze stats → verifier +
     confound-audit gates → claim/verdict → /brief + /paper. <= ~15 nodes; EVERY edge labeled
     with WHAT moves; classes semantic (.src/.engine/.artifact/.surface/.user). Numbered
     one-line legend below. -->

### Compute & runtime surfaces

| Surface | Kind | What it does | How to run / reach |
|---|---|---|---|
{{#SURFACES}}| {{SURFACE}} | {{KIND}} | {{WHAT}} | {{HOW}} |
{{/SURFACES}}
<!-- Every CLI/script entrypoint, the remote-GPU dispatch path (host-config.json: scp → launch →
     poll → fetch) when used, quicklook checkpoints, notebooks. Each exactly once. -->

### Data & results artifacts

| Artifact | Producer | Consumers | Shape (1 line) |
|---|---|---|---|
{{#ARTIFACTS}}| `{{PATH}}` | {{PRODUCER}} | {{CONSUMERS}} | {{SHAPE}} |
{{/ARTIFACTS}}
<!-- Datasets (+ content hashes), runs/RUN-*/ bundle files, results/<exp>/stats.json, figures,
     prereg.lock, the ledger itself. Open the files; give real 1-line shapes. -->

### Dependency & retraction-cascade graph

```graph
{{DEPENDENCY_GRAPH_DSL}}
```
<!-- ```graph DSL block: one node per ledger experiment (label "EXP-id\n(lifecycle)"), edges
     from `parent:` + `_Depends:_` evidence, each labeled with what the dependent cites. -->

**How this graph is built:** nodes are the ledger's experiment entries; tree edges come from each
node's `parent:` in `atlas.yaml`; evidence edges come from `_Depends:_` annotations in each
experiment's `runs.md` (a claim citing a RETRACTED dependency must cascade — `/drift` sweeps
this). The graph is DECLARED structure; {{DEP_GRAPH_DISCREPANCIES}}.
<!-- DEP_GRAPH_DISCREPANCIES completes the sentence: e.g. "no undeclared dependencies are
     currently known" or "the following are flagged: ...". -->

### Method battery

{{METHOD_BATTERY}}
<!-- From atlas.yaml battery: — reusable method modules + state. Table or list; skip if absent. -->

### Cross-cutting invariants (frozen truths)

{{CROSS_CUTTING}}
<!-- From atlas.yaml cross_cutting: + experiments/_global/invariants.md when present. One line
     each + source. These bind every experiment; /conflicts enforces them pre-run. -->

**Contents:** {{EXPERIMENT_TOC}}

---

{{#EXPERIMENTS}}
### `{{EXP_ID}}` — {{EXP_TITLE}}

**Tier:** {{RIGOR_TIER}} · **Status:** {{LIFECYCLE}} · **Verdict:** {{VERDICT_ONE_LINER}} ·
**Confound audit:** {{SURVIVES}} · **Parent:** {{PARENT}} ·
**Links:** {{LINKS}}
<!-- LINKS: trace, brief.html, paper, results dir — whatever exists. SURVIVES: "Survives: YES/NO
     (audit.md)" or "n/a — no positive claimed". -->

#### The science (hypothesis & motivation)

{{SCIENCE_NARRATIVE}}
<!-- The FULL falsifiable H-NNN card(s) from hypothesis.md (statement, prediction, kill
     condition), the motivation in plain scientific language, and what the answer changes.
     For a dead-end: lead with the why-it-died lesson. -->

#### In plain words — what we did and what we found

{{LAYMAN_WALK}}
<!-- THE LAYMAN TWIN of the mechanics below (judged by layman-judge — see LAYMAN BAR). Mirror
     the pipeline walk STEP FOR STEP with the SAME numbering, in everyday words: what went in,
     what was done to it, what came out. Then "What the numbers mean:" — every reported number
     in this experiment retold in words (what it measures, how it was computed, what it was
     compared against, and whether that bar was promised in advance or chosen after). Then
     "How it could have fooled us — and what we did about it:" the checks/gates story in plain
     words (for a retraction: what looked true, which probe caught it, the lesson kept). No
     unexplained term at first use; no file paths; no pointing at the expert sections.
     Coverage and length comparable to the mechanics — a translation, not a teaser. -->

#### For the paper — why we ran it, what led here, and what a paper would claim

{{PAPER_NARRATIVE}}
<!-- THE PAPER TWIN (judged by paper-author — see PAPER BAR). For an ML engineer new to the
     project, writing the paper. Cover, in order: (1) WHY this experiment exists — the motivation
     and the JOURNEY LINK: what the previous experiment's result or an open gap implied that made
     THIS one necessary (and, if applicable, what it set up for the next). (2) The hypothesis in
     publication terms (what was predicted, what would falsify it) and which prereg/tier governed
     it. (3) A bare-bones METHODS recap: name every project-specific method/dataset/estimator a
     reader meets here, in one clause each, and POINT to the mechanics walk + tables for the exact
     symbols/formulas (do not restate them). (4) A CITE-THIS reading guide: which result artifact
     (file/key/commit/hash) backs each headline number a paper would report. (5) What a paper would
     CLAIM from this experiment and the scope/limits on that claim. Assume ML literacy; explain
     only what is specific to THIS project. The test the paper-author applies: could I draft the
     Intro-motivation, Methods, Results-sourcing, and Discussion for this experiment from here
     ALONE, without emailing the authors? -->

#### How it works — mechanics

{{PIPELINE_WALK}}
<!-- NUMBERED end-to-end walk of ONE run: data in → preprocessing → method/model → evaluation →
     metrics out. Each step: what happens, to what data, where (`path` · `symbol()` · line).
     If the run code lives outside the repo (remote host), walk the dispatch flow and cite the
     bundle files that prove what ran (config.resolved.json, git.commit, env.lock). -->

**Runtime topology:** {{RUNTIME_TOPOLOGY}}
<!-- Local vs remote GPU (host-config.json), wall-clock/compute budget actually logged,
     quicklook checkpoints, what never leaves the host. -->

**Algorithms & formulas:**

{{ALGORITHMS_AND_FORMULAS}}
<!-- The statistic(s) and estimator(s) VERBATIM with each term defined + implementing symbol;
     the test procedure as its actual rule (permutation scheme, CV fold construction, correction
     method). -->

**Data & splits (leakage controls):**

{{DATA_AND_SPLITS}}
<!-- Dataset(s) + content hash, split construction (temporal/group/qid disjointness), the
     leakage checks that PASSED/FAILED from data-audit.md, n per split. -->

**What the numbers mean, computed:**

{{NUMBERS_COMPUTED}}
<!-- THE core table — the research analog of "what the user sees, computed". For EACH reported
     metric/figure/claim: its exact derivation — which runs (RUN-IDs × seeds), which code
     computes it, which CI method / correction, which stats.json key holds it. A reader must be
     able to reproduce the headline number's provenance from this table alone. -->

**Failure & degradation:**

{{FAILURE_PATHS}}
<!-- What happens when a run crashes / a gate fails / data is missing; what the quicklook
     aborts; how partial results are (not) used. -->

**Repro bundle:**

{{REPRO_BUNDLE}}
<!-- Per key run: seed(s), config.resolved.json deltas from default, git.commit, env.lock,
     dataset.hash — the D-004 reconstructability evidence, with file cites. -->

#### Design decisions (DDRs, with trade-offs)

{{DDRS_FULL}}
<!-- Per DDR from design.md: decision · alternative considered · trade-off accepted · what
     evidence would flip it. Faithful condensation, never titles. -->

#### Pre-registered thresholds & constants

| Constant | Value | Frozen at prereg? | Set where | How derived |
|---|---|---|---|---|
{{#CONSTANTS}}| {{NAME}} | {{VALUE}} | {{FROZEN}} | {{WHERE}} | {{DERIVATION}} |
{{/CONSTANTS}}
<!-- FROZEN ∈ YES (in prereg.lock's hashed plan) | POST-HOC (decided after seeing data — must
     say why that is defensible) | n/a. This column is load-bearing; never omit it. -->

#### Runs & verdicts ledger

{{RUNS_LEDGER}}
<!-- Compact table over runs.md + bundles: RUN-ID · node/task · seeds · outcome (headline
     metric) · results-verifier verdict · confound-audit Survives · notes. -->

#### Files & symbols map

| Path | Role | Key symbols / fields |
|---|---|---|
{{#FILES}}| `{{PATH}}` | {{ROLE}} | {{SYMBOLS}} |
{{/FILES}}

#### Gotchas & lessons

{{GOTCHAS}}
<!-- From Run Notes + verifier/auditor catches + trace: the non-obvious things the next
     researcher MUST know (seed-threading traps, dataset quirks, why a threshold moved, what
     the confound audit nearly killed). For dead-ends this section IS the deliverable. -->

{{/EXPERIMENTS}}
---

## Parking lot

{{PARKING_LOT}}

## Archived (off-board)

{{ARCHIVED}}
<!-- From atlas.yaml archived: — the frozen prior regime pointer + carried lessons; omit if absent. -->

---

_Generated by `/atlas` from `experiments/_atlas/atlas.yaml` + each experiment's
`{experiment.json, hypothesis.md, design.md, runs.md (ALL Run Notes), preregistration.md,
prereg.lock, data-audit.md, audit.md, verdict.md, analysis.md}` + the actual run code + the
`runs/RUN-*/` bundles + `results/` + `trace/`. Do not hand-edit — re-run `/atlas <exp>`
(incremental) or `/atlas --full`, then `render_html.py` for ATLAS.html._
