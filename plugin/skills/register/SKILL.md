---
name: register
description: The pre-registration GATE — freeze a confirmed path+tier into experiments/<exp>/experiment.json (status=registered) + hypothesis.md (falsifiable H-NNN cards) + prereg.lock (sha256 of the frozen {primary_metric, splits, analysis_plan}) + preregistration.md (the persisted ## Preregistration block consumers read). Persists the ## Preregistration block carrying the Prereg-hash to preregistration.md (not only returned).
whenToUse: Invoked after /triage returns a ## ResearchRouting block with a confirmed Experiment + Rigor-tier and the user has approved proceeding. Triggered by "pre-register this", "register the experiment", "lock the hypotheses", "/register <exp>", or by /triage routing to the register path. Do NOT fire before a tier is chosen, and do NOT fire if experiments/<exp>/prereg.lock already exists (that is a re-register / down-tier case — see Hard constraints).
---

# /register

## Static

### Summary
Turn one confirmed experiment proposal (an `EXP-<slug>` with a chosen `rigor_tier`, typically arriving from `/triage`'s `## ResearchRouting` block) into a frozen pre-registration. `/register` is the harness's anti-HARKing gate (RULE-5): it writes `experiments/<exp>/experiment.json` (`status: registered`), a `hypothesis.md` containing one or more falsifiable `H-NNN` cards, a `prereg.lock` that hashes the frozen `{primary_metric, splits, analysis_plan}` with an ISO timestamp, and `experiments/<exp>/preregistration.md` containing the verbatim `## Preregistration` block — the canonical block file every consumer (`/design-experiment`, `/analyze`, `/paper`, `/brief`) reads from (never from `prereg.lock`, which is the separate hashed snake_case plan body). After this skill runs, the analysis plan is committed *before any result exists* — at `confirmatory`+ a later deviation HARD-BLOCKS PROMOTE. It REFUSES any hypothesis without an explicit falsification criterion or one resting on subjective / visual-only judgement (RULE-7), exactly as order-66's `/decompose` refuses prose that is not in EARS form.

### Preconditions
- `experiments/` exists at the project root.
- The experiment has been routed and confirmed: there is a `## ResearchRouting` block (from `/triage`) naming the `Experiment` (`EXP-<slug>`) and a `Rigor-tier`, OR the user has stated both explicitly. A missing/unknown tier ⇒ treat as `publication` (strictest) and surface the gap (RULE-0).
- `experiments/<exp>/prereg.lock` does NOT yet exist (this is what guards against silently re-freezing a different plan over a committed one).
- For `confirmatory`+ tiers: the user has supplied (or confirmed) a primary metric, a split definition keyed by the unit of scientific interest, and a seed count with a one-line power justification. `/register` will not invent these.

If `experiments/<exp>/prereg.lock` already exists, refuse with: `"EXP-<exp> is already pre-registered (prereg.lock present, hash <first8>). To change the frozen plan, re-register explicitly with --amend (records a superseding lock + deviation note) or down-tier to exploratory."` Re-registering without `--amend` is forbidden — silently overwriting a lock is the exact failure RULE-5 exists to prevent.

If the routed `Signal-validated` field is `no` and the tier is `confirmatory` or `publication`, refuse with: `"Cannot pre-register EXP-<exp> at <tier> before signal validation. Down-tier to pilot, run the cheap quicklook, confirm signal, then re-register."` (Tiers nest: the `signal_confirmed` gate is a `pilot` precondition; you cannot skip it to land at confirmatory.)

### Parameters
- `experiment` — required. The `EXP-<slug>` id (stable, kebab-case, ≤ 30 chars). Reused as the directory name under `experiments/`.
- `rigor_tier` — required in effect; if absent or unrecognized, defaults to `publication` AND is flagged as a blocking gap (RULE-0). One of `exploratory | pilot | confirmatory | publication`.
- `hypotheses` — required. One or more candidate hypotheses in prose or EARS-shaped form; `/register` converts each into an `H-NNN` card and REFUSES any that cannot be given a falsification criterion (see Hard constraints).
- `primary_metric` — required at `pilot`+. The single pre-declared metric the verifier will grade against (e.g. `balanced_accuracy`, `R2`, `selectivity_index`). Exactly one primary; everything else is secondary/exploratory.
- `splits` — required at `pilot`+. How the held-out set is defined, keyed by the unit of scientific interest, never by row (RULE-10). E.g. `"by qid, disjoint files; no question appears in both folds"`.
- `analysis_plan` — required at `confirmatory`+. The frozen statistical plan: estimator, CI method + named variation source, multiple-comparison correction, confound-audit thresholds. Free prose, captured verbatim into the lock.
- `amend` — optional flag. Permits superseding an existing `prereg.lock`; writes a new lock that references the prior hash and appends a deviation note (which HARD-BLOCKS PROMOTE downstream at confirmatory+ until the verifier re-clears it).

### Output format
Writes four files under `experiments/<exp>/`:

1. `experiment.json` — conforms to `${CLAUDE_PLUGIN_ROOT}/templates/experiment.schema.json`. `version` is bumped, `status` set to `registered`, `rigor_tier` set, `hypothesis_ids` listing every `H-NNN`, `prereg_hash` set to the sha256 from `prereg.lock` (required at confirmatory+), `dataset_refs` carried through with content hashes if known, `created`/`updated` stamped ISO. `status` MUST be `registered` after this skill — never `running`/`complete`.
2. `hypothesis.md` — one `H-NNN` card per hypothesis, using `${CLAUDE_PLUGIN_ROOT}/skills/register/templates/hypothesis-card.md`. Each card is EARS-shaped and carries: prediction, falsification criterion, named confounds, cost, novelty.
3. `prereg.lock` — the frozen `{primary_metric, splits, analysis_plan}` + git commit + ISO timestamp, hashed per `${CLAUDE_PLUGIN_ROOT}/skills/register/templates/prereg-lock-format.md`. This is a SEPARATE artifact from the block file: its keys are snake_case (`primary_metric` / `splits` / `analysis_plan`) and downstream skills read it by those keys ONLY when they need the frozen plan *values* (e.g. to detect a deviation from the locked plan). The `Prereg-hash` field below is the sha256 of this file's canonical body (the value recorded as `prereg_sha256` in this same lock).
4. `preregistration.md` — the verbatim `## Preregistration` block (the same mechanical fields returned below: `- Experiment`, `- Hypotheses`, `- Primary-metric`, `- Splits`, `- Analysis-plan`, `- Prereg-hash`, `- Rigor-tier`). This is the CANONICAL block file: every consumer (`/design-experiment`, `/analyze`, `/paper`, `/brief`) reads the `## Preregistration` block from `experiments/<exp>/preregistration.md` — never from `prereg.lock`. Do NOT conflate the two: `preregistration.md` carries hyphenated mechanical block fields; `prereg.lock` carries the hashed snake_case plan body. The `- Prereg-hash:` value here equals the sha256 in `prereg.lock`.

Returns the same `## Preregistration` block as a message AND persists it verbatim to `preregistration.md` (file 4). Field lines are mechanical — the heading and every `- <Field>:` key MUST match `hooks/block-schemas.tsv` verbatim or `block-lint.sh` rejects it:

```
## Preregistration
- Experiment: EXP-<slug>
- Hypotheses: H-001, H-002        # comma-separated H-NNN ids written to hypothesis.md
- Primary-metric: <the single pre-declared metric>   # "<MISSING — flagged>" if tier < pilot and none given
- Splits: <split definition, keyed by unit of scientific interest>
- Analysis-plan: <one-line summary; full text lives in prereg.lock>
- Prereg-hash: <sha256 of prereg.lock canonical body, full 64-hex>
- Rigor-tier: <exploratory|pilot|confirmatory|publication>   # append " (defaulted, RULE-0)" if it was missing
```

### Hard constraints
- **Refuse any hypothesis lacking an explicit falsification criterion** (RULE-5, RULE-7). The research analog of order-66's EARS-conformance refusal: a hypothesis that cannot state *what observation would prove it wrong* is not registrable. Emit the refusal and the offending hypothesis text; do not silently drop it or invent a criterion.
- **Refuse any hypothesis resting on subjective or visual-only judgement** — "the neurons look more clustered", "the attention map appears sharper", "by inspection the feature is monosemantic". There is no eyeballing (RULE-7). Every prediction must name a computable metric and a threshold. Rewrite into EARS-metric form or refuse.
- **Every `H-NNN` card is EARS-shaped**: `"When <model+config> is evaluated on <held-out set>, it shall achieve <metric> >= <threshold>."` This mirrors order-66's six EARS templates; the falsification criterion is the negation made explicit (`<metric> < <threshold>` ⇒ H rejected).
- **Exactly one primary metric** (RULE-3). Multiple "primaries" is how p-hacking enters; declare one primary and list the rest as secondary/exploratory in the card. At `confirmatory`+ the analysis_plan must name the correction (Holm or Benjamini–Hochberg) and the comparison count.
- **Splits key on the unit of scientific interest, never on rows** (RULE-10). Reject `"random 80/20 over rows"` when the unit is question/protein/prompt — that is split contamination by construction.
- **Freeze, then hash** (RULE-5). `prereg.lock` hashes the *frozen* `{primary_metric, splits, analysis_plan}` exactly as written, plus an ISO timestamp. The hash is deterministic over a canonical serialization (see prereg-lock-format.md) so it is reproducible and tamper-evident. Once written, the lock is append-only; changes go through `--amend`.
- **Tier nesting is one-directional** (CONVENTIONS §2). Do not impose a higher tier's requirements on a lower tier: `exploratory` does not need a frozen analysis_plan or a CI method; do not demand them. Conversely, do not let a `confirmatory` registration ship without seeds-justification + correction + confound-audit thresholds.
- **`status: registered`, not `running`.** `/register` is a gate, not an executor. It never launches a run, never touches `host-config.json`, never writes into `runs/`. The lifecycle transition to `running` belongs to `/execute`.
- **No absolute paths** anywhere in the written files (RULE-2). Use `${CLAUDE_PLUGIN_ROOT}` for plugin assets and `${CLAUDE_PROJECT_DIR}` for project paths; dataset/host references are relative or env-resolved.
- **Never self-grade** (RULE-1). `/register` records what *will* be tested and how it *will* be judged; it does not assert the hypothesis is true, does not pre-rate plausibility as a verdict, and does not pre-fill any `## Verdict`. Plausibility belongs in the card's novelty/cost fields as context, not as a score.

### Common mistakes (avoid)
1. **Registering a hypothesis with no falsification criterion.** Wrong: *"H-001: spectral features encode sequence length."* That is unfalsifiable as written — what result kills it? Right: *"When the probe is evaluated on the held-out qid-disjoint fold, it shall achieve balanced-accuracy ≥ 0.65 over the 0.5 baseline; if balanced-accuracy < 0.65 on that fold, H-001 is rejected."* Refuse the former; do not "fix" it by guessing the threshold the user never stated — ask, or refuse.
2. **Accepting a visual-only prediction.** *"The UMAP will show three clear clusters."* is eyeballing (RULE-7). A reviewer cannot grade "clear". Rewrite to a computable claim (e.g. silhouette score ≥ τ on a pre-declared k, or an ARI against a labeled partition) or refuse the card.
3. **Declaring more than one primary metric "to be safe."** Two primaries is two bites at significance. Pick one primary; the rest are secondary and inherit the multiple-comparison correction. Hedging the primary metric is the most common way confirmatory rigor silently degrades to exploratory.
4. **Splitting by row when the unit is a question/protein/prompt.** A random row split leaks: the same question's rows land in both folds and the probe memorizes the question, not the phenomenon. Split by the scientific unit (RULE-10) or it is a DO-NOT-PROMOTE before a single run exists.
5. **Setting `status: running` or filling `prereg_hash` at exploratory tier.** `/register` ends at `registered`; `/execute` flips it to `running`. And `prereg_hash` is *required* at confirmatory+ but *optional* at exploratory — do not fabricate a lock for exploratory work just to populate the field; emit `Prereg-hash: n/a (exploratory)` instead.
6. **Re-registering by overwriting `prereg.lock`.** If a lock exists and the plan changed, that is an `--amend` (records the prior hash + a deviation note that downstream PROMOTE will block on at confirmatory+) or a down-tier — never a silent overwrite. Overwriting the lock destroys the anti-HARKing guarantee that is the entire point of this skill.
7. **Inventing the analysis plan the user didn't give.** At confirmatory+ the estimator, CI method, variation source, and correction are *user decisions* that get frozen. If they are absent, refuse and ask — do not pick "bootstrap 1000× by seed, Holm" on the user's behalf and lock it. A guessed plan is worse than no plan because the hash makes it look authoritative.

## Dynamic

Templates: `${CLAUDE_PLUGIN_ROOT}/skills/register/templates/`. Read with the Read tool —
- `hypothesis-card.md` — the `H-NNN` card format (prediction / falsification criterion / named confounds / cost / novelty), EARS-shaped.
- `prereg-lock-format.md` — exactly what gets hashed and how (canonical serialization → sha256), so the `Prereg-hash` is reproducible and tamper-evident.

Schema: read `${CLAUDE_PLUGIN_ROOT}/templates/experiment.schema.json` for the `experiment.json` shape (only `version`, `id`, `status`, `rigor_tier` are universally required; the rest accretes per tier). Do NOT impose confirmatory-only fields (`prereg_hash`, `seed_policy.n_justification`) on an exploratory registration.

`experiments/` already exists at the project root — write to `experiments/<exp>/` directly without `mkdir -p` ceremony beyond the experiment subdirectory itself (R-2 / RULE-2: relative paths only).

If the proposal arrived from `/triage`, its `## ResearchRouting` block carries `Experiment`, `Rigor-tier`, `Signal-validated`, and `Rationale` — pass them through as `experiment`, `rigor_tier`, and the precondition checks; do not re-derive the tier.

Confirm presence/absence before generating (do not overwrite a committed lock):

- existing experiment dirs: `!{ls experiments/ 2>/dev/null || echo '(none yet)'}`
- lock guard for this exp: `!{test -f experiments/${EXP}/prereg.lock && echo 'LOCK EXISTS — refuse unless --amend' || echo 'no lock — safe to register'}`
- current UTC ISO timestamp for the lock + json stamps: `!{date -u +%Y-%m-%dT%H:%M:%SZ}`
- git commit pinned into the lock for repro (lightweight repro capture): `!{git -C ${CLAUDE_PROJECT_DIR} rev-parse --short HEAD 2>/dev/null || echo 'no-git'}`

To compute the `Prereg-hash` after writing the canonical lock body (per prereg-lock-format.md):
`!{sha256sum experiments/${EXP}/prereg.lock 2>/dev/null | cut -d' ' -f1 || echo 'WRITE-LOCK-FIRST'}`

After computing the hash, persist the `## Preregistration` block to `experiments/${EXP}/preregistration.md` (file 4) with the Write tool — the SAME verbatim block returned as the message, with the resolved `- Prereg-hash:` (the sha256 above, equal to `prereg_sha256` in `prereg.lock`). This file is the canonical block every consumer reads; the return-message copy is a convenience echo. The block is persisted, never only returned.
