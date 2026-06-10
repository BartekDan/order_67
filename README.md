# order-67 Research Harness · *Proteus Harness*

A **rigor-aware, spec-driven harness for conducting AI/ML research** — the research-world sibling
of the `order-66-sdd-harness` plugin.
Where order-66 turns a work request into shipped software, order-67 turns a research question into
a **defensible scientific claim** plus the two artifacts that communicate it: a paper-grade write-up
and a layman R&D-management brief.

It is built to run against real mechanistic-interpretability work (e.g. `proteus-h-neurons`), where
data and compute live on a remote SSH/GPU host and only code + write-ups are versioned locally.

> 📖 **New here? Start with the friendly, illustrated walkthrough:** [`docs/user-guide.html`](docs/user-guide.html)
> — what the harness is, how a finding gets established, the four rigor tiers, every skill in one
> line, and the worked spectral-length-bias example. (Open it in a browser.)

## The one idea

> **Mode → rigor tier.** order-66's load-bearing `mode` enum (spike→clickable→mvp→production)
> becomes a `rigor_tier` enum (**exploratory → pilot → confirmatory → publication**) carried in
> `experiment.json`. It cumulatively tightens every downstream gate; a missing tier fails *loud*
> to publication-strict. The atomic unit of work is an **experiment** (≈ a slice) governed by a
> **falsifiable hypothesis** (≈ an EARS requirement).

## The pipeline

```
/triage → /register → /design-experiment → /data-audit → /plan-runs → /conflicts
        → /execute ⇄ /confound-audit → /analyze → (results-verifier) → /paper + /brief
        … /note (capture)  … /drift (consolidate + retraction sweep)
```

Three gates are non-negotiable, each reverse-engineered from how proteus caught (or missed) its own
errors:

1. **Pre-registration hash-lock** (`/register`) — freeze {hypothesis, primary metric, splits,
   analysis plan} *before* any result exists; deviation hard-blocks PROMOTE at confirmatory+.
2. **Leakage gate** (`/data-audit`) — Kapoor–Narayanan L1/L2/L3 taxonomy + qid-level split +
   leakage-safe CV + a committed-secret scan.
3. **Confound-audit on every positive (pilot+)** (`/confound-audit`) — permutation null +
   nuisance-variable screen + statistic-swap + alternative-preprocessing re-run; a finding that
   doesn't survive is retracted. (Pilot requires the permutation-null probe at minimum; the full
   four-probe screen is mandatory at confirmatory+. Exploratory positives are flagged, not audited.)

And one law: **never self-grade** — the `results-verifier` subagent (fresh context, write-disabled)
issues the `## Verdict` (PROMOTE / PROMOTE-WITH-CAVEAT / RERUN / REJECT / BLOCKED); the agent that
ran the experiment never grades its own result.

## Skills

| Skill | Returns | Purpose |
|-------|---------|---------|
| `/triage` | `## ResearchRouting` | 7-path classify a request + recommend a rigor tier |
| `/register` | `## Preregistration` | falsifiable H-cards + hash-lock the analysis plan |
| `/design-experiment` | `## DesignDraft` | quicklook-first design + Data&Compute + threats |
| `/data-audit` | `## DataAudit` | leakage taxonomy + secret scan (auto-fail on blanks) |
| `/plan-runs` | `## RunPlan` | best-first experiment tree w/ boundaries + tier-scaled seeds |
| `/conflicts` | `## Conflicts` | cross-experiment invariant scan |
| `/execute` | `## RunReport` | autonomous-within-budget remote-GPU run loop |
| `/confound-audit` | `## ConfoundAudit` | adversarial confound screen on every positive |
| `/analyze` | `## AnalysisReport` | effect size + CI + FDR + linted figures |
| `/verify-claim` | `## Verdict` | manual re-spawn of the independent verifier |
| `/paper` | `## PaperReport` | IMRaD, claims-carry-stats, NeurIPS checklist |
| `/brief` | `## BriefReport` | BLUF HTML for R&D mgmt + pushback handbook |
| `/drift` | `## DriftReport` | DREAM consolidation + retraction-citation sweep |
| `/note` | *(silent)* | non-disruptive scratchpad |

## Agents (isolated subagents)

`results-verifier` · `data-steward` · `reproducibility-checker` · `peer-reviewer` (red-team) ·
`figure-smith` · `run-reader`.

## Where things live

A project under the harness grows: `experiments/<exp>/` (the unit), `results/<exp>/`,
`trace/<exp>.md`, `FINDINGS.md`, `RIGOR_DEBT.md`, `sessions/`. See **[`docs/user-guide.html`](docs/user-guide.html)**
for the friendly walkthrough, **`plugin/CONVENTIONS.md`** for the full artifact model and the `## Block` ABI,
and **ROADMAP.md** for build status.

## Install (user scope)

This repo is a single-plugin marketplace; the installable plugin is in `plugin/`.

```
claude plugin marketplace add /path/to/order-67
claude plugin install order-67-research-harness@order-67   # --scope user is the default
```

Then restart Claude Code (or `/reload-plugins`) and the `/triage`, `/register`, … skills appear.

## Status

`v0.1.0` — scaffolding. See `ROADMAP.md`.
