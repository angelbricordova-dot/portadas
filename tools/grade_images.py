#!/usr/bin/env python3
"""Gradúa el color de las fotos de images/raw/ con el look de cada revista y las deja en images/generated/.

Por qué: las imágenes generadas salen cada una con su propio color. Un mismo tratamiento por revista
(tono partido en sombras/luces, contraste y grano fino) las unifica y las aleja del aspecto "plástico"
típico de la IA. Los ajustes son suaves a propósito.

    python3 tools/grade_images.py            # procesa todas
    python3 tools/grade_images.py --mag arena
"""
import os, glob, argparse
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# sombra, luz (RGB), fuerza del tono, contraste, saturación, negro elevado, grano
LOOKS = {
    "pulso":  dict(shadow=(11, 31, 58), light=(255, 170, 110), tone=0.22, contrast=1.08, sat=0.96, lift=0.0, grain=0.018),
    "arena":  dict(shadow=(40, 20, 90), light=(235, 255, 200), tone=0.14, contrast=1.14, sat=1.06, lift=0.0, grain=0.012),
    "impetu": dict(shadow=(31, 90, 100), light=(240, 190, 100), tone=0.20, contrast=0.98, sat=0.90, lift=0.05, grain=0.022),
}
MAX_SIDE = 3600


def grade(img, look, seed):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]
    # saturación
    a = lum + (a - lum) * look["sat"]
    # contraste en S alrededor del gris medio
    a = 0.5 + (a - 0.5) * look["contrast"]
    # tono partido: sombras hacia un color, luces hacia otro
    sh = np.array(look["shadow"], np.float32) / 255.0
    li = np.array(look["light"], np.float32) / 255.0
    ws = np.clip(1 - lum * 2, 0, 1) ** 1.5
    wl = np.clip(lum * 2 - 1, 0, 1) ** 1.5
    t = look["tone"]
    a = a * (1 - t * ws) + sh * (t * ws)
    a = a * (1 - t * 0.6 * wl) + li * (t * 0.6 * wl)
    # negros elevados (película)
    a = look["lift"] + a * (1 - look["lift"])
    # grano monocromo, más visible en medios tonos
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, a.shape[:2]).astype(np.float32)[..., None]
    a = a + g * look["grain"] * (1 - np.abs(lum - 0.5) * 1.2)
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mag", default="all", choices=["pulso", "arena", "impetu", "all"])
    a = ap.parse_args()
    mags = LOOKS if a.mag == "all" else [a.mag]
    for mag in mags:
        for src in sorted(glob.glob(os.path.join(ROOT, "images", "raw", mag, "*.*"))):
            slot = os.path.splitext(os.path.basename(src))[0]
            img = Image.open(src)
            if max(img.size) > MAX_SIDE:
                s = MAX_SIDE / max(img.size)
                img = img.resize((round(img.size[0] * s), round(img.size[1] * s)), Image.LANCZOS)
            out = grade(img, LOOKS[mag], seed=sum(map(ord, mag + slot)))
            dst_dir = os.path.join(ROOT, "images", "generated", mag)
            os.makedirs(dst_dir, exist_ok=True)
            for old in glob.glob(os.path.join(dst_dir, slot + ".*")):
                os.remove(old)
            dst = os.path.join(dst_dir, slot + ".jpg")
            out.save(dst, quality=92, subsampling=0)
            print("%s/%s  %dx%d" % (mag, slot, *out.size))


if __name__ == "__main__":
    main()
