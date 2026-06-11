# Diagram DSL — authoring guide (order-67 atlas v3; shared with order-66 — keep in sync)

ATLAS.md diagrams are no longer ASCII art. They are small declarative blocks that
`render_html.py` lays out deterministically as SVG (layered top-down, house palette). The
source block stays perfectly readable in the raw markdown — it IS the diagram's edge list.

## Block form

Use a fenced block whose info string is `flow` (pipelines / data-flow) or `graph`
(dependency graphs). Both use the same grammar and engine; the name documents intent.

````
```flow
node data "dataset @ sha256:..." .artifact
node run "remote GPU run\n(featurize + CV + eval)" .engine
node gates "/data-audit + /confound-audit" .engine
node claim "claim C-NNN (verdict)" .surface
edge data -> run "qid-disjoint splits"
edge run -> gates "metrics.json scalars"
edge gates -> claim "Survives + Verdict"
```
````

## Grammar (one statement per line; `#` starts a comment)

| Statement | Meaning |
|---|---|
| `group <id> "Title"` | a named cluster (an area, an environment). Drawn as a dashed panel when its members sit together; automatically falls back to per-node chips when groups interleave (cross-cutting dependency graphs). |
| `node <id> "Label" [@<group>] [.<class>]` | a box. `\n` inside the label forces a line break; long lines auto-wrap at ~26 chars. |
| `edge <a> -> <b> ["what moves"] [dashed]` | a directed arrow. The label names the DATA that moves (shape, not vibes) — same rule as the old ASCII arrows. `dashed` marks optional/degraded paths. |

Node classes color the box border + top band: `.src` external source (ochre) · `.engine`
computation (teal) · `.artifact` file/data produced (olive) · `.surface` user-facing
route/page (rust) · `.user` the human (inverted ink). No class = neutral.

## Layout rules you control

- **Top-down layers come from the edges** (longest path from the roots). You don't position
  anything vertically — get the edge directions right and the flow reads downward.
- **Left-to-right order within a layer = declaration order** (grouped nodes cluster by their
  group's declaration order first). If two boxes should sit side by side in a specific
  order, declare them in that order.
- Cycles are allowed (back edges route around the right side) but think twice — a flow
  diagram with a cycle is usually two diagrams.

## Authoring rules (binding — same spirit as the depth bar)

1. **One idea per diagram.** The system data-flow, an area's runtime map, and the
   dependency graph are separate diagrams — never merge them. ≤ ~15 nodes each; if you need
   more, split the diagram.
2. **Every edge is labeled with WHAT moves** (`"cleaned comparables"`, `"§2 records"`) —
   an unlabeled arrow is a vibe. Keep labels ≤ ~28 chars; they must survive being read on
   the arrow.
3. **Node labels name the real thing** — a symbol (`build.aggregate()`), an artifact path
   (`operaty/_records.json`), a route (`GET /korpus`) — not a paraphrase. The diagram must
   agree with the cited mechanics text next to it.
4. **Classes are semantic, not decorative.** `.src` only for things outside the system,
   `.artifact` only for data at rest, `.surface` only for things the user reaches.
5. **Dependency/retraction graphs:** node per experiment (label "EXP-id\n(lifecycle)"), `edge A -> B "what A's claim cites"` per ledger `parent:` / `_Depends:_` evidence edge. Expect chips, not panels, when campaigns interleave.
6. **The exploration tree is EXEMPT** — it stays the verbatim ASCII block copied from STATUS.md (single source = atlas.yaml; it is a ledger render, not a drawn diagram). Everything else that was ASCII boxes-and-arrows becomes DSL.
7. The renderer falls back to a `<pre>` of the raw block (plus an HTML comment with the
   parse error) when a DSL line is malformed — a rendered fallback is a BUG in the block;
   fix the line, never ship the fallback.

## Legacy

A plain ``` fenced block (no info string) still renders as monospace ASCII — kept for
back-compat with v2 documents and for genuinely textual content (directory trees, sample
records). New diagrams must use the DSL.
