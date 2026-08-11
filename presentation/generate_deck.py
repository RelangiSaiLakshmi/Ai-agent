"""Generate the project demo deck (PowerPoint) — CONDENSED 12-slide edition —
for the AI Agent Coordination & Decision Engine (Leave Approval System).

Every slide is grounded in the actual codebase (agents/, tools/, llm/,
workflows/, database/). Run:

    pip install python-pptx
    python presentation/generate_deck.py

Output: presentation/AI_Leave_Approval_Demo.pptx
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

# ── Theme ────────────────────────────────────────────────────────────────────
NAVY = RGBColor(0x0B, 0x1F, 0x3A)
INK = RGBColor(0x16, 0x21, 0x30)
SLATE = RGBColor(0x5B, 0x6B, 0x7F)
TEAL = RGBColor(0x17, 0xB0, 0x9A)
BLUE = RGBColor(0x2E, 0x6C, 0xF6)
AMBER = RGBColor(0xF2, 0xA9, 0x1B)
RED = RGBColor(0xE4, 0x57, 0x4E)
CLOUD = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xD4, 0xDD, 0xE8)
CHIP = RGBColor(0xE7, 0xED, 0xF6)

FONT = "Calibri"
FONT_H = "Calibri"

EMU_W = Emu(12192000)
EMU_H = Emu(6858000)
SW = 13.333
SH = 7.5

prs = Presentation()
prs.slide_width = EMU_W
prs.slide_height = EMU_H
BLANK = prs.slide_layouts[6]


# ── Low-level helpers ────────────────────────────────────────────────────────
def slide():
    return prs.slides.add_slide(BLANK)


def _set_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def _no_line(shape):
    shape.line.fill.background()


def _line(shape, color, w=1.0):
    shape.line.color.rgb = color
    shape.line.width = Pt(w)


def Inches(v):
    return Emu(int(v * 914400))


def bg(s, color=WHITE):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, EMU_W, EMU_H)
    _set_fill(r, color)
    _no_line(r)
    r.shadow.inherit = False
    return r


def rect(s, x, y, w, h, color=None, shape=MSO_SHAPE.RECTANGLE,
         line_color=None, line_w=1.0):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if color is None:
        sp.fill.background()
    else:
        _set_fill(sp, color)
    if line_color is None:
        _no_line(sp)
    else:
        _line(sp, line_color, line_w)
    return sp


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    first = True
    for para in runs:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        if isinstance(para, str):
            para = [(para, {})]
        popts = para[0][1] if para and isinstance(para[0], tuple) else {}
        if "space_before" in popts:
            p.space_before = Pt(popts["space_before"])
        if "space_after" in popts:
            p.space_after = Pt(popts["space_after"])
        if "line" in popts:
            p.line_spacing = popts["line"]
        for frag in para:
            t, o = frag
            run = p.add_run()
            run.text = t
            run.font.size = Pt(o.get("size", 18))
            run.font.bold = o.get("bold", False)
            run.font.italic = o.get("italic", False)
            run.font.name = o.get("font", FONT)
            run.font.color.rgb = o.get("color", INK)
    return tb


def bullets(s, x, y, w, h, items, size=17, color=INK, gap=8, marker="•",
            marker_color=TEAL, line=1.12):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    first = True
    for it in items:
        level = 0
        opts = {}
        if isinstance(it, tuple):
            txt = it[0]
            if len(it) > 1:
                level = it[1]
            if len(it) > 2:
                opts = it[2]
        else:
            txt = it
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        p.line_spacing = line
        m = marker if level == 0 else "–"
        mc = marker_color if level == 0 else SLATE
        indent = "" if level == 0 else "   "
        r0 = p.add_run()
        r0.text = f"{indent}{m}  "
        r0.font.size = Pt(size)
        r0.font.name = FONT
        r0.font.bold = True
        r0.font.color.rgb = opts.get("marker_color", mc)
        if opts.get("lead"):
            rb = p.add_run()
            rb.text = opts["lead"]
            rb.font.size = Pt(size)
            rb.font.name = FONT
            rb.font.bold = True
            rb.font.color.rgb = opts.get("lead_color", INK)
        r1 = p.add_run()
        r1.text = txt
        r1.font.size = Pt(opts.get("size", size))
        r1.font.name = FONT
        r1.font.color.rgb = opts.get("color", color)
        r1.font.bold = opts.get("bold", False)
    return tb


def chip(s, x, y, w, h, label, fill=CHIP, fg=NAVY, size=12, bold=True,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    c = rect(s, x, y, w, h, fill, shape=shape)
    try:
        c.adjustments[0] = 0.5
    except Exception:
        pass
    text(s, x + 0.05, y, w - 0.1, h, [[(label, {"size": size, "bold": bold,
         "color": fg, "font": FONT})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return c


def box(s, x, y, w, h, title, sub=None, fill=CLOUD, accent=BLUE, tsize=13,
        ssize=10.5, title_color=None, rounded=True):
    shp = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    b = rect(s, x, y, w, h, fill, shape=shp, line_color=LINE, line_w=1.0)
    if rounded:
        try:
            b.adjustments[0] = 0.08
        except Exception:
            pass
    rect(s, x, y, w, 0.09, accent, shape=MSO_SHAPE.RECTANGLE)
    runs = [[(title, {"size": tsize, "bold": True, "color": title_color or NAVY, "font": FONT})]]
    if sub:
        runs.append([(sub, {"size": ssize, "color": SLATE, "font": FONT,
                            "space_before": 3, "line": 1.05})])
    text(s, x + 0.14, y + 0.14, w - 0.28, h - 0.24, runs, anchor=MSO_ANCHOR.TOP)
    return b


def connector(s, x1, y1, x2, y2, color=SLATE, w=1.6, dash=False):
    ln = s.shapes.add_connector(2, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = color
    ln.line.width = Pt(w)
    if dash:
        d = ln.line._get_or_add_ln()
        pd = d.makeelement(qn('a:prstDash'), {'val': 'dash'})
        d.append(pd)
    ln.shadow.inherit = False
    return ln


def notes(s, txt):
    s.notes_slide.notes_text_frame.text = txt.strip()


PAGE = 0


def header(s, kicker, title):
    global PAGE
    PAGE += 1
    bg(s, WHITE)
    rect(s, 0, 0, 0.22, SH, NAVY)
    rect(s, 0, 0, 0.22, 2.2, TEAL)
    text(s, 0.62, 0.42, 11.5, 0.35,
         [[(kicker.upper(), {"size": 12.5, "bold": True, "color": TEAL, "font": FONT})]])
    text(s, 0.6, 0.72, 11.6, 0.9,
         [[(title, {"size": 29, "bold": True, "color": NAVY, "font": FONT_H})]])
    rect(s, 0.62, 1.48, 1.5, 0.045, TEAL)
    text(s, 12.2, 6.95, 0.9, 0.35,
         [[(f"{PAGE:02d}", {"size": 11, "color": SLATE, "bold": True})]], align=PP_ALIGN.RIGHT)
    text(s, 0.62, 6.95, 9, 0.35,
         [[("AI Agent Coordination & Decision Engine — Leave Approval System",
            {"size": 9.5, "color": SLATE})]])
    return s


def new(kicker, title):
    s = slide()
    header(s, kicker, title)
    return s


# =============================================================================
# SLIDE 1 — TITLE
# =============================================================================
s = slide()
bg(s, NAVY)
rect(s, 8.7, 0, 4.63, SH, RGBColor(0x0E, 0x28, 0x4C))
rect(s, 0, 6.7, SW, 0.8, RGBColor(0x0E, 0x28, 0x4C))
node_cx = [9.35, 10.35, 11.35, 12.35]
for i, cx in enumerate(node_cx):
    col = [TEAL, BLUE, AMBER, TEAL][i]
    rect(s, cx, 2.9, 0.5, 0.5, col, shape=MSO_SHAPE.OVAL)
for i in range(len(node_cx) - 1):
    connector(s, node_cx[i] + 0.5, 3.15, node_cx[i + 1], 3.15, RGBColor(0x3A, 0x5A, 0x82), 2.2)
chip(s, 0.9, 1.15, 3.5, 0.5, "MILESTONE 1 + 2  ·  DEMO",
     fill=RGBColor(0x12, 0x33, 0x5B), fg=TEAL, size=12.5)
text(s, 0.9, 2.0, 8.0, 2.2, [
    [("AI Agent Coordination", {"size": 46, "bold": True, "color": WHITE, "font": FONT_H})],
    [("& Decision Engine", {"size": 46, "bold": True, "color": WHITE, "font": FONT_H, "space_before": 2})],
])
rect(s, 0.95, 4.15, 1.7, 0.05, TEAL)
text(s, 0.9, 4.35, 8.2, 1.0, [
    [("A multi-agent AI system that processes employee leave requests",
      {"size": 18, "color": RGBColor(0xC7, 0xD4, 0xE6)})],
    [("end to end — Approve · Reject · Escalate.",
      {"size": 18, "color": RGBColor(0xC7, 0xD4, 0xE6), "space_before": 2})],
])
text(s, 0.9, 5.75, 9, 0.8, [
    [("Built on LangChain", {"size": 14, "bold": True, "color": TEAL}),
     ("   ·   7 specialized agents   ·   native tool-calling   ·   runs fully offline",
      {"size": 14, "color": RGBColor(0x9F, 0xB2, 0xCC)})],
])
text(s, 0.9, 6.85, 11.5, 0.5, [
    [("Presenter: _______________", {"size": 11, "color": RGBColor(0x7E, 0x92, 0xAE)}),
     ("        Date: 23 July 2026", {"size": 11, "color": RGBColor(0x7E, 0x92, 0xAE)})],
])
notes(s, """
Good [morning/afternoon] everyone. This is the AI Agent Coordination & Decision Engine — an intelligent Leave Approval System.

In one sentence: it takes an employee's leave request and, just like a real HR team, checks the policy, the balances, and the eligibility, then automatically Approves it, Rejects it, or Escalates it to a manager — and finally writes a professional reply to the employee.

Three things to remember: it's built on LangChain, it uses seven specialized agents that collaborate, and it runs fully offline for this demo through a deterministic mock model, with a one-line switch to real Claude. Over the next ~12 minutes I'll cover the problem, the architecture and agents, the tooling, a live demo, and the roadmap. Let's start with the problem.
""")

# =============================================================================
# SLIDE 2 — PROBLEM & OVERVIEW
# =============================================================================
s = new("Problem & Solution", "Why leave approval needs more than one prompt")
bullets(s, 0.62, 1.85, 5.9, 2.3, [
    ("Manual & slow, inconsistent between approvers, error-prone (balances, notice, overlaps), and opaque to employees.", 0, {}),
    ("Naïve fix — one LLM prompt that \"just decides\" — is a black box: it can hallucinate rules, can't be audited, and can't be trusted with the HR database.", 0, {}),
], size=14.5, gap=10)
box(s, 6.7, 1.8, 6.0, 2.35, "We need decisions that are…", None, fill=CLOUD, accent=RED)
text(s, 6.95, 2.35, 5.5, 1.7, [
    [("✓ Automated", {"size": 14, "bold": True, "color": TEAL}), ("   no waiting on a person", {"size": 12, "color": SLATE}),
     ("      ✓ Auditable", {"size": 14, "bold": True, "color": TEAL}), ("   traceable", {"size": 12, "color": SLATE})],
    [("✓ Grounded", {"size": 14, "bold": True, "color": TEAL, "space_before": 8}), ("   in real data, not prose", {"size": 12, "color": SLATE}),
     ("      ✓ Safe", {"size": 14, "bold": True, "color": TEAL}), ("   least-privilege", {"size": 12, "color": SLATE})],
    [("A single \"do-everything\" prompt gives none of these four.",
      {"size": 12, "italic": True, "color": SLATE, "space_before": 12})],
])
# Our solution pipeline
text(s, 0.62, 4.35, 12, 0.4, [
    [("Our solution:  ", {"size": 15, "bold": True, "color": NAVY}),
     ("a team of 7 single-purpose agents on an assembly line, sharing one state object.", {"size": 15, "color": INK})],
])
box(s, 0.62, 4.95, 2.1, 1.15, "Leave Request", "employee · type · dates", fill=NAVY, accent=TEAL, title_color=WHITE, tsize=12, ssize=9.5)
connector(s, 2.72, 5.52, 3.05, 5.52, SLATE, 2.2)
mini = ["Coordinator", "Policy", "Employee\nData", "Analysis", "Decision", "Notify", "Responder"]
cols = [BLUE, BLUE, BLUE, BLUE, AMBER, TEAL, TEAL]
x = 3.1
for i, (label, c) in enumerate(zip(mini, cols)):
    box(s, x, 4.98, 1.18, 1.1, label.replace("\n", " "), None, fill=CLOUD, accent=c, tsize=9.8)
    if i < len(mini) - 1:
        connector(s, x + 1.18, 5.52, x + 1.3, 5.52, LINE, 1.8)
    x += 1.3
text(s, 0.62, 6.35, 12, 0.4, [
    [("Outcome: ", {"size": 12, "bold": True, "color": NAVY}),
     ("APPROVE", {"size": 12, "bold": True, "color": TEAL}), ("  ·  ", {"size": 12, "color": SLATE}),
     ("REJECT", {"size": 12, "bold": True, "color": RED}), ("  ·  ", {"size": 12, "color": SLATE}),
     ("ESCALATE", {"size": 12, "bold": True, "color": AMBER}),
     ("  — each with a confidence score and a full, logged [agent] trace.", {"size": 12, "color": SLATE})],
])
notes(s, """
Leave approval sounds trivial but hides a lot of rules. Today it's manual and slow, inconsistent between approvers, error-prone — it's genuinely easy to miss a balance, a notice period, or an overlap — and opaque to the employee.

The tempting fix is "just let an LLM decide." But that's a black box: it can invent rules, you can't audit it, and you don't want to give a raw model write-access to HR data. So — top right — the real requirement is decisions that are automated AND auditable AND grounded AND safe, all four. A single do-everything prompt gives you none of them.

Our solution, at the bottom, is the whole system in one line: instead of one giant prompt, a team of seven single-purpose agents on an assembly line. A request comes in on the left; it flows through Coordinator, Policy, Employee-Data, Analysis, Decision, Notification, and Responder; and out comes an Approve, Reject, or Escalate — each with a confidence score and a complete logged trace. That shape is what satisfies all four requirements, and it's what the rest of the talk unpacks.
""")

# =============================================================================
# SLIDE 3 — OBJECTIVES & KEY FEATURES
# =============================================================================
s = new("Objectives & Features", "What we built, and what it does")
feats = [
    ("7 collaborating agents", "One job each; uniform run(state) → state contract.", TEAL),
    ("Native tool-calling (M2)", "Policy & Employee-Data hand read tools to the LLM, which selects & invokes them.", BLUE),
    ("Auditable Decision Engine", "Config-free rule ladder → outcome + confidence + per-criterion pass/fail.", AMBER),
    ("Grounded, never invented", "State built from recorded tool results — model prose is never trusted as fact.", BLUE),
    ("Safe by construction", "Least privilege: only read tools exposed; writes stay behind trusted agents.", RED),
    ("Enterprise API connector", "Holiday calendar via a swappable transport (offline JSON → HTTP, no agent changes).", BLUE),
    ("Graceful degradation", "Tool errors, unknown tools & skipped calls are recovered — never crashes.", RED),
    ("Offline-first & tested", "Runs with no API key via a deterministic mock LLM; 29 tests passing.", TEAL),
]
x0, y0, cw, ch, gx, gy = 0.62, 1.9, 5.97, 1.12, 0.16, 0.14
for i, (t, b, c) in enumerate(feats):
    cx = x0 + (i % 2) * (cw + gx)
    cy = y0 + (i // 2) * (ch + gy)
    rect(s, cx, cy, cw, ch, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, cx, cy, 0.11, ch, c)
    text(s, cx + 0.32, cy + 0.12, cw - 0.5, ch - 0.2, [
        [(t, {"size": 13.5, "bold": True, "color": NAVY})],
        [(b, {"size": 10.6, "color": SLATE, "space_before": 2, "line": 1.02})],
    ], anchor=MSO_ANCHOR.MIDDLE)
notes(s, """
These eight tiles are both our objectives and the features that deliver them — objectives on the left of each pair, essentially, and the "how" underneath.

Seven collaborating agents, each with one job and the same run(state) contract. Native tool-calling, added in Milestone 2 — the data agents hand their read tools to the model and let it choose. An auditable Decision Engine that outputs an outcome, a confidence, and a pass/fail for every criterion.

Then the safety-and-trust group: grounded, never invented — state comes only from recorded tool results, never the model's prose. Safe by construction — least privilege, only read tools are exposed, writes stay behind trusted code. An enterprise connector for the holiday calendar behind a swappable transport. Graceful degradation so a failing tool never crashes the run. And offline-first and tested — it runs with no API key at all, backed by 29 passing tests.

I'll show several of these in action. Let's look at the architecture that holds it together.
""")

# =============================================================================
# SLIDE 4 — ARCHITECTURE & TECH STACK
# =============================================================================
s = new("Architecture & Stack", "Layered — with the model boxed in")
layers = [
    ("Interface", "main.py CLI  ·  (planned: FastAPI · Streamlit)", RGBColor(0x24, 0x3B, 0x5E)),
    ("Orchestration", "workflows/pipeline.py — sequential runner  ·  (LangGraph → M4)", BLUE),
    ("Agents", "Coordinator · Policy · Employee-Data · Analysis · Decision · Notification · Responder", TEAL),
    ("Reasoning / LLM", "BaseLLM · run_with_tools loop · MockLLM / Claude · prompts registry", AMBER),
    ("Tools & Connectors", "@tool schemas (read-only to model) · leave_tools · Holiday connector", BLUE),
    ("Data", "SQLite — employees · leave_balances · leave_requests · decisions · policy_rules", RGBColor(0x24, 0x3B, 0x5E)),
]
y = 1.85
h = 0.66
for i, (title, sub, c) in enumerate(layers):
    rect(s, 0.62, y, 9.0, h, WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, 0.62, y, 0.14, h, c)
    text(s, 0.95, y, 3.0, h, [[(title, {"size": 13, "bold": True, "color": NAVY})]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 3.15, y, 6.3, h, [[(sub, {"size": 10, "color": SLATE, "line": 1.0})]], anchor=MSO_ANCHOR.MIDDLE)
    if i < len(layers) - 1:
        connector(s, 5.12, y + h, 5.12, y + h + 0.09, LINE, 1.4)
    y += h + 0.09
rect(s, 9.9, 1.85, 2.82, y - 1.85 - 0.09, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=TEAL, line_w=1.5)
text(s, 10.05, 2.0, 2.55, 4.4, [
    [("SHARED STATE", {"size": 11.5, "bold": True, "color": TEAL})],
    [("LeaveState", {"size": 13, "bold": True, "color": NAVY, "font": "Consolas", "space_before": 5})],
    [("flows through every layer", {"size": 10, "color": SLATE, "space_before": 4, "line": 1.05})],
    [("request → policy →", {"size": 9.5, "color": SLATE, "font": "Consolas", "space_before": 8, "line": 1.15})],
    [("balance → analysis →", {"size": 9.5, "color": SLATE, "font": "Consolas", "line": 1.15})],
    [("decision → response", {"size": 9.5, "color": SLATE, "font": "Consolas", "line": 1.15})],
    [("+ status + logs[]", {"size": 9.5, "color": NAVY, "font": "Consolas", "space_before": 6})],
])
# tech chips
text(s, 0.62, 6.35, 2.0, 0.4, [[("Stack:", {"size": 12, "bold": True, "color": NAVY})]])
techs = ["Python 3.12", "LangChain", "LangGraph (M4)", "Claude / Mock", "SQLite", "pytest ×29"]
x = 1.55
for t in techs:
    w = 0.3 + len(t) * 0.1
    chip(s, x, 6.32, w, 0.42, t, fill=CHIP, fg=NAVY, size=10.5)
    x += w + 0.18
notes(s, """
Here's the architecture as six clean layers, and the key thing is where the language model sits.

Top to bottom: the interface — today the command-line harness, later FastAPI and Streamlit. Orchestration — pipeline.py, which runs the agents in order and later becomes a LangGraph graph. The agents themselves. Then the reasoning layer — the model interface, the tool-loop, the two providers, the prompts. Below that the tools and connectors — and this is the important boundary, the model only ever sees read-only tools here. And at the bottom, the data layer: SQLite with five tables.

Running vertically on the right is the LeaveState — not a layer, but the object that flows through all of them, getting enriched at each step: request, policy, balance, analysis, decision, response, carrying a status and a growing log the whole way.

The single most important design decision: the LLM is boxed inside the reasoning layer and only reaches data through read-only tools. It never touches the database directly and never writes.

And the stack, along the bottom: Python 3.12, LangChain today with LangGraph planned for M4, Claude or the offline mock, SQLite, and 29 pytest tests. Now the agents themselves.
""")

# =============================================================================
# SLIDE 5 — THE 7 AGENTS
# =============================================================================
s = new("The Agents", "Seven specialists, one job each — why each exists")
agents = [
    ("1  Coordinator", "Validates the request, assigns an ID, persists it, plans the sequence.", "one entry point; guarantees order & a durable record", BLUE),
    ("2  Policy", "Fetches the rules for the leave type (max days, notice, docs, manager-req).", "decisions must be grounded in real policy", TEAL),
    ("3  Employee-Data", "Retrieves the employee record, leave balance, and overlapping requests.", "supplies the facts the decision is measured against", TEAL),
    ("4  Analysis", "Turns policy + data into boolean eligibility signals + flags. Decides nothing.", "separating assessment from decision keeps both auditable", BLUE),
    ("5  Decision", "The engine — APPROVE / REJECT / ESCALATE with confidence + rationale.", "a single, transparent place where the outcome is made", AMBER),
    ("6  Notification", "Persists the decision, sets status, (mock) notifies employee & manager.", "the ONLY agent with DB write access (least privilege)", RED),
    ("7  Responder", "Composes the final message; LLM polishes the grounded draft.", "closes the loop with a courteous, human reply", TEAL),
]
x0, y0, cw, ch, gx, gy = 0.62, 1.85, 5.97, 1.28, 0.16, 0.13
for i, (title, body, why, c) in enumerate(agents):
    cx = x0 + (i % 2) * (cw + gx)
    cy = y0 + (i // 2) * (ch + gy)
    rect(s, cx, cy, cw, ch, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, cx, cy, 0.13, ch, c)
    text(s, cx + 0.3, cy + 0.11, cw - 0.45, ch - 0.2, [
        [(title, {"size": 13, "bold": True, "color": NAVY})],
        [(body, {"size": 10.4, "color": INK, "space_before": 2, "line": 1.0})],
        [("Why: ", {"size": 9.8, "italic": True, "bold": True, "color": c}),
         (why, {"size": 9.8, "italic": True, "color": c, "line": 1.0})],
    ])
box(s, 6.75, 6.55, 5.85, 0.75, "Uniform contract: every agent is  run(state) → state",
    "→ sequence them today, drop them into a LangGraph node tomorrow.", fill=NAVY, accent=TEAL,
    title_color=WHITE, tsize=12, ssize=10)
notes(s, """
This is the heart of the system. Each agent has a single job and a reason it exists — that's the "Why" line on each card.

The Coordinator is the front door: it validates the dates, stamps a request ID, persists the request, and lays out the plan. Policy fetches the actual rules. Employee-Data pulls the record, the balance, and any overlapping leave — the facts.

Analysis is subtle but important: it turns policy plus data into pure boolean signals — balance ok, notice ok, no overlap, within max — and decides nothing. That separation is exactly why the Decision agent, number five, can have one clean job: read the signals, output Approve, Reject, or Escalate with a confidence and rationale.

Notification is the only agent allowed to write to the database — that's our least-privilege boundary in action. And the Responder writes the final courteous message.

The bar at the bottom ties it together: every agent is the same contract, run(state) returns state. That uniformity is why we can sequence them now and drop them into a LangGraph graph later without rewriting them. So how do they actually talk to each other?
""")

# =============================================================================
# SLIDE 6 — COMMUNICATION & END-TO-END FLOW
# =============================================================================
s = new("Communication & Flow", "A shared 'blackboard' + the end-to-end trace")
# left: blackboard
text(s, 0.62, 1.8, 6, 0.7, [
    [("Agents don't call each other.", {"size": 14.5, "bold": True, "color": NAVY})],
    [("They read & write one shared ", {"size": 12.5, "color": INK}),
     ("LeaveState", {"size": 12.5, "color": NAVY, "font": "Consolas"}),
     (" — the blackboard pattern. The orchestrator sequences; the state carries context.",
      {"size": 12.5, "color": INK})],
])
rect(s, 1.9, 3.15, 2.4, 1.15, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, 1.9, 3.15, 2.4, 1.15, [
    [("LeaveState", {"size": 14, "bold": True, "color": WHITE, "font": "Consolas"})],
    [("shared blackboard", {"size": 9.5, "color": RGBColor(0x9F, 0xB2, 0xCC), "space_before": 3})],
    [("+ status + logs[]", {"size": 9, "color": TEAL, "font": "Consolas", "space_before": 2})],
], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
around = [
    ("Policy → policy", 0.62, 4.65, TEAL),
    ("Emp-Data → employee, balance", 0.62, 5.4, TEAL),
    ("Analysis → signals", 3.5, 4.65, AMBER),
    ("Decision → outcome", 3.5, 5.4, AMBER),
]
for label, x, y, c in around:
    box(s, x, y, 2.75, 0.62, label, None, fill=CLOUD, accent=c, tsize=10.5)
    connector(s, x + 1.35, y, 3.1, 4.3, LINE, 1.4)
text(s, 0.62, 6.2, 6, 0.9, [
    [("Loose coupling", {"size": 11.5, "bold": True, "color": NAVY}),
     (" — add/reorder an agent without touching others.", {"size": 11, "color": SLATE})],
    [("Auditability", {"size": 11.5, "bold": True, "color": NAVY, "space_before": 3}),
     (" — the final state is a replayable record.", {"size": 11, "color": SLATE})],
])
# right: end-to-end numbered flow
rect(s, 6.95, 1.75, 5.75, 5.55, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
text(s, 7.2, 1.9, 5.3, 0.4, [[("End-to-end run", {"size": 13, "bold": True, "color": NAVY})]])
stages = [
    ("1", "Coordinator", "validate · assign ID · persist · plan", BLUE),
    ("2", "Policy", "LLM calls get_policy → grounded rules", TEAL),
    ("3", "Employee-Data", "LLM calls 3 tools → record, balance, overlaps", TEAL),
    ("4", "Analysis", "booleans + flags · check holiday connector", BLUE),
    ("5", "Decision", "rule ladder → outcome + confidence", AMBER),
    ("6", "Notification", "persist decision · set status · notify", RED),
    ("7", "Responder", "compose + LLM-polish final message", TEAL),
]
y = 2.4
for i, (n, name, desc, c) in enumerate(stages):
    rect(s, 7.2, y, 0.5, 0.5, c, shape=MSO_SHAPE.OVAL)
    text(s, 7.2, y, 0.5, 0.5, [[(n, {"size": 13, "bold": True, "color": WHITE})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 7.85, y - 0.02, 4.7, 0.56, [
        [(name + "  ", {"size": 11.5, "bold": True, "color": NAVY}),
         (desc, {"size": 9.8, "color": SLATE, "font": "Consolas"})],
    ], anchor=MSO_ANCHOR.MIDDLE)
    if i < len(stages) - 1:
        connector(s, 7.45, y + 0.5, 7.45, y + 0.62, c, 1.6)
    y += 0.62
text(s, 7.2, y + 0.02, 5.3, 0.4, [
    [("Short-circuit: ", {"size": 9.8, "bold": True, "color": NAVY}),
     ("any step marking FAILED halts the pipeline.", {"size": 9.8, "color": SLATE})],
])
notes(s, """
This slide answers two questions at once: how the agents communicate, and what a full run looks like.

On the left — communication. The agents don't call each other; that's deliberate. They all read and write one shared object, the LeaveState, in the middle. In computer-science terms this is the blackboard pattern — everyone works against common shared memory instead of point-to-point messages. Policy writes the policy, Employee-Data writes the record and balance, Analysis writes the signals, Decision writes the outcome. The orchestrator decides the order; the state carries the context. Two payoffs: loose coupling — I can add or reorder an agent without any other agent knowing — and auditability, because the final state, with its status and log, is a complete replayable record.

On the right — the same thing as an end-to-end run, which is exactly what you'll see in the demo. Coordinator validates and persists; Policy and Employee-Data use the LLM to call their tools; Analysis computes the booleans and checks the holiday connector; Decision applies the rule ladder; Notification persists and flips the status; Responder writes the reply. And if any step marks the state FAILED — say an invalid date range — the pipeline halts immediately. Now the Milestone 2 upgrade that made the data agents genuinely intelligent.
""")

# =============================================================================
# SLIDE 7 — TOOL INTEGRATION & RELIABILITY (M2)
# =============================================================================
s = new("Tool Integration  ·  M2", "The model calls the tools — safely")
text(s, 0.62, 1.75, 12.1, 0.5, [
    [("Policy & Employee-Data hand their ", {"size": 14, "color": INK}),
     ("read tools", {"size": 14, "bold": True, "color": NAVY}),
     (" to the LLM. It decides which to call; the loop executes them and feeds results back.", {"size": 14, "color": INK})],
])
steps = [
    ("Agent", "run_with_tools(...)", NAVY),
    ("LLM turn", "emits tool_calls", BLUE),
    ("Execute", "tool.invoke → record", TEAL),
    ("Feed back", "result / ERROR → model", AMBER),
]
x = 0.62
for i, (t, sub, c) in enumerate(steps):
    rect(s, x, 2.4, 2.75, 1.0, c, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, x + 0.14, 2.48, 2.5, 0.85, [
        [(t, {"size": 12.5, "bold": True, "color": WHITE})],
        [(sub, {"size": 9.3, "color": RGBColor(0xDD, 0xE6, 0xF2), "font": "Consolas", "space_before": 2})],
    ], anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        connector(s, x + 2.75, 2.9, x + 2.98, 2.9, SLATE, 2.2)
    x += 2.98
connector(s, 11.55, 3.4, 11.55, 3.75, SLATE, 2.0)
connector(s, 11.55, 3.75, 2.0, 3.75, SLATE, 2.0, dash=True)
connector(s, 2.0, 3.75, 2.0, 3.4, SLATE, 2.0)
text(s, 3.5, 3.78, 7, 0.3, [[("repeat until the model answers in text (bounded by max_iterations = 8)",
     {"size": 10, "italic": True, "color": SLATE})]], align=PP_ALIGN.CENTER)
# reliability columns
rel = [
    ("Intelligent selection", "Model picks tools natively; the mock reproduces the same loop deterministically.", BLUE),
    ("Grounded + validated", "State built from recorded results; each checked vs. the request (right employee/policy).", TEAL),
    ("Fails safe", "Tool errors → ERROR to model; unknown tools rejected; skipped tools re-fetched directly.", RED),
]
x = 0.62
for t, b, c in rel:
    box(s, x, 4.35, 3.95, 2.15, t, None, fill=CLOUD, accent=c)
    text(s, x + 0.2, 4.95, 3.6, 1.4, [[(b, {"size": 11.5, "color": SLATE, "line": 1.12})]])
    x += 4.06
text(s, 0.62, 6.7, 12, 0.4, [
    [("Philosophy: ", {"size": 12, "bold": True, "color": NAVY}),
     ("the model is an optimizer, not a single point of failure — primary path, validation, fallback.",
      {"size": 12, "italic": True, "color": SLATE})],
])
notes(s, """
This is the Milestone 2 upgrade — the difference between "code that calls a database" and "an agent that reasons about what data it needs."

Before, the data agent hard-coded its calls. Now it hands the read tools to the LLM and lets it choose. Follow the loop across the top: the agent calls run_with_tools; the model emits structured tool calls; we execute each one and record the result; we feed the result — or an error — back to the model; and it repeats until it answers in plain text, bounded to eight iterations so it can never loop forever.

The three columns are what make this safe rather than scary. Intelligent selection — and crucially the offline mock reproduces the exact same loop deterministically, which is why the demo and tests are stable. Grounded and validated — we build state from recorded results, and we check each one against the request: the employee record must belong to the requester, the policy must be for the requested type. And it fails safe — a tool that raises comes back to the model as an ERROR string so it can recover, an unknown tool call is rejected, and any tool the model skipped is re-fetched with a direct call so no data is ever lost.

The philosophy in one line: the model is an optimizer, not a single point of failure. Primary path, validation, fallback. Now the piece evaluators always focus on — the Decision Engine.
""")

# =============================================================================
# SLIDE 8 — DECISION ENGINE
# =============================================================================
s = new("The Decision Engine", "A transparent, auditable rule ladder")
text(s, 0.62, 1.8, 12, 0.5, [
    [("The outcome is decided by rules, not the LLM. ", {"size": 14.5, "bold": True, "color": NAVY}),
     ("Highest-precedence rule wins; every outcome carries a confidence + per-criterion pass/fail.",
      {"size": 13.5, "color": INK})],
])
ladder = [
    ("balance insufficient  OR  exceeds annual max", "REJECT", "0.90", RED),
    ("policy requires manager approval", "ESCALATE", "0.90", AMBER),
    ("notice period not met", "ESCALATE", "0.60", AMBER),
    ("overlaps existing leave", "ESCALATE", "0.60", AMBER),
    ("all criteria satisfied", "APPROVE", "0.95", TEAL),
]
y = 2.5
for i, (cond, out, conf, c) in enumerate(ladder):
    rect(s, 0.62, y, 7.7, 0.66, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    text(s, 0.85, y, 0.5, 0.66, [[(f"{i+1}", {"size": 15, "bold": True, "color": c})]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.4, y, 6.8, 0.66, [[("if  ", {"size": 12, "italic": True, "color": SLATE, "font": "Consolas"}),
         (cond, {"size": 12, "color": INK, "font": "Consolas"})]], anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 8.5, y, 2.6, 0.66, c, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, 8.5, y, 2.6, 0.66, [[(out, {"size": 13.5, "bold": True, "color": WHITE})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 11.25, y, 1.4, 0.66, [[("conf ", {"size": 10, "color": SLATE}),
         (conf, {"size": 13, "bold": True, "color": NAVY})]], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.74
text(s, 0.62, y + 0.05, 12.1, 1.0, [
    [("Why rules, not the LLM: ", {"size": 12.5, "bold": True, "color": NAVY}),
     ("deterministic, testable, explainable — an auditor can read the exact criteria.", {"size": 12.5, "color": SLATE})],
    [("Roadmap: ", {"size": 12.5, "bold": True, "color": NAVY, "space_before": 3}),
     ("weights move to config; the LLM helps on borderline cases — on top of this base, never replacing it.",
      {"size": 12.5, "color": SLATE})],
])
notes(s, """
This is the Decision Engine, and I want to be very explicit: the final Approve/Reject/Escalate is NOT made by the language model — it's made by this transparent rule ladder, evaluated highest-precedence first.

Reading down: insufficient balance or over the annual max is a hard REJECT at 0.9. Otherwise, a policy that requires manager approval — which earned leave always does — is an ESCALATE at 0.9. Then two softer escalations: notice not met, or an overlap with existing leave, each at 0.6 because those genuinely need human discretion. And if everything passes, it's an APPROVE at 0.95. Every outcome also emits a per-criterion pass/fail map, so you can see exactly which checks drove it.

Why do it this way instead of asking the model "should I approve?" Because a rule ladder is deterministic, testable — we have tests for each path — and explainable. An employee or auditor can read the exact criterion that caused a rejection.

And the roadmap isn't to keep it rigid forever: the weights move to config, and the LLM starts helping on genuinely borderline cases — but always on top of this auditable base, never replacing it. Let me quickly cover the data and security model, then run the demo.
""")

# =============================================================================
# SLIDE 9 — DATABASE & SECURITY
# =============================================================================
s = new("Database & Security", "Five tables — and the model boxed in")
# left: database
text(s, 0.62, 1.8, 6, 0.4, [[("Data model — SQLite, Postgres-shaped", {"size": 14, "bold": True, "color": NAVY})]])
tables = [
    ("employees", "id, name, email, dept, manager_id (self-FK)", BLUE),
    ("leave_balances", "employee_id, leave_type, total/used_days", TEAL),
    ("leave_requests", "id, dates, days, reason, status", AMBER),
    ("decisions", "outcome, confidence, rationale, criteria_json", RED),
    ("policy_rules", "max_days, notice, docs, manager_required", SLATE),
]
y = 2.3
for name, cols, c in tables:
    rect(s, 0.62, y, 5.9, 0.72, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, 0.62, y, 0.1, 0.72, c)
    text(s, 0.85, y + 0.08, 5.5, 0.6, [
        [(name, {"size": 12, "bold": True, "color": NAVY, "font": "Consolas"})],
        [(cols, {"size": 9.8, "color": SLATE, "font": "Consolas", "space_before": 1})],
    ], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.8
text(s, 0.62, y + 0.02, 6, 0.5, [
    [("decisions", {"size": 10.5, "bold": True, "color": NAVY, "font": "Consolas"}),
     (" is the audit table — any verdict is fully reconstructable.", {"size": 10.5, "color": SLATE})],
])
# right: security
text(s, 6.8, 1.8, 6, 0.4, [[("Security — least privilege by design", {"size": 14, "bold": True, "color": NAVY})]])
sec = [
    ("Only read tools exposed to the LLM", "the 2 DB writes are direct calls in trusted agents", RED),
    ("db_path never in a tool schema", "the model can't choose which database to hit", AMBER),
    ("Grounding over prose", "results validated vs. the request before use", TEAL),
    ("Bounded execution", "loop capped; unknown tools rejected; errors contained", BLUE),
    ("Auditable trail", "decisions persisted; every step logged [agent]", TEAL),
    ("Secrets in env only", "offline mode needs no key at all", SLATE),
]
y = 2.3
for t, b, c in sec:
    rect(s, 6.8, y, 5.9, 0.72, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, 6.8, y, 0.1, 0.72, c)
    text(s, 7.05, y + 0.08, 5.5, 0.6, [
        [(t, {"size": 11.5, "bold": True, "color": NAVY})],
        [(b, {"size": 9.8, "color": SLATE, "space_before": 1, "line": 1.0})],
    ], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.8
notes(s, """
Two things on one slide — the data model and the security model — because they're closely linked.

On the left, five normalized tables. Employees has a self-referencing manager_id, so the org hierarchy lives in the table — that's how we know who to escalate to. Balances, requests, and policy_rules are self-explanatory. The one I'd point you to is decisions: it stores the outcome, the confidence, the rationale, and criteria_json — the full pass/fail map serialized — so any decision ever made is fully reconstructable. It's SQLite for development but every shape is Postgres-compatible, so production is a config change, not a rewrite.

On the right, security, and it all flows from least privilege. The model only ever sees read tools; the two operations that write to the database are not tools at all — they're direct calls inside the Coordinator and Notification agents. So even a fully hallucinating model literally cannot write, because it has no mechanism to. The database path is deliberately kept out of every schema. We ground over prose and validate. Execution is bounded. Every decision and step is logged for a forensic trail. And secrets live in the environment only — in offline mode there's no secret at all.

The one-liner: the model can look and suggest, but it can't act on anything sensitive. Now — the live demo.
""")

# =============================================================================
# SLIDE 10 — LIVE DEMO
# =============================================================================
s = new("Live Demo", "Three scenarios — every outcome, end to end")
rect(s, 0.62, 1.85, 12.1, 1.25, RGBColor(0x0E, 0x1A, 0x2B), shape=MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, 0.9, 1.98, 11.6, 1.05, [
    [("$ ", {"size": 13, "color": TEAL, "font": "Consolas"}),
     ("python main.py --init-db", {"size": 13, "color": WHITE, "font": "Consolas"}),
     ("     # reset to clean, deterministic seed", {"size": 11.5, "color": SLATE, "font": "Consolas"})],
    [("$ ", {"size": 13, "color": TEAL, "font": "Consolas", "space_before": 3}),
     ("python main.py --list", {"size": 13, "color": WHITE, "font": "Consolas"}),
     ("        # show the seeded employees", {"size": 11.5, "color": SLATE, "font": "Consolas"})],
    [("$ ", {"size": 13, "color": TEAL, "font": "Consolas", "space_before": 3}),
     ("python main.py --demo", {"size": 13, "color": WHITE, "font": "Consolas"}),
     ("        # run APPROVE / REJECT / ESCALATE end-to-end", {"size": 11.5, "color": SLATE, "font": "Consolas"})],
])
scen = [
    ("APPROVE", "E001 · casual · 3 days", "Ample balance, notice met, no overlap → auto-approved (0.95).", TEAL),
    ("REJECT", "E002 · earned · 5 days", "Only 1 earned day left → balance fails → rejected (0.90).", RED),
    ("ESCALATE", "E003 · earned · 3 days", "Eligible, but earned = manager-required → escalated (0.90).", AMBER),
]
x = 0.62
for name, who, desc, c in scen:
    rect(s, x, 3.4, 3.87, 2.4, WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, x, 3.4, 3.87, 0.6, c, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, x, 3.7, 3.87, 0.3, c)
    text(s, x, 3.4, 3.87, 0.6, [[(name, {"size": 15, "bold": True, "color": WHITE})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.22, 4.2, 3.45, 1.5, [
        [(who, {"size": 12, "bold": True, "color": NAVY, "font": "Consolas"})],
        [(desc, {"size": 11.5, "color": SLATE, "space_before": 6, "line": 1.1})],
    ])
    x += 4.05
text(s, 0.62, 6.1, 12, 0.9, [
    [("Watch for  ", {"size": 12.5, "bold": True, "color": NAVY}),
     ("[employee_data] Model selected 3 tool call(s)", {"size": 11.5, "color": NAVY, "font": "Consolas"}),
     ("  — that's the LLM choosing tools live —", {"size": 12, "color": SLATE})],
    [("plus the final confidence + generated message per scenario.", {"size": 12, "color": SLATE, "space_before": 2})],
])
notes(s, """
Here's what I'm about to run. Three commands. First, init-db, to reset to clean seed data — I do this so results are deterministic and I don't trip the self-overlap detection from an earlier run. Second, --list, to show the six seeded employees. Third, the main event, --demo, which runs all three decision paths back to back.

The three scenarios are picked to exercise every outcome. APPROVE is E001, Asha Rao, three casual days — plenty of balance, notice fine, no overlaps, auto-approves at 0.95. REJECT is E002, Ravi Kumar, five earned days when he has only one left — balance check fails, clean rejection at 0.90. ESCALATE is E003, Meera Nair — fully eligible, but earned leave is manager-required by policy, so it escalates to her manager at 0.90.

The line to watch for is in the Employee-Data step: "Model selected 3 tool call(s)." That is the LLM choosing and calling the database tools live — Milestone 2 working in front of you. Also watch the final confidence and the message generated for each employee. Let me run it now. [SWITCH TO TERMINAL — run the three commands and narrate the trace as it scrolls.]
""")

# =============================================================================
# SLIDE 11 — ROADMAP
# =============================================================================
s = new("Roadmap", "Done today — and what's next")
rect(s, 0.62, 1.95, 12.1, 0.85, RGBColor(0xE7, 0xF6, 0xF2), shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=TEAL)
rect(s, 0.62, 1.95, 1.4, 0.85, RGBColor(0x1E, 0x8E, 0x7C), shape=MSO_SHAPE.ROUNDED_RECTANGLE)
rect(s, 1.3, 1.95, 0.72, 0.85, RGBColor(0x1E, 0x8E, 0x7C))
text(s, 0.62, 1.95, 1.4, 0.85, [[("✓", {"size": 24, "bold": True, "color": WHITE})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 2.25, 1.95, 10.2, 0.85, [
    [("M1–M2  ·  Done today", {"size": 14, "bold": True, "color": RGBColor(0x1E, 0x8E, 0x7C)}),
     ("   —   7 agents · tool-calling · connector · exception handling · 29 tests",
      {"size": 12, "color": SLATE})],
], anchor=MSO_ANCHOR.MIDDLE)
road = [
    ("M3", "Memory & RAG", "Embed the policy doc into ChromaDB so Policy cites real passages; per-employee history.", TEAL),
    ("M4", "Workflow + API", "LangGraph graph with conditional edges; human-in-the-loop manager approval; FastAPI endpoints.", BLUE),
    ("M5", "Dashboard & Observability", "Streamlit UI to submit requests & watch the agent trace live; manager approval queue.", AMBER),
]
y = 3.05
for tag, title, desc, c in road:
    rect(s, 0.62, y, 12.1, 1.02, CLOUD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=LINE)
    rect(s, 0.62, y, 1.4, 1.02, c, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, 1.3, y, 0.72, 1.02, c)
    text(s, 0.62, y, 1.4, 1.02, [[(tag, {"size": 17, "bold": True, "color": WHITE})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 2.25, y + 0.12, 10.2, 0.82, [
        [(title, {"size": 14.5, "bold": True, "color": NAVY})],
        [(desc, {"size": 11.5, "color": SLATE, "space_before": 3, "line": 1.05})],
    ], anchor=MSO_ANCHOR.MIDDLE)
    y += 1.14
text(s, 0.62, y + 0.05, 12, 0.4, [
    [("Every dependency is already in ", {"size": 12, "color": SLATE}),
     ("requirements.txt", {"size": 12, "color": NAVY, "font": "Consolas"}),
     (" — the seams (Transport, BaseLLM, run(state)) are built for exactly these upgrades.", {"size": 12, "color": SLATE})],
])
notes(s, """
Where does this go next? The green bar at the top is what's already done — Milestones 1 and 2: seven agents, native tool-calling, the connector, exception handling, 29 tests. That's the platform.

Milestone 3 is memory and RAG. Today the Policy agent reads structured rules from a table; in M3 we also embed the human-readable policy document into ChromaDB so it can retrieve and cite the actual passage in its rationale, plus per-employee history as long-term memory.

Milestone 4 is workflow automation and the API — we swap the sequential runner for a real LangGraph graph with conditional edges, so a REJECT can short-circuit and an ESCALATE routes to a genuine human-in-the-loop manager approval, all exposed over FastAPI. The agents themselves don't change; only the orchestrator does.

Milestone 5 is the front end — a Streamlit dashboard where you submit a request and watch the agent trace unfold live, with a manager approval queue.

And the key point: this isn't wishful thinking. Every dependency — ChromaDB, LangGraph, FastAPI, Streamlit — is already in requirements.txt, and the seams we built were designed specifically to make these drop-in rather than rewrites. Let me wrap up.
""")

# =============================================================================
# SLIDE 12 — CONCLUSION & Q&A
# =============================================================================
s = slide()
bg(s, NAVY)
rect(s, 0, 0, SW, 0.22, TEAL)
rect(s, 0, 6.7, SW, 0.8, RGBColor(0x0E, 0x28, 0x4C))
text(s, 0.9, 0.75, 11.5, 0.8, [[("Conclusion & Q&A", {"size": 32, "bold": True, "color": WHITE})]])
rect(s, 0.95, 1.5, 1.6, 0.05, TEAL)
takeaways = [
    ("A working multi-agent decision engine", "seven specialists collaborate over a shared state — Approve, Reject, Escalate, end to end."),
    ("Intelligent, but safe", "the LLM selects & calls tools, yet is boxed in by least privilege, grounding & validation."),
    ("Auditable by design", "a transparent rule ladder, per-criterion scores, and a full logged trace for every decision."),
    ("Built to grow", "clean seams make RAG, LangGraph, an API, and a dashboard drop-in — all already scoped."),
]
y = 1.85
for i, (t, b) in enumerate(takeaways):
    rect(s, 0.9, y, 0.5, 0.5, TEAL, shape=MSO_SHAPE.OVAL)
    text(s, 0.9, y, 0.5, 0.5, [[(str(i + 1), {"size": 16, "bold": True, "color": NAVY})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.65, y - 0.03, 10.8, 0.9, [
        [(t, {"size": 16.5, "bold": True, "color": WHITE})],
        [(b, {"size": 12, "color": RGBColor(0xC7, 0xD4, 0xE6), "space_before": 2, "line": 1.03})],
    ])
    y += 1.02
# q&a chips
topics = ["Why 7 agents?", "Why not let the LLM decide?", "How is it grounded?",
          "What if a tool fails?", "Mock vs. Claude", "Scaling to production"]
x = 0.9
yy = 6.0
for t in topics:
    w = 0.24 + len(t) * 0.108
    chip(s, x, yy, w, 0.48, t, fill=RGBColor(0x12, 0x33, 0x5B), fg=TEAL, size=11.5)
    x += w + 0.22
    if x > 10.6:
        x = 0.9
        yy += 0.62
text(s, 0.9, 6.9, 11, 0.4, [
    [("29 tests passing", {"size": 11.5, "bold": True, "color": TEAL}),
     ("   ·   runs offline, no API key   ·   Milestones 1 & 2 complete   ·   Thank you!",
      {"size": 11.5, "color": RGBColor(0x9F, 0xB2, 0xCC)})],
])
notes(s, """
To bring it together — four takeaways.

One: this is a working multi-agent decision engine, not a concept. Seven specialists collaborate over a shared state to take a request from submission to a written reply and correctly Approve, Reject, or Escalate it.

Two: it's intelligent but safe. The model genuinely reasons — it selects and calls its own tools — but it's boxed in by three walls: least privilege on writes, grounding in real results, and validation of everything it produces.

Three: it's auditable by design. No black box at the decision point — a transparent rule ladder, a pass/fail score for every criterion, and a complete logged trace.

And four: it's built to grow — the seams mean RAG, LangGraph, a REST API, and a dashboard all drop in without disturbing the agents.

Bottom line: Milestones 1 and 2 complete, runs offline with no API key, 29 tests passing. Thank you — I'd love your questions. If it's quiet, I'm happy to dig into any of the topics on screen: why seven agents, why the LLM doesn't make the final call, how we keep it grounded, what happens when a tool fails, mock versus real Claude, and how it scales to production. See PRESENTATION_SCRIPT.md for detailed answers.
""")

# ── Save ─────────────────────────────────────────────────────────────────────
out = Path(__file__).resolve().parent / "AI_Leave_Approval_Demo.pptx"
prs.save(str(out))
print(f"Saved {out}  ({len(prs.slides._sldIdLst)} slides)")
