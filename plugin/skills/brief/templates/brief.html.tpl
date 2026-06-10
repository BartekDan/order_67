<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{EXP_TITLE}} — R&amp;D brief</title>
<!--
  /brief deliverable skeleton. Single self-contained file (D-006): inline CSS, CDN MathJax,
  base64-embedded figures (NO <img src> to a local file, NO <link rel=stylesheet>). A stakeholder
  must be able to open this over file:// or paste it into an email with zero dependency resolution.
  English only (D-006). Placeholders are {{UPPER_SNAKE}}; the skill body lists every substitution.
-->
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

{{PALETTE_CSS}}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter Tight', system-ui, sans-serif;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.62;
  font-size: 16px;
}

.container { max-width: 920px; margin: 0 auto; padding: 56px 36px 96px; }

/* --- masthead --- */
.masthead { border-top: 4px solid var(--ink); padding-top: 18px; margin-bottom: 40px; }
.masthead .meta {
  display: flex; flex-wrap: wrap; gap: 22px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--grey);
  padding-bottom: 18px; border-bottom: 1px dashed var(--soft-line); margin-bottom: 28px;
}
.masthead .meta b { color: var(--ink); font-weight: 500; }
.masthead h1 {
  font-family: 'Fraunces', Georgia, serif; font-weight: 500;
  font-size: clamp(32px, 5vw, 52px); line-height: 1.04; letter-spacing: -0.02em;
}
.masthead .subtitle {
  font-family: 'Fraunces', serif; font-style: italic; font-size: 19px;
  color: var(--slate); margin-top: 12px; max-width: 680px;
}

/* --- BLUF / bottom line --- */
.bluf {
  background: var(--cream); border-left: 5px solid var(--rust);
  padding: 24px 28px; margin: 36px 0 48px; font-size: 18px; line-height: 1.55;
}
.bluf .label {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--rust-dark); display: block; margin-bottom: 8px;
}

h2.section {
  font-family: 'Fraunces', serif; font-weight: 500; font-size: 27px; letter-spacing: -0.01em;
  margin: 56px 0 8px; padding-bottom: 8px; border-bottom: 1px solid var(--soft-line);
}
h2.section .num { color: var(--rust); font-variant-numeric: tabular-nums; margin-right: 10px; }
.section-lede { color: var(--grey); font-size: 14px; margin-bottom: 20px; }

p { max-width: 740px; margin-bottom: 14px; }
.q-answer { font-size: 16.5px; }

/* --- question 2: methodological grade chip --- */
.grade-row { display: flex; align-items: center; gap: 20px; margin: 8px 0 20px; flex-wrap: wrap; }
.grade-chip {
  font-family: 'Fraunces', serif; font-weight: 600; font-size: 48px; line-height: 1;
  color: var(--paper); width: 92px; height: 92px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; flex: 0 0 auto;
}
.grade-chip[data-grade^="A"] { background: var(--grade-a); }
.grade-chip[data-grade^="B"] { background: var(--grade-b); }
.grade-chip[data-grade^="C"] { background: var(--grade-c); }
.grade-chip[data-grade^="D"] { background: var(--grade-d); }
.grade-chip[data-grade^="F"] { background: var(--grade-f); }
.grade-rationale { max-width: 600px; }
.grade-rationale .gr-head { font-weight: 600; margin-bottom: 4px; }

/* --- question 3 / 4 venue & fit chips --- */
.tag {
  display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 11px;
  letter-spacing: 0.04em; padding: 3px 9px; border-radius: 4px; margin: 3px 4px 3px 0;
  background: var(--status-null-bg); color: var(--status-null);
}

/* --- finding → status → meaning table --- */
table.findings { width: 100%; border-collapse: collapse; margin: 16px 0 28px; font-size: 15px; }
table.findings th {
  text-align: left; font-family: 'JetBrains Mono', monospace; font-size: 11px;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--grey);
  border-bottom: 2px solid var(--soft-line); padding: 8px 12px; vertical-align: bottom;
}
table.findings td { padding: 12px; border-bottom: 1px solid var(--soft-line); vertical-align: top; }
table.findings td.finding { font-weight: 500; max-width: 240px; }
table.findings td.meaning { color: var(--slate); }
.status-pill {
  display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 11px;
  font-weight: 500; letter-spacing: 0.03em; padding: 4px 10px; border-radius: 12px; white-space: nowrap;
}
.status-pill[data-status="strong"] { background: var(--status-strong-bg); color: var(--status-strong); }
.status-pill[data-status="caveat"] { background: var(--status-caveat-bg); color: var(--status-caveat); }
.status-pill[data-status="weak"]   { background: var(--status-weak-bg);   color: var(--status-weak); }
.status-pill[data-status="null"]   { background: var(--status-null-bg);   color: var(--status-null); }
.effect { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--ink); }
.effect .consistency { color: var(--grey); display: block; font-size: 11px; margin-top: 3px; }

/* --- next-action list --- */
ol.actions { list-style: none; counter-reset: act; max-width: 760px; }
ol.actions li {
  counter-increment: act; position: relative; padding: 14px 16px 14px 56px;
  border-bottom: 1px solid var(--soft-line); margin-bottom: 0;
}
ol.actions li::before {
  content: counter(act); position: absolute; left: 14px; top: 14px;
  font-family: 'Fraunces', serif; font-weight: 600; font-size: 22px; color: var(--rust);
  width: 30px; text-align: center;
}
ol.actions .act-head { font-weight: 600; }
ol.actions .act-cost {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--grey);
  letter-spacing: 0.04em; margin-left: 8px;
}
ol.actions .act-body { color: var(--slate); font-size: 15px; margin-top: 3px; }

/* --- callouts: DEFINITION / CHECKPOINT / HONEST-CAVEAT --- */
.callout { border-radius: 6px; padding: 16px 20px; margin: 20px 0; font-size: 15px; }
.callout .ctag {
  font-family: 'JetBrains Mono', monospace; font-size: 10.5px; font-weight: 500;
  letter-spacing: 0.14em; text-transform: uppercase; display: block; margin-bottom: 6px;
}
.callout.definition { background: var(--cream); border-left: 4px solid var(--teal); }
.callout.definition .ctag { color: var(--teal); }
.callout.checkpoint { background: var(--status-caveat-bg); border-left: 4px solid var(--ochre); }
.callout.checkpoint .ctag { color: var(--status-caveat); }
.callout.honest { background: var(--status-weak-bg); border-left: 4px solid var(--status-weak); }
.callout.honest .ctag { color: var(--status-weak); }

/* --- pushback handbook --- */
.pushback { margin-top: 12px; }
.objection {
  border: 1px solid var(--soft-line); border-radius: 6px; margin-bottom: 16px; overflow: hidden;
}
.objection .obj-q {
  background: var(--cream); padding: 14px 18px; font-weight: 600; color: var(--slate);
  border-bottom: 1px solid var(--soft-line);
}
.objection .obj-q::before {
  content: "Objection"; font-family: 'JetBrains Mono', monospace; font-size: 10px;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--rust); display: block; margin-bottom: 4px;
}
.objection .obj-a { padding: 14px 18px; }
.objection .obj-a::before {
  content: "Rebuttal"; font-family: 'JetBrains Mono', monospace; font-size: 10px;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--olive); display: block; margin-bottom: 4px;
}
.closing-argument {
  background: var(--cream); border-top: 3px solid var(--ink); padding: 22px 24px; margin-top: 28px;
  font-family: 'Fraunces', serif; font-size: 17px; line-height: 1.5; color: var(--ink);
}
.closing-argument .label {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--grey); display: block; margin-bottom: 8px;
}

/* --- figures (base64-embedded) --- */
figure { margin: 24px 0; }
figure img { display: block; max-width: 100%; height: auto; border: 1px solid var(--soft-line); }
figure figcaption { font-size: 13px; color: var(--grey); margin-top: 8px; font-style: italic; }

code {
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  background: var(--cream); color: var(--rust-dark); padding: 1px 5px; border-radius: 3px;
}

footer.brief-footer {
  margin-top: 72px; padding-top: 20px; border-top: 1px solid var(--soft-line);
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--grey);
  letter-spacing: 0.06em; line-height: 1.8;
}
footer.brief-footer .disclaimer { text-transform: none; letter-spacing: 0; font-size: 11.5px; margin-top: 6px; }
</style>
<!-- MathJax via CDN (D-006 permits CDN for math rendering; figures are base64, not CDN). -->
<script>
window.MathJax = { tex: { inlineMath: [['\\(', '\\)']], displayMath: [['$$', '$$']] } };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
</head>
<body>
<div class="container">

  <header class="masthead">
    <div class="meta">
      <span><b>Experiment</b> {{EXP_ID}}</span>
      <span><b>Rigor tier</b> {{RIGOR_TIER}}</span>
      <span><b>Verdict</b> {{VERDICT}}</span>
      <span><b>Generated</b> {{GENERATED_AT}}</span>
      <span><b>Audience</b> R&amp;D management</span>
    </div>
    <h1>{{EXP_TITLE}}</h1>
    <p class="subtitle">{{EXP_SUBTITLE}}</p>
  </header>

  <!-- ============ BLUF / bottom line (single Minto top paragraph) ============ -->
  <section class="bluf">
    <span class="label">Bottom line up front</span>
    {{BLUF_PARAGRAPH}}
  </section>

  <!-- ============ The fixed FOUR questions ============ -->

  <h2 class="section"><span class="num">1.</span>What was done?</h2>
  <p class="section-lede">In plain terms, for someone who was not in the room.</p>
  <div class="q-answer">{{Q1_WHAT_WAS_DONE}}</div>

  <h2 class="section"><span class="num">2.</span>Is it methodologically sound?</h2>
  <p class="section-lede">A letter grade for how much the result can be trusted, and why.</p>
  <div class="grade-row">
    <div class="grade-chip" data-grade="{{GRADE}}">{{GRADE}}</div>
    <div class="grade-rationale">
      <div class="gr-head">Grade {{GRADE}} — {{GRADE_HEADLINE}}</div>
      {{GRADE_RATIONALE}}
    </div>
  </div>

  <h2 class="section"><span class="num">3.</span>What is its scientific value?</h2>
  <p class="section-lede">Is this publishable, and if so, where?</p>
  <div class="q-answer">{{Q3_SCIENTIFIC_VALUE}}</div>
  <p>{{Q3_VENUE_TAGS}}</p>

  <h2 class="section"><span class="num">4.</span>Is it marketable / does it fit a product?</h2>
  <p class="section-lede">Honest read on commercial and internal-tooling fit.</p>
  <div class="q-answer">{{Q4_PRODUCT_FIT}}</div>

  <!-- ============ finding → status → meaning ============ -->
  <h2 class="section">Findings at a glance</h2>
  <p class="section-lede">Each row reports effect-size magnitude AND consistency across seeds/splits — never significance alone (RULE-7).</p>
  <table class="findings">
    <thead>
      <tr><th>Finding</th><th>Effect (magnitude &amp; spread)</th><th>Status</th><th>What it means</th></tr>
    </thead>
    <tbody>
      {{FINDINGS_ROWS}}
    </tbody>
  </table>

  <!-- ============ priority-ordered next actions ============ -->
  <h2 class="section">What to do next</h2>
  <p class="section-lede">Priority order. Each line names the decision it unblocks and its rough cost.</p>
  <ol class="actions">
    {{NEXT_ACTIONS}}
  </ol>

  <!-- ============ callouts (zero or more of each) ============ -->
  {{CALLOUTS}}

  <!-- ============ pushback handbook ============ -->
  <h2 class="section">Pushback handbook</h2>
  <p class="section-lede">The objections a sharp methodologist will raise, and the verbatim answer to each.</p>
  <div class="pushback">
    {{PUSHBACK_OBJECTIONS}}
    <div class="closing-argument">
      <span class="label">Closing argument</span>
      {{CLOSING_ARGUMENT}}
    </div>
  </div>

  <footer class="brief-footer">
    Generated by <code>/brief {{EXP_ID}}</code> &middot; order-67 research harness &middot; rigor tier: {{RIGOR_TIER}}
    <div class="disclaimer">{{PROVENANCE_LINE}}</div>
  </footer>

</div>
</body>
</html>
