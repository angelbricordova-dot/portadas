# Proyecto: 3 revistas de deporte (A4, 10 páginas, PDF) — instrucciones para Claude Code

Lee este archivo completo y luego `docs/brief.md` (contexto del encargo) y `docs/diseno.md` (especificaciones de cada revista) antes de tocar nada.

## Quién es el usuario y cómo trabajar con él
- Alejandro Lamont, Venezuela. Presta este servicio de diseño a unos compañeros de universidad (Comunicación Social, UCAB Guayana). No sabe programar pero es cómodo con herramientas técnicas.
- Español, directo, concreto, con una breve explicación del contexto. Sin adulación ni relleno. Dile las verdades duras.
- Si pide algo rápido, dáselo sin preámbulo. Si algo que pide contradice un hecho (p. ej. fechas, páginas, datos), dilo.
- Patrón que él pidió que le confrontes: empieza cosas antes de cobrarlas. Recuérdale cuándo falta el pago/confirmación antes de construir o entregar.

## Qué hay aquí
- `src/` código que genera las 3 revistas con reportlab (Python). `python3 src/build_all.py` las regenera en `output/`. Reproducen píxel a píxel los PDF entregados (verificado).
- `src/texts_*.py` textos (los "propios" están escritos; el resto es lorem ipsum generado en código).
- `src/fonts/` Inter, Inter Display y Lora (licencia OFL) ya en TTF.
- `src/imgslots.py` permite sustituir cada ilustración vectorial por una imagen generada (Gemini u otra) sin tocar el código: basta con dejar `images/generated/<revista>/<hueco>.png`.
- `tools/gemini_images.py` genera esas imágenes con la API de Gemini (SIN PROBAR: se escribió sin acceso a red; revisa nombres de modelo y SDK en la documentación vigente).
- `images/slots.json` lista de huecos, tamaño en mm y prompts.
- `output/` los 3 PDF actuales. `reference/` pizarra con los requisitos y la primera versión de 16 páginas (obsoleta).

## Requisitos de la pizarra (la tarea de clase, "en Adobe InDesign")
Revista sobre los tipos de deporte, entrega el **martes 13 de octubre de 2026**. Debe incluir: portada; editorial e índice; 6 artículos con texto falso (2 de ellos "propios", interpretado como 2 artículos con texto real escrito); 3 publicidades; contraportada. Además: retícula, ceñir texto, texto falso, insertar imágenes, diagramación con principios de diseño (la última línea de la pizarra está cortada; se asumió contraste, repetición, alineación y proximidad). Límite acordado con la clienta: **10 páginas**.

## Reglas al modificar
- Cada revista debe verse claramente distinta de las otras (paleta, tipografía, retícula, ilustraciones, temas y textos): son para compañeros del mismo curso y no deben parecer plagio.
- Los anuncios son de marcas ficticias y deben llevar siempre el pie "Anuncio ficticio realizado con fines académicos." No uses marcas, logos ni personas reales.
- Tras cualquier cambio: regenera el PDF, conviértelo a imágenes (`pdftoppm -r 70 -png`), **mira cada página** y busca texto cortado/solapado, huecos y desbordes. Los builders ya hacen `assert` si un artículo desborda.
- Datos reales citados (récords, años, distancias) están escritos de memoria y no verificados: contrástalos con fuentes antes de la entrega.
- Los datos de autor (nombre/cédula) están en `src/authors/*.json`. Son datos personales de terceros: úsalos solo para las portadas/índices de su revista.

## Pendientes conocidos (ver docs/brief.md §6)
1. Ímpetu aún no tiene datos de autor (nombre, cédula, universidad) ni pago confirmado.
2. Decidir con la clienta/profesor si basta con PDF o hay que entregar el archivo de InDesign (.indd/.idml). Intentos de convertir con el conector de Adobe fallaron (502); un IDML de la versión de 16 páginas existió pero no se probó y está obsoleto.
3. Confirmar qué revista corresponde a qué estudiante (ver brief).
