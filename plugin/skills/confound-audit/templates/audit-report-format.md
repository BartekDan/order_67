<!--
audit-report-format.md — the layout for experiments/<exp>/audit.md, written by /confound-audit
(RULE-6). This is a TEMPLATE: copy the structure, fill the <angle-bracket> slots, delete this
comment and the instructional `> ` lines. The ordering is load-bearing — the FROZEN-THRESHOLDS
header is written and timestamped BEFORE any probe is computed; the per-probe sections come after;
the overall verdict last. The tail `## ConfoundAudit` block is the mechanical summary the
results-verifier and /analyze grep (CONVENTIONS §4). No absolute paths (RULE-2): use
${CLAUDE_PROJECT_DIR} / ${CLAUDE_PLUGIN_ROOT}.
-->

# Confound audit — <C-NNN> @ <EXP-slug>

- **Finding under audit:** <one-line statement of the positive finding, e.g. "H-002: a linear probe on layer-17 mean-pooled activations detects <construct> at balanced-accuracy 0.71 (+0.21 over class-prior baseline)">
- **Rigor tier:** <exploratory|pilot|confirmatory|publication> <(flag: defaulted to publication — rigor_tier missing, RULE-0) if applicable>
- **Primary statistic:** <stat> <(matches prereg) | (DEVIATES from prereg primary metric <X> — RULE-5)>
- **Split (leakage-safe per ## DataAudit PASS):** <e.g. "qid-disjoint, 5-fold, reducers fit on train fold only">
- **Source runs:** <RUN-NNN, RUN-NNN — the runs whose per-unit outputs this audit consumes>
- **Auditor:** /confound-audit · **Independent verdict owner:** results-verifier (this report does NOT grade — RULE-1)

---

## 1. FROZEN THRESHOLDS  (written <YYYY-MM-DDThh:mm:ssZ> — BEFORE any probe was computed)

> Commit to "what counts as surviving" while blind to the outcomes. This section's timestamp MUST
> precede every per-probe section below. If any probe was computed before this header existed, the
> audit is VOID — restart. This is the discipline that self-retracted proteus Eksperyment 1.

| Probe | Frozen threshold to SURVIVE | Value chosen | Rationale (pre-outcome) |
|-------|------------------------------|--------------|--------------------------|
| 1 · Permutation-null | true statistic must lie `|z| ≥ z*` vs the shuffle null | `z* = <e.g. 3.0>`, `K = <tier floor: explo 1k / pilot 5k / conf+pub 10k>` | <why this z* / K for this tier> |
| 2 · Nuisance-screen | confound must NOT be separable: `p ≥ α*` (fail to reject "distributions equal") | `α* = <e.g. 0.05>`, test = `<KS | Mann-Whitney>`, nuisance(s) = `<answer_length, …>` | <why this confound is the threat to this construct> |
| 3 · Statistic-swap | conclusion (sign + direction) holds under alt statistic, `|Δ| ≤ t*` | `alt = <e.g. L2-norm vs mean>`, `t* = <tolerance>` | <why this swap is a fair stress on the same construct> |
| 4 · Alt-preprocessing | finding reproduces under alternative pipeline, effect retained `≥ r*%` | `alt pipeline = <e.g. raw vs z-score; last-token vs mean-pool>`, `r* = <e.g. 80>` | <why this pipeline is a defensible alternative> |

- **Gate rule (frozen):** `Survives = YES` iff probes 1 AND 2 AND 3 AND 4 all PASS. No majority vote.
  An UNSCORABLE probe (inputs not fetched) ⇒ NOT a PASS ⇒ `Survives = NO` + RERUN.
- **Multiple comparisons (RULE-3):** <N = number of nuisances screened × statistics swapped>; correction = `<Holm | Benjamini–Hochberg | none (N=1)>`. Per-probe p-values below are the **corrected** values where N>1.
- **Permutation grouping (RULE-10):** labels shuffled WITHIN <split unit, e.g. qid-disjoint fold>, never across the test boundary.

---

## 2. PROBE 1 — Label-permutation null

> Shuffle the labels K times under the frozen grouping; recompute the statistic each time to build
> the null; locate the TRUE statistic against it.

- True statistic: `<v>`
- Null distribution over `K=<K>` shuffles: mean `<m>` ± sd `<s>`  (also report 2.5/97.5 percentiles: `[<lo>, <hi>]`)
- z = `(true − mean) / sd` = `<z>` · empirical `p_perm = (#null ≥ true + 1)/(K + 1) = <p>`
- Null histogram (ASCII or path to figure): `<sparkline / ${CLAUDE_PROJECT_DIR}/results/<exp>/figures/<C-NNN>_perm_null.png>`
- **Threshold (frozen):** `|z| ≥ <z*>` · **Observed:** `|z| = <z>` · **Verdict: PASS | FAIL**
- Notes: <e.g. "true stat sits at the 99.97th percentile of the null; not a chance artifact">

## 3. PROBE 2 — Nuisance-variable screen

> Test that the effect is NOT explained by a confound (canonically answer/sequence length). The
> finding SURVIVES when the confound is NOT separable between the classes the finding splits.

- Nuisance variable(s): `<answer_length>` <add rows for each additional nuisance screened>
- Test: `<KS | Mann-Whitney>` on `<nuisance>` across `<the two groups the finding distinguishes>`
- Statistic: `<D | U> = <value>` · p (corrected if N>1) = `<p>`
- Effect explained by confound? `<no | partial | yes>` — <e.g. "length distributions are statistically indistinguishable (KS D=0.04, p=0.62), so the probe is not a length detector">
- Optional control: <if partial/yes, report the finding RE-RUN with the nuisance regressed out / matched — does the effect survive the control? `<effect after control = …>`>
- **Threshold (frozen):** `p ≥ <α*>` (confound NOT separable) · **Verdict: PASS | FAIL**

## 4. PROBE 3 — Statistic-swap

> Recompute the finding with a different statistic measuring the same construct. A real effect is
> robust to the choice of summary statistic; an artifact of one statistic is not.

- Primary statistic: `<stat>` → value `<v_primary>`
- Alternative statistic: `<alt_stat, e.g. L2-norm vs mean>` → value `<v_alt>`
- Sign / direction of conclusion holds? `<yes | no>` · `|Δ| = <…>` vs frozen tolerance `t* = <t*>`
- **Verdict: PASS | FAIL** — <e.g. "mean→L2 leaves the +0.21 delta within 0.03; conclusion unchanged">

## 5. PROBE 4 — Alternative-preprocessing re-run

> Re-run the analysis through a defensibly-different preprocessing pipeline. The finding SURVIVES
> when it reproduces under the alternative; a preprocessing-specific effect does not.

- Pipeline A (primary): `<e.g. z-scored, mean-pooled, layer-17>` → effect `<e_A>`
- Pipeline B (alternative): `<e.g. raw, last-token, layer-17>` → effect `<e_B>`
- Effect retained: `e_B / e_A = <…>%` vs frozen `r* = <r*>%`
- **Verdict: PASS | FAIL** — <e.g. "last-token pooling retains 91% of the effect; not a mean-pool artifact">
- UNSCORABLE note (if applicable): <"per-unit outputs for pipeline B not fetched ⇒ UNSCORABLE ⇒ NO + RERUN; remote re-run is /execute's owned loop, not this audit's">

---

## 6. OVERALL VERDICT

- Probe 1 (permutation-null): `<PASS|FAIL>`
- Probe 2 (nuisance-screen): `<PASS|FAIL>`
- Probe 3 (statistic-swap): `<PASS|FAIL>`
- Probe 4 (alt-preprocessing): `<PASS|FAIL|UNSCORABLE>`
- **Survives (cumulative AND): `<YES | NO>`**

> If NO: this finding is REJECTED / retracted. Update its state in `${CLAUDE_PROJECT_DIR}/trace/<exp>.md`
> to REJECT and record the retraction (RULE-8 — a retracted finding is a finding; do not soften it
> into the brief). The downstream results-verifier will see REJECT. If YES: the finding proceeds to
> the independent results-verifier for the promote/reject `## Verdict` (RULE-1 — this report does not
> grade).

---

## ConfoundAudit
- Claim: <C-NNN @ EXP-slug — one-line statement of the positive finding>
- Permutation-null: true stat=<v>; null=<m>±<s> over K=<K>; z=<z>; p_perm=<p>; THRESHOLD |z|≥<z*> (frozen) — <PASS|FAIL>
- Nuisance-screen: nuisance=<name>; test=<KS|Mann-Whitney>; <D|U>=<stat>; p=<p>; explained-by-confound=<no|partial|yes>; THRESHOLD p≥<α*> (frozen) — <PASS|FAIL>
- Statistic-swap: <stat>→<alt_stat>; conclusion holds=<yes|no>; |Δ|≤t*=<t*>? — <PASS|FAIL>
- Alt-preprocessing: A=<primary>→B=<alt>; reproduces=<yes|no>; retained≥<r*>% — <PASS|FAIL|UNSCORABLE>
- Survives: <YES|NO>
