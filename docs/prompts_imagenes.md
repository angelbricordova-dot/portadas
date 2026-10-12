# Imágenes generadas (Gemini u otra API)

Hay 21 huecos de imagen (`images/slots.json`). Cada uno tiene: revista, nombre, tamaño en mm, un sujeto (qué mostrar) y dos estilos (ilustración o foto) con la paleta de esa revista.

Reglas para que quede bien en la maqueta:
- Proporción: el script elige la más cercana al hueco; el código recorta para rellenar. Deja zonas tranquilas donde va el titular (los prompts ya lo piden).
- Nada de texto, logos ni personas reales en la imagen (los textos los pone el código).
- Mantén un solo estilo por revista, y estilos distintos entre revistas.
- Si usas fotos, revisa derechos/uso académico del generador y evita parecidos con personas reales.

Flujo recomendado:
1. `python3 tools/gemini_images.py --mag pulso --dry-run` para ver los prompts.
2. Genera, revisa, regenera solo las que no te gusten (`--only slot --force`).
3. `python3 src/build_all.py` y revisa cada página del PDF.
4. Para volver a la ilustración vectorial de un hueco, borra su archivo en `images/generated/<revista>/`.

Alternativa si no quieres API: genera las imágenes en la app de Gemini, descárgalas y guárdalas con el nombre del hueco (`images/generated/arena/montana.png`, etc.).
