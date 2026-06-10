#!/usr/bin/env python3
"""
atlas.py — order-67 harness skill generator. Regenerate a project's ATLAS (the
single control surface) from its hand-curated ledger experiments/_atlas/atlas.yaml.

It runs against the PROJECT being managed, not the plugin. Resolve the project root
from (in order): argv[1], $CLAUDE_PROJECT_DIR, or the current working directory.

Outputs (NEVER hand-edit — re-run to regenerate):
  <project>/experiments/_atlas/STATUS.md   — markdown board: you-are-here + exploration
        tree (incl. dead-ends/backtracks with `why`) + status table + method battery
        + cross-cutting truths + parking lot + drift check.
  <project>/experiments/_atlas/ATLAS.html  — self-contained styled one-pager.

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

import html
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
OUT_HTML = ROOT / "experiments/_atlas/ATLAS.html"

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


# ---------------------------------------------------------------- html
CSS = """
:root{--ink:#23201b;--muted:#6b6256;--paper:#fbf8f2;--line:#e4dccd;--rust:#a8442a;
--rust-dark:#872f12;--teal:#2f6d6a;--olive:#6b6f3a;--ochre:#c89212;--code:#f1ece1;--cream:#f6efe2;}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:40px 26px 100px}
h1,h2{font-family:Georgia,serif;color:#1c1813}h1{font-size:1.8em;border-bottom:3px solid var(--rust);padding-bottom:.3em;margin-top:0}
h2{font-size:1.25em;margin-top:1.9em;border-bottom:1px solid var(--line);padding-bottom:.2em}
code{background:var(--code);padding:.1em .35em;border-radius:4px;font:12px/1.4 Consolas,Menlo,monospace;color:var(--rust-dark)}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:13px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:#efe7d8;font-family:Georgia,serif}tr:nth-child(even) td{background:#f6f1e7}
.banner{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
.yah{background:var(--cream);border-left:5px solid var(--ochre);border-radius:0 6px 6px 0;padding:14px 18px;margin:1.2em 0}
.warn{background:#f7e9e4;border-left:4px solid var(--rust);border-radius:0 6px 6px 0;padding:8px 14px;margin:.8em 0;font-size:13px}
ul.tree{list-style:none;padding-left:0}ul.tree ul{list-style:none;padding-left:22px;border-left:1px dashed var(--line);margin-left:8px}
ul.tree li{margin:5px 0}.g{display:inline-block;width:1.5em;text-align:center}
.why{color:var(--muted);font-size:12.5px;font-style:italic}
.pill{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:5px;text-transform:uppercase}
.done{background:#e3eeed;color:var(--teal)}.active{background:#fbf2d8;color:#8a6608}
.blocked{background:#f3dcd4;color:var(--rust-dark)}.dead{background:#ece7df;color:#7a7268;text-decoration:line-through}
.defer{background:#eef0e2;color:var(--olive)}.todo{background:#f3efe6;color:var(--muted)}.idea{background:#fbf2d8;color:#8a6608}
.small{font-size:12px;color:var(--muted)}
"""


def html_tree(kids, parent):
    items = kids.get(parent, [])
    if not items:
        return ""
    s = "<ul class='tree'>"
    for n in items:
        g, lab, cls = LIFE.get(n.get("lifecycle"), ("•", n.get("lifecycle", "?"), ""))
        s += "<li>"
        s += f"<span class='g'>{g}</span><strong>{html.escape(_short(n['id']))}</strong> "
        s += f"<span class='pill {cls}'>{html.escape(lab)}</span> — {html.escape(n.get('verdict',''))}"
        if n.get("why"):
            s += f"<br><span class='why'>↳ why: {html.escape(n['why'])}</span>"
        s += html_tree(kids, n["id"])
        s += "</li>"
    return s + "</ul>"


def render_html(d, commit, now, drift_res):
    nodes = d.get("nodes", [])
    kids = children_map(nodes)
    yah = d.get("you_are_here") or {}
    missing_node, missing_dir = drift_res
    proj = d.get("project", "Project")
    h = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width, initial-scale=1'>",
         f"<title>{html.escape(proj)} — Atlas</title><style>{CSS}</style></head><body><div class='wrap'>",
         f"<div class='banner'>Atlas · {html.escape(str(d.get('regime','')))} · {now} · {commit}</div>",
         f"<h1>{html.escape(proj)} — Atlas</h1>",
         "<div class='warn'>⚠️ Generated from <code>experiments/_atlas/atlas.yaml</code> — do not hand-edit; "
         "edit the ledger and run <code>/atlas</code>.</div>"]
    if yah:
        h.append("<div class='yah'><strong>▶ YOU ARE HERE</strong><br>"
                 f"<strong>Node:</strong> <code>{html.escape(str(yah.get('node','—')))}</code><br>"
                 f"<strong>State:</strong> {html.escape(yah.get('summary',''))}")
        if yah.get("blocker"):
            h.append(f"<br><strong>⛔ Blocker:</strong> {html.escape(yah['blocker'])}")
        if yah.get("next"):
            h.append(f"<br><strong>→ Next:</strong> {html.escape(yah['next'])}")
        h.append("</div>")
    h += ["<h2>The exploration tree</h2>",
          "<p class='small'>✅ done · ▶ active · ⛔ blocked · ✗ dead-end · ⊘ superseded · ⏸ deferred · ◻ not built · 💡 idea</p>",
          html_tree(kids, None)]
    if d.get("battery"):
        h.append("<h2>Method battery</h2><table><tr><th>Family</th><th>Method</th><th>State</th><th>Note</th></tr>")
        for b in d["battery"]:
            h.append(f"<tr><td>{html.escape(b.get('family',''))}</td><td>{html.escape(b.get('method',''))}</td>"
                     f"<td>{BATTERY_GLYPH.get(b.get('state'),'•')} {html.escape(str(b.get('state','')))}</td>"
                     f"<td>{html.escape(b.get('note',''))}</td></tr>")
        h.append("</table>")
    if d.get("cross_cutting"):
        h.append("<h2>Cross-cutting truths (frozen)</h2><ul>")
        h += [f"<li>{html.escape(c)}</li>" for c in d["cross_cutting"]]
        h.append("</ul>")
    if d.get("parking_lot"):
        h.append("<h2>⏸ Parking lot</h2><ul>")
        h += [f"<li>{html.escape(p)}</li>" for p in d["parking_lot"]]
        h.append("</ul>")
    if d.get("archived"):
        a = d["archived"]
        h.append("<h2>🗄 Archived (off-board)</h2>")
        if a.get("regime_a"):
            h.append(f"<p class='small'>{html.escape(a['regime_a'])}</p>")
        h.append("<ul>")
        h += [f"<li class='small'>{html.escape(x)}</li>" for x in a.get("carried_lessons", [])]
        h.append("</ul>")
    h.append("<h2>🔎 Drift check</h2>")
    if not missing_node and not missing_dir:
        h.append("<p>✅ ledger and experiment dirs agree.</p>")
    else:
        h.append("<ul>")
        h += [f"<li class='warn'>experiment dir <code>{html.escape(m)}</code> has no ledger node.</li>" for m in missing_node]
        h += [f"<li class='warn'>ledger experiment <code>{html.escape(m)}</code> has no dir.</li>" for m in missing_dir]
        h.append("</ul>")
    h.append("</div></body></html>")
    return "\n".join(h)


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
    OUT_HTML.write_text(render_html(d, commit, now, drift_res))

    counts = {}
    for x in nodes:
        counts[x.get("lifecycle", "?")] = counts.get(x.get("lifecycle", "?"), 0) + 1
    missing_node, missing_dir = drift_res
    print("## AtlasReport")
    print(f"- generated-at: {now} · commit {commit}")
    print(f"- wrote: experiments/_atlas/STATUS.md + experiments/_atlas/ATLAS.html")
    print(f"- nodes: {len(nodes)} — " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    yah = d.get("you_are_here") or {}
    print(f"- you-are-here: {yah.get('node','—')}")
    if missing_node or missing_dir:
        print(f"- ⚠️ DRIFT: dirs-without-node={missing_node}; nodes-without-dir={missing_dir}")
    else:
        print("- drift: none (ledger ↔ dirs agree)")


if __name__ == "__main__":
    main()
