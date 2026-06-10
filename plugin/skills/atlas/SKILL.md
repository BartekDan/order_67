---
name: atlas
description: Regenerate the project-level ATLAS — a single control surface that shows the WHOLE exploration in one place: a you-are-here pointer, the exploration TREE (every path including dead-ends and backtracks, each with its `why`), a status table, the method battery, the parking lot, and a drift check. Generated from the hand-curated ledger experiments/_atlas/atlas.yaml by skills/atlas/atlas.py into experiments/_atlas/STATUS.md + ATLAS.html. The research-harness analog of order-66 /atlas. Unlike /drift (consolidation pass) it is a fast deterministic render and deliberately shows in-flight + abandoned state.
whenToUse: Invoked when the user is lost about overall project state or wants the cross-experiment map — NOT a single experiment. Triggered by "/atlas", "where are we", "what's the project status", "show the roadmap/map/board", "regenerate the atlas", "what's left", "what did we try and drop", or at the end of a working session and whenever a path is started, blocked, dead-ended, superseded, deferred, or backtracked. Prefer this over reading experiment.json files one by one when the question is "what does this whole project consist of and what's live right now".
isEnabled: test -d experiments
---

# /atlas — the single project control surface

## Static

### Summary
The ATLAS is how the human keeps control of a branching research project in **one place** — every path, including
the ones we abandoned and *why*, so backtracking never loses information. It is generated, never hand-kept.

- **Source of truth:** `experiments/_atlas/atlas.yaml` — a hand-curated ledger. Edit this.
- **Generator:** `${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py` (PyYAML required).
- **Outputs (generated — never hand-edit):** `experiments/_atlas/STATUS.md` (the board) and
  `experiments/_atlas/ATLAS.html` (a self-contained styled one-pager).

### The ledger schema (`experiments/_atlas/atlas.yaml`)
```yaml
project: "<name>"
regime: "<optional one-liner>"          # optional
you_are_here: {node: <id>, summary: <...>, blocker: <...>, next: <...}   # optional
nodes:                                    # REQUIRED — the exploration tree
  - id: <unique-id>                       # experiment dirs use their dir name (EXP-...)
    kind: experiment|step|method|decision|dead-end|idea
    lifecycle: done|active|blocked|dead-end|superseded|deferred|not-built|idea
    parent: <id|null>                     # builds the tree
    verdict: "<one line — the result/decision>"
    why: "<REQUIRED for dead-end/superseded/backtracked: the lesson kept>"
    next: "<optional>"
    links: {<label>: <path>}              # optional
battery: [...]        # optional: reusable method modules + state
cross_cutting: [...]  # optional: frozen truths that bind every node
parking_lot: [...]    # optional: real ideas/tasks not started
infra: {...}          # optional: environment / current blocker
archived: {...}       # optional: off-board scope (e.g. a frozen prior regime) + carried lessons
```
Only `project` + `nodes` are required; every other section renders if present, skips if absent.

### Lifecycle glyphs
✅ done · ▶ active · ⛔ blocked · ✗ dead-end · ⊘ superseded · ⏸ deferred · ◻ not built · 💡 idea

### Output format
Writes the two files under `experiments/_atlas/`, then emits a `## AtlasReport` block (counts + you-are-here +
drift). Heading is exactly `## AtlasReport` so it is greppable.

### Hard constraints
- **Dead-ends and backtracks are FIRST-CLASS.** Never delete an abandoned path from the ledger — set its
  `lifecycle` to `dead-end`/`superseded`/`deferred` and write a one-line `why:`. Losing that history is the
  exact failure this skill exists to prevent.
- **Never hand-edit the generated files** (`STATUS.md`, `ATLAS.html`). Edit `atlas.yaml` and regenerate; a re-run
  overwrites them.
- **Resolve drift immediately.** The AtlasReport flags any `experiments/EXP-*` dir with no ledger node (a path
  off the board) and any started experiment node whose dir is gone. A board that silently omits a path lies — fix it.
- **Skip leading-underscore dirs** (`experiments/_atlas`, `experiments/_global`) as experiments; they are infra.
- **Scope is the human's call.** If a prior regime / line of work is declared off-board, keep it only as the
  `archived:` pointer + carried lessons — never render its detail or mix its numbers onto the live board.

### Common mistakes (avoid)
1. Hand-editing `STATUS.md`/`ATLAS.html` instead of the ledger (they are overwritten on the next run).
2. Deleting a failed experiment's node "to clean up" — that destroys the backtrack record; mark it `dead-end` + `why`.
3. Ignoring a drift warning — if a real `EXP-*` dir isn't in the ledger, the board is lying; add the node.

## Dynamic

`experiments/` exists when this fires. Steps:

1. **If project state changed, update the ledger first** — `experiments/_atlas/atlas.yaml`:
   - move `you_are_here` (node + summary + blocker + next);
   - update the affected node's `lifecycle` / `verdict` / `next`;
   - a path abandoned/backtracked → set `lifecycle: dead-end|superseded|deferred` + a `why:` (do NOT delete it);
   - a new idea → add a node with `lifecycle: idea`;
   - keep `battery:` / `parking_lot:` current.
2. **Regenerate** (run against the current project):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py" "${CLAUDE_PROJECT_DIR}"
   ```
   (PyYAML must be importable by that python. If absent: `pip install pyyaml`.)
3. **Report** the printed `## AtlasReport` (counts + you-are-here + any drift) to the user. If drift is flagged,
   add/fix the node in the ledger and re-run before finishing.
