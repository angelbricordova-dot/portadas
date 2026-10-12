"""Genera las tres revistas en ../output/<REVISTA>/ : PDF, IDML (InDesign), Links/, fuentes y un ZIP.

    python3 src/build_all.py            # PDF + IDML
    python3 src/build_all.py --solo-pdf # solo PDF (más rápido)
"""
import subprocess, sys, os, shutil, glob, zipfile

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
jobs = [("build_pulso.py", "PULSO", "authors/pulso_manuel_vera.json"),
        ("build_arena.py", "ARENA", None),     # ARENA: autor pendiente (Jesús Trias pasó a Ímpetu)
        ("build_impetu.py", "IMPETU", "authors/impetu_jesus_trias.json")]

LEEME = """{mag} — archivos para Adobe InDesign
=====================================

{mag}.pdf     versión final para ver o imprimir.
{mag}.idml    documento de InDesign (ábrelo con Archivo > Abrir; InDesign lo convierte en .indd).
Links/        fotos y degradados vinculados. Deben quedar junto al .idml.
Fuentes/      Inter, Inter Display y Lora (licencia OFL). Instálalas ANTES de abrir el .idml
              (doble clic en cada .ttf > Instalar), o InDesign marcará fuentes que faltan.

Al abrir:
1. Si aparece el aviso de vínculos que faltan: Ventana > Vínculos > selecciona todos >
   menú del panel > «Volver a vincular a carpeta…» y elige la carpeta Links.
2. Guarda como .indd (Archivo > Guardar como).

Qué incluye el documento
- Página maestra «A-Retícula» con márgenes y columnas de la revista (retícula).
- Estilos de párrafo (Cuerpo, Entradilla, Sumario, Pie de foto, Firma, Cita…).
- Artículos en marcos de texto encadenados entre columnas y páginas.
- Fotos y recuadros con ceñido de texto (Ventana > Ceñir texto: «Saltar objeto»).
- Ilustraciones y fondos como objetos vectoriales editables.

Nota: InDesign compone el texto con su propio motor; los cortes de línea pueden diferir
levemente del PDF. Si algún marco muestra el signo + rojo (texto desbordado), agranda un
poco el último marco del artículo.
"""


def main():
    solo_pdf = "--solo-pdf" in sys.argv
    out_root = os.path.join(root, "output")
    for script, mag, autor in jobs:
        d = os.path.join(out_root, mag)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        env = dict(os.environ)
        if not solo_pdf:
            env["IDML_OUT"] = os.path.join(d, mag + ".idml")
        cmd = [sys.executable, "-I", os.path.join(here, script), os.path.join(d, mag + ".pdf")]
        if autor and os.path.exists(os.path.join(here, autor)):
            cmd.append(os.path.join(here, autor))
        elif autor:
            print("!! falta %s: %s saldrá sin datos de autor" % (autor, mag))
        print(">>", mag)
        subprocess.run(cmd, check=True, cwd=here, env=env)
        if solo_pdf:
            continue
        fdir = os.path.join(d, "Fuentes")
        os.makedirs(fdir)
        for f in glob.glob(os.path.join(here, "fonts", "*.ttf")):
            shutil.copy(f, fdir)
        with open(os.path.join(d, "LEEME.txt"), "w", encoding="utf-8") as fh:
            fh.write(LEEME.format(mag=mag))
        zpath = os.path.join(out_root, mag + "_InDesign.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)):
                if os.path.isfile(p):
                    z.write(p, os.path.join(mag, os.path.relpath(p, d)))
        print("   ZIP ->", os.path.relpath(zpath, root))


if __name__ == "__main__":
    main()
