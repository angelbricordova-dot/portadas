"""Figuras humanas detalladas en estilo de ilustración plana (sustituyen a los «palitos»).

Una figura se define por un esqueleto (ángulos de cada articulación) y un estilo (piel, ropa, calzado,
pelo o casco). Se dibuja por capas: extremidades del lado lejano (tono más oscuro), tronco, cabeza y
extremidades del lado cercano. Las extremidades tienen perfil muscular (muslo, gemelo, bíceps), la ropa
cubre las partes que corresponde y el calzado tiene suela y franja.

Unidades: estatura = 1. Ángulos absolutos en grados (0 = derecha, 90 = arriba); la figura mira a la
derecha (usar mirror=True para que mire a la izquierda).
"""
import math
from reportlab.lib.colors import HexColor, Color


def shade(col, k=0.78):
    r, g, b = col.rgb()
    return Color(r * k, g * k, b * k)


def _pt(p, a, d):
    return (p[0] + d * math.cos(math.radians(a)), p[1] + d * math.sin(math.radians(a)))


def _chain(o, lens, angs):
    pts = [o]
    for L, a in zip(lens, angs):
        pts.append(_pt(pts[-1], a, L))
    return pts


def _interp(prof, t):
    """Perfil de anchura [(t, w), ...] con interpolación suave (coseno)."""
    for (t0, w0), (t1, w1) in zip(prof, prof[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 0
            u = (1 - math.cos(math.pi * u)) / 2
            return w0 + (w1 - w0) * u
    return prof[-1][1]


class Painter:
    def __init__(self, c, x, y, s, mirror=False):
        self.c, self.x, self.y, self.s, self.m = c, x, y, s, -1 if mirror else 1

    def T(self, p):
        return (self.x + self.m * p[0] * self.s, self.y + p[1] * self.s)

    def poly(self, pts, col, alpha=1.0):
        c = self.c
        c.saveState()
        c.setFillColor(col)
        if alpha < 1:
            c.setFillAlpha(alpha)
        P = [self.T(p) for p in pts]
        path = c.beginPath(); path.moveTo(*P[0])
        for q in P[1:]:
            path.lineTo(*q)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        c.restoreState()

    def disc(self, p, r, col):
        X, Y = self.T(p)
        self.c.setFillColor(col)
        self.c.circle(X, Y, r * self.s, stroke=0, fill=1)

    def ellipse(self, p, rx, ry, ang, col, n=24):
        pts = []
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for k in range(n):
            t = 2 * math.pi * k / n
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            pts.append((p[0] + ex * ca - ey * sa, p[1] + ex * sa + ey * ca))
        self.poly(pts, col)

    def organ(self, p0, p1, prof, col, t0=0.0, t1=1.0, caps=True):
        """Forma alargada entre p0 y p1 con perfil de anchura `prof`, dibujada entre t0 y t1."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1e-6
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        n = 14
        left, right = [], []
        for k in range(n + 1):
            t = t0 + (t1 - t0) * k / n
            w = _interp(prof, t) / 2
            cx, cy = p0[0] + dx * t, p0[1] + dy * t
            left.append((cx + nx * w, cy + ny * w))
            right.append((cx - nx * w, cy - ny * w))
        pts = left[:]
        if caps and t1 >= 0.999:                      # remate redondo al final
            w = _interp(prof, t1) / 2
            ex, ey = p0[0] + dx * t1, p0[1] + dy * t1
            for k in range(1, 8):
                a = math.pi / 2 - math.pi * k / 8
                pts.append((ex + (nx * math.sin(a) + ux * math.cos(a)) * w, ey + (ny * math.sin(a) + uy * math.cos(a)) * w))
        pts += right[::-1]
        if caps and t0 <= 0.001:                      # remate redondo al inicio
            w = _interp(prof, t0) / 2
            for k in range(1, 8):
                a = -math.pi / 2 - math.pi * k / 8
                pts.append((p0[0] + (nx * math.sin(a) + ux * math.cos(a)) * w, p0[1] + (ny * math.sin(a) + uy * math.cos(a)) * w))
        self.poly(pts, col)


# perfiles musculares (anchura en función de la posición a lo largo del segmento)
THIGH = [(0, 0.104), (0.3, 0.1), (1, 0.064)]
SHIN = [(0, 0.064), (0.28, 0.072), (0.75, 0.046), (1, 0.04)]
UPPER = [(0, 0.06), (0.45, 0.058), (1, 0.044)]
FORE = [(0, 0.046), (0.3, 0.05), (1, 0.034)]


def shoe(P, ankle, toe, col, sole, stripe, sock=None):
    dx, dy = toe[0] - ankle[0], toe[1] - ankle[1]
    L = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux                                   # hacia el empeine (lado delantero del pie)

    def Q(a, b):
        return (ankle[0] + ux * a + nx * b, ankle[1] + uy * a + ny * b)

    if sock:
        P.organ(Q(-0.004, 0.03), Q(0.0, -0.002), [(0, 0.046), (1, 0.046)], sock, caps=False)
    upper = [Q(-0.038, 0.032), Q(-0.042, -0.006), Q(L + 0.018, -0.008), Q(L + 0.03, 0.004),
             Q(L + 0.012, 0.02), Q(L * 0.45, 0.036), Q(L * 0.05, 0.04)]
    P.poly(upper, col)
    P.poly([Q(-0.044, -0.004), Q(L + 0.022, -0.006), Q(L + 0.032, 0.0), Q(L + 0.028, -0.018),
            Q(-0.04, -0.018)], sole)
    P.poly([Q(L * 0.15, 0.03), Q(L * 0.32, 0.034), Q(L * 0.55, 0.0), Q(L * 0.38, -0.004)], stripe)


def head(P, neck_top, tilt, style, far=False):
    """Cabeza de perfil mirando a la derecha. tilt: inclinación (grados, + = hacia delante)."""
    hc = _pt(neck_top, 90 - tilt, 0.06)
    skin = style["skin"]
    P.disc(hc, 0.064, skin)
    P.poly([_pt(hc, -10 - tilt, 0.058), _pt(hc, -20 - tilt, 0.082), _pt(hc, -38 - tilt, 0.06)], skin)   # nariz
    P.ellipse(_pt(hc, -70 - tilt, 0.05), 0.03, 0.022, -tilt, skin)                                     # mandíbula
    if style.get("helmet"):
        col = style["helmet"]
        pts = [_pt(hc, a - tilt, 0.074) for a in range(5, 200, 12)] + [_pt(hc, 200 - tilt, 0.05), _pt(hc, 5 - tilt, 0.05)]
        P.poly(pts, col)
        P.poly([_pt(hc, 0 - tilt, 0.072), _pt(hc, 18 - tilt, 0.09), _pt(hc, 25 - tilt, 0.07)], col)       # visera
        if style.get("goggles"):
            P.poly([_pt(hc, -8 - tilt, 0.066), _pt(hc, 22 - tilt, 0.068), _pt(hc, 30 - tilt, 0.04),
                    _pt(hc, -5 - tilt, 0.035)], style["goggles"])
    else:
        hair = style.get("hair", HexColor("#1A1214"))
        pts = [_pt(hc, a - tilt, 0.069) for a in range(60, 250, 10)] + [_pt(hc, 250 - tilt, 0.03), _pt(hc, 80 - tilt, 0.045)]
        P.poly(pts, hair)
        if style.get("ponytail"):
            base = _pt(hc, 175 - tilt, 0.062)
            P.organ(base, _pt(base, 200 - tilt, 0.1), [(0, 0.04), (0.5, 0.045), (1, 0.012)], hair)
    P.ellipse(_pt(hc, 175 - tilt, 0.008), 0.014, 0.019, -tilt, shade(skin, 0.82))                        # oreja
    return hc


def ik(origin, target, l1, l2, bend):
    """Cinemática inversa de dos segmentos: ángulos (grados) para llegar de origin a target.
    bend=+1 dobla la articulación hacia el lado antihorario (rodilla adelante si mira a la derecha)."""
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    d = min(math.hypot(dx, dy), (l1 + l2) * 0.999)
    a0 = math.atan2(dy, dx)
    alpha = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    a1 = a0 + bend * alpha
    j = (origin[0] + l1 * math.cos(a1), origin[1] + l1 * math.sin(a1))
    a2 = math.atan2(target[1] - j[1], target[0] - j[0])
    return [math.degrees(a1), math.degrees(a2)]


def resolve(pose, leg_len=(0.245, 0.245)):
    """Convierte objetivos {'target': (x, y), 'bend': ±1, 'foot': ángulo} en ángulos."""
    lean = pose.get("lean", 0)
    sh = _pt((0, 0), 90 - lean, 0.29)
    out = dict(pose)
    out["legs"], out["arms"] = {}, {}
    for side, v in pose["legs"].items():
        if isinstance(v, dict):
            o = (0.012 if side == "near" else -0.012, 0)
            out["legs"][side] = ik(o, v["target"], leg_len[0], leg_len[1], v.get("bend", 1)) + [v.get("foot", 0)]
        else:
            out["legs"][side] = v
    for side, v in pose["arms"].items():
        if isinstance(v, dict):
            o = _pt(sh, -90 - lean, 0.02)
            out["arms"][side] = ik(o, v["target"], 0.165, 0.15, v.get("bend", -1))
        else:
            out["arms"][side] = v
    return out


def figure(c, x, y, s, pose, style, mirror=False, only=None):
    """Dibuja una figura. (x, y) = punto de la cadera en el lienzo; s = estatura en puntos.

    pose: dict(lean, legs={'near': [muslo, pierna, pie], 'far': [...]}, arms={'near': [brazo, antebrazo],
          'far': [...]}, tilt=inclinación de la cabeza, knee_len=(0.245, 0.245)).
    style: dict(skin, top, bottom, shoes, sole, stripe, sock, hair|helmet, sleeves(0..1), pants(bool))."""
    pose = resolve(pose, pose.get("leg_len", (0.245, 0.245)))
    P = Painter(c, x, y, s, mirror)
    body = only in (None, "body")
    hip = (0.0, 0.0)
    lean = pose.get("lean", 0)
    sh = _pt(hip, 90 - lean, 0.29)
    neck_top = _pt(sh, 90 - lean * 0.6, 0.055)
    lt, ls = pose.get("leg_len", (0.245, 0.245))
    legs = {k: _chain(_pt(hip, 0, 0.012 if k == "near" else -0.012), [lt, ls, 0.08], v) for k, v in pose["legs"].items()}
    arms = {k: _chain(_pt(sh, -90 - lean, 0.02), [0.165, 0.15], v) for k, v in pose["arms"].items()}
    out = dict(hip=hip, shoulder=sh, legs=legs, arms=arms)

    def draw_leg(side):
        k = 0.8 if side == "far" else 1.0
        hp, kn, an, to = legs[side]
        skin, bottom = shade(style["skin"], k), shade(style["bottom"], k)
        pants = style.get("pants", False)
        P.organ(kn, an, SHIN, bottom if pants else skin)
        P.organ(hp, kn, THIGH, skin if not pants else bottom)
        if not pants:
            P.disc(hp, 0.06, bottom)
            P.organ(hp, kn, [(0, 0.12), (0.5, 0.114), (1, 0.106)], bottom, 0, style.get("shorts", 0.42), caps=False)
        P.disc(kn, 0.033 if not pants else 0.035, bottom if pants else skin)
        shoe(P, an, to, shade(style["shoes"], k), style.get("sole", HexColor("#F4F1EA")),
             shade(style.get("stripe", style["shoes"]), k), None if pants else shade(style.get("sock", style["sole"]), k))

    def draw_arm(side):
        k = 0.8 if side == "far" else 1.0
        sp, el, wr = arms[side]
        skin, top = shade(style["skin"], k), shade(style["top"], k)
        sleeves = style.get("sleeves", 0.0)
        P.organ(el, wr, FORE, top if sleeves >= 1 else skin)
        P.organ(sp, el, UPPER, top if sleeves >= 1 else skin)
        if 0 < sleeves < 1:
            P.organ(sp, el, [(0, 0.068), (1, 0.06)], top, 0, sleeves, caps=False)
        P.disc(el, 0.022, top if sleeves >= 1 else skin)
        hand_dir = math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0]))
        P.ellipse(_pt(wr, hand_dir, 0.022), 0.03, 0.021, hand_dir, skin)       # mano cerrada
        if sleeves >= 1 and style.get("gloves"):
            P.ellipse(_pt(wr, hand_dir, 0.022), 0.033, 0.024, hand_dir, shade(style["gloves"], k))

    hc = None
    if body:
        draw_leg("far")
        draw_arm("far")
        # tronco: cadera estrecha, cintura, pecho y hombros
        P.organ(hip, sh, [(0, 0.13), (0.35, 0.118), (0.72, 0.15), (1, 0.13)], style["top"])
        P.organ(hip, sh, [(0, 0.142), (1, 0.13)], style["bottom"], 0, 0.22, caps=False)             # cintura del short
        if style.get("bottom_band"):
            P.organ(hip, sh, [(0, 0.144), (1, 0.132)], style["bottom_band"], 0.2, 0.24, caps=False)
        P.organ(_pt(sh, 90 - lean, -0.01), neck_top, [(0, 0.052), (1, 0.046)], style["skin"])       # cuello
        if style.get("top_stripe"):
            P.organ(hip, sh, [(0, 0.03), (1, 0.03)], style["top_stripe"], 0.25, 0.95, caps=False)
        hc = head(P, neck_top, pose.get("tilt", lean * 0.4), style)
        draw_leg("near")
    if only in (None, "near_arm"):
        draw_arm("near")
    out["head"] = hc
    out["T"] = P.T
    return out


# ---------------------------------------------------------------- poses
RUN = dict(lean=14, tilt=4,
           legs=dict(near=[-28, -112, -10], far=[-112, 158, -135]),
           arms=dict(near=[-140, -100], far=[-58, 55]))

SPRINT = dict(lean=22, tilt=10,
              legs=dict(near=[-20, -100, -5], far=[-118, 170, -150]),
              arms=dict(near=[-150, -95], far=[-50, 65]))


def lowest(pose, leg_len=(0.245, 0.245)):
    """Punto más bajo de los pies respecto de la cadera (para apoyar la figura en el suelo)."""
    ys = []
    for v in pose["legs"].values():
        pts = _chain((0, 0), [leg_len[0], leg_len[1], 0.08], v)
        ys += [p[1] for p in pts[1:]]
    return min(ys) - 0.02


def player_top(c, x, y, s, facing, jersey, skin, hair, shoes, number=None, num_col=None, text_fn=None, arms_up=0.0):
    """Jugador visto desde arriba (planta). s = ancho de hombros en puntos; facing en grados.
    arms_up: 0 = brazos a los lados, 1 = brazos hacia delante (defendiendo/recibiendo)."""
    c.saveState()
    c.translate(x, y); c.rotate(facing - 90)            # el jugador «mira» hacia +y local
    P = Painter(c, 0, 0, s)
    # zapatillas (asoman delante y detrás: zancada)
    P.ellipse((-0.18, 0.32), 0.075, 0.13, 0, shoes)
    P.ellipse((0.18, -0.26), 0.075, 0.13, 0, shoes)
    # brazos
    for side in (-1, 1):
        sh = (side * 0.44, 0.02)
        a = 90 + side * (25 + 45 * (1 - arms_up))
        el = _pt(sh, a, 0.28)
        hd = _pt(el, 90 + side * (10 + 30 * (1 - arms_up)), 0.24)
        P.organ(sh, el, [(0, 0.16), (1, 0.12)], skin)
        P.organ(el, hd, [(0, 0.12), (1, 0.1)], skin)
        P.disc(hd, 0.075, skin)
        P.organ(sh, el, [(0, 0.2), (1, 0.17)], jersey, 0, 0.35, caps=False)   # manga
    # tronco (hombros) y cabeza
    P.ellipse((0, 0), 0.52, 0.24, 0, jersey)
    P.ellipse((0, -0.02), 0.5, 0.2, 0, shade(jersey, 0.9))
    if number and text_fn:
        text_fn(c, str(number), 0, -0.13 * s, "Disp-X", 0.22 * s, num_col, "c", 0)
    P.disc((0, 0.04), 0.2, skin)
    P.ellipse((0, -0.01), 0.19, 0.17, 0, hair)
    P.ellipse((0, 0.21), 0.05, 0.03, 0, skin)                              # nariz
    c.restoreState()
