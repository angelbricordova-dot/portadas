"""Genera las tres revistas en ../output/ (PULSO, ARENA, ÍMPETU)."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
jobs = [("build_pulso.py", "../output/PULSO.pdf", "authors/pulso_manuel_vera.json"),
        ("build_arena.py", "../output/ARENA.pdf", "authors/arena_jesus_trias.json"),
        ("build_impetu.py", "../output/IMPETU.pdf", None)]   # ÍMPETU: aún sin datos de autor
for script, out, autor in jobs:
    cmd = [sys.executable, "-I", os.path.join(here, script), os.path.join(here, out)] + ([os.path.join(here, autor)] if autor else [])
    print(">>", " ".join(os.path.basename(x) for x in cmd))
    subprocess.run(cmd, check=True, cwd=here)
