#!/usr/bin/env python3
"""Deterministic ATLAS.md → ATLAS.html editorial renderer (order-67 atlas v3, zero dependencies).

Ported verbatim from order-66 skills/atlas/render_html.py (the two harnesses share the house
editorial); only this docstring and the footer line differ. Keep the two in sync on bugfixes.

Renders the deep dossier into a self-contained editorial HTML page in the house style
(Fraunces display / Inter Tight body / JetBrains Mono code; ink-paper-rust-ochre-olive-teal
palette — same family as /showcase and tmp/bhp-strategy.html). CONTENT SINGLE-SOURCE RULE:
this script never adds, drops, or rewrites content — ATLAS.md is the only authored artifact;
ATLAS.html is a pure presentation of it. Re-run after every ATLAS.md regeneration:

    python3 render_html.py <path/to/ATLAS.md>     # writes sibling ATLAS.html

NOTE: the ATLAS.md h1 must be PLAIN TEXT (no raw HTML) — inline() escapes raw tags; the
renderer itself italicizes the "(deep dossier)" suffix.

Parses exactly the markdown subset the atlas-deep template emits: YAML frontmatter, #/##/###/####
headings, fenced code blocks, pipe tables, bullet + ordered lists (one nesting level),
blockquotes, hrs, raw <a id=…> anchor lines, and inline **bold** / *italic* / `code` /
[links](…).

v3 additions:
- ```flow / ```graph fenced blocks hold the diagram DSL (templates/diagram-dsl.md) and are
  rendered as deterministic layered SVG diagrams (boxes, labeled arrows, area groups) instead
  of ASCII art. Plain ``` blocks still render as monospace <pre> (legacy/back-compat). A DSL
  block that fails to parse falls back to <pre> with the error noted — never a crash.
- Headings starting with "In plain words" open a visually distinct layman panel that wraps
  the whole section (until the next heading of the same or higher level).
"""
from __future__ import annotations

import html
import itertools
import re
import sys
import textwrap
from pathlib import Path

# ----------------------------------------------------------------------------- inline markdown
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_ITAL = re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def inline(text: str) -> str:
    """HTML-escape, then apply inline markdown. Code spans are substituted first (placeholder
    pass) so asterisks inside formulas like `Σ(wᵢ·oᵢ)` are never mangled by bold/italic."""
    esc = html.escape(text, quote=False)
    stash: list[str] = []

    def _stash(m: re.Match) -> str:
        stash.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(stash) - 1}\x00"

    esc = _CODE.sub(_stash, esc)
    esc = _LINK.sub(r'<a href="\2">\1</a>', esc)
    esc = _BOLD.sub(r"<strong>\1</strong>", esc)
    esc = _ITAL.sub(r"<em>\1</em>", esc)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], esc)


def slug(text: str) -> str:
    s = re.sub(r"[`*]", "", text).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", s).strip("-") or "s"


# ----------------------------------------------------------------------------- diagram DSL
# Grammar (one statement per line; see templates/diagram-dsl.md):
#   group <id> "Title"
#   node  <id> "Label"  [@<group>] [.<class>]      class ∈ src|engine|artifact|surface|user
#   edge  <a> -> <b> ["what moves"] [dashed]
# Layout is layered top-down: layer = longest path from the roots; within a layer nodes keep
# (group, declaration) order — authors control left-to-right by declaration order. Fully
# deterministic: no randomness, no timestamps.

_DSL_GROUP = re.compile(r'^group\s+(\S+)\s+"([^"]*)"\s*$')
_DSL_NODE = re.compile(r'^node\s+(\S+)\s+"([^"]*)"((?:\s+[@.]\S+)*)\s*$')
_DSL_EDGE = re.compile(r'^edge\s+(\S+)\s*->\s*(\S+)(?:\s+"([^"]*)")?(\s+dashed)?\s*$')

_CLASS_COLOR = {"src": "#d4a017", "engine": "#1e5f6e", "artifact": "#4a5d23",
                "surface": "#c4451c", "user": "#0a0a0a", "": "rgba(10,10,10,.55)"}
_GROUP_TINTS = ["rgba(30,95,110,.06)", "rgba(212,160,23,.08)", "rgba(74,93,35,.07)",
                "rgba(196,69,28,.05)", "rgba(10,10,10,.04)"]

_NODE_FS, _CHAR_W, _LINE_H, _PAD_X, _PAD_Y = 12.5, 7.6, 17.0, 13.0, 10.0
_H_GAP, _V_GAP, _WRAP_COLS = 34.0, 64.0, 26
_svg_seq = itertools.count()


class _DslError(Exception):
    pass


def _parse_dsl(text: str):
    nodes: dict[str, dict] = {}
    groups: dict[str, dict] = {}
    edges: list[dict] = []

    def ensure(nid: str) -> dict:
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": nid, "group": None, "cls": "", "order": len(nodes)}
        return nodes[nid]

    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        if m := _DSL_GROUP.match(ln):
            groups[m.group(1)] = {"id": m.group(1), "title": m.group(2), "order": len(groups)}
        elif m := _DSL_NODE.match(ln):
            n = ensure(m.group(1))
            n["label"] = m.group(2)
            for tok in (m.group(3) or "").split():
                if tok.startswith("@"):
                    n["group"] = tok[1:]
                elif tok.startswith("."):
                    n["cls"] = tok[1:]
            if n["cls"] and n["cls"] not in _CLASS_COLOR:
                raise _DslError(f"unknown class .{n['cls']} (known: {', '.join(k for k in _CLASS_COLOR if k)})")
        elif m := _DSL_EDGE.match(ln):
            ensure(m.group(1)); ensure(m.group(2))
            edges.append({"src": m.group(1), "dst": m.group(2),
                          "label": m.group(3) or "", "dashed": bool(m.group(4))})
        else:
            raise _DslError(f"unparseable line: {ln!r}")
    if not nodes:
        raise _DslError("diagram has no nodes")
    for n in nodes.values():
        if n["group"] and n["group"] not in groups:
            raise _DslError(f"node {n['id']} names undeclared group @{n['group']}")
    return nodes, groups, edges


def _layer(nodes: dict, edges: list[dict]) -> None:
    preds: dict[str, list[str]] = {nid: [] for nid in nodes}
    for e in edges:
        if e["src"] != e["dst"]:
            preds[e["dst"]].append(e["src"])
    state: dict[str, int] = {}  # 1 = visiting, 2 = done

    def depth(nid: str) -> int:
        if state.get(nid) == 1:        # cycle: cut the back edge for layering
            return 0
        if state.get(nid) == 2:
            return nodes[nid]["layer"]
        state[nid] = 1
        d = max((depth(p) + 1 for p in preds[nid]), default=0)
        nodes[nid]["layer"] = d
        state[nid] = 2
        return d

    for nid in nodes:
        depth(nid)


def _size(n: dict) -> None:
    lines: list[str] = []
    for part in n["label"].split("\\n"):
        lines.extend(textwrap.wrap(part, _WRAP_COLS) or [""])
    n["lines"] = lines
    n["w"] = max(70.0, max(len(l) for l in lines) * _CHAR_W + 2 * _PAD_X)
    n["h"] = len(lines) * _LINE_H + 2 * _PAD_Y


def _place(nodes: dict, groups: dict, edges: list[dict]) -> tuple[float, float]:
    by_layer: dict[int, list[dict]] = {}
    for n in nodes.values():
        by_layer.setdefault(n["layer"], []).append(n)
    gorder = lambda n: (groups[n["group"]]["order"] if n["group"] else -1, n["order"])
    for lst in by_layer.values():
        lst.sort(key=gorder)

    # y per layer
    y = 8.0
    for li in sorted(by_layer):
        row_h = max(n["h"] for n in by_layer[li])
        for n in by_layer[li]:
            n["y"] = y + (row_h - n["h"]) / 2
        y += row_h + _V_GAP
    total_h = y - _V_GAP + 8.0

    # initial x: sequential per layer, centered on the widest layer
    widths = {li: sum(n["w"] for n in lst) + _H_GAP * (len(lst) - 1)
              for li, lst in by_layer.items()}
    cx = max(widths.values()) / 2 + 8.0
    for li, lst in by_layer.items():
        x = cx - widths[li] / 2
        for n in lst:
            n["x"] = x
            x += n["w"] + _H_GAP

    # alignment sweeps: pull nodes toward the mean of their neighbors, keep order, no overlap
    nbrs_dn = {nid: [e["src"] for e in edges if e["dst"] == nid] for nid in nodes}
    nbrs_up = {nid: [e["dst"] for e in edges if e["src"] == nid] for nid in nodes}
    layers_sorted = sorted(by_layer)
    for nbrs, order in ((nbrs_dn, layers_sorted), (nbrs_up, layers_sorted[::-1])) * 2:
        for li in order:
            lst = by_layer[li]
            for n in lst:
                pts = [nodes[m]["x"] + nodes[m]["w"] / 2 for m in nbrs[n["id"]]]
                if pts:
                    n["x"] = sum(pts) / len(pts) - n["w"] / 2
            left = 8.0
            for n in lst:                       # resolve overlaps left → right
                n["x"] = max(n["x"], left)
                left = n["x"] + n["w"] + _H_GAP
            right = max(n["x"] + n["w"] for n in lst) if lst else 0
            for n in reversed(lst):             # and once right → left to recentre
                n["x"] = min(n["x"], right - n["w"])
                right = n["x"] - _H_GAP

    total_w = max(n["x"] + n["w"] for n in nodes.values()) + 8.0
    return total_w, total_h


def _bezier_at(p0, p1, p2, p3, t: float) -> tuple[float, float]:
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


_GROUP_SOLID = ["#1e5f6e", "#9a7510", "#4a5d23", "#8b2f10", "#555555"]


def _render_svg(text: str) -> str:
    nodes, groups, edges = _parse_dsl(text)
    _layer(nodes, edges)
    for n in nodes.values():
        _size(n)
    _place(nodes, groups, edges)

    # spread multi-edge attachment points across node tops/bottoms
    outs: dict[str, list[dict]] = {}
    ins: dict[str, list[dict]] = {}
    for e in edges:
        outs.setdefault(e["src"], []).append(e)
        ins.setdefault(e["dst"], []).append(e)
    other_x = lambda e, end: nodes[e[end]]["x"] + nodes[e[end]]["w"] / 2
    for nid, lst in outs.items():
        lst.sort(key=lambda e: other_x(e, "dst"))
        for k, e in enumerate(lst):
            e["sx"] = nodes[nid]["x"] + nodes[nid]["w"] * (k + 1) / (len(lst) + 1)
    for nid, lst in ins.items():
        lst.sort(key=lambda e: other_x(e, "src"))
        for k, e in enumerate(lst):
            e["tx"] = nodes[nid]["x"] + nodes[nid]["w"] * (k + 1) / (len(lst) + 1)

    # bounds tracker — viewBox is computed from everything actually drawn
    bx = [1e9, 1e9, -1e9, -1e9]

    def grow(x0: float, y0: float, x1: float, y1: float) -> None:
        bx[0] = min(bx[0], x0); bx[1] = min(bx[1], y0)
        bx[2] = max(bx[2], x1); bx[3] = max(bx[3], y1)

    cx_all = sum(n["x"] + n["w"] / 2 for n in nodes.values()) / len(nodes)

    # group rendering decision: PANELS only when EVERY group's bbox is free of foreign nodes;
    # if any group is cross-cutting, ALL groups render as per-node corner CHIPS instead — a
    # mixed presentation reads worse than either pure form.
    panels, chips = [], {}
    candidates = []
    any_foreign = False
    for g in sorted(groups.values(), key=lambda g: g["order"]):
        mem = [n for n in nodes.values() if n["group"] == g["id"]]
        if not mem:
            continue
        x0 = min(n["x"] for n in mem) - 12
        y0 = min(n["y"] for n in mem) - 27
        x1 = max(n["x"] + n["w"] for n in mem) + 12
        x1 = max(x1, x0 + len(g["title"]) * 6.1 + 26)        # title must fit
        y1 = max(n["y"] + n["h"] for n in mem) + 12
        foreign = any(n["group"] != g["id"]
                      and n["x"] < x1 - 4 and n["x"] + n["w"] > x0 + 4
                      and n["y"] < y1 - 4 and n["y"] + n["h"] > y0 + 4
                      for n in nodes.values())
        any_foreign = any_foreign or foreign
        candidates.append((g, mem, x0, y0, x1, y1))
    for g, mem, x0, y0, x1, y1 in candidates:
        if any_foreign:
            for n in mem:
                chips[n["id"]] = g
        else:
            panels.append((g, x0, y0, x1, y1))

    aid = f"arr{next(_svg_seq)}"
    parts: list[str] = [
        f'<defs><marker id="{aid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
        'fill="#2a2a2a"/></marker></defs>']

    for g, x0, y0, x1, y1 in panels:
        tint = _GROUP_TINTS[g["order"] % len(_GROUP_TINTS)]
        parts.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" '
                     f'rx="10" fill="{tint}" stroke="rgba(10,10,10,.22)" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{x0+10:.1f}" y="{y0+15:.1f}" font-family="JetBrains Mono,monospace" '
                     f'font-size="9.5" letter-spacing="1.4" fill="#6b6b6b">'
                     f'{html.escape(g["title"].upper())}</text>')
        grow(x0, y0, x1, y1)

    # edges under nodes; labels collected for a collision pass
    lbl: list[dict] = []
    for idx, e in enumerate(edges):
        s, t = nodes[e["src"]], nodes[e["dst"]]
        dash = ' stroke-dasharray="5 4"' if e["dashed"] else ""
        span = t["layer"] - s["layer"]
        if span >= 1:
            p0 = (e.get("sx", s["x"] + s["w"] / 2), s["y"] + s["h"])
            p3 = (e.get("tx", t["x"] + t["w"] / 2), t["y"])
            dy = (p3[1] - p0[1]) * 0.42
            bow = 0.0
            if span >= 2:                       # bow long edges sideways, away from the middle
                side = 1.0 if (p0[0] + p3[0]) / 2 >= cx_all else -1.0
                bow = side * (44.0 + 18.0 * (span - 2) + 12.0 * (idx % 2))
            p1, p2 = (p0[0] + bow, p0[1] + dy), (p3[0] + bow, p3[1] - dy)
            lt = 0.30 if span == 1 else 0.5     # label near source, or mid-bow for long edges
        else:                                   # flat or upward edge: bulge out on the right
            p0 = (s["x"] + s["w"], s["y"] + s["h"] / 2)
            p3 = (t["x"] + t["w"], t["y"] + t["h"] / 2)
            bulge = max(p0[0], p3[0]) + 52 + 16 * (idx % 3)
            p1, p2 = (bulge, p0[1]), (bulge, p3[1])
            lt = 0.5
        parts.append(f'<path d="M{p0[0]:.1f},{p0[1]:.1f} C{p1[0]:.1f},{p1[1]:.1f} '
                     f'{p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" fill="none" '
                     f'stroke="#2a2a2a" stroke-width="1.2"{dash} marker-end="url(#{aid})"/>')
        for q in (p0, p1, p2, p3):
            grow(q[0], q[1], q[0], q[1])
        if e["label"]:
            mx, my = _bezier_at(p0, p1, p2, p3, lt)
            lbl.append({"x": mx, "y": my + 4.0, "text": e["label"]})

    # deterministic label de-collision: a label must clear both earlier labels AND node boxes
    # (pushed down 13px at a time until free — downwards lands in the inter-layer gap)
    rects = [(n["x"] - 4, n["y"] - 4, n["x"] + n["w"] + 4, n["y"] + n["h"] + 4)
             for n in nodes.values()]
    placed: list[dict] = []
    for L in lbl:
        hw = len(L["text"]) * 3.1 + 6
        for _ in range(10):
            hit_lbl = any(abs(L["x"] - p["x"]) < hw + p["hw"] and abs(L["y"] - p["y"]) < 13
                          for p in placed)
            hit_node = any(L["x"] + hw > rx0 and L["x"] - hw < rx1
                           and L["y"] > ry0 and L["y"] - 11 < ry1
                           for rx0, ry0, rx1, ry1 in rects)
            if not hit_lbl and not hit_node:
                break
            L["y"] += 13.0
        L["hw"] = hw
        placed.append(L)

    # nodes (+ group chips for cross-cutting groups)
    for n in sorted(nodes.values(), key=lambda n: n["order"]):
        color = _CLASS_COLOR[n["cls"]]
        dark = n["cls"] == "user"
        fill, tcol = ("#0a0a0a", "#f5f1e8") if dark else ("#faf6ed", "#1a1a1a")
        parts.append(f'<rect x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]:.1f}" '
                     f'height="{n["h"]:.1f}" rx="7" fill="{fill}" stroke="{color}" '
                     f'stroke-width="{1.6 if n["cls"] else 1.2}"/>')
        if n["cls"] and not dark:
            parts.append(f'<rect x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]:.1f}" '
                         f'height="3.5" rx="1.75" fill="{color}"/>')
        ty0 = n["y"] + _PAD_Y + _LINE_H * 0.72
        for j, line in enumerate(n["lines"]):
            parts.append(f'<text x="{n["x"] + n["w"]/2:.1f}" y="{ty0 + j*_LINE_H:.1f}" '
                         f'text-anchor="middle" font-family="JetBrains Mono,monospace" '
                         f'font-size="{_NODE_FS}" fill="{tcol}">{html.escape(line)}</text>')
        grow(n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"])
        if n["id"] in chips:
            g = chips[n["id"]]
            parts.append(f'<text x="{n["x"]:.1f}" y="{n["y"]-5:.1f}" '
                         f'font-family="JetBrains Mono,monospace" font-size="8.5" '
                         f'letter-spacing="1.1" fill="{_GROUP_SOLID[g["order"] % len(_GROUP_SOLID)]}" '
                         f'paint-order="stroke" stroke="#faf6ed" stroke-width="3">'
                         f'{html.escape(g["title"].upper())}</text>')
            grow(n["x"], n["y"] - 16, n["x"] + len(g["title"]) * 5.6, n["y"])

    for L in placed:                            # edge labels on top of everything
        parts.append(f'<text x="{L["x"]:.1f}" y="{L["y"]:.1f}" text-anchor="middle" '
                     f'font-family="JetBrains Mono,monospace" font-size="10.5" fill="#444" '
                     f'paint-order="stroke" stroke="#faf6ed" stroke-width="4">'
                     f'{html.escape(L["text"])}</text>')
        grow(L["x"] - L["hw"], L["y"] - 11, L["x"] + L["hw"], L["y"] + 3)

    vx, vy = bx[0] - 10, bx[1] - 10
    vw, vh = bx[2] - bx[0] + 20, bx[3] - bx[1] + 20
    return (f'<figure class="dsl"><svg viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}" '
            f'style="max-width:{vw:.0f}px" role="img" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg></figure>')


# ----------------------------------------------------------------------------- block parsing
def parse(md: str) -> tuple[dict, list[dict], str]:
    """Return (frontmatter, nav entries, body html)."""
    meta: dict[str, str] = {}
    lines = md.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            if ":" in lines[i]:
                k, _, v = lines[i].partition(":")
                meta[k.strip()] = v.split("#")[0].strip().strip('"')
            i += 1
        i += 1

    out: list[str] = []
    nav: list[dict] = []
    seen_ids: set[str] = set()
    pending_anchor: str | None = None
    layman_lvl: int | None = None
    para: list[str] = []
    quote: list[str] = []
    n = len(lines)

    def uniq(s: str) -> str:
        base, k = s, 2
        while s in seen_ids:
            s = f"{base}-{k}"
            k += 1
        seen_ids.add(s)
        return s

    def flush_para() -> None:
        nonlocal para
        if para:
            text = " ".join(para)
            cls = ' class="slice-meta"' if text.startswith("**Mode:**") else ""
            out.append(f"<p{cls}>{inline(text)}</p>")
            para = []

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            out.append("<blockquote>" + "<br>".join(inline(q) for q in quote) + "</blockquote>")
            quote = []

    while i < n:
        ln = lines[i]
        s = ln.strip()

        if s.startswith("```"):
            flush_para(); flush_quote()
            info = s[3:].strip().lower()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            raw = "\n".join(buf)
            if info in ("flow", "graph", "diagram"):
                try:
                    out.append(_render_svg(raw))
                except _DslError as err:  # honest fallback, never a crash
                    out.append(f"<!-- diagram DSL error: {html.escape(str(err))} -->")
                    out.append('<pre class="diagram">' + html.escape(raw) + "</pre>")
            else:
                out.append('<pre class="diagram">' + html.escape(raw) + "</pre>")
            i += 1
            continue

        if re.match(r'^<a id="[^"]+"></a>\s*$', s):
            flush_para(); flush_quote()
            pending_anchor = re.search(r'id="([^"]+)"', s).group(1)
            i += 1
            continue

        m = re.match(r"^(#{1,4}) (.+)$", s)
        if m:
            flush_para(); flush_quote()
            lvl, text = len(m.group(1)), m.group(2)
            if layman_lvl and lvl <= layman_lvl:
                out.append("</section>")
                layman_lvl = None
            hid = pending_anchor or uniq(slug(text))
            pending_anchor = None
            if lvl == 1:
                out.append(f'<h1 id="{hid}">{inline(text)}</h1>')
            else:
                if text.lower().startswith("in plain words"):
                    out.append('<section class="layman">')
                    layman_lvl = lvl
                if lvl == 2:
                    nav.append({"lvl": 2, "text": re.sub(r"[`]", "", text), "id": hid})
                elif lvl == 3 and text.startswith("`"):
                    nav.append({"lvl": 3, "text": re.sub(r"[`]", "", text.split(" — ")[0]), "id": hid})
                out.append(f'<h{lvl} id="{hid}">{inline(text)}</h{lvl}>')
            i += 1
            continue

        if s.startswith("|"):
            flush_para(); flush_quote()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = None, rows
            if len(rows) >= 2 and all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1]):
                head, body = rows[0], rows[2:]
            t = ["<table>"]
            if head:
                t.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        if s.startswith(">"):
            flush_para()
            quote.append(s.lstrip("> ").strip())
            i += 1
            continue

        if re.fullmatch(r"-{3,}|_{3,}", s):
            flush_para(); flush_quote()
            out.append("<hr>")
            i += 1
            continue

        if re.match(r"^\s*\d{1,3}[.)] ", ln):
            flush_para(); flush_quote()
            out.append("<ol>")
            while i < n and re.match(r"^\s*\d{1,3}[.)] ", lines[i]):
                item = re.sub(r"^\s*\d{1,3}[.)] ", "", lines[i]).strip()
                i += 1
                while i < n and lines[i].strip() and not re.match(r"^\s*\d{1,3}[.)] ", lines[i]) \
                        and not re.match(r"^\s*[-*] ", lines[i]) \
                        and not re.match(r"^(#{1,4}) |^```|^\||^>", lines[i].strip()):
                    item += " " + lines[i].strip()
                    i += 1
                out.append(f"<li>{inline(item)}</li>")
            out.append("</ol>")
            continue

        if re.match(r"^\s*[-*] ", ln):
            flush_para(); flush_quote()
            out.append("<ul>")
            opened_sub = False
            while i < n and re.match(r"^\s*[-*] ", lines[i]):
                indent = len(lines[i]) - len(lines[i].lstrip())
                item = lines[i].strip()[2:]
                i += 1
                # continuation lines (hanging indent, not new bullets)
                while i < n and lines[i].strip() and not re.match(r"^\s*[-*] ", lines[i]) \
                        and not re.match(r"^(#{1,4}) |^```|^\||^>", lines[i].strip()):
                    item += " " + lines[i].strip()
                    i += 1
                if indent >= 2 and not opened_sub:
                    out.append("<ul>"); opened_sub = True
                elif indent < 2 and opened_sub:
                    out.append("</ul>"); opened_sub = False
                out.append(f"<li>{inline(item)}</li>")
            if opened_sub:
                out.append("</ul>")
            out.append("</ul>")
            continue

        if not s:
            flush_para(); flush_quote()
            i += 1
            continue

        flush_quote()
        para.append(s)
        i += 1

    flush_para(); flush_quote()
    if layman_lvl:
        out.append("</section>")
    return meta, nav, "\n".join(out)


# ----------------------------------------------------------------------------- page shell
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter+Tight:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--ink:#0a0a0a;--paper:#f5f1e8;--cream:#faf6ed;--rust:#c4451c;--rust-dark:#8b2f10;
--ochre:#d4a017;--olive:#4a5d23;--teal:#1e5f6e;--slate:#2a2a2a;--grey:#6b6b6b;--line:#1a1a1a;
--soft-line:rgba(10,10,10,.15)}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:24px}
body{font-family:'Inter Tight',sans-serif;background:var(--paper);color:var(--ink);
font-size:15.5px;line-height:1.62}
.layout{display:grid;grid-template-columns:284px minmax(0,1fr);max-width:1480px;margin:0 auto}
nav{position:sticky;top:0;height:100vh;overflow-y:auto;padding:34px 18px 60px 28px;
border-right:1px solid var(--soft-line);font-size:12.5px;scrollbar-width:thin}
nav .nav-title{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.14em;
text-transform:uppercase;color:var(--grey);margin-bottom:14px}
nav a{display:block;color:var(--slate);text-decoration:none;padding:3px 8px;border-radius:3px;
line-height:1.35}
nav a:hover{background:var(--cream);color:var(--rust-dark)}
nav a.lvl2{font-weight:600;margin-top:10px;color:var(--rust-dark)}
nav a.lvl3{padding-left:20px;font-family:'JetBrains Mono',monospace;font-size:11.5px}
main{padding:0 56px 110px;min-width:0}
.hero{border-top:3px solid var(--ink);border-bottom:1px solid var(--ink);padding:26px 0 56px;
margin-bottom:56px}
.hero-meta{display:flex;flex-wrap:wrap;gap:8px 22px;font-family:'JetBrains Mono',monospace;
font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);
padding-bottom:18px;margin-bottom:44px;border-bottom:1px dashed var(--soft-line)}
.hero-meta b{color:var(--ink);font-weight:500}
h1{font-family:'Fraunces',serif;font-weight:300;font-size:clamp(40px,5.5vw,76px);line-height:.98;
letter-spacing:-.03em;font-variation-settings:'opsz' 144}
h1 em,h1 .dossier{font-style:italic;font-weight:400;color:var(--rust)}
h2{font-family:'Fraunces',serif;font-weight:400;font-size:34px;letter-spacing:-.02em;
color:var(--rust-dark);margin:72px 0 18px;padding-bottom:10px;border-bottom:2px solid var(--soft-line)}
h2 code{font-size:30px;background:none;color:inherit;padding:0}
h3{font-family:'Fraunces',serif;font-weight:500;font-size:25px;letter-spacing:-.01em;
margin:54px 0 10px}
h3 code{font-size:22px;background:var(--cream);color:var(--rust-dark)}
h4{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;letter-spacing:.13em;
text-transform:uppercase;color:var(--teal);margin:34px 0 10px}
p{margin:0 0 14px;max-width:860px}
p.slice-meta{font-size:13px;background:var(--cream);border:1px solid var(--soft-line);
border-left:3px solid var(--ochre);border-radius:4px;padding:10px 14px;max-width:none;
line-height:1.8}
p.slice-meta strong{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.1em;
text-transform:uppercase;color:var(--grey);font-weight:600}
blockquote{font-family:'Fraunces',serif;font-style:italic;font-size:16.5px;color:var(--slate);
border-left:3px solid var(--rust);padding:6px 0 6px 18px;margin:0 0 18px;max-width:860px}
ul{margin:0 0 14px 22px;max-width:860px}
ul ul{margin-bottom:0}
li{margin-bottom:5px}
code{font-family:'JetBrains Mono',monospace;font-size:.87em;background:var(--cream);
padding:1.5px 5px;border-radius:3px;color:var(--rust-dark)}
pre.diagram{font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.42;
font-variant-ligatures:none;background:var(--cream);border:1px solid var(--soft-line);
border-left:3px solid var(--olive);border-radius:4px;padding:16px 18px;margin:0 0 18px;
overflow-x:auto;white-space:pre}
figure.dsl{margin:0 0 22px;background:var(--cream);border:1px solid var(--soft-line);
border-left:3px solid var(--olive);border-radius:4px;padding:18px 16px;overflow-x:auto}
figure.dsl svg{display:block;margin:0 auto;width:100%;height:auto}
section.layman{background:linear-gradient(135deg,rgba(212,160,23,.07),rgba(30,95,110,.05));
border:1px solid var(--soft-line);border-left:4px solid var(--ochre);border-radius:6px;
padding:6px 26px 14px;margin:30px 0 34px;position:relative}
section.layman::before{content:'PLAIN WORDS — NO JARGON';position:absolute;top:-9px;left:18px;
background:var(--paper);padding:0 8px;font-family:'JetBrains Mono',monospace;font-size:9.5px;
letter-spacing:.16em;color:var(--ochre);font-weight:600}
section.layman h2,section.layman h3,section.layman h4{margin-top:22px}
section.layman h4{color:#9a7510}
section.layman p{font-size:16px;line-height:1.72}
section.layman ol li,section.layman ul li{font-size:15.5px;line-height:1.66;margin-bottom:9px}
ol{margin:0 0 14px 24px;max-width:860px}
ol li{margin-bottom:7px}
table{border-collapse:collapse;width:100%;margin:0 0 20px;font-size:13.5px;background:var(--cream)}
th{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.1em;
text-transform:uppercase;color:var(--paper);background:var(--teal);text-align:left;
padding:8px 11px;font-weight:500}
td{padding:7px 11px;border-bottom:1px solid var(--soft-line);vertical-align:top}
tr:nth-child(even) td{background:rgba(10,10,10,.022)}
td code{background:rgba(10,10,10,.05)}
a{color:var(--rust);text-decoration-color:rgba(196,69,28,.4)}
hr{border:0;border-top:1px solid var(--soft-line);margin:46px 0}
strong{font-weight:600}
footer{margin-top:70px;padding-top:18px;border-top:1px solid var(--soft-line);
font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.08em;
text-transform:uppercase;color:var(--grey)}
@media (max-width:980px){.layout{grid-template-columns:1fr}nav{position:static;height:auto;
border-right:0;border-bottom:1px solid var(--soft-line)}main{padding:0 22px 70px}}
@media print{nav{display:none}.layout{grid-template-columns:1fr}body{background:#fff}}
"""


def render(md_path: Path) -> Path:
    meta, nav, body = parse(md_path.read_text(encoding="utf-8"))
    project = meta.get("project", "Project")
    title = f"{html.escape(project)} — ATLAS"

    # Editorial accent on the hero h1: italicize the parenthetical.
    body = body.replace("(deep dossier)</h1>", '<span class="dossier">(deep dossier)</span></h1>', 1)

    chips = "".join(
        f'<span>{label} <b>{html.escape(meta[key])}</b></span>'
        for key, label in (("generated_at", "generated"), ("git_anchor", "commit"),
                           ("regen_mode", "regen"), ("template_rev", "template-rev"))
        if meta.get(key)
    )
    nav_html = "".join(
        f'<a class="lvl{e["lvl"]}" href="#{e["id"]}">{html.escape(e["text"])}</a>' for e in nav
    )

    out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
<nav><div class="nav-title">{title}</div>{nav_html}</nav>
<main>
<header class="hero"><div class="hero-meta">{chips}</div></header>
{body}
<footer>Rendered by render_html.py from ATLAS.md — the single content source (order-67 research
harness). Do not hand-edit; re-run /atlas, then this renderer.</footer>
</main>
</div>
</body>
</html>
"""
    # Move the h1 (first body element) into the hero, after the meta chips.
    m = re.search(r"<h1[^>]*>.*?</h1>", out, re.S)
    if m:
        h1 = m.group(0)
        out = out.replace(h1, "", 1).replace('<header class="hero"><div class="hero-meta">' + chips + "</div></header>",
                                             f'<header class="hero"><div class="hero-meta">{chips}</div>{h1}</header>', 1)
    dst = md_path.with_suffix(".html")
    dst.write_text(out, encoding="utf-8")
    return dst


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 render_html.py <path/to/ATLAS.md>")
    src = Path(sys.argv[1])
    if not src.is_file():
        sys.exit(f"not found: {src}")
    print(render(src))
