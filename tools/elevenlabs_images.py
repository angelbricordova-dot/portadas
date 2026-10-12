#!/usr/bin/env python3
"""Genera las fotos de los huecos con la API de imágenes de ElevenLabs (POST /v1/flows/image).

La clave NUNCA va en el código ni en el repo:
    export ELEVENLABS_API_KEY="sk_..."

Uso:
    python3 tools/elevenlabs_images.py --mag all                  # genera lo que falte
    python3 tools/elevenlabs_images.py --mag pulso --only portada --force
    python3 tools/elevenlabs_images.py --mag arena --dry-run      # solo muestra los prompts
    python3 tools/elevenlabs_images.py --model gpt-image-2 --extra '{"quality": "high"}'

Guarda el original en images/raw/<revista>/<hueco>.<ext>. Después ejecuta tools/grade_images.py,
que recorta, gradúa el color con el look de cada revista y deja el resultado en images/generated/,
que es lo que usan los builders.

La API es asíncrona: crea la generación, sondea GET /v1/flows/image/<id> hasta que termina y
descarga la URL firmada del resultado. Requiere plan Pro o superior en ElevenLabs.
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.elevenlabs.io/v1/flows/image"
RATIOS = {"1:1": 1.0, "3:2": 1.5, "2:3": 2 / 3, "3:4": 0.75, "4:3": 4 / 3, "4:5": 0.8, "5:4": 1.25,
          "9:16": 9 / 16, "16:9": 16 / 9, "21:9": 21 / 9}


def nearest_ratio(w, h):
    r = w / h
    return min(RATIOS, key=lambda k: abs(RATIOS[k] - r))


def call(method, url, key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s en %s %s: %s" % (e.code, method, url, e.read().decode(errors="replace")[:1500]))


def find_urls(obj):
    """Busca URLs de imagen en la respuesta sin depender del nombre exacto del campo."""
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += find_urls(v)
    elif isinstance(obj, list):
        for v in obj:
            out += find_urls(v)
    elif isinstance(obj, str) and obj.startswith("http"):
        out.append(obj)
    return out


def generate(key, model, prompt, ratio, extra, poll=4, timeout=600):
    body = {"model_id": model, "prompt": prompt, "aspect_ratio": ratio}
    body.update(extra)
    job = call("POST", API, key, body)
    gid = job.get("id") or job.get("generation_id")
    if not gid:
        raise RuntimeError("Respuesta sin id: %s" % job)
    t0 = time.time()
    while True:
        st = call("GET", "%s/%s" % (API, gid), key)
        status = str(st.get("status", "")).lower()
        if status in ("completed", "complete", "succeeded", "success", "done"):
            urls = find_urls(st.get("output") or st.get("outputs") or st)
            if not urls:
                raise RuntimeError("Completado pero sin URL: %s" % st)
            return gid, urls[0]
        if status in ("failed", "error", "cancelled", "canceled", "rejected"):
            raise RuntimeError("Generación %s: %s" % (status, st))
        if time.time() - t0 > timeout:
            raise RuntimeError("Tiempo agotado esperando %s (último estado: %s)" % (gid, status))
        time.sleep(poll)


def download(url, dest):
    with urllib.request.urlopen(urllib.request.Request(url), timeout=300) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    ext = ".png" if "png" in ctype else ".webp" if "webp" in ctype else ".jpg"
    path = dest + ext
    with open(path, "wb") as f:
        f.write(data)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mag", default="all", choices=["pulso", "arena", "impetu", "all"])
    ap.add_argument("--only", nargs="*", help="nombres de huecos concretos")
    ap.add_argument("--force", action="store_true", help="regenerar aunque exista")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default=os.environ.get("ELEVENLABS_IMAGE_MODEL", "gemini-3-pro-image"))
    ap.add_argument("--extra", default="{}", help="JSON con campos extra del modelo (p. ej. resolución)")
    a = ap.parse_args()

    cfg = json.load(open(os.path.join(ROOT, "images", "photos.json")))
    slots = [s for s in cfg["slots"] if (a.mag == "all" or s["mag"] == a.mag) and (not a.only or s["slot"] in a.only)]
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not a.dry_run and not key:
        sys.exit("Falta ELEVENLABS_API_KEY en el entorno.")
    extra = json.loads(a.extra)
    log_path = os.path.join(ROOT, "images", "raw", "log.json")
    log = json.load(open(log_path)) if os.path.exists(log_path) else {}

    for s in slots:
        w, h = s["size_mm"]
        ratio = nearest_ratio(w, h)
        prompt = "%s %s %s" % (s["prompt"], cfg["looks"][s["mag"]], cfg["global"])
        dest = os.path.join(ROOT, "images", "raw", s["mag"], s["slot"])
        exists = [e for e in (".png", ".jpg", ".webp") if os.path.exists(dest + e)]
        if exists and not a.force:
            print("= %s/%s ya existe" % (s["mag"], s["slot"]))
            continue
        print("> %s/%s  %s  %s" % (s["mag"], s["slot"], ratio, a.model))
        if a.dry_run:
            print("  ", prompt)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            gid, url = generate(key, a.model, prompt, ratio, extra)
            for e in exists:
                os.remove(dest + e)
            path = download(url, dest)
            log["%s/%s" % (s["mag"], s["slot"])] = {"id": gid, "model": a.model, "ratio": ratio, "prompt": prompt}
            json.dump(log, open(log_path, "w"), indent=1, ensure_ascii=False)
            print("  ok ->", os.path.relpath(path, ROOT))
        except Exception as e:
            print("  ERROR:", e)


if __name__ == "__main__":
    main()
