"""Sustitución opcional de las ilustraciones vectoriales por imágenes generadas (Gemini, etc.).

Cada ilustración de las revistas es una función dibujada en código. `wrap` la envuelve:
si existe  images/generated/<revista>/<slot>.(png|jpg|jpeg|webp)  se usa esa imagen
(recortada para rellenar el marco, como "Rellenar marco proporcionalmente" en InDesign);
si no existe, se dibuja la ilustración vectorial original. Los degradados, textos y
recuadros de las páginas se dibujan encima igual que antes.

RECORD_SLOTS=1 vuelca en images/slots_used.json el tamaño (mm) de cada hueco usado.
"""
import os, json, atexit
import idml_export
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.environ.get("IMG_DIR", os.path.join(ROOT, "images", "generated"))
_LOG = {}


def _find(mag, slot):
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = os.path.join(IMG_DIR, mag, "%s.%s" % (slot, ext))
        if os.path.exists(p):
            return p
    return None


def wrap(fn, mag, slot, get_canvas=None):
    """get_canvas=None: fn(c, x, y, w, h). Con get_canvas: fn(x, y, w, h) y el lienzo es global."""
    def g(*a):
        if get_canvas:
            x, y, w, h = a; c = get_canvas(); call = lambda: fn(x, y, w, h)
        else:
            c, x, y, w, h = a; call = lambda: fn(c, x, y, w, h)
        _LOG.setdefault("%s/%s" % (mag, slot), set()).add((round(w / mm), round(h / mm)))
        p = _find(mag, slot)
        if not p:
            return call()
        img = ImageReader(p)
        iw, ih = img.getSize()
        s = max(w / iw, h / ih)
        dw, dh = iw * s, ih * s
        c.saveState()
        idml_export.hook_image(c, p, x, y, w, h, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, slot)
        path = c.beginPath(); path.rect(x, y, w, h); c.clipPath(path, stroke=0, fill=0)
        c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
        c.restoreState()
    return g


def has(mag, slot):
    """True si hay foto para ese hueco."""
    return _find(mag, slot) is not None


def photo(c, mag, slot, x, y, w, h):
    """Dibuja la foto del hueco (recortada para rellenar). Devuelve False si no existe."""
    p = _find(mag, slot)
    if not p:
        return False
    wrap(lambda *a: None, mag, slot)(c, x, y, w, h)
    return True


@atexit.register
def _dump():
    if os.environ.get("RECORD_SLOTS") and _LOG:
        f = os.path.join(ROOT, "images", "slots_used.json")
        try:
            data = json.load(open(f))
        except Exception:
            data = {}
        for k, v in _LOG.items():
            data[k] = sorted(v)
        json.dump(data, open(f, "w"), indent=1)
