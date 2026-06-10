# order-67 Research Harness — Build Roadmap

Locked decisions (2026-05-30):

| # | Decision | Choice |
|---|----------|--------|
| D-001 | Rigor tiers | 4 (exploratory/pilot/confirmatory/publication); replication is a `/triage` path |
| D-002 | GPU execution | harness owns SSH scp→launch→poll→fetch via `host-config.json` |
| D-003 | Tree autonomy | autonomous within a GPU/$/time budget; halt at cap |
| D-004 | Repro tooling | lightweight first — per-run seed+config+git+env+dataset-hash capture |
| D-005 | Pre-reg deviation | hard-block PROMOTE at confirmatory+; exploratory free |
| D-006 | Language | English for both paper and brief |
| D-007 | `## Block` ABI | validating linter hook (`block-lint.sh`) |
| D-008 | Acceptance test | re-run the proteus spectral length-bias retraction end-to-end |

## Milestones

### M1 — Foundation ✅ (this build)
- RR-001 `.claude-plugin/plugin.json` with PostToolUse(update-trace, block-lint) + Stop hooks.
- RR-002 `CONVENTIONS.md`: identifier schemes, rigor tiers, SKILL/AGENT templates, the `## Block` ABI.
- RR-003 Hooks: `update-trace.sh`, `block-lint.sh` + `block-schemas.tsv`, `stop-logger.sh`.
- RR-004 Templates: `research-rulebook.md`, `experiment.schema.json`, `host-config.example.json`.

### M2 — Skills (14)
- RR-010 `/triage` · RR-011 `/register` · RR-012 `/design-experiment` · RR-013 `/data-audit`
- RR-014 `/plan-runs` · RR-015 `/conflicts` · RR-016 `/execute` · RR-017 `/confound-audit`
- RR-018 `/analyze` · RR-019 `/verify-claim` · RR-020 `/paper` · RR-021 `/brief`
- RR-022 `/drift` · RR-023 `/note`

### M3 — Agents (6)
- RR-030 `results-verifier` (never-self-grade, tiered audit) · RR-031 `data-steward`
- RR-032 `reproducibility-checker` · RR-033 `peer-reviewer` · RR-034 `figure-smith` · RR-035 `run-reader`

### M4 — Skill templates
- Hypothesis card, design.md, model-info-sheet (Kapoor–Narayanan), datasheet (Gebru), runs.md
  experiment-tree, confound-audit report, NeurIPS checklist, paper skeleton, brief.html.

### M5 — Acceptance (validate against proteus) ✅
- RR-040 ✅ Built `examples/spectral-length-bias/` (fixture project) re-running the self-retracted
  proteus Eksperyment-1 finding end-to-end. An independent results-verifier (fresh context) reached
  `REJECT` at confirmatory tier: `/data-audit` PASS (clean qid-disjoint split) but `/confound-audit`
  `Survives: NO` (answer-length nuisance screen) — reproducing the proteus retraction. Not BLOCKED
  (the BAcc was logged). All `## Block`s pass block-lint; prereg hash consistent across artifacts.

## Deferred / open
- Auto-`/drift` on the Stop hook (order-66 left this a logging stub; we follow suit until proven —
  manual `/drift` for now, to avoid silently relying on a stub).
- Heavier repro tooling (DVC/Hydra/MLflow) — add after lightweight capture proves insufficient (D-004).
- Block-schema enforcement is advisory at PostToolUse; `/execute` re-checks as a hard precondition.
