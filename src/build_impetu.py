import sys, json, random
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mag_lib import *
from texts_impetu import EDITORIAL3, RESIST, TIERRA

OUT = sys.argv[1] if len(sys.argv) > 1 else "../output/IMPETU.pdf"
AUTOR = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
c = cv.Canvas(OUT, pagesize=A4)
c.setTitle("Ímpetu – Revista de deporte y movimiento (Nº 01)")
c.setSubject("Tipos de deporte")
idml_export.configure(mag="impetu", cols=2, gutter=G, margins=(16 * mm, 24 * mm, 18 * mm, 18 * mm),
                      baseline=(16 * mm, 14.2), palette={
    "#5E1A35": "Vino", "#E7A82E": "Mostaza", "#1F6F78": "Verde azulado", "#EEF1F2": "Papel",
    "#1E1E24": "Tinta", "#C8454E": "Rosa", "#BFD9DF": "Cielo", "#6C7378": "Gris", "#C5CCCF": "Filete"})

# ---------- paleta propia ----------
WINE = HexColor("#5E1A35"); MUST = HexColor("#E7A82E"); TEAL = HexColor("#1F6F78")
PAPER = HexColor("#EEF1F2"); INK3 = HexColor("#1E1E24"); ROSE = HexColor("#C8454E")
SKY2 = HexColor("#BFD9DF"); GRAY3 = HexColor("#6C7378"); RULE = HexColor("#C5CCCF")

M3 = 18 * mm
TOP3 = H - 16 * mm
BOT3 = 24 * mm
CWID = (W - 2 * M3 - G) / 2          # ancho de columna (2 columnas)


def CX(i):
    return M3 + i * (CWID + G)


BODY3 = ParagraphStyle("b3", fontName="Serif", fontSize=9.4, leading=14.2, textColor=INK3, spaceAfter=6)
BODY3O = ParagraphStyle("b3o", parent=BODY3, fontSize=9.8, leading=14.8)
LEAD3 = ParagraphStyle("l3", fontName="Serif-BI", fontSize=12.6, leading=17.6, textColor=WINE, spaceAfter=9)
CAP3 = ParagraphStyle("c3", fontName="Sans", fontSize=6.8, leading=9, textColor=GRAY3)
DECK3 = lambda col=INK3, sz=12.4: ParagraphStyle("d3", fontName="Serif-I", fontSize=sz, leading=sz * 1.38, textColor=col)
BYL3 = ParagraphStyle("by3", fontName="Sans-SB", fontSize=6.6, leading=9, textColor=GRAY3, spaceAfter=8)


def report(tag, frames):
    print(tag, "libre (mm):", [round((f._y - f._y1) / mm) for f in frames])


def own(items, byline):
    out = [Paragraph(byline, BYL3)]
    for k, s in items:
        out.append(Paragraph(s, LEAD3 if k == "lead" else BODY3O))
    return out


def lorem3(seed, k):
    rng = random.Random(seed)
    out = []
    for i in range(k):
        txt = " ".join(lorem_sentence(rng) for _ in range(rng.randint(3, 5)))
        if i % 3 == 1:
            h = " ".join(rng.choice(LW) for _ in range(2)).capitalize()
            txt = '<font name="Sans-B" color="#5E1A35" size="8">%s.</font> %s' % (h.upper(), txt)
        out.append(Paragraph(txt, BODY3))
    return out


def bg(col=PAPER):
    c.setFillColor(col); c.rect(0, 0, W, H, stroke=0, fill=1)


def label(s, x, y, col=WINE, size=7, cs=2.2):
    text(c, s.upper(), x, y, "Sans-B", size, col, cs=cs)


def stitle(lines, x, ybase, size, col, lead=1.0, font="Serif-B"):
    for i, s in enumerate(lines):
        text(c, s, x, ybase - i * size * lead, font, size, col, cs=-0.6)


def footer3(n, dark=False):
    col = HexColor("#D8DCDE") if dark else GRAY3
    y = 11 * mm
    c.setStrokeColor(col); c.setLineWidth(0.4)
    c.line(M3, y + 5 * mm, W - M3, y + 5 * mm)
    lab = "REVISTA DE DEPORTE Y MOVIMIENTO  ·  Nº 01"
    if n % 2 == 0:
        text(c, "%02d" % n, M3, y - 0.5, "Serif-B", 12, MUST if dark else WINE)
        text(c, "Ímpetu", M3 + 10 * mm, y - 0.3, "Serif-BI", 10, col)
        text(c, lab, W - M3, y + 0.6, "Sans-SB", 5.8, col, "r", cs=1.4)
    else:
        text(c, "%02d" % n, W - M3, y - 0.5, "Serif-B", 12, MUST if dark else WINE, "r")
        text(c, "Ímpetu", W - M3 - 10 * mm, y - 0.3, "Serif-BI", 10, col, "r")
        text(c, lab, M3, y + 0.6, "Sans-SB", 5.8, col, cs=1.4)


def caption(x, y, w, s):
    c.setFillColor(WINE); c.rect(x, y - 2 * mm - 6.4, 2.2, 6.4, stroke=0, fill=1)
    para(c, s, CAP3, x + 4 * mm, y - 2 * mm, w - 4 * mm)


def infobox3(x, ytop, w, title, rows):
    rh = 7.2 * mm; th = 11 * mm; h = th + rh * len(rows) + 2 * mm
    c.setFillColor(WINE); c.rect(x, ytop - h, w, h, stroke=0, fill=1)
    c.setFillColor(MUST); c.rect(x, ytop - 2.2, 16 * mm, 2.2, stroke=0, fill=1)
    text(c, title.upper(), x + 4 * mm, ytop - 8 * mm, "Sans-B", 6.6, white, cs=1.3)
    for i, (a, b) in enumerate(rows):
        yy = ytop - th - rh * (i + 1) + 2.4 * mm
        c.setStrokeColor(HexColor("#85405A")); c.setLineWidth(0.4)
        c.line(x + 4 * mm, yy + rh - 2.2 * mm + 0.5, x + w - 4 * mm, yy + rh - 2.2 * mm + 0.5)
        text(c, a, x + 4 * mm, yy, "Serif", 8, white)
        text(c, b, x + w - 4 * mm, yy, "Sans-B", 7.6, MUST, "r")
    return h


def balanced_y0(story_fn, x0, x1, ytop, ncols, ymin, obst=()):
    for h in range(20, 400, 2):
        y0 = ytop - h * mm
        if y0 < ymin:
            break
        st = story_fn()
        fill(cv.Canvas(io.BytesIO()), st, make_frames(x0, y0, x1, ytop, ncols, obst=obst))
        if not st:
            return y0
    return ymin


def ib_h(n):
    return 11 * mm + 7.2 * mm * n + 2 * mm


# =================== ESCENAS ===================
def limb(p0, p1, w0, w1, col):
    """Extremidad ahusada con extremos redondeados (p en coordenadas absolutas)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    poly(c, [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
             (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)], fill=col)
    circle(c, p0[0], p0[1], w0 / 2, fill=col)
    circle(c, p1[0], p1[1], w1 / 2, fill=col)


def runner(x, y, s, col, lw=None):
    """Corredor de perfil, mirando a la derecha, en el instante del impulso. (x, y) = punta del pie de apoyo."""
    far = HexColor("#52525F") if col == INK3 else col
    def P(a, b): return (x + (a + 0.19) * s, y + (b - 0.01) * s)
    # brazo lejano
    limb(P(0.08, 0.79), P(-0.05, 0.69), 0.07 * s, 0.05 * s, far)
    limb(P(-0.05, 0.69), P(-0.13, 0.8), 0.05 * s, 0.042 * s, far)
    # pierna de impulso (atrás, extendida)
    limb(P(0.0, 0.52), P(-0.1, 0.29), 0.125 * s, 0.085 * s, col)
    limb(P(-0.1, 0.29), P(-0.27, 0.07), 0.085 * s, 0.05 * s, col)
    limb(P(-0.27, 0.07), P(-0.19, 0.01), 0.045 * s, 0.038 * s, col)
    # pierna adelantada (rodilla arriba)
    limb(P(0.0, 0.52), P(0.25, 0.56), 0.125 * s, 0.085 * s, col)
    limb(P(0.25, 0.56), P(0.2, 0.3), 0.085 * s, 0.052 * s, col)
    limb(P(0.2, 0.3), P(0.3, 0.27), 0.046 * s, 0.038 * s, col)
    # torso y cabeza
    limb(P(0.0, 0.52), P(0.08, 0.81), 0.125 * s, 0.14 * s, col)
    circle(c, *P(0.13, 0.93), 0.067 * s, fill=col)
    # brazo cercano
    limb(P(0.08, 0.79), P(0.2, 0.66), 0.072 * s, 0.052 * s, col)
    limb(P(0.2, 0.66), P(0.3, 0.76), 0.052 * s, 0.046 * s, col)


def S_sun(x, y, w, h):
    """Atardecer en el llano: sol con cortes, palmas de moriche en el horizonte y pista de atletismo
    en perspectiva con un corredor en fase de vuelo."""
    import cover_art as ca
    top_rgb, hor_rgb = (58, 14, 38), (205, 86, 72)
    hz = y + h * 0.44                                     # horizonte

    def sky(yy):                                          # color del cielo a la altura yy
        t = max(0.0, min(1.0, (y + h - yy) / (y + h - hz)))
        return HexColor("#%02x%02x%02x" % tuple(int(top_rgb[i] + (hor_rgb[i] - top_rgb[i]) * t) for i in range(3)))

    clip_rect(c, x, y, w, h)
    grad_bands(c, x, hz, w, y + h - hz, top_rgb, hor_rgb, 60)
    # sol con cortes del color del cielo (se ve el cielo a través de ellos)
    R = min(w * 0.34, h * 0.25)
    cx, cy = x + w * 0.57, hz + R * 0.1
    circle(c, cx, cy, R, fill=MUST)
    c.saveState()
    p = c.beginPath(); p.circle(cx, cy, R); c.clipPath(p, stroke=0, fill=0)
    halftone(c, cx - R, hz, 2 * R, R * 0.9, HexColor("#C8454E"), step=6, rmax=1.9, mode="bottom", alpha=0.55)
    for i in range(6):
        yy = cy + R * 0.5 - i * R * 0.11
        th = R * (0.012 + i * 0.011)
        c.setFillColor(sky(yy)); c.rect(cx - R, yy - th, 2 * R, th, stroke=0, fill=1)
    c.restoreState()
    # horizonte: lomas bajas y palmas de moriche
    HILL = HexColor("#17414A"); FAR = HexColor("#0E2B31")
    pts = [(x, hz - 2)]
    for i in range(41):
        t = i / 40
        pts.append((x + w * t, hz + h * 0.012 * (1 + math.sin(t * 9.0) * 0.6 + math.sin(t * 23 + 1) * 0.3)))
    pts.append((x + w, hz - 2))
    poly(c, pts, fill=HILL)
    for px, ph, sd in [(0.07, 0.10, 1), (0.14, 0.07, 2), (0.86, 0.085, 3), (0.94, 0.065, 4)]:
        ca.palm(c, x + w * px, hz + h * 0.008, h * ph, FAR, lean=(-5 if sd % 2 else 7), seed=sd)
    # suelo: franja de césped, pista vista de lado (calles paralelas al horizonte) e interior oscuro
    c.setFillColor(HexColor("#123840")); c.rect(x, y, w, hz - y, stroke=0, fill=1)
    t_top, t_bot = hz - h * 0.025, hz - h * 0.19
    c.setFillColor(HexColor("#A8453F")); c.rect(x, t_bot, w, t_top - t_bot, stroke=0, fill=1)
    lanes = [t_top - (t_top - t_bot) * (k / 5) ** 1.3 for k in range(6)]   # más anchas hacia delante
    for k, ly in enumerate(lanes):
        th = 0.5 + 1.9 * (k / 5)
        c.setFillColor(HexColor("#EEF1F2")); c.rect(x, ly - th / 2, w, th, stroke=0, fill=1)
    # corredor en la calle 3, en fase de vuelo, con su sombra en el suelo
    s = h * 0.33
    gy = (lanes[2] + lanes[3]) / 2
    gx = x + w * 0.40
    c.saveState(); c.setFillColor(HexColor("#3A0F1E")); c.setFillAlpha(0.5)
    c.ellipse(gx - s * 0.26, gy - s * 0.022, gx + s * 0.2, gy + s * 0.012, stroke=0, fill=1)
    c.restoreState()
    ca.runner(c, gx, gy, s, INK3, HexColor("#4A4A58"))
    c.restoreState()


def S_bike(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(TEAL); c.rect(x, y, w, h, stroke=0, fill=1)
    circle(c, x + w * 0.78, y + h * 0.7, h * 0.2, fill=MUST)
    c.setFillColor(HexColor("#17414A")); c.rect(x, y, w, h * 0.2, stroke=0, fill=1)
    u = h * 0.26
    ox, oy = x + w * 0.27, y + h * 0.2 + u
    def P(a, b): return ox + u * a, oy + u * b
    for cxw in (0.0, 2.3):
        circle(c, *P(cxw, 0), u * 1.0, fill=None, stroke=INK3, lw=u * 0.09)
        for k in range(12):
            a = math.radians(k * 30)
            line(c, *P(cxw, 0), *P(cxw + math.cos(a), math.sin(a)), HexColor("#DDE5E7"), 0.8, 0)
        circle(c, *P(cxw, 0), u * 0.08, fill=INK3)
    fr = [(0.0, 0.0), (1.05, 0.0), (0.85, 0.95), (1.9, 0.95), (1.05, 0.0)]
    c.setStrokeColor(MUST); c.setLineWidth(u * 0.09); c.setLineCap(1); c.setLineJoin(1)
    p = c.beginPath(); p.moveTo(*P(*fr[0]))
    for q in fr[1:]:
        p.lineTo(*P(*q))
    c.drawPath(p, stroke=1, fill=0)
    line(c, *P(0.0, 0.0), *P(0.85, 0.95), MUST, u * 0.09)
    line(c, *P(1.9, 0.95), *P(2.3, 0.0), MUST, u * 0.09)
    line(c, *P(1.9, 0.95), *P(1.78, 1.12), MUST, u * 0.09)
    # ciclista
    c.setStrokeColor(WINE); c.setLineWidth(u * 0.22)
    p = c.beginPath(); p.moveTo(*P(0.85, 1.05)); p.lineTo(*P(1.75, 1.6)); c.drawPath(p, stroke=1, fill=0)
    p = c.beginPath(); p.moveTo(*P(0.85, 1.05)); p.lineTo(*P(1.3, 0.62)); p.lineTo(*P(1.12, 0.08)); c.drawPath(p, stroke=1, fill=0)
    c.setLineWidth(u * 0.13)
    p = c.beginPath(); p.moveTo(*P(1.7, 1.55)); p.lineTo(*P(1.9, 1.1)); c.drawPath(p, stroke=1, fill=0)
    circle(c, *P(1.98, 1.78), u * 0.22, fill=WINE)
    for k in range(5):
        line(c, x + w * 0.03, y + h * (0.35 + k * 0.1), x + w * (0.08 + (k % 3) * 0.03), y + h * (0.35 + k * 0.1), SKY2, 2)
    c.restoreState()


def S_road(x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (250, 214, 150), (231, 168, 46), 30)
    vx, vy = x + w * 0.5, y + h * 0.5
    circle(c, vx, vy + h * 0.06, h * 0.18, fill=HexColor("#F6E4B4"))
    poly(c, [(x, y + h * 0.5), (x + w * 0.3, y + h * 0.62), (x + w * 0.55, y + h * 0.5), (x + w * 0.8, y + h * 0.58), (x + w, y + h * 0.5), (x + w, y), (x, y)], fill=TEAL)
    poly(c, [(x, y + h * 0.5), (x + w * 0.2, y + h * 0.56), (x + w * 0.45, y + h * 0.5), (x, y + h * 0.4)], fill=HexColor("#17606A"))
    poly(c, [(x - w * 0.3, y), (vx - 4, vy), (vx + 4, vy), (x + w * 1.3, y)], fill=INK3)
    for k in range(7):
        t0 = (k / 7.0) ** 1.7; t1 = ((k + 0.5) / 7.0) ** 1.7
        yy0 = vy - (vy - y) * t0; yy1 = vy - (vy - y) * t1
        ww0 = 1 + 7 * t0 ** 1.0 * 4; ww1 = 1 + 7 * t1 * 4
        poly(c, [(vx - ww0, yy0), (vx + ww0, yy0), (vx + ww1, yy1), (vx - ww1, yy1)], fill=white)
    c.restoreState()


def S_lift(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(TEAL); c.rect(x, y, w, h, stroke=0, fill=1)
    for i in range(6):
        circle(c, x + w * 0.5, y + h * 0.55, h * (0.18 + i * 0.1), fill=None, stroke=HexColor("#2A7F89" if i % 2 else "#195F68"), lw=7)
    c.setFillColor(INK3); c.rect(x, y, w, h * 0.14, stroke=0, fill=1)
    by = y + h * 0.5
    c.setFillColor(HexColor("#C9D0D3")); c.roundRect(x + w * 0.03, by - 3, w * 0.94, 6, 3, stroke=0, fill=1)
    for side in (-1, 1):
        for k, (ww, hh, col) in enumerate([(w * 0.045, h * 0.62, WINE), (w * 0.035, h * 0.5, MUST), (w * 0.03, h * 0.38, ROSE)]):
            xx = x + w * 0.5 + side * (w * 0.2 + sum([w * 0.045, w * 0.035, w * 0.03][:k]) * 1.08) - (ww if side < 0 else 0) * 0
            c.setFillColor(col); c.roundRect(xx - ww / 2, by - hh / 2, ww, hh, 3, stroke=0, fill=1)
    c.setFillColor(HexColor("#9AA3A7"))
    for side in (-1, 1):
        c.rect(x + w * 0.5 + side * w * 0.31 - 3, by - 10, 6, 20, stroke=0, fill=1)
    c.restoreState()


def S_sprint(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(WINE); c.rect(x, y, w, h, stroke=0, fill=1)
    n = 8
    for i in range(n):
        c.setFillColor(HexColor("#6B2140" if i % 2 else "#5E1A35")); c.rect(x, y + i * h / n, w, h / n, stroke=0, fill=1)
    for k in range(9):
        yy = y + h * (0.12 + k * 0.1)
        line(c, x + w * (0.02 + (k % 4) * 0.03), yy, x + w * (0.42 + (k % 3) * 0.07), yy, MUST if k % 2 else ROSE, 3)
    s = fit_size("9,58", "Serif-B", w * 0.38, maxsize=240, cs=-4)
    text(c, "9,58", x + w * 0.96, y + h * 0.22, "Serif-B", s, MUST, "r", cs=-4)
    text(c, "SEGUNDOS · 100 M · BERLÍN 2009", x + w * 0.96, y + h * 0.1, "Sans-B", 7.4, white, "r", cs=2.4)
    c.restoreState()


def S_balance(x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (191, 217, 223), (250, 236, 200), 30)
    circle(c, x + w * 0.72, y + h * 0.7, h * 0.14, fill=MUST)
    poly(c, [(x, y), (x, y + h * 0.28), (x + w * 0.5, y + h * 0.2), (x + w, y + h * 0.3), (x + w, y)], fill=TEAL)
    for tx in (0.1, 0.9):
        c.setFillColor(INK3); c.rect(x + w * tx - 5, y + h * 0.2, 10, h * 0.5, stroke=0, fill=1)
        for j in range(3):
            poly(c, [(x + w * tx - h * 0.16 + j * 4, y + h * (0.5 + j * 0.1)), (x + w * tx, y + h * (0.72 + j * 0.1)), (x + w * tx + h * 0.16 - j * 4, y + h * (0.5 + j * 0.1))], fill=HexColor("#17606A"))
    p = c.beginPath(); p.moveTo(x + w * 0.1, y + h * 0.5)
    p.curveTo(x + w * 0.35, y + h * 0.46, x + w * 0.65, y + h * 0.46, x + w * 0.9, y + h * 0.5)
    c.setStrokeColor(WINE); c.setLineWidth(3.4); c.drawPath(p, stroke=1, fill=0)
    # equilibrista
    px, py = x + w * 0.5, y + h * 0.47
    s = h * 0.3
    c.setStrokeColor(INK3); c.setLineWidth(s * 0.07); c.setLineCap(1)
    line(c, px, py, px, py + s * 0.5, INK3, s * 0.1)
    line(c, px, py, px - s * 0.12, py - s * 0.02, INK3, s * 0.07)
    line(c, px, py + s * 0.45, px - s * 0.6, py + s * 0.62, INK3, s * 0.06)
    line(c, px, py + s * 0.45, px + s * 0.6, py + s * 0.7, INK3, s * 0.06)
    line(c, px, py + s * 0.05, px + s * 0.1, py - s * 0.28, INK3, s * 0.07)
    circle(c, px, py + s * 0.64, s * 0.1, fill=INK3)
    c.restoreState()


def S_chess(x, y, w, h):
    clip_rect(c, x, y, w, h)
    n = 8
    sq = max(w, h) / 5.5
    c.setFillColor(WINE); c.rect(x, y, w, h, stroke=0, fill=1)
    ox = x + w * 0.5 - sq * 4; oy = y + h * 0.5 - sq * 4
    for i in range(n):
        for j in range(n):
            if (i + j) % 2 == 0:
                c.setFillColor(HexColor("#EADFCB")); c.rect(ox + i * sq, oy + j * sq, sq, sq, stroke=0, fill=1)
    def pawn(px, py, sc, col, king=False):
        c.setFillColor(col)
        circle(c, px, py + sc * 1.35, sc * 0.3, fill=col)
        poly(c, [(px - sc * 0.14, py + sc * 1.1), (px + sc * 0.14, py + sc * 1.1), (px + sc * 0.42, py + sc * 0.2), (px - sc * 0.42, py + sc * 0.2)], fill=col)
        c.roundRect(px - sc * 0.55, py, sc * 1.1, sc * 0.24, 3, stroke=0, fill=1)
        if king:
            c.setFillColor(MUST)
            c.rect(px - sc * 0.05, py + sc * 1.7, sc * 0.1, sc * 0.42, stroke=0, fill=1)
            c.rect(px - sc * 0.16, py + sc * 1.86, sc * 0.32, sc * 0.1, stroke=0, fill=1)
    sc = sq * 0.5
    pawn(x + w * 0.3, y + h * 0.3, sc, INK3, king=True)
    pawn(x + w * 0.52, y + h * 0.45, sc * 0.8, white)
    pawn(x + w * 0.72, y + h * 0.28, sc * 0.8, INK3)
    pawn(x + w * 0.62, y + h * 0.62, sc * 0.9, white, king=True)
    c.restoreState()


def S_land(x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (94, 26, 53), (240, 160, 70), 40)
    circle(c, x + w * 0.75, y + h * 0.42, h * 0.2, fill=MUST)
    poly(c, [(x, y), (x, y + h * 0.3), (x + w * 0.4, y + h * 0.27), (x + w, y + h * 0.31), (x + w, y)], fill=HexColor("#17414A"))
    poly(c, [(x, y), (x, y + h * 0.2), (x + w * 0.5, y + h * 0.16), (x + w, y + h * 0.21), (x + w, y)], fill=INK3)
    # palma
    tx, ty = x + w * 0.2, y + h * 0.27
    p = c.beginPath(); p.moveTo(tx, ty); p.curveTo(tx + 10, ty + h * 0.2, tx - 6, ty + h * 0.32, tx + 4, ty + h * 0.45)
    c.setStrokeColor(INK3); c.setLineWidth(5); c.setLineCap(1); c.drawPath(p, stroke=1, fill=0)
    top = (tx + 4, ty + h * 0.45)
    for a in (160, 130, 100, 60, 30, 10):
        r = h * 0.2
        ex, ey = top[0] + r * math.cos(math.radians(a)), top[1] + r * 0.6 * math.sin(math.radians(a)) - (abs(math.cos(math.radians(a))) * r * 0.35)
        p = c.beginPath(); p.moveTo(*top); p.curveTo(top[0] + (ex - top[0]) * 0.4, top[1] + r * 0.5, top[0] + (ex - top[0]) * 0.8, top[1] + r * 0.4, ex, ey)
        c.setLineWidth(3.4); c.drawPath(p, stroke=1, fill=0)
    # pelota de béisbol
    bx, by, br = x + w * 0.84, y + h * 0.16, h * 0.15
    circle(c, bx, by, br, fill=PAPER)
    c.setStrokeColor(ROSE); c.setLineWidth(2)
    p = c.beginPath(); p.arc(bx - br * 1.6, by - br, bx - br * 0.2, by + br, -50, 100); c.drawPath(p, stroke=1, fill=0)
    p = c.beginPath(); p.arc(bx + br * 0.2, by - br, bx + br * 1.6, by + br, 130, 100); c.drawPath(p, stroke=1, fill=0)
    # bate
    c.saveState(); c.translate(x + w * 0.6, y + h * 0.1); c.rotate(28)
    c.setFillColor(HexColor("#C98A4B")); c.roundRect(0, 0, h * 0.5, h * 0.045, h * 0.02, stroke=0, fill=1)
    c.setFillColor(HexColor("#C98A4B")); c.roundRect(h * 0.28, -h * 0.006, h * 0.24, h * 0.06, h * 0.025, stroke=0, fill=1)
    c.restoreState()
    c.restoreState()


# =================== ANUNCIOS (cuadro de una columna) ===================
AD_W = CWID
AD_H = 112 * mm
AD_Y = BOT3 + 2 * mm


def ad_btn(x, y, w, s, fillc, txtc):
    c.setFillColor(fillc); c.roundRect(x, y, w, 8 * mm, 4 * mm, stroke=0, fill=1)
    text(c, s, x + w / 2, y + 2.8 * mm, "Sans-B", 7, txtc, "c", cs=1.2)


def ad_note(x, y, col):
    text(c, "Anuncio ficticio realizado con fines académicos.", x, y, "Sans", 5.6, col)


def ad_trazo(x, y, w, h):
    c.setFillColor(TEAL); c.rect(x, y, w, h, stroke=0, fill=1)
    cx, cy, R = x + w * 0.5, y + h * 0.66, h * 0.19
    c.setFillColor(INK3); c.rect(cx - R * 0.45, cy + R * 0.9, R * 0.9, R * 1.3, stroke=0, fill=1)
    c.rect(cx - R * 0.45, cy - R * 2.2, R * 0.9, R * 1.3, stroke=0, fill=1)
    circle(c, cx, cy, R * 1.1, fill=INK3); circle(c, cx, cy, R * 0.95, fill=PAPER)
    for k in range(12):
        a = math.radians(k * 30)
        line(c, cx + R * 0.8 * math.cos(a), cy + R * 0.8 * math.sin(a), cx + R * 0.9 * math.cos(a), cy + R * 0.9 * math.sin(a), INK3, 1.2, 0)
    line(c, cx, cy, cx + R * 0.45, cy + R * 0.3, WINE, 2.6)
    line(c, cx, cy, cx - R * 0.1, cy + R * 0.6, MUST, 2)
    text(c, "TRAZO", x + 5 * mm, y + h - 9 * mm, "Sans-B", 8.6, MUST, cs=3.4)
    para(c, "El tiempo, a tu muñeca.", ParagraphStyle("t", fontName="Serif-BI", fontSize=19, leading=21, textColor=white), x + 5 * mm, y + 36 * mm, w - 10 * mm)
    para(c, "Relojes deportivos con GPS y 7 días de batería.", ParagraphStyle("t2", fontName="Sans", fontSize=7.8, leading=10.4, textColor=SKY2), x + 5 * mm, y + 22 * mm, w - 10 * mm)
    ad_btn(x + 5 * mm, y + 9 * mm, 34 * mm, "CONÓCELO", MUST, INK3)
    ad_note(x + 5 * mm, y + 4 * mm, SKY2)


def ad_vertice(x, y, w, h):
    c.setFillColor(MUST); c.rect(x, y, w, h, stroke=0, fill=1)
    clip_rect(c, x, y, w, h)
    cx, cy, R = x + w * 0.5, y + h * 0.68, h * 0.23
    circle(c, cx, cy, R, fill=None, stroke=WINE, lw=R * 0.12)
    for k in range(16):
        a = math.radians(k * 22.5)
        line(c, cx, cy, cx + R * math.cos(a), cy + R * math.sin(a), WINE, 0.9, 0)
    circle(c, cx, cy, R * 0.1, fill=WINE)
    c.restoreState()
    text(c, "VÉRTICE", x + 5 * mm, y + h - 9 * mm, "Sans-B", 8.6, WINE, cs=3.4)
    para(c, "Hecha para rodar.", ParagraphStyle("v", fontName="Serif-BI", fontSize=21, leading=23, textColor=INK3), x + 5 * mm, y + 34 * mm, w - 10 * mm)
    para(c, "Bicicletas de ruta ligeras, listas para tu próxima salida.", ParagraphStyle("v2", fontName="Sans", fontSize=7.8, leading=10.4, textColor=INK3), x + 5 * mm, y + 22 * mm, w - 10 * mm)
    ad_btn(x + 5 * mm, y + 9 * mm, 34 * mm, "PRUÉBALA", WINE, white)
    ad_note(x + 5 * mm, y + 4 * mm, INK3)


def ad_raiz(x, y, w, h):
    c.setFillColor(WINE); c.rect(x, y, w, h, stroke=0, fill=1)
    clip_rect(c, x, y, w, h)
    cx, cy = x + w * 0.5, y + h * 0.66
    for sgn, col in ((1, MUST), (-1, ROSE)):
        p = c.beginPath(); p.moveTo(cx, cy - h * 0.16)
        p.curveTo(cx + sgn * h * 0.3, cy - h * 0.05, cx + sgn * h * 0.28, cy + h * 0.2, cx, cy + h * 0.24)
        p.curveTo(cx - sgn * h * 0.02, cy + h * 0.1, cx - sgn * h * 0.02, cy - h * 0.05, cx, cy - h * 0.16)
        c.setFillColor(col); c.drawPath(p, stroke=0, fill=1)
    line(c, cx, cy - h * 0.22, cx, cy + h * 0.2, WINE, 2)
    c.restoreState()
    text(c, "RAÍZ", x + 5 * mm, y + h - 9 * mm, "Sans-B", 8.6, MUST, cs=3.4)
    para(c, "Fuerza que nace de la tierra.", ParagraphStyle("r", fontName="Serif-BI", fontSize=17, leading=19, textColor=white), x + 5 * mm, y + 38 * mm, w - 10 * mm)
    para(c, "Proteína vegetal para entrenar y recuperarte mejor.", ParagraphStyle("r2", fontName="Sans", fontSize=7.8, leading=10.4, textColor=HexColor("#E8C9D4")), x + 5 * mm, y + 20.5 * mm, w - 10 * mm)
    ad_btn(x + 5 * mm, y + 8.5 * mm, 34 * mm, "DESCÚBRELA", MUST, INK3)
    ad_note(x + 5 * mm, y + 4 * mm, HexColor("#E8C9D4"))


# ---- ilustraciones sustituibles por imágenes generadas (ver imgslots.py) ----
import imgslots
S_sun = imgslots.wrap(S_sun, "impetu", "sol_portada", lambda: c)
S_bike = imgslots.wrap(S_bike, "impetu", "bicicleta", lambda: c)
S_road = imgslots.wrap(S_road, "impetu", "camino", lambda: c)
S_lift = imgslots.wrap(S_lift, "impetu", "pesas", lambda: c)
S_balance = imgslots.wrap(S_balance, "impetu", "equilibrio", lambda: c)
S_chess = imgslots.wrap(S_chess, "impetu", "ajedrez", lambda: c)
S_land = imgslots.wrap(S_land, "impetu", "nuestra_tierra", lambda: c)


# =================== 01 PORTADA ===================
def cover():
    import cover_art as ca
    S_sun(0, 0, W, H)
    scrim(c, 0, H - 70 * mm, W, 70 * mm, color=HexColor("#3C0F24"), amax=0.9, up=False)
    scrim(c, 0, 0, W, 92 * mm, color=HexColor("#1A0712"), amax=0.88)
    ms = fit_size("Ímpetu", "Serif-BI", W - 2 * M3, maxsize=200, cs=-5)
    text(c, "Ímpetu", M3 - 3, H - 22 * mm - ms * 0.7, "Serif-BI", ms, white, cs=-5)
    yb = H - 22 * mm - ms * 0.7 - ms * 0.27 - 4 * mm
    text(c, "REVISTA DE DEPORTE Y MOVIMIENTO", M3, yb, "Sans-B", 8, white, cs=3.4)
    text(c, "Nº 01 · OCTUBRE 2026", W - M3, yb, "Sans-B", 8, white, "r", cs=2)
    c.setFillColor(white); c.rect(M3, yb - 4 * mm, W - 2 * M3, 1, stroke=0, fill=1)
    label("Especial · el cuerpo en movimiento", M3, 67 * mm, MUST)
    for i, s in enumerate(["Cada cuerpo,", "su deporte."]):
        text(c, s, M3, 54.5 * mm - i * 15.5 * mm, "Serif-BI", 46, white, cs=-1.2)
    items = [("03", "Resistencia", "llegar más lejos sin rendirse"),
             ("06", "Velocidad", "9,58 segundos que cambiaron todo"),
             ("09", "Nuestra tierra", "béisbol, bolas criollas y coleo")]
    for i, (n, t, d) in enumerate(items):
        yy = 26 * mm - i * 6.2 * mm
        text(c, n, M3, yy, "Serif-B", 11, MUST)
        tw = pdfmetrics.stringWidth(t.upper(), "Sans-B", 7) + 1.3 * len(t)
        text(c, t.upper(), M3 + 8 * mm, yy + 0.4, "Sans-B", 7, white, cs=1.3)
        text(c, d, M3 + 8 * mm + tw + 2.5 * mm, yy + 0.4, "Serif-I", 9, HexColor("#E9C9CF"))
    ca.barcode(c, W - M3 - 28 * mm, 10 * mm, 28 * mm, 18 * mm, "759100260013", text,
               ink=HexColor("#1E1E24"), paper=HexColor("#EEF1F2"), label="EJEMPLAR ACADÉMICO")
    ca.author_credit(c, W - M3, 44 * mm, AUTOR, text, MUST, white, HexColor("#E9C9CF"))


# =================== 02 EDITORIAL + ÍNDICE ===================
PAN2 = 118 * mm


def editorial_indice():
    bg()
    label("Carta de la redacción", M3, TOP3 - 3)
    stitle(["Editorial"], M3 - 1, TOP3 - 22 * mm, 48, WINE)
    c.setFillColor(MUST); c.rect(M3, TOP3 - 28 * mm, 20 * mm, 2.4, stroke=0, fill=1)
    EB = ParagraphStyle("eb3", parent=BODY3, fontSize=11, leading=16.6, spaceAfter=8)
    EL = ParagraphStyle("el3", parent=LEAD3, fontSize=15, leading=21, spaceAfter=11)
    def estory():
        return [Paragraph(EDITORIAL3[0], EL)] + [Paragraph(p, EB) for p in EDITORIAL3[1:]] + [Paragraph('<font name="Sans-B" size="7" color="#5E1A35">—  LA REDACCIÓN DE ÍMPETU</font>', BODY3)]
    ytop = TOP3 - 34 * mm
    y0 = balanced_y0(estory, M3, W - M3, ytop, 2, PAN2 + 6 * mm)
    st = estory()
    fr = make_frames(M3, y0, W - M3, ytop, ncols=2)
    fill(c, st, fr); report("editorial", fr)
    assert not st, "editorial desborda"
    gy = y0 - 10 * mm
    c.setFillColor(MUST); c.rect(M3, gy, 20 * mm, 2.4, stroke=0, fill=1)
    para(c, "Nos movemos porque estamos hechos para ello: lo único que cambia es cómo.", ParagraphStyle("pq", fontName="Serif-BI", fontSize=24, leading=30, textColor=WINE), M3, gy - 6 * mm, W - 2 * M3 - 30 * mm)
    # índice: panel vino a sangre
    c.setFillColor(WINE); c.rect(0, 0, W, PAN2, stroke=0, fill=1)
    label("En este número", M3, PAN2 - 12 * mm, MUST)
    stitle(["Índice"], M3 - 1, PAN2 - 30 * mm, 34, white)
    rows = [("02", "Editorial", "Carta de la redacción"),
            ("03", "Resistencia", "Llegar más lejos"),
            ("05", "Fuerza", "El peso de la constancia"),
            ("06", "Velocidad", "Cada centésima cuenta"),
            ("07", "Equilibrio", "Cuerpo en movimiento"),
            ("08", "Estrategia", "Jugar con la mente"),
            ("09", "Nuestra tierra", "Juegos y deportes de casa")]
    y = PAN2 - 42 * mm
    xr = W - M3
    for n, t, d in rows:
        text(c, t, M3, y, "Serif-B", 12, white)
        text(c, d, M3 + 46 * mm, y + 0.4, "Serif-I", 9, HexColor("#E0B8C6"))
        text(c, n, xr, y, "Serif-B", 12, MUST, "r")
        c.setStrokeColor(HexColor("#85405A")); c.setLineWidth(0.5); c.setDash(1, 2.4)
        c.line(M3 + 46 * mm + pdfmetrics.stringWidth(d, "Serif-I", 9) + 3 * mm, y + 1.2, xr - 9 * mm, y + 1.2)
        c.setDash()
        y -= 9.4 * mm
    if AUTOR:
        L = AUTOR["lineas"]
        yb = PAN2 - 18 * mm
        text(c, "REVISTA ELABORADA POR", xr, yb + 4.6 * mm, "Sans-B", 5.8, MUST, "r", cs=1.5)
        text(c, L[0], xr, yb, "Sans-SB", 8.4, white, "r")
        for j, s in enumerate(L[1:]):
            text(c, s, xr, yb - (4 + j * 3.3) * mm, "Sans", 6.6, HexColor("#E0B8C6"), "r")
    c.setFillColor(WINE)
    if not AUTOR:
        pass
    c.showPage()


# =================== 03-04 RESISTENCIA (texto propio) ===================
SC3 = 118 * mm


def p3_frames():
    y1 = H - 16 * mm - 62 * mm - SC3 - 10 * mm - 18 * mm
    return make_frames(M3, BOT3, W - M3, y1, ncols=2)


P4 = {"img": 118 * mm}


def leftover3():
    st = own(RESIST, "POR LA REDACCIÓN   ·   4 MIN DE LECTURA")
    fill(cv.Canvas(io.BytesIO()), st, p3_frames())
    return st


def p4_ytop():
    return H - P4["img"] - 14 * mm


def resistencia():
    st = own(RESIST, "POR LA REDACCIÓN   ·   4 MIN DE LECTURA")
    bg()
    label("Resistencia", M3, TOP3 - 3)
    stitle(["Llegar", "más lejos"], M3 - 1, TOP3 - 24 * mm, 54, WINE, lead=0.98)
    yim = H - 16 * mm - 62 * mm
    S_bike(M3, yim - SC3, W - 2 * M3, SC3)
    caption(M3, yim - SC3, W - 2 * M3, "La bicicleta convierte la constancia en distancia: pedalada a pedalada.")
    para(c, "Maratón, ciclismo de ruta, remo y triatlón: el arte de no detenerse.", DECK3(INK3, 12.2), M3, yim - SC3 - 14 * mm, W - 2 * M3)
    fr = p3_frames(); fill(c, st, fr); report("resistencia p3", fr)
    footer3(3); c.showPage()
    # p4
    bg()
    ih = P4["img"]
    S_road(0, H - ih, W, ih)
    scrim(c, 0, H - ih, W, 40 * mm, color=HexColor("#3C0F24"), amax=0.5)
    label("Resistencia · continúa", M3, H - 14 * mm, white)
    para(c, "“Los grandes resultados son la suma de muchos pasos pequeños.”", ParagraphStyle("q", fontName="Serif-BI", fontSize=21, leading=26, textColor=white), M3, H - ih + 50 * mm, 80 * mm)
    yt = p4_ytop()
    y0 = balanced_y0(leftover3, M3, W - M3, yt, 2, BOT3 + 44 * mm)
    fr = make_frames(M3, y0, W - M3, yt, ncols=2); fill(c, st, fr); report("resistencia p4", fr)
    yb = BOT3 + 2 * mm; hb = 30 * mm
    c.setFillColor(WINE); c.rect(M3, yb, W - 2 * M3, hb, stroke=0, fill=1)
    c.setFillColor(MUST); c.rect(M3, yb + hb - 2.2, 16 * mm, 2.2, stroke=0, fill=1)
    text(c, "RESISTENCIA EN CIFRAS", M3 + 5 * mm, yb + hb - 8.5 * mm, "Sans-B", 6.6, white, cs=1.3)
    cwb = (W - 2 * M3) / 4
    for i, (a, b) in enumerate([("42,195 km", "maratón"), ("21 etapas", "tour de francia"), ("≈ 226 km", "ironman"), ("2.000 m", "remo olímpico")]):
        xx = M3 + 5 * mm + i * cwb
        text(c, a, xx, yb + 8 * mm, "Serif-B", 14, white)
        text(c, b.upper(), xx, yb + 3.4 * mm, "Sans-B", 5.8, MUST, cs=1.2)
    assert not st, "resistencia desborda"
    footer3(4); c.showPage()


# =================== 05 FUERZA + TRAZO ===================
def p5_frames():
    y1 = H - 66 * mm
    img = (CX(0), y1 - 78 * mm, CX(0) + CWID, y1)
    ad = (CX(1), AD_Y, CX(1) + CWID, AD_Y + AD_H)
    box = (CX(1), y1 - ib_h(3), CX(1) + CWID, y1)
    return make_frames(M3, BOT3, W - M3, y1, ncols=2, obst=[(img[0], img[1] - 9 * mm, img[2], img[3]), (ad[0], ad[1] - 2 * mm, ad[2], ad[3] + 4 * mm), box])


def fuerza(story):
    bg()
    label("Fuerza", M3, TOP3 - 3)
    stitle(["El peso de", "la constancia"], M3 - 1, TOP3 - 22 * mm, 40, WINE, lead=1.0)
    y1 = H - 66 * mm
    S_lift(CX(0), y1 - 78 * mm, CWID, 78 * mm)
    caption(CX(0), y1 - 78 * mm, CWID, "Los discos suman kilos; la técnica los vuelve ligeros.")
    infobox3(CX(1), y1, CWID, "Fuerza en números",
             [("Halterofilia", "2 movimientos"), ("Powerlifting", "3 movimientos"), ("Bala (hombres)", "7,26 kg")])
    fr = p5_frames(); fill(c, story, fr); report("fuerza", fr)
    ad_trazo(CX(1), AD_Y, AD_W, AD_H)
    footer3(5); c.showPage()


# =================== 06 VELOCIDAD ===================
SC6 = 110 * mm


def p6_frames():
    y1 = H - SC6 - 28 * mm
    box = (CX(1), BOT3 + 2 * mm, W - M3, BOT3 + 2 * mm + ib_h(3))
    return make_frames(M3, BOT3, W - M3, y1, ncols=2, obst=[box])


def velocidad(story):
    bg()
    S_sprint(0, H - SC6, W, SC6)
    label("Velocidad", M3, H - 14 * mm, white)
    stitle(["Cada centésima", "cuenta"], M3 - 1, H - SC6 + 26 * mm, 40, white, lead=1.0)
    para(c, "Del esprint de 100 metros al ciclismo de pista: la velocidad como obsesión.", DECK3(INK3, 12.2), M3, H - SC6 - 7 * mm, W - 2 * M3)
    infobox3(CX(1), BOT3 + 2 * mm + ib_h(3), CWID, "Récords mundiales",
             [("100 m", "9,58 s"), ("200 m", "19,19 s"), ("400 m", "43,03 s")])
    fr = p6_frames(); fill(c, story, fr); report("velocidad", fr)
    footer3(6); c.showPage()


# =================== 07 EQUILIBRIO + VÉRTICE ===================
def p7_frames():
    y1 = H - 84 * mm
    img = (CX(1), y1 - 84 * mm, W - M3, y1)
    ad = (CX(0), AD_Y, CX(0) + CWID, AD_Y + AD_H)
    return make_frames(M3, BOT3, W - M3, y1, ncols=2, obst=[(img[0], img[1] - 9 * mm, img[2], img[3]), (ad[0], ad[1] - 2 * mm, ad[2], ad[3] + 4 * mm)])


def equilibrio(story):
    bg()
    label("Equilibrio", M3, TOP3 - 3)
    stitle(["Cuerpo en movimiento"], M3 - 1, TOP3 - 20 * mm, 40, WINE, lead=1.0)
    y1 = H - 84 * mm
    S_balance(CX(1), y1 - 84 * mm, CWID, 84 * mm)
    caption(CX(1), y1 - 84 * mm, CWID, "Sobre una cinta de pocos centímetros, cada músculo trabaja a la vez.")
    fr = p7_frames(); fill(c, story, fr); report("equilibrio", fr)
    ad_vertice(CX(0), AD_Y, AD_W, AD_H)
    para(c, "Gimnasia, surf, skateboarding y slackline: coordinación en cada gesto.", DECK3(INK3, 12.2), M3, TOP3 - 44 * mm, W - 2 * M3)
    footer3(7); c.showPage()


# =================== 08 ESTRATEGIA + RAÍZ ===================
def p8_frames():
    y1 = H - 16 * mm - 52 * mm - 74 * mm - 14 * mm
    ad = (CX(1), AD_Y, W - M3, AD_Y + AD_H)
    box = (CX(0), BOT3 + 2 * mm, CX(0) + CWID, BOT3 + 2 * mm + ib_h(3))
    return make_frames(M3, BOT3, W - M3, y1, ncols=2, obst=[(ad[0], ad[1] - 2 * mm, ad[2], ad[3] + 4 * mm), box])


def estrategia(story):
    bg()
    label("Estrategia", M3, TOP3 - 3)
    stitle(["Jugar con la mente"], M3 - 1, TOP3 - 20 * mm, 40, WINE)
    para(c, "Ajedrez, go, bridge: el deporte donde la jugada decisiva ocurre antes de moverse.", DECK3(INK3, 12.2), M3, TOP3 - 28 * mm, W - 2 * M3 - 20 * mm)
    iy = H - 16 * mm - 52 * mm
    S_chess(M3, iy - 74 * mm, W - 2 * M3, 74 * mm)
    caption(M3, iy - 74 * mm, W - 2 * M3, "Sesenta y cuatro casillas bastan para infinitas partidas.")
    infobox3(CX(0), BOT3 + 2 * mm + ib_h(3), CWID, "Tablero y piezas",
             [("Casillas del ajedrez", "64"), ("Piezas por bando", "16"), ("Tablero de go", "19 × 19")])
    fr = p8_frames(); fill(c, story, fr); report("estrategia", fr)
    ad_raiz(CX(1), AD_Y, AD_W, AD_H)
    footer3(8); c.showPage()


# =================== 09 NUESTRA TIERRA (texto propio) ===================
def tierra():
    sc = 118
    for sc in range(118, 70, -3):
        s = own(TIERRA, "POR LA REDACCIÓN   ·   3 MIN DE LECTURA")
        fr = make_frames(M3, 54 * mm, W - M3, H - sc * mm - 24 * mm, ncols=2)
        fill(cv.Canvas(io.BytesIO()), s, fr)
        if not s:
            break
    SC = sc * mm; print("tierra: escena", sc, "mm")
    story = own(TIERRA, "POR LA REDACCIÓN   ·   3 MIN DE LECTURA")
    bg()
    S_land(0, H - SC, W, SC)
    scrim(c, 0, H - SC, W, SC * 0.55, color=HexColor("#2B0A18"), amax=0.7)
    label("Nuestra tierra", M3, H - SC + 40 * mm, MUST)
    stitle(["Juegos y deportes", "de casa"], M3 - 1, H - SC + 27 * mm, 34, white, lead=1.0)
    para(c, "Béisbol, bolas criollas y coleo: lo que jugamos también nos cuenta quiénes somos.", DECK3(INK3, 12.2), M3, H - SC - 7 * mm, W - 2 * M3)
    fr = make_frames(M3, 54 * mm, W - M3, H - SC - 24 * mm, ncols=2)
    fill(c, story, fr); report("tierra", fr)
    assert not story, "tierra desborda"
    # franja de 4 juegos
    yb = 25 * mm; hb = 24 * mm
    c.setFillColor(WINE); c.rect(M3, yb, W - 2 * M3, hb, stroke=0, fill=1)
    cw = (W - 2 * M3) / 4
    for i, (a, b) in enumerate([("Béisbol", "pasión nacional"), ("Bolas criollas", "juego de patio"), ("Coleo", "tradición llanera"), ("Trompo", "juego de infancia")]):
        xx = M3 + 5 * mm + i * cw
        text(c, a, xx, yb + hb - 10 * mm, "Serif-B", 11, white)
        text(c, b.upper(), xx, yb + hb - 15.5 * mm, "Sans-B", 5.8, MUST, cs=1.2)
        if i:
            c.setStrokeColor(HexColor("#85405A")); c.setLineWidth(0.5); c.line(xx - 3 * mm, yb + 4 * mm, xx - 3 * mm, yb + hb - 4 * mm)
    footer3(9); c.showPage()


# =================== 10 CONTRAPORTADA ===================
def contraportada():
    bg(WINE)
    S_sun(0, 0, W, H * 0.58)
    for i, s in enumerate(["¿Y si", "empiezas", "hoy?"]):
        text(c, s, M3 - 1, H - 40 * mm - i * 28 * mm, "Serif-BI", 80, white, cs=-2.4)
    label("Próximo número", M3, H - 20 * mm, MUST)
    ms = fit_size("Ímpetu", "Serif-BI", W - 2 * M3, maxsize=120, cs=-4)
    c.setFillColor(HexColor("#17414A")); c.rect(0, 0, W, 36 * mm, stroke=0, fill=1)
    text(c, "Ímpetu", M3, 13 * mm, "Serif-BI", ms * 0.46, white, cs=-3)
    text(c, "REVISTA DE DEPORTE Y MOVIMIENTO", W - M3, 21 * mm, "Sans-B", 6.6, MUST, "r", cs=3)
    text(c, "Nº 01 · OCTUBRE 2026", W - M3, 14 * mm, "Sans-SB", 6.4, white, "r", cs=2)
    c.showPage()


# =================== ENSAMBLADO ===================
cover(); c.showPage()
editorial_indice()
resistencia()
k = fit(lambda n: lorem3(11, n), [p5_frames]); fuerza(lorem3(11, k))
k = fit(lambda n: lorem3(22, n), [p6_frames]); velocidad(lorem3(22, k))
k = fit(lambda n: lorem3(33, n), [p7_frames]); equilibrio(lorem3(33, k))
k = fit(lambda n: lorem3(44, n), [p8_frames]); estrategia(lorem3(44, k))
tierra()
contraportada()
c.save()
print("OK ->", OUT)
