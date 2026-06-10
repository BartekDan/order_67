---
name: confound-audit
description: Adversarial self-audit run on EVERY positive finding before it may be claimed — four probes (label-permutation null, nuisance-variable screen, statistic-swap, alternative-preprocessing re-run) with thresholds frozen FIRST; returns a `## ConfoundAudit` block whose `Survives: YES/NO` is the gate (RULE-6).
whenToUse: Fire on any positive finding produced by /execute or /analyze before it is recorded as a claim — i.e. whenever a `## RunReport` (or an /analyze pass) yields an above-chance/above-baseline effect that someone wants to call a result. Triggered by "audit this finding", "confound-check C-NNN", "does this survive a permutation test", or automatically by /execute on every positive before the results-verifier is spawned. Do NOT fire on a null result (RULE-8 records it directly) and do NOT fire after the verdict — the audit is a PRE-condition of claiming, not a re-check of an already-graded claim.
---

# /confound-audit

## Static

### Summary
Subjects one positive finding to a four-probe adversarial screen designed to make the effect disappear: a label-permutation null, a nuisance-variable screen, a statistic-swap, and an alternative-preprocessing re-run. The audit thresholds are **frozen in the report header before any probe is computed** — you commit to "what would count as surviving" while blind to the outcomes, exactly the discipline that self-retracted proteus Eksperyment 1 (the "detector" was reading answer length, not the construct). Emits a `## ConfoundAudit` block; its `Survives` field is the gate. A `NO` flips the finding to REJECT/retracted and writes `audit.md`; a `YES` lets the finding proceed to the independent `results-verifier`. This skill audits — it does **not** issue the final `## Verdict` (RULE-1).

### Preconditions
- The finding under audit exists as a positive: a `## RunReport` with a non-null `Metrics` line, or an /analyze pass with an above-baseline effect. A null finding does not enter here (RULE-8 records it directly).
- `experiments/<exp>/experiment.json` exists and carries a `rigor_tier`. Missing/unknown ⇒ treat as `publication` and flag it as blocking (RULE-0).
- The run's raw per-unit outputs are fetched locally — the per-example predictions/labels and at least one nuisance covariate (e.g. sequence/answer length) — so the null and the KS/MWU screen can be recomputed without a fresh GPU run. If only an aggregate metric was fetched, the audit cannot run: emit `Survives: NO` with `Permutation-null: UNSCORABLE — per-unit outputs not fetched` and route to RERUN (do not silently pass).
- The split is leakage-safe per the prior `## DataAudit` (PASS). An audit on a leaky split is meaningless; if `## DataAudit` Verdict was FAIL/absent, refuse and say so.

### Parameters
- `claim` — required. The C-NNN id (or a one-line statement) of the positive finding being audited, plus the experiment `EXP-<slug>`.
- `statistic` — optional. The true (primary) statistic the finding rests on (e.g. balanced-accuracy delta, mean activation, probe AUC). Defaults to the experiment's pre-registered primary metric; if it differs from prereg, flag the deviation (RULE-5).
- `nuisance` — optional. The confound to screen against (e.g. `answer_length`, `sequence_length`, `token_count`, `class_prior`). Defaults to answer/sequence length — the proteus-canonical confound — and you MAY add more; list every one screened.
- `K` — optional. Permutation count for the null. Defaults by tier: exploratory 1 000, pilot 5 000, confirmatory/publication 10 000. More is never wrong; fewer than the tier floor is a downgrade and must be flagged.
- `alt_statistic` / `alt_preprocessing` — optional. The swapped statistic and the alternative pipeline for probes 3 and 4. Defaults: `alt_statistic` = L2-norm if the primary is a mean (and vice-versa); `alt_preprocessing` = re-run with the opposite of the primary normalization choice (e.g. z-score ⇄ raw, or last-token ⇄ mean-pool).

### Output format
A `## ConfoundAudit` RETURN FORMAT block. The heading and the six `- <Field>:` keys are mechanical (the `results-verifier` and `/analyze` grep them); emit them verbatim and in this order. The frozen-threshold header is written to `audit.md` **before** the field values are filled — the block is the summary of that report, not a substitute for it.

```
## ConfoundAudit
- Claim: <C-NNN @ EXP-slug — one-line statement of the positive finding>
- Permutation-null: <true stat = <v>; null mean±sd = <m>±<s> over K=<K> shuffles; z = <z>; p_perm = <p>; THRESHOLD |z|≥<z*> (frozen) — PASS|FAIL>
- Nuisance-screen: <nuisance=<name>; test=<KS|Mann-Whitney>; statistic=<D|U>; p=<p>; effect explained by confound? <no|partial|yes>; THRESHOLD p≥<a*> i.e. confound NOT separable (frozen) — PASS|FAIL>
- Statistic-swap: <primary=<stat>→alt=<alt_stat>; conclusion sign/direction holds? <yes|no>; |Δ| within frozen tolerance <t*>? — PASS|FAIL>
- Alt-preprocessing: <pipeline A=<primary>→B=<alt>; finding reproduces under B? <yes|no>; THRESHOLD effect retained ≥<r*>% (frozen) — PASS|FAIL>
- Survives: <YES|NO>
```

`Survives: YES` iff **all four probes PASS** (cumulative AND — there is no majority vote). Any single FAIL ⇒ `Survives: NO`. An UNSCORABLE probe (inputs not fetched) is NOT a PASS and NOT a FAIL: it forces `Survives: NO` and a RERUN recommendation in `audit.md`, mirroring the BLOCKED≠REJECT distinction (CONVENTIONS §4) — an unobservable confound check is never scored as success.

### Hard constraints
- **Freeze thresholds FIRST, while blind to outcomes (RULE-6).** Write the frozen-threshold header of `audit.md` (z*, α*, swap tolerance t*, retention r*, K) before computing a single probe. Choosing |z*| after seeing z=2.7 is the exact HARKing the audit exists to catch. The frozen header is timestamped (ISO-8601) and the timestamps must precede the per-probe sections in the file.
- **All four probes are mandatory; the gate is cumulative-AND.** You may not skip a probe because the finding "obviously" survives, and you may not pass on 3-of-4. One FAIL retracts the finding.
- **A NO retracts.** On `Survives: NO` you MUST write `experiments/<exp>/audit.md` and update the finding's state to REJECT/retracted in `trace/<exp>.md`; the downstream `results-verifier` will see REJECT. Do not soften a NO to "promising but". (This is what self-retracted proteus Eksperyment 1.)
- **Never self-grade the final verdict (RULE-1).** This skill produces the audit evidence and the `Survives` gate only. The promote/reject `## Verdict` is the independent `results-verifier`'s, on a fresh write-disabled context. Emitting a `## Verdict` here is a violation.
- **Report K and every comparison (RULE-3).** If you screen multiple nuisances or swap multiple statistics, that is multiple comparisons — declare the count and the correction (Holm/BH) in `audit.md`; the block's per-probe lines report the corrected p where correction applies.
- **Permutation respects the split unit (RULE-10).** Shuffle labels within the leakage-safe grouping (e.g. permute within qid-disjoint folds), never across the test boundary. A permutation that crosses the split inflates the null and is wrong.
- **Tier-graded, NOT tier-independent (RULE-6, RULE-0, §2).** confound-audit is tier-graded: **exploratory** positives are FLAGGED, not audited (no confound-audit required). At **pilot** a positive must pass AT MINIMUM the label-permutation-null probe of this audit BEFORE it may be claimed or PROMOTED — pilot gates expensive confirmatory spend, so the Eksperyment-1 length-confound is screened here (the cheapest single probe, at the exploratory K floor, without mandatory FDR). At **confirmatory+** the FULL four-probe screen (permutation-null + nuisance-screen + statistic-swap + alt-preprocessing) is MANDATORY and `Survives: YES` is required to PROMOTE. The K floor and whether multiple-comparison correction is enforced scale with `rigor_tier`; never impose a publication-tier K (10 000) or a NeurIPS-grade write-up on a `pilot` audit — that re-creates the bloat the tier system prevents.
- **No absolute paths (RULE-2).** All paths via `${CLAUDE_PROJECT_DIR}` (the project under study) / `${CLAUDE_PLUGIN_ROOT}` (templates). The audit recomputes locally on fetched outputs; it does not own the remote loop.

### Common mistakes (avoid)
1. **Setting the threshold after seeing the statistic.** Reading z=3.1 and then declaring "|z|≥3 survives" is precisely the failure mode RULE-6 exists for. The frozen header is written, and timestamped, before any probe runs. If you computed a probe before freezing, the audit is void — restart with a frozen header.
2. **Passing on a majority of probes.** "Permutation, swap, and preprocessing all passed; the length screen was a little borderline" is a `Survives: NO`. The gate is AND, not vote. A real construct survives a confound screen; a confounded one does not.
3. **Screening only the obvious nuisance.** Answer/sequence length is the proteus-canonical confound and the default, but it is not the only one — class prior, position, and prompt-template artifacts confound too. Defaulting to length without thinking about the actual data-generating process is how the next Eksperyment 1 ships.
4. **Auditing an aggregate.** If only `accuracy=0.71` was fetched and not the per-example predictions, you cannot permute, cannot run KS/MWU, cannot swap. That is `Survives: NO` + UNSCORABLE + RERUN — not a generous PASS. Never score an unobservable check as success.
5. **Treating the audit as a re-check after the verdict.** The audit is a PRE-condition of claiming — it runs before the `results-verifier` sees the finding, so a confounded finding never reaches the verdict as a positive. Running it afterwards inverts the gate.
6. **Permuting across the leakage-safe split.** Shuffling labels globally (ignoring qid grouping) builds a null that is too easy to beat, manufacturing a spurious PASS. Permute within the split unit only (RULE-10).
7. **Softening a NO into the brief.** A retracted finding is a finding (RULE-8): record the retraction in `audit.md` and `trace/`. "We saw a signal but couldn't fully confirm it" smuggles a dead claim back in.

## Dynamic

Audit-report layout: read `${CLAUDE_PLUGIN_ROOT}/skills/confound-audit/templates/audit-report-format.md` and follow it for `experiments/<exp>/audit.md` — the **frozen-thresholds header first**, then per-probe null distributions and verdicts, then the overall `Survives`. The `## ConfoundAudit` block you return is the tail summary of that file.

Rulebook: `${CLAUDE_PLUGIN_ROOT}/templates/research-rulebook.md` — this skill is the operationalization of **RULE-6** and leans on RULE-0 (fail-loud tier), RULE-1 (no self-grade), RULE-3 (report N + correct), RULE-5 (prereg deviation), RULE-8 (nulls are results), RULE-10 (leakage-safe permutation). Field/block contract: `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` §4.

Resolve the tier and primary metric (don't re-derive them) from:
- experiment state — `!{cat ${CLAUDE_PROJECT_DIR}/experiments/*/experiment.json 2>/dev/null | grep -E '"(id|status|rigor_tier|prereg_hash)"'}`
- the upstream leakage gate (must be PASS) — `!{grep -A1 '^## DataAudit' ${CLAUDE_PROJECT_DIR}/trace/*.md 2>/dev/null | grep -iE 'verdict|leak'}`
- the positive finding under audit and whether per-unit outputs were fetched — `!{ls ${CLAUDE_PROJECT_DIR}/results/*/runs/*/ 2>/dev/null | grep -iE 'pred|label|per_unit|raw|nuisance|length'}`

If the tier is absent ⇒ publication-strict + flag (RULE-0). If per-unit outputs are absent ⇒ the audit is UNSCORABLE ⇒ `Survives: NO` + RERUN; do not request a fresh GPU run from here (that is /execute's owned remote loop) — surface the gap and stop. If `## DataAudit` is absent or FAIL ⇒ refuse and say the split is unaudited.
