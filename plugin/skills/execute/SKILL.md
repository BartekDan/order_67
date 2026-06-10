---
name: execute
description: The core run loop. Per experiment-tree node, read the tier and prior Run Notes, set [~], clear the /conflicts + /data-audit preconditions, dispatch the run on the REMOTE GPU host (owns scp→launch→poll→fetch via experiments/<exp>/host-config.json), capture the lightweight repro bundle into runs/<RUN-NNN>/, spawn the independent results-verifier BEFORE recording any claim (RULE-1), auto-dispatch /confound-audit on positives (RULE-6), map the verdict to a node status, and expand the tree autonomously only while under the declared budget. Returns a ## RunReport block per run.
whenToUse: Invoked once experiments/<exp>/runs.md exists and the orchestrator (or user) wants to advance an experiment. Triggered by "execute the experiment", "run /execute <exp>", "do node <node-id>", or by the autonomous loop after /plan-runs. Do NOT fire if runs.md or host-config.json is missing — refuse with the RR-061 message.
isEnabled: test -d experiments
---

# /execute

## Static

### Summary
Per-node loop over the best-first experiment tree in `experiments/<exp>/runs.md`. For each node:
resolve the effective `rigor_tier` (node `_Tier:_` override → `experiment.json` → **publication if missing, RULE-0**) →
read prior `## Run Notes` (RR-020) → set status `[~]` → clear the `/conflicts` + `/data-audit` preconditions
and hard-lint every upstream block it will consume → dispatch the run **within `_Owns:_`** on the remote GPU
host (the harness owns `scp`→launch→`ssh`-poll→`scp`-fetch via `experiments/<exp>/host-config.json`, D-002) →
write the lightweight repro bundle into `runs/<RUN-NNN>/` → append `path:value` provenance to the trace →
spawn the **independent `results-verifier`** on a fresh context BEFORE recording any claim (RULE-1) → on a
POSITIVE finding, auto-dispatch `/confound-audit` (RULE-6) before promotion → map the `## Verdict` to a node
status → expand the tree autonomously **only while under the declared budget** and halt at the cap. Idempotent:
nodes whose newest run is already `status: ok` and verified are skipped. Quicklook checkpoints snapshot
metrics+figure non-blocking.

### Preconditions
- `experiments/<exp>/runs.md` exists with at least one node (RR-061; emitted by `/plan-runs` as the `## RunPlan` block source).
- `experiments/<exp>/experiment.json` exists and is readable (for the default `rigor_tier`, `compute.budget`, `quicklook`, `seed_policy`).
- `experiments/<exp>/host-config.json` exists (gitignored; see `templates/host-config.example.json`). The harness dispatches runs only on the remote host described there.
- `agents/results-verifier/AGENT.md` exists (the verifier is mandatory and write-disabled).
- `experiments/<exp>/prereg.lock` exists when the effective tier is `confirmatory` or `publication` (RULE-5 / RULE-0; its absence at those tiers is itself a blocking issue).

If `runs.md` is missing: refuse with `"No run plan found for <exp>. Run /plan-runs first."` (RR-061).
If `host-config.json` is missing: refuse with `"No host-config.json for <exp>. Copy templates/host-config.example.json to experiments/<exp>/host-config.json (and gitignore it) before /execute can dispatch a remote run."` (RR-062). Do NOT fall back to a local run — a local fallback silently changes the hardware, the data mount, and the cost accounting, which corrupts every downstream comparison.

### Parameters
- `exp` — required. Experiment ID (`EXP-<slug>`).
- `node_id` — optional. A specific node from `runs.md`. If omitted, pick the first `[ ]` pending node whose `_Depends:_` are all `[x]` and that fits the remaining budget (best-first by the priority `/plan-runs` recorded).
- `dry_run` — optional. Resolve config + render the launch command + check budget/preconditions, but do NOT `scp`/launch on the remote. Used to estimate cost before spending it.

### Output format
One `## RunReport` RETURN FORMAT block per run dispatched (CONVENTIONS.md §4). The heading and every
`- <Field>:` key MUST match `hooks/block-schemas.tsv` verbatim or `block-lint.sh` rejects it. Write the
block into `experiments/<exp>/runs/<RUN-NNN>/run-report.md` (so the trace hook and downstream skills can
read it) and surface it in the skill output:

```
## RunReport
- Run: RUN-007
- Node: N-3 spectral-length-bias / seed-sweep
- Status: ok                      # ok | error | timeout | budget-halt | precondition-fail
- Metrics: balanced_acc=0.731, auroc=0.804, n_test=412   # the node's primary + declared secondaries, from the fetched metrics.json
- Seed: 1337
- Artifacts: runs/RUN-007/ (config.resolved.json, env.lock, dataset.hash, git.commit, metrics.json, run.log); results/EXP-spectral-length-bias/RUN-007/figures/quicklook.png
- Trace: trace/EXP-spectral-length-bias.md#RUN-007
```

`Status` enum is mechanical: `ok` (run completed, metrics fetched), `error` (non-zero remote exit /
crashed), `timeout` (exceeded the node wallclock and was not fetched), `budget-halt` (the node would
exceed `compute.budget` so it was never launched), `precondition-fail` (a `/conflicts` BLOCKER, a
`/data-audit` FAIL, or a `block-lint` failure stopped dispatch before any GPU was touched). `Metrics`
carries the actual logged values, never an estimate; if the primary metric was never logged the run is
`status: ok` but the *claim* is `BLOCKED` by the verifier (CONVENTIONS.md §4: never score an unobservable
metric). `Node` echoes the node id + its short label so the report is readable standalone.

The node line in `runs.md` is then updated to the status the verifier's verdict maps to (see Hard
constraints). For a `PROMOTE-WITH-CAVEAT` node, a `RIGOR_DEBT(due:YYYY-MM-DD):` marker is appended to the
node's `## Run Notes` describing the caveat and its remediation deadline (greppable per CONVENTIONS.md §1).

### Hard constraints
- **Resolve the tier, fail loud if absent (RULE-0).** Effective tier = node `_Tier:_` override else `experiment.json:rigor_tier`. A missing/unknown tier ⇒ treat as **`publication` (strictest)** AND surface it as a blocking issue in the `## RunReport` — never silently proceed as if exploratory. Tiers NEST: never impose a higher tier's checks on a lower-tier node (e.g. do not demand N≥k seeds or a confound-audit on an `exploratory` node — that re-creates the bloat the tier system exists to prevent).
- **Preconditions are HARD and run before any GPU is touched.** In order: (1) `/conflicts <exp>` → read the `## Conflicts` block; a `Verdict: BLOCKER` halts the node `[!]` with `status: precondition-fail`. (2) `/data-audit <exp>` (or read its current `## DataAudit` block) → a `Verdict: FAIL` (leakage / committed secret / L1–L3 failure) halts `[!]`. (3) Before consuming ANY upstream block (`## RunPlan`, `## DataAudit`, `## Preregistration`, a `_Depends:_` node's `## RunReport`), HARD-call `bash ${CLAUDE_PLUGIN_ROOT}/hooks/block-lint.sh <upstream file>` and abort the node on a non-zero exit. A silent field-drift in an upstream block must never waste an expensive GPU run — that is the entire reason block-lint is a hard precondition and not only the advisory PostToolUse hook.
- **The harness owns the remote loop; runs go to the remote host, never locally (D-002).** Read `experiments/<exp>/host-config.json`. `scp` only the run script + the resolved config to `{remote.workdir}/{exp}`. Launch via the `launch.cmd_template` (substituting `{python} {script} {seed} {config} {logfile}`). Poll over SSH at `poll.interval_sec` using `poll.alive_check` (pgrep), `poll.gpu_check` (nvidia-smi), `poll.disk_check` (df); back off to a longer interval for long runs to stay under the cache TTL. On completion, `scp` back ONLY `fetch.result_globs` into `fetch.dest` — the reduced artifacts (metrics, logs, reduced `.npz`, figures). **Never fetch the raw tensors** (the multi-TB activations stay remote; two-tier data access). Credentials are passed by NAME via `remote.env_passthrough` / `auth.key_env`, never read from or written into any file (RULE-2, secret-scan).
- **Write only inside `_Owns:_` (the data contract).** A run may write only within the node's declared `_Owns:_` paths/datasets/configs. A write outside it — especially to a frozen baseline, a held-out/test split, or another node's `runs/` — is a hard `REJECT` and halts the node `[!]`. This is the leakage/contamination guard (RULE-10) at execution time.
- **Capture the lightweight repro bundle per run, into `runs/<RUN-NNN>/`** (D-004, repro-capture is lightweight): the **seed**, the **full resolved config** (`config.resolved.json` — every default expanded, nothing implicit), the **git commit** of the run script (`git.commit`), the **env/lockfile** (`env.lock` — interpreter + pinned deps from the remote venv), and the **dataset content-hash** (`dataset.hash`, matching `experiment.json:dataset_refs[].hash`). See `templates/run-manifest.md` for the exact layout. A missing seed/config/commit/hash at `confirmatory+` is a blocking issue (RULE-0).
- **Append `path:value` provenance to `trace/<exp>.md`** for every run: the run id, the resolved config path, and the primary-metric value. The PostToolUse `update-trace.sh` hook also fires on writes under `experiments/<exp>/` and `results/<exp>/`; `/execute` still appends its own `RUN-NNN` anchor line so the `## RunReport`'s `Trace` field resolves.
- **Spawn the independent verifier BEFORE recording any claim (RULE-1, never-self-grade).** `/execute` produces the result; it does NOT grade it. Spawn `results-verifier` on a fresh, write-disabled context with the adversarial prompt, passing `{exp, node_id, run_id, tier, _Owns:_, the resolved config, the fetched metrics.json, the trace anchor}`. The verifier emits a `## Verdict` block. `/execute` reads, never authors, that verdict.
- **Confound-audit every positive BEFORE promotion — tier-graded (RULE-6).** If the run is a POSITIVE finding (the primary metric clears the pre-registered threshold in the direction the hypothesis predicted), the gate depends on the effective tier. At **exploratory** a positive is FLAGGED, not audited (no confound-audit required — advisory/flag-only). At **pilot** a positive triggers a MANDATORY `/confound-audit <exp> <run_id>` label-permutation-null probe (the cheapest single probe, at the exploratory K floor) that MUST PASS before PROMOTE — pilot gates expensive confirmatory spend, so the Eksperyment-1 length-confound is screened here; `/execute` MUST NOT PROMOTE a pilot positive without the permutation-null probe passing. At **confirmatory+** the FULL four-probe screen (permutation-null + nuisance-screen + statistic-swap + alt-preprocessing) is MANDATORY and `Survives: YES` is required to PROMOTE. In every audited case read the `## ConfoundAudit` block: a non-surviving probe (pilot permutation-null FAIL, or confirmatory+ `Survives: NO`) ⇒ the finding is retracted: status `[!]`, `status: error` is NOT used (the run was fine; the *claim* failed) — record a `## RunReport` with `Status: ok` and let the verifier issue `REJECT`.
- **Verdict→status map (mechanical):** `PROMOTE` → node `[x]`. `PROMOTE-WITH-CAVEAT` → node `[x]` AND append a `RIGOR_DEBT(due:YYYY-MM-DD):` marker to the node's `## Run Notes`. `RERUN` / `REJECT` / `BLOCKED` → node `[!]`, halt this node, surface the verdict's `Required fixes` verbatim. `BLOCKED` ≠ `REJECT`: BLOCKED means the metric was never logged (unscorable); REJECT means it was logged and does not support the claim. Do NOT proceed to expand children of a halted node except a bounded debug-child (below).
- **Prereg deviation HARD-BLOCKS PROMOTE at `confirmatory`/`publication` (RULE-5).** If the resolved config/analysis deviates from `prereg.lock` (different primary metric, split, or analysis plan than the hashed prereg), the verifier MUST NOT issue `PROMOTE` at those tiers — the node either re-registers (a new `prereg_hash`) or down-tiers. At `exploratory`/`pilot` a deviation is free but flagged in `## Run Notes`.
- **Autonomous tree expansion is budget-bounded (D-003).** Before launching any node, check the running totals (GPU-hours, USD, wallclock) against `experiment.json:compute.budget`. If launching the node would exceed any cap, do NOT launch it: record `Status: budget-halt`, leave the node `[ ]`, stop autonomous expansion, and report the spend vs cap. The cap is a hard stop, not a target.
- **Buggy nodes may spawn bounded debug-children.** A `[!]` node whose halt is a fixable run-time bug (not a leakage/secret/contradiction BLOCKER) may spawn a child node at depth ≤ `max_debug_depth` (from `runs.md` / `experiment.json`) carrying the same `_Owns:_`. Exceeding `max_debug_depth` halts and reports — no unbounded debug recursion.
- **Idempotent skip-existing.** Skip any node whose newest run has `status: ok` AND a recorded verifier verdict (`[x]` or `[!]`). Re-running it would burn GPU for no new information. Re-execution requires an explicit `node_id` (or a new debug-child).
- **Quicklook checkpoints are non-blocking.** At the `experiment.json:quicklook` checkpoint (notebook/figure/metric), snapshot the current metrics + the quicklook figure into `runs/<RUN-NNN>/quicklook/` and continue. Never poll for user approval — the value is continuous visibility, mirrored from order-66's clickable checkpoints.
- **No absolute paths (RULE-2).** Everything resolves via `${CLAUDE_PLUGIN_ROOT}` (plugin) and `${CLAUDE_PROJECT_DIR}` (project / `experiments/`). Remote paths come only from `host-config.json`.

### Common mistakes (avoid)
1. **Self-grading the run.** `/execute` produced the numbers, so it is the LAST agent that should judge them. Always spawn the independent `results-verifier` and read its `## Verdict` — never write your own verdict or "interpret" the metrics into a PROMOTE. This is the harness's central integrity guarantee (RULE-1); skipping it makes every claim unfalsifiable.
2. **Consuming an upstream block without block-linting it first.** The advisory PostToolUse hook only nudges at write-time; before *this* run reads a `## RunPlan` / `## DataAudit` / `## Preregistration` / a dependency's `## RunReport`, hard-call `block-lint.sh <file>` and abort on failure. A drifted field discovered only after a 6-GPU-hour run is the exact waste this precondition prevents.
3. **Falling back to a local run when `host-config.json` is missing or the host is unreachable.** Refuse instead. A local fallback silently swaps hardware, data mount, and cost accounting and contaminates every cross-run comparison. The harness OWNS the remote loop; if it can't reach the host, it halts and reports.
4. **Fetching the raw tensors.** Only `fetch.result_globs` (reduced metrics/logs/`.npz`/figures) come back into the repo. Pulling the multi-TB activations defeats the two-tier data access and floods the repo. The raw data stays remote by design.
5. **Imposing a higher tier's gates on a lower-tier node.** Demanding N≥k seeds, a 95% CI, an FDR correction, or a mandatory confound-audit on an `exploratory` node is the bloat the tier ladder exists to prevent. Apply exactly the effective tier's cumulative checks — no more (tiers nest upward only). The inverse — silently treating a `confirmatory` node as exploratory — is caught by RULE-0 (missing tier ⇒ publication-strict).
6. **Treating `budget-halt` as a failure to debug.** Hitting the GPU/$/wallclock cap is the autonomous loop working as designed: stop, record the spend vs cap, report. Do NOT raise the cap yourself or keep launching — the cap is the user's, not the harness's, to lift.
7. **Writing outside `_Owns:_` "to fix up a baseline" or "to cache a split".** The `_Owns:_` set is the data contract; a write outside it (frozen baseline, test split, sibling node's `runs/`) is a hard REJECT and a leakage risk (RULE-10). Escalate to the user; never silently widen the contract.
8. **Recording a positive finding before the confound-audit returns at `confirmatory+`.** A positive that has not cleared the permutation-null / nuisance-screen / statistic-swap / alt-preprocessing audit is not yet a finding (RULE-6). Auto-dispatch `/confound-audit` and gate PROMOTE on `Survives: YES`; a non-surviving positive is retracted, not quietly kept.
9. **Scoring an unobservable metric as success.** If the primary metric was never logged, the run can be `Status: ok` but the claim is `BLOCKED`, not PROMOTE and not REJECT. BLOCKED ≠ REJECT (CONVENTIONS.md §4). Never invent a value or read a proxy in its place.
10. **Skipping prior `## Run Notes` before launching a node.** Sibling and ancestor nodes record what config, seed, and gotcha already burned a run. Re-litigating a decision a prior node already settled wastes GPU. Read all prior `## Run Notes` for the experiment first (RR-020).

## Dynamic

Templates: `${CLAUDE_PLUGIN_ROOT}/skills/execute/templates/run-manifest.md` defines the per-run
`runs/<RUN-NNN>/` layout and the exact repro-bundle contents — author each run's bundle to match it.

`experiments/<exp>/runs.md`, `experiments/<exp>/experiment.json`, `experiments/<exp>/host-config.json`,
`trace/`, `results/`, and `sessions/` already exist when this skill fires — write to them directly. Create
`experiments/<exp>/runs/<RUN-NNN>/` and `results/<exp>/<RUN-NNN>/` with `mkdir -p` on first write of a run.

Tree + tier context for the current `<exp>` (read before picking a node):

- Run plan / node tree (status, `_Owns:_`, `_Depends:_`, `_Tier:_`, `(P)`):
  !{sed -n '1,200p' "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/runs.md" 2>/dev/null || echo "runs.md not found — refuse (RR-061)"}
- Experiment state (default `rigor_tier`, `compute.budget`, `quicklook`, `seed_policy`, `dataset_refs[].hash`):
  !{sed -n '1,120p' "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/experiment.json" 2>/dev/null || echo "experiment.json not found — RULE-0: treat as publication and flag"}
- Remote host config (the scp→launch→poll→fetch contract; never echo credentials — they are env names):
  !{sed -n '1,60p' "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/host-config.json" 2>/dev/null || echo "host-config.json not found — refuse (RR-062); do NOT run locally"}
- Existing runs (for idempotent skip-existing — a node whose newest run is `status: ok` + verified is skipped):
  !{ls -1 "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/runs/" 2>/dev/null || echo "(no runs yet)"}
- Prereg lock (required at confirmatory+; a deviation HARD-BLOCKS PROMOTE per RULE-5):
  !{test -f "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/prereg.lock" && echo "prereg.lock present" || echo "prereg.lock ABSENT — blocking at confirmatory/publication (RULE-0/RULE-5)"}

Hard precondition lint of an upstream block before this run consumes it (abort the node on non-zero exit):
  !{bash ${CLAUDE_PLUGIN_ROOT}/hooks/block-lint.sh "${CLAUDE_PROJECT_DIR}/experiments/${EXP}/runs.md" 2>&1 || echo "BLOCK-LINT FAIL — do not dispatch"}

Repro-bundle helpers (run on the remote via the SSH channel from `host-config.json`, captured into the
bundle — these are illustrative; the actual values are written by the run, not by the skill body):
  - git commit of the run script:  `git -C {workdir}/{exp} rev-parse HEAD`
  - env/lockfile from the remote venv:  `{python} -m pip freeze`
  - dataset content-hash (must match `experiment.json:dataset_refs[].hash`):  recorded in `runs/<RUN-NNN>/dataset.hash`

Today's metric file: `sessions/metrics-$(date +%Y-%m-%d).jsonl`. Create on first append (touch then `>>`);
never read before write. Every line carries `{"skill":"execute","exp":"<exp>","node":"<node_id>","run":"<RUN-NNN>","tier":"<effective tier>", ...}` plus timing/tokens, the verdict, and on a halt a `"halt_reason"` (`precondition_blocker` | `data_audit_fail` | `block_lint_fail` | `owns_violation` | `budget_halt` | `verifier_rerun` | `verifier_reject` | `verifier_blocked` | `confound_failed` | `debug_depth_exceeded`).
