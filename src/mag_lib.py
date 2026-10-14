import io, math, random
import idml_export
cv = idml_export.canvas_module      # lienzo de reportlab (o el que además registra para IDML)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os

# Registro para IDML: cada párrafo dibujado fuera de fill() queda anotado con su posición.
_draw_on = Paragraph.drawOn


def _draw_on_rec(self, canvas, x, y, _sW=0):
    idml_export.hook_para(self, canvas, x, y)
    return _draw_on(self, canvas, x, y, _sW)


Paragraph.drawOn = _draw_on_rec

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + os.sep
for name, f in [("Sans", "Inter-Regular"), ("Sans-M", "Inter-Medium"), ("Sans-SB", "Inter-SemiBold"),
                ("Sans-B", "Inter-Bold"), ("Sans-I", "Inter-Italic"), ("Sans-BI", "Inter-Bold"),
                ("Disp", "InterDisplay-Black"), ("Disp-I", "InterDisplay-BlackItalic"), ("Disp-X", "InterDisplay-ExtraBold"),
                ("Serif", "Lora-Regular"), ("Serif-M", "Lora-Medium"), ("Serif-SB", "Lora-SemiBold"),
                ("Serif-B", "Lora-Bold"), ("Serif-I", "Lora-Italic"), ("Serif-BI", "Lora-BoldItalic")]:
    pdfmetrics.registerFont(TTFont(name, FD + f + ".ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-BI")
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-B", italic="Serif-I", boldItalic="Serif-BI")

W, H = A4
M = 15 * mm
G = 5 * mm
CW = (W - 2 * M - 2 * G) / 3
BOT = 22 * mm
PAD = 4 * mm


def colx(i):
    return M + i * (CW + G)


NAVY = HexColor("#0B1F3A"); ORANGE = HexColor("#FF5A1F"); CREAM = HexColor("#F6F1E7")
TEAL = HexColor("#14A3A0"); YELLOW = HexColor("#FFC53D"); RED = HexColor("#C8262D")
GREEN = HexColor("#0F6B4F"); INK = HexColor("#1B1B1B"); GREY = HexColor("#6B6B6B")
CLAY = HexColor("#C9582A"); LGREY = HexColor("#D9D3C7")

BODY = ParagraphStyle("body", fontName="Serif", fontSize=9.2, leading=13.4, textColor=INK,
                      spaceAfter=5.5, alignment=TA_LEFT, allowWidows=0, allowOrphans=0)
BODYL = ParagraphStyle("bodyl", parent=BODY, fontSize=9.7, leading=14.2)
LEAD = ParagraphStyle("lead", parent=BODY, fontName="Serif-SB", fontSize=11.6, leading=16.4,
                      textColor=NAVY, spaceAfter=9)
CAP = ParagraphStyle("cap", fontName="Sans", fontSize=6.9, leading=9, textColor=GREY)
BYL = ParagraphStyle("byl", fontName="Sans-SB", fontSize=6.8, leading=9, textColor=GREY, spaceAfter=8)


def fit_size(s, font, width, maxsize=400, cs=0.0):
    """Tamaño de fuente para que el texto s ocupe exactamente `width` puntos."""
    unit = pdfmetrics.stringWidth(s, font, 1)
    # ancho = size*unit + cs*len(s)  (cs en puntos, fijo)
    return min(maxsize, (width - cs * len(s)) / unit)


def scrim(c, x, y, w, h, color=NAVY, amax=0.88, n=28, up=True):
    """Degradado oscuro: opaco en el borde inferior (up=True) y transparente arriba.

    Se dibuja como una imagen PNG con canal alfa (suave, sin franjas); en el IDML queda como un
    único objeto vinculado. `n` se conserva por compatibilidad."""
    path = _scrim_png(color, amax, up)
    c.drawImage(path, x, y, w, h, mask="auto")
    idml_export.hook_image(c, path, x, y, w, h, x, y, w, h, "degradado")


def _scrim_png(color, amax, up):
    from PIL import Image
    r, g, b = [round(v * 255) for v in color.rgb()]
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "cache")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "degradado_%02x%02x%02x_%d_%s.png" % (r, g, b, round(amax * 100), "abajo" if up else "arriba"))
    if not os.path.exists(p):
        R = 512
        im = Image.new("RGBA", (8, R))
        px = im.load()
        for row in range(R):
            t = 1 - row / (R - 1)          # 0 abajo, 1 arriba
            a = amax * ((1 - t) ** 1.7) if up else amax * (t ** 1.7)
            for col in range(8):
                px[col, row] = (r, g, b, round(a * 255))
        im.save(p)
    return p


def halftone(c, x, y, w, h, color, step=7, rmax=2.6, mode="left", alpha=1.0):
    clip_rect(c, x, y, w, h)
    c.setFillColor(color); c.setFillAlpha(alpha)
    nx, ny = int(w / step) + 2, int(h / step) + 2
    for j in range(ny):
        for i in range(nx):
            px = x + i * step + (step / 2 if j % 2 else 0)
            py = y + j * step
            if mode == "left": t = 1 - (px - x) / w
            elif mode == "right": t = (px - x) / w
            elif mode == "bottom": t = 1 - (py - y) / h
            elif mode == "top": t = (py - y) / h
            elif mode == "corner": t = 1 - math.hypot(px - x, py - y) / (0.95 * math.hypot(w, h))
            else: t = 1
            r = rmax * max(0.0, min(1.0, t)) ** 1.2
            if r > 0.25:
                c.circle(px, py, r, stroke=0, fill=1)
    c.restoreState()


def text(c, s, x, y, font, size, color, align="l", cs=0):
    t = c.beginText()
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(cs)
    idml_export.hook_text(c, s, x, y, font, size, color, align, cs)
    w = pdfmetrics.stringWidth(s, font, size) + cs * len(s)
    if align == "c":
        x = x - w / 2
    elif align == "r":
        x = x - w
    t.setTextOrigin(x, y)
    t.textOut(s)
    t.setCharSpace(0)  # el espaciado persiste en el estado gráfico: restablecer
    c.drawText(t)


def para(c, s, style, x, ytop, w):
    p = Paragraph(s, style)
    _, h = p.wrap(w, 10000)
    p.drawOn(c, x, ytop - h)
    return h


class FrameList(list):
    """Lista de marcos que recuerda la retícula y los obstáculos (para el ceñido en IDML)."""
    mf = None


def make_frames(x0, y0, x1, y1, ncols=3, obst=()):
    cw = (x1 - x0 - (ncols - 1) * G) / ncols
    frames = FrameList()
    frames.mf = (x0, y0, x1, y1, ncols, tuple(obst))
    for i in range(ncols):
        cx0 = x0 + i * (cw + G); cx1 = cx0 + cw
        blocks = []
        for (ox0, oy0, ox1, oy1) in obst:
            if ox1 + PAD > cx0 + 1 and ox0 - PAD < cx1 - 1:
                blocks.append((oy0 - PAD, oy1 + PAD))
        free = [(y0, y1)]
        for (b0, b1) in sorted(blocks):
            new = []
            for (f0, f1) in free:
                if b1 <= f0 or b0 >= f1:
                    new.append((f0, f1))
                else:
                    if b0 > f0: new.append((f0, b0))
                    if b1 < f1: new.append((b1, f1))
            free = new
        for (f0, f1) in sorted(free, key=lambda t: -t[1]):
            if f1 - f0 >= 30:
                frames.append(Frame(cx0, f0, cw, f1 - f0, 0, 0, 0, 0))
    return frames


def fill(c, story, frames):
    """Llena los marcos en orden y PARTE los párrafos entre columnas (addFromList no parte)."""
    idml_export.hook_flow(c, story, frames)
    idml_export.REC.suppress += 1
    try:
        return _fill(c, story, frames)
    finally:
        idml_export.REC.suppress -= 1


def _fill(c, story, frames):
    for f in frames:
        while story:
            h = story[0]
            if f.add(h, c, trySplit=0):
                story.pop(0)
                continue
            S = f.split(h, c)
            if S and len(S) > 1:
                f.add(S[0], c, trySplit=0)
                story[0:1] = S[1:]
            break
    return story


def fit(builder, makers, kmax=40):
    for k in range(kmax, 0, -1):
        story = builder(k)
        dummy = cv.Canvas(io.BytesIO())
        for mk in makers:
            fill(dummy, story, mk())
        if not story:
            if os.environ.get("DEBUG_FIT"):
                import re as _re
                print("FIT k=%d palabras=%d" % (k, sum(len(_re.sub("<[^>]+>", "", p.text).split()) for p in builder(k))))
            return k
    return 1


# ---------- lorem ----------
LW = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et "
      "dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea "
      "commodo consequat duis aute irure in reprehenderit voluptate velit esse cillum fugiat nulla pariatur "
      "excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum").split()


def lorem_sentence(rng):
    n = rng.randint(8, 17)
    s = " ".join(rng.choice(LW) for _ in range(n))
    return s.capitalize() + "."


def lorem_story(seed, k, heads=True):
    rng = random.Random(seed)
    out = []
    for i in range(k):
        txt = " ".join(lorem_sentence(rng) for _ in range(rng.randint(3, 5)))
        if heads and i % 3 == 2:
            h = " ".join(rng.choice(LW) for _ in range(3)).capitalize()
            txt = '<font name="Sans-B" color="#FF5A1F" size="8.6">%s.</font> %s' % (h.upper(), txt)
        out.append(Paragraph(txt, BODY))
    return out


# ---------- drawing primitives ----------
def clip_rect(c, x, y, w, h):
    c.saveState()
    p = c.beginPath(); p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)


def poly(c, pts, fill=None, stroke=None, lw=1):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    if fill is not None: c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.drawPath(p, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def circle(c, x, y, r, fill=None, stroke=None, lw=1):
    if fill is not None: c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.circle(x, y, r, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def line(c, x0, y0, x1, y1, color, lw=1, cap=1):
    c.setStrokeColor(color); c.setLineWidth(lw); c.setLineCap(cap)
    c.line(x0, y0, x1, y1)


def ball(c, cx, cy, r, fillc=white, patch=NAVY):
    circle(c, cx, cy, r, fill=fillc, stroke=patch, lw=max(1, r * 0.03))
    pts = [(cx + r * 0.36 * math.cos(math.radians(90 + 72 * k)), cy + r * 0.36 * math.sin(math.radians(90 + 72 * k))) for k in range(5)]
    poly(c, pts, fill=patch)
    for k in range(5):
        a = math.radians(90 + 72 * k)
        x1, y1 = cx + r * 0.36 * math.cos(a), cy + r * 0.36 * math.sin(a)
        x2, y2 = cx + r * 0.68 * math.cos(a), cy + r * 0.68 * math.sin(a)
        line(c, x1, y1, x2, y2, patch, r * 0.03)
        a2 = math.radians(90 + 72 * k + 36)
        tri = [(cx + r * 1.0 * math.cos(a2 - 0.30), cy + r * 1.0 * math.sin(a2 - 0.30)),
               (cx + r * 1.0 * math.cos(a2 + 0.30), cy + r * 1.0 * math.sin(a2 + 0.30)),
               (cx + r * 0.72 * math.cos(a2), cy + r * 0.72 * math.sin(a2))]
        poly(c, tri, fill=patch)


def grad_bands(c, x, y, w, h, c0, c1, n=30):
    for i in range(n):
        t = i / (n - 1)
        col = HexColor("#%02x%02x%02x" % tuple(int(c0[j] + (c1[j] - c0[j]) * t) for j in range(3)))
        c.setFillColor(col)
        c.rect(x, y + h - (i + 1) * h / n - 0.5, w, h / n + 1, stroke=0, fill=1)


def motion(c, x, y, length, n, color, lw, gap):
    for i in range(n):
        l = length * (0.55 + 0.45 * ((i * 37) % 10) / 10)
        line(c, x - l, y - i * gap, x, y - i * gap, color, lw)


# ---------- scenes ----------
def scene_team(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(GREEN); c.rect(x, y, w, h, stroke=0, fill=1)
    n = 10
    for i in range(n):
        if i % 2:
            c.setFillColor(HexColor("#13805E")); c.rect(x + i * w / n, y, w / n, h, stroke=0, fill=1)
    wl = white
    c.setStrokeColor(wl); c.setLineWidth(2.2)
    c.circle(x + w / 2, y + h / 2, h * 0.24, stroke=1, fill=0)
    c.line(x + w / 2, y, x + w / 2, y + h)
    c.rect(x - 4, y + h * 0.22, w * 0.14, h * 0.56, stroke=1, fill=0)
    c.rect(x + w - w * 0.14 + 4, y + h * 0.22, w * 0.14, h * 0.56, stroke=1, fill=0)
    cx, cy, r = x + w * 0.64, y + h * 0.5, h * 0.2
    c.saveState(); c.setFillColor(HexColor("#0A4A37")); c.setFillAlpha(0.5)
    c.ellipse(cx - r * 1.1, cy - r * 1.25, cx + r * 1.1, cy - r * 0.95, stroke=0, fill=1); c.restoreState()
    for i, (dy, ln, col) in enumerate([(0.55, 0.9, ORANGE), (0.25, 1.3, YELLOW), (-0.05, 1.0, ORANGE), (-0.35, 0.7, YELLOW)]):
        line(c, cx - r * 1.2 - w * 0.02 * i, cy + dy * r, cx - r * 1.2 - r * ln * 1.4, cy + dy * r, col, h * 0.018)
    ball(c, cx, cy, r)
    c.restoreState()


def scene_racket(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(CLAY); c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(white); c.setLineWidth(2.4)
    ix, iy = x + w * 0.06, y + h * 0.1
    c.rect(ix, iy, w * 0.88, h * 0.8, stroke=1, fill=0)
    c.line(ix, y + h * 0.5, ix + w * 0.88, y + h * 0.5)
    c.line(x + w * 0.5, iy + h * 0.2, x + w * 0.5, iy + h * 0.6)
    c.line(ix + w * 0.2, iy, ix + w * 0.2, iy + h * 0.8)
    c.line(ix + w * 0.68, iy, ix + w * 0.68, iy + h * 0.8)
    c.saveState()
    c.translate(x + w * 0.42, y + h * 0.5); c.rotate(32)
    rw, rh = h * 0.2, h * 0.27
    c.setStrokeColor(NAVY); c.setFillColor(HexColor("#EDE6D6"))
    p = c.beginPath(); p.ellipse(-rw, -rh + h * 0.12, rw, rh + h * 0.12)
    c.saveState(); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(HexColor("#F3EEDF")); c.rect(-rw, -rh, 2 * rw, 2.6 * rh, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#9AA3AF")); c.setLineWidth(0.8)
    for i in range(-8, 9):
        c.line(i * rw / 7, -rh, i * rw / 7, rh * 2)
    for j in range(-8, 12):
        c.line(-rw, h * 0.12 + j * rh / 7, rw, h * 0.12 + j * rh / 7)
    c.restoreState()
    c.setStrokeColor(NAVY); c.setLineWidth(h * 0.03)
    c.ellipse(-rw, -rh + h * 0.12, rw, rh + h * 0.12, stroke=1, fill=0)
    c.setFillColor(NAVY); c.roundRect(-h * 0.025, -rh - h * 0.2, h * 0.05, h * 0.2 + h * 0.12 - (-0) , h * 0.02, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.roundRect(-h * 0.03, -rh - h * 0.2, h * 0.06, h * 0.1, h * 0.02, stroke=0, fill=1)
    c.restoreState()
    bx, by, br = x + w * 0.76, y + h * 0.7, h * 0.07
    circle(c, bx, by, br, fill=HexColor("#D7E84B"))
    c.setStrokeColor(white); c.setLineWidth(br * 0.18)
    c.arc(bx - br * 1.6, by - br * 0.9, bx - br * 0.1, by + br * 0.9, -50, 100)
    c.arc(bx + br * 0.1, by - br * 0.9, bx + br * 1.6, by + br * 0.9, 130, 100)
    line(c, bx - br * 1.4, by + br * 1.5, bx - br * 3.4, by + br * 2.4, YELLOW, h * 0.012)
    line(c, bx - br * 1.8, by + br * 0.8, bx - br * 4.0, by + br * 1.4, YELLOW, h * 0.012)
    c.restoreState()


def scene_water(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (140, 220, 235), (8, 70, 135), 36)
    for k in range(3):
        yy = y + h * (0.28 + 0.2 * k)
        for i in range(int(w / 10) + 1):
            col = [RED, white, TEAL][(i + k) % 3]
            circle(c, x + i * 10, yy, 3.4, fill=col)
        line(c, x, yy, x + w, yy, white, 0.7)
    c.setStrokeColor(white)
    for k in range(6):
        yy = y + h * (0.12 + 0.14 * k)
        c.setLineWidth(1.4 + 0.2 * k)
        p = c.beginPath(); p.moveTo(x, yy)
        for i in range(1, 81):
            p.lineTo(x + w * i / 80, yy + math.sin(i / 80 * 14 + k) * h * 0.018)
        c.drawPath(p, stroke=1, fill=0)
    sx, sy = x + w * 0.58, y + h * 0.52
    circle(c, sx, sy, h * 0.055, fill=YELLOW)
    c.setStrokeColor(ORANGE); c.setLineWidth(h * 0.05); c.setLineCap(1)
    c.arc(sx - h * 0.38, sy - h * 0.25, sx + h * 0.02, sy + h * 0.28, 20, 100)
    c.setStrokeColor(HexColor("#F6C9A3")); c.setLineWidth(h * 0.045)
    c.arc(sx - h * 0.62, sy - h * 0.1, sx - h * 0.06, sy + h * 0.14, 10, 120)
    for (dx, dy, r) in [(-0.1, 0.08, 4), (0.12, 0.04, 3), (0.0, 0.14, 2.5), (0.18, -0.02, 3), (-0.2, 0.12, 3)]:
        circle(c, sx + dx * h, sy + dy * h, r, fill=white)
    c.restoreState()


def glove(c, cx, cy, s, ang, col):
    c.saveState(); c.translate(cx, cy); c.rotate(ang)
    c.setFillColor(col); c.setStrokeColor(HexColor("#5A0F14")); c.setLineWidth(s * 0.04)
    c.roundRect(-s * 0.5, -s * 0.38, s * 0.95, s * 0.76, s * 0.34, stroke=1, fill=1)
    c.ellipse(-s * 0.18, s * 0.18, s * 0.38, s * 0.56, stroke=1, fill=1)
    c.setFillColor(white); c.roundRect(-s * 0.78, -s * 0.3, s * 0.34, s * 0.6, s * 0.06, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#7A1A1F")); c.setLineWidth(s * 0.03)
    for k in range(3):
        c.line(s * 0.05 + k * s * 0.12, -s * 0.28, s * 0.05 + k * s * 0.12, s * 0.02)
    c.restoreState()


def scene_combat(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(HexColor("#2B0D10")); c.rect(x, y, w, h, stroke=0, fill=1)
    for i in range(8):
        c.setFillColor(HexColor("#%02x%02x%02x" % (60 + i * 8, 14 + i * 3, 18 + i * 3)))
        c.circle(x + w / 2, y + h * 0.5, h * (0.62 - i * 0.07), stroke=0, fill=1)
    for k, col in enumerate([RED, white, RED]):
        yy = y + h * (0.78 - k * 0.2)
        line(c, x, yy + h * 0.06, x + w, yy - h * 0.06, col, h * 0.022)
    line(c, x + w * 0.08, y, x + w * 0.1, y + h, HexColor("#444"), h * 0.03)
    line(c, x + w * 0.92, y, x + w * 0.9, y + h, HexColor("#444"), h * 0.03)
    cx, cy = x + w * 0.5, y + h * 0.45
    pts = []
    for k in range(16):
        r = h * (0.2 if k % 2 == 0 else 0.1)
        a = math.radians(k * 22.5)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly(c, pts, fill=YELLOW)
    glove(c, x + w * 0.3, cy, h * 0.3, -8, RED)
    c.saveState(); c.translate(x + w * 0.7, cy); c.scale(-1, 1)
    glove(c, 0, 0, h * 0.3, -8, ORANGE)
    c.restoreState()
    c.restoreState()


def scene_extreme(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    grad_bands(c, x, y, w, h, (45, 25, 90), (255, 190, 90), 40)
    circle(c, x + w * 0.86, y + h * 0.42, h * 0.16, fill=YELLOW)
    for (col, base, amp, seed) in [(HexColor("#5B3A7A"), 0.3, 0.3, 1), (HexColor("#2F2358"), 0.18, 0.34, 2), (NAVY, 0.0, 0.3, 3)]:
        rng = random.Random(seed)
        pts = [(x, y)]
        n = 7
        for i in range(n + 1):
            pts.append((x + w * i / n, y + h * (base + amp * rng.uniform(0.25, 1.0) * (0.4 + 0.6 * (i % 2)))))
        pts.append((x + w, y))
        poly(c, pts, fill=col)
    for (px, py, s) in [(0.22, 0.58, 0.07), (0.5, 0.5, 0.06)]:
        poly(c, [(x + w * px, y + h * py + h * s), (x + w * px - h * s * 0.8, y + h * py - h * s * 0.6), (x + w * px + h * s * 0.8, y + h * py - h * s * 0.6)], fill=white)
    gx, gy, gr = x + w * 0.68, y + h * 0.72, h * 0.18
    n = 6
    for i in range(n):
        a0 = 180 - i * 180 / n
        pts = [(gx, gy)]
        for t in range(0, 11):
            a = math.radians(a0 - t * (180 / n) / 10)
            pts.append((gx + gr * 1.4 * math.cos(a), gy + gr * 0.7 * math.sin(a)))
        poly(c, pts, fill=[RED, white][i % 2])
    for dx in (-1.3, -0.65, 0, 0.65, 1.3):
        line(c, gx + gr * dx * 0.95, gy + 1, gx, gy - gr * 1.1, white, 0.8)
    circle(c, gx, gy - gr * 1.25, h * 0.022, fill=NAVY)
    line(c, gx, gy - gr * 1.28, gx, gy - gr * 1.6, NAVY, h * 0.02)
    c.restoreState()


def scene_athletics(c, x, y, w, h):
    clip_rect(c, x, y, w, h)
    c.setFillColor(HexColor("#B8341E")); c.rect(x, y, w, h, stroke=0, fill=1)
    vx, vy = x + w * 0.5, y + h * 1.05
    for k in range(-5, 7):
        line(c, x + w * (0.5 + k * 0.26), y - 4, vx + (k - 0) * w * 0.012, vy, white, 2.2, 0)
    for i in range(1, 7):
        yy = y + h * (i / 7) ** 1.6 * 0.9
        c.saveState(); c.setStrokeColor(HexColor("#D45A3A")); c.setLineWidth(1); c.line(x, yy, x + w, yy); c.restoreState()
    circle(c, x + w * 0.82, y + h * 0.82, h * 0.1, fill=YELLOW)
    ox, oy, s = x + w * 0.46, y + h * 0.18, h * 0.52
    ink = NAVY
    c.setLineCap(1); c.setLineJoin(1)
    def seg(a, b, lw): line(c, ox + a[0] * s, oy + a[1] * s, ox + b[0] * s, oy + b[1] * s, ink, lw)
    lw = h * 0.05
    seg((0.0, 0.62), (0.06, 0.95), lw * 1.3)
    circle(c, ox + 0.1 * s, oy + 1.04 * s, s * 0.09, fill=ink)
    seg((0.06, 0.92), (0.26, 0.74), lw)
    seg((0.26, 0.74), (0.42, 0.88), lw * 0.8)
    seg((0.06, 0.92), (-0.14, 0.78), lw)
    seg((-0.14, 0.78), (-0.1, 0.56), lw * 0.8)
    seg((0.0, 0.62), (0.36, 0.5), lw)
    seg((0.36, 0.5), (0.36, 0.12), lw)
    seg((0.0, 0.62), (-0.26, 0.4), lw)
    seg((-0.26, 0.4), (-0.52, 0.5), lw)
    motion(c, ox - 0.3 * s, oy + 0.9 * s, s * 0.8, 5, white, 2, h * 0.07)
    c.restoreState()


def _polish(fn, col, alpha=0.28, rmax=3.4):
    def g(c, x, y, w, h):
        fn(c, x, y, w, h)
        halftone(c, x, y, w, h, col, step=8, rmax=rmax, mode="corner", alpha=alpha)
    return g


scene_team = _polish(scene_team, HexColor("#052E22"), 0.45)
scene_racket = _polish(scene_racket, HexColor("#7A2A10"), 0.40)
scene_water = _polish(scene_water, NAVY, 0.45)
scene_combat = _polish(scene_combat, HexColor("#12040A"), 0.5)
scene_extreme = _polish(scene_extreme, NAVY, 0.4)
scene_athletics = _polish(scene_athletics, HexColor("#5A150C"), 0.45)

SCENES = dict(team=scene_team, racket=scene_racket, water=scene_water,
              combat=scene_combat, extreme=scene_extreme, athletics=scene_athletics)


def footer(c, pageno, dark=False, numcol=None):
    numcol = numcol or ORANGE
    col = white if dark else GREY
    y = 10.5 * mm
    c.setStrokeColor(col); c.setLineWidth(0.4)
    c.line(M, y + 5.4 * mm, W - M, y + 5.4 * mm)
    label = "PULSO  ·  REVISTA DE DEPORTES  ·  Nº 01"
    if pageno % 2 == 0:
        text(c, "%02d" % pageno, M, y - 0.5, "Disp-I", 15, numcol)
        text(c, label, M + 14 * mm, y + 0.8, "Sans-SB", 6.2, col, cs=1.3)
    else:
        text(c, "%02d" % pageno, W - M, y - 0.5, "Disp-I", 15, numcol, "r")
        text(c, label, W - M - 14 * mm, y + 0.8, "Sans-SB", 6.2, col, "r", cs=1.3)


def infobox(c, x, ytop, w, title, rows, accent=ORANGE, bg=NAVY):
    rh = 7.2 * mm
    th = 12 * mm
    h = th + rh * len(rows) + 2.5 * mm
    c.setFillColor(bg); c.rect(x, ytop - h, w, h, stroke=0, fill=1)
    c.setFillColor(accent); c.rect(x, ytop - 2.6, 14 * mm, 2.6, stroke=0, fill=1)
    text(c, title.upper(), x + 4 * mm, ytop - 8.6 * mm, "Sans-B", 6.8, white, cs=1.2)
    for i, (a, b) in enumerate(rows):
        yy = ytop - th - rh * (i + 1) + 2.4 * mm
        c.setStrokeColor(HexColor("#3A4C6A")); c.setLineWidth(0.4)
        c.line(x + 4 * mm, yy + rh - 2.2 * mm + 0.5, x + w - 4 * mm, yy + rh - 2.2 * mm + 0.5)
        text(c, a, x + 4 * mm, yy, "Sans", 7.6, HexColor("#DCE4F2"))
        text(c, b, x + w - 4 * mm, yy, "Sans-B", 7.8, YELLOW, "r")
    return h


def quote(c, s, x, ytop, w, h, bg=NAVY, fg=white, size=19, mark=ORANGE):
    c.setFillColor(bg); c.rect(x, ytop - h, w, h, stroke=0, fill=1)
    text(c, "“", x + 5 * mm, ytop - 17 * mm, "Disp-I", 78, mark)
    st = ParagraphStyle("q", fontName="Serif-I", fontSize=size, leading=size * 1.28, textColor=fg)
    p = Paragraph(s, st)
    _, ph = p.wrap(w - 30 * mm, 1000)
    p.drawOn(c, x + 21 * mm, ytop - h / 2 - ph / 2 + 1.5 * mm)


def image_block(c, kind, x, y, w, h, caption=None):
    SCENES[kind](c, x, y, w, h)
    if caption:
        c.setFillColor(ORANGE); c.rect(x, y - 2 * mm - 6.4, 2.2, 6.4, stroke=0, fill=1)
        para(c, caption, CAP, x + 4 * mm, y - 2 * mm, w - 4 * mm)


def kicker(c, s, x, y, color=ORANGE, cs=1.9, rule=True):
    if rule:
        c.setFillColor(color); c.rect(x, y + 0.9, 7 * mm, 1.6, stroke=0, fill=1)
        x += 9.5 * mm
    text(c, s.upper(), x, y, "Sans-B", 7.4, color, cs=cs)


def title_block(c, lines, x, ybase, size, color, lead=0.88, font="Disp-I", cs=-1.0):
    """Titular en mayúsculas, interlineado ajustado. ybase = línea base de la primera línea."""
    for i, s in enumerate(lines):
        text(c, s.upper(), x, ybase - i * size * lead, font, size, color, cs=cs)
