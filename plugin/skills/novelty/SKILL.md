---
name: novelty
description: Examine what is NEW about a project (or one experiment) against the external literature. Decomposes the work into discrete claimed contributions, fans out one novelty-scout subagent per contribution (grounded WebSearch/WebFetch, cites only retrieved papers), then synthesizes a NOVELTY dossier — a contribution→novelty-class table, the closest prior art per claim, the strongest defensible "to our knowledge" claims, the related-work landscape, and the threats-to-novelty a reviewer will raise. Writes NOVELTY.md (project) or experiments/<exp>/novelty.md, and returns a ## NoveltyReport block. The constructive, pre-paper novelty map; peer-reviewer later ATTACKS what it frames.
whenToUse: Fire on "/novelty", "/novelty <exp>", "what is new here", "examine novelty", "is this novel", "prior-art scan", "related-work scan", "what can we claim is first", and BEFORE /paper on any work heading for publication (novelty framing + the Related Work backbone should exist before the manuscript is drafted). Project-level by default; pass an EXP-slug to scope it to one experiment.
isEnabled: test -d experiments
---

# /novelty

## Static

### Summary
`/novelty` is how the project decides — honestly and with citations — **what it can claim is new**. It reads the work's own statement of its contributions (the ATLAS "For the paper" track + method roster + hypothesis cards, or one experiment's), breaks it into a list of discrete *claimed contributions*, and dispatches one **`novelty-scout`** subagent per contribution. Each scout goes to the OUTSIDE literature (WebSearch/WebFetch), finds the closest prior art, and returns a `## NoveltyScan` classifying the contribution (NOVEL | NOVEL-COMBINATION | INCREMENTAL | PRIOR-ART | UNVERIFIED) with the defensible claim AND the reviewer's objection. `/novelty` then synthesizes the scans into a **NOVELTY dossier** and returns a `## NoveltyReport`. It is the **constructive** novelty step (map the neighbourhood, frame the strongest honest claim); the `peer-reviewer` later red-teams that framing inside `/paper`. The cardinal discipline is inherited from the scout: **every cited paper was retrieved this run with a URL — none from memory** — and the verdict defaults to the most modest class the evidence supports (RULE-9 / CLAUDE.md anti-overclaim). This skill **never grades the science** (RULE-1); it only locates it against the literature.

### Preconditions
- `experiments/` exists. For project-level: a contributions source exists — `experiments/_atlas/ATLAS.md` (the "For the paper" track / method roster), or failing that the per-experiment `hypothesis.md` set. For `/novelty <exp>`: `experiments/<exp>/hypothesis.md` (the `H-NNN` cards) exists.
- WebSearch/WebFetch available to subagents. If web is unavailable the run still completes but every scan returns `UNVERIFIED` and the report's `Open-gaps` says so — a NOVELTY dossier with no web grounding is honest about being ungrounded, never fabricated.

### Parameters
- `exp` — optional. An `EXP-<slug>` to scope the scan to one experiment's contribution(s). Omitted ⇒ **project-level** (the program's contributions from ATLAS).
- `depth` — optional `quick | standard | thorough` (default `standard`). Controls how many search angles each scout runs and how many near works it fetches; `thorough` for a real submission, `quick` for an early gut-check.

### Output format
Writes the dossier — `experiments/_atlas/NOVELTY.md` (project-level) or `experiments/<exp>/novelty.md` (scoped) — then RETURNS this block (and appends it to `trace/<exp>.md`, or `trace/_novelty.md` for project-level, so the block-lint hook and `/drift` see it):

```
## NoveltyReport
- Experiment: <EXP-slug | program>
- Artifact: experiments/_atlas/NOVELTY.md
- Contributions-scanned: <n>
- Novel: <count> (<short ids of NOVEL + NOVEL-COMBINATION>)
- Incremental: <count> (<short ids>)
- Prior-art: <count> (<short ids of claims a prior work defeats>)
- Open-gaps: <UNVERIFIED scans, thin searches, claims a reviewer will contest; or "none">
```

Field semantics (mechanical — `hooks/block-schemas.tsv` greps these keys): **Experiment** = the slug or `program`; **Artifact** = the written dossier path (relative; RULE-2); **Contributions-scanned** = how many discrete claims were assessed; **Novel / Incremental / Prior-art** = counts + short ids partitioning the scans (Novel = NOVEL ∪ NOVEL-COMBINATION); **Open-gaps** = the honest-debt ledger: every UNVERIFIED scan, every claim whose closest prior art a reviewer would call a defeat, and any contribution the search could not reach.

### Hard constraints
- **Cite only retrieved papers (inherited, non-negotiable).** The dossier may name a prior work ONLY if a scout retrieved it with a URL this run. Strip any citation without a fetched URL; if a claim's novelty rests on "no prior art" it must say which queries were run to reach that. Memory citations are forbidden — this project studies hallucinated references; do not ship one.
- **Modest-class default (RULE-9).** When synthesizing, never upgrade a scout's verdict. If scouts split, report the split; do not round NOVEL-COMBINATION up to NOVEL in the summary. "First to…" appears only when a scout returned NOVEL with the empty search that earns it, and always scoped.
- **Both sides of every claim.** Each contribution in the dossier carries its `Defensible-claim` AND its `Reviewer-objection` + the closest prior art. A one-sided "this is novel" entry is a defect.
- **Never grade the science (RULE-1).** `/novelty` maps novelty, not correctness. If the substrate looks wrong, note it as a one-line aside and route it to the results-verifier — do not re-analyze.
- **Distinct from peer-reviewer.** This is the constructive map run BEFORE the paper. The `peer-reviewer` (inside `/paper`) is the adversarial check run on the drafted manuscript. Do not duplicate the peer-reviewer's rubric here; produce the prior-art landscape and the framing it will test.
- **Feeds /paper, does not replace it.** The dossier's "related-work landscape" + "citations-found" become `/paper`'s Related Work backbone and seed `citations_needed.txt`; the "defensible-claim" set becomes the Contributions framing. `/paper` still runs its own checklist + peer-reviewer.
- **No absolute paths** (RULE-2). **English only** (D-006).
- **Same-session agent caveat:** if `novelty-scout` was only just added to the plugin and is not yet in the agent registry (it registers at session start), dispatch the scan via a general-purpose subagent with the `novelty-scout` AGENT.md persona inlined verbatim — the contract (`## NoveltyScan`, cite-only-retrieved) is identical. In normal operation, dispatch the registered `order-67-research-harness:novelty-scout`.

### Common mistakes (avoid)
1. **Letting a scout (or the synthesis) cite from memory.** The cardinal failure; re-search instead. Every URL in the dossier must trace to a fetch.
2. **Rounding novelty up.** A program of NOVEL-COMBINATIONs is a strong, honest paper; inflating it to "first-ever NOVEL" is how the Related Work section gets the paper desk-rejected. Keep the scouts' modest verdicts.
3. **Scanning the name, not the mechanism.** Decompose each contribution into its mechanism + setting + constraint so the scout searches for the real ancestors, not the project's nickname.
4. **Dropping the scope constraint.** The constraint (one model, label semantics, regime) is usually where the novelty lives AND where look-alike prior art gets distinguished — pass it to every scout and keep it in the dossier.
5. **Duplicating the peer-reviewer.** `/novelty` is the prior-art map, not the manuscript red-team. Frame the claim; let `/paper`'s peer-reviewer attack it.
6. **Treating UNVERIFIED as a pass or a fail.** It is neither — it is "not yet determined". It goes to `Open-gaps` with the queries tried, for a re-run when web is available.

## Dynamic

`experiments/` exists when this fires. The scout persona is `${CLAUDE_PLUGIN_ROOT}/agents/novelty-scout/AGENT.md`; the `## NoveltyScan` / `## NoveltyReport` contracts are in `CONVENTIONS.md §4` and `hooks/block-schemas.tsv`.

### Algorithm

1. **Resolve scope.** With `exp`: read `experiments/<exp>/hypothesis.md` (the `H-NNN` cards) + `experiments/<exp>/design.md` for that experiment's claimed contribution(s). Project-level: read `experiments/_atlas/ATLAS.md` — the "For the paper" track (the one-sentence contribution + through-line findings) and the method roster — as the contributions source.
2. **Decompose into discrete claimed contributions.** Each becomes a scout task with: `contribution` (1-2 sentences), `basis` (the concrete method/finding + estimator + data), `keywords` (seed terms + known-adjacent method names), `field`, `scope_constraints` (the constraints that make it narrow/different — one model, label = grounded-in-passage, regime, filtered distribution). Aim for one contribution per genuinely separable claim (a headline method, each recurring finding, the framing/constraint, the benchmark choice) — not one giant blob.
3. **Fan out the scouts.** Dispatch one `novelty-scout` per contribution (registered agent, or the inlined-persona fallback per the same-session caveat), passing the five inputs and `depth`. Run them concurrently. Collect each `## NoveltyScan` + its `### Evidence`.
4. **Synthesize the dossier** (`NOVELTY.md`), in this order:
   - **BLUF** — one paragraph: how many contributions, the class split, and the single most defensible novelty claim of the whole program.
   - **Contribution → novelty-class table** — one row per contribution: claim · Verdict · closest prior art (with URL) · the one-line delta.
   - **Per-contribution detail** — for each: the defensible claim (scoped, "to our knowledge"), what is new vs the named prior art, and the reviewer-objection to pre-empt.
   - **Related-work landscape** — cluster the retrieved works into the field's sub-areas; this is the Related Work backbone for `/paper`.
   - **Threats to novelty** — the consolidated list of the strongest reviewer objections + any PRIOR-ART defeats; the section the authors must answer.
   - **Citations found** — every retrieved work, `Title — authors, year, venue — URL`. Only fetched works; this seeds `citations_needed.txt`.
5. **Emit `## NoveltyReport`** (Output format) and append it to the trace. Partition the scans into Novel / Incremental / Prior-art; list every UNVERIFIED + contested claim in `Open-gaps`.
6. **Hand off:** note in the report that `/paper` consumes the landscape + citations and the defensible-claim set, and that the `peer-reviewer` will red-team the framing — `/novelty` does not certify novelty, it maps it.
