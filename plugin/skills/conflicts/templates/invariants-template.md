# `invariants.md` — canonical invariant-card shape

Copy this file into `experiments/<your-exp>/invariants.md` (or `experiments/_global/invariants.md`
for project-wide rules) and edit. Each invariant declared here is evaluated by `/conflicts` against
the experiments listed in `applies_to`, as a precondition before `/execute` commits a GPU run. See
`${CLAUDE_PLUGIN_ROOT}/skills/conflicts/SKILL.md` for scanner semantics; see `conflicts-format.md`
in this same directory for the `## Conflicts` block the scanner produces.

An invariant is a **cross-experiment scope rule** — a contract one experiment imposes on its peers
(or the whole project) about what they may import, where they may read sealed data, where they may
write checkpoints, and how they must seed. It is NOT a hypothesis (that lives in `hypothesis.md`)
and NOT a within-experiment analysis choice (that lives in the pre-registration).

---

## Frontmatter (required)

```yaml
---
experiment: <EXP-slug>        # MUST equal the directory name under experiments/
                              # (use "_global" for the project-wide pseudo-experiment)
version: "1"                  # Card schema version; only "1" is recognized today
applies_to:                   # List of peer experiment IDs this invariant binds.
  - EXP-<peer-1>              # OR the literal [ALL] to bind every experiment
  - EXP-<peer-2>              # except the declaring experiment itself.
severity_default: BLOCKER     # BLOCKER | NIT — per-invariant Severity may override;
                              # this is the floor. (/conflicts' verdict enum is
                              # CLEAR/BLOCKER, so NIT findings never gate a run —
                              # they are reported for the record only.)
created: <YYYY-MM-DD>         # ISO-8601, absolute (never "today").
maintainer: <email>
---
```

All four required fields (`experiment`, `version`, `applies_to`, `severity_default`) MUST be present
or `/conflicts` emits a BLOCKER-severity `MalformedInvariant` finding. `applies_to` may name
experiments that do not yet exist on disk — a future-experiment name is accepted so an experiment can
declare an invariant in advance of the consuming experiment being registered.

---

## Invariant shapes (supported today)

`/conflicts` recognizes four shapes inside the body. Each invariant is a level-2 heading (`##`)
followed by a structured paragraph and an `**INVARIANT:** <shape>: <body>` line the scanner parses.
All four encode a property reverse-engineered from a way real mech-interp work leaked, clobbered, or
under-powered itself.

### 1. `ForbiddenTestSetImport`

Use when no run in the target experiment's boundary may import or read the sealed test set. The
single hardest leakage failure (RULE-10): a feature selector or reducer that ever touches test rows.

```markdown
## INV-001 — No run may import the sealed test split

**Rationale:** The held-out qid-level test split for the proteus probe must never be
read outside the final sealed-eval call. Any preprocessing, reducer-fit, or
feature-selection that touches `data/proteus/test/**` is train/test leakage and makes
every downstream effect size uninterpretable (RULE-10).

**INVARIANT:** ForbiddenTestSetImport: `data/proteus/test/` | `load_test_split(` |
`split="test"` (in any run whose `_Owns:_` is in an applies_to experiment, EXCEPT the
single sealed-eval run declared in RequiredSealedEvalPath below)

**Severity:** BLOCKER

**Suggested resolution:** Fit all reducers/selectors on the train fold inside CV only;
read the test split exactly once, in the sealed-eval run. See
experiments/_global/invariants.md INV-001.
```

### 2. `RequiredSealedEvalPath`

Use when held-out evaluation must read from one declared sealed path and only there.

```markdown
## INV-002 — Held-out eval reads only the sealed path

**Rationale:** Leakage-safe-by-construction (RULE-10): the only legitimate read of
held-out data is the final sealed evaluation, and it must come from the frozen sealed
directory so the split cannot be silently re-derived.

**INVARIANT:** RequiredSealedEvalPath: any eval run in an applies_to experiment MUST
read held-out data only from `data/proteus/sealed/` and MUST list that path in its
`_Owns:_` as read-only; an eval `_Owns:_` naming any other held-out source is a finding

**Severity:** BLOCKER

**Suggested resolution:** Point the eval run at `data/proteus/sealed/`; remove any
ad-hoc held-out path from its `_Owns:_`.
```

### 3. `AllowedCheckpointGlob`

Use when checkpoints a run writes must match a glob (a write-whitelist). Prevents one experiment
clobbering a peer's frozen baseline — an `_Owns:_` collision that silently corrupts a comparison.

```markdown
## INV-003 — Checkpoints stay inside the experiment's own scope

**Rationale:** A frozen baseline checkpoint is a shared dependency for several
experiments. A run that writes a checkpoint outside its own scope can overwrite that
baseline, and every comparison against it becomes a comparison against garbage.

**INVARIANT:** AllowedCheckpointGlob: checkpoints written by an applies_to experiment
MUST match `results/${EXP}/checkpoints/**`; a checkpoint path matching
`models/frozen/**` or another experiment's `results/**` is a finding

**Severity:** BLOCKER

**Suggested resolution:** Redirect the run's checkpoint dir into
`results/<this-exp>/checkpoints/`; never write under `models/frozen/`.
```

### 4. `RequiredSeedPolicy`

Use when peers must meet a minimum seed policy so their headline metric can carry a CI (RULE-7).

```markdown
## INV-004 — Confirmatory runs carry ≥3 seeds

**Rationale:** RULE-7 — an effect size needs a named variation source and a CI. A
single-seed confirmatory run cannot report seed-variance, so its CI is undefined and
the claim is not a confirmatory result.

**INVARIANT:** RequiredSeedPolicy: any applies_to experiment at rigor_tier
confirmatory+ MUST declare a `Seed-policy` of ≥3 seeds (k justified) in its `## RunPlan`;
a weaker policy is a finding

**Severity:** BLOCKER

**Suggested resolution:** Raise `Seed-policy` to ≥3 seeds with a one-line justification,
or down-tier the experiment to pilot.
```

---

## Worked example — `experiments/_global/invariants.md`

```yaml
---
experiment: _global
version: "1"
applies_to: [ALL]
severity_default: BLOCKER
created: 2026-05-30
maintainer: bartek.dan@gmail.com
---
```

```markdown
## INV-001 — No run may import the sealed test split (project-wide)

**Rationale:** Leakage is the single most common way a mech-interp result silently
inflates. The sealed proteus test split is read exactly once, by the sealed-eval run.
Any other read is RULE-10 train/test leakage.

**INVARIANT:** ForbiddenTestSetImport: `data/proteus/test/` | `load_test_split(`
(in any run in any non-`_` experiment's `_Owns:_`, EXCEPT the sealed-eval run)

**Severity:** BLOCKER

**Suggested resolution:** Fit on train folds inside CV; read sealed data once. See
experiments/_global/invariants.md.
```

---

## Retraction cascade (no card needed — the dependency graph carries it)

`/conflicts` ALSO walks the `_Depends:_` graph independently of any card here: if an experiment the
target depends on has `status: retracted` in its `experiment.json` (or a `REJECT`+retraction in
`trace/<dep>.md`), the scanner raises a `RETRACTION-CASCADE` BLOCKER on the target. A retraction
propagates to every dependent because the dependent's result rests on a confound the upstream already
failed to clear (RULE-6). You do NOT declare this as an invariant — it is structural, derived from
the `_Depends:_` edges plus upstream status. To clear it: re-base the experiment off a non-retracted
prerequisite, or re-run the upstream and clear its confound-audit first.

---

## What this file is NOT

- **Not a hypothesis.** Falsifiable `H-NNN` cards live in `experiments/<exp>/hypothesis.md`.
- **Not a pre-registration.** {hypothesis, primary metric, splits, analysis plan} are hash-locked by
  `/register`, not here.
- **Not a per-run boundary.** `_Owns:_`/`_Depends:_` annotations live in `runs.md`. An invariant
  *constrains* boundaries across experiments; it does not declare them.
- **Not a place for taste.** "I prefer a different optimizer" is not a cross-experiment invariant.

---

## When to declare an invariant here vs. solve it differently

Declare here when:
- The rule binds ≥2 experiments (single-experiment rules belong in `hypothesis.md` / the prereg).
- Detection requires reading another experiment's boundary, imports, checkpoints, or seed policy.
- A violation lands silently today and only surfaces after an expensive GPU run has already burned
  budget on a contaminated result.

Solve differently when:
- The rule is enforceable inside one run by an assertion or a leakage-safe CV harness — put it there.
- The rule is a within-experiment analysis choice — pre-register it via `/register`.
- The rule is a repo-hygiene rule (no committed secrets) — that is `/data-audit`'s secret scan.
