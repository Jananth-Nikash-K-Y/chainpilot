"""
Regenerate docs/architecture-overview/ChainPilot-Architecture-Overview.pdf.

Run weekly by scripts/development/weekly_architecture_update.sh (via cron).
Each run:
  - bumps the version counter in docs/architecture-overview/VERSION
  - re-reads the repo (top-level folders, agents/, README roadmap) so
    structural sections stay current as the project grows
  - summarizes git commits from the last 7 days into a "Recent Changes"
    section
  - overwrites the PDF in place (no v1/v2/v3 files pile up — the version
    number lives inside the document, the file itself is replaced)
"""
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable,
    PageBreak, HRFlowable,
)
from reportlab.pdfgen import canvas as canvas_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs" / "architecture-overview"
OUT_PATH = DOCS_DIR / "ChainPilot-Architecture-Overview.pdf"
VERSION_PATH = DOCS_DIR / "VERSION"

# ---- Palette -------------------------------------------------------------
NAVY = HexColor("#0F1B3C")
BLUE = HexColor("#1E4FD8")
LIGHT_BLUE = HexColor("#EAF0FF")
SLATE = HexColor("#3D4A63")
MUTED = HexColor("#6B7488")
LINE = HexColor("#C6CCDC")
AMBER = HexColor("#B8720B")
AMBER_BG = HexColor("#FFF4E1")
GREEN = HexColor("#1F7A4D")
GREEN_BG = HexColor("#E9F7EF")
WHITE = HexColor("#FFFFFF")

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=27, leading=32, textColor=NAVY, spaceAfter=4, alignment=TA_LEFT)
subtitle_style = ParagraphStyle("SubtitleStyle", parent=styles["Normal"], fontName="Helvetica",
                                 fontSize=13.5, leading=18, textColor=BLUE, spaceAfter=2)
meta_style = ParagraphStyle("MetaStyle", parent=styles["Normal"], fontName="Helvetica",
                             fontSize=9, leading=13, textColor=MUTED)
h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                           fontSize=15.5, leading=19, textColor=NAVY, spaceBefore=22, spaceAfter=8)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                           fontSize=11.5, leading=15, textColor=SLATE, spaceBefore=12, spaceAfter=5)
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                             fontSize=9.8, leading=15, textColor=HexColor("#1C2333"),
                             spaceAfter=6, alignment=TA_LEFT)
bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=14, bulletIndent=2, spaceAfter=4)
caption_style = ParagraphStyle("Caption", parent=styles["Normal"], fontName="Helvetica-Oblique",
                                fontSize=8.3, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceBefore=4)
mono_style = ParagraphStyle("Mono", parent=styles["Normal"], fontName="Courier",
                             fontSize=8.4, leading=12.5, textColor=HexColor("#1C2333"), spaceAfter=2)


# ---- Diagram flowables (unchanged visual language from v1) --------------
class BoxChainDiagram(Flowable):
    def __init__(self, items, width, box_h=0.42 * inch, gap=0.30 * inch,
                 box_color=LIGHT_BLUE, text_color=NAVY, border_color=BLUE,
                 sublabels=None, font_size=9.2):
        super().__init__()
        self.items = items
        self.width = width
        self.box_h = box_h
        self.gap = gap
        self.box_color = box_color
        self.text_color = text_color
        self.border_color = border_color
        self.sublabels = sublabels or {}
        self.font_size = font_size
        n = len(items)
        self.height = n * box_h + (n - 1) * gap

    def wrap(self, avail_w, avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setLineWidth(1.1)
        n = len(self.items)
        box_w = self.width * 0.86
        x = (self.width - box_w) / 2
        y = self.height
        for i, label in enumerate(self.items):
            y -= self.box_h
            c.setFillColor(self.box_color)
            c.setStrokeColor(self.border_color)
            c.roundRect(x, y, box_w, self.box_h, 5, fill=1, stroke=1)
            c.setFillColor(self.text_color)
            c.setFont("Helvetica-Bold", self.font_size)
            if i in self.sublabels:
                c.drawCentredString(self.width / 2, y + self.box_h / 2 + 6, label)
                c.setFont("Helvetica", 7.4)
                c.setFillColor(MUTED)
                c.drawCentredString(self.width / 2, y + self.box_h / 2 - 9, self.sublabels[i])
            else:
                c.drawCentredString(self.width / 2, y + self.box_h / 2 - 4, label)
            if i < n - 1:
                ax = self.width / 2
                ay1 = y - self.gap + 2
                ay2 = y - 2
                c.setStrokeColor(SLATE)
                c.setLineWidth(1.3)
                c.line(ax, ay1, ax, ay2)
                c.line(ax, ay1, ax - 3.2, ay1 + 6.5)
                c.line(ax, ay1, ax + 3.2, ay1 + 6.5)
            y -= self.gap


class PipelineDiagram(Flowable):
    def __init__(self, width, height=1.05 * inch):
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, avail_w, avail_h):
        return self.width, self.height

    def draw(self):
        c = self.canv
        stages = [
            ("recommend_\naction", LIGHT_BLUE, BLUE, NAVY),
            ("validate_\naction", LIGHT_BLUE, BLUE, NAVY),
            ("HUMAN\nAPPROVAL", AMBER_BG, AMBER, AMBER),
            ("execute_\naction", GREEN_BG, GREEN, GREEN),
        ]
        n = len(stages)
        gap = 0.34 * inch
        box_w = (self.width - (n - 1) * gap) / n
        box_h = 0.62 * inch
        y = self.height - box_h - 0.20 * inch
        for i, (label, fill, border, text_color) in enumerate(stages):
            x = i * (box_w + gap)
            c.setFillColor(fill)
            c.setStrokeColor(border)
            c.setLineWidth(1.3)
            c.roundRect(x, y, box_w, box_h, 6, fill=1, stroke=1)
            c.setFillColor(text_color)
            c.setFont("Helvetica-Bold", 9)
            lines = label.split("\n")
            ly = y + box_h / 2 + (len(lines) - 1) * 5.5
            for ln in lines:
                c.drawCentredString(x + box_w / 2, ly - 4, ln)
                ly -= 11
            if i < n - 1:
                ay = y + box_h / 2
                ax1 = x + box_w + 3
                ax2 = x + box_w + gap - 3
                c.setStrokeColor(SLATE)
                c.setLineWidth(1.3)
                c.line(ax1, ay, ax2, ay)
                c.line(ax2, ay, ax2 - 6.5, ay + 3.2)
                c.line(ax2, ay, ax2 - 6.5, ay - 3.2)
        c.setFont("Helvetica-Oblique", 7.6)
        c.setFillColor(MUTED)
        c.drawCentredString(self.width / 2, y - 14,
                             "No agent-recommended action executes automatically — approval is a hard architectural gate, not a UI affordance.")


def rule():
    return HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=2, spaceAfter=10)


def bullets(items):
    return [Paragraph(f"• {t}", bullet_style) for t in items]


# ---- Dynamic content: read the repo instead of hardcoding ---------------
FOLDER_DESCRIPTIONS = {
    "frontend": "React + TypeScript + Vite + Three.js digital twin UI",
    "backend": "FastAPI service (API → services → domain → repositories → DB)",
    "agents": "Orchestrator + specialized agent definitions",
    "mcp": "MCP server exposing operational tools to agents",
    "database": "Alembic migrations + seed data",
    "data": "Local raw / processed / sample data",
    "docs": "Architecture, API, agent, MCP, A2A, and domain documentation",
    "scripts": "Setup, database, and dev helper scripts",
    "tests": "Cross-cutting integration / e2e tests",
    "infra": "Docker / deployment configuration",
}
SKIP_TOP_DIRS = {".git", ".github", "node_modules", "__pycache__"}


def discover_top_level_dirs():
    rows = []
    for p in sorted(REPO_ROOT.iterdir()):
        if not p.is_dir() or p.name in SKIP_TOP_DIRS or p.name.startswith("."):
            continue
        desc = FOLDER_DESCRIPTIONS.get(p.name, "")
        if not desc:
            readme = p / "README.md"
            if readme.exists():
                for line in readme.read_text(errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        desc = line
                        break
        rows.append((f"{p.name}/", desc or "—"))
    return rows


def discover_agents():
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.exists():
        return []
    names = sorted(
        p.name for p in agents_dir.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
    )
    return [n.replace("-", " ").replace("_", " ").title() for n in names]


def parse_roadmap():
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return []
    text = readme.read_text(errors="ignore")
    m = re.search(r"^## Roadmap\s*$(.*?)(^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        line = line.strip()
        mm = re.match(r"^\d+\.\s*(✅\s*)?(.+)$", line)
        if mm:
            done = bool(mm.group(1))
            items.append(("done" if done else "todo", mm.group(2).strip()))
    if items:
        # mark the first not-done item as "next"
        for i, (status, label) in enumerate(items):
            if status == "todo":
                items[i] = ("next", label)
                break
    return items


def git(*args):
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def recent_changes(days=7):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    log = git("log", f"--since={since}", "--pretty=format:%ad|%h|%s", "--date=short")
    commits = [line.split("|", 2) for line in log.splitlines() if line.strip()]
    stat = git("log", f"--since={since}", "--name-only", "--pretty=format:")
    files_touched = sorted({f for f in stat.splitlines() if f.strip()})
    return commits, files_touched


def read_version():
    if VERSION_PATH.exists():
        try:
            return int(VERSION_PATH.read_text().strip())
        except ValueError:
            return 0
    return 0


def write_version(v):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_PATH.write_text(str(v) + "\n")


def on_page(c: canvas_mod.Canvas, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 0.16 * inch, PAGE_W, 0.16 * inch, fill=1, stroke=0)
    if doc.page > 1:
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, PAGE_H - 0.42 * inch, "CHAINPILOT")
        c.setFont("Helvetica", 8)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.42 * inch, "Architecture Overview")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(MARGIN, PAGE_H - 0.50 * inch, PAGE_W - MARGIN, PAGE_H - 0.50 * inch)
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 0.5 * inch, "ChainPilot — Agentic AI Supply Chain Control Tower")
    c.drawRightString(PAGE_W - MARGIN, 0.5 * inch, f"Page {doc.page}")
    c.restoreState()


def build():
    version = read_version() + 1
    write_version(version)
    today = datetime.now().strftime("%B %-d, %Y") if hasattr(datetime.now(), "strftime") else str(datetime.now())
    commits, files_touched = recent_changes(7)

    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.62 * inch, bottomMargin=0.75 * inch,
        title=f"ChainPilot Architecture Overview v{version}",
        author="ChainPilot",
    )
    story = []
    content_w = PAGE_W - 2 * MARGIN

    # ---- Title ----
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("ChainPilot", title_style))
    story.append(Paragraph("Agentic AI Supply Chain Control Tower — Architecture Overview", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Version v{version} · Auto-generated {today} · reflects the repository as of this run",
        meta_style,
    ))
    story.append(Spacer(1, 10))
    story.append(rule())

    # ---- 1. Overview ----
    story.append(Paragraph("1. What is ChainPilot?", h1_style))
    story.append(Paragraph(
        "ChainPilot is a platform for operating a supply chain through a live 3D digital twin "
        "combined with a network of specialized AI agents. Operators will be able to see "
        "warehouses, trucks, docks, and inventory in real time; surface operational exceptions "
        "as they emerge; simulate recovery options; and — with human approval — let agents "
        "take action.",
        body_style,
    ))
    story.append(Paragraph("Design goals", h2_style))
    for p in bullets([
        "A believable, real-time 3D digital twin of warehouse and logistics operations "
        "(parking lots, dock doors, aisles, bays, trucks, trailers, pallets, shipment routes).",
        "A modular agent architecture (Orchestrator → specialized agents) exposed through "
        "MCP tools, so agents reason over live operational data.",
        "Human-in-the-loop control: agents recommend and simulate; humans approve; actions "
        "execute and are logged as operational events.",
        "A clean separation between frontend, backend, agents, and MCP so each layer can "
        "evolve independently.",
    ]):
        story.append(p)

    # ---- 2. Application layers ----
    story.append(Paragraph("2. Application Layers", h1_style))
    story.append(Paragraph(
        "The product stack is a straightforward top-to-bottom layering. Each layer talks only "
        "to the one directly below it, which keeps the UI, HTTP concerns, application logic, "
        "business rules, and persistence independently replaceable.",
        body_style,
    ))
    diag_w = content_w * 0.62
    diagram = BoxChainDiagram(
        ["Frontend", "API", "Backend Services", "Domain Layer", "Database"],
        width=diag_w,
        sublabels={0: "React + TypeScript + Vite + Three.js (Control Tower / Digital Twin)",
                   1: "FastAPI route handlers — no business logic",
                   2: "Use-case orchestration, calls domain + repositories",
                   3: "Core business rules & entities, framework-independent",
                   4: "PostgreSQL — accessed only via repositories"},
        box_h=0.56 * inch, gap=0.30 * inch,
    )
    wrapper = Table([[diagram]], colWidths=[content_w])
    wrapper.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(Spacer(1, 6))
    story.append(wrapper)
    story.append(Paragraph(
        "Frontend → API → Backend Services → Domain → Database. "
        "Repositories are the only layer permitted to issue SQLAlchemy queries.",
        caption_style,
    ))

    # ---- 3. AI / Agent layer ----
    story.append(Paragraph("3. AI / Agent Layer", h1_style))
    story.append(Paragraph(
        "A parallel stack handles reasoning and action. An Orchestrator agent receives a goal, "
        "decides which specialized agents are relevant, and coordinates their responses. Agents "
        "never talk to the database directly — all reads and actions go through MCP tools, "
        "which ultimately call the same backend services and repositories the application uses.",
        body_style,
    ))
    diag2_w = content_w * 0.62
    diagram2 = BoxChainDiagram(
        ["User / System Goal", "Orchestrator", "Specialized Agents", "MCP Tools", "Business Data"],
        width=diag2_w, box_h=0.40 * inch, gap=0.42 * inch,
        box_color=HexColor("#EDEBFB"), border_color=HexColor("#5B3FD1"), text_color=HexColor("#2C1B6B"),
    )
    wrapper2 = Table([[diagram2]], colWidths=[content_w])
    wrapper2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(Spacer(1, 6))
    story.append(wrapper2)
    story.append(Paragraph(
        "Same underlying PostgreSQL database as the application stack — the digital twin and "
        "the agents are two views of one source of truth, not two systems.",
        caption_style,
    ))

    story.append(Paragraph("Specialized agents (each owns one operational domain)", h2_style))
    agent_names = discover_agents() or [
        "Logistics", "Inventory", "Warehouse", "Supplier Risk", "Demand",
        "Cost Optimization", "Document", "Exception", "Simulation",
        "Communication", "Validation",
    ]
    cols = 4
    agent_rows = [agent_names[i:i + cols] for i in range(0, len(agent_names), cols)]
    pill_rows = []
    for row in agent_rows:
        row = row + [""] * (cols - len(row))
        pill_rows.append([Paragraph(f"• {c}", body_style) if c else "" for c in row])
    agent_table = Table(pill_rows, colWidths=[content_w / cols] * cols, hAlign="LEFT")
    agent_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(agent_table)

    story.append(PageBreak())

    # ---- 4. Digital twin data flow ----
    story.append(Paragraph("4. Digital Twin ↔ Agent ↔ Data Relationship", h1_style))
    story.append(Paragraph(
        "The digital twin is a <b>view</b> of the same operational data the agents reason over "
        "— never a separate source of truth. Actions agents take, once approved, flow back "
        "through the backend as <b>OperationalEvents</b>, which both the digital twin and the "
        "Control Tower UI subscribe to, closing the loop.",
        body_style,
    ))

    flow_w = content_w
    flow_h = 2.35 * inch

    class TwinFlow(Flowable):
        def wrap(self, aw, ah):
            return flow_w, flow_h

        def draw(self):
            c = self.canv
            box_w, box_h = flow_w * 0.62, 0.42 * inch
            x = (flow_w - box_w) / 2
            top_y = flow_h - box_h
            mid_y = flow_h / 2 - box_h / 2
            bot_y = 0

            def box(y, label, sub, fill=LIGHT_BLUE, border=BLUE, text=NAVY):
                c.setFillColor(fill); c.setStrokeColor(border); c.setLineWidth(1.2)
                c.roundRect(x, y, box_w, box_h, 5, fill=1, stroke=1)
                c.setFillColor(text); c.setFont("Helvetica-Bold", 9.2)
                c.drawCentredString(flow_w / 2, y + box_h / 2 + (3 if sub else -3), label)
                if sub:
                    c.setFont("Helvetica", 7.2); c.setFillColor(MUTED)
                    c.drawCentredString(flow_w / 2, y + box_h / 2 - 10, sub)

            box(top_y, "Digital Twin (Frontend)",
                "warehouse, aisles, bays, docks, trucks, trailers, forklifts, pallets, routes")
            box(mid_y, "Backend API",
                "real-time state + operational events", fill=HexColor("#F1F3F8"), border=SLATE, text=SLATE)
            box(bot_y, "Specialized Agents",
                "reason about exceptions, risk, recovery options",
                fill=HexColor("#EDEBFB"), border=HexColor("#5B3FD1"), text=HexColor("#2C1B6B"))

            cx = flow_w / 2
            c.setStrokeColor(SLATE); c.setLineWidth(1.3)
            y1, y2 = top_y, mid_y + box_h
            c.line(cx - 10, y1, cx - 10, y2)
            c.line(cx - 10, y2, cx - 10 - 3.2, y2 + 6.5)
            c.line(cx - 10, y2, cx - 10 + 3.2, y2 + 6.5)
            c.setFont("Helvetica-Oblique", 6.6); c.setFillColor(MUTED)
            c.drawString(cx + 4, (y1 + y2) / 2 - 2, "renders live state")

            y1, y2 = mid_y, bot_y + box_h
            c.line(cx + 10, y1, cx + 10, y2)
            c.line(cx + 10, y1, cx + 10 - 3.2, y1 + 6.5)
            c.line(cx + 10, y1, cx + 10 + 3.2, y1 + 6.5)
            c.setFont("Helvetica-Oblique", 6.6); c.setFillColor(MUTED)
            c.drawString(cx + 14, (y1 + y2) / 2 - 2, "read via MCP tools")

    story.append(Spacer(1, 4))
    story.append(TwinFlow())
    story.append(Paragraph(
        "Recommendations → human approval → actions → operational events, fed back "
        "into both the digital twin and the backend API.",
        caption_style,
    ))

    # ---- 5. Human-in-the-loop ----
    story.append(Paragraph("5. Human-in-the-Loop Principle", h1_style))
    story.append(Paragraph(
        "No agent-recommended action executes automatically. This is a hard architectural "
        "constraint, not just a UI affordance — the <b>validation</b> agent and the "
        "<b>execute_action</b> MCP tool are deliberately separate from <b>recommend_action</b> "
        "so a human approval gate always sits between them.",
        body_style,
    ))
    story.append(Spacer(1, 4))
    story.append(PipelineDiagram(width=content_w))

    story.append(PageBreak())

    # ---- 6. Repository structure (dynamic) ----
    story.append(Paragraph("6. Repository Structure", h1_style))
    repo_rows = [["Folder", "Purpose"]] + discover_top_level_dirs()
    t = Table(repo_rows, colWidths=[1.4 * inch, content_w - 1.4 * inch], hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (0, -1), BLUE),
        ("TEXTCOLOR", (1, 1), (1, -1), HexColor("#1C2333")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, HexColor("#F4F6FB")]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)

    # ---- 7. Status & roadmap (dynamic, parsed from README) ----
    story.append(Paragraph("7. Current Status & Roadmap", h1_style))
    roadmap = parse_roadmap()
    if roadmap:
        rm_rows = []
        for status, label in roadmap:
            mark = "X" if status == "done" else (">" if status == "next" else "-")
            rm_rows.append([mark, label, status.upper()])
        rm_table = Table(rm_rows, colWidths=[0.3 * inch, content_w - 1.3 * inch, 1.0 * inch], hAlign="LEFT")
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (2, 0), (2, -1), 7.6),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ]
        for i, (status, _) in enumerate(roadmap):
            color = GREEN if status == "done" else (AMBER if status == "next" else MUTED)
            style_cmds.append(("TEXTCOLOR", (0, i), (0, i), color))
            style_cmds.append(("TEXTCOLOR", (2, i), (2, i), color))
            style_cmds.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        rm_table.setStyle(TableStyle(style_cmds))
        story.append(rm_table)
    else:
        story.append(Paragraph("No roadmap section found in README.md.", body_style))

    # ---- 8. Recent changes (this week) ----
    story.append(Paragraph("8. Recent Changes (Last 7 Days)", h1_style))
    if commits:
        story.append(Paragraph(
            f"{len(commits)} commit(s) touching {len(files_touched)} file(s) since last week's run.",
            body_style,
        ))
        for date, sha, subject in commits[:25]:
            story.append(Paragraph(f"{date}  <font face='Courier'>{sha}</font>  {subject}", mono_style))
        if len(commits) > 25:
            story.append(Paragraph(f"… and {len(commits) - 25} more.", caption_style))
    else:
        story.append(Paragraph(
            "No commits in the last 7 days — architecture unchanged since the previous version.",
            body_style,
        ))

    story.append(Spacer(1, 16))
    story.append(rule())
    story.append(Paragraph(
        "Source: README.md, ARCHITECTURE.md, and git history, ChainPilot repository. "
        "This document is regenerated automatically every week.",
        meta_style,
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Wrote {OUT_PATH} (v{version})")
    return version


if __name__ == "__main__":
    build()
