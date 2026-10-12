# Paquete de traspaso: revistas de deporte (PULSO · ARENA · ÍMPETU)

## Contenido
```
CLAUDE.md                instrucciones del proyecto (Claude Code lo lee solo)
docs/brief.md            contexto completo: cliente, requisitos, decisiones, historial, pendientes
docs/diseno.md           especificaciones de diseño de las 3 revistas y mapa de páginas
docs/prompts_imagenes.md cómo generar imágenes con Gemini y qué pedir
images/slots.json        huecos de imagen (tamaño en mm + prompts)
src/                     código, textos, fuentes, autores
tools/gemini_images.py   generador de imágenes (Gemini / Imagen)
output/                  PDF actuales (referencia exacta)
reference/               pizarra original + primera versión de 16 pp
```

## Cómo empezar en Claude Code (en tu computadora)
1. Descomprime la carpeta y ábrela en una terminal: `cd revistas_deporte && claude`
2. Instala dependencias: `pip install reportlab pillow fonttools google-genai` (y `poppler` para `pdftoppm`: `brew install poppler` en Mac).
3. Comprueba que todo funciona: `python3 src/build_all.py` (debe crear `output/PULSO.pdf`, `ARENA.pdf`, `IMPETU.pdf`).
4. Pega este primer mensaje a Claude Code:

> Lee CLAUDE.md, docs/brief.md y docs/diseno.md. Luego dime en 5 líneas qué entendiste y qué falta. Después: (a) completa los pendientes que dependan de mí, (b) conecta la generación de imágenes con Gemini (tools/gemini_images.py, mi clave está en la variable GEMINI_API_KEY), (c) regenera las 3 revistas con las imágenes, revisa cada página visualmente y dime qué mejorarías antes de entregarlas.

## Skills / herramientas que pediste instalar (hazlo en tu máquina, que sí tiene red)
```
npx skills add emilkowalski/skill
npx impeccable install
npx skills add Leonxlnx/taste-skill
npx skills add dickwu/apple-design-skill
```
Desde aquí no pude instalarlas (el registro npm devolvía 403). Antes de usarlas, revisa qué instrucciones traen: son código y texto de terceros. Útiles además: el skill de PDF y `frontend-design` de Claude Code.

## Imágenes con Gemini
- La suscripción de la app de Gemini **no** es la API. Necesitas una clave de API de Google AI Studio (aistudio.google.com). Guárdala como variable de entorno: `export GEMINI_API_KEY="..."`. No la pegues en el chat ni la subas a ningún repositorio.
- Claude Code no genera fotos por sí mismo: puede dibujar vectores (como las ilustraciones actuales) o llamar a una API/MCP de imágenes.
- Flujo: `python3 tools/gemini_images.py --mag pulso --style illustration` guarda `images/generated/pulso/<hueco>.png`; luego `python3 src/build_all.py` usa esas imágenes automáticamente. Los textos, degradados y recuadros siguen dibujados por código encima de la imagen.
- Si una imagen no gusta, bórrala y se vuelve a usar la ilustración vectorial.

## Qué NO está incluido a propósito
- La transcripción literal del chat y la conversación con el cliente: contienen datos de pago y personales. En `docs/brief.md` va un resumen fiel sin esos datos.
- El IDML antiguo (16 páginas, nunca probado en InDesign).
