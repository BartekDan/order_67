# Figure style guide — the Ten-Simple-Rules linter (`/analyze` + figure-smith)

Read by `/analyze` to write panel specs, and by the **figure-smith** agent to lint and render them. figure-smith returns a `## FigureReport` (fields `Figure, Lint, Violations, Path`); a single open violation is `Lint: FAIL` and the figure is not shipped. The rules below ARE the linter. They are adapted from "Ten Simple Rules for Better Figures" (Rougier, Droettboom & Bourne, 2014) and the perceptual-uniformity / accessibility literature. The point is that a figure is an *argument*, machine-checkable for the ways figures most often lie.

Every analysis figure is a static, vector, multi-panel artifact written to `results/<exp>/figures/<name>.svg` (RULE-2 — never an absolute path). The harness prints to PDF and lives in static views; no interactivity, no animation.

---

## The ten rules (each is a lint check)

1. **Know your message — declarative-sentence title.** The title states the finding, not the variables. `"Probe accuracy peaks at relative depth 0.6 and exceeds chance at every layer"`, NOT `"Accuracy vs layer"`. The reader should grasp the claim from the title alone. *Lint: title is a full declarative sentence (verb present), not a noun phrase, not "Figure 3".*

2. **Adapt the figure to the medium — vector, embeddable.** Output is `.svg` (or PDF), not raster `.png`/`.jpg`. Text is selectable; lines stay crisp under zoom. *Lint: output extension ∈ {.svg, .pdf}; no `<image>`/embedded raster bitmap.*

3. **Captions are not optional — every panel carries axis labels + units.** Each axis has a label and, where applicable, a unit. The caption states n, the variation source (seed/init/split), and the CI method — mirroring the `## AnalysisReport` `CI:` line. *Lint: every axis labeled; caption names n + variation source + CI method.*

4. **Do not trust the defaults — show the random/chance baseline as a DASHED line.** Any performance/score figure draws the random-baseline reference (chance, majority-class, or published baseline) as a dashed horizontal line, labeled, so "above chance" is visible at a glance. Effect sizes show their CI as a band or error bar, never a bare point. *Lint: performance panels contain a dashed baseline reference; effect-size/mean markers carry a visible CI (band or whisker).*

5. **Use color effectively — colorblind-safe, perceptually uniform.** Categorical encodings use a colorblind-safe qualitative palette (Okabe–Ito 8-color, or Tol's qualitative set). Sequential/continuous encodings use a perceptually-uniform map (viridis / cividis / magma). **Banned, hard fail:** `jet`, `rainbow`, `hsv`, `turbo`, and any non-uniform map — they manufacture false edges and are unreadable in grayscale. *Lint: colormap ∈ approved set; `jet|rainbow|hsv|turbo` ⇒ FAIL. Distinguishable when desaturated.*

6. **Do not mislead the reader — no chartjunk geometry.** **Banned, hard fail:** 3D bars/surfaces (perspective distorts magnitude), pie/donut charts (angle is read worse than length), and **dual-axis (twin-y)** plots (they imply a correlation by arbitrary axis scaling). Bars start at zero unless the axis break is explicit and labeled. *Lint: no 3D projection, no pie/donut, no second y-axis; bar baselines at 0 or an explicit labeled break.*

7. **Avoid "chartjunk" — ink serves data.** No drop shadows, gradient fills behind bars, decorative gridline clutter, or background images. Gridlines are faint and behind the data. Legends sit inside dead space, not over data. *Lint: no shadow/gradient/background-image; ≤1 legend; data ink ≫ decoration ink.*

8. **Message trumps beauty — but consistency across panels.** A multi-panel figure shares one color mapping, one axis convention, and one font across panels; the same series is the same color everywhere. The primary (pre-registered) panel is visually first (top-left) and may carry a single accent. *Lint: shared legend/scale across panels; consistent series→color mapping; primary panel position fixed.*

9. **Use the right tool — reproducible, scripted.** The figure is produced by code committed under the run's `_Owns:_` set (e.g. `results/<exp>/figures/make_figures.py`), seeded if it samples, reading `stats.json` — never hand-edited in a vector editor. The script path + git commit are recorded so the figure regenerates byte-stably. *Lint: a committed script produced it; data source is `stats.json`; no manual post-edit.*

10. **Get the right data — figure matches the numbers.** Every value drawn traces to a row in `results/<exp>/stats.json`; the figure cannot show an effect the stats do not contain (no eyeballed trend lines, no smoothing that invents structure). Cross-model panels plot the *normalized* axis (relative depth / z-score / Procrustes) per RULE-4, with the normalization named in the caption. *Lint: every plotted series ↔ a stats.json field; cross-model axis is normalized + named.*

---

## Approved palette (colorblind-safe; the only fills/strokes the linter accepts)

Use named tokens, not eyeballed hex. The Okabe–Ito set (safe for deuteranopia, protanopia, tritanopia, and grayscale):

| Token | Hex | Use for |
|-------|-----|---------|
| `ok-black`  | `#000000` | text, axes, the dashed baseline line |
| `ok-orange` | `#E69F00` | primary series / the headline condition |
| `ok-skyblue`| `#56B4E9` | second condition |
| `ok-green`  | `#009E73` | "above chance" / success encoding |
| `ok-yellow` | `#F0E442` | sparingly — low contrast on white |
| `ok-blue`   | `#0072B2` | third condition |
| `ok-vermil` | `#D55E00` | error / retracted / negative |
| `ok-purple` | `#CC79A7` | fourth condition |
| `grey-60`   | `#999999` | gridlines, secondary annotation |

Continuous data: `viridis` (default), `cividis` (CVD-optimized), or `magma`. Sequential-diverging: `RdBu` only with a declared, symmetric midpoint. Never `jet`, `rainbow`, `hsv`, `turbo`.

---

## Standard panel kinds (what `/analyze` asks figure-smith to render)

- **Per-layer / per-depth curve** — x = relative depth (0–1) for cross-model comparability (RULE-4); y = metric; one line per model; **dashed chance baseline**; CI band per line. Title states where the peak is and that it clears chance.
- **Effect-size forest plot** — one row per claim/condition; point = effect size (Cohen d / R² / bal-acc Δ), whisker = its 95% CI; a vertical dashed line at the null (d=0 / Δ=0). Reads at a glance which effects clear zero.
- **Corrected-significance panel** — for a swept grid: cells shaded by adjusted statistic (Holm/BH), N annotated, the pre-registered primary cell marked. Never an uncorrected heatmap of raw p's.
- **Null-with-power panel** — the observed effect + CI against the minimum detectable effect for the achieved N, so a *clean* null is visibly distinguished from an *underpowered* one (RULE-8).

Default canvas: a 2×2 panel grid at a 7×7 in (≈ single-column-pair) footprint; primary panel top-left. A single-panel figure is fine when one panel carries the claim — do not pad to four.

---

## Hard prohibitions (any one ⇒ `Lint: FAIL`, figure not shipped)

- `jet`, `rainbow`, `hsv`, or `turbo` colormap — anywhere.
- 3D axes / perspective bars / surface plots.
- Pie or donut charts.
- Dual / twin y-axis.
- Raster output (`.png`/`.jpg`) or an embedded bitmap inside the SVG.
- A performance panel with no dashed random/chance baseline.
- A mean or effect-size marker with no CI shown.
- A cross-model panel on a raw (un-normalized) axis (RULE-4).
- A noun-phrase or "Figure N" title instead of a declarative sentence.
- A hand-edited figure with no producing script / no `stats.json` provenance.
- An absolute path (`/home/...`, `/Users/...`) in the script or the figure metadata (RULE-2).

---

## Self-check before figure-smith returns `Lint: PASS`

For every rendered figure, verify:

1. Title is a declarative sentence stating the finding.
2. Output is vector (`.svg`/`.pdf`); no embedded raster.
3. Every axis is labeled (with units); caption names n + variation source + CI method.
4. Performance panels show a dashed random/chance baseline; means/effects carry a visible CI.
5. Colormap is colorblind-safe and perceptually uniform; readable when desaturated; no `jet/rainbow/hsv/turbo`.
6. No 3D, no pie/donut, no dual-axis; bars start at 0 (or an explicit labeled break).
7. Multi-panel figures share one scale/legend/font; primary panel top-left; series→color consistent.
8. A committed, seeded script produced it from `results/<exp>/stats.json`; no manual post-edit.
9. Every plotted value traces to a `stats.json` field; cross-model axes are normalized + named (RULE-4).
10. No absolute paths anywhere (RULE-2).

A figure that fails any check is returned `Lint: FAIL` with the violating rule numbers in `Violations:` of the `## FigureReport`; `/analyze` fixes the spec and re-dispatches — it does not overwrite the verdict (RULE-1).
