# spectral-length-bias (order-67 acceptance fixture) — ATLAS

_Regime synthetic re-enactment of the proteus Eksperyment-1 self-retraction — proves the confound-audit gate_

**Generated 2026-06-10 17:09 UTC · commit 3369f61 2026-06-10 · source `experiments/_atlas/atlas.yaml` (edit that, then `/atlas`).**

> ⚠️ GENERATED FILE — do not hand-edit. Edit `atlas.yaml` and regenerate.

## ▶ YOU ARE HERE
- **Node:** `EXP-spectral-length-bias`
- **State:** C-001 RETRACTED at confirmatory tier — confound-audit Survives: NO (answer-length confound); the fixture is complete and frozen as the worked example.
- **→ Next:** (if this were live) re-register a length-robust hypothesis: PRIMARY metric = length-controlled balanced accuracy, new prereg_hash (verdict.md Required fixes)

## The exploration tree
Glyphs: ✅ done · ▶ active · ⛔ blocked · ✗ dead-end · ⊘ superseded · ⏸ deferred · ◻ not built · 💡 idea

```
✗ EXP-spectral-length-bias — REJECT / retracted — held-out bal-acc 0.71 was an answer-length confound (feature~length ρ=0.79); length-regressed bal-acc 0.53, CI [0.49,0.57] ≋ chance. The 'hallucination detector' detected answer length.
    why: Probe-1 permutation-null PASSED (z=6.2) — the classifier predicts SOMETHING; probes 2–4 (nuisance screen, statistic-swap, alt-preprocessing) all FAILED — it predicts LENGTH. Lesson kept: a permutation PASS is necessary, never sufficient; pre-name the nuisance variables and gate every positive on the four-probe audit (RULE-6). /data-audit passing while /confound-audit fails is the exact distinction this fixture exists to teach.
```

## Status table
| Node | Kind | State | Verdict | Next |
|---|---|---|---|---|
| `EXP-spectral-length-bias` | experiment | ✗ dead-end | REJECT / retracted — held-out bal-acc 0.71 was an answer-length confound (feature~length ρ=0.79); length-regressed bal-acc 0.53, CI [0.49,0.57] ≋ chance. The 'hallucination detector' detected answer length. |  |

## Cross-cutting truths (frozen — don't re-litigate)
- fixture: true on every artifact — excluded from real findings; no human sign-off
- qid-disjoint split is CLEAN (data-audit PASS) — the failure is a VALIDITY confound, not leakage

## 🔎 Drift check
- ✅ ledger and experiment dirs agree.
