"""Exportación a IDML (Adobe InDesign) de las mismas páginas que se generan en PDF.

Cómo funciona
-------------
El builder dibuja con reportlab como siempre. Si la variable de entorno IDML_OUT está definida,
el lienzo principal se sustituye por `RecCanvas`, que además de generar el PDF:

* registra cada texto de una línea (`mag_lib.text`), cada párrafo (`Paragraph.drawOn`), cada
  flujo de texto en columnas (`mag_lib.fill`, con sus marcos y obstáculos) y cada foto (`imgslots`);
* al cerrar cada página interpreta el flujo de dibujo PDF de esa página (operadores q/Q, cm, m/l/c,
  re, W, f/S/B, colores, transparencias) para obtener los vectores con su orden de apilamiento,
  recortes y opacidad;
* al guardar escribe un paquete IDML: un pliego por página, retícula en la página maestra,
  párrafos con estilos de párrafo, artículos encadenados entre columnas y páginas, fotos vinculadas
  (carpeta Links/) con ceñido de texto, y los vectores como polígonos/rectángulos editables.

Lo que se ve en InDesign se compone con su propio motor de texto: los cortes de línea pueden variar
ligeramente respecto del PDF. Se usa el compositor de línea única y sin separación silábica para
acercarse al resultado de reportlab.
"""
import os, re, io, math, shutil, zipfile, copy
from xml.sax.saxutils import escape, quoteattr

from reportlab.pdfgen import canvas as _rl_canvas
from reportlab.lib.units import mm
from reportlab.platypus.paraparser import ParaParser

ENABLED = bool(os.environ.get("IDML_OUT"))
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "idml_template")

FONTS = {  # nombre reportlab -> (familia, estilo, PostScript)
    "Sans": ("Inter", "Regular", "Inter-Regular"), "Sans-M": ("Inter", "Medium", "Inter-Medium"),
    "Sans-SB": ("Inter", "SemiBold", "Inter-SemiBold"), "Sans-B": ("Inter", "Bold", "Inter-Bold"),
    "Sans-I": ("Inter", "Italic", "Inter-Italic"), "Sans-BI": ("Inter", "Bold", "Inter-Bold"),
    "Disp": ("Inter Display", "Black", "InterDisplay-Black"),
    "Disp-I": ("Inter Display", "Black Italic", "InterDisplay-BlackItalic"),
    "Disp-X": ("Inter Display", "ExtraBold", "InterDisplay-ExtraBold"),
    "Serif": ("Lora", "Regular", "Lora-Regular"), "Serif-M": ("Lora", "Medium", "Lora-Medium"),
    "Serif-SB": ("Lora", "SemiBold", "Lora-SemiBold"), "Serif-B": ("Lora", "Bold", "Lora-Bold"),
    "Serif-I": ("Lora", "Italic", "Lora-Italic"), "Serif-BI": ("Lora", "BoldItalic", "Lora-BoldItalic"),
}

STYLE_NAMES = {"body": "Cuerpo", "bodyl": "Cuerpo (propio)", "lead": "Entradilla", "cap": "Pie de foto",
               "byl": "Firma", "d": "Sumario", "q": "Cita", "b2": "Cuerpo", "l2": "Entradilla",
               "bo": "Cuerpo (propio)", "c2": "Pie de foto", "d2": "Sumario",
               "b3": "Cuerpo", "b3o": "Cuerpo (propio)", "l3": "Entradilla", "c3": "Pie de foto",
               "d3": "Sumario", "by3": "Firma", "e0": "Entradilla editorial", "eb": "Cuerpo editorial"}


# ======================================================================================
#  Registro durante el dibujo
# ======================================================================================
class _State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pages = []           # cada página: dict(code=[...], extg={}, hooks=[...])
        self.hooks = []           # ganchos de la página en curso
        self.flows = {}           # id(lista story) -> dict(paras=[...], frames=[...], story=list)
        self.flow_order = []
        self.suppress = 0         # >0 mientras fill() dibuja: no registrar párrafos sueltos
        self.cfg = dict(mag="revista", cols=1, gutter=5 * mm, margins=(15 * mm,) * 4, palette={},
                        baseline=None)


REC = _State()


def configure(**kw):
    REC.cfg.update(kw)


def is_main(c):
    return getattr(c, "_idml_main", False)


def _ctm(c):
    return tuple(getattr(c, "_currentMatrix", (1, 0, 0, 1, 0, 0)))


def hook_text(c, s, x, y, font, size, color, align, cs):
    if not is_main(c) or REC.suppress:
        return
    REC.hooks.append(dict(kind="line", idx=len(c._code), ctm=_ctm(c), s=s, x=x, y=y, font=font,
                          size=size, color=_rgb(color), align=align, cs=cs))


def hook_para(p, c, x, y):
    if not is_main(c) or REC.suppress:
        return
    REC.hooks.append(dict(kind="para", idx=len(c._code), ctm=_ctm(c), para=p, x=x, y=y,
                          w=p.width, h=p.height))


def hook_flow(c, story, frames):
    """Se llama al empezar fill(): registra los marcos (y el artículo la primera vez)."""
    if not is_main(c):
        return
    key = id(story)
    if key not in REC.flows:
        REC.flows[key] = dict(paras=list(story), story=story, frames=[])
        REC.flow_order.append(key)
    mf = getattr(frames, "mf", None)
    REC.hooks.append(dict(kind="flow", idx=len(c._code), ctm=_ctm(c), key=key, mf=mf,
                          frames=[(f._x1, f._y1, f._width, f._height) for f in frames]))


def hook_image(c, path, x, y, w, h, dx, dy, dw, dh, name):
    if not is_main(c):
        return
    REC.hooks.append(dict(kind="image", idx=len(c._code), ctm=_ctm(c), path=path, rect=(x, y, w, h),
                          draw=(dx, dy, dw, dh), name=name))


class RecCanvas(_rl_canvas.Canvas):
    def __init__(self, filename, *a, **k):
        super().__init__(filename, *a, **k)
        self._idml_main = ENABLED and isinstance(filename, str)
        if self._idml_main:
            REC.reset()

    def showPage(self):
        if self._idml_main:
            inv = {}
            eg = getattr(self, "_extgstate", None)
            if eg is not None:
                for (a, v), name in eg._c.items():
                    inv[name] = (a, v)
            REC.pages.append(dict(code=list(self._code), extg=inv, hooks=REC.hooks))
            REC.hooks = []
        super().showPage()

    def save(self):
        main = self._idml_main
        super().save()
        if main:
            Writer(REC).write(os.environ["IDML_OUT"])


class _CanvasModule:
    Canvas = RecCanvas if ENABLED else _rl_canvas.Canvas


canvas_module = _CanvasModule


def _rgb(col):
    if col is None:
        return None
    if hasattr(col, "rgb"):
        r, g, b = col.rgb()
        return (round(r * 255), round(g * 255), round(b * 255))
    return tuple(col)


# ======================================================================================
#  Intérprete del flujo de dibujo PDF (solo gráficos; el texto y las imágenes van por ganchos)
# ======================================================================================
_TOK = re.compile(rb"""\s*(?:
      (?P<str>\()                       |
      (?P<arr>\[) | (?P<arrend>\])      |
      (?P<name>/[^\s/\[\]()<>]+)        |
      (?P<num>[-+]?(?:\d+\.?\d*|\.\d+)) |
      (?P<op>[A-Za-z_'"*]+)              |
      (?P<other><<|>>|<[0-9A-Fa-f\s]*>)
    )""", re.X)


def _tokens(chunk):
    b = chunk.encode("latin-1", "replace") if isinstance(chunk, str) else chunk
    i, n = 0, len(b)
    while i < n:
        m = _TOK.match(b, i)
        if not m:
            i += 1
            continue
        i = m.end()
        if m.group("str"):
            depth, j = 1, i
            while j < n and depth:
                ch = b[j:j + 1]
                if ch == b"\\":
                    j += 2
                    continue
                if ch == b"(":
                    depth += 1
                elif ch == b")":
                    depth -= 1
                j += 1
            i = j
            yield ("str", None)
        elif m.group("arr"):
            yield ("arr", None)
        elif m.group("arrend"):
            yield ("arrend", None)
        elif m.group("name"):
            yield ("name", m.group("name")[1:].decode())
        elif m.group("num"):
            yield ("num", float(m.group("num")))
        elif m.group("op"):
            yield ("op", m.group("op").decode())


def _mul(m, n):
    """m aplicado después de n (PDF: nueva CTM = m x CTM)."""
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F)


def _ap(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


class GState:
    def __init__(self):
        self.ctm = (1, 0, 0, 1, 0, 0)
        self.fill = (0, 0, 0)
        self.stroke = (0, 0, 0)
        self.lw = 1.0
        self.cap = 0
        self.join = 0
        self.dash = ()
        self.fa = 1.0
        self.sa = 1.0
        self.clip = None
        self.clip_id = 0


def _flatten(sub, steps=14):
    """Puntos (x, y) de un subtrazado con segmentos rectos y Bézier."""
    pts = [sub["start"]]
    cur = sub["start"]
    for seg in sub["segs"]:
        if seg[0] == "l":
            cur = seg[1]
            pts.append(cur)
        else:
            _, c1, c2, p = seg
            for k in range(1, steps + 1):
                t = k / steps
                u = 1 - t
                pts.append((u ** 3 * cur[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p[0],
                            u ** 3 * cur[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p[1]))
            cur = p
    return pts


def _interp2(code):
    """Interpreta los operadores gráficos de una página. Devuelve una lista de trazados pintados
    con su posición en el flujo (idx), relleno/trazo, opacidad y máscara de recorte.
    La opacidad llega como los operadores sintéticos FA_/SA_ (ver _interp2_with_alpha)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    out = []
    gs = GState()
    stack = []
    path = []
    cur = {"sub": None}
    pending_clip = [False]
    in_text = [False]
    clip_seq = [0]

    def newsub(p):
        cur["sub"] = dict(start=p, segs=[], closed=False)
        path.append(cur["sub"])

    def path_geom():
        polys = []
        for s in path:
            pts = _flatten(s)
            if len(pts) >= 3:
                pg = Polygon(pts)
                if not pg.is_valid:
                    pg = pg.buffer(0)
                if not pg.is_empty:
                    polys.append(pg)
        return unary_union(polys) if polys else None

    for ci, chunk in enumerate(code):
        args = []
        for kind, val in _tokens(chunk):
            if kind == "num":
                args.append(val)
                continue
            if kind != "op":
                continue
            op = val
            sub = cur["sub"]
            if op == "FA_":
                gs.fa = args[-9]
            elif op == "SA_":
                gs.sa = args[-9]
            elif op == "BT":
                in_text[0] = True
            elif op == "ET":
                in_text[0] = False
            elif op in ("rg", "RG") and len(args) >= 3:
                col = tuple(max(0, min(255, round(v * 255))) for v in args[-3:])
                if op == "rg":
                    gs.fill = col
                else:
                    gs.stroke = col
            elif op in ("g", "G") and args:
                v = max(0, min(255, round(args[-1] * 255)))
                if op == "g":
                    gs.fill = (v, v, v)
                else:
                    gs.stroke = (v, v, v)
            elif op in ("k", "K") and len(args) >= 4:
                cc, m_, yy, kk = args[-4:]
                col = tuple(round(255 * (1 - min(1, v + kk))) for v in (cc, m_, yy))
                if op == "k":
                    gs.fill = col
                else:
                    gs.stroke = col
            elif in_text[0]:
                pass
            elif op == "q":
                st = copy.copy(gs)
                stack.append(st)
            elif op == "Q":
                if stack:
                    gs = stack.pop()
            elif op == "cm" and len(args) >= 6:
                gs.ctm = _mul(tuple(args[-6:]), gs.ctm)
            elif op == "w" and args:
                gs.lw = args[-1]
            elif op == "J" and args:
                gs.cap = int(args[-1])
            elif op == "j" and args:
                gs.join = int(args[-1])
            elif op == "d":
                gs.dash = tuple(args[:-1])
            elif op == "m" and len(args) >= 2:
                newsub(_ap(gs.ctm, *args[-2:]))
            elif op == "l" and len(args) >= 2:
                if sub is None:
                    newsub(_ap(gs.ctm, *args[-2:]))
                else:
                    sub["segs"].append(("l", _ap(gs.ctm, *args[-2:])))
            elif op in ("c", "v", "y") and sub is not None:
                last = sub["segs"][-1][-1] if sub["segs"] else sub["start"]
                if op == "c" and len(args) >= 6:
                    c1, c2, p = _ap(gs.ctm, *args[-6:-4]), _ap(gs.ctm, *args[-4:-2]), _ap(gs.ctm, *args[-2:])
                elif op == "v" and len(args) >= 4:
                    c1, c2, p = last, _ap(gs.ctm, *args[-4:-2]), _ap(gs.ctm, *args[-2:])
                elif op == "y" and len(args) >= 4:
                    c1, p = _ap(gs.ctm, *args[-4:-2]), _ap(gs.ctm, *args[-2:])
                    c2 = p
                else:
                    args = []
                    continue
                sub["segs"].append(("c", c1, c2, p))
            elif op == "h" and sub is not None:
                sub["closed"] = True
            elif op == "re" and len(args) >= 4:
                x, y, w, h = args[-4:]
                newsub(_ap(gs.ctm, x, y))
                s2 = cur["sub"]
                s2["segs"] += [("l", _ap(gs.ctm, x + w, y)), ("l", _ap(gs.ctm, x + w, y + h)), ("l", _ap(gs.ctm, x, y + h))]
                s2["closed"] = True
                s2["rect"] = True
            elif op in ("W", "W*"):
                pending_clip[0] = True
            elif op in ("f", "F", "f*", "S", "s", "B", "B*", "b", "b*", "n"):
                if op in ("s", "b", "b*") and sub is not None:
                    sub["closed"] = True
                if pending_clip[0]:
                    g = path_geom()
                    if g is not None:
                        gs.clip = g if gs.clip is None else gs.clip.intersection(g)
                        clip_seq[0] += 1
                        gs.clip_id = clip_seq[0]
                    pending_clip[0] = False
                if op != "n" and path:
                    dofill = op in ("f", "F", "f*", "B", "B*", "b", "b*")
                    dostroke = op in ("S", "s", "B", "B*", "b", "b*")
                    sc = math.sqrt(abs(gs.ctm[0] * gs.ctm[3] - gs.ctm[1] * gs.ctm[2]))
                    out.append(dict(idx=ci, subs=list(path), fill=gs.fill if dofill else None,
                                    stroke=gs.stroke if dostroke else None, lw=gs.lw * sc, cap=gs.cap,
                                    join=gs.join, dash=tuple(v * sc for v in gs.dash), fa=gs.fa, sa=gs.sa,
                                    clip=gs.clip, clip_id=gs.clip_id if gs.clip is not None else 0))
                path.clear()
                cur["sub"] = None
            args = []
    return out


# ======================================================================================
#  Escritura del paquete IDML
# ======================================================================================
def _f(v):
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Writer:
    def __init__(self, rec):
        self.rec = rec
        self.cfg = rec.cfg
        from reportlab.lib.pagesizes import A4
        self.W, self.H = A4
        self.OX, self.OY = -self.W / 2, -self.H / 2
        self.n = 0
        self.colors = {}          # rgb -> Self
        self.pstyles = {}         # clave -> (Self, attrs)
        self.stories = []         # (Self, xml)
        self.links = {}           # ruta origen -> nombre en Links/
        self.layer = "uLayer"
        self.warnings = []

    def uid(self, p="u"):
        self.n += 1
        return "%s%x" % (p, self.n + 0x200)

    # ---------- coordenadas ----------
    def S(self, x, y):
        """Página (pt, y hacia arriba) -> pliego (y hacia abajo, origen en el centro de la página)."""
        return (x + self.OX, (self.H - y) + self.OY)

    # ---------- colores ----------
    def color(self, rgb):
        if rgb is None:
            return "Swatch/None"
        rgb = tuple(int(v) for v in rgb)
        if rgb not in self.colors:
            hx = "#%02X%02X%02X" % rgb
            name = self.cfg["palette"].get(hx)
            if name is None and rgb == (255, 255, 255):
                name = "Blanco"
            self.colors[rgb] = ("Color/" + (name if name else "u%02x%02x%02x" % rgb), name)
        return self.colors[rgb][0]

    # ---------- estilos de párrafo ----------
    def pstyle(self, name, font, size, leading, color, align="LeftAlign", sb=0, sa=0, tracking=0):
        fam, sty, _ = FONTS.get(font, FONTS["Sans"])
        key = (name, fam, sty, round(size, 2), round(leading, 2), color, align, round(sb, 2), round(sa, 2), round(tracking))
        if key not in self.pstyles:
            base = name
            k = 2
            used = {v[1]["Name"] for v in self.pstyles.values()}
            while name in used:
                name = "%s %d" % (base, k)
                k += 1
            attrs = dict(Name=name, FontStyle=sty, PointSize=_f(size), Leading=_f(leading),
                         FillColor=self.color(color), Justification=align, SpaceBefore=_f(sb), SpaceAfter=_f(sa),
                         Tracking=str(round(tracking)), Hyphenation="false", Composer="HL Single",
                         KerningMethod="$ID/Metrics", _font=fam)
            self.pstyles[key] = ("ParagraphStyle/" + _selfname(name), attrs)
        return self.pstyles[key]

    # ---------- texto ----------
    def runs_of(self, p):
        """Párrafo reportlab -> lista de tramos (texto, fuente, tamaño, color)."""
        text = getattr(p, "text", None)
        st = p.style
        if isinstance(text, str):
            _, frags, _ = ParaParser().parse(text, st)
        else:
            frags = []
        runs = []
        for fr in frags or []:
            t = fr.text
            if getattr(fr, "lineBreak", False):
                t = " "
            if not t:
                continue
            runs.append((t, fr.fontName, fr.fontSize, _rgb(fr.textColor)))
        return runs

    def para_style_for(self, p):
        st = p.style
        al = {0: "LeftAlign", 1: "CenterAlign", 2: "RightAlign", 4: "LeftJustified"}.get(st.alignment, "LeftAlign")
        name = STYLE_NAMES.get(st.name, "Párrafo " + st.name)
        return self.pstyle(name, st.fontName, st.fontSize, st.leading, _rgb(st.textColor), al,
                           getattr(st, "spaceBefore", 0), getattr(st, "spaceAfter", 0))

    def story_xml(self, sid, paras):
        """paras: lista de (estilo_self, attrs_estilo, runs)."""
        out = ['<Story Self="%s" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">' % sid,
               '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection"/>',
               '<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false"/>']
        for i, (pself, pattrs, runs) in enumerate(paras):
            out.append('<ParagraphStyleRange AppliedParagraphStyle=%s>' % quoteattr(pself))
            last = len(runs) - 1
            if not runs:
                runs = [("", None, None, None)]
                last = 0
            for j, (t, font, size, col) in enumerate(runs):
                at = ['AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"']
                props = ""
                if font:
                    fam, sty, _ = FONTS.get(font, FONTS["Sans"])
                    if fam != pattrs["_font"]:
                        props = '<Properties><AppliedFont type="string">%s</AppliedFont></Properties>' % escape(fam)
                    if sty != pattrs["FontStyle"] or props:
                        at.append('FontStyle=%s' % quoteattr(sty))
                    if _f(size) != pattrs["PointSize"]:
                        at.append('PointSize="%s"' % _f(size))
                    cs = self.color(col)
                    if cs != pattrs["FillColor"]:
                        at.append('FillColor=%s' % quoteattr(cs))
                out.append('<CharacterStyleRange %s>%s' % (" ".join(at), props))
                parts = t.split(" ")
                for k, part in enumerate(parts):
                    if k:
                        out.append('<Content> </Content>')
                    if part:
                        out.append('<Content>%s</Content>' % escape(part))
                if j == last and i < len(paras) - 1:
                    out.append('<Br/>')
                out.append('</CharacterStyleRange>')
            out.append('</ParagraphStyleRange>')
        out.append('</Story>')
        return "\n".join(out)

    def add_story(self, paras):
        sid = self.uid("st")
        self.stories.append((sid, self.story_xml(sid, paras)))
        return sid

    def text_frame(self, sid, x0, y0, x1, y1, ctm=(1, 0, 0, 1, 0, 0), prev="n", nxt="n", first_bl=10,
                   ignore_wrap=True, fid=None, name="$ID/"):
        """Marco de texto con esquinas (x0,y0)-(x1,y1) en el espacio de usuario PDF (y hacia arriba)."""
        a, b, c, d, e, f = ctm
        it = (a, -b, -c, d, e + self.OX, (self.H - f) + self.OY)
        pts = [(x0, -y1), (x0, -y0), (x1, -y0), (x1, -y1)]
        fid = fid or self.uid("tf")
        pp = "".join('<PathPointType Anchor="%s %s" LeftDirection="%s %s" RightDirection="%s %s"/>' % ((_f(px), _f(py)) * 3)
                     for px, py in pts)
        return ('<TextFrame Self="%s" ParentStory="%s" PreviousTextFrame="%s" NextTextFrame="%s" ContentType="TextType" '
                'ItemLayer="%s" Locked="false" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" Visible="true" Name=%s '
                'ItemTransform="%s">'
                '<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>%s</PathPointArray>'
                '</GeometryPathType></PathGeometry></Properties>'
                '<TextFramePreference TextColumnCount="1" FirstBaselineOffset="FixedHeight" MinimumFirstBaselineOffset="%s" '
                'VerticalJustification="TopAlign" IgnoreWrap="%s" AutoSizingType="Off">'
                '<Properties><InsetSpacing type="list"><ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
                '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem></InsetSpacing></Properties>'
                '</TextFramePreference></TextFrame>') % (
            fid, sid, prev, nxt, self.layer, quoteattr(name), " ".join(_f(v) for v in it), pp, _f(first_bl),
            "true" if ignore_wrap else "false")

    # ---------- gráficos ----------
    def path_points(self, sub):
        pts = []
        cur = sub["start"]
        pts.append([cur, cur, cur])
        for seg in sub["segs"]:
            if seg[0] == "l":
                pts.append([seg[1], seg[1], seg[1]])
            else:
                _, c1, c2, p = seg
                pts[-1][2] = c1
                pts.append([p, c2, p])
        if sub.get("closed") and len(pts) > 1:
            a, b = pts[0][0], pts[-1][0]
            if abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01:
                pts[0][1] = pts[-1][1]
                pts.pop()
        return pts

    def geom_xml(self, subs_pts, closed_flags):
        out = ["<Properties><PathGeometry>"]
        for pts, closed in zip(subs_pts, closed_flags):
            out.append('<GeometryPathType PathOpen="%s"><PathPointArray>' % ("false" if closed else "true"))
            for anc, left, right in pts:
                A, L, R = self.S(*anc), self.S(*left), self.S(*right)
                out.append('<PathPointType Anchor="%s %s" LeftDirection="%s %s" RightDirection="%s %s"/>' % (
                    _f(A[0]), _f(A[1]), _f(L[0]), _f(L[1]), _f(R[0]), _f(R[1])))
            out.append("</PathPointArray></GeometryPathType>")
        out.append("</PathGeometry></Properties>")
        return "".join(out)

    def shape_xml(self, tag, subs_pts, closed, fill, stroke, lw=0, cap=0, join=0, dash=(), opacity=1.0,
                  name="$ID/", wrap=None, fid=None):
        fid = fid or self.uid("g")
        caps = ["ButtEndCap", "RoundEndCap", "ProjectingEndCap"]
        joins = ["MiterEndJoin", "RoundEndJoin", "BevelEndJoin"]
        at = ['Self="%s"' % fid, 'ContentType="Unassigned"', 'ItemLayer="%s"' % self.layer, 'Locked="false"',
              'FillColor="%s"' % self.color(fill), 'StrokeColor="%s"' % self.color(stroke),
              'StrokeWeight="%s"' % (_f(lw) if stroke is not None else "0"),
              'EndCap="%s"' % caps[cap % 3], 'EndJoin="%s"' % joins[join % 3], 'StrokeAlignment="CenterAlignment"',
              'AppliedObjectStyle="ObjectStyle/$ID/[None]"', 'Visible="true"', 'Name=%s' % quoteattr(name),
              'ItemTransform="1 0 0 1 0 0"']
        if stroke is not None and dash:
            at.append('StrokeType="StrokeStyle/$ID/Dashed"')
            at.append('StrokeDashAndGap="%s"' % " ".join(_f(v) for v in (list(dash) * 2)[:max(2, len(dash))]))
        body = self.geom_xml(subs_pts, closed)
        if opacity < 0.999:
            body += '<TransparencySetting><BlendingSetting Opacity="%s"/></TransparencySetting>' % _f(opacity * 100)
        if wrap:
            body += self.wrap_xml(*wrap)
        return "<%s %s>%s</%s>" % (tag, " ".join(at), body, tag)

    def wrap_xml(self, top, left, bottom, right):
        return ('<TextWrapPreference Inverse="false" ApplyToMasterPageOnly="false" TextWrapSide="BothSides" '
                'TextWrapMode="JumpObjectTextWrap"><Properties><TextWrapOffset Top="%s" Left="%s" Bottom="%s" Right="%s"/>'
                '</Properties></TextWrapPreference>') % (_f(top), _f(left), _f(bottom), _f(right))

    def graphic_items(self, g):
        """Un gráfico interpretado -> lista de (xml, bbox) ya recortados por su máscara."""
        from shapely.geometry import Polygon, LineString, box as sbox
        from shapely.geometry.polygon import orient
        subs = g["subs"]
        allpts = [p for s in subs for p in _flatten(s, 4)]
        if not allpts:
            return []
        xs = [p[0] for p in allpts]
        ys = [p[1] for p in allpts]
        bb = (min(xs), min(ys), max(xs), max(ys))
        if bb[2] < -5 or bb[0] > self.W + 5 or bb[3] < -5 or bb[1] > self.H + 5:
            return []
        fill, stroke = g["fill"], g["stroke"]
        if fill is not None and g["fa"] <= 0.003:
            fill = None
        if stroke is not None and (g["sa"] <= 0.003 or g["lw"] <= 0):
            stroke = None
        if fill is None and stroke is None:
            return []
        clip = g["clip"]
        if clip is not None and clip.is_empty:
            return []
        if clip is not None and clip.buffer(0.5).contains(sbox(*bb)):
            clip = None
        page = sbox(0, 0, self.W, self.H)
        if clip is None and not page.contains(sbox(*bb)) and fill is not None and stroke is None:
            # recorta lo que sale de la página (las ilustraciones a sangre se dibujan más grandes)
            if not page.buffer(0.5).contains(sbox(*bb)):
                clip = page
        items = []
        if clip is None:
            pts = [self.path_points(s) for s in subs]
            closed = [bool(s.get("closed")) or fill is not None for s in subs]
            is_rect = len(subs) == 1 and subs[0].get("rect") and stroke is None
            tag = "Rectangle" if is_rect else ("Polygon" if any(closed) else "GraphicLine")
            if fill is None and not any(closed):
                tag = "GraphicLine"
            op = g["fa"] if fill is not None else g["sa"]
            items.append((self.shape_xml(tag, pts, closed, fill, stroke, g["lw"], g["cap"], g["join"], g["dash"], op), bb))
            return items
        # con máscara: geometría aplanada e intersección
        if fill is not None:
            polys = []
            for s in subs:
                p = _flatten(s)
                if len(p) >= 3:
                    pg = Polygon(p)
                    if not pg.is_valid:
                        pg = pg.buffer(0)
                    polys.append(pg)
            if polys:
                from shapely.ops import unary_union
                geo = unary_union(polys).intersection(clip)
                for poly in getattr(geo, "geoms", [geo]):
                    if poly.geom_type != "Polygon" or poly.is_empty or poly.area < 0.05:
                        continue
                    poly = orient(poly.simplify(0.05), 1.0)
                    rings = [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]
                    pts = [[[q, q, q] for q in ring] for ring in rings if len(ring) >= 3]
                    if pts:
                        b = poly.bounds
                        items.append((self.shape_xml("Polygon", pts, [True] * len(pts), fill, None, 0, 0, 0, (), g["fa"]), b))
        if stroke is not None:
            for s in subs:
                p = _flatten(s)
                if s.get("closed"):
                    p = p + [p[0]]
                if len(p) < 2:
                    continue
                geo = LineString(p).intersection(clip)
                for ln in getattr(geo, "geoms", [geo]):
                    if ln.geom_type != "LineString" or ln.is_empty or ln.length < 0.2:
                        continue
                    q = list(ln.simplify(0.03).coords)
                    pts = [[[v, v, v] for v in q]]
                    items.append((self.shape_xml("GraphicLine", pts, [False], None, stroke, g["lw"], g["cap"], g["join"], g["dash"], g["sa"]), ln.bounds))
        return items

    # ---------- imágenes ----------
    def image_xml(self, h, wrap=None):
        from PIL import Image
        x, y, w, hh = h["rect"]
        dx, dy, dw, dh = h["draw"]
        ctm = h["ctm"]
        src = h["path"]
        if src not in self.links:
            base = "%s_%s" % (self.cfg["mag"], h["name"])
            self.links[src] = base + os.path.splitext(src)[1].lower()
        fname = self.links[src]
        iw, ih = Image.open(src).size
        # esquinas del marco (en página) y transformación de la imagen
        c0 = _ap(ctm, x, y)
        c1 = _ap(ctm, x + w, y + hh)
        fx0, fy0, fx1, fy1 = min(c0[0], c1[0]), min(c0[1], c1[1]), max(c0[0], c1[0]), max(c0[1], c1[1])
        tl = _ap(ctm, dx, dy + dh)
        s = (dw / iw) * math.sqrt(abs(ctm[0] * ctm[3] - ctm[1] * ctm[2]))
        TX, TY = self.S(*tl)
        rid, iid, lid = self.uid("im"), self.uid("ii"), self.uid("lk")
        pts = [(fx0, fy1), (fx0, fy0), (fx1, fy0), (fx1, fy1)]
        pp = "".join('<PathPointType Anchor="%s %s" LeftDirection="%s %s" RightDirection="%s %s"/>' % (
            (_f(self.S(*p)[0]), _f(self.S(*p)[1])) * 3) for p in pts)
        ext = os.path.splitext(fname)[1].lower()
        fmt = "$ID/JPEG" if ext in (".jpg", ".jpeg") else "$ID/Portable Network Graphics (PNG)"
        wrapx = self.wrap_xml(*wrap) if wrap else ""
        return ('<Rectangle Self="%s" ContentType="GraphicType" StoryTitle="$ID/" ItemLayer="%s" Locked="false" '
                'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
                'AppliedObjectStyle="ObjectStyle/$ID/[None]" Visible="true" Name=%s ItemTransform="1 0 0 1 0 0">'
                '<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>%s</PathPointArray>'
                '</GeometryPathType></PathGeometry></Properties>%s'
                '<FrameFittingOption FittingOnEmptyFrame="FillProportionally" FittingAlignment="CenterAnchor"/>'
                '<Image Self="%s" Space="$ID/#Links_RGB" ActualPpi="72 72" EffectivePpi="%s %s" '
                'ImageRenderingIntent="UseColorSettings" LocalDisplaySetting="Default" ImageTypeName="%s" '
                'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="%s 0 0 %s %s %s" Visible="true" Name="$ID/">'
                '<Properties><Profile type="string">$ID/None</Profile>'
                '<GraphicBounds Left="0" Top="0" Right="%d" Bottom="%d"/></Properties>'
                '<Link Self="%s" AssetURL="$ID/" AssetID="$ID/" LinkResourceURI=%s LinkResourceFormat="%s" '
                'StoredState="Normal" LinkClassID="35906" LinkClientID="257" LinkResourceModified="false" '
                'LinkObjectModified="false" ShowInUI="true" CanEmbed="true" CanUnembed="true" CanPackage="true" '
                'ImportPolicy="NoAutoImport" ExportPolicy="NoAutoExport"/>'
                '</Image></Rectangle>') % (
            rid, self.layer, quoteattr("Foto · " + h["name"]), pp, wrapx, iid, round(72 / s), round(72 / s),
            fmt.replace("PNG)", "PNG)"), _f(s), _f(s), _f(TX), _f(TY), iw, ih, lid,
            quoteattr("file:Links/" + fname), fmt)

    # ---------- páginas ----------
    def page_items(self, pi, page, flowframes):
        """XML de los elementos de una página en orden de apilamiento."""
        hooks = page["hooks"]
        graphics = _interp2_with_alpha(page["code"], page["extg"])
        # obstáculos de ceñido de esta página: (bbox obstáculo, flujo)
        obstacles = []
        for h in hooks:
            if h["kind"] == "flow" and h["mf"]:
                for ob in h["mf"][5]:
                    obstacles.append(ob)
        PAD = 4 * mm
        hosts = {}
        # elementos ordenados por posición en el flujo de dibujo
        entries = [(g["idx"], 1, g) for g in graphics] + [(h["idx"], 0, h) for h in hooks]
        entries.sort(key=lambda t: (t[0], t[1]))
        # anfitriones del ceñido: imagen o rectángulo contenido en el obstáculo
        def find_host(ob):
            ox0, oy0, ox1, oy1 = ob
            best = None
            for _, kind, it in entries:
                if kind == 0 and it["kind"] == "image":
                    x, y, w, h = it["rect"]
                    bb = (x, y, x + w, y + h)
                elif kind == 1 and it["fill"] is not None and len(it["subs"]) == 1 and it["subs"][0].get("rect") and it["clip"] is None:
                    ps = [it["subs"][0]["start"]] + [s[1] for s in it["subs"][0]["segs"]]
                    bb = (min(p[0] for p in ps), min(p[1] for p in ps), max(p[0] for p in ps), max(p[1] for p in ps))
                else:
                    continue
                if bb[0] >= ox0 - 1 and bb[1] >= oy0 - 1 and bb[2] <= ox1 + 1 and bb[3] <= oy1 + 1:
                    area = (bb[2] - bb[0]) * (bb[3] - bb[1])
                    if best is None or area > best[0]:
                        best = (area, id(it), bb)
            return best
        for ob in obstacles:
            hb = find_host(ob)
            ox0, oy0, ox1, oy1 = ob
            if hb:
                _, key, bb = hb
                wrap = (PAD + (oy1 - bb[3]), PAD + (bb[0] - ox0), PAD + (bb[1] - oy0), PAD + (ox1 - bb[2]))
                hosts[key] = wrap
            else:
                hosts[("inv", ob)] = (PAD, PAD, PAD, PAD)
        out = []
        group = []      # (clip_id, [xml])
        def flush():
            if not group:
                return
            cid, xs = group[0][0], [x for _, x in group]
            if len(xs) >= 2:
                out.append('<Group Self="%s" ItemLayer="%s" Locked="false" Visible="true" Name="$ID/" '
                           'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">%s</Group>' % (
                               self.uid("gr"), self.layer, "".join(xs)))
            else:
                out.extend(xs)
            group.clear()
        for _, kind, it in entries:
            if kind == 1:
                wrap = hosts.get(id(it))
                xmls = self.graphic_items(it)
                if wrap and xmls:
                    # el ceñido va en el primer objeto (rectángulo de fondo del recuadro)
                    x0, b0 = xmls[0]
                    x0 = x0.replace("</Rectangle>", self.wrap_xml(*wrap) + "</Rectangle>", 1)
                    xmls[0] = (x0, b0)
                cid = it["clip_id"]
                for x, _ in xmls:
                    if cid and group and group[0][0] != cid:
                        flush()
                    if cid:
                        group.append((cid, x))
                    else:
                        flush()
                        out.append(x)
                continue
            flush()
            k = it["kind"]
            if k == "image":
                out.append(self.image_xml(it, hosts.get(id(it))))
            elif k == "line":
                out.append(self.line_frame(it))
            elif k == "para":
                out.append(self.para_frame(it))
            elif k == "flow":
                out.extend(flowframes.get(id(it), []))
        flush()
        for key, wrap in hosts.items():
            if isinstance(key, tuple) and key[0] == "inv":
                ox0, oy0, ox1, oy1 = key[1]
                pts = [[[(ox0, oy1)] * 3, [(ox0, oy0)] * 3, [(ox1, oy0)] * 3, [(ox1, oy1)] * 3]]
                out.append(self.shape_xml("Rectangle", pts, [True], None, None, name="Ceñir texto", wrap=wrap))
        return out

    def line_frame(self, h):
        from reportlab.pdfbase import pdfmetrics
        s, font, size, cs = h["s"], h["font"], h["size"], h["cs"]
        ctm = h["ctm"]
        a, b, c, d, e, f = ctm
        if abs(b) < 1e-6 and abs(c) < 1e-6 and abs(a - d) < 1e-6 and a > 0 and abs(a - 1) > 1e-6:
            # texto dentro de un objeto escalado (p. ej. la etiqueta de una botella): se aplica la escala
            # al tamaño de letra para que en InDesign el marco no quede deformado
            h = dict(h, x=a * h["x"] + e, y=d * h["y"] + f, size=size * a, cs=cs * a, ctm=(1, 0, 0, 1, 0, 0))
            size, cs = h["size"], h["cs"]
        w = pdfmetrics.stringWidth(s, font, size) + cs * len(s)
        x = h["x"]
        if h["align"] == "c":
            x -= w / 2
        elif h["align"] == "r":
            x -= w
        slack = 2 + 0.04 * w
        al = {"l": "LeftAlign", "c": "CenterAlign", "r": "RightAlign"}[h["align"]]
        x0, x1 = x, x + w
        if al == "LeftAlign":
            x1 += slack
        elif al == "RightAlign":
            x0 -= slack
        else:
            x0 -= slack / 2
            x1 += slack / 2
        fam, sty, _ = FONTS.get(font, FONTS["Sans"])
        tracking = cs / size * 1000 if size else 0
        pself, pattrs = self.pstyle("Línea · %s %s %s pt" % (fam, sty, _f(size)), font, size, size * 1.2, h["color"], al,
                                    tracking=tracking)
        sid = self.add_story([(pself, pattrs, [(s, font, size, h["color"])])])
        return self.text_frame(sid, x0, h["y"] - size * 0.32, x1, h["y"] + size, h["ctm"], first_bl=size)

    def para_frame(self, h):
        p = h["para"]
        pself, pattrs = self.para_style_for(p)
        runs = self.runs_of(p)
        sid = self.add_story([(pself, pattrs, runs)])
        lead = p.style.leading
        return self.text_frame(sid, h["x"], h["y"] - lead * 0.9, h["x"] + h["w"] + 1.5, h["y"] + h["h"], h["ctm"],
                               first_bl=p.style.fontSize)

    def build_flows(self):
        """Crea las historias encadenadas. Devuelve {id(gancho): [xml de marcos]}."""
        frames_by_hook = {}
        for key in self.rec.flow_order:
            fl = self.rec.flows[key]
            hooks = [(pi, h) for pi, pg in enumerate(self.rec.pages) for h in pg["hooks"]
                     if h["kind"] == "flow" and h["key"] == key]
            paras = fl["paras"]
            left = fl["story"]
            if left:
                leftover = {id(x) for x in left}
                kept = [p for p in paras if id(p) not in leftover]
                if len(kept) != len(paras):
                    self.warnings.append("Un artículo tenía %d párrafos sin colocar; no se incluyen." % (len(paras) - len(kept)))
                paras = kept
            items = []
            sizes = {}
            for p in paras:
                pself, pattrs = self.para_style_for(p)
                items.append((pself, pattrs, self.runs_of(p)))
                sizes[p.style.fontSize] = sizes.get(p.style.fontSize, 0) + 1
            fbl = max(sizes, key=sizes.get) if sizes else 9
            sid = self.add_story(items)
            # marcos: columnas completas si vienen de make_frames, si no los marcos tal cual
            rects = []
            for pi, h in hooks:
                if h["mf"]:
                    x0, y0, x1, y1, ncols, obst = h["mf"]
                    cw = (x1 - x0 - (ncols - 1) * 5 * mm) / ncols
                    used_cols = sorted({round((fx - x0) / (cw + 5 * mm)) for fx, fy, fw, fh in h["frames"]})
                    for i in used_cols:
                        cx0 = x0 + i * (cw + 5 * mm)
                        rects.append((h, (cx0, y0, cx0 + cw, y1), bool(obst)))
                else:
                    for fx, fy, fw, fh in h["frames"]:
                        rects.append((h, (fx, fy, fx + fw, fy + fh), False))
            ids = [self.uid("tf") for _ in rects]
            for n, (h, (x0, y0, x1, y1), _) in enumerate(rects):
                prev = ids[n - 1] if n else "n"
                nxt = ids[n + 1] if n + 1 < len(ids) else "n"
                xml = self.text_frame(sid, x0, y0, x1 + 0.5, y1, h["ctm"], prev, nxt, first_bl=fbl,
                                      ignore_wrap=False, fid=ids[n], name="Artículo")
                frames_by_hook.setdefault(id(h), []).append(xml)
        return frames_by_hook

    # ---------- recursos ----------
    def graphic_xml(self):
        src = open(os.path.join(TPL, "Graphic.xml"), encoding="utf-8").read()
        cols = []
        for rgb, (self_, name) in self.colors.items():
            vis = "true" if name else "false"
            nm = escape(name) if name else "$ID/"
            cols.append('<Color Self="%s" Model="Process" Space="RGB" ColorValue="%d %d %d" ColorOverride="Normal" '
                        'AlternateSpace="NoAlternateColor" AlternateColorValue="" Name=%s ColorEditable="true" '
                        'ColorRemovable="true" Visible="%s" SwatchCreatorID="7937"/>' % (
                            escape(self_), rgb[0], rgb[1], rgb[2], quoteattr(nm), vis))
        i = src.index("<Ink ")
        return src[:i] + "\n\t".join(cols) + "\n\t" + src[i:]

    def styles_xml(self):
        src = open(os.path.join(TPL, "Styles.xml"), encoding="utf-8").read()
        ps = []
        for self_, a in self.pstyles.values():
            attrs = " ".join('%s=%s' % (k, quoteattr(v)) for k, v in a.items() if not k.startswith("_"))
            ps.append('<ParagraphStyle Self=%s Imported="false" %s NextStyle=%s>'
                      '<Properties><BasedOn type="string">$ID/NormalParagraphStyle</BasedOn>'
                      '<AppliedFont type="string">%s</AppliedFont></Properties></ParagraphStyle>' % (
                          quoteattr(self_), attrs, quoteattr(self_), escape(a["_font"])))
        i = src.index("</RootParagraphStyleGroup>")
        return src[:i] + "\n\t\t".join(ps) + "\n\t" + src[i:]

    def fonts_xml(self):
        fams = {}
        for fam, sty, ps in FONTS.values():
            fams.setdefault(fam, {})[sty] = ps
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">']
        for i, (fam, stys) in enumerate(fams.items()):
            fid = "di%x" % (0x900 + i)
            out.append('<FontFamily Self="%s" Name=%s>' % (fid, quoteattr(fam)))
            for sty, ps in stys.items():
                full = "%s %s" % (fam, sty)
                out.append('<Font Self=%s FontFamily=%s Name=%s PostScriptName=%s Status="Installed" FontStyleName=%s '
                           'FontType="OpenTypeTT" WritingScript="0" FullName=%s FullNameNative=%s FontStyleNameNative=%s '
                           'PlatformName="$ID/" Version=""/>' % (
                               quoteattr("%sFontn%s" % (fid, full)), quoteattr(fam), quoteattr(full), quoteattr(ps),
                               quoteattr(sty), quoteattr(full), quoteattr(full), quoteattr(sty)))
            out.append('</FontFamily>')
        out.append('</idPkg:Fonts>')
        return "\n".join(out)

    def prefs_xml(self, npages):
        src = open(os.path.join(TPL, "Preferences.xml"), encoding="utf-8").read()
        t, b, l, r = self.cfg["margins"]

        def setattrs(tag, **kv):
            nonlocal src
            m = re.search(r"<%s\b[^>]*>" % tag, src)
            el = m.group(0)
            for k, v in kv.items():
                if re.search(r'\b%s="[^"]*"' % k, el):
                    el = re.sub(r'\b%s="[^"]*"' % k, '%s="%s"' % (k, v), el)
                else:
                    el = el.replace("<%s " % tag, '<%s %s="%s" ' % (tag, k, v), 1)
            src = src[:m.start()] + el + src[m.end():]

        setattrs("DocumentPreference", PageHeight=_f(self.H), PageWidth=_f(self.W), PagesPerDocument=str(npages),
                 FacingPages="false")
        setattrs("MarginPreference", ColumnCount=str(self.cfg["cols"]), ColumnGutter=_f(self.cfg["gutter"]),
                 Top=_f(t), Bottom=_f(b), Left=_f(l), Right=_f(r))
        if self.cfg.get("baseline"):
            st, dv = self.cfg["baseline"]
            setattrs("GridPreference", BaselineStart=_f(st), BaselineDivision=_f(dv))
        return src

    def margin_xml(self):
        t, b, l, r = self.cfg["margins"]
        n, g = self.cfg["cols"], self.cfg["gutter"]
        cw = (self.W - l - r - (n - 1) * g) / n
        pos = []
        for i in range(n):
            pos += [i * (cw + g), i * (cw + g) + cw]
        return ('<MarginPreference ColumnCount="%d" ColumnGutter="%s" Top="%s" Bottom="%s" Left="%s" Right="%s" '
                'ColumnDirection="Horizontal" ColumnsPositions="%s"/>') % (n, _f(g), _f(t), _f(b), _f(l), _f(r),
                                                                          " ".join(_f(v) for v in pos))

    def page_xml(self, pself, name, master):
        return ('<Page Self="%s" GeometricBounds="0 0 %s %s" ItemTransform="1 0 0 1 %s %s" Name="%s" '
                'AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName" OverrideList="" AppliedMaster="%s" '
                'MasterPageTransform="1 0 0 1 0 0" TabOrder="" GridStartingPoint="TopOutside" UseMasterGrid="true">'
                '<Properties><PageColor type="enumeration">UseMasterColor</PageColor></Properties>%s</Page>') % (
            pself, _f(self.H), _f(self.W), _f(self.OX), _f(self.OY), name, master, self.margin_xml())

    def write(self, out_path):
        pages = self.rec.pages
        flowframes = self.build_flows()
        spreads = []
        page_ids = []
        for pi, page in enumerate(pages):
            items = self.page_items(pi, page, flowframes)
            sid, pid = self.uid("sp"), self.uid("pg")
            page_ids.append(pid)
            xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                   '<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">'
                   '<Spread Self="%s" FlattenerOverride="Default" AllowPageShuffle="true" ItemTransform="1 0 0 1 0 0" '
                   'ShowMasterItems="true" PageCount="1" BindingLocation="0" PageTransitionType="None" '
                   'PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium">%s\n%s</Spread></idPkg:Spread>') % (
                sid, self.page_xml(pid, str(pi + 1), "mA"), "\n".join(items))
            spreads.append((sid, xml))
        master = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                  '<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">'
                  '<MasterSpread Self="mA" ItemTransform="1 0 0 1 0 0" OverriddenPageItemProps="" Name="A-Retícula" '
                  'NamePrefix="A" BaseName="Retícula" ShowMasterItems="true" PageCount="1">'
                  '<Properties><PageColor type="enumeration">UseMasterColor</PageColor></Properties>%s'
                  '</MasterSpread></idPkg:MasterSpread>') % self.page_xml("mApg", "A", "n")
        # designmap
        dm = open(os.path.join(TPL, "designmap.xml"), encoding="utf-8").read()
        dm = re.sub(r'\s*<Layer .*?</Layer>', "", dm, flags=re.S)
        dm = re.sub(r'\s*<idPkg:(MasterSpread|Spread|Story) [^>]*/>', "", dm)
        dm = re.sub(r'\s*<Section .*?</Section>', "", dm, flags=re.S)
        backing = "uBack"
        story_ids = [s for s, _ in self.stories] + [backing]
        dm = re.sub(r'StoryList="[^"]*"', 'StoryList="%s"' % " ".join(story_ids), dm)
        dm = re.sub(r'ActiveLayer="[^"]*"', 'ActiveLayer="%s"' % self.layer, dm)
        layer = ('<Layer Self="%s" Name="Maqueta" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true" '
                 'LockGuides="false" UI="true" Expendable="true" Printable="true"><Properties>'
                 '<LayerColor type="enumeration">LightBlue</LayerColor></Properties></Layer>') % self.layer
        refs = [layer, '<idPkg:MasterSpread src="MasterSpreads/MasterSpread_mA.xml"/>']
        refs += ['<idPkg:Spread src="Spreads/Spread_%s.xml"/>' % s for s, _ in spreads]
        refs.append('<Section Self="sec1" Length="%d" Name="" ContinueNumbering="true" IncludeSectionPrefix="false" '
                    'Marker="" PageStart="%s" SectionPrefix=""><Properties><PageNumberStyle type="enumeration">Arabic'
                    '</PageNumberStyle></Properties></Section>' % (len(spreads), page_ids[0]))
        i = dm.index('<idPkg:BackingStory')
        dm = dm[:i] + "\n\t".join(refs) + "\n\t" + dm[i:]
        i = dm.index('<idPkg:BackingStory')
        j = dm.index('/>', i) + 2
        dm = dm[:j] + "".join('\n\t<idPkg:Story src="Stories/Story_%s.xml"/>' % s for s, _ in self.stories) + dm[j:]
        backing_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                       '<idPkg:BackingStory xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">'
                       '<XmlStory Self="%s" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">'
                       '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">'
                       '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                       '<XMLElement Self="di2" MarkupTag="XMLTag/Root"/>'
                       '</CharacterStyleRange></ParagraphStyleRange></XmlStory></idPkg:BackingStory>') % backing
        tags = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<idPkg:Tags xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">'
                '<XMLTag Self="XMLTag/Root" Name="Root"><Properties><TagColor type="enumeration">LightBlue</TagColor>'
                '</Properties></XMLTag></idPkg:Tags>')
        # el orden importa: los estilos y colores se llenan al generar páginas e historias
        graphic, styles = self.graphic_xml(), self.styles_xml()
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with zipfile.ZipFile(out_path, "w") as z:
            z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.adobe.indesign-idml-package", compress_type=zipfile.ZIP_STORED)
            zf = lambda n, s: z.writestr(n, s.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
            zf("META-INF/container.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
               '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
               '<rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles></container>')
            zf("designmap.xml", dm)
            zf("Resources/Graphic.xml", graphic)
            zf("Resources/Fonts.xml", self.fonts_xml())
            zf("Resources/Styles.xml", styles)
            zf("Resources/Preferences.xml", self.prefs_xml(len(spreads)))
            zf("MasterSpreads/MasterSpread_mA.xml", master)
            for s, xml in spreads:
                zf("Spreads/Spread_%s.xml" % s, xml)
            for s, xml in self.stories:
                zf("Stories/Story_%s.xml" % s,
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                   '<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="7.5">%s</idPkg:Story>' % xml)
            zf("XML/BackingStory.xml", backing_xml)
            zf("XML/Tags.xml", tags)
        # vínculos junto al IDML
        links = os.path.join(os.path.dirname(os.path.abspath(out_path)), "Links")
        if self.links:
            os.makedirs(links, exist_ok=True)
            for src, name in self.links.items():
                shutil.copyfile(src, os.path.join(links, name))
        for w in self.warnings:
            print("AVISO IDML:", w)
        print("IDML ->", out_path, "(%d páginas, %d historias, %d fotos)" % (len(spreads), len(self.stories), len(self.links)))


def _selfname(name):
    return name.replace("%", "%25").replace(":", "%3a")


def _interp2_with_alpha(code, extg):
    fixed = []
    for chunk in code:
        def rep(m):
            a, v = extg.get(m.group(1), (None, None))
            if a == "ca":
                return " %s 0 0 0 0 0 0 0 0 FA_ " % v
            if a == "CA":
                return " %s 0 0 0 0 0 0 0 0 SA_ " % v
            return " "
        fixed.append(re.sub(r"/(\S+)\s+gs", rep, chunk))
    return _interp2(fixed)
