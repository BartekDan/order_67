---
name: data-audit
description: The data-hygiene GATE that runs before any experiment touches compute — fills the Kapoor–Narayanan model-info-sheet (L1/L2/L3 leakage), runs static leakage checks (fit-before-split, cross-split duplicates, label-correlated features, temporal/group disjointness, qid-level split, leakage-safe CV) and a committed-secret scan, then returns a `## DataAudit` block with a hard PASS/FAIL Verdict. Cites RULE-10.
whenToUse: Invoke after /design-experiment has produced a `## DesignDraft` (so the dataset_refs are known) and BEFORE /plan-runs or /execute. Triggered by "/data-audit <exp>", "audit the data", "leakage check", "is this dataset safe to run", or when /execute's precondition fires. Often delegated to the data-steward agent for the mechanical scans. Do NOT fire on an experiment with no declared datasets — return BLOCKED-style FAIL telling the user to run /design-experiment first.
isEnabled: test -d experiments
---

# /data-audit

## Static

### Summary
The leakage gate. For one experiment `EXP-<slug>`, fill the Kapoor–Narayanan model-info-sheet (the ~21-question leakage protocol, organized as L1 train/test contamination, L2 illegitimate features, L3 sampling/population scope), run the static leakage checks against the dataset code and split definition, run a committed-secret scan over the experiment + dataset code, and require a Gebru-style Datasheet for any NEW dataset. Return a `## DataAudit` block whose `Verdict` is `PASS` or `FAIL`. **A blank L1/L2/L3 justification is an automatic `FAIL`** — silence is not safety (RULE-10). This skill is a *precondition* to compute: `/plan-runs` and `/execute` refuse to proceed past a `FAIL`.

### Preconditions
- `experiments/<exp>/experiment.json` exists and carries `dataset_refs` (populated by `/design-experiment`; this is where the `## DesignDraft` `Datasets` line lands). If `dataset_refs` is empty or absent, the audit cannot run — return a `FAIL` with `Verdict: FAIL` and a single check telling the user to run `/design-experiment` first. Do not fabricate datasets.
- `experiments/<exp>/data-audit/` is writable (the filled model-info-sheet and any datasheet stubs are written there).
- The dataset *loader* / split code is reachable under `${CLAUDE_PROJECT_DIR}` (e.g. `src/**/data*.py`, `**/dataset*.py`, the notebook that builds splits). The harness owns no remote data fetch here — static checks read code and config, not the 7.4 TB of remote tensors. If the loader is remote-only, audit the committed config + split spec and record `Leakage-checks` entries as `UNVERIFIABLE-REMOTE` rather than `PASS`.

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`); must match a directory under `experiments/`.
- `dataset` — optional. Restrict the audit to one named dataset from `dataset_refs` (re-audit after a fix). Default: every dataset in `dataset_refs`.
- `--new` — optional flag. Marks at least one dataset as NEW (first appearance in this project), which makes the Gebru Datasheet stub MANDATORY for it; absent the flag, the skill still infers NEW from a `dataset_refs[].hash` that appears in no prior `experiments/*/data-audit/` record and treats it as NEW with a flag.

### Output format
A `## DataAudit` RETURN FORMAT block. The heading and every `- <Field>:` key below are mechanical (the `block-lint` hook and `/execute`'s precondition grep them verbatim — `Experiment`, `L1`, `L2`, `L3`, `Leakage-checks`, `Secret-scan`, `Verdict`). The `Verdict` line is one of exactly `PASS` / `FAIL` — nothing else (this is a gate, not a graded score; the four+one PROMOTE-family strings belong to `## Verdict`, not here).

```
## DataAudit
- Experiment: EXP-<slug>
- Rigor-tier: <exploratory|pilot|confirmatory|publication>  (echoed from experiment.json; missing ⇒ publication + flag, RULE-0)
- Model-info-sheet: experiments/<exp>/data-audit/model-info-sheet.md  (filled; <n>/21 answered)
- L1: <PASS|FAIL> — train/test contamination — justification: experiments/<exp>/data-audit/model-info-sheet.md#L1  (or: <inline one-liner>)
- L2: <PASS|FAIL> — illegitimate / label-leaking features — justification: …#L2
- L3: <PASS|FAIL> — sampling / population-scope leakage — justification: …#L3
- Leakage-checks:
  - fit-before-split (L1.2/L1.3): <PASS|FAIL|UNVERIFIABLE-REMOTE> — <evidence file:line or note>
  - duplicate-rows-across-splits (L1.4): <PASS|FAIL|UNVERIFIABLE-REMOTE> — <n dups / 0>
  - label-correlated-features (L2 proxy, |r|≥<thr>): <PASS|FAIL|N/A> — <feature: r>
  - temporal/group-disjoint (L3): <PASS|FAIL|N/A> — <flag value + evidence>
  - qid-level-split (RULE-10): <PASS|FAIL> — split unit = <qid|row|file|group>
  - leakage-safe-CV (RULE-10): <PASS|FAIL|N/A> — reducers fit on train fold only: <yes|no>
- Datasheet: <name>: <PRESENT|STUB-WRITTEN|NOT-REQUIRED|MISSING> — experiments/<exp>/data-audit/datasheet-<name>.md
- Secret-scan: <CLEAN|HIT> — scanned <n> files; <hits or "no committed credentials">
- Verdict: <PASS|FAIL>
```

`Verdict: FAIL` if ANY of: an L1/L2/L3 justification is blank or the corresponding L is `FAIL`; any `Leakage-checks` line is `FAIL`; the `Secret-scan` is `HIT`; a NEW dataset's Datasheet is `MISSING`. `Verdict: PASS` only when every required line is `PASS`/`PRESENT`/`CLEAN`/`N/A`. `UNVERIFIABLE-REMOTE` does NOT pass at `confirmatory`/`publication` (it becomes a `FAIL` there per RULE-0's strict-default spirit); at `exploratory`/`pilot` it is allowed through but flagged.

### Hard constraints
- **Blank ⇒ FAIL (the central rule, RULE-10).** Each of L1, L2, L3 MUST carry a non-empty justification (a pointer into the filled model-info-sheet, or an inline one-liner). An empty justification, a `TODO`, an `N/A` without a stated reason, or "looks fine" is treated as blank ⇒ `Verdict: FAIL`. Never PASS an L on absence of evidence. This is the leakage analog of the never-self-grade law: the producer must *positively demonstrate* hygiene, not assert it.
- **qid-level split is mandatory, not row-level (RULE-10).** Split by the unit of scientific interest (question id for proteus's QA-derived data; group/subject elsewhere), never by row. A row-level split where rows from the same `qid` straddle train and test is a `FAIL` on the `qid-level-split` line regardless of how clean the rest looks — this is the single most common silent leak.
- **Reducers fit on the train fold only (RULE-10).** Any PCA / scaler / feature-selector / dimensionality reducer / answer-length normalizer fit on combined-or-test data is a `FAIL` on `leakage-safe-CV`. A `.fit()` (or `fit_transform`) called before the split, or on `X` rather than `X_train`, is the `fit-before-split` (L1.2/L1.3) `FAIL` and must cite `file:line`.
- **The secret-scan HIT is a hard FAIL — and motivated by a real incident.** A live key was found committed in the proteus repo. Scan the experiment dir + reachable dataset/loader code under `${CLAUDE_PROJECT_DIR}` for the patterns `sk-`, `Bearer `, AWS access keys (`AKIA[0-9A-Z]{16}`), `password=`/`passwd=`/`pwd=` with a non-placeholder value, and `-----BEGIN` (any PEM private key block). A hit FAILS the audit AND must surface the offending `file:line` so it can be rotated and purged from history. Do NOT print the secret value itself in the block — cite the location only.
- **Datasheet required for any NEW dataset (Gebru 7-category).** A dataset whose content-hash is unseen in this project's prior audits needs a `datasheet-<name>.md` stub with all 7 Gebru categories, the mandatory **"should-NOT-be-used-for"** statement, and an explicit **license/consent** line. A NEW dataset with a `MISSING` datasheet is a `FAIL`. (For an already-audited hash, `NOT-REQUIRED` is fine.)
- **Tiers nest; never over-impose (CONVENTIONS §2, RULE-0).** The full leakage battery, blank⇒FAIL, and secret-scan apply at *every* tier (no-leakage and no-committed-secret are in the `exploratory` floor). The Datasheet + the L3 population-scope rigor + treating `UNVERIFIABLE-REMOTE` as FAIL escalate at `confirmatory`/`publication`. A missing `rigor_tier` ⇒ audit at `publication` strictness and add a flag line. Never run a higher tier's escalations against `exploratory` work.
- **Read-only on the project; write only under the audit dir (RULE-2).** `/data-audit` does not edit the dataset, the loader, or the splits — it diagnoses. It writes only the filled `model-info-sheet.md` and any `datasheet-*.md` under `experiments/<exp>/data-audit/`. No absolute paths in any output; use `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PROJECT_DIR}`-relative or project-relative paths.
- **Cite evidence (`file:line`) on every FAIL.** "Feels leaky" is not actionable. A `FAIL` line with no evidence pointer is itself malformed — either find the line or downgrade the claim to `UNVERIFIABLE-REMOTE` with a stated reason.

### Common mistakes (avoid)
1. **PASSing an L because the justification box is empty rather than because the data is clean.** Blank is `FAIL`, full stop (RULE-10). The whole point of the Kapoor–Narayanan sheet is to force a positive, written justification; an unanswered question is the *most* dangerous state, not a neutral one. Reviewers who skim and tick boxes are exactly how proteus's Eksperyment 1 leaked.
2. **Accepting a row-level split because per-row classes look balanced.** Balance across rows says nothing about `qid` straddling. If 40 rows of one question land 25-in-train/15-in-test, the model memorizes the question, not the phenomenon — and your held-out metric is inflated. Check the split *unit*, not the class balance.
3. **Scanning only `.env`/config for secrets and skipping notebooks + the loader.** The live proteus key was in code, not in a dotfile. Scan every reachable `.py`, `.ipynb`, `.sh`, `.json`, `.yaml`, and `.toml` under the experiment + dataset boundary. And never echo the matched secret into the block — cite `file:line` only, or you have just leaked it into `trace/`.
4. **Treating `fit_transform` on the whole matrix as "preprocessing, not modeling".** A scaler/PCA/selector is part of the model's information path. Fitting it before the split (or on `X` instead of `X_train` inside the CV fold) leaks test-set statistics into training — `fit-before-split` `FAIL` (L1.2/L1.3) with a cited line.
5. **Letting `UNVERIFIABLE-REMOTE` masquerade as `PASS` at confirmatory+.** "The loader runs on the GPU box and I couldn't read it" is not a clean bill of health. At `confirmatory`/`publication` an unverifiable check is a `FAIL` (RULE-0 strict-default): pull the split spec local, or down-tier the experiment. At `exploratory`/`pilot` it passes-with-flag.
6. **Promoting a re-used dataset to NEW (forcing a redundant datasheet) — or demoting a genuinely new one.** Decide NEW by the `dataset_refs[].hash` against prior `experiments/*/data-audit/` records, not by the name string. A renamed-but-identical dataset is `NOT-REQUIRED`; a same-named-but-re-collected one (new hash) is NEW and needs the stub.

## Dynamic

Templates live under `${CLAUDE_PLUGIN_ROOT}/skills/data-audit/templates/`. Read both with the Read tool at skill startup — they are the single source of truth for what the steward fills in:
- `model-info-sheet.md` — the ~21-question Kapoor–Narayanan leakage protocol as fillable blanks, grouped L1 / L2 / L3. Copy it to `experiments/<exp>/data-audit/model-info-sheet.md` and fill every blank; the per-section verdict feeds the `L1` / `L2` / `L3` block lines.
- `datasheet.md` — the Gebru 7-category Datasheet stub (Motivation / Composition / Collection / Preprocessing / Uses / Distribution / Maintenance) with the mandatory "should-NOT-be-used-for" and license/consent fields. Copy to `experiments/<exp>/data-audit/datasheet-<name>.md` per NEW dataset.

This experiment already exists when the skill fires — read its state directly, do not re-derive it:

`!{cat experiments/<exp>/experiment.json 2>/dev/null | grep -E '"(id|rigor_tier|status)"'}` — echo `id` and `rigor_tier` into the block (`rigor_tier` missing ⇒ publication + flag, RULE-0).

`!{grep -A30 '"dataset_refs"' experiments/<exp>/experiment.json 2>/dev/null}` — the datasets to audit, each with `name` / `hash` / `split`. The `split` string is your first read on the `qid-level-split` line.

`!{ls experiments/<exp>/data-audit/ 2>/dev/null}` — what audit artifacts already exist (a prior partial run; do not clobber a filled sheet without folding its answers forward).

`!{ls experiments/*/data-audit/ 2>/dev/null | grep -iE 'datasheet'}` — prior datasheets across the project; cross-reference a dataset's `hash` here to decide NEW vs NOT-REQUIRED rather than re-stubbing.

Locate the split / loader code to run the static checks against (best-effort under the project):
`!{grep -rnE 'train_test_split|GroupKFold|StratifiedKFold|\.fit\(|fit_transform|groupby\(.*qid|by\s*=\s*.qid' ${CLAUDE_PROJECT_DIR} --include='*.py' --include='*.ipynb' 2>/dev/null | head -40}` — anchors for `fit-before-split`, `qid-level-split`, and `leakage-safe-CV`; confirm each hit's ordering relative to the split and cite the line.

Committed-secret scan (the FAIL-on-hit gate; cite `file:line`, never echo the value):
`!{grep -rnoE 'sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{12,}|(password|passwd|pwd)\s*=\s*[^ \t"'"'"']{6,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' ${CLAUDE_PROJECT_DIR} --include='*.py' --include='*.ipynb' --include='*.sh' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.env' 2>/dev/null | head -20}` — any line of output is a `Secret-scan: HIT` ⇒ `Verdict: FAIL`. Empty output ⇒ `CLEAN`. (No `jq` dependency — pure grep per RULE-2.)

When the mechanical scans are heavy or the loader is large, delegate the whole audit to the `data-steward` agent (fresh context); it fills the sheet, runs the grep battery, and returns the same `## DataAudit` block. The producer of the data still does not grade their own hygiene where a steward is available (RULE-1 spirit).
