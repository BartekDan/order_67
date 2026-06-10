# `## Conflicts` RETURN FORMAT — exemplar

The `## Conflicts` block is what `/conflicts` returns and what `/execute` greps for at run-start
time. This file is the canonical reference for the block's shape. See
`${CLAUDE_PLUGIN_ROOT}/skills/conflicts/SKILL.md` for invocation semantics; see
`invariants-template.md` for how the invariants being checked are declared.

The block heading is exactly `## Conflicts` — every `/conflicts` invocation ends with this block,
even when zero findings, even when SKIPPED. The block is the ENTIRE return value: no preamble, no
trailing prose.

---

## Mechanical top-level fields (the ABI — `hooks/block-schemas.tsv`)

Per `hooks/block-schemas.tsv`, the block MUST contain these four field lines, each as a
`- <Field>:` line at the block's top level. `hooks/block-lint.sh` greps the section between
`## Conflicts` and the next `## ` heading and fails if any is missing:

1. **`- Experiment:`** — the target `EXP-slug`, or `ALL` for a whole-project scan.
2. **`- Scanned:`** — `<n peers, n invariants, n _Depends:_ edges>` (the budget receipt).
3. **`- Findings:`** — header for the per-finding list below it (`(none)` when empty).
4. **`- Verdict:`** — exactly `CLEAR` or `BLOCKER` (the only two values; no other token).

Keep per-finding keys lowercase (`severity`, `invariant_id`, …) so they never collide with the four
top-level field keys the linter matches.

---

## Per-finding shape

Each finding is a `### Finding <n>` sub-heading under `- Findings:` with these fields, in order:

1. **`severity`** — `BLOCKER` or `NIT`. (`/conflicts` has no FIXABLE; the verdict enum is binary.)
2. **`invariant_id`** — the level-2 heading ID from the declarer's `invariants.md` (e.g. `INV-001`),
   OR a structural ID: `RETRACTION-CASCADE`, `MalformedInvariant`, `ScannerFailure`, `UnknownTarget`.
3. **`declared_in`** — the experiment that declares the invariant (e.g. `_global`), or
   `retraction graph` for a cascade, or the file path for a malformed card.
4. **`violated_in`** — target `EXP-slug` + the offending path / `RUN-ID` / retracted dependency.
5. **`description`** — one-line summary of why this is a violation.
6. **`suggested_resolution`** — copied from the invariant card's `Suggested resolution:` line, or
   scanner-augmented for structural findings.

Optional:

7. **`confidence`** — `PRE-PLAN` only, when the finding is inferred from a `design.md`
   `## Compute-plan` boundary because the target has no `runs.md` yet; omit otherwise.
8. **`evidence`** — `runs.md:line` or the `experiment.json` status field when the scanner has a
   precise citation; omit when only boundary-level detection fired.

---

## Verdict rule

`- Verdict: BLOCKER` iff at least one finding has `severity: BLOCKER` whose `violated_in` names the
**current target**. A peer-only BLOCKER (violating a peer's boundary, not the target's) is reported
but does NOT flip the target's verdict. On a whole-project scan (`Experiment: ALL`) any BLOCKER flips
the verdict. Otherwise `- Verdict: CLEAR`.

---

## Mandatory summary line

The block MUST end with a single summary line in this exact form:

```
BLOCKER: <n> | NIT: <n> | scanned: <n peers, n invariants, n _Depends:_ edges>
```

---

## Exemplar — CLEAR (zero findings)

```
## Conflicts
- Experiment: EXP-spectral-length-bias
- Scanned: 4 peers, 3 invariants, 1 _Depends:_ edge
- Findings: (none)
- Verdict: CLEAR

BLOCKER: 0 | NIT: 0 | scanned: 4 peers, 3 invariants, 1 _Depends:_ edge
```

---

## Exemplar — BLOCKER (sealed-test-set leakage on the target)

```
## Conflicts
- Experiment: EXP-spectral-length-bias
- Scanned: 4 peers, 3 invariants, 1 _Depends:_ edge
- Findings:
  ### Finding 1
  - severity: BLOCKER
  - invariant_id: INV-001
  - declared_in: _global
  - violated_in: EXP-spectral-length-bias + runs.md RUN-003 _Owns:_ data/proteus/test/
  - description: RUN-003's _Owns:_ reads the sealed test split during reducer-fit;
    ForbiddenTestSetImport binds every non-_ experiment to read test data only in the
    sealed-eval run (RULE-10 train/test leakage).
  - suggested_resolution: Fit the reducer on train folds inside CV; move the test read
    into the single sealed-eval run. See experiments/_global/invariants.md INV-001.
  - evidence: experiments/EXP-spectral-length-bias/runs.md:41
- Verdict: BLOCKER

BLOCKER: 1 | NIT: 0 | scanned: 4 peers, 3 invariants, 1 _Depends:_ edge
```

---

## Exemplar — BLOCKER (retraction cascade from a `_Depends:_` upstream)

```
## Conflicts
- Experiment: EXP-length-bias-followup
- Scanned: 5 peers, 3 invariants, 2 _Depends:_ edges
- Findings:
  ### Finding 1
  - severity: BLOCKER
  - invariant_id: RETRACTION-CASCADE
  - declared_in: retraction graph
  - violated_in: EXP-length-bias-followup + _Depends:_ EXP-proteus-eksp1 (status: retracted)
  - description: This experiment _Depends:_ on EXP-proteus-eksp1, whose experiment.json
    status is "retracted" (failed its confound-audit). A retraction cascades to every
    dependent — the followup's result rests on the same uncleared confound (RULE-6).
  - suggested_resolution: Re-base the followup on a non-retracted prerequisite, or re-run
    EXP-proteus-eksp1 and clear its confound-audit before this run proceeds.
  - evidence: experiments/EXP-proteus-eksp1/experiment.json (status: retracted)
- Verdict: BLOCKER

BLOCKER: 1 | NIT: 0 | scanned: 5 peers, 3 invariants, 2 _Depends:_ edges
```

Note: the scanner halts on this first decisive target-BLOCKER (the budget is for fast veto, not an
exhaustive list) and returns immediately.

---

## Exemplar — BLOCKER (under-seeded confirmatory run, pre-plan inference)

```
## Conflicts
- Experiment: EXP-cross-model-depth
- Scanned: 6 peers, 4 invariants, 0 _Depends:_ edges
- Findings:
  ### Finding 1
  - severity: BLOCKER
  - invariant_id: INV-004
  - declared_in: _global
  - violated_in: EXP-cross-model-depth + (design.md Compute-plan: Seed-policy "1 seed")
  - description: Target is rigor_tier confirmatory but its design.md Compute-plan declares
    a single seed; RequiredSeedPolicy binds confirmatory+ to ≥3 seeds so a CI can be
    reported (RULE-7). No runs.md yet, so this is inferred from the design boundary.
  - suggested_resolution: Raise Seed-policy to ≥3 seeds (k justified) at /plan-runs, or
    down-tier to pilot.
  - confidence: PRE-PLAN
- Verdict: BLOCKER

BLOCKER: 1 | NIT: 0 | scanned: 6 peers, 4 invariants, 0 _Depends:_ edges
```

---

## Exemplar — CLEAR, SKIPPED at exploratory tier (RULE-0 tier nesting)

```
## Conflicts
- Experiment: EXP-quick-probe-sketch
- Scanned: 0 peers, 0 invariants, 0 _Depends:_ edges
- Findings: (none)
- Verdict: CLEAR
- Status: SKIPPED (exploratory tier)

BLOCKER: 0 | NIT: 0 | scanned: 0 peers, 0 invariants, 0 _Depends:_ edges
```

`/conflicts` is a pilot+ precondition. At exploratory tier the scan is skipped entirely and the
verdict is CLEAR — imposing the gate on exploratory work would re-create the bloat the tier system
exists to prevent (CONVENTIONS §2). A missing/unknown tier is NOT exploratory; it defaults to
`publication` (RULE-0) and the scan runs.

---

## Exemplar — no invariants declared anywhere, no retraction edges

```
## Conflicts
- Experiment: EXP-spectral-length-bias
- Scanned: 4 peers, 0 invariants, 1 _Depends:_ edge
- Findings: (none)
- Verdict: CLEAR
- Status: NO INVARIANTS DECLARED

BLOCKER: 0 | NIT: 0 | scanned: 4 peers, 0 invariants, 1 _Depends:_ edge
```

---

## Exemplar — unknown target (stale experiment name from a caller)

```
## Conflicts
- Experiment: EXP-does-not-exist
- Scanned: 0 peers, 0 invariants, 0 _Depends:_ edges
- Findings:
  ### Finding 1
  - severity: BLOCKER
  - invariant_id: UnknownTarget
  - declared_in: n/a
  - violated_in: EXP-does-not-exist (no experiments/EXP-does-not-exist/ on disk)
  - description: /conflicts was invoked against an experiment that does not exist. The run
    cannot be cleared because there is no boundary to check.
  - suggested_resolution: Re-run /conflicts with a valid EXP-slug, or /register the
    experiment first.
- Verdict: BLOCKER

BLOCKER: 1 | NIT: 0 | scanned: 0 peers, 0 invariants, 0 _Depends:_ edges
```

---

## Parsing notes for `/execute`

`/execute` greps the block for `- Verdict:` and reads exactly one token. `BLOCKER` ⇒ halt the run
with `[!]` (do not scp/launch anything) and surface the BLOCKER findings verbatim; `CLEAR` ⇒ proceed
to the remote launch loop. `/execute` does NOT parse the summary line for decisioning — only for the
metrics record. A `Status: SKIPPED` line with `Verdict: CLEAR` means the gate was correctly skipped
at exploratory tier; `/execute` proceeds. If the block is missing or `Verdict:` is any token other
than `CLEAR`/`BLOCKER`, `/execute` treats it as `BLOCKER` (fail-loud, RULE-0).
