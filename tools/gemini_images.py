#!/usr/bin/env python3
"""Genera las imágenes de los huecos con la API de Gemini y las guarda en images/generated/<revista>/<hueco>.png

SIN PROBAR: se escribió sin acceso a internet. Antes de usarlo:
  1) pip install google-genai pillow
  2) export GEMINI_API_KEY="tu_clave"   (clave de Google AI Studio; la suscripción de la app NO sirve)
  3) Revisa en la documentación vigente (ai.google.dev) el nombre actual del modelo de imágenes y ajusta
     GEMINI_IMAGE_MODEL / IMAGEN_MODEL. Los valores por defecto son los que conocía y pueden haber cambiado.

Uso:
  python3 tools/gemini_images.py --mag pulso --style illustration
  python3 tools/gemini_images.py --mag all --style photo --only equipo_apertura raqueta
  python3 tools/gemini_images.py --mag arena --engine imagen --dry-run     # solo muestra los prompts
"""
import os, sys, json, argparse, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIOS = {"1:1": 1.0, "3:2": 1.5, "2:3": 2 / 3, "3:4": 0.75, "4:3": 4 / 3, "4:5": 0.8, "5:4": 1.25, "9:16": 9 / 16, "16:9": 16 / 9, "21:9": 21 / 9}


def nearest_ratio(w, h):
    r = w / h
    return min(RATIOS, key=lambda k: abs(RATIOS[k] - r))


def gen_gemini(client, types, model, prompt, ratio):
    cfg = None
    try:
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=ratio))
    except Exception:
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE"])
        prompt = "%s Aspect ratio %s." % (prompt, ratio)
    resp = client.models.generate_content(model=model, contents=[prompt], config=cfg)
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return part.inline_data.data
    raise RuntimeError("La respuesta no trajo imagen: %s" % (resp.text if hasattr(resp, "text") else resp))


def gen_imagen(client, types, model, prompt, ratio):
    resp = client.models.generate_images(model=model, prompt=prompt,
                                         config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=ratio))
    return resp.generated_images[0].image.image_bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mag", default="all", choices=["pulso", "arena", "impetu", "all"])
    ap.add_argument("--style", default="illustration", choices=["illustration", "photo"])
    ap.add_argument("--engine", default="gemini", choices=["gemini", "imagen"])
    ap.add_argument("--only", nargs="*", help="nombres de huecos concretos")
    ap.add_argument("--force", action="store_true", help="regenerar aunque exista")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    slots = json.load(open(os.path.join(ROOT, "images", "slots.json")))["slots"]
    slots = [s for s in slots if (a.mag == "all" or s["mag"] == a.mag) and (not a.only or s["slot"] in a.only)]

    client = types = None
    if not a.dry_run:
        from google import genai
        from google.genai import types as T
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            sys.exit("Falta GEMINI_API_KEY en el entorno.")
        client, types = genai.Client(api_key=key), T
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    imodel = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")

    for s in slots:
        w, h = s["size_mm"]
        ratio = nearest_ratio(w, h)
        prompt = "%s %s" % (s["subject"], s["style_" + a.style])
        out = os.path.join(ROOT, "images", "generated", s["mag"], s["slot"] + ".png")
        print("[%s/%s] %dx%d mm -> %s" % (s["mag"], s["slot"], w, h, ratio))
        if a.dry_run:
            print("   ", prompt)
            continue
        if os.path.exists(out) and not a.force:
            print("    ya existe, se omite (usa --force)")
            continue
        try:
            data = gen_gemini(client, types, model, prompt, ratio) if a.engine == "gemini" else gen_imagen(client, types, imodel, prompt, ratio)
        except Exception as e:
            print("    ERROR:", e)
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        from PIL import Image
        Image.open(io.BytesIO(data)).convert("RGB").save(out)
        print("    guardada")


if __name__ == "__main__":
    main()
