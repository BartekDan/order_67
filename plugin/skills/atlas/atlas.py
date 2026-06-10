#!/usr/bin/env python3
"""
atlas.py — order-67 harness skill generator. Regenerate a project's ATLAS (the
single control surface) from its hand-curated ledger experiments/_atlas/atlas.yaml.

It runs against the PROJECT being managed, not the plugin. Resolve the project root
from (in order): argv[1], $CLAUDE_PROJECT_DIR, or the current working directory.

Output (NEVER hand-edit — re-run to regenerate):
  <project>/experiments/_atlas/STATUS.md   — markdown board: you-are-here + exploration
        tree (incl. dead-ends/backtracks with `why`) + status table + method battery
        + cross-cutting truths + parking lot + drift check.

atlas v2 split: the deep dossier ATLAS.md is model-authored per the /atlas SKILL.md
(template templates/atlas-deep.md.tpl) and rendered to ATLAS.html by render_html.py —
this script no longer emits HTML (the old board one-pager is retired; the board is
STATUS.md, whose tree block ATLAS.md embeds verbatim).

Prints an `## AtlasReport` block (counts + you-are-here + drift flags).

Usage:
  python ${CLAUDE_PLUGIN_ROOT}/skills/atlas/atlas.py [project_dir]

Ledger schema (experiments/_atlas/atlas.yaml): project, [regime], [you_are_here],
nodes[] (id, kind, lifecycle, parent, verdict, [why], [next], [links]), [battery],
[cross_cutting], [parking_lot], [infra], [archived]. Only `project` + `nodes` are
required; every other section renders if present and is skipped if absent — so the
skill works for any order-67 project, not just Proteus.

Dependency: PyYAML (pip install pyyaml).
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("atlas.py needs PyYAML — `pip install pyyaml` in the python you invoke it with.")


def project_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()


ROOT = project_root()
LEDGER = ROOT / "experiments/_atlas/atlas.yaml"
OUT_MD = ROOT / "experiments/_atlas/STATUS.md"

# lifecycle -> (glyph, human label, css class)
LIFE = {
    "done":      ("✅", "done",        "done"),
    "active":    ("▶",  "active",      "active"),
    "blocked":   ("⛔", "blocked",     "blocked"),
    "dead-end":  ("✗",  "dead-end",    "dead"),
    "superseded":("⊘",  "superseded",  "dead"),
    "deferred":  ("⏸",  "deferred",    "defer"),
    "not-built": ("◻",  "not built",   "todo"),
    "idea":      ("💡", "idea",        "idea"),
}
BATTERY_GLYPH = {"built": "✅", "built-deferred": "⏸", "not-built": "◻",
                 "dead": "✗", "infra-ready": "◑"}


def _short(node_id: str) -> str:
    return str(node_id).split("/")[-1]


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--pretty=format:%h %cs"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
        return out or "(uncommitted)"
    except Exception:
        return "(no git)"


def children_map(nodes):
    kids = {}
    for n in nodes:
        kids.setdefault(n.get("parent"), []).append(n)
    return kids


def drift(nodes):
    """missing_node = experiment dir with no ledger node (a path off the board — the
    dangerous case). missing_dir = an already-STARTED experiment node whose dir is
    gone (stale/renamed). Planned (not-built/idea) experiments need no dir yet."""
    exp_root = ROOT / "experiments"
    exp_dirs = {p.name for p in exp_root.iterdir()
                if p.is_dir() and p.name.startswith("EXP-")} if exp_root.is_dir() else set()
    all_exp = {n["id"] for n in nodes if n.get("kind") == "experiment"}
    started = {n["id"] for n in nodes if n.get("kind") == "experiment"
               and n.get("lifecycle") not in ("not-built", "idea")}
    return sorted(exp_dirs - all_exp), sorted(started - exp_dirs)


# ---------------------------------------------------------------- markdown
def md_tree(kids, parent, depth, out):
    for n in kids.get(parent, []):
        g, _, _ = LIFE.get(n.get("lifecycle"), ("•", n.get("lifecycle", "?"), ""))
        pad = "    " * depth
        out.append(f"{pad}{g} {_short(n['id'])} — {n.get('verdict','')}")
        if n.get("why"):
            out.append(f"{pad}    why: {n['why']}")
        md_tree(kids, n["id"], depth + 1, out)


def render_md(d, commit, now, drift_res):
    nodes = d.get("nodes", [])
    kids = children_map(nodes)
    yah = d.get("you_are_here") or {}
    missing_node, missing_dir = drift_res
    L = [f"# {d.get('project','(untitled project)')} — ATLAS", ""]
    if d.get("regime"):
        L += [f"_Regime {d['regime']}_", ""]
    L += [f"**Generated {now} · commit {commit} · source `experiments/_atlas/atlas.yaml` "
          f"(edit that, then `/atlas`).**", "",
          "> ⚠️ GENERATED FILE — do not hand-edit. Edit `atlas.yaml` and regenerate.", ""]
    if yah:
        L += ["## ▶ YOU ARE HERE",
              f"- **Node:** `{yah.get('node','—')}`",
              f"- **State:** {yah.get('summary','')}"]
        if yah.get("blocker"):
            L.append(f"- **⛔ Blocker:** {yah['blocker']}")
        if yah.get("next"):
            L.append(f"- **→ Next:** {yah['next']}")
        L.append("")
    L += ["## The exploration tree",
          "Glyphs: ✅ done · ▶ active · ⛔ blocked · ✗ dead-end · ⊘ superseded · ⏸ deferred · ◻ not built · 💡 idea",
          "", "```"]
    tree = []
    md_tree(kids, None, 0, tree)
    L += tree + ["```", ""]
    # status table
    L += ["## Status table", "| Node | Kind | State | Verdict | Next |", "|---|---|---|---|---|"]
    for x in nodes:
        g, lab, _ = LIFE.get(x.get("lifecycle"), ("•", x.get("lifecycle", "?"), ""))
        L.append(f"| `{x['id']}` | {x.get('kind','')} | {g} {lab} | {x.get('verdict','')} | {x.get('next','') or ''} |")
    L.append("")
    if d.get("battery"):
        L += ["## Method battery (modules, run per dataset)", "| Family | Method | State | Note |", "|---|---|---|---|"]
        for b in d["battery"]:
            L.append(f"| {b.get('family','')} | {b.get('method','')} | {BATTERY_GLYPH.get(b.get('state'),'•')} {b.get('state','')} | {b.get('note','')} |")
        L.append("")
    if d.get("cross_cutting"):
        L.append("## Cross-cutting truths (frozen — don't re-litigate)")
        L += [f"- {c}" for c in d["cross_cutting"]] + [""]
    if d.get("parking_lot"):
        L.append("## ⏸ Parking lot")
        L += [f"- {p}" for p in d["parking_lot"]] + [""]
    if d.get("infra"):
        L.append("## Infra / blocker")
        L += [f"- **{k}:** {v}" for k, v in d["infra"].items()] + [""]
    if d.get("archived"):
        a = d["archived"]
        L.append("## 🗄 Archived (off-board)")
        if a.get("regime_a"):
            L.append(f"- {a['regime_a']}")
        L += [f"  - lesson: {x}" for x in a.get("carried_lessons", [])] + [""]
    L.append("## 🔎 Drift check")
    if not missing_node and not missing_dir:
        L.append("- ✅ ledger and experiment dirs agree.")
    L += [f"- ⚠️ experiment dir `{m}` has NO ledger node — add it to atlas.yaml." for m in missing_node]
    L += [f"- ⚠️ ledger experiment `{m}` has NO dir under experiments/ — stale or renamed." for m in missing_dir]
    L.append("")
    return "\n".join(L)


def main():
    if not LEDGER.exists():
        sys.exit(f"No ledger at {LEDGER}. Create experiments/_atlas/atlas.yaml first "
                 f"(see the /atlas skill for the schema).")
    d = yaml.safe_load(LEDGER.read_text())
    commit = git_commit()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    nodes = d.get("nodes", [])
    drift_res = drift(nodes)
    OUT_MD.write_text(render_md(d, commit, now, drift_res))

    counts = {}
    for x in nodes:
        counts[x.get("lifecycle", "?")] = counts.get(x.get("lifecycle", "?"), 0) + 1
    missing_node, missing_dir = drift_res
    print("## AtlasReport")
    print(f"- generated-at: {now} · commit {commit}")
    print("- wrote: experiments/_atlas/STATUS.md (board) — deep dossier ATLAS.md/ATLAS.html is model-authored + render_html.py (see SKILL.md)")
    print(f"- nodes: {len(nodes)} — " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    yah = d.get("you_are_here") or {}
    print(f"- you-are-here: {yah.get('node','—')}")
    if missing_node or missing_dir:
        print(f"- ⚠️ DRIFT: dirs-without-node={missing_node}; nodes-without-dir={missing_dir}")
    else:
        print("- drift: none (ledger ↔ dirs agree)")


if __name__ == "__main__":
    main()
