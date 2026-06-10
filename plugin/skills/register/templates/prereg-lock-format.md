# prereg.lock format — what gets hashed and how

`experiments/<exp>/prereg.lock` is the tamper-evident freeze of the analysis plan. It implements
RULE-5 (pre-register, then honor it): the `{primary_metric, splits, analysis_plan}` triple is
committed to a sha256 *before any result exists*. At `confirmatory`+ a later deviation from this
lock HARD-BLOCKS PROMOTE (re-register via `--amend` or down-tier); at `exploratory` deviation is
free but flagged.

The `Prereg-hash` field in the `## Preregistration` block is the sha256 of this file's **canonical
body** (everything between the `--- BEGIN PREREG BODY ---` and `--- END PREREG BODY ---` markers,
inclusive of neither marker). Hashing a canonical, deterministic serialization — not the whole file
with its human-readable preamble — is what makes the hash reproducible across machines and
re-derivable by the verifier.

---

## File layout

```
# prereg.lock — EXP-<slug>  (DO NOT EDIT; append-only via /register --amend)
# Human preamble (NOT hashed): tier, who, why. Free text above the BEGIN marker.
rigor_tier: <exploratory|pilot|confirmatory|publication>
git_commit: <short sha or 'no-git'>        # lightweight repro pin (D-004: per-run repro capture)
supersedes: <prior 64-hex hash or 'none'>  # set by --amend; 'none' on first registration

--- BEGIN PREREG BODY ---
timestamp_iso: <YYYY-MM-DDThh:mm:ssZ>
primary_metric: <single pre-declared metric; exactly one>
splits: <split definition, keyed by the unit of scientific interest, never by row>
analysis_plan: |
  <verbatim frozen plan>
--- END PREREG BODY ---

# Below the END marker (NOT hashed): the computed hash, recorded for human convenience.
prereg_sha256: <64-hex>
```

Only the four keys inside the body — `timestamp_iso`, `primary_metric`, `splits`, `analysis_plan` —
are hashed. The preamble, the `prereg_sha256` echo, and any comments are outside the body and do not
affect the hash (so fixing a typo in the human preamble does not invalidate a committed plan, while
changing the *plan itself* necessarily changes the hash — that is the tamper-evidence).

---

## Canonical serialization (so the hash is reproducible)

Before hashing, the body is normalized so two registrations of the same plan on two machines produce
the same digest:

1. Keys appear in fixed order: `timestamp_iso`, `primary_metric`, `splits`, `analysis_plan`.
2. Line endings are LF (`\n`), no trailing whitespace on any line, exactly one trailing newline.
3. `analysis_plan` is a literal block scalar (`|`); its content is verbatim (preserves the user's
   wording — the point is to freeze *their* plan, not a paraphrase).
4. No tabs; two-space indentation inside the block scalar.

The hash is then:

```sh
# hash the canonical body only (between, exclusive of, the BEGIN/END markers)
sed -n '/^--- BEGIN PREREG BODY ---$/,/^--- END PREREG BODY ---$/p' experiments/${EXP}/prereg.lock \
  | sed '1d;$d' \
  | sha256sum | cut -d' ' -f1
```

(Pure POSIX `sed` + `sha256sum`; no `jq` — hooks and the verifier may run on a box without it,
RULE-2.) The `/register` Dynamic section computes this and writes it both into `prereg_sha256` and
into `experiment.json:prereg_hash`, and reports it as `Prereg-hash` in the `## Preregistration`
block. All three MUST be identical.

---

## Tier conditionality

| Tier | Lock requirement |
|------|------------------|
| `exploratory` | `prereg.lock` is OPTIONAL. If omitted, report `Prereg-hash: n/a (exploratory)`. Do not fabricate a lock to populate the field. |
| `pilot` | `primary_metric` and `splits` MUST be real (split keyed by unit of interest, RULE-10); `analysis_plan` MAY be brief. |
| `confirmatory` | ALL three body keys frozen and non-empty; `analysis_plan` MUST name the estimator, the CI method + variation source (seed/init/split), and the multiple-comparison correction (Holm or BH) + comparison count (RULE-3, RULE-7). `experiment.json:prereg_hash` is REQUIRED. |
| `publication` | + the plan references the datasheet/model-card and the NeurIPS items 4–8 it will evidence. |

A missing `prereg_hash` where the tier requires it ⇒ treat as `publication` and surface a blocking
gap (RULE-0). Never silently proceed without the lock at confirmatory+.

---

## Amendment (`--amend`) and deviation

Re-registration never overwrites a committed lock. `/register --amend`:

1. reads the existing `prereg_sha256`, copies it into the new lock's `supersedes:` field,
2. writes the new body (new `timestamp_iso`, changed metric/splits/plan),
3. recomputes the hash,
4. records a one-line deviation note in `hypothesis.md` (and bumps `experiment.json:version`).

Downstream, at `confirmatory`+, a `supersedes != none` lock means the analysis plan changed after
the original freeze: PROMOTE is HARD-BLOCKED until the results-verifier explicitly re-clears the
deviation (or the experiment is down-tiered to `exploratory`, where deviation is free-but-flagged).
This is the mechanism that makes "we changed the metric after seeing the data" impossible to hide.
