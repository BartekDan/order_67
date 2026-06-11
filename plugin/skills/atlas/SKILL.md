---
name: atlas
description: Regenerate the project-level ATLAS — now THREE artifacts under experiments/_atlas/. (1) STATUS.md, the thin board rendered deterministically by skills/atlas/atlas.py from the hand-curated ledger atlas.yaml — you-are-here, the exploration TREE (every path incl. dead-ends/backtracks, each with its `why`), status table, method battery, parking lot, drift check. (2) ATLAS.md, THE deep single-place dossier (the science + the mechanics + a LAYMAN TRACK per experiment) — full falsifiable hypothesis cards, numbered pipeline walks with path:symbol:line citations into the ACTUAL run code, verbatim statistics/estimators, data & leakage controls, a mandatory "what the numbers mean, computed" derivation table per experiment (which runs, which code, which CI method, which stats.json key), repro bundles, DDR full text with trade-offs, pre-registered-vs-post-hoc threshold tables, runs & verdicts ledgers, gotchas from ALL Run Notes, PLUS mandatory "In plain words" twin sections at equal depth for non-technical readers (incl. the frozen-in-advance-vs-chosen-after story per number), gated by the layman-judge agent until a zero-background reader genuinely follows. (3) ATLAS.html, a self-contained house-editorial render of ATLAS.md produced DETERMINISTICALLY by skills/atlas/render_html.py — layman panels visually distinct; v3 diagrams are declarative flow/graph DSL blocks rendered as layered SVG (templates/diagram-dsl.md; ASCII retired EXCEPT the verbatim exploration tree). The research analog of order-66 /atlas v3. Incremental by default; --full rebuilds everything.
whenToUse: Invoked when the user is lost about overall project state, wants the cross-experiment map, or asks how an experiment ACTUALLY works / where a reported number comes from. Triggered by "/atlas", "where are we", "what's the project status", "show the map/board", "what did we try and drop", "how does EXP-X actually work", "where does that number come from", "regenerate the atlas", and at the end of a working session or whenever a path is started, blocked, dead-ended, superseded, deferred, or backtracked. Prefer this over reading experiment.json files one by one.
isEnabled: test -d experiments
---

# /atlas — the single project control surface (v2: board + deep dossier)

## Static

### Summary
The ATLAS is how the human keeps control of a branching research project in **one place** — every
path including the abandoned ones and *why*, AND the full depth of each experiment (the science +
the mechanics), so neither backtracking nor onboarding ever loses information. Three artifacts
under `experiments/_atlas/`:

1. **`STATUS.md`** — the thin board. Rendered **deterministically** by
   `${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py` from the hand-curated ledger
   `experiments/_atlas/atlas.yaml` (PyYAML required). You-are-here, the exploration tree with
   per-dead-end `why`, status table, method battery, cross-cutting truths, parking lot, drift
   check. Unchanged from v1.
2. **`ATLAS.md`** — **the deep dossier: ONE place holding everything, science AND mechanics AND a layman track.**
   Model-authored from deep sources per `templates/atlas-deep.md.tpl` (its HTML comments are the
   AUTHORING RULES — follow them, strip them from output). Per experiment: the FULL falsifiable
   H-NNN hypothesis cards; a numbered pipeline walk of what one run actually computes with
   `path` · `symbol()` · line citations into the real code (or, for remote runs, the dispatch
   flow plus the bundle files proving what ran); runtime topology; the statistics/estimators
   **verbatim** with terms defined; data & splits with the leakage controls that passed/failed;
   a mandatory **"what the numbers mean, computed"** table — for every reported metric/figure/
   claim, its exact derivation (which RUN-IDs × seeds, which code, which CI/correction method,
   which `stats.json` key); failure paths; the repro bundle; DDR full text with trade-offs and
   flip triggers; a **pre-registered-vs-post-hoc** constants table (the FROZEN column is
   load-bearing — RULE-3/RULE-6 honesty); a runs & verdicts ledger (results-verifier verdict +
   confound-audit Survives per key run); files & symbols map; and gotchas from ALL Run Notes.
   Per experiment the science narrative is followed by **"In plain words — what we did and
   what we found"** (the layman twin — see the layman bar below). Project head: **"In plain
   words — what this research project is doing and finding"** (the layman entry point, FIRST
   body section), the program at a glance, **the exploration tree copied VERBATIM from the
   freshly regenerated STATUS.md** (single source = atlas.yaml — never re-drawn; EXEMPT from
   the diagram DSL), a program data-flow ```flow DSL block (data → method → runs → metrics →
   gates → claim, rendered as SVG), compute & runtime surfaces inventory, data & results
   artifacts inventory, the dependency/retraction-cascade graph (```graph DSL block) **with
   an explanation of how it is built** (ledger `parent:` edges + `_Depends:_` evidence edges),
   the method battery, and cross-cutting invariants.
3. **`ATLAS.html`** — the editorial render of ATLAS.md: self-contained house style (Fraunces /
   Inter Tight / JetBrains Mono on the paper palette, sticky TOC, styled derivation tables,
   ```flow/```graph blocks rendered as layered SVG diagrams, "In plain words" sections in
   visually distinct layman panels). Generated **deterministically** by
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/atlas/render_html.py experiments/_atlas/ATLAS.md`.
   **Content single-source rule:** ATLAS.md is the only authored artifact; ATLAS.html is a pure
   presentation of it, re-rendered after every ATLAS.md write. (v1's board-style ATLAS.html is
   retired; `atlas.py` no longer emits HTML.)

**The depth bar (binding):** a competent researcher new to the project, reading ONLY ATLAS.md,
must be able to answer — (1) what each experiment actually computes end-to-end; (2) where every
reported number comes from (runs, code, CI method); (3) what was frozen at pre-registration vs
decided post-hoc; (4) what data/compute artifacts exist and their shape; (5) why each design
decision was made, what would flip it — and for every dead-end, why it died. A section that
can't answer these is too shallow; go back to the sources.

**The layman bar (binding, v3, gated by the `layman-judge` agent):** an intelligent reader with
ZERO scientific or technical background, reading ONLY the "In plain words" sections (plus the
science narratives), must be able to retell — (1) what question the program asks and how an
answer gets made here; (2) what each experiment did, step by step, mirroring the mechanics
walk's numbering 1:1; (3) what every reported number means, where it comes from, and — in plain
words — whether its pass/fail bar was promised in advance or chosen after seeing the data;
(4) why a result was believed, doubted, or retracted (a retraction story is layman gold — tell
it straight). Equal DEPTH to the mechanics — a translation, not a teaser; no unexplained term
at first use; no file paths; never point into the expert sections. After assembling ATLAS.md,
`/atlas` MUST spawn the `layman-judge` agent (subagent type
`order-67-research-harness:layman-judge:layman-judge`; returns `## LaymanReport` with
explain-backs, findings, and open questions) and revise the flagged sections to answer its
questions IN the text — up to 3 rounds. Still NEEDS REWORK after round 3 → ship anyway, carry
the unresolved findings verbatim into the `## AtlasReport` (honesty over polish). Skip the gate
only when NO layman/science section changed. Distinct from `/brief` (a per-experiment
management deliverable): the layman track lives IN the dossier and covers the whole program.

### The ledger schema (`experiments/_atlas/atlas.yaml`) — unchanged
```yaml
project: "<name>"
regime: "<optional one-liner>"          # optional
you_are_here: {node: <id>, summary: <...>, blocker: <...>, next: <...>}   # optional
nodes:                                    # REQUIRED — the exploration tree
  - id: <unique-id>                       # experiment dirs use their dir name (EXP-...)
    kind: experiment|step|method|decision|dead-end|idea
    lifecycle: done|active|blocked|dead-end|superseded|deferred|not-built|idea
    parent: <id|null>                     # builds the tree
    verdict: "<one line — the result/decision>"
    why: "<REQUIRED for dead-end/superseded/backtracked: the lesson kept>"
    next: "<optional>"
    links: {<label>: <path>}              # optional
battery: [...]        # optional: reusable method modules + state
cross_cutting: [...]  # optional: frozen truths that bind every node
parking_lot: [...]    # optional: real ideas/tasks not started
infra: {...}          # optional: environment / current blocker
archived: {...}       # optional: off-board scope + carried lessons
```
Lifecycle glyphs: ✅ done · ▶ active · ⛔ blocked · ✗ dead-end · ⊘ superseded · ⏸ deferred · ◻ not built · 💡 idea

### Parameters
- `exp` — optional. Rebuild only that experiment's ATLAS.md section (head + STATUS.md always refresh).
- `--full` — optional. Rebuild every section from sources. Required on `Template-rev` mismatch,
  when ATLAS.md is missing/pre-v2, or when cross-experiment facts are suspected stale.
- No-argument invocation: **incremental by default** — diff each experiment's
  `**Tier:** … **Status:** … **Verdict:**` header line in the existing ATLAS.md against the
  ledger + experiment.json; changed/new nodes form the rebuild set (a node with no existing
  section counts as changed; a section whose experiment left the ledger is dropped at assembly,
  noted in the report). Empty set → still refresh STATUS.md + the head.

### Output format
1. `experiments/_atlas/STATUS.md` — via `python "${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py" "${CLAUDE_PROJECT_DIR}"`.
2. `experiments/_atlas/ATLAS.md` — per `templates/atlas-deep.md.tpl`.
3. `experiments/_atlas/ATLAS.html` — via `python3 ${CLAUDE_PLUGIN_ROOT}/skills/atlas/render_html.py experiments/_atlas/ATLAS.md`
   AFTER writing ATLAS.md (also in incremental mode). On renderer error: surface it, still finish
   (ATLAS.md is the source of truth); never hand-write the HTML instead.

Then emit the combined `## AtlasReport` block: atlas.py's printed block (counts + you-are-here +
drift) extended with `Regen-mode`, `Sections-rebuilt`, and
`Outputs: STATUS.md, ATLAS.md, ATLAS.html`.

### Hard constraints
- **Dead-ends and backtracks are FIRST-CLASS.** Never delete an abandoned path from the ledger —
  set `lifecycle: dead-end|superseded|deferred` + a one-line `why:`. In ATLAS.md a dead-end's
  Gotchas section IS the deliverable (the lesson kept).
- **Deep sourcing is mandatory for ATLAS.md experiment sections.** Inputs per experiment:
  `experiment.json`; `hypothesis.md` (FULL H-NNN cards); `design.md` (methods + DDR FULL TEXT);
  `runs.md` (statuses + **ALL Run Notes**); `preregistration.md` + `prereg.lock`;
  `data-audit.md`; `audit.md` (confound audit); `verdict.md`; `analysis.md`;
  `runs/RUN-*/` bundles (`config.resolved.json`, `metrics.json`, `seed.txt`, `env.lock`,
  `dataset.hash`, `git.commit`); `results/<exp>/stats.json` + figures; `trace/<exp>.md`; **and
  the actual run code** where it exists in-repo. Spec summaries alone are NOT a valid source for
  a mechanics section.
- **Citation rule:** every mechanical claim cites `path` + symbol (+ line as of generation);
  every NUMBER cites its artifact (`stats.json` key, `metrics.json` field, prereg.lock).
  Unverifiable → `unverified — inferred from <source>` or omitted. Never from memory.
- **"What the numbers mean, computed" is mandatory** for every experiment with reported results.
- **Pre-registered vs post-hoc is load-bearing:** every threshold/constant row carries the
  FROZEN column (YES = inside prereg.lock's hashed plan · POST-HOC = decided after data, with
  the defense stated · n/a). Mislabeling this fails review.
- **The exploration tree in ATLAS.md is copied verbatim** from the freshly regenerated STATUS.md
  tree block — never re-drawn, never edited (single source: atlas.yaml). It is EXEMPT from the
  diagram DSL rule below.
- **Diagrams are declarative ```flow / ```graph DSL blocks** (grammar + binding authoring rules
  in `templates/diagram-dsl.md` — read it before writing any diagram), rendered deterministically
  to layered SVG by `render_html.py`. One idea per diagram, ≤ ~15 nodes, EVERY edge labeled with
  what moves. ASCII art is retired for diagrams (plain ``` blocks remain only for genuinely
  textual content — the exploration tree, sample records). After rendering, grep ATLAS.html for
  `diagram DSL error` — a fallback comment means a malformed block; fix it, never ship the
  fallback.
- **The layman track is mandatory and judged.** The head opens with "In plain words — what this
  research project is doing and finding"; every experiment section carries "In plain words —
  what we did and what we found" between the science narrative and the mechanics. Headings MUST
  start with "In plain words" (the renderer styles the panel and the layman-judge locates the
  sections by that prefix). The layman-judge gate (see the layman bar) runs on every
  regeneration that touched any layman/science section.
- **ATLAS.html is render-only** (self-contained: inline CSS, fonts via `@import` in `<style>`,
  no external files, no JS). Authoring content in it that is not in ATLAS.md breaks the
  single-source rule.
- **Incremental coherence:** rebuilding one experiment's section also refreshes the project head
  (tree, inventories, graphs, generated-at) and any sibling sections whose `_Depends:_` /
  retraction edges name the changed experiment. When in doubt, `--full`.
- **Never hand-edit generated files** (`STATUS.md`, `ATLAS.md`, `ATLAS.html`). Edit `atlas.yaml`
  / the experiment files and regenerate.
- **Resolve drift immediately** (atlas.py flags dirs-without-node / nodes-without-dir); a board
  that omits a path lies. Skip leading-underscore dirs as experiments. Off-board scope stays
  `archived:`-only.
- **No absolute paths** in the skill body or generated output; the skill body uses
  `${CLAUDE_PLUGIN_ROOT}`; generated citations are repo-relative.

### Common mistakes (avoid)
1. **Building the dossier from doc summaries only** — the failure mode v2 exists to kill (same
   as order-66): hypothesis one-liners + DDR titles + a file list cannot answer "what does this
   experiment actually compute". Open the run code, the bundles, and the Run Notes.
2. **Uncited numbers.** "balanced accuracy beat chance" is a vibe; "bal_acc 0.61 ± 0.04 (95% CI,
   seed-bootstrap n=12, `results/EXP-x/stats.json:bal_acc`) vs permutation chance 0.50
   (`audit.md` C-001)" is a result.
3. **Flattening prereg honesty** — presenting a post-hoc threshold as if frozen (or omitting the
   FROZEN column). The distinction is the harness's core rule.
4. **Hand-editing STATUS.md/ATLAS.html instead of the sources** (overwritten on next run); or
   deleting a failed node "to clean up" — mark it dead-end + `why`.
5. **Running `--full` on every invocation** (it re-reads every experiment's code) — default is
   incremental; escalate on Template-rev mismatch or stale cross-experiment facts. Equally
   wrong: incremental forever while retraction edges rot.
6. **Writing the layman section as a teaser, or self-grading it.** "The detector turned out to
   be wrong" fails the layman bar exactly like an uncited number fails the citation rule — the
   layman twin walks the SAME steps, retells the SAME numbers (including which bars were
   promised in advance), and tells the retraction story straight. The layman-judge gate exists
   because the author is the worst judge of their own jargon.
7. **Fighting the diagram engine, or converting the exploration tree.** Hand-drawing ASCII
   because "the SVG didn't look right" breaks the deterministic render — simplify the block
   instead. And the tree is the one diagram that must STAY verbatim ASCII (single source =
   atlas.yaml); shipping a `diagram DSL error` fallback is a failed run.

## Dynamic

`experiments/` exists when this fires. Templates at `${CLAUDE_PLUGIN_ROOT}/skills/atlas/templates/`:
`atlas-deep.md.tpl` (authoring rules in its comments) and `diagram-dsl.md` (the ```flow/```graph
diagram grammar — read BEFORE writing any diagram). Renderer: `render_html.py` (zero-dep,
DSL→SVG + layman panels). Board generator: `atlas.py` (PyYAML).

### Algorithm

1. **Update the ledger first** if project state changed — `experiments/_atlas/atlas.yaml`:
   move `you_are_here`; update affected nodes' `lifecycle`/`verdict`/`next`; abandoned path →
   `dead-end|superseded|deferred` + `why:` (never delete); new idea → `lifecycle: idea`; keep
   `battery:`/`parking_lot:` current.
2. **Regenerate the board:** `python "${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py" "${CLAUDE_PROJECT_DIR}"`
   (PyYAML required). Fix any drift it flags (add/repair ledger nodes), re-run until clean.
3. **Decide regen mode** (see Parameters): full / explicit `exp` / incremental diff of section
   header lines vs ledger + experiment.json state.
4. **Per experiment in the rebuild set, gather deep sources** (the full list in Hard
   constraints) — then **open the run code and the bundles**: entry points, stages, key symbols
   + lines, the statistic implementations, config deltas, metrics/stats fields.
5. **Write each experiment section** per the template skeleton (science → **In plain words —
   what we did and what we found** (the layman twin: mirror the pipeline walk's numbering 1:1
   in everyday words, then "What the numbers mean:" with the frozen-in-advance-vs-chosen-after
   story per number, then the gates/retraction story — see the layman bar) → mechanics incl.
   "what the numbers mean, computed" → DDRs → prereg constants table → runs & verdicts ledger →
   files & symbols → gotchas), applying the depth bar, the layman bar + citation rule. Diagrams
   per `diagram-dsl.md`.
6. **Project head** (always rebuilt): **In plain words — what this research project is doing
   and finding** (the layman entry point, first body section); program paragraph; the tree
   COPIED from STATUS.md (verbatim ASCII — exempt from DSL); program data-flow ```flow block +
   legend; compute & runtime surfaces; data & results artifacts; dependency/retraction ```graph
   block + "how this graph is built" (+ discrepancies or "none known"); method battery;
   cross-cutting invariants (`atlas.yaml` + `experiments/_global/invariants.md`).
7. **Assemble ATLAS.md** (experiments in tree order, parents first; in incremental mode carry
   unchanged sections over VERBATIM), parking lot + archived tail, strip template comments,
   write. Frontmatter carries `template_rev` copied from the template's `Template-rev:` line.
8. **Layman gate:** spawn the `layman-judge` agent
   (`order-67-research-harness:layman-judge:layman-judge`) with the ATLAS.md path and the list
   of "In plain words" + science sections to judge (incremental mode: the rebuilt sections +
   the head). Read its `## LaymanReport`. On `NEEDS REWORK`: revise the flagged sections so
   the text itself answers every finding and question, re-write ATLAS.md, re-spawn — max 3
   rounds total. Still failing after round 3 → proceed, carry the unresolved findings into the
   `## AtlasReport` verbatim. Skip only when NO layman/science section changed.
9. **Render:** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/atlas/render_html.py experiments/_atlas/ATLAS.md`
   → confirms the sibling ATLAS.html path, then `grep -c 'diagram DSL error'` on it — any hit
   means a malformed diagram block: fix and re-render. On renderer error: report, continue.
10. **Emit the combined `## AtlasReport`** (atlas.py block + Regen-mode + Sections-rebuilt +
   `Layman-gate: <PASS round n | NEEDS REWORK after 3 rounds>` + `Layman-open-findings:
   <none | verbatim list>` + `Diagrams: <n> DSL blocks, <n> errors` + the three Outputs). If
   drift was flagged and fixed, say so.
