---
name: brief
description: Generate the layman R&D-management deliverable for a finished experiment — a single self-contained brief.html (BLUF + the fixed four questions with a methodological letter grade + finding→status→meaning table + priority next-actions + DEFINITION/CHECKPOINT/HONEST-CAVEAT callouts + a pushback handbook) and return a `## BriefReport` block.
whenToUse: Fire after `/analyze` has emitted `## AnalysisReport` and the `results-verifier` has issued a `## Verdict` for the experiment — i.e. the decision-makers need a plain-language read, not the paper. Triggered by "/brief <exp>", "write the management brief", "BLUF for <exp>", "what do I tell the R&D lead about <exp>", "is <exp> sound / publishable / a product?". Sibling of `/paper` (which targets reviewers); both consume the same analysis but `/brief` speaks to people who will not read a methods section.
---

# /brief

## Static

### Summary
Read the experiment's `experiment.json`, the latest `## AnalysisReport` (effect sizes, CIs, FDR correction, figures), the `results-verifier`'s `## Verdict`, the `## Preregistration` block from `experiments/<exp>/preregistration.md`, and any `## ConfoundAudit` blocks; synthesize a single self-contained `brief.html` aimed at R&D management — people who decide budget and roadmap, not people who read methods sections. The document leads with one BLUF/Minto bottom-line paragraph, answers the **fixed four questions** (what was done · is it sound [letter grade A–F] · scientific value [publishable where] · marketable/product fit), then gives a finding→status→meaning table, a priority-ordered next-action list, DEFINITION/CHECKPOINT/HONEST-CAVEAT callouts, and a pushback handbook (anticipated expert objections + verbatim rebuttals + a closing argument). Communicate effect-size **magnitude and consistency**, never significance alone (RULE-7). Return a `## BriefReport` block; the deliverable IS the HTML file.

### Preconditions
- `${CLAUDE_PROJECT_DIR}/experiments/<exp>/experiment.json` exists and carries a `rigor_tier`. A missing/unknown tier ⇒ treat as `publication` (strictest) AND surface it as a HONEST-CAVEAT callout + a `Required-flag` line in the report (RULE-0).
- An `## AnalysisReport` for `<exp>` exists (in `results/<exp>/analysis.md` or wherever `/analyze` wrote it). `/brief` does not compute statistics; it translates them. If no `## AnalysisReport` exists, refuse — there is nothing to brief.
- A `## Verdict` from the independent `results-verifier` exists for the claims being briefed. `/brief` NEVER issues a verdict of its own and NEVER upgrades the verifier's verdict (RULE-1). If the verdict is `BLOCKED` (metric unscorable), the brief says so plainly — it does not paper over an unobservable metric.
- Run `bash ${CLAUDE_PLUGIN_ROOT}/hooks/block-lint.sh <analysis-file>` as a hard precondition before reading numbers out of an upstream block, so silent field-drift does not propagate into the brief.

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `audience` — optional, default `rd-management`. Reserved for future registers (e.g. `exec`, `investor`); only `rd-management` is implemented and it is the locked default. Any other value ⇒ proceed as `rd-management` and note it in `Deviations`.

### Output format
A `## BriefReport` RETURN FORMAT block (CONVENTIONS §4; required fields verbatim from `hooks/block-schemas.tsv`). The HTML file is the deliverable; this block is the machine-readable receipt the orchestrator and `/drift` consume.

```
## BriefReport
- Experiment: EXP-<slug>
- Artifact: results/<exp>/brief.html
- Bottom-line: <the one-sentence BLUF — the single most decision-relevant statement, magnitude-first>
- Grade: <one of A | A- | B+ | B | B- | C+ | C | C- | D | F — the methodological soundness letter grade>
- Next-actions: <count> (top: <verbatim first action>)
```

Field semantics (the mechanical consumers read these literally):
- **`Grade`** is the letter grade answering fixed-question 2 — methodological soundness only, NOT scientific importance or product value (those are questions 3 and 4). It is a translation of the verifier's `## Verdict` + the tier's checklist coverage, never an independent re-grade (RULE-1). Mapping floor: `PROMOTE` at the experiment's tier with the confound-audit surviving and no prereg deviation ⇒ A-range; `PROMOTE-WITH-CAVEAT` ⇒ B-range; `RERUN` ⇒ C/D; `REJECT` ⇒ F; `BLOCKED` ⇒ the grade is `F` with the HONEST-CAVEAT that the metric was never observable. Down-tier within a range for: single-seed at confirmatory+, missing CI method name, unaudited positive, scope narrower than claimed.
- **`Bottom-line`** is the BLUF: one sentence, lead with the effect-size MAGNITUDE and its CONSISTENCY ("a +12-point balanced-accuracy lift over baseline, stable across all 5 seeds"), not with a p-value. It must be true even if the reader stops there.
- **`Next-actions`** count + the verbatim top action, so the orchestrator can surface the single most important next step without parsing the HTML.

### Hard constraints
- **Single self-contained file (D-006).** All CSS inlined from `templates/palette.css` into the `<style>` block; every figure embedded base64 (`<img src="data:image/png;base64,...">`) — NEVER an `<img src>` to a local path. The only permitted external references are the Google-Fonts `@import` (inside CSS) and the MathJax CDN `<script>` (D-006 permits CDN for math rendering). No `<link rel="stylesheet">`, no `<img src="file:...">`. A stakeholder must open it over `file://` or paste it into an email with zero dependency resolution.
- **English only (D-006).** Every word of the deliverable is English regardless of the project's working language.
- **Effect size over bare significance (RULE-7).** Every finding row and the BLUF report magnitude AND a named spread (CI / std with its variation source: seed/init/split) AND the CI method. A row that can only say "p < 0.05" is malformed — pull the effect size from the `## AnalysisReport`; if `/analyze` did not supply one, that finding becomes a HONEST-CAVEAT, not a headline.
- **Never self-grade; never upgrade the verdict (RULE-1).** The `Grade` and every "holds up" status descend from the `results-verifier`'s `## Verdict`. `/brief` may translate and explain it; it may NOT promote `PROMOTE-WITH-CAVEAT` to an A, nor soften a `REJECT`. If the brief author disagrees with the verdict, the recourse is `/verify-claim`, not a rosier brief.
- **Scope-honest (RULE-9).** The "scientific value" and "product fit" answers state the data-distribution scope the result was measured on (often a heavily filtered slice). Claims do not silently generalize beyond it. A confirmatory/publication brief whose prereg deviated must say so — a prereg deviation HARD-BLOCKS PROMOTE at those tiers (RULE-5), so the brief cannot claim a promoted result it does not have.
- **Nulls are results (RULE-8).** A clean, adequately-powered null is reported as a finding with `data-status="null"`, framed as decision-useful ("rules out X; stop spending on Y"). An underpowered null is flagged as such, never sold as a clean negative.
- **No absolute paths in the skill body or the template (RULE-2).** Resolve plugin reads via `${CLAUDE_PLUGIN_ROOT}` and project reads/writes via `${CLAUDE_PROJECT_DIR}`. The written `brief.html` itself contains no `/home`, `/Users`, `/root` paths.
- **The pushback handbook is mandatory and adversarial.** At least three objections a competent methodologist would actually raise (leakage, seed count, multiple-comparison correction, scope, baseline strength, confound), each with a verbatim rebuttal grounded in what the harness actually did (cite the gate: prereg hash-lock / `/data-audit` L1–L3 / `/confound-audit`). If an objection cannot be honestly rebutted, it becomes a HONEST-CAVEAT instead of a fake rebuttal.

### Common mistakes (avoid)
1. **Reporting significance without magnitude (RULE-7).** A brief that says "the effect was statistically significant (p = 0.003)" tells an R&D lead nothing about whether to act. Lead with how big and how repeatable: "+0.14 balanced-accuracy over the strongest baseline, 95% bootstrap CI [0.09, 0.19], consistent across 5 seeds." The whole reason this skill exists is to make magnitude and consistency legible to a non-statistician.
2. **Letting the letter grade drift up from the verdict (RULE-1).** It is tempting to give a "promising" `PROMOTE-WITH-CAVEAT` result an A because the idea is exciting. The grade measures methodological soundness, which is fixed by the verifier and the tier checklist — not by enthusiasm. Excitement belongs in question 3 (scientific value), where it does not corrupt the soundness signal.
3. **Conflating the four questions.** "Sound" (Q2), "scientifically valuable" (Q3) and "marketable" (Q4) are independent axes: a methodologically immaculate result can be a scientific non-event and a commercial non-starter, and a rough exploratory finding can be a huge product lead. Answer each on its own terms; do not average them into one vibe.
4. **A pushback handbook of strawmen.** Rebutting easy objections ("but did you use a GPU?") while ducking the real one (label leakage across the qid split, or N=1 seed at a confirmatory tier) destroys the document's credibility with the exact expert it is meant to disarm. Steelman first, then answer — and if there is no honest answer, downgrade it to a HONEST-CAVEAT.
5. **Inflating scope (RULE-9).** Writing "the model detects deception" when the measurement was on a filtered 4-token-answer slice of one dataset. State the distribution the number was measured on, every time, in both Q3 and Q4. An over-broad brief is how a self-retracting result (proteus Eksperyment 1) escapes into a roadmap.
6. **External file references in the HTML (D-006).** Linking a local PNG or an external stylesheet breaks the "email it / open it offline" contract the instant the file leaves the repo. Inline the palette; base64 every figure.

## Dynamic

Templates live under `${CLAUDE_PLUGIN_ROOT}/skills/brief/templates/`:
- `brief.html.tpl` — the self-contained skeleton (masthead · BLUF · four-question sections · findings table · next-action list · callouts · pushback handbook · footer). Placeholders are `{{UPPER_SNAKE}}`.
- `palette.css` — the professional palette + the semantic `--status-*` / `--grade-*` tokens the table and grade chip resolve against. Inlined verbatim at `{{PALETTE_CSS}}`.

What already exists when `/brief` fires (do not re-check): `experiment.json`, the `## AnalysisReport`, the `## Verdict`, the `## Preregistration` block at `experiments/<exp>/preregistration.md`, and the frozen plan body in `experiments/<exp>/prereg.lock`. `/brief` reads them; it does not recompute, re-audit, or re-verify. Read the `## Preregistration` block (hyphenated mechanical fields) from `preregistration.md`; if it needs the frozen plan values, read `prereg.lock` by its snake_case keys `primary_metric` / `splits` / `analysis_plan` — never conflate the two (CONVENTIONS §4).

Discover the experiment's current state and the upstream blocks:

```
!{ls "${CLAUDE_PROJECT_DIR}/experiments/" 2>/dev/null}
!{cat "${CLAUDE_PROJECT_DIR}/experiments/<exp>/experiment.json" 2>/dev/null | grep -o '"rigor_tier"[^,}]*'}
!{ls "${CLAUDE_PROJECT_DIR}/results/<exp>/" 2>/dev/null}
!{grep -n '^## \(AnalysisReport\|Verdict\|ConfoundAudit\|Preregistration\)' "${CLAUDE_PROJECT_DIR}/results/<exp>/"*.md "${CLAUDE_PROJECT_DIR}/experiments/<exp>/"*.md 2>/dev/null}
!{ls "${CLAUDE_PROJECT_DIR}/experiments/<exp>/preregistration.md" "${CLAUDE_PROJECT_DIR}/experiments/<exp>/prereg.lock" 2>/dev/null}
!{git -C "${CLAUDE_PROJECT_DIR}" rev-parse --short HEAD 2>/dev/null}
```

Algorithm:

1. **Resolve the tier and fail loud.** Read `experiment.json`; capture `rigor_tier` as `tier`. If absent/unknown, set `tier = publication`, set `tier_was_missing = true`, and queue a HONEST-CAVEAT callout reading "Rigor tier was not declared; this brief applies the strictest (publication) checklist by default (RULE-0)." Capture `id` → `EXP_ID`, and a human title from `experiment.json` or `hypothesis.md` → `EXP_TITLE` (+ a one-line `EXP_SUBTITLE`).

2. **Lint then read the upstream blocks.** Run `bash ${CLAUDE_PLUGIN_ROOT}/hooks/block-lint.sh <analysis-file>`; if it exits non-zero, halt and report the malformed block rather than briefing drifted numbers. Then read the `## AnalysisReport` (capture `Primary-metric`, `Effect-size`, `CI`, `Correction`, `Figures`), the `## Verdict` (capture the verdict string, `Tier applied`, `Claims`), every `## ConfoundAudit` (capture each claim's `Survives` YES/NO), and the `## Preregistration` block from `experiments/<exp>/preregistration.md`. To detect a deviation from the locked plan, read the frozen plan values from `experiments/<exp>/prereg.lock` by its snake_case keys `primary_metric` / `splits` / `analysis_plan` and compare against what was actually analyzed — never read the block from `prereg.lock` nor the frozen values from `preregistration.md` (CONVENTIONS §4). If no `## AnalysisReport` exists, refuse: `No AnalysisReport for <exp>; run /analyze before /brief.` If no `## Verdict` exists, refuse: `No results-verifier Verdict for <exp>; /brief never self-grades (RULE-1).`

3. **Derive the grade (translate, do not re-grade — RULE-1).** Map the verdict → letter-grade range per the Output-format mapping (`PROMOTE`→A, `PROMOTE-WITH-CAVEAT`→B, `RERUN`→C/D, `REJECT`→F, `BLOCKED`→F+caveat). Then move within the range for tier-coverage gaps: confirmatory+ with single seed, missing named CI method, an unaudited positive (`ConfoundAudit.Survives` not YES), or scope narrower than the claim ⇒ down within range. Record the chosen letter as `GRADE`, a 3–6 word `GRADE_HEADLINE` ("sound but narrowly scoped"), and a 1–2 sentence `GRADE_RATIONALE` naming the specific reason.

4. **Write the BLUF.** One Minto bottom-line paragraph, magnitude-first and consistency-second, true on its own. This sentence also becomes the report's `Bottom-line` field. Never lead with a p-value (RULE-7).

5. **Answer the four questions.**
   - **Q1 — what was done:** plain-language description of the hypothesis tested and how, no jargon, no file paths.
   - **Q2 — sound? [grade]:** the `GRADE` chip + `GRADE_RATIONALE`; explicitly name which gates ran (prereg hash-lock, `/data-audit` L1–L3, `/confound-audit`) and which did not.
   - **Q3 — scientific value [publishable where]:** is the finding novel/important; if publishable, name a realistic venue tier as `Q3_VENUE_TAGS` (e.g. `<span class="tag">workshop-ready</span>`, `interpretability venue`, `not yet — needs N seeds`). State the data-distribution scope (RULE-9).
   - **Q4 — marketable / product fit:** honest commercial / internal-tooling read, scoped to the same distribution; say "no product fit yet" when that is the truth.

6. **Build the findings table.** One `<tr>` per claim from `## AnalysisReport` / `## Verdict`:
   ```html
   <tr>
     <td class="finding">{plain-language finding}</td>
     <td><span class="effect">{magnitude, e.g. d=0.82 / +0.14 bal-acc}<span class="consistency">{CI + method + variation source, e.g. 95% bootstrap CI [0.09,0.19], 5 seeds}</span></span></td>
     <td><span class="status-pill" data-status="strong|caveat|weak|null">{Holds | Holds, narrow | Underpowered | Clean null}</span></td>
     <td class="meaning">{the decision this supports or forecloses}</td>
   </tr>
   ```
   `data-status`: `strong` = promoted, large + consistent; `caveat` = promote-with-caveat / narrow scope; `weak` = rerun / did-not-survive-audit / underpowered; `null` = clean null (RULE-8). Concatenate into `FINDINGS_ROWS`.

7. **Order the next actions by priority.** One `<li>` per action, most decision-unblocking first, each naming the decision it unblocks and a rough cost stamp:
   ```html
   <li><span class="act-head">{action}</span><span class="act-cost">{~GPU-h / ~$ / ~wallclock}</span>
       <div class="act-body">{what it unblocks}</div></li>
   ```
   Concatenate into `NEXT_ACTIONS`; record the count and the verbatim first action for the report's `Next-actions` field.

8. **Emit callouts** (zero or more of each) into `CALLOUTS`:
   ```html
   <div class="callout definition"><span class="ctag">Definition</span>{term a non-specialist needs, e.g. "balanced accuracy"}</div>
   <div class="callout checkpoint"><span class="ctag">Checkpoint</span>{the go/pivot/kill decision gate this brief informs}</div>
   <div class="callout honest"><span class="ctag">Honest caveat</span>{the thing you would tell a trusted colleague over coffee — leakage risk, seed count, scope, the missing-tier flag from step 1}</div>
   ```
   The missing-tier flag (if `tier_was_missing`) and every `ConfoundAudit.Survives = NO` MUST appear as a HONEST-CAVEAT.

9. **Write the pushback handbook** into `PUSHBACK_OBJECTIONS` — ≥3 steelmanned objections, each:
   ```html
   <div class="objection"><div class="obj-q">{the real objection, steelmanned}</div>
     <div class="obj-a">{verbatim rebuttal grounded in the gate that addressed it; or, if none, escalate to a HONEST-CAVEAT instead of faking a rebuttal}</div></div>
   ```
   Then one-paragraph `CLOSING_ARGUMENT`: the strongest honest case for the result, scope intact.

10. **Substitute and write.** Read `templates/palette.css` → `PALETTE_CSS`; read `templates/brief.html.tpl`. Substitute `{{PALETTE_CSS}}`, `{{EXP_ID}}`, `{{EXP_TITLE}}`, `{{EXP_SUBTITLE}}`, `{{RIGOR_TIER}}` (= `tier`), `{{VERDICT}}`, `{{GENERATED_AT}}` (current UTC `YYYY-MM-DDTHH:MM:SSZ`), `{{BLUF_PARAGRAPH}}`, `{{Q1_WHAT_WAS_DONE}}`, `{{GRADE}}`, `{{GRADE_HEADLINE}}`, `{{GRADE_RATIONALE}}`, `{{Q3_SCIENTIFIC_VALUE}}`, `{{Q3_VENUE_TAGS}}`, `{{Q4_PRODUCT_FIT}}`, `{{FINDINGS_ROWS}}`, `{{NEXT_ACTIONS}}`, `{{CALLOUTS}}`, `{{PUSHBACK_OBJECTIONS}}`, `{{CLOSING_ARGUMENT}}`, and `{{PROVENANCE_LINE}}` (verdict string + `Tier applied` + git short-hash from the discovery block, so the brief is traceable to the exact verdict and commit). Embed each figure from `## AnalysisReport.Figures` base64 inline. Write to `${CLAUDE_PROJECT_DIR}/results/<exp>/brief.html` (overwrite; generated output).

11. **Return the `## BriefReport` block** with the fields above. The HTML is the deliverable; the block is the receipt.
