"""Gráficos de portada (PULSO e Ímpetu): balón 3D, trazo de pulso, código de barras y corredor.

Todo es vectorial y se dibuja con las primitivas de reportlab, así que sale igual en el PDF y en el IDML.
"""
import math
import itertools
import numpy as np
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

PHI = (1 + 5 ** 0.5) / 2


# ------------------------------------------------------------------ balón
def _truncated_icosahedron():
    """Vértices (60) y caras pentagonales (12) del balón clásico, en la esfera unidad."""
    base = []
    for a, b, cc in [(0, 1, 3 * PHI), (1, 2 + PHI, 2 * PHI), (PHI, 2, PHI ** 3)]:
        for sa, sb, sc in itertools.product([1, -1], repeat=3):
            v = (a * sa, b * sb, cc * sc)
            for k in range(3):                       # permutaciones cíclicas
                base.append(tuple(v[(i + k) % 3] for i in range(3)))
    V = np.unique(np.round(np.array(base, float), 6), axis=0)
    V = V / np.linalg.norm(V, axis=1)[:, None]
    # aristas: pares a distancia mínima
    D = np.linalg.norm(V[:, None] - V[None], axis=2)
    dmin = np.min(D[D > 1e-6])
    edges = [(i, j) for i in range(len(V)) for j in range(i + 1, len(V)) if abs(D[i, j] - dmin) < 1e-4]
    # pentágonos: alrededor de los 12 vértices del icosaedro
    ico = []
    for p in [(0, 1, PHI), (0, 1, -PHI), (0, -1, PHI), (0, -1, -PHI)]:
        for k in range(3):
            ico.append(tuple(p[(i + k) % 3] for i in range(3)))
    ico = np.array(ico, float)
    ico /= np.linalg.norm(ico, axis=1)[:, None]
    pents = []
    for cdir in ico:
        idx = np.argsort(-V @ cdir)[:5]
        # ordenar alrededor del centro
        e1 = np.cross(cdir, [0.3, 0.5, 0.8]); e1 /= np.linalg.norm(e1)
        e2 = np.cross(cdir, e1)
        ang = [math.atan2(V[i] @ e2, V[i] @ e1) for i in idx]
        pents.append((cdir, [i for _, i in sorted(zip(ang, idx))]))
    return V, edges, pents


_TI = _truncated_icosahedron()


def _rot(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def _arc(a, b, n=8):
    """Puntos sobre el arco de círculo máximo entre a y b (esfera unidad)."""
    out = []
    for k in range(n + 1):
        t = k / n
        p = a * (1 - t) + b * t
        out.append(p / np.linalg.norm(p))
    return out


def ball3d(c, cx, cy, r, rot=(0.35, -0.5, 0.2), base=white, patch=HexColor("#0B1F3A"),
           shade=HexColor("#0B1F3A"), seam=None, light=(-0.55, 0.6, 0.6)):
    """Balón de fútbol en perspectiva (proyección ortográfica de un icosaedro truncado).

    Pentágonos curvos sobre la esfera, costuras visibles y un sombreado plano en dos tonos
    (zona en sombra con opacidad), coherente con el estilo de ilustración plana."""
    V, edges, pents = _TI
    R = _rot(*rot)
    P = V @ R.T
    seam = seam or patch
    c.saveState()
    # sombra proyectada en el suelo (elipse)
    c.setFillColor(shade); c.setFillAlpha(0.35)
    c.ellipse(cx - r * 0.9, cy - r * 1.13, cx + r * 0.9, cy - r * 0.95, stroke=0, fill=1)
    c.setFillAlpha(1)
    # base
    c.setFillColor(base); c.circle(cx, cy, r, stroke=0, fill=1)
    p = c.beginPath(); p.circle(cx, cy, r); c.clipPath(p, stroke=0, fill=0)

    def to2d(q):
        return cx + q[0] * r, cy + q[1] * r

    # pentágonos visibles (curvos)
    for cdir, idx in pents:
        cz = (R @ cdir)[2]
        if cz < -0.25:
            continue
        pts = []
        for a, b in zip(idx, idx[1:] + idx[:1]):
            pts += _arc(P[a], P[b])[:-1]
        path = c.beginPath()
        q0 = to2d(pts[0]); path.moveTo(*q0)
        for q in pts[1:]:
            path.lineTo(*to2d(q))
        path.close()
        c.setFillColor(patch)
        c.drawPath(path, stroke=0, fill=1)
    # costuras (aristas de los hexágonos) en la cara visible
    c.setStrokeColor(seam); c.setLineWidth(max(0.6, r * 0.022)); c.setLineCap(1)
    for i, j in edges:
        arc = _arc(P[i], P[j], 6)
        if min(q[2] for q in arc) < 0.02:
            continue
        path = c.beginPath(); path.moveTo(*to2d(arc[0]))
        for q in arc[1:]:
            path.lineTo(*to2d(q))
        c.drawPath(path, stroke=1, fill=0)
    # sombreado: media luna oscura opuesta a la luz (polígono = disco menos disco desplazado)
    from shapely.geometry import Point
    lx, ly = light[0], light[1]
    L = math.hypot(lx, ly)
    ox, oy = lx / L * r * 0.42, ly / L * r * 0.42
    moon = Point(cx, cy).buffer(r * 1.02, 64).difference(Point(cx + ox, cy + oy).buffer(r, 64))
    for g in getattr(moon, "geoms", [moon]):
        if g.is_empty:
            continue
        pts = list(g.exterior.coords)
        c.setFillColor(shade); c.setFillAlpha(0.28)
        path = c.beginPath(); path.moveTo(*pts[0])
        for q in pts[1:]:
            path.lineTo(*q)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
    c.setFillAlpha(1)
    # brillo
    c.setFillColor(white); c.setFillAlpha(0.55)
    c.ellipse(cx - r * 0.62, cy + r * 0.38, cx - r * 0.30, cy + r * 0.58, stroke=0, fill=1)
    c.setFillAlpha(1)
    c.restoreState()
    c.saveState()
    c.setStrokeColor(patch); c.setLineWidth(max(1, r * 0.03))
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.restoreState()


# ------------------------------------------------------------------ pulso
def ecg_points(x0, x1, y, amp):
    """Trazo de electrocardiograma (P, QRS, T) entre x0 y x1, con dos latidos."""
    pts = [(x0, y)]
    span = x1 - x0
    for beat in (0.18, 0.62):
        b = x0 + span * beat
        u = span * 0.06
        pts += [(b - 2.2 * u, y), (b - 1.7 * u, y + amp * 0.12), (b - 1.2 * u, y),       # P
                (b - 0.6 * u, y), (b - 0.35 * u, y - amp * 0.18), (b, y + amp),            # Q, R
                (b + 0.4 * u, y - amp * 0.42), (b + 0.75 * u, y),                          # S
                (b + 1.6 * u, y), (b + 2.2 * u, y + amp * 0.22), (b + 2.9 * u, y)]         # T
    pts.append((x1, y))
    return pts


def polyline(c, pts, color, lw, alpha=1.0):
    c.saveState()
    c.setStrokeColor(color); c.setLineWidth(lw); c.setLineCap(1); c.setLineJoin(1)
    c.setStrokeAlpha(alpha)
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


# ------------------------------------------------------------------ código de barras
_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
_G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
_R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
_PAR = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def ean13(digits12):
    d = [int(x) for x in digits12]
    chk = (10 - (sum(d[i] * (3 if i % 2 else 1) for i in range(12)) % 10)) % 10
    d.append(chk)
    bits = "101"
    for i, ch in enumerate(_PAR[d[0]]):
        bits += (_L if ch == "L" else _G)[d[i + 1]]
    bits += "01010"
    for k in d[7:]:
        bits += _R[k]
    bits += "101"
    return "".join(map(str, d)), bits


def barcode(c, x, y, w, h, digits12, text_fn, ink=HexColor("#111111"), paper=white, label=None, font="Sans"):
    """Código EAN-13 (ficticio) con su caja blanca. (x, y) = esquina inferior izquierda de la caja."""
    code, bits = ean13(digits12)
    c.saveState()
    c.setFillColor(paper); c.rect(x, y, w, h, stroke=0, fill=1)
    pad = w * 0.08
    mw = (w - 2 * pad) / len(bits)
    by = y + h * 0.26
    bh = h - h * 0.26 - pad * 0.8
    if label:
        bh -= h * 0.14
        text_fn(c, label, x + w / 2, y + h - pad * 0.8 - h * 0.1, font, h * 0.085, ink, "c", 0.6)
    c.setFillColor(ink)
    for i, b in enumerate(bits):
        if b == "1":
            long_ = i < 3 or 45 <= i < 50 or i >= 92
            c.rect(x + pad + i * mw, by - (h * 0.07 if long_ else 0), mw * 1.02, bh + (h * 0.07 if long_ else 0), stroke=0, fill=1)
    text_fn(c, "%s %s %s" % (code[0], code[1:7], code[7:]), x + w / 2, y + h * 0.07, font, h * 0.11, ink, "c", 0.8)
    c.restoreState()


# ------------------------------------------------------------------ corredor
def _seg(c, p0, p1, w0, w1, col):
    """Segmento ahusado con extremos redondeados."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    c.setFillColor(col)
    p = c.beginPath()
    p.moveTo(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2)
    p.lineTo(p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2)
    p.lineTo(p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2)
    p.lineTo(p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.circle(p0[0], p0[1], w0 / 2, stroke=0, fill=1)
    c.circle(p1[0], p1[1], w1 / 2, stroke=0, fill=1)


def _chain(origin, lengths, angles):
    """Cadena articulada: ángulos absolutos en grados (0 = derecha, 90 = arriba)."""
    pts = [origin]
    for L, a in zip(lengths, angles):
        x, y = pts[-1]
        pts.append((x + L * math.cos(math.radians(a)), y + L * math.sin(math.radians(a))))
    return pts


def runner_pose():
    """Esqueleto (unidades = estatura) de un corredor en fase de vuelo, de perfil, hacia la derecha.

    Proporciones humanas (muslo y pierna 0,245, brazo 0,17, antebrazo 0,15, cabeza 1/8) y ángulos de la
    mecánica de carrera: tronco inclinado ~14°, rodilla delantera alta con el pie bajo la rodilla,
    talón trasero recogido tras el impulso y brazos opuestos a las piernas con los codos a ~90°."""
    lean = 14
    hip = (0.0, 0.53)
    shoulder = (hip[0] + 0.29 * math.sin(math.radians(lean)), hip[1] + 0.29 * math.cos(math.radians(lean)))
    neck = (shoulder[0] + 0.035, shoulder[1] + 0.05)
    head = (shoulder[0] + 0.07, shoulder[1] + 0.115)
    return dict(hip=hip, shoulder=shoulder, neck=neck, head=head,
                front_leg=_chain(hip, [0.245, 0.245, 0.085], [-28, -112, -10]),
                back_leg=_chain(hip, [0.245, 0.245, 0.085], [-112, 158, -135]),
                front_arm=_chain(shoulder, [0.17, 0.15], [-58, 55]),
                back_arm=_chain(shoulder, [0.17, 0.15], [-140, -100]))


def runner(c, x, y, s, near, far, gap=0.03):
    """Dibuja el corredor. x = vertical de la cadera, y = línea del suelo, s = estatura en puntos.

    El pie más bajo queda a `gap`·s del suelo (fase de vuelo). Las extremidades del lado lejano
    van en un tono más claro para dar profundidad."""
    k = runner_pose()
    low = min(p[1] for key in ("front_leg", "back_leg") for p in k[key][1:]) - 0.02
    y = y + (gap - low) * s

    def T(p):
        return (x + p[0] * s, y + p[1] * s)

    def limb(pts, widths, col):
        for (a, b), (w0, w1) in zip(zip(pts, pts[1:]), widths):
            _seg(c, T(a), T(b), w0 * s, w1 * s, col)

    leg_w = [(0.085, 0.06), (0.058, 0.04), (0.04, 0.03)]
    arm_w = [(0.052, 0.04), (0.04, 0.032)]
    c.saveState()
    # lado lejano: pierna trasera y brazo delantero
    limb(k["back_leg"], leg_w, far)
    limb(k["front_arm"], arm_w, far)
    # tronco (cadera -> hombro), cuello y cabeza
    _seg(c, T(k["hip"]), T(k["shoulder"]), 0.095 * s, 0.115 * s, near)
    _seg(c, T(k["shoulder"]), T(k["neck"]), 0.06 * s, 0.05 * s, near)
    hx, hy = T(k["head"])
    c.setFillColor(near); c.circle(hx, hy, 0.062 * s, stroke=0, fill=1)
    # lado cercano: pierna delantera y brazo trasero
    limb(k["front_leg"], leg_w, near)
    limb(k["back_arm"], arm_w, near)
    c.restoreState()
    return k


# ------------------------------------------------------------------ palma de moriche (silueta)
def palm(c, x, y, h, col, lean=6, seed=1):
    """Palma de moriche en silueta: tronco recto y fino con copa en abanico. (x, y) = base."""
    import random
    rng = random.Random(seed)
    top = (x + h * math.sin(math.radians(lean)) * 0.4, y + h)
    _seg(c, (x, y), top, h * 0.045, h * 0.03, col)
    c.setFillColor(col)
    for k in range(13):
        a = math.radians(-15 + k * (210 / 12) + rng.uniform(-6, 6))
        L = h * rng.uniform(0.28, 0.4)
        droop = 0.35 if abs(math.cos(a)) > 0.6 else 0.1
        tip = (top[0] + L * math.cos(a), top[1] + L * math.sin(a) - L * droop)
        mid = (top[0] + L * 0.55 * math.cos(a), top[1] + L * 0.55 * math.sin(a))
        nx, ny = -math.sin(a), math.cos(a)
        w = h * 0.035
        p = c.beginPath()
        p.moveTo(*top)
        p.curveTo(mid[0] + nx * w, mid[1] + ny * w, tip[0], tip[1], tip[0], tip[1])
        p.curveTo(tip[0], tip[1], mid[0] - nx * w, mid[1] - ny * w, top[0], top[1])
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    c.circle(top[0], top[1], h * 0.04, stroke=0, fill=1)


# ------------------------------------------------------------------ crédito de autor en portada
def author_credit(c, x_right, y, autor, text_fn, label_col, name_col, sub_col):
    """Crédito alineado a la derecha: etiqueta, nombre (y C.I.) e institución abreviada.
    `autor` es el JSON de src/authors ({"lineas": [...]}); si es None no dibuja nada."""
    if not autor or not autor.get("lineas"):
        return
    text_fn(c, "REVISTA REALIZADA POR", x_right, y, "Sans-B", 6, label_col, "r", 1.6)
    text_fn(c, autor["lineas"][0], x_right, y - 4.6 * mm, "Sans-SB", 8.6, name_col, "r", 0.2)
    text_fn(c, "UCAB Guayana · Comunicación Social", x_right, y - 8.6 * mm, "Serif-I", 8, sub_col, "r", 0)
