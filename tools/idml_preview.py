#!/usr/bin/env python3
"""Vista previa aproximada de un IDML (sin InDesign) para revisar la exportación.

Lee el paquete IDML como lo haría InDesign (pliegos, ItemTransform, trazados, colores, opacidad,
imágenes vinculadas, historias encadenadas y ceñido "saltar objeto") y dibuja cada página en PNG.
El texto se compone con un algoritmo simple (línea a línea, sin kerning): sirve para detectar
texto desbordado, marcos mal colocados u objetos fuera de orden, no para juzgar la tipografía fina.

    python3 tools/idml_preview.py output/PULSO.idml /tmp/prev  [--dpi 60]
"""
import os, sys, re, math, zipfile, argparse
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTDIR = os.path.join(ROOT, "src", "fonts")
FONTFILES = {
    ("Inter", "Regular"): "Inter-Regular", ("Inter", "Medium"): "Inter-Medium", ("Inter", "SemiBold"): "Inter-SemiBold",
    ("Inter", "Bold"): "Inter-Bold", ("Inter", "Italic"): "Inter-Italic",
    ("Inter Display", "Black"): "InterDisplay-Black", ("Inter Display", "Black Italic"): "InterDisplay-BlackItalic",
    ("Inter Display", "ExtraBold"): "InterDisplay-ExtraBold",
    ("Lora", "Regular"): "Lora-Regular", ("Lora", "Medium"): "Lora-Medium", ("Lora", "SemiBold"): "Lora-SemiBold",
    ("Lora", "Bold"): "Lora-Bold", ("Lora", "Italic"): "Lora-Italic", ("Lora", "BoldItalic"): "Lora-BoldItalic",
}
_fcache = {}


def font(fam, sty, px):
    key = (fam, sty, round(px * 4))
    if key not in _fcache:
        f = FONTFILES.get((fam, sty), "Inter-Regular")
        _fcache[key] = ImageFont.truetype(os.path.join(FONTDIR, f + ".ttf"), max(1, round(px)))
    return _fcache[key]


def mat(s):
    return tuple(float(v) for v in s.split())


def mul(m, n):  # aplica m y luego n
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F)


def ap(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


class Doc:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        self.dir = os.path.dirname(os.path.abspath(path))
        self.colors = {}
        g = ET.fromstring(self.z.read("Resources/Graphic.xml"))
        for c in g.iter("Color"):
            v = [float(x) for x in c.get("ColorValue", "0 0 0").split()]
            if c.get("Space") == "RGB":
                self.colors[c.get("Self")] = tuple(int(x) for x in v)
            else:
                cc, m, y, k = (v + [0, 0, 0, 0])[:4]
                self.colors[c.get("Self")] = tuple(int(255 * (1 - min(1, (q + k) / 100))) for q in (cc, m, y))
        self.pstyles = {}
        st = ET.fromstring(self.z.read("Resources/Styles.xml"))
        for p in st.iter("ParagraphStyle"):
            d = dict(p.attrib)
            af = p.find("Properties/AppliedFont")
            d["font"] = af.text if af is not None else "Inter"
            self.pstyles[p.get("Self")] = d
        dm = ET.fromstring(self.z.read("designmap.xml"))
        ns = "{http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging}"
        self.spreads = [e.get("src") for e in dm if e.tag == ns + "Spread"]
        self.stories = {}
        for e in dm:
            if e.tag == ns + "Story":
                s = ET.fromstring(self.z.read(e.get("src"))).find("Story")
                self.stories[s.get("Self")] = s
        self.frames = {}
        for sp in self.spreads:
            root = ET.fromstring(self.z.read(sp))
            for tf in root.iter("TextFrame"):
                self.frames[tf.get("Self")] = tf

    def paragraphs(self, sid):
        """Historia -> lista de párrafos; cada uno: (estilo, [(texto, fam, sty, size, color, tracking)])."""
        out = []
        for psr in self.stories[sid].iter("ParagraphStyleRange"):
            ps = self.pstyles.get(psr.get("AppliedParagraphStyle"), {})
            cur = []
            for csr in psr.iter("CharacterStyleRange"):
                af = csr.find("Properties/AppliedFont")
                fam = af.text if af is not None else ps.get("font", "Inter")
                sty = csr.get("FontStyle", ps.get("FontStyle", "Regular"))
                size = float(csr.get("PointSize", ps.get("PointSize", 12)))
                col = self.colors.get(csr.get("FillColor", ps.get("FillColor")), (0, 0, 0))
                tr = float(csr.get("Tracking", ps.get("Tracking", 0)))
                for ch in csr:
                    if ch.tag == "Content":
                        cur.append((ch.text or "", fam, sty, size, col, tr))
                    elif ch.tag == "Br":
                        out.append((ps, cur))
                        cur = []
            if cur:
                out.append((ps, cur))
        return out


def path_pts(el, it):
    subs = []
    for gp in el.iter("GeometryPathType"):
        pts = []
        raw = [(tuple(map(float, p.get("Anchor").split())), tuple(map(float, p.get("LeftDirection").split())),
                tuple(map(float, p.get("RightDirection").split()))) for p in gp.iter("PathPointType")]
        closed = gp.get("PathOpen") == "false"
        n = len(raw)
        segs = range(n if closed else n - 1)
        if not raw:
            continue
        pts.append(raw[0][0])
        for i in segs:
            a, b = raw[i], raw[(i + 1) % n]
            p0, c1, c2, p1 = a[0], a[2], b[1], b[0]
            if c1 == p0 and c2 == p1:
                pts.append(p1)
            else:
                for k in range(1, 13):
                    t = k / 12
                    u = 1 - t
                    pts.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                                u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p1[1]))
        subs.append(([ap(it, *p) for p in pts], closed))
    return subs


class Page:
    def __init__(self, doc, spread_xml, dpi):
        self.doc = doc
        self.dpi = dpi
        root = ET.fromstring(spread_xml)
        self.spread = root.find("Spread")
        pg = self.spread.find("Page")
        gb = [float(v) for v in pg.get("GeometricBounds").split()]
        self.ph, self.pw = gb[2], gb[3]
        self.pt = mat(pg.get("ItemTransform"))
        self.k = dpi / 72.0
        self.img = Image.new("RGBA", (round(self.pw * self.k), round(self.ph * self.k)), (255, 255, 255, 255))
        self.wraps = []
        self.notes = []

    def P(self, x, y):  # pliego -> píxel de la página
        return ((x - self.pt[4]) * self.k, (y - self.pt[5]) * self.k)

    def draw_poly(self, subs, fill, stroke, lw, opacity):
        a = int(255 * opacity)
        pix = [([self.P(*p) for p in pts], closed) for pts, closed in subs]
        allp = [p for q, _ in pix for p in q]
        if not allp:
            return
        pad = (lw * self.k if stroke else 0) + 2
        x0 = max(0, int(min(p[0] for p in allp) - pad)); y0 = max(0, int(min(p[1] for p in allp) - pad))
        x1 = min(self.img.size[0], int(max(p[0] for p in allp) + pad) + 1)
        y1 = min(self.img.size[1], int(max(p[1] for p in allp) + pad) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        sh = lambda q: [(p[0] - x0, p[1] - y0) for p in q]
        if fill:
            mask = Image.new("L", layer.size, 0)
            md = ImageDraw.Draw(mask)
            for q, closed in pix:
                if len(q) >= 3:
                    md.polygon(sh(q), fill=255)
            layer.paste(fill + (a,), (0, 0), mask)
        if stroke and lw > 0:
            for q, closed in pix:
                q2 = sh(q) + (sh(q[:1]) if closed else [])
                if len(q2) >= 2:
                    d.line(q2, fill=stroke + (a,), width=max(1, round(lw * self.k)))
        self.img.alpha_composite(layer, (x0, y0))

    def walk(self, parent, it=(1, 0, 0, 1, 0, 0)):
        for el in parent:
            tag = el.tag
            if tag in ("Rectangle", "Polygon", "GraphicLine", "Oval", "Group", "TextFrame"):
                m = mul(mat(el.get("ItemTransform", "1 0 0 1 0 0")), it)
                tw = el.find("TextWrapPreference")
                if tw is not None and tw.get("TextWrapMode") == "JumpObjectTextWrap":
                    off = tw.find("Properties/TextWrapOffset")
                    xs = [p[0] for s, _ in path_pts(el, m) for p in s]
                    ys = [p[1] for s, _ in path_pts(el, m) for p in s]
                    self.wraps.append((min(xs) - float(off.get("Left")), min(ys) - float(off.get("Top")),
                                       max(xs) + float(off.get("Right")), max(ys) + float(off.get("Bottom"))))
                if tag == "Group":
                    self.walk(el, m)
                    continue
                if tag == "TextFrame":
                    continue
                subs = path_pts(el, m)
                op = 1.0
                bs = el.find("TransparencySetting/BlendingSetting")
                if bs is not None:
                    op = float(bs.get("Opacity", 100)) / 100
                fill = self.doc.colors.get(el.get("FillColor"))
                stroke = self.doc.colors.get(el.get("StrokeColor"))
                lw = float(el.get("StrokeWeight", 0))
                img = el.find("Image")
                if img is not None:
                    self.draw_image(img, subs, m)
                elif fill or stroke:
                    self.draw_poly(subs, fill, stroke, lw, op)

    def draw_image(self, img, subs, parent_m):
        link = img.find("Link").get("LinkResourceURI").replace("file:", "")
        path = os.path.join(self.doc.dir, link)
        if not os.path.exists(path):
            self.notes.append("falta vínculo " + link)
            return
        m = mul(mat(img.get("ItemTransform")), parent_m)
        im = Image.open(path).convert("RGBA")
        x0, y0 = self.P(*ap(m, 0, 0))
        x1, y1 = self.P(*ap(m, im.size[0], im.size[1]))
        im = im.resize((max(1, round(x1 - x0)), max(1, round(y1 - y0))))
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        layer.paste(im, (round(x0), round(y0)))
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).polygon([self.P(*p) for p in subs[0][0]], fill=255)
        clipped = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        clipped.paste(layer, (0, 0), mask)
        self.img.alpha_composite(clipped)


def frame_box(tf):
    m = mat(tf.get("ItemTransform"))
    pts = [ap(m, *map(float, p.get("Anchor").split())) for p in tf.iter("PathPointType")]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pref = tf.find("TextFramePreference")
    fbl = float(pref.get("MinimumFirstBaselineOffset", 0)) if pref is not None else 0
    ign = pref is not None and pref.get("IgnoreWrap") == "true"
    return (min(xs), min(ys), max(xs), max(ys)), m, fbl, ign


def compose(doc, pages_by_frame, sid, first_frame, draw=True):
    """Compone una historia en su cadena de marcos. Devuelve el número de líneas que no caben."""
    chain = []
    f = first_frame
    while f and f != "n":
        chain.append(doc.frames[f])
        f = doc.frames[f].get("NextTextFrame")
    paras = doc.paragraphs(sid)
    # tokens: (texto, estilo de carácter, salto forzado)
    lines_left = 0
    fi = 0
    box, m, fbl, ign = frame_box(chain[0])
    page = pages_by_frame[chain[0].get("Self")]
    y = box[1] + fbl
    first_in_frame = True

    def next_frame():
        nonlocal fi, box, m, fbl, ign, page, y, first_in_frame
        fi += 1
        if fi >= len(chain):
            return False
        box, m, fbl, ign = frame_box(chain[fi])
        page = pages_by_frame[chain[fi].get("Self")]
        y = box[1] + fbl
        first_in_frame = True
        return True

    def jump(yb, lead):
        if ign:
            return yb
        for wx0, wy0, wx1, wy1 in page.wraps:
            if wx1 > box[0] + 0.5 and wx0 < box[2] - 0.5 and yb - lead * 0.8 < wy1 and yb + lead * 0.25 > wy0:
                return wy1 + fbl
        return yb

    overset = 0
    prev_lead = None
    for ps, runs in paras:
        lead = float(ps.get("Leading", 12)) if ps.get("Leading", "Auto") != "Auto" else 12
        sa = float(ps.get("SpaceAfter", 0))
        align = ps.get("Justification", "LeftAlign")
        words = []
        for (t, fam, sty, size, col, tr) in runs:
            for piece in re.split(r"(\s+| )", t):
                if piece:
                    words.append((piece, fam, sty, size, col, tr))
        def wlen(w):
            f = font(w[1], w[2], w[3] * 4)
            return f.getlength(w[0]) / 4 + len(w[0]) * w[3] * w[5] / 1000

        i = 0
        while i <= len(words):
            if i == len(words) and i > 0:
                break
            # posición de la línea (salta obstáculos y pasa al marco siguiente si hace falta)
            if not overset:
                y = jump(y, lead)
                while y > box[3] + 0.5:
                    if not next_frame():
                        overset = 1
                        break
                    y = jump(y, lead)
            width = box[2] - box[0]
            ln, wsum = [], 0
            while i < len(words):
                w = words[i]
                if w[0] == "\u2028":
                    i += 1
                    break
                lw = wlen(w)
                if ln and not w[0].isspace() and wsum + lw > width + 0.01:
                    break
                i += 1
                if not ln and w[0].isspace():
                    continue
                ln.append(w)
                wsum += lw
            while ln and ln[-1][0].isspace():
                ln.pop()
            if overset:
                overset += 1
            elif draw:
                tot = sum(wlen(w) for w in ln)
                x = box[0] + {"CenterAlign": (width - tot) / 2, "RightAlign": width - tot}.get(align, 0)
                d = ImageDraw.Draw(page.img)
                for w in ln:
                    if w[5]:
                        for ch in w[0]:
                            px, py = page.P(x, y)
                            d.text((px, py), ch, font=font(w[1], w[2], w[3] * page.k), fill=w[4] + (255,), anchor="ls")
                            x += font(w[1], w[2], w[3] * 4).getlength(ch) / 4 + w[3] * w[5] / 1000
                    else:
                        px, py = page.P(x, y)
                        d.text((px, py), w[0], font=font(w[1], w[2], w[3] * page.k), fill=w[4] + (255,), anchor="ls")
                        x += wlen(w)
            y += lead
            if i >= len(words):
                break
        y += sa - 0  # espacio después
    return overset


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("idml")
    ap_.add_argument("outdir")
    ap_.add_argument("--dpi", type=float, default=60)
    a = ap_.parse_args()
    doc = Doc(a.idml)
    os.makedirs(a.outdir, exist_ok=True)
    pages = []
    by_frame = {}
    for sp in doc.spreads:
        pg = Page(doc, doc.z.read(sp), a.dpi)
        pg.walk(pg.spread)
        for tf in pg.spread.iter("TextFrame"):
            by_frame[tf.get("Self")] = pg
        pages.append(pg)
    # texto encima, en orden de cadena
    report = []
    for fid, tf in doc.frames.items():
        if tf.get("PreviousTextFrame") == "n":
            over = compose(doc, by_frame, tf.get("ParentStory"), fid)
            if over:
                pg = pages.index(by_frame[fid]) + 1
                txt = "".join(r[0] for _, rr in doc.paragraphs(tf.get("ParentStory"))[:1] for r in rr)[:40]
                report.append("pág %d: %d líneas desbordadas en «%s»" % (pg, over, txt))
    base = os.path.splitext(os.path.basename(a.idml))[0]
    for i, pg in enumerate(pages):
        pg.img.convert("RGB").save(os.path.join(a.outdir, "%s-%02d.png" % (base, i + 1)))
        for n in pg.notes:
            report.append("pág %d: %s" % (i + 1, n))
    print("\n".join(report) if report else "sin texto desbordado")


if __name__ == "__main__":
    main()
