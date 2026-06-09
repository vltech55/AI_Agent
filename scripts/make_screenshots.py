"""Generate portfolio screenshots for King Arthur Baking AI as PIL composites.

  chat.png       — Streamlit chat with product cards
  workflow.png   — LangGraph state machine
  analytics.png  — Analytics dashboard
  landing.png    — Landing page

Run from repo root:  python3 scripts/make_screenshots.py
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Palette — warm bakery feel
BG          = (250, 248, 244)   # warm off-white
SURFACE     = (255, 255, 255)
BORDER      = (228, 222, 213)
BORDER_SOFT = (236, 231, 223)
INK         = (28, 25, 22)      # near-black warm
INK_SECOND  = (107, 99, 89)     # warm gray
INK_DIM     = (158, 149, 137)
ACCENT      = (217, 119, 87)    # warm amber #d97757
ACCENT_DIM  = (244, 213, 198)
GREEN       = (52, 168, 83)
BLUE        = (37, 99, 235)
PURPLE      = (124, 58, 237)
YELLOW      = (245, 158, 11)
SIDEBAR     = (243, 238, 230)

W, H = 1600, 1000
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def f(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        p = ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
             if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    else:
        p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
             if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, size=size)
    except OSError:
        return ImageFont.load_default()


def canvas(bg=BG) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img, "RGBA")


def card(d, x, y, w, h, *, fill=SURFACE, border=BORDER, radius=12):
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=border, width=1)


def text(d, xy, s, *, font, fill=INK, anchor="lt"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def chip(d, x, y, label, *, fill=ACCENT_DIM, ink=ACCENT, pad=(10, 6)):
    fnt = f(13, bold=True)
    bbox = d.textbbox((0, 0), label, font=fnt)
    w = bbox[2] - bbox[0] + pad[0] * 2
    h = bbox[3] - bbox[1] + pad[1] * 2
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill)
    text(d, (x + pad[0], y + pad[1] - 2), label, font=fnt, fill=ink)
    return w


# Header used across screens
def draw_topbar(d, title: str):
    d.rectangle((0, 0, W, 56), fill=SURFACE, outline=None)
    d.line((0, 56, W, 56), fill=BORDER, width=1)
    # logo
    d.ellipse((24, 14, 56, 46), fill=ACCENT)
    text(d, (38, 30), "K", font=f(18, bold=True), fill=SURFACE, anchor="mm")
    text(d, (68, 28), title, font=f(15, bold=True), anchor="lm")
    # divider + subtitle, positioned after the title with proper spacing
    d.line((320, 16, 320, 40), fill=BORDER, width=1)
    text(d, (336, 28), "Catalog: 47 products  ·  Mongo Atlas: connected", font=f(12), fill=INK_DIM, anchor="lm")
    # right-side actions
    text(d, (W - 130, 28), "v1.2.0", font=f(12, mono=True), fill=INK_DIM, anchor="lm")
    d.ellipse((W - 64, 14, W - 32, 46), fill=ACCENT_DIM, outline=BORDER)
    text(d, (W - 48, 30), "V", font=f(13, bold=True), fill=ACCENT, anchor="mm")


def draw_sidebar(d, active: str):
    d.rectangle((0, 56, 240, H), fill=SIDEBAR)
    d.line((240, 56, 240, H), fill=BORDER, width=1)
    text(d, (24, 88), "Workspace", font=f(11, bold=True), fill=INK_DIM)
    items = [
        ("Chat", "💬"),
        ("Agent Graph", "🔀"),
        ("Analytics", "📊"),
        ("Catalog", "📦"),
        ("Settings", "⚙"),
    ]
    y = 116
    for label, _ in items:
        is_active = label == active
        if is_active:
            d.rounded_rectangle((16, y - 6, 224, y + 28), radius=8, fill=(255, 255, 255), outline=BORDER)
        text(d, (32, y + 10), label,
             font=f(14, bold=is_active),
             fill=ACCENT if is_active else INK_SECOND, anchor="lm")
        y += 44
    # Footer block
    d.rounded_rectangle((16, H - 120, 224, H - 24), radius=8, fill=(255, 255, 255), outline=BORDER)
    text(d, (32, H - 100), "Indexed corpus", font=f(11, bold=True), fill=INK_DIM)
    text(d, (32, H - 78), "47 products", font=f(16, bold=True))
    text(d, (32, H - 56), "1,536-dim embeddings", font=f(11), fill=INK_DIM)
    text(d, (32, H - 40), "Vector + text indexes", font=f(11), fill=INK_DIM)


# ─────────────────────────────────────────────────────────────
# chat.png
# ─────────────────────────────────────────────────────────────
def chat():
    img, d = canvas()
    draw_topbar(d, "King Arthur Baking AI")
    draw_sidebar(d, "Chat")

    # Conversation column
    cx, cy = 280, 96
    cw = 880
    # User message bubble
    msg_user = "Looking for a chocolate cake mix that's easy for beginners — what do you recommend?"
    d.rounded_rectangle((cx + 200, cy, cx + cw, cy + 70), radius=14, fill=(245, 240, 232), outline=BORDER_SOFT)
    text(d, (cx + 220, cy + 22), msg_user, font=f(14))
    text(d, (cx + cw - 14, cy + 52), "You · 2:14 PM", font=f(11), fill=INK_DIM, anchor="rt")

    cy += 100
    # Assistant — reasoning trace strip
    text(d, (cx, cy), "AGENT", font=f(11, bold=True), fill=INK_DIM)
    cy += 22
    steps = [
        ("analyse_query", "intent=recommend  category=cake  difficulty=easy", GREEN),
        ("route_decision", "→ recommend (semantic search + beginner filter)", BLUE),
        ("recommend",      "found 4 products · cosine ≥ 0.81", PURPLE),
        ("reason",         "ranking by ease-of-use + reviewer skill level", YELLOW),
    ]
    for name, desc, color in steps:
        d.rounded_rectangle((cx, cy, cx + 14, cy + 14), radius=3, fill=color)
        text(d, (cx + 26, cy + 8), name, font=f(12, mono=True, bold=True), anchor="lm")
        text(d, (cx + 200, cy + 8), desc, font=f(12, mono=True), fill=INK_DIM, anchor="lm")
        cy += 24
    cy += 12

    # Assistant message
    asst = ("Three good options for a beginner. The Gluten-Free Devil's Food Cake "
            "Mix is the simplest — just add eggs, butter, and milk. The Classic "
            "Chocolate Cake Mix is the most traditional. Skip the Triple-Chocolate "
            "Layer Cake — it's labelled \"intermediate\" by King Arthur and "
            "requires layered assembly.")
    d.rounded_rectangle((cx, cy, cx + cw, cy + 110), radius=14, fill=SURFACE, outline=BORDER)
    # wrap manually
    lines = []
    line = ""
    for w_ in asst.split():
        if len(line) + len(w_) > 80:
            lines.append(line); line = w_
        else:
            line = (line + " " + w_).strip()
    lines.append(line)
    yi = cy + 18
    for ln in lines:
        text(d, (cx + 22, yi), ln, font=f(14))
        yi += 22

    cy += 130
    # Product cards
    text(d, (cx, cy), "RECOMMENDED PRODUCTS", font=f(11, bold=True), fill=INK_DIM)
    cy += 22
    products = [
        ("Gluten-Free Devil's Food Cake Mix", "$8.95",  "easy",       0.91, GREEN),
        ("Classic Chocolate Cake Mix",        "$7.50",  "easy",       0.87, GREEN),
        ("Chocolate Bundt Cake Mix",          "$9.25",  "intermediate", 0.82, YELLOW),
    ]
    px = cx
    for i, (name, price, diff, score, dcolor) in enumerate(products):
        card(d, px, cy, 280, 130)
        text(d, (px + 18, cy + 16), name, font=f(13, bold=True))
        text(d, (px + 18, cy + 44), price, font=f(20, bold=True), fill=ACCENT)
        chip(d, px + 18, cy + 78, diff.upper(), fill=(232, 247, 235), ink=dcolor)
        text(d, (px + 18, cy + 110), f"similarity {score:.2f}", font=f(11, mono=True), fill=INK_DIM)
        px += 295

    # Right side — input box
    ix = 1180
    iy = 96
    d.rounded_rectangle((ix, iy, W - 24, H - 24), radius=12, fill=SURFACE, outline=BORDER)
    text(d, (ix + 20, iy + 22), "Ask the assistant", font=f(13, bold=True))
    text(d, (ix + 20, iy + 48), "Tip: try \"recommend\", \"compare\", or describe what you want to bake.",
         font=f(11), fill=INK_DIM)
    d.rounded_rectangle((ix + 20, iy + 80, W - 44, iy + 170), radius=8, fill=BG, outline=BORDER_SOFT)
    text(d, (ix + 32, iy + 96), "Type your message…", font=f(12, mono=True), fill=INK_DIM)
    d.rounded_rectangle((ix + 20, iy + 184, ix + 116, iy + 218), radius=6, fill=ACCENT)
    text(d, (ix + 68, iy + 201), "Send", font=f(12, bold=True), fill=SURFACE, anchor="mm")

    # Quick prompts
    qy = iy + 250
    text(d, (ix + 20, qy), "QUICK PROMPTS", font=f(11, bold=True), fill=INK_DIM)
    qy += 22
    for q in ["Compare pancake mixes", "What's in your bread mixes?", "Show vegan options", "Best for kids' baking"]:
        d.rounded_rectangle((ix + 20, qy, W - 44, qy + 34), radius=6, fill=BG, outline=BORDER_SOFT)
        text(d, (ix + 32, qy + 17), q, font=f(12), anchor="lm")
        qy += 42

    img.save(OUT / "chat.png", optimize=True)
    print("✓ chat.png")


# ─────────────────────────────────────────────────────────────
# workflow.png — LangGraph state machine
# ─────────────────────────────────────────────────────────────
def workflow():
    img, d = canvas()
    draw_topbar(d, "King Arthur Baking AI")
    draw_sidebar(d, "Agent Graph")

    text(d, (280, 88), "LangGraph state machine", font=f(20, bold=True))
    text(d, (280, 116), "Live graph — node colors indicate the path taken on the last run", font=f(13), fill=INK_DIM)

    # Helper to draw a node
    def node(cx, cy, label, sub, *, color=BLUE, taken=False):
        w_, h_ = 220, 80
        fill = color if taken else SURFACE
        ink_main = SURFACE if taken else INK
        ink_sub = (255, 255, 255, 180) if taken else INK_DIM
        d.rounded_rectangle((cx - w_ // 2, cy - h_ // 2, cx + w_ // 2, cy + h_ // 2),
                            radius=12, fill=fill, outline=color, width=2)
        text(d, (cx, cy - 12), label, font=f(15, bold=True), fill=ink_main, anchor="mm")
        text(d, (cx, cy + 18), sub, font=f(11, mono=True), fill=ink_sub, anchor="mm")

    def edge(x1, y1, x2, y2, *, color=BORDER, taken=False, label=None, dashed=False):
        c = color if not taken else ACCENT
        w_ = 2 if taken else 1
        if not dashed:
            d.line((x1, y1, x2, y2), fill=c, width=w_)
        else:
            steps = 18
            for i in range(steps):
                if i % 2 == 0:
                    sx = x1 + (x2 - x1) * (i / steps)
                    sy = y1 + (y2 - y1) * (i / steps)
                    ex = x1 + (x2 - x1) * ((i + 1) / steps)
                    ey = y1 + (y2 - y1) * ((i + 1) / steps)
                    d.line((sx, sy, ex, ey), fill=c, width=w_)
        # arrow head
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        ahx = x2 - 10 * math.cos(ang)
        ahy = y2 - 10 * math.sin(ang)
        d.polygon([(x2, y2),
                   (ahx - 5 * math.sin(ang), ahy + 5 * math.cos(ang)),
                   (ahx + 5 * math.sin(ang), ahy - 5 * math.cos(ang))], fill=c)
        if label:
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2
            bbox = d.textbbox((0, 0), label, font=f(11))
            tw = bbox[2] - bbox[0]
            d.rectangle((mid_x - tw // 2 - 6, mid_y - 10, mid_x + tw // 2 + 6, mid_y + 8), fill=BG)
            text(d, (mid_x, mid_y), label, font=f(11), fill=INK_DIM, anchor="mm")

    # Layout: top → 5-node funnel
    base_x = 800
    # analyse_query (top)
    node(base_x, 230, "analyse_query", "extract intent + tags", color=GREEN, taken=True)
    # route_decision
    node(base_x, 370, "route_decision", "conditional edge", color=BLUE, taken=True)
    # 3 branches
    node(base_x - 280, 510, "search", "semantic match", color=PURPLE, taken=False)
    node(base_x,        510, "recommend", "ranked candidates", color=PURPLE, taken=True)
    node(base_x + 280, 510, "compare", "side-by-side", color=PURPLE, taken=False)
    # reason
    node(base_x, 660, "reason", "ground in retrieved", color=YELLOW, taken=True)
    # respond
    node(base_x, 800, "respond", "final answer", color=ACCENT, taken=True)

    # Edges
    edge(base_x, 270, base_x, 330, taken=True)
    edge(base_x, 410, base_x - 280, 470, label="search", dashed=True)
    edge(base_x, 410, base_x,        470, label="recommend", taken=True)
    edge(base_x, 410, base_x + 280, 470, label="compare", dashed=True)
    edge(base_x - 280, 550, base_x - 30, 630, dashed=True)
    edge(base_x,        550, base_x,        620, taken=True)
    edge(base_x + 280, 550, base_x + 30, 630, dashed=True)
    edge(base_x, 700, base_x, 760, taken=True)

    # Right panel — run stats
    panel_x = 1280
    card(d, panel_x, 200, 290, 360)
    text(d, (panel_x + 20, 220), "Last run", font=f(13, bold=True))
    text(d, (panel_x + 20, 244), "Question 2:14 PM", font=f(11), fill=INK_DIM)
    rows = [
        ("Path",          "analyse → recommend → reason → respond"),
        ("Sources",       "4 products (cosine ≥ 0.81)"),
        ("LLM",           "gpt-4o (temp 0.2)"),
        ("Embedding",     "text-embedding-3-small"),
        ("Tokens",        "in 412   out 287"),
        ("Cost",          "$0.0034"),
        ("Latency",       "1.84 s"),
        ("Confidence",    "high"),
    ]
    ry = 274
    for k, v in rows:
        text(d, (panel_x + 20, ry), k, font=f(11), fill=INK_DIM)
        text(d, (panel_x + 110, ry), v, font=f(11, mono=True))
        ry += 22

    # State schema
    card(d, panel_x, 580, 290, 350)
    text(d, (panel_x + 20, 600), "AgentState (TypedDict)", font=f(13, bold=True))
    code = [
        ("question", "str"),
        ("intent", "Literal[search,"),
        ("",          "  recommend,"),
        ("",          "  compare]"),
        ("filters", "dict"),
        ("candidates", "list[Product]"),
        ("reasoning", "str"),
        ("answer", "str"),
    ]
    cy = 632
    for k, v in code:
        if k:
            text(d, (panel_x + 20, cy), f"{k}:", font=f(11, mono=True), fill=PURPLE)
            text(d, (panel_x + 120, cy), v, font=f(11, mono=True), fill=INK_SECOND)
        else:
            text(d, (panel_x + 120, cy), v, font=f(11, mono=True), fill=INK_SECOND)
        cy += 22

    img.save(OUT / "workflow.png", optimize=True)
    print("✓ workflow.png")


# ─────────────────────────────────────────────────────────────
# analytics.png
# ─────────────────────────────────────────────────────────────
def analytics():
    img, d = canvas()
    draw_topbar(d, "King Arthur Baking AI")
    draw_sidebar(d, "Analytics")

    text(d, (280, 88), "Catalog analytics", font=f(20, bold=True))
    text(d, (280, 116), "Derived from the indexed corpus", font=f(13), fill=INK_DIM)

    # KPI tiles
    kpis = [
        ("Indexed products", "47", "+3 this week", GREEN),
        ("Avg price", "$11.32", "+$0.42 vs last month", INK_DIM),
        ("Categories", "12", "cake · bread · muffin · …", INK_DIM),
        ("Vector dim", "1,536", "text-embedding-3-small", INK_DIM),
    ]
    kx = 280
    for label, value, delta, dcol in kpis:
        card(d, kx, 156, 220, 100)
        text(d, (kx + 18, 174), label, font=f(11, bold=True), fill=INK_DIM)
        text(d, (kx + 18, 200), value, font=f(28, bold=True))
        text(d, (kx + 18, 240), delta, font=f(11), fill=dcol)
        kx += 232

    # Price distribution histogram
    px, py, pw, ph = 280, 288, 690, 340
    card(d, px, py, pw, ph)
    text(d, (px + 22, py + 18), "Price distribution", font=f(15, bold=True))
    text(d, (px + 22, py + 42), "$0 to $30, 2-USD buckets", font=f(11), fill=INK_DIM)

    bars = [2, 4, 7, 9, 12, 10, 8, 6, 5, 3, 2, 1, 1, 0, 1]
    max_b = max(bars)
    bx0, by0 = px + 40, py + 290
    bw = (pw - 80) // len(bars)
    for i, b in enumerate(bars):
        bh = int(b / max_b * 180)
        bxi = bx0 + i * bw
        d.rectangle((bxi + 4, by0 - bh, bxi + bw - 4, by0), fill=ACCENT)
        if i % 2 == 0:
            text(d, (bxi + bw // 2, by0 + 10), f"${i * 2}", font=f(10), fill=INK_DIM, anchor="mt")
    # y axis ticks
    for v, lbl in [(0, "0"), (max_b // 2, str(max_b // 2)), (max_b, str(max_b))]:
        ytick = by0 - int(v / max_b * 180)
        text(d, (px + 30, ytick), lbl, font=f(10), fill=INK_DIM, anchor="rm")
        d.line((px + 35, ytick, px + pw - 35, ytick), fill=BORDER_SOFT, width=1)

    # Category breakdown (donut)
    cx, cy, cw, ch = 990, 288, 380, 340
    card(d, cx, cy, cw, ch)
    text(d, (cx + 22, cy + 18), "By category", font=f(15, bold=True))
    text(d, (cx + 22, cy + 42), "Top product groups", font=f(11), fill=INK_DIM)
    # donut chart (pie segments)
    import math
    cats = [
        ("Cake",      14, ACCENT),
        ("Bread",     11, BLUE),
        ("Muffin",     8, GREEN),
        ("Cookie",     6, YELLOW),
        ("Pancake",    4, PURPLE),
        ("Other",      4, (180, 170, 158)),
    ]
    total = sum(c for _, c, _ in cats)
    donut_cx, donut_cy, r1, r2 = cx + 130, cy + 200, 90, 50
    ang = -90
    for _name, count, color in cats:
        sweep = 360 * count / total
        d.pieslice((donut_cx - r1, donut_cy - r1, donut_cx + r1, donut_cy + r1),
                   ang, ang + sweep, fill=color)
        ang += sweep
    d.ellipse((donut_cx - r2, donut_cy - r2, donut_cx + r2, donut_cy + r2), fill=SURFACE)
    text(d, (donut_cx, donut_cy - 8), str(total), font=f(20, bold=True), anchor="mm")
    text(d, (donut_cx, donut_cy + 14), "products", font=f(10), fill=INK_DIM, anchor="mm")
    # legend
    lx = cx + 240
    ly = cy + 90
    for name, count, color in cats:
        d.rectangle((lx, ly + 4, lx + 12, ly + 16), fill=color)
        text(d, (lx + 22, ly + 4), name, font=f(11), anchor="lt")
        text(d, (cx + cw - 22, ly + 4), str(count), font=f(11, mono=True), fill=INK_DIM, anchor="rt")
        ly += 32

    # Top features bar chart
    bx, by, bw_, bh_ = 280, 656, pw, 256
    card(d, bx, by, bw_, bh_)
    text(d, (bx + 22, by + 18), "Most common features (tag counts)", font=f(15, bold=True))
    features = [
        ("gluten-free",       22),
        ("vegan-friendly",    14),
        ("organic-flour",     13),
        ("no-added-sugar",     9),
        ("kosher-certified",   8),
        ("non-GMO",            6),
    ]
    yy = by + 64
    max_v = max(v for _, v in features)
    for label, v in features:
        text(d, (bx + 22, yy + 8), label, font=f(12))
        bw_inner = int((bw_ - 280) * v / max_v)
        d.rectangle((bx + 200, yy + 4, bx + 200 + bw_inner, yy + 22), fill=ACCENT)
        text(d, (bx + 200 + bw_inner + 8, yy + 12), str(v), font=f(11, mono=True), fill=INK_DIM, anchor="lm")
        yy += 30

    # Right panel — embedding drift gauge
    rx = 990
    ry = 656
    card(d, rx, ry, cw, bh_)
    text(d, (rx + 22, ry + 18), "Embedding health", font=f(15, bold=True))
    text(d, (rx + 22, ry + 42), "Cosine-similarity diagnostics across the index", font=f(11), fill=INK_DIM)
    metrics = [
        ("Coverage",          "97 %", GREEN),
        ("Avg pairwise sim",  "0.34", INK),
        ("Drift vs baseline", "+0.02 σ", GREEN),
        ("Last reindex",      "2 days ago", INK_DIM),
        ("Empty-result rate", "2.1 %", INK),
        ("Reranker on top-5", "enabled", GREEN),
    ]
    my = ry + 76
    for name, value, color in metrics:
        text(d, (rx + 22, my), name, font=f(12), fill=INK_DIM)
        text(d, (rx + cw - 22, my), value, font=f(12, mono=True, bold=True), fill=color, anchor="rt")
        my += 26

    img.save(OUT / "analytics.png", optimize=True)
    print("✓ analytics.png")


# ─────────────────────────────────────────────────────────────
# landing.png
# ─────────────────────────────────────────────────────────────
def landing():
    img, d = canvas()
    draw_topbar(d, "King Arthur Baking AI")
    draw_sidebar(d, "Chat")

    # Hero
    hx, hy = 280, 100
    d.rounded_rectangle((hx, hy, W - 24, hy + 280), radius=16, fill=(255, 252, 248), outline=BORDER)
    # Big circle logo
    d.ellipse((hx + 40, hy + 40, hx + 140, hy + 140), fill=ACCENT)
    text(d, (hx + 90, hy + 90), "K", font=f(56, bold=True), fill=SURFACE, anchor="mm")
    text(d, (hx + 170, hy + 50), "King Arthur Baking AI", font=f(34, bold=True))
    text(d, (hx + 170, hy + 100),
         "RAG-powered product-catalog assistant.",
         font=f(18), fill=INK_SECOND)
    text(d, (hx + 170, hy + 130),
         "47 products indexed · MongoDB Atlas Vector Search · LangGraph agent",
         font=f(13), fill=INK_DIM)
    # CTAs
    chip(d, hx + 170, hy + 170, "Start a conversation", fill=ACCENT, ink=SURFACE, pad=(18, 12))

    # Big search box
    sx, sy = hx + 40, hy + 200
    d.rounded_rectangle((sx, sy, hx + 1200, sy + 60), radius=10, fill=SURFACE, outline=BORDER, width=2)
    text(d, (sx + 24, sy + 30), "Ask anything about King Arthur Baking mixes…",
         font=f(15, mono=True), fill=INK_DIM, anchor="lm")
    d.rounded_rectangle((hx + 1080, sy + 8, hx + 1190, sy + 52), radius=8, fill=ACCENT)
    text(d, (hx + 1135, sy + 30), "Ask →", font=f(14, bold=True), fill=SURFACE, anchor="mm")

    # Sample prompts row
    py = hy + 304
    text(d, (hx, py), "TRY ASKING", font=f(11, bold=True), fill=INK_DIM)
    py += 24
    cards_x = hx
    samples = [
        ("Recommend",
         "Recommend a gluten-free chocolate cake mix that's easy for beginners.",
         "↳ uses recommend route"),
        ("Compare",
         "Compare your three pancake mixes by ingredients and price.",
         "↳ uses compare route"),
        ("Search",
         "What ingredients are in your bread mixes?",
         "↳ uses semantic search"),
    ]
    cw_ = (W - 280 - 24 * 2 - 24 * 2) // 3
    for kind, q, hint in samples:
        card(d, cards_x, py, cw_, 130)
        chip(d, cards_x + 18, py + 18, kind.upper())
        # 2-line wrap of question
        words = q.split()
        line1 = []
        line2 = []
        chars = 0
        for w_ in words:
            if chars + len(w_) > 48 and not line2:
                line2 = [w_]
                chars = len(w_)
            elif line2:
                line2.append(w_)
            else:
                line1.append(w_)
                chars += len(w_) + 1
        text(d, (cards_x + 18, py + 56), " ".join(line1), font=f(14))
        if line2:
            text(d, (cards_x + 18, py + 78), " ".join(line2), font=f(14))
        text(d, (cards_x + 18, py + 104), hint, font=f(11, mono=True), fill=ACCENT)
        cards_x += cw_ + 24

    # System status row
    sy = py + 160
    text(d, (hx, sy), "SYSTEM", font=f(11, bold=True), fill=INK_DIM)
    sy += 24
    cards_x = hx
    items = [
        ("Catalog",    "47 products",       "scraped 2026-06-05", GREEN),
        ("Mongo",      "atlas connected",   "vector index v3",     GREEN),
        ("LLM",        "gpt-4o online",     "latency p50 1.4 s",   GREEN),
        ("Reranker",   "enabled",           "top-5 cross-encoder", GREEN),
    ]
    ttw = (W - 280 - 24 - 24 * 3) // 4
    for label, status, sub, sc in items:
        card(d, cards_x, sy, ttw, 84)
        d.ellipse((cards_x + 18, sy + 22, cards_x + 30, sy + 34), fill=sc)
        text(d, (cards_x + 40, sy + 28), label, font=f(13, bold=True), anchor="lm")
        text(d, (cards_x + 18, sy + 48), status, font=f(12), anchor="lt")
        text(d, (cards_x + 18, sy + 64), sub, font=f(11), fill=INK_DIM)
        cards_x += ttw + 24

    img.save(OUT / "landing.png", optimize=True)
    print("✓ landing.png")


if __name__ == "__main__":
    chat()
    workflow()
    analytics()
    landing()
    print(f"\nAll screenshots written to {OUT}")
