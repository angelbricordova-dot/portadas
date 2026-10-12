#!/usr/bin/env python3
"""Importa fotos generadas a mano (p. ej. en la web de ElevenCreative).

Acepta un ZIP o una carpeta con archivos llamados <revista>_<hueco>.(png|jpg|jpeg|webp),
p. ej. pulso_portada.png o arena_montana.jpg, y los copia a images/raw/<revista>/<hueco>.<ext>.
Después ejecuta tools/grade_images.py.

    python3 tools/import_photos.py fotos.zip
"""
import os, sys, json, zipfile, shutil, tempfile, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return s.replace(" ", "_").replace("-", "_")


def main(src):
    slots = {"%s_%s" % (s["mag"], s["slot"]): (s["mag"], s["slot"])
             for s in json.load(open(os.path.join(ROOT, "images", "photos.json")))["slots"]}
    tmp = None
    if zipfile.is_zipfile(src):
        tmp = tempfile.mkdtemp()
        zipfile.ZipFile(src).extractall(tmp)
        src = tmp
    found = set()
    for dp, _, files in os.walk(src):
        for f in files:
            base, ext = os.path.splitext(f)
            if ext.lower() not in EXTS or f.startswith("."):
                continue
            key = norm(base)
            if key not in slots:
                print("?  no reconozco:", f)
                continue
            mag, slot = slots[key]
            d = os.path.join(ROOT, "images", "raw", mag)
            os.makedirs(d, exist_ok=True)
            for e in EXTS:
                if os.path.exists(os.path.join(d, slot + e)):
                    os.remove(os.path.join(d, slot + e))
            shutil.copyfile(os.path.join(dp, f), os.path.join(d, slot + ext.lower()))
            found.add(key)
            print("ok", key)
    missing = sorted(set(slots) - found)
    print("\n%d importadas, faltan %d%s" % (len(found), len(missing), (": " + ", ".join(missing)) if missing else ""))
    if tmp:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main(sys.argv[1])
