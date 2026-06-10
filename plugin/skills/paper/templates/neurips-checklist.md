# NeurIPS 16-item checklist (order-67 /paper self-audit)

`/paper` auto-runs this as a self-audit and renders the filled result to
`results/<exp>/paper/neurips-checklist.md`. Each item is answered **Yes / No / NA** with a
one-line **justification**. For most items, `No` or `NA` is acceptable *if honestly justified* —
this is a self-audit, not a self-grade (RULE-1; the science was already graded by the
`results-verifier`'s `## Verdict`).

> **Ship-blocking items 4–8.** Items 4, 5, 6, 7, 8 MUST be **Yes-with-evidence** — the
> justification must carry a concrete pointer into the paper (a §/Eq./figure) or into the
> `## ReproReport`. If any of 4–8 is `No`, `NA`, or `Yes` without an evidence pointer, the paper is
> **GATED**: `/paper` still writes the four files but sets the `## PaperReport` `Checklist` field to
> `GATED` and lists the failing item in `Open-gaps`. Do NOT fabricate evidence to clear a gate.

Answer format per item:
```
N. <item> — [Yes|No|NA] — <justification; for 4–8 include the evidence pointer>
```

---

1. **Claims scope.** Do the abstract and intro accurately reflect the contributions and scope,
   including what is confirmatory vs exploratory (RULE-5)? — [ ] — `<…>`
2. **Limitations stated.** Are limitations discussed, with the confirmatory/exploratory split? — [ ] — `<…>`
3. **Societal impact.** Is the broader/dual-use impact addressed (or justified NA)? — [ ] — `<…>`

4. **(SHIP-BLOCKING) Claims match results.** Does every main claim map to a Results subsection led
   by its headline stat, with effect size + test statistic + p + n + correction (RULE-7/3)? —
   [ ] — `<evidence: §4.x, Eq. n; from ## AnalysisReport>`
5. **(SHIP-BLOCKING) Limitations are honest.** Are the confirmatory limitations and the exploratory
   findings (incl. every prereg deviation, RULE-5) stated, not buried? —
   [ ] — `<evidence: §5.1 / §5.2>`
6. **(SHIP-BLOCKING) Theory/assumptions.** Are all modelling assumptions and statistical
   assumptions (test choice, CI method, variation source, distribution scope RULE-9) stated and
   checked, including the confound-audit thresholds frozen first (RULE-6)? —
   [ ] — `<evidence: §3 Methods; ## ConfoundAudit header>`
7. **(SHIP-BLOCKING) Experimental reproducibility — protocol.** Are data (with content-hash),
   split (qid-level, RULE-10), seeds, and full config disclosed sufficiently to reproduce the main
   results? — [ ] — `<evidence: ## ReproReport Config-snapshot / Seed-recorded; experiment.json dataset_refs[].hash>`
8. **(SHIP-BLOCKING) Experimental reproducibility — environment.** Is the environment pinned
   (env/lockfile, git commit) and the code/artifact access stated? —
   [ ] — `<evidence: ## ReproReport Env-pinned; NeurIPS-4-8 line>`

9. **Training details.** Are optimizer, hyperparameters, and compute-per-run disclosed (or NA for a
   probing-only / analysis-only study)? — [ ] — `<…>`
10. **Error bars / variation.** Does every quantitative result carry a CI/std with a named variation
    source and CI method (RULE-7)? — [ ] — `<…>`
11. **Baselines.** Are the baselines the effect size is measured against named and fair? — [ ] — `<…>`
12. **Statistical significance + correction.** Is the multiple-comparison correction declared and
    the number of comparisons reported (RULE-3)? — [ ] — `<…>`
13. **Datasets — licensing/provenance.** Are dataset source, license, and consent/PII status
    stated (datasheet pointer at publication tier)? — [ ] — `<…>`
14. **Assets/code release.** Is the code/asset release plan stated, with versions? — [ ] — `<…>`
15. **Compute resources.** Are the GPU/$/wallclock resources for the full experiment tree reported
    (from `experiment.json` `compute.budget` + actual `## RunReport` totals)? — [ ] — `<…>`
16. **Reproducibility statement.** Is there a single statement pointing to the seed + full config +
    git commit + env/lockfile + dataset content-hash record (the lightweight repro capture)? —
    [ ] — `<…>`

---

**Tally line** (rendered at the bottom of `neurips-checklist.md`, and parsed into the
`## PaperReport` `Checklist` field):
```
Overall: <n>/16 Yes · items 4-8: <m>/5 Yes-with-evidence · status: PASS|GATED · venue: <venue>
```
`status: GATED` whenever any of items 4–8 is not Yes-with-evidence. `GATED` describes a held
manuscript — it is NOT a verdict on the underlying science (that is the verifier's job, RULE-1).
