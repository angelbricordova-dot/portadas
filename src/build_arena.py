import sys, json, random
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mag_lib import *
from texts_arena import EDITORIAL2, SOLO, ADAPT

OUT = sys.argv[1] if len(sys.argv) > 1 else "../output/ARENA.pdf"
AUTOR = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
c = cv.Canvas(OUT, pagesize=A4)
c.setTitle("ARENA – Revista deportiva (Nº 01)")
c.setSubject("Tipos de deporte")
idml_export.configure(mag="arena", cols=4, gutter=G, margins=(15 * mm, 22 * mm, 15 * mm, 15 * mm),
                      baseline=(15 * mm, 12.9), palette={
    "#0E0E10": "Tinta", "#C4F135": "Lima", "#5B3FD9": "Violeta", "#FF4F8B": "Rosa", "#F3F2EC": "Hueso",
    "#7CE0FF": "Cielo", "#C9C0F5": "Lila", "#8B8B93": "Gris medio", "#D3D2CA": "Línea"})

# ---------- paleta propia ----------
INK = HexColor("#0E0E10"); LIME = HexColor("#C4F135"); VIOLET = HexColor("#5B3FD9")
PINK = HexColor("#FF4F8B"); BONE = HexColor("#F3F2EC"); MID = HexColor("#8B8B93")
SKY = HexColor("#7CE0FF"); LILAC = HexColor("#C9C0F5"); LINE = HexColor("#D3D2CA")

# ---------- retícula de 4 columnas ----------
C4 = (W - 2 * M - 3 * G) / 4
TOP = H - 15 * mm


def X(i):
    return M + i * (C4 + G)


def SP(n):
    return n * C4 + (n - 1) * G


BODY2 = ParagraphStyle("b2", fontName="Sans", fontSize=8.7, leading=12.9, textColor=INK, spaceAfter=5.2)
LEAD2 = ParagraphStyle("l2", fontName="Sans-SB", fontSize=10.6, leading=14.8, textColor=INK, spaceAfter=7)
BODY_OWN = ParagraphStyle("bo", parent=BODY2, fontSize=9.5, leading=14.2, spaceAfter=6)
CAP2 = ParagraphStyle("c2", fontName="Sans", fontSize=6.8, leading=9, textColor=MID)
DECK2 = lambda col=INK, sz=12.2: ParagraphStyle("d2", fontName="Serif-I", fontSize=sz, leading=sz * 1.36, textColor=col)


def report(tag, frames):
    print(tag, "libre (mm):", [round((f._y - f._y1) / mm) for f in frames])


def own(items):
    return [Paragraph(s, LEAD2 if k == "lead" else BODY_OWN) for k, s in items]


def lorem2(seed, k):
    rng = random.Random(seed)
    out = []
    for i in range(k):
        txt = " ".join(lorem_sentence(rng) for _ in range(rng.randint(3, 5)))
        if i % 3 == 1:
            h = " ".join(rng.choice(LW) for _ in range(2)).capitalize()
            txt = '<font name="Sans-B" color="#5B3FD9">%s.</font> %s' % (h.upper(), txt)
        out.append(Paragraph(txt, BODY2))
    return out


def bg(col=BONE):
    c.setFillColor(col); c.rect(0, 0, W, H, stroke=0, fill=1)


def bar(x, y, w=12 * mm, col=VIOLET, h=2.6):
    c.setFillColor(col); c.rect(x, y, w, h, stroke=0, fill=1)


def tag(s, x, y, col=VIOLET, bgc=None):
    tw = pdfmetrics.stringWidth(s.upper(), "Sans-B", 7) + 1.6 * len(s) + 8
    if bgc is not None:
        c.setFillColor(bgc); c.roundRect(x, y - 3.4, tw, 12.5, 6.2, stroke=0, fill=1)
    text(c, s.upper(), x + 4, y, "Sans-B", 7, col, cs=1.6)
    return tw


def footer2(n, dark=False, numcol=None):
    col = BONE if dark else MID
    y = 10 * mm
    nc = numcol or (LIME if dark else VIOLET)
    lab = "ARENA  ·  Nº 01  ·  OCTUBRE 2026"
    if n % 2 == 0:
        text(c, "%02d" % n, M, y - 1, "Disp-X", 14, nc)
        text(c, lab, M + 11 * mm, y + 0.4, "Sans-SB", 6, col, cs=1.4)
    else:
        text(c, "%02d" % n, W - M, y - 1, "Disp-X", 14, nc, "r")
        text(c, lab, W - M - 11 * mm, y + 0.4, "Sans-SB", 6, col, "r", cs=1.4)


# =================== ESCENAS ===================
def S_solo(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(LIME); c.rect(x, y, w, h, stroke=0, fill=1)
    cx, cy = x + w * 0.76, y + h * 0.46
    R = min(h * 0.32, w * 0.2)
    clip_rect(c, x + w * 0.56, y, w * 0.44, h)
    for i in range(8):                                  # pista: arcos concéntricos
        c.setStrokeColor(VIOLET if i % 2 == 0 else INK); c.setLineWidth(3.2)
        c.circle(cx, cy, R * (1.28 + i * 0.16), stroke=1, fill=0)
    c.restoreState()
    circle(c, cx, cy, R * 1.04, fill=INK)
    circle(c, cx, cy, R * 0.9, fill=BONE)
    rect_ = c.setFillColor(INK); c.roundRect(cx - R * 0.14, cy + R * 1.0, R * 0.28, R * 0.24, 3, stroke=0, fill=1)
    c.roundRect(cx + R * 0.72, cy + R * 0.82, R * 0.2, R * 0.2, 3, stroke=0, fill=1)
    for k in range(60):
        a = math.radians(90 - k * 6)
        r0 = R * (0.74 if k % 5 == 0 else 0.8)
        line(c, cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + R * 0.86 * math.cos(a), cy + R * 0.86 * math.sin(a), INK, 1.6 if k % 5 == 0 else 0.8, 0)
    a = math.radians(90 - 138)
    c.setFillColor(VIOLET)
    poly(c, [(cx + R * 0.62 * math.cos(a), cy + R * 0.62 * math.sin(a)),
             (cx + R * 0.07 * math.cos(a + 1.57), cy + R * 0.07 * math.sin(a + 1.57)),
             (cx + R * 0.07 * math.cos(a - 1.57), cy + R * 0.07 * math.sin(a - 1.57))], fill=PINK)
    circle(c, cx, cy, R * 0.09, fill=INK)
    c.restoreState()


def S_pool(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(HexColor("#1B8FD6")); c.rect(x, y, w, h, stroke=0, fill=1)
    n = 6
    for i in range(n):
        c.setFillColor(HexColor("#2DB7F5") if i % 2 else HexColor("#1B8FD6")); c.rect(x, y + i * h / n, w, h / n, stroke=0, fill=1)
    for i in range(n + 1):
        yy = y + i * h / n
        for k in range(int(w / 9)):
            circle(c, x + k * 9 + 4, yy, 2.2, fill=(PINK if k % 2 else BONE))
    # nadador en el carril 3: cabeza + brazo en arco
    sx, sy = x + w * 0.56, y + 2.5 * h / n
    circle(c, sx, sy, h * 0.045, fill=BONE)
    c.setStrokeColor(LIME); c.setLineWidth(h * 0.04); c.setLineCap(1)
    p = c.beginPath(); p.moveTo(sx - h * 0.04, sy + h * 0.02)
    p.curveTo(sx - h * 0.2, sy + h * 0.2, sx - h * 0.36, sy + h * 0.06, sx - h * 0.46, sy - h * 0.08)
    c.drawPath(p, stroke=1, fill=0)
    line(c, sx - h * 0.06, sy - h * 0.02, sx - w * 0.3, sy - h * 0.02, BONE, h * 0.05)
    for k in range(4):
        line(c, sx + h * 0.12 + k * 10, sy + h * 0.03 - k * 2, sx + h * 0.28 + k * 10, sy + h * 0.03 - k * 2, BONE, 1.6)
    c.restoreState()


def S_team(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(VIOLET); c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(LILAC); c.setLineWidth(2.2)
    c.rect(x + w * 0.06, y + h * 0.1, w * 0.88, h * 0.8, stroke=1, fill=0)
    c.line(x + w * 0.5, y + h * 0.1, x + w * 0.5, y + h * 0.9)
    c.rect(x + w * 0.06, y + h * 0.3, w * 0.16, h * 0.4, stroke=1, fill=0)
    c.rect(x + w * 0.78, y + h * 0.3, w * 0.16, h * 0.4, stroke=1, fill=0)
    # red
    for i in range(14):
        xx = x + w * 0.5 - 2
    pos = [(0.22, 0.62, LIME), (0.3, 0.38, LIME), (0.38, 0.72, LIME), (0.64, 0.5, BONE), (0.74, 0.7, BONE), (0.7, 0.3, BONE)]
    for (px, py, col) in pos:
        cx_, cy_ = x + w * px, y + h * py
        s = h * 0.06
        circle(c, cx_, cy_ + s * 2.0, s * 0.78, fill=col)
        c.setFillColor(col); c.roundRect(cx_ - s * 0.85, cy_ - s * 1.0, s * 1.7, s * 2.4, s * 0.6, stroke=0, fill=1)
        circle(c, cx_, cy_ - s * 1.3, s * 0.0, fill=col)
    bx, by = x + w * 0.5, y + h * 0.5
    circle(c, bx, by, h * 0.15, fill=PINK)
    c.setStrokeColor(INK); c.setLineWidth(2.4)
    c.circle(bx, by, h * 0.15, stroke=1, fill=0)
    p = c.beginPath(); p.arc(bx - h * 0.15, by - h * 0.15, bx + h * 0.15, by + h * 0.15, 40, 100); c.drawPath(p, stroke=1, fill=0)
    c.line(bx - h * 0.15, by, bx + h * 0.15, by)
    c.line(bx, by - h * 0.15, bx, by + h * 0.15)
    c.restoreState()


def S_mount(x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (255, 79, 139), (255, 205, 130), 40)
    circle(c, x + w * 0.78, y + h * 0.66, h * 0.17, fill=LIME)
    peaks = [(0.0, 0.0, 0.2, 0.62, 0.5, 0.0, VIOLET), (0.3, 0.0, 0.58, 0.8, 0.95, 0.0, HexColor("#3F27A8")),
             (-0.1, 0.0, 0.1, 0.38, 0.4, 0.0, HexColor("#2A1A78")), (0.62, 0.0, 0.85, 0.5, 1.1, 0.0, HexColor("#2A1A78"))]
    for (x0, y0, x1, y1, x2, y2, col) in peaks:
        poly(c, [(x + w * x0, y + h * y0), (x + w * x1, y + h * y1), (x + w * x2, y + h * y2)], fill=col)
    # nieve en cumbres
    poly(c, [(x + w * 0.5, y + h * 0.62), (x + w * 0.58, y + h * 0.8), (x + w * 0.66, y + h * 0.62), (x + w * 0.6, y + h * 0.56), (x + w * 0.55, y + h * 0.6)], fill=BONE)
    poly(c, [(x + w * 0.15, y + h * 0.5), (x + w * 0.2, y + h * 0.62), (x + w * 0.26, y + h * 0.5), (x + w * 0.2, y + h * 0.46)], fill=BONE)
    poly(c, [(x, y), (x, y + h * 0.2), (x + w * 0.35, y + h * 0.13), (x + w * 0.7, y + h * 0.18), (x + w, y + h * 0.1), (x + w, y)], fill=INK)
    # bandera
    line(c, x + w * 0.58, y + h * 0.8, x + w * 0.58, y + h * 0.93, INK, 2.4)
    poly(c, [(x + w * 0.58, y + h * 0.93), (x + w * 0.64, y + h * 0.9), (x + w * 0.58, y + h * 0.87)], fill=LIME)
    c.restoreState()


def S_winter(x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (124, 224, 255), (243, 242, 236), 30)
    circle(c, x + w * 0.2, y + h * 0.8, h * 0.11, fill=LIME)
    poly(c, [(x, y + h * 0.55), (x + w, y + h * 0.1), (x + w, y), (x, y)], fill=white)
    poly(c, [(x, y + h * 0.4), (x + w, y - h * 0.05), (x + w, y), (x, y)], fill=HexColor("#DCEBF5"))
    for (tx, th) in [(0.12, 0.32), (0.2, 0.24), (0.07, 0.2), (0.88, 0.22)]:
        base = y + h * (0.5 - tx * 0.45) if tx < 0.5 else y + h * 0.1
        bx_ = x + w * tx
        for j in range(3):
            poly(c, [(bx_ - h * 0.07 + j * 2, base + j * h * th * 0.28), (bx_, base + h * th * (0.5 + j * 0.28)), (bx_ + h * 0.07 - j * 2, base + j * h * th * 0.28)], fill=INK)
    # esquiador
    sx, sy = x + w * 0.58, y + h * 0.3
    ang = math.radians(-22)
    c.saveState(); c.translate(sx, sy); c.rotate(-22)
    u = h * 0.12
    c.setStrokeColor(PINK); c.setLineWidth(u * 0.2); c.setLineCap(1)
    c.line(-u * 1.5, -u * 0.5, u * 1.6, -u * 0.5)
    c.setStrokeColor(INK); c.setLineWidth(u * 0.3)
    c.line(-u * 0.3, -u * 0.5, 0.1 * u, u * 0.6); c.line(u * 0.4, -u * 0.5, 0.1 * u, u * 0.6)
    c.line(0.1 * u, u * 0.6, u * 0.55, u * 1.3)
    c.setLineWidth(u * 0.14); c.line(u * 0.5, u * 1.1, u * 1.4, u * 0.2)
    circle(c, u * 0.7, u * 1.65, u * 0.3, fill=INK)
    c.restoreState()
    for k in range(14):
        rr = random.Random(k)
        circle(c, x + rr.random() * w, y + h * (0.45 + rr.random() * 0.5), 1.4 + rr.random() * 1.6, fill=white)
    c.restoreState()


def S_prec(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(VIOLET); c.rect(x, y, w, h, stroke=0, fill=1)
    cx, cy = x + w * 0.6, y + h * 0.5
    R = min(w, h) * 0.42
    for r, col in [(1.0, BONE), (0.8, INK), (0.6, PINK), (0.4, BONE), (0.22, LIME)]:
        circle(c, cx, cy, R * r, fill=col)
    circle(c, cx, cy, R * 0.07, fill=INK)
    # flecha clavada en el centro
    ax, ay = x + w * 0.06, y + h * 0.9
    c.setStrokeColor(INK); c.setLineWidth(R * 0.045); c.setLineCap(1)
    c.line(ax, ay, cx - R * 0.02, cy + R * 0.02)
    c.setStrokeColor(LIME)
    for k in range(3):
        t = 0.03 + k * 0.05
        px, py = ax + (cx - ax) * t, ay + (cy - ay) * t
        line(c, px, py, px + R * 0.2, py + R * 0.07, PINK, R * 0.045)
        line(c, px, py, px - R * 0.07, py - R * 0.2, PINK, R * 0.045)
    for k in range(10):
        rr = random.Random(k + 5)
        circle(c, x + rr.random() * w * 0.4, y + rr.random() * h, 1.6, fill=LILAC)
    c.restoreState()


def S_adapt(x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(VIOLET); c.rect(x, y, w, h, stroke=0, fill=1)
    for i in range(7):
        circle(c, x + w * 0.74, y + h * 0.44, h * (0.2 + i * 0.1), fill=None, stroke=HexColor("#6B50E6" if i % 2 else "#4F34C4"), lw=10)
    u = h * 0.165
    ox, oy = x + w * 0.7, y + h * 0.4
    for k in range(5):
        line(c, ox - u * 2.6, oy + u * (1.4 - k * 0.4), ox - u * (1.4 + (k % 2) * 0.4), oy + u * (1.4 - k * 0.4), LIME, u * 0.07)
    def P(a, b): return ox + u * a, oy + u * b
    # ruedas
    circle(c, *P(0, 0), u * 1.0, fill=None, stroke=INK, lw=u * 0.12)
    circle(c, *P(0, 0), u * 0.88, fill=BONE)
    for k in range(10):
        a = math.radians(k * 36)
        line(c, *P(0, 0), *P(0.88 * math.cos(a), 0.88 * math.sin(a)), PINK, 1.6, 0)
    circle(c, *P(0, 0), u * 0.12, fill=INK)
    circle(c, *P(2.2, -0.55), u * 0.45, fill=INK)
    circle(c, *P(2.2, -0.55), u * 0.3, fill=BONE)
    # chasis
    line(c, *P(0.1, 0.3), *P(2.2, -0.55), LIME, u * 0.14)
    line(c, *P(0.1, 0.3), *P(0.55, 0.3), LIME, u * 0.14)
    # cuerpo
    c.setStrokeColor(LIME); c.setLineWidth(u * 0.24); c.setLineCap(1)
    p = c.beginPath(); p.moveTo(*P(0.5, 0.45)); p.lineTo(*P(1.35, 0.5)); p.lineTo(*P(1.75, -0.1)); c.drawPath(p, stroke=1, fill=0)
    line(c, *P(0.5, 0.45), *P(0.28, 1.4), LIME, u * 0.3)
    line(c, *P(0.28, 1.35), *P(-0.4, 0.98), LIME, u * 0.17)
    circle(c, *P(0.5, 1.82), u * 0.26, fill=LIME)
    c.restoreState()


# =================== ANUNCIOS (cuadro de 2 columnas) ===================
AD_W = SP(2)
AD_H = 96 * mm
AD_Y = 24 * mm


def ad_note(x, y, col):
    text(c, "Anuncio ficticio realizado con fines académicos.", x, y, "Sans", 5.6, col)


def ad_button(x, y, w, s, fillc, txtc):
    c.setFillColor(fillc); c.roundRect(x, y, w, 8 * mm, 4 * mm, stroke=0, fill=1)
    text(c, s, x + w / 2, y + 2.8 * mm, "Sans-B", 7.2, txtc, "c", cs=1.2)


def ad_altura(x, y, w, h):
    c.setFillColor(INK); c.rect(x, y, w, h, stroke=0, fill=1)
    clip_rect(c, x, y, w, h)
    poly(c, [(x + w * 0.1, y + h * 0.5), (x + w * 0.4, y + h * 0.9), (x + w * 0.7, y + h * 0.5)], fill=VIOLET)
    poly(c, [(x + w * 0.45, y + h * 0.5), (x + w * 0.7, y + h * 0.82), (x + w * 1.0, y + h * 0.5)], fill=LIME)
    poly(c, [(x + w * 0.4, y + h * 0.9), (x + w * 0.34, y + h * 0.8), (x + w * 0.4, y + h * 0.77), (x + w * 0.46, y + h * 0.8)], fill=BONE)
    c.restoreState()
    text(c, "ALTURA", x + 5 * mm, y + h - 9 * mm, "Disp-X", 11, LIME, cs=3)
    for i, s in enumerate(["Más arriba,", "sin peso", "de más."]):
        text(c, s.upper(), x + 5 * mm, y + h * 0.42 - i * 8.2 * mm, "Disp-X", 22, BONE, cs=-0.4)
    para(c, "Mochilas y botas ligeras para cada ruta.", ParagraphStyle("a", fontName="Sans", fontSize=7.8, leading=10.5, textColor=LILAC), x + 5 * mm, y + 21 * mm, w - 10 * mm)
    ad_button(x + 5 * mm, y + 8.5 * mm, 36 * mm, "VER COLECCIÓN", LIME, INK)
    ad_note(x + 5 * mm, y + 3.6 * mm, MID)


def ad_nordica(x, y, w, h):
    c.setFillColor(VIOLET); c.rect(x, y, w, h, stroke=0, fill=1)
    clip_rect(c, x, y, w, h)
    cx, cy = x + w * 0.74, y + h * 0.72
    for k in range(6):                                  # copo de nieve
        a = math.radians(k * 60 + 15)
        line(c, cx, cy, cx + h * 0.2 * math.cos(a), cy + h * 0.2 * math.sin(a), BONE, 3)
        mx, my = cx + h * 0.13 * math.cos(a), cy + h * 0.13 * math.sin(a)
        for s in (-1, 1):
            b = a + s * 0.9
            line(c, mx, my, mx + h * 0.05 * math.cos(b), my + h * 0.05 * math.sin(b), BONE, 2)
    circle(c, cx, cy, h * 0.025, fill=LIME)
    c.restoreState()
    text(c, "NÓRDICA", x + 5 * mm, y + h - 9 * mm, "Disp-X", 11, LIME, cs=3)
    for i, s in enumerate(["Frío afuera.", "Calor", "adentro."]):
        text(c, s.upper(), x + 5 * mm, y + h * 0.5 - i * 8.2 * mm, "Disp-X", 21, white, cs=-0.4)
    para(c, "Ropa térmica para esquiar, correr o simplemente salir.", ParagraphStyle("n", fontName="Sans", fontSize=7.8, leading=10.5, textColor=LILAC), x + 5 * mm, y + 28 * mm, w - 10 * mm)
    ad_button(x + 5 * mm, y + 12 * mm, 36 * mm, "ABRÍGATE HOY", LIME, INK)
    ad_note(x + 5 * mm, y + 5.5 * mm, LILAC)


def ad_ritmo(x, y, w, h):
    c.setFillColor(PINK); c.rect(x, y, w, h, stroke=0, fill=1)
    clip_rect(c, x, y, w, h)
    cx, cy = x + w * 0.5, y + h * 0.7
    c.setStrokeColor(INK); c.setLineWidth(h * 0.045); c.setLineCap(1)
    p = c.beginPath(); p.arc(cx - h * 0.2, cy - h * 0.2, cx + h * 0.2, cy + h * 0.2, 0, 180); c.drawPath(p, stroke=1, fill=0)
    c.setFillColor(INK)
    c.roundRect(cx - h * 0.25, cy - h * 0.12, h * 0.1, h * 0.2, h * 0.04, stroke=0, fill=1)
    c.roundRect(cx + h * 0.15, cy - h * 0.12, h * 0.1, h * 0.2, h * 0.04, stroke=0, fill=1)
    for k in range(4):
        line(c, x + w * 0.1 + k * 5, cy - h * 0.2 - k * 2, x + w * 0.1 + k * 5, cy + h * 0.2 + k * 2, LIME, 1.6)
        line(c, x + w * 0.9 - k * 5, cy - h * 0.2 - k * 2, x + w * 0.9 - k * 5, cy + h * 0.2 + k * 2, LIME, 1.6)
    c.restoreState()
    text(c, "RITMO", x + 5 * mm, y + h - 9 * mm, "Disp-X", 11, INK, cs=3)
    for i, s in enumerate(["Tu ritmo,", "tu música."]):
        text(c, s.upper(), x + 5 * mm, y + h * 0.4 - i * 9.2 * mm, "Disp-X", 24, INK, cs=-0.4)
    para(c, "Audífonos deportivos a prueba de sudor y de excusas.", ParagraphStyle("r", fontName="Sans", fontSize=7.8, leading=10.5, textColor=INK), x + 5 * mm, y + 28 * mm, w - 10 * mm)
    ad_button(x + 5 * mm, y + 12 * mm, 36 * mm, "ESCÚCHALOS", INK, LIME)
    ad_note(x + 5 * mm, y + 5.5 * mm, INK)


# ---- ilustraciones sustituibles por imágenes generadas (ver imgslots.py) ----
import imgslots
S_solo = imgslots.wrap(S_solo, "arena", "individuales", lambda: c)
S_pool = imgslots.wrap(S_pool, "arena", "piscina", lambda: c)
S_team = imgslots.wrap(S_team, "arena", "colectivos", lambda: c)
S_mount = imgslots.wrap(S_mount, "arena", "montana", lambda: c)
S_winter = imgslots.wrap(S_winter, "arena", "invierno", lambda: c)
S_prec = imgslots.wrap(S_prec, "arena", "precision", lambda: c)
S_adapt = imgslots.wrap(S_adapt, "arena", "adaptado", lambda: c)


# =================== 01 PORTADA ===================
def cover():
    bg(INK)
    if imgslots.photo(c, "arena", "portada", 0, 0, W, H):
        scrim(c, 0, H - 80 * mm, W, 80 * mm, color=INK, amax=0.8, up=False)
        scrim(c, 0, 0, W, 120 * mm, color=INK, amax=0.92)
    else:
        # ARENA vista desde arriba: un estadio cuyas seis calles son las seis «arenas» del número
        import cover_art as ca
        clip_rect(c, 0, 0, W, H)
        halftone(c, 0, 0, W, H * 0.62, VIOLET, step=9, rmax=2.6, mode="bottom", alpha=0.35)
        ca.stadium(c, W * 0.60, H * 0.495, 290, 64, -16,
                   dict(stands=VIOLET, rows=HexColor("#7A62F0"), track=PINK, lines=BONE, field=LIME,
                        field_lines=INK, nums=BONE),
                   text, lanes=6, lane_w=13,
                   labels=["Solos contra el reloj", "El juego de todos", "Hasta la cima",
                           "Frío y velocidad", "Un punto exacto", "Sin barreras"])
        c.restoreState()
    ms = fit_size("ARENA", "Disp-X", W - 2 * M, cs=-5)
    text(c, "ARENA", M - 4, H - 15 * mm - ms * 0.73, "Disp-X", ms, BONE, cs=-5)
    yb = H - 15 * mm - ms * 0.73 - 9 * mm
    text(c, "REVISTA DEPORTIVA", M, yb, "Sans-B", 9, LIME, cs=5)
    text(c, "Nº 01  ·  OCTUBRE 2026", W - M, yb, "Sans-B", 9, BONE, "r", cs=2.4)
    for i, s in enumerate(["Seis arenas,", "una sola", "pasión."]):
        text(c, s, M - 1, 66 * mm - i * 15 * mm, "Disp-X", 44, BONE, cs=-1.2)
    items = [("03", "Solos contra el reloj"), ("06", "Hasta la cima"), ("09", "Sin barreras")]
    for i, (n, t) in enumerate(items):
        yy = 18.5 * mm - i * 0
    x0 = M
    for i, (n, t) in enumerate(items):
        text(c, n, x0, 17 * mm, "Disp-X", 11, LIME)
        text(c, t.upper(), x0 + 8.5 * mm, 17 * mm, "Sans-B", 6.6, BONE, cs=1.1)
        x0 += 8.5 * mm + pdfmetrics.stringWidth(t.upper(), "Sans-B", 6.6) + 1.1 * len(t) + 7 * mm
    import cover_art as ca
    ca.barcode(c, W - M - 28 * mm, 10 * mm, 28 * mm, 18 * mm, "759100260037", text,
               ink=INK, paper=BONE, label="EJEMPLAR ACADÉMICO")
    ca.author_credit(c, W - M, 44 * mm, AUTOR, text, LIME, BONE, LILAC)


# =================== 02 EDITORIAL + ÍNDICE ===================
def editorial_indice():
    bg()
    pw = X(2) - G / 2
    c.setFillColor(INK); c.rect(0, 0, pw, H, stroke=0, fill=1)
    tag("En este número", M, TOP - 4, LIME)
    title_block(c, ["Índice"], M - 2, TOP - 24 * mm, 46, BONE, lead=0.9, font="Disp-X", cs=-1.2)
    rows = [("02", "Editorial", "Carta de la redacción"),
            ("03", "Deportes individuales", "Solos contra el reloj"),
            ("05", "Deportes colectivos", "El juego de todos"),
            ("06", "Deportes de montaña", "Hasta la cima"),
            ("07", "Deportes de invierno", "Frío y velocidad"),
            ("08", "Deportes de precisión", "Un punto exacto"),
            ("09", "Deporte adaptado", "Sin barreras")]
    y = TOP - 48 * mm
    for n, t, d in rows:
        text(c, n, M, y - 8, "Disp-X", 28, LIME, cs=-0.6)
        text(c, t, M + 21 * mm, y - 1, "Sans-B", 9.6, BONE)
        text(c, d, M + 21 * mm, y - 12, "Serif-I", 8.6, LILAC)
        c.setStrokeColor(HexColor("#2C2C33")); c.setLineWidth(0.6)
        c.line(M, y - 19, pw - 8 * mm, y - 19)
        y -= 26.5 * mm
    # lado derecho: editorial
    x = X(2); w = SP(2)
    tag("Carta de la redacción", x, TOP - 4, VIOLET)
    es = fit_size("Editorial", "Disp-X", w, maxsize=50, cs=-1.4)
    text(c, "Editorial", x - 1, TOP - 24 * mm, "Disp-X", es, INK, cs=-1.4)
    bar(x, TOP - 30 * mm)
    st = [Paragraph(EDITORIAL2[0], ParagraphStyle("e0", parent=LEAD2, fontName="Serif-SB", fontSize=12.4, leading=17.4, spaceAfter=9))]
    st += [Paragraph(p, ParagraphStyle("e1", parent=BODY2, fontSize=9.4, leading=14, spaceAfter=7)) for p in EDITORIAL2[1:]]
    st += [Paragraph('<font name="Sans-B" size="7" color="#5B3FD9">—  EL EQUIPO DE ARENA</font>', BODY2)]
    fr = [Frame(x, 112 * mm, w, TOP - 36 * mm - 112 * mm, 0, 0, 0, 0)]
    fill(c, st, fr); report("editorial", fr)
    assert not st, "editorial desborda"
    # cita lima
    c.setFillColor(LIME); c.rect(x, 62 * mm, w, 44 * mm, stroke=0, fill=1)
    text(c, "“", x + 4 * mm, 62 * mm + 44 * mm - 16 * mm, "Disp-X", 60, VIOLET)
    para(c, "El deporte se entiende mejor jugándolo.", ParagraphStyle("q", fontName="Serif-BI", fontSize=15.5, leading=20, textColor=INK), x + 17 * mm, 62 * mm + 36 * mm, w - 22 * mm)
    # autor
    if AUTOR:
        c.setStrokeColor(INK); c.setLineWidth(1)
        bh = 14 * mm + len(AUTOR["lineas"]) * 4.6 * mm
        c.rect(x, 24 * mm, w, bh, stroke=1, fill=0)
        text(c, "REVISTA ELABORADA POR", x + 4 * mm, 24 * mm + bh - 6 * mm, "Sans-B", 6.2, VIOLET, cs=1.5)
        for j, s in enumerate(AUTOR["lineas"]):
            text(c, s, x + 4 * mm, 24 * mm + bh - 12.5 * mm - j * 4.6 * mm, "Sans-B" if j == 0 else "Sans", 9 if j == 0 else 7.6, INK)
    footer2(2, dark=False)
    # folio dentro del panel oscuro
    c.saveState(); c.setFillColor(INK); c.rect(0, 0, pw, 14 * mm, stroke=0, fill=1); c.restoreState()
    text(c, "02", M, 9 * mm, "Disp-X", 14, LIME)
    text(c, "ARENA  ·  Nº 01  ·  OCTUBRE 2026", M + 11 * mm, 10.4 * mm, "Sans-SB", 6, LILAC, cs=1.4)
    c.showPage()


# =================== 03-04 INDIVIDUALES (texto propio) ===================
SC3 = 185 * mm


def p3_frames():
    return [Frame(X(0), 24 * mm, SP(2), H - SC3 - 30 * mm - 24 * mm, 0, 0, 0, 0)]


P4_TXT = 78 * mm


def p4_frames():
    ytop = TOP - 50 * mm - 6 * mm
    return make_frames(M, ytop - P4_TXT, W - M, ytop, ncols=4)


def individuales(story):
    bg()
    S_solo(0, H - SC3, W, SC3)
    tag("Deportes individuales", M, H - 18 * mm, INK, None)
    title_block(c, ["Solos", "contra", "el reloj"], M - 2, H - 40 * mm, 54, INK, lead=0.9, font="Disp-X", cs=-2)
    para(c, "Atletismo, natación, gimnasia, ciclismo: una persona, una marca.", DECK2(INK, 12.4), M, H - SC3 + 20 * mm, SP(2) - 10 * mm)
    story.insert(0, Paragraph("POR LA REDACCIÓN   ·   4 MIN DE LECTURA", ParagraphStyle("by", fontName="Sans-SB", fontSize=6.8, leading=9, textColor=MID, spaceAfter=7)))
    fr = p3_frames(); fill(c, story, fr); report("individuales p3", fr)
    # recuadro triatlón
    x = X(2); w = SP(2); yb = 24 * mm; hb = H - SC3 - 30 * mm - 24 * mm
    c.setFillColor(VIOLET); c.rect(x, yb, w, hb, stroke=0, fill=1)
    tag("Triatlón olímpico", x + 5 * mm, yb + hb - 9 * mm, LIME)
    for i, (n, u, d) in enumerate([("1,5", "km", "natación"), ("40", "km", "ciclismo"), ("10", "km", "carrera")]):
        yy = yb + hb - 22 * mm - i * 11.6 * mm
        text(c, n, x + 5 * mm, yy - 8, "Disp-X", 25, white, cs=-1)
        text(c, u, x + 5 * mm + pdfmetrics.stringWidth(n, "Disp-X", 25) + 3, yy - 8, "Disp-X", 11, LIME)
        text(c, d.upper(), x + w - 5 * mm, yy - 4, "Sans-B", 7.4, LILAC, "r", cs=1.6)
    footer2(3)
    c.showPage()
    # ---- p4
    bg()
    quote_h = 50 * mm
    c.setFillColor(INK); c.rect(M, TOP - quote_h, W - 2 * M, quote_h, stroke=0, fill=1)
    text(c, "“", M + 6 * mm, TOP - 19 * mm, "Disp-X", 76, LIME)
    para(c, "Contra el reloj no hay excusas. A favor, solo la preparación.", ParagraphStyle("q", fontName="Serif-I", fontSize=21, leading=27, textColor=BONE), M + 26 * mm, TOP - 16 * mm, W - 2 * M - 40 * mm)
    ytop = TOP - quote_h - 6 * mm
    iy = ytop - P4_TXT - 8 * mm
    S_pool(M, iy - 100 * mm, W - 2 * M, 100 * mm)
    c.setFillColor(VIOLET); c.rect(M, iy - 100 * mm - 2 * mm - 6.4, 2.2, 6.4, stroke=0, fill=1)
    para(c, "Cada carril es una promesa: nadie comparte la prueba, todos comparten el agua.", CAP2, M + 4 * mm, iy - 100 * mm - 2 * mm, W - 2 * M - 4 * mm)
    fr = p4_frames(); fill(c, story, fr); report("individuales p4", fr)
    assert not story, "individuales desborda %d" % len(story)
    footer2(4)
    c.showPage()


# =================== 05 COLECTIVOS ===================
def p5_frames():
    ytop = H - 82 * mm - 8 * mm
    img = (X(2), ytop - 80 * mm, W - M, ytop)
    ib_h = 12 * mm + 7.2 * mm * 5 + 2.5 * mm
    box = (M, BOT + 4 * mm, X(1) + C4, BOT + 4 * mm + ib_h)
    return make_frames(M, BOT, W - M, ytop, ncols=4, obst=[(img[0], img[1] - 9 * mm, img[2], img[3]), box])


def infobox2(x, ytop, w, title, rows, bgc=INK, accent=LIME, txt=BONE):
    rh = 7.2 * mm; th = 12 * mm; h = th + rh * len(rows) + 2.5 * mm
    c.setFillColor(bgc); c.rect(x, ytop - h, w, h, stroke=0, fill=1)
    c.setFillColor(accent); c.rect(x, ytop - 2.6, 14 * mm, 2.6, stroke=0, fill=1)
    text(c, title.upper(), x + 4 * mm, ytop - 8.6 * mm, "Sans-B", 6.8, txt, cs=1.2)
    for i, (a, b) in enumerate(rows):
        yy = ytop - th - rh * (i + 1) + 2.4 * mm
        c.setStrokeColor(HexColor("#44444C")); c.setLineWidth(0.4)
        c.line(x + 4 * mm, yy + rh - 2.2 * mm + 0.5, x + w - 4 * mm, yy + rh - 2.2 * mm + 0.5)
        text(c, a, x + 4 * mm, yy, "Sans", 7.6, txt)
        text(c, b, x + w - 4 * mm, yy, "Sans-B", 7.8, accent, "r")
    return h


def colectivos(story):
    bg()
    c.setFillColor(INK); c.rect(0, H - 82 * mm, W, 82 * mm, stroke=0, fill=1)
    tag("Deportes colectivos", M, H - 18 * mm, LIME)
    title_block(c, ["El juego", "de todos"], M - 2, H - 40 * mm, 54, BONE, lead=0.9, font="Disp-X", cs=-1.6)
    para(c, "Fútbol, voleibol, baloncesto y rugby: ganar es una tarea compartida.", DECK2(LILAC, 12.2), M, H - 66 * mm, SP(3))
    ytop = H - 82 * mm - 8 * mm
    S_team(X(2), ytop - 80 * mm, SP(2), 80 * mm)
    c.setFillColor(VIOLET); c.rect(X(2), ytop - 80 * mm - 2 * mm - 6.4, 2.2, 6.4, stroke=0, fill=1)
    para(c, "La cancha se lee en conjunto: cada posición abre espacio para otra.", CAP2, X(2) + 4 * mm, ytop - 80 * mm - 2 * mm, SP(2) - 4 * mm)
    ib_h = 12 * mm + 7.2 * mm * 5 + 2.5 * mm
    infobox2(M, BOT + 4 * mm + ib_h, SP(2), "Duración de un partido",
             [("Fútbol", "90 min"), ("Baloncesto", "40 min"), ("Rugby", "80 min"), ("Balonmano", "60 min"), ("Voleibol", "al mejor de 5 sets")])
    fr = p5_frames(); fill(c, story, fr); report("colectivos", fr)
    footer2(5)
    c.showPage()


# =================== 06 MONTAÑA + ALTURA ===================
SC6 = 118 * mm


def p6_frames():
    ytop = H - SC6 - 22 * mm
    ad = (X(2), AD_Y, W - M, AD_Y + AD_H)
    return make_frames(M, BOT, W - M, ytop, ncols=4, obst=[(ad[0], ad[1] - 0, ad[2], ad[3] + 4 * mm)])


def montana(story):
    bg()
    S_mount(0, H - SC6, W, SC6)
    scrim(c, 0, H - SC6, W, 60 * mm, color=INK, amax=0.85)
    tag("Deportes de montaña", M, H - SC6 + 41 * mm, LIME)
    title_block(c, ["Hasta", "la cima"], M - 2, H - SC6 + 28 * mm, 40, BONE, lead=0.9, font="Disp-X", cs=-1.2)
    para(c, "Escalada, senderismo y trail running: la naturaleza como cancha.", DECK2(INK, 12.2), M, H - SC6 - 6 * mm, SP(3))
    ytop = H - SC6 - 22 * mm
    fr = p6_frames(); fill(c, story, fr); report("montaña", fr)
    ad_altura(X(2), AD_Y, AD_W, AD_H)
    footer2(6)
    c.showPage()


# =================== 07 INVIERNO + NÓRDICA ===================
SC7 = 138 * mm


def p7_frames():
    ytop = H - SC7 - 10 * mm
    ad = (M, AD_Y, X(1) + C4, AD_Y + AD_H)
    return make_frames(M, BOT, W - M, ytop, ncols=4, obst=[(ad[0], ad[1], ad[2], ad[3] + 4 * mm)])


def invierno(story):
    bg()
    sw = X(2) - G / 2
    S_winter(0, H - SC7, sw, SC7)
    x = X(2)
    tag("Deportes de invierno", x, TOP - 4, VIOLET)
    title_block(c, ["Frío y", "velocidad"], x - 1, TOP - 26 * mm, 36, INK, lead=0.92, font="Disp-X", cs=-1)
    bar(x, TOP - 52 * mm)
    para(c, "Esquí, snowboard, patinaje y curling sobre nieve y hielo.", DECK2(INK, 12.2), x, TOP - 58 * mm, SP(2))
    infobox2(x, TOP - 86 * mm, SP(2), "Un deporte, un objeto",
             [("Esquí", "esquís"), ("Snowboard", "tabla"), ("Curling", "piedra"), ("Hockey sobre hielo", "disco")])
    fr = p7_frames(); fill(c, story, fr); report("invierno", fr)
    ad_nordica(M, AD_Y, AD_W, AD_H)
    footer2(7)
    c.showPage()


# =================== 08 PRECISIÓN + RITMO ===================
SC8H = 98 * mm


def p8_frames():
    ytop = H - 66 * mm - SC8H - 8 * mm
    ad = (X(2), AD_Y, W - M, AD_Y + AD_H)
    return make_frames(M, BOT, W - M, ytop, ncols=4, obst=[(ad[0], ad[1], ad[2], ad[3] + 4 * mm)])


def precision(story):
    bg()
    tag("Deportes de precisión", M, TOP - 4, VIOLET)
    title_block(c, ["Un punto", "exacto"], M - 2, TOP - 28 * mm, 56, INK, lead=0.9, font="Disp-X", cs=-1.6)
    ysc = H - 66 * mm
    S_prec(M, ysc - SC8H, SP(3), SC8H)
    para(c, "Tiro con arco, golf, dardos y boliche: la calma como técnica.", DECK2(INK, 12.2), X(3), ysc - 4 * mm, C4)
    infobox2(X(3), ysc - SC8H + 40 * mm, C4, "Datos", [("Arco", "70 m"), ("Dardos", "2,37 m"), ("Golf", "18 hoyos")], bgc=VIOLET, accent=LIME)
    fr = p8_frames(); fill(c, story, fr); report("precisión", fr)
    ad_ritmo(X(2), AD_Y, AD_W, AD_H)
    footer2(8)
    c.showPage()


# =================== 09 ADAPTADO (texto propio) ===================
def p9_geom(sc):
    return sc


def p9_frames(sc):
    return [Frame(M, 66 * mm, W - 2 * M, H - sc - 20 * mm - 66 * mm, 0, 0, 0, 0)]


def adaptado():
    story = None
    for sc in range(125, 70, -3):
        s = own(ADAPT)
        fr = make_frames(M, 62 * mm, W - M, H - sc * mm - 22 * mm, ncols=4)
        fill(cv.Canvas(io.BytesIO()), s, fr)
        if not s:
            break
    SC = sc * mm; print("adaptado: escena", sc, "mm")
    story = own(ADAPT)
    story.insert(0, Paragraph("POR LA REDACCIÓN   ·   3 MIN DE LECTURA", ParagraphStyle("by", fontName="Sans-SB", fontSize=6.8, leading=9, textColor=MID, spaceAfter=7)))
    bg()
    S_adapt(0, H - SC, W, SC)
    scrim(c, 0, H - SC, W, SC * 0.62, color=HexColor("#2A1A78"), amax=0.7)
    tag("Deporte adaptado", M, H - SC + 37 * mm, LIME)
    title_block(c, ["Sin barreras"], M - 2, H - SC + 20 * mm, 54, white, lead=0.9, font="Disp-X", cs=-2)
    para(c, "Mismo compromiso, reglas pensadas para cada persona.", DECK2(INK, 12.2), M, H - SC - 7 * mm, SP(3))
    fr = make_frames(M, 62 * mm, W - M, H - SC - 22 * mm, ncols=4)
    fill(c, story, fr); report("adaptado", fr)
    assert not story, "adaptado desborda"
    # franja de datos
    yb = 24 * mm; hb = 32 * mm
    c.setFillColor(INK); c.rect(M, yb, W - 2 * M, hb, stroke=0, fill=1)
    tag("Jugadores por equipo", M + 5 * mm, yb + hb - 8 * mm, LIME)
    items = [("3", "Goalball"), ("4", "Rugby en silla"), ("5", "Baloncesto en silla"), ("6", "Voleibol sentado")]
    cw = (W - 2 * M) / 4
    for i, (n, d) in enumerate(items):
        xx = M + 5 * mm + i * cw
        text(c, n, xx, yb + 7.5 * mm, "Disp-X", 34, BONE, cs=-1)
        parts = d.split(" ", 1)
        for jj, pt in enumerate(parts):
            text(c, pt.upper(), xx + 15 * mm, yb + 12 * mm - jj * 3.6 * mm, "Sans-B", 6.2, LILAC, cs=1)
    footer2(9)
    c.showPage()


# =================== 10 CONTRAPORTADA ===================
def contraportada():
    bg(LIME)
    photo = imgslots.has("arena", "contra")
    if photo:
        # foto bajo una franja lima con el titular; pie oscuro para la cabecera
        BAND = 102 * mm
        imgslots.photo(c, "arena", "contra", 0, 0, W, H - BAND)
        scrim(c, 0, 0, W, 70 * mm, color=INK, amax=0.88)
    else:
        import cover_art as ca
        clip_rect(c, 0, 0, W, H)
        ca.stadium(c, W * 0.52, H * 0.42, 230, 55, 14,
                   dict(stands=INK, rows=HexColor("#34343C"), track=VIOLET, lines=BONE, field=PINK,
                        field_lines=BONE, nums=BONE),
                   text, lanes=6, lane_w=11)
        c.restoreState()
    tag("Próximo número", M, H - 22 * mm, INK)
    for i, s in enumerate(["Elige", "tu arena."]):
        text(c, s, M - 2, H - 48 * mm - i * 25 * mm, "Disp-X", 74, INK, cs=-2.2)
    fg = LIME if photo else INK
    ms = fit_size("ARENA", "Disp-X", W - 2 * M, maxsize=120, cs=-4)
    text(c, "ARENA", M - 3, 22 * mm, "Disp-X", ms * 0.62, fg, cs=-3)
    text(c, "REVISTA DEPORTIVA", W - M, 31 * mm, "Sans-B", 7.6, fg, "r", cs=4)
    text(c, "Nº 01  ·  OCTUBRE 2026", W - M, 24 * mm, "Sans-SB", 7, BONE if photo else INK, "r", cs=2)
    c.showPage()


# =================== ENSAMBLADO ===================
cover(); c.showPage()
editorial_indice()
individuales(own(SOLO))
k = fit(lambda n: lorem2(11, n), [p5_frames]); colectivos(lorem2(11, k))
k = fit(lambda n: lorem2(22, n), [p6_frames]); montana(lorem2(22, k))
k = fit(lambda n: lorem2(33, n), [p7_frames]); invierno(lorem2(33, k))
k = fit(lambda n: lorem2(44, n), [p8_frames]); precision(lorem2(44, k))
adaptado()
contraportada()
c.save()
print("OK ->", OUT)
