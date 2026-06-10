# Run Manifest (template)

The per-run layout `/execute` writes for every dispatched run, plus the exact lightweight repro bundle.
One directory per run: `experiments/<exp>/runs/<RUN-NNN>/`. Reduced result artifacts (and only those —
never the raw multi-TB tensors) are fetched into `results/<exp>/<RUN-NNN>/` via `host-config.json:fetch.result_globs`.
Repro capture is deliberately lightweight (D-004): seed + full resolved config + git commit +
env/lockfile + dataset content-hash. No heavyweight container snapshotting; the bundle must be enough to
re-launch the identical run on the remote host.

## `experiments/<exp>/runs/<RUN-NNN>/` layout

```
experiments/<exp>/runs/RUN-007/
├── run-report.md          # the ## RunReport block (CONVENTIONS §4); block-lint-clean
├── seed.txt               # the single integer seed for this run (one of experiment.json:seed_policy.seeds)
├── config.resolved.json   # FULL resolved config — every default expanded, nothing implicit
├── git.commit             # git rev-parse HEAD of the run script at dispatch time (+ "-dirty" if the tree was dirty)
├── env.lock               # remote interpreter + pinned deps (pip freeze / uv lock) from {remote.python}'s venv
├── dataset.hash           # content-hash(es) of the dataset(s) used; MUST match experiment.json:dataset_refs[].hash
├── launch.cmd             # the exact rendered launch.cmd_template that was scp'd + run (creds shown as $ENV names only)
├── run.log                # the fetched remote stdout/stderr (fetch.result_globs)
├── metrics.json           # the fetched reduced metrics (primary + declared secondaries); source of the Metrics field
├── poll.log               # timestamped SSH-poll samples: pgrep alive? + nvidia-smi util/mem + df workdir
├── quicklook/             # non-blocking checkpoint snapshot (experiment.json:quicklook): metrics + figure
│   ├── quicklook.png
│   └── quicklook.json
└── verdict.md             # the results-verifier's ## Verdict block (RULE-1: authored by the verifier, NOT by /execute)
```

`results/<exp>/<RUN-NNN>/` mirrors the fetched reduced artifacts (figures, reduced `.npz`) outside the
`experiments/` tree so `/analyze` and `/paper` read them without touching the run's repro bundle.

## The lightweight repro bundle (what must be present)

- **Seed** — `seed.txt`. The single seed this run used. At `confirmatory+`, the node runs once per seed in
  `experiment.json:seed_policy.seeds`; each seed is its own `RUN-NNN` with its own bundle.
- **Full resolved config** — `config.resolved.json`. Not the template, the *resolved* config: every default
  expanded so the run is reconstructible without re-reading the skill's defaults. Implicit defaults are how
  silent drift creeps in between runs.
- **Git commit** — `git.commit`. The commit of the run script (and analysis code) at dispatch. A dirty tree
  is recorded as `<sha>-dirty` and flagged in `## Run Notes` — a dirty-tree run is never PROMOTE-able at
  `confirmatory+`.
- **Env / lockfile** — `env.lock`. The remote interpreter version + pinned dependency set from `{remote.python}`'s
  venv (`pip freeze` / `uv lock`). This is what `reproducibility-checker` reads for the NeurIPS items 4–8.
- **Dataset content-hash** — `dataset.hash`. The immutable content-hash of every dataset/split consumed,
  matching `experiment.json:dataset_refs[].hash`. A mismatch (data changed under the run) is a hard halt —
  the comparison baseline moved (closes proteus's no-checksum gap, D-004).

A missing seed / config / commit / env / hash at `confirmatory` or `publication` tier is a blocking issue
(RULE-0). At `exploratory`/`pilot` a missing piece is flagged in `## Run Notes` but does not halt (tiers nest).

## `## Run Notes` (appended to the node in `runs.md` after the verifier returns)

3–7 bullets, mirroring order-66's Implementation Notes; subsequent nodes MUST read prior Run Notes (RR-020).
Categories:

- **Decisions** — chose config/seed/budget X over Y because Z; how it constrains child nodes.
- **Gotchas** — remote surprises (OOM at batch N, a flaky data mount, a non-deterministic kernel, a dirty tree).
- **Result** — the primary-metric value + the verifier's verdict (PROMOTE / PROMOTE-WITH-CAVEAT / RERUN / REJECT / BLOCKED).
- **Confound-audit** — for a positive: did it survive (`Survives: YES/NO`)? what was screened?
- **Rigor debt** — for PROMOTE-WITH-CAVEAT: the `RIGOR_DEBT(due:YYYY-MM-DD):` marker text + remediation.
- **Follow-up** — deferred child node / re-run / down-tier (with node id); never silent.

## Example

```
## Run Notes — N-3 spectral-length-bias / seed-sweep (RUN-007)

- **Decisions:** Seed 1337 of {1337,2024,7}; froze reducer fit to the train fold only (RULE-10). Batch 64 to fit 1 GPU.
- **Gotchas:** First launch OOM'd at batch 128 on the A100 (poll.log captured nvidia-smi at 79.1 GB); dropped to 64, relaunched as a debug-child within max_debug_depth.
- **Result:** balanced_acc=0.731 (primary), auroc=0.804, n_test=412. Verifier verdict: PROMOTE-WITH-CAVEAT.
- **Confound-audit:** positive → /confound-audit dispatched; label-permutation null centered at 0.502, Survives: YES.
- **Rigor debt:** RIGOR_DEBT(due:2026-06-30): only 1 of 3 prereg seeds run so far; CI is single-seed. Run seeds 2024 & 7 before brief.
- **Follow-up:** child node N-3a to complete the seed sweep; then /analyze for the 95% CI (confirmatory needs N≥3).
```
