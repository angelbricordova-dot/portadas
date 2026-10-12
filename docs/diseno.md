# Especificaciones de diseño

Todas: A4 (210×297 mm), 10 páginas, fuentes incrustadas, anuncios con pie "Anuncio ficticio realizado con fines académicos.", ilustraciones vectoriales generadas en código (sustituibles por imágenes, ver `images/slots.json`).

## PULSO — `src/build_pulso.py`, textos `src/texts_pulso.py`
- Paleta: Marino #0B1F3A, Naranja #FF5A1F, Crema #F6F1E7 (fondo), Turquesa #14A3A0, Amarillo #FFC53D, Rojo #C8262D, Verde #0F6B4F, Tinta #1B1B1B, Gris #6B6B6B.
- Tipografía: titulares Inter Display Black Italic en mayúsculas; etiquetas Inter Bold/SemiBold con tracking; cuerpo Lora 9,2/13,4 (propios 9,7/14,2); entradilla Lora SemiBold; citas Lora Italic.
- Retícula: 3 columnas, márgenes 15 mm (inferior 22), medianil 5 mm. Texto ceñido con `make_frames` (marcos que esquivan obstáculos).
- Páginas: 1 portada · 2 editorial+índice (panel marino lateral, cita, recuadro de autor) · 3–4 Deportes de equipo (texto propio) · 5 Raqueta · 6 Acuáticos + anuncio HYDRA (franja 78 mm) · 7 Combate (texto propio) · 8 Extremos + anuncio ATLAS GYM · 9 Atletismo + anuncio VELOZ · 10 contraportada.
- Autor: `src/authors/pulso_manuel_vera.json`.

## ARENA — `src/build_arena.py`, textos `src/texts_arena.py`
- Paleta: Tinta #0E0E10, Lima #C4F135, Violeta #5B3FD9, Rosa #FF4F8B, Hueso #F3F2EC, Cielo #7CE0FF, Lila #C9C0F5.
- Tipografía: titulares Inter Display ExtraBold (sin cursiva) en mayúsculas/mixtas, cuerpo Inter 8,7/12,9 (propios 9,5/14,2), citas Lora Italic.
- Retícula: 4 columnas, márgenes 15, medianil 5. Anuncios: cuadros de 2 columnas (ALTURA, NÓRDICA, RITMO) con texto ceñido.
- Páginas: 1 portada (diana) · 2 índice en panel negro + editorial · 3–4 Individuales "Solos contra el reloj" (propio) · 5 Colectivos · 6 Montaña + ALTURA · 7 Invierno + NÓRDICA · 8 Precisión + RITMO · 9 Adaptado "Sin barreras" (propio) · 10 contraportada.
- Autor: `src/authors/arena_jesus_trias.json` (solo nombre y C.I.).

## ÍMPETU — `src/build_impetu.py`, textos `src/texts_impetu.py`
- Paleta: Vino #5E1A35, Mostaza #E7A82E, Verde azulado #1F6F78, Papel #EEF1F2, Tinta #1E1E24, Rosa #C8454E, Cielo #BFD9DF.
- Tipografía: titulares Lora Bold / Bold Italic (serif, mixtas), etiquetas Inter Bold, cuerpo Lora 9,4/14,2 (propios 9,8/14,8).
- Retícula: 2 columnas anchas, márgenes 18 mm, medianil 5. Anuncios: cuadros de 1 columna (TRAZO, VÉRTICE, RAÍZ).
- Páginas: 1 portada (sol retro + corredor) · 2 editorial + índice con puntos guía en panel vino · 3–4 Resistencia "Llegar más lejos" (propio) · 5 Fuerza + TRAZO · 6 Velocidad (tipografía "9,58") · 7 Equilibrio + VÉRTICE · 8 Estrategia + RAÍZ · 9 Nuestra tierra (propio) · 10 contraportada.
- Autor: aún sin datos. Para añadirlo: crear `src/authors/impetu_<nombre>.json` con `{"lineas": ["Nombre · C.I. …", "Universidad…", …]}` y pasarlo como segundo argumento en `build_all.py`.

## Cómo funciona el código
- `mag_lib.py`: helpers (texto con interletrado, párrafos, `make_frames`, `fill` que parte párrafos entre marcos, `fit` que calcula cuántos párrafos de lorem caben, escenas vectoriales de PULSO, halftone, scrims).
- Cada builder define sus páginas como funciones y las ensambla al final. Los artículos "propios" usan bucles de ajuste (`combate_fits`, `adaptado`, `balanced_y0`) para que el texto quepa y se equilibre.
- Para añadir autor a una revista: segundo argumento JSON `{"lineas": [...]}`.
- Pie de página: PULSO usa `footer` de mag_lib; ARENA `footer2`; Ímpetu `footer3`.
