#!/usr/bin/env python3
"""Deterministic ATLAS.md → ATLAS.html editorial renderer (order-67 atlas v2, zero dependencies).

Ported verbatim from order-66 skills/atlas/render_html.py (the two harnesses share the house
editorial); only this docstring and the footer line differ. Keep the two in sync on bugfixes.

Renders the deep dossier into a self-contained editorial HTML page in the house style
(Fraunces display / Inter Tight body / JetBrains Mono code; ink-paper-rust-ochre-olive-teal
palette — same family as /showcase and tmp/bhp-strategy.html). CONTENT SINGLE-SOURCE RULE:
this script never adds, drops, or rewrites content — ATLAS.md is the only authored artifact;
ATLAS.html is a pure presentation of it. Re-run after every ATLAS.md regeneration:

    python3 render_html.py <path/to/ATLAS.md>     # writes sibling ATLAS.html

Parses exactly the markdown subset the atlas-deep template emits: YAML frontmatter, #/##/###/####
headings, fenced code blocks, pipe tables, bullet lists (one nesting level), blockquotes, hrs,
raw <a id=…> anchor lines, and inline **bold** / *italic* / `code` / [links](…).
"""
from __future__ import annotations

import html
import re
import sys
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
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            out.append('<pre class="diagram">' + html.escape("\n".join(buf)) + "</pre>")
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
            hid = pending_anchor or uniq(slug(text))
            pending_anchor = None
            if lvl == 1:
                out.append(f'<h1 id="{hid}">{inline(text)}</h1>')
            else:
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
