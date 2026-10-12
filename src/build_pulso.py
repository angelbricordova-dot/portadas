import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mag_lib import *
from texts_pulso import EDITORIAL, TEAM, COMBAT

import json
OUT = sys.argv[1] if len(sys.argv) > 1 else "../output/PULSO.pdf"
AUTOR = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
c = cv.Canvas(OUT, pagesize=A4)
c.setTitle("PULSO – Revista de deportes (Nº 01)")
c.setSubject("Tipos de deporte")

TOP = H - 15 * mm


def DECK(col=GREY, sz=12.5):
    return ParagraphStyle("d", fontName="Serif-I", fontSize=sz, leading=sz * 1.36, textColor=col)


def report(tag, frames):
    print(tag, "libre (mm):", [round((f._y - f._y1) / mm) for f in frames])


def own_story(items):
    out = []
    for kind, s in items:
        out.append(Paragraph(s, LEAD if kind == "lead" else BODYL))
    return out


def rule(x, y, w=26 * mm, col=ORANGE, h=3):
    c.setFillColor(col); c.rect(x, y, w, h, stroke=0, fill=1)


def bg(col=CREAM):
    c.setFillColor(col); c.rect(0, 0, W, H, stroke=0, fill=1)


# ---- ilustraciones sustituibles por imágenes generadas (ver imgslots.py) ----
import imgslots, mag_lib
scene_water = imgslots.wrap(mag_lib.scene_water, "pulso", "acuaticos")
scene_extreme = imgslots.wrap(mag_lib.scene_extreme, "pulso", "extremos")
scene_athletics = imgslots.wrap(mag_lib.scene_athletics, "pulso", "atletismo")
scene_team = imgslots.wrap(mag_lib.scene_team, "pulso", "equipo_apertura")
mag_lib.SCENES["team"] = imgslots.wrap(mag_lib.scene_team, "pulso", "equipo_pagina")
mag_lib.SCENES["racket"] = imgslots.wrap(mag_lib.scene_racket, "pulso", "raqueta")
mag_lib.SCENES["combat"] = imgslots.wrap(mag_lib.scene_combat, "pulso", "combate")
# (el índice usa scene_extreme dentro de otra función: no se toca)


# ================= 01 PORTADA =================
def cover():
    bg(NAVY)
    # círculo naranja y balón sangrando por la derecha
    halftone(c, 0, H * 0.2, W * 0.62, H * 0.5, TEAL, step=9, rmax=3.6, mode="right", alpha=0.55)
    circle(c, W * 0.84, H * 0.5, W * 0.5, fill=ORANGE)
    circle(c, W * 0.84, H * 0.5, W * 0.39, fill=HexColor("#FF7A3D"))
    for i, (col, lw, ln) in enumerate([(YELLOW, 7, 0.34), (TEAL, 4, 0.42), (white, 2.4, 0.3), (YELLOW, 4, 0.38), (TEAL, 7, 0.26)]):
        yy = H * 0.5 + 24 - i * 17
        line(c, W * 0.02, yy, W * (0.02 + ln), yy, col, lw)
    ball(c, W * 0.8, H * 0.5, W * 0.3)
    # cabecera: logotipo a todo el ancho
    ms = fit_size("PULSO", "Disp-I", W - 2 * M, cs=-4)
    text(c, "PULSO", M - 3, H - 15 * mm - ms * 0.727, "Disp-I", ms, white, cs=-4)
    ybase = H - 15 * mm - ms * 0.727 - 11 * mm
    text(c, "REVISTA DE DEPORTES", M, ybase, "Sans-B", 10.5, YELLOW, cs=6.5)
    text(c, "OCTUBRE 2026", W - M, ybase, "Sans-B", 10.5, white, "r", cs=3)
    c.setFillColor(YELLOW); c.rect(M, ybase - 5 * mm, W - 2 * M, 1.2, stroke=0, fill=1)
    # insignia del número
    bx, by = M + 17 * mm, ybase - 40 * mm
    circle(c, bx, by, 16 * mm, fill=YELLOW)
    text(c, "Nº", bx, by + 4.2 * mm, "Sans-B", 9, NAVY, "c", cs=2)
    text(c, "01", bx, by - 8 * mm, "Disp-I", 30, NAVY, "c", cs=-1)
    # titulares inferiores
    scrim(c, 0, 0, W, 112 * mm, color=NAVY, amax=0.95)
    kicker(c, "Especial · los tipos de deporte", M, 80 * mm, ORANGE)
    title_block(c, ["Seis maneras", "de moverse"], M, 64 * mm, 46, white, lead=0.9, cs=-1.2)
    items = [("03", "Ganar juntos", "la fuerza de los deportes de equipo"),
             ("07", "Disciplina antes que fuerza", "el mundo del combate"),
             ("08", "Al límite", "adrenalina con preparación")]
    for i, (n, t, d) in enumerate(items):
        yy = 27 * mm - i * 7.4 * mm
        text(c, n, M, yy, "Disp-I", 12.5, ORANGE)
        tw = pdfmetrics.stringWidth(t.upper(), "Sans-B", 8.4) + 1.1 * len(t)
        text(c, t.upper(), M + 11 * mm, yy + 0.2, "Sans-B", 8.4, white, cs=1.1)
        text(c, d, M + 11 * mm + tw + 3 * mm, yy + 0.2, "Serif-I", 9.4, HexColor("#B9C6DD"))




# ================= 02 EDITORIAL + ÍNDICE =================
PANEL_H = 146 * mm


def editorial_indice():
    bg()
    sx = colx(2)
    # panel marino lateral (columna 3) a sangre arriba
    c.setFillColor(NAVY); c.rect(sx - 4 * mm, H - PANEL_H, W - sx + 4 * mm, PANEL_H, stroke=0, fill=1)
    clip_rect(c, sx - 4 * mm, H - PANEL_H, W - sx + 4 * mm, PANEL_H)
    halftone(c, sx - 4 * mm, H - PANEL_H, W - sx + 4 * mm, 70 * mm, ORANGE, step=8, rmax=3.2, mode="bottom", alpha=0.9)
    circle(c, sx + CW * 0.5, H - PANEL_H + 22 * mm, CW * 0.8, fill=ORANGE)
    ball(c, sx + CW * 0.54, H - PANEL_H + 22 * mm, CW * 0.55)
    c.restoreState()
    text(c, "“", sx, TOP - 22 * mm, "Disp-I", 80, ORANGE)
    para(c, "El deporte no se mira,<br/>se vive.", ParagraphStyle("q", fontName="Serif-BI", fontSize=20, leading=25, textColor=white),
         sx, TOP - 28 * mm, CW)
    kicker(c, "Carta de la redacción", M, TOP - 4 * mm)
    es = fit_size("EDITORIAL", "Disp-I", 2 * CW + G, maxsize=58, cs=-1.6)
    text(c, "EDITORIAL", M - 2, TOP - 22 * mm, "Disp-I", es, NAVY, cs=-1.6)
    rule(M, TOP - 28 * mm)
    EB = ParagraphStyle("eb", parent=BODY, fontSize=9.2, leading=13, spaceAfter=5)
    st = [Paragraph(EDITORIAL[0], ParagraphStyle("e0", parent=LEAD, fontSize=11, leading=15.4, spaceAfter=7))]
    st += [Paragraph(p, EB) for p in EDITORIAL[1:4]]
    st += [Paragraph("<b>Gracias por leernos.</b>", EB),
           Paragraph('<font name="Sans-B" size="7" color="#FF5A1F">—  LA REDACCIÓN</font>', BODY)]
    frames = make_frames(M, H - PANEL_H + 2 * mm, M + 2 * CW + G, TOP - 33 * mm, ncols=2)
    fill(c, st, frames); report("editorial", frames)
    assert not st, "editorial desborda"

    # ---- índice ----
    y0 = H - PANEL_H - 12 * mm
    kicker(c, "En este número", M, y0)
    title_block(c, ["Índice"], M - 2, y0 - 17 * mm, 40, NAVY, cs=-1.2)
    rule(M, y0 - 23 * mm)
    rows = [("02", "Editorial", "Una invitación a conocer los tipos de deporte."),
            ("03", "Deportes de equipo", "Ganar juntos: roles, comunicación y valores."),
            ("05", "Deportes de raqueta", "Velocidad y precisión en cada punto."),
            ("06", "Deportes acuáticos", "Bajo y sobre el agua."),
            ("07", "Deportes de combate", "Disciplina antes que fuerza."),
            ("08", "Deportes extremos", "Al límite, con preparación."),
            ("09", "Atletismo", "Correr, saltar y lanzar.")]
    colw = (W - 2 * M - 8 * mm) / 2
    ytop = y0 - 32 * mm
    rh = 20 * mm
    for i, (n, t, d) in enumerate(rows):
        cx = M if i < 4 else M + colw + 8 * mm
        yy = ytop - (i if i < 4 else i - 4) * rh
        text(c, n, cx, yy - 10, "Disp-I", 28, ORANGE, cs=-1)
        text(c, t.upper(), cx + 19 * mm, yy - 1, "Disp-X", 11.2, NAVY, cs=0.5)
        text(c, d, cx + 19 * mm, yy - 11.5, "Serif-I", 8.6, GREY)
        c.setStrokeColor(LGREY); c.setLineWidth(0.6)
        c.line(cx, yy - 16, cx + colw, yy - 16)
    if AUTOR:
        cx = M + colw + 8 * mm
        yy = ytop - 3 * rh
        c.setFillColor(NAVY); c.rect(cx, yy - 22 * mm, colw, 23.5 * mm, stroke=0, fill=1)
        c.setFillColor(ORANGE); c.rect(cx, yy + 1.5 * mm - 2.2, 12 * mm, 2.2, stroke=0, fill=1)
        lines = AUTOR["lineas"]
        n = len(lines)
        text(c, "REVISTA ELABORADA POR", cx + 4 * mm, yy - 3.2 * mm, "Sans-B", 5.8, ORANGE, cs=1.4)
        for j, s in enumerate(lines):
            text(c, s, cx + 4 * mm, yy - 8 * mm - j * 3.2 * mm, "Sans", 6.4 if j else 7.6, white if j else YELLOW)
    footer(c, 2)
    c.showPage()


# ================= ANUNCIOS (franja inferior) =================
AH = 78 * mm          # alto de la franja publicitaria
AGAP = 7 * mm         # separación entre artículo y anuncio


def ad_disclaimer(col):
    text(c, "Anuncio ficticio realizado con fines académicos.", M, 19.2 * mm, "Sans", 5.8, col)


def button(x, y, w, label, fillc, txtc):
    c.setFillColor(fillc); c.roundRect(x, y, w, 8.5 * mm, 4.25 * mm, stroke=0, fill=1)
    text(c, label, x + w / 2, y + 3.0 * mm, "Sans-B", 7.6, txtc, "c", cs=1.2)


def ad_hydra_strip(pageno):
    c.saveState()
    p = c.beginPath(); p.rect(0, 0, W, AH); c.clipPath(p, stroke=0, fill=0)
    grad_bands(c, 0, 0, W, AH, (10, 95, 170), (6, 25, 70), 40)
    c.setStrokeColor(white); c.setLineWidth(1)
    for k in range(5):
        yy = AH * (0.15 + 0.17 * k)
        pp = c.beginPath(); pp.moveTo(0, yy)
        for i in range(1, 91):
            pp.lineTo(W * i / 90, yy + math.sin(i / 90 * 12 + k) * 5)
        c.drawPath(pp, stroke=1, fill=0)
    text(c, "HYDRA", M, AH - 12 * mm, "Disp-I", 14, white, cs=3)
    title_block(c, ["Rinde hasta", "el final."], M - 2, AH - 25 * mm, 38, white, lead=0.88, cs=-1.2)
    para(c, "Bebida isotónica con electrolitos para entrenar, competir y recuperarte.",
         ParagraphStyle("hy", fontName="Serif-I", fontSize=9.6, leading=12.8, textColor=white), M, 36 * mm, 78 * mm)
    # botella
    bx, by = W * 0.64, 21.5 * mm
    c.saveState(); c.translate(bx, by); c.scale(0.62, 0.62)
    c.setFillColor(HexColor("#E8F6FF")); c.roundRect(0, 0, 78, 230, 22, stroke=0, fill=1)
    c.setFillColor(TEAL); c.roundRect(6, 6, 66, 150, 18, stroke=0, fill=1)
    c.setFillColor(YELLOW); c.roundRect(14, 226, 50, 30, 7, stroke=0, fill=1)
    c.setFillColor(white); c.rect(6, 80, 66, 48, stroke=0, fill=1)
    text(c, "HYDRA", 39, 98, "Disp-I", 13, NAVY, "c", cs=0.8)
    c.restoreState()
    for (dx, dy, r) in [(-14, 30, 5), (-22, 70, 3.4), (74, 40, 5.5), (86, 92, 3.5)]:
        circle(c, bx + dx, by + dy, r, fill=None, stroke=white, lw=1.4)
    button(W - M - 44 * mm, 36 * mm, 44 * mm, "PRUÉBALA HOY", YELLOW, NAVY)
    ad_disclaimer(HexColor("#9FB0C8"))
    c.restoreState()
    footer(c, pageno, dark=True)


def ad_atlas_strip(pageno):
    DK = HexColor("#101010")
    c.saveState()
    p = c.beginPath(); p.rect(0, 0, W, AH); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(DK); c.rect(0, 0, W, AH, stroke=0, fill=1)
    c.setStrokeColor(YELLOW); c.setLineWidth(2.4)
    for i in range(10):
        c.line(W * 0.52 + i * 38, -10, W * 0.52 + i * 38 + 130, AH + 10)
    c.setFillColor(DK); c.rect(0, 0, W * 0.56, AH, stroke=0, fill=1)
    text(c, "ATLAS GYM", M, AH - 12 * mm, "Disp-I", 14, YELLOW, cs=3)
    title_block(c, ["Tu mejor versión", "empieza hoy."], M - 2, AH - 23.5 * mm, 30, white, lead=0.9, cs=-0.9)
    para(c, "Máquinas, pesas libres y entrenadores que te acompañan en cada serie.",
         ParagraphStyle("at", fontName="Serif-I", fontSize=9.6, leading=12.8, textColor=white), M, 41 * mm, 98 * mm)
    button(M, 22.5 * mm, 56 * mm, "PRIMERA SEMANA GRATIS", YELLOW, DK)
    # barra con discos
    cy = 46 * mm
    c.setFillColor(HexColor("#B0B0B0")); c.roundRect(W * 0.58, cy - 2.2 * mm, W * 0.38, 4.4 * mm, 2, stroke=0, fill=1)
    for dx, wd, ht in [(W * 0.60, 7 * mm, 38 * mm), (W * 0.60 + 8.5 * mm, 5.5 * mm, 29 * mm),
                       (W * 0.94 - 7 * mm, 7 * mm, 38 * mm), (W * 0.94 - 13.5 * mm, 5.5 * mm, 29 * mm)]:
        c.setFillColor(YELLOW); c.roundRect(dx, cy - ht / 2, wd, ht, 2, stroke=0, fill=1)
    ad_disclaimer(HexColor("#9A9A9A"))
    c.restoreState()
    footer(c, pageno, dark=True)


def ad_veloz_strip(pageno):
    c.saveState()
    p = c.beginPath(); p.rect(0, 0, W, AH); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(ORANGE); c.rect(0, 0, W, AH, stroke=0, fill=1)
    for i in range(10):
        c.setStrokeColor(HexColor("#FF7A3D" if i % 2 else "#E8481A")); c.setLineWidth(14)
        c.circle(W * 0.86, 4 * mm, 30 + i * 26, stroke=1, fill=0)
    text(c, "VELOZ", M, AH - 12 * mm, "Disp-I", 14, white, cs=3)
    title_block(c, ["Corre más", "lejos."], M - 2, AH - 24 * mm, 38, white, lead=0.88, cs=-1.4)
    para(c, "Ligeras. Resistentes. Para tu próximo kilómetro.",
         ParagraphStyle("ve", fontName="Serif-I", fontSize=9.6, leading=12.8, textColor=white), M, 40 * mm, 100 * mm)
    button(M, 22.5 * mm, 46 * mm, "DESCÚBRELAS HOY", YELLOW, NAVY)
    c.saveState(); c.translate(W * 0.55, 27 * mm); c.rotate(8); c.scale(0.58, 0.58)
    poly(c, [(0, 0), (300, 0), (330, 18), (318, 34), (0, 34)], fill=white)
    c.setFillColor(NAVY)
    pp = c.beginPath(); pp.moveTo(8, 34); pp.curveTo(10, 120, 60, 150, 110, 140)
    pp.curveTo(150, 132, 160, 100, 200, 96); pp.curveTo(260, 92, 310, 70, 316, 34); pp.close()
    c.drawPath(pp, fill=1, stroke=0)
    c.setStrokeColor(YELLOW); c.setLineWidth(10); c.setLineCap(1)
    c.line(60, 40, 150, 100); c.line(120, 40, 210, 90)
    for i in range(5):
        circle(c, 130 + i * 22, 112 - i * 3, 4, fill=white)
    c.restoreState()
    ad_disclaimer(HexColor("#FFE2D2"))
    c.restoreState()
    footer(c, pageno, dark=True, numcol=NAVY)


# ================= 06 ACUÁTICOS + HYDRA =================
IH6 = 100 * mm


def p6_agua_frames():
    ytop = H - IH6 - 24 * mm
    ib_h = 12 * mm + 7.2 * mm * 5 + 2.5 * mm
    box = (colx(2), ytop - ib_h, W - M, ytop)
    return make_frames(M, AH + AGAP, W - M, ytop, 3, obst=[box])


def agua_page(story):
    bg()
    scene_water(c, 0, H - IH6, W, IH6)
    scrim(c, 0, H - IH6, W, 66 * mm, color=NAVY, amax=0.96)
    c.saveState(); c.setFillColor(NAVY); c.setFillAlpha(0.9)
    c.rect(M - 2 * mm, H - IH6 + 36.2 * mm, 62 * mm, 6 * mm, stroke=0, fill=1); c.restoreState()
    kicker(c, "Deportes acuáticos", M, H - IH6 + 38 * mm, YELLOW)
    title_block(c, ["Bajo y sobre", "el agua"], M - 2, H - IH6 + 24 * mm, 44, white, lead=0.9, cs=-1.1)
    para(c, "Natación, waterpolo, clavados y surf: el reto de moverse en un medio que no perdona.", DECK(INK, 12.2), M, H - IH6 - 6 * mm, W - 2 * M)
    ytop = H - IH6 - 24 * mm
    infobox(c, colx(2), ytop, CW, "Cinco disciplinas",
            [("Natación", "carriles"), ("Waterpolo", "equipos"), ("Clavados", "plataforma"), ("N. artística", "música"), ("Surf", "olas")])
    fr = p6_agua_frames()
    fill(c, story, fr); report("agua", fr)
    ad_hydra_strip(6)
    c.showPage()


# ================= 07 COMBATE (texto propio) =================
CBH = [118 * mm]
CB_IB_H = 12 * mm + 7.2 * mm * 4 + 2.5 * mm


def p7_frames():
    ih = CBH[0]
    img = (colx(1), H - 88 * mm - ih, W - M, H - 88 * mm)
    box = (M, BOT + 4 * mm, M + CW, BOT + 4 * mm + CB_IB_H)
    return make_frames(M, BOT, W - M, H - 82 * mm, 3, obst=[(img[0], img[1] - 10 * mm, img[2], img[3]), box])


def combate_fits():
    for ih in range(118, 60, -2):
        CBH[0] = ih * mm
        st = own_story(COMBAT)
        st.insert(0, Paragraph("POR LA REDACCIÓN   ·   4 MIN DE LECTURA", BYL))
        fill(cv.Canvas(io.BytesIO()), st, p7_frames())
        if not st:
            return ih
    raise SystemExit("combate no cabe")


def combate_page():
    ih = combate_fits(); print("combate: alto imagen", ih, "mm")
    story = own_story(COMBAT)
    bg()
    c.setFillColor(RED); c.rect(0, H - 78 * mm, W, 78 * mm, stroke=0, fill=1)
    text(c, "07", W - M + 4 * mm, H - 66 * mm, "Disp-I", 210, HexColor("#D8444A"), "r", cs=-8)
    kicker(c, "Deportes de combate", M, H - 18 * mm, YELLOW)
    title_block(c, ["Disciplina antes", "que fuerza"], M - 2, H - 38 * mm, 52, white, lead=0.9, cs=-1.2)
    para(c, "Boxeo, judo, taekwondo y karate: el arte de controlar el cuerpo y la mente.", DECK(white, 12.4), M, H - 61 * mm, CW * 1.55)
    story.insert(0, Paragraph("POR LA REDACCIÓN   ·   4 MIN DE LECTURA", BYL))
    ix0 = colx(1)
    image_block(c, "combat", ix0, H - 88 * mm - CBH[0], W - M - ix0, CBH[0], "Guantes, protectores y árbitro: las reglas hacen posible el combate.")
    infobox(c, M, BOT + 4 * mm + CB_IB_H, CW, "Origen de 4 disciplinas",
            [("Judo", "Japón"), ("Taekwondo", "Corea"), ("Karate", "Okinawa"), ("Muay thai", "Tailandia")])
    fr = p7_frames()
    fill(c, story, fr); report("combate", fr)
    assert not story
    footer(c, 7)
    c.showPage()


# ================= 08 EXTREMOS + ATLAS =================
IH8 = 106 * mm


def p8_frames():
    ytop = H - IH8 - 22 * mm
    ib_h = 12 * mm + 7.2 * mm * 4 + 2.5 * mm
    box = (colx(2), ytop - ib_h, W - M, ytop)
    return make_frames(M, AH + AGAP, W - M, ytop, 3, obst=[box])


def extremos_page(story):
    bg()
    scene_extreme(c, 0, H - IH8, W, IH8)
    scrim(c, 0, H - IH8, W, 56 * mm, color=NAVY, amax=0.9)
    kicker(c, "Deportes extremos", M, H - IH8 + 38 * mm, YELLOW)
    ts = fit_size("AL LÍMITE", "Disp-I", W - 2 * M - 30 * mm, maxsize=84, cs=-2)
    text(c, "AL LÍMITE", M - 2, H - IH8 + 12 * mm, "Disp-I", ts, white, cs=-2)
    para(c, "Escalada, paracaidismo, surf de olas grandes y más: adrenalina con preparación.", DECK(INK, 12.2), M, H - IH8 - 6 * mm, W - 2 * M)
    ytop = H - IH8 - 22 * mm
    infobox(c, colx(2), ytop, CW, "Equipo básico",
            [("Escalada", "arnés"), ("Paracaidismo", "paracaídas"), ("Snowboard", "casco"), ("Surf", "tabla")])
    fr = p8_frames()
    fill(c, story, fr); report("extremos", fr)
    ad_atlas_strip(8)
    c.showPage()


# ================= 09 ATLETISMO + VELOZ =================
BAND9 = 62 * mm
SC9 = 56 * mm


def p9_frames():
    return make_frames(M, AH + AGAP, W - M, H - BAND9 - SC9 - 14 * mm, 3)


def atletismo_page(story):
    bg()
    c.setFillColor(NAVY); c.rect(0, H - BAND9, W, BAND9, stroke=0, fill=1)
    halftone(c, W * 0.45, H - BAND9, W * 0.55, BAND9, ORANGE, step=8, rmax=3.2, mode="right", alpha=0.9)
    kicker(c, "Atletismo", M, H - 17 * mm, YELLOW)
    title_block(c, ["Correr, saltar,", "lanzar"], M - 2, H - 34 * mm, 46, white, lead=0.9, cs=-1.2)
    para(c, "La base de casi todos los deportes: pista, campo y carretera.", DECK(white, 12.2), M, H - 52 * mm, CW * 2.3)
    scene_athletics(c, 0, H - BAND9 - SC9, W, SC9)
    c.setFillColor(ORANGE); c.rect(M, H - BAND9 - SC9 - 2 * mm - 6.4, 2.2, 6.4, stroke=0, fill=1)
    para(c, "Cada carril, cada salto y cada lanzamiento tiene su técnica.", CAP, M + 4 * mm, H - BAND9 - SC9 - 2 * mm, W - 2 * M)
    fr = p9_frames()
    fill(c, story, fr); report("atletismo", fr)
    ad_veloz_strip(9)
    c.showPage()


# ================= 10 CONTRAPORTADA =================
def contraportada():
    bg(NAVY)
    halftone(c, 0, 0, W, H * 0.6, TEAL, step=9, rmax=3.4, mode="bottom", alpha=0.45)
    circle(c, W * 0.5, H * 0.45, W * 0.38, fill=ORANGE)
    circle(c, W * 0.5, H * 0.45, W * 0.28, fill=HexColor("#FF7A3D"))
    ball(c, W * 0.5, H * 0.45, W * 0.19)
    for i, col in enumerate([TEAL, YELLOW, white]):
        line(c, 0, H * 0.45 + 18 - i * 14, W * 0.2, H * 0.45 + 18 - i * 14, col, 4)
    kicker(c, "Próximo número", M, H - 22 * mm, ORANGE)
    s1, s2 = "¿Y SI EL PRÓXIMO", "DEPORTE LO ELIGES TÚ?"
    sz = fit_size(s2, "Disp-I", W - 2 * M, maxsize=60, cs=-1.2)
    text(c, s1, M - 1, H - 46 * mm, "Disp-I", sz, white, cs=-1.2)
    text(c, s2, M - 1, H - 46 * mm - sz * 1.02, "Disp-I", sz, white, cs=-1.2)
    ms = fit_size("PULSO", "Disp-I", W - 2 * M, maxsize=120, cs=-3)
    text(c, "PULSO", W / 2, 38 * mm, "Disp-I", ms * 0.62, white, "c", cs=-2)
    text(c, "REVISTA DE DEPORTES", W / 2, 27 * mm, "Sans-B", 8.6, YELLOW, "c", cs=5.5)
    text(c, "Nº 01   ·   OCTUBRE 2026", W / 2, 17.5 * mm, "Sans-SB", 7, white, "c", cs=2)
    c.showPage()

# ================= 04-05 ARTÍCULO 1 (texto propio) =================
IH4 = 222 * mm


def p4_frames():
    return make_frames(M, BOT, W - M, H - IH4 - 7 * mm, ncols=3)


TEAM_IB_H = 12 * mm + 7.2 * mm * 6 + 2.5 * mm


def p5_frames():
    y1 = H - 18 * mm
    img = (colx(1), y1 - 44 * mm - 140 * mm, W - M, y1 - 44 * mm)
    box = (colx(2), BOT + 4 * mm, W - M, BOT + 4 * mm + TEAM_IB_H)
    return make_frames(M, BOT, W - M, y1 - 44 * mm, ncols=3, obst=[(img[0], img[1] - 10 * mm, img[2], img[3]), box])


def team_pages(story):
    bg()
    scene_team(c, 0, H - IH4, W, IH4)
    scrim(c, 0, H - IH4, W, 92 * mm, color=NAVY, amax=0.94)
    kicker(c, "Deportes de equipo", M, H - IH4 + 66 * mm, YELLOW)
    ts = fit_size("GANAR JUNTOS", "Disp-I", W - 2 * M, maxsize=78, cs=-1.5)
    text(c, "GANAR JUNTOS", M - 2, H - IH4 + 40 * mm, "Disp-I", ts, white, cs=-1.5)
    para(c, "Fútbol, baloncesto, voleibol y más: cuando el resultado depende de todos.", DECK(white, 13.2),
         M, H - IH4 + 31 * mm, W - 2 * M - 50 * mm)
    story.insert(0, Paragraph("POR LA REDACCIÓN   ·   4 MIN DE LECTURA", BYL))
    fr = p4_frames()
    fill(c, story, fr); report("equipo p4", fr)
    footer(c, 3)
    c.showPage()
    bg()
    y1 = H - 18 * mm
    kicker(c, "Deportes de equipo · continúa", M, H - 12 * mm, GREY, rule=False)
    quote(c, "El talento abre puertas, pero es el equipo el que las mantiene abiertas.", M, y1 - 2 * mm, W - 2 * M, 36 * mm, size=19)
    ix0, iy1 = colx(1), y1 - 44 * mm
    image_block(c, "team", ix0, iy1 - 140 * mm, W - M - ix0, 140 * mm, "Un partido se gana mucho antes del pitazo inicial: en la preparación del grupo.")
    infobox(c, colx(2), BOT + 4 * mm + TEAM_IB_H, CW, "Jugadores por equipo",
            [("Fútbol", "11"), ("Baloncesto", "5"), ("Voleibol", "6"), ("Béisbol (defensa)", "9"), ("Balonmano", "7"), ("Rugby (unión)", "15")])
    fr = p5_frames()
    fill(c, story, fr); report("equipo p5", fr)
    assert not story, "equipo desborda %d" % len(story)
    footer(c, 4)
    c.showPage()

# ================= 06 RAQUETA =================
def p6_frames():
    ix0 = colx(1)
    img = (ix0, TOP - 90 * mm - 70 * mm, W - M, TOP - 90 * mm)
    ib_h = 12 * mm + 7.2 * mm * 4 + 2.5 * mm
    box = (M, BOT + 4 * mm, M + CW, BOT + 4 * mm + ib_h)
    return make_frames(M, BOT, W - M, TOP - 84 * mm, 3, obst=[(img[0], img[1] - 10 * mm, img[2], img[3]), box])


def raqueta_page(story):
    bg()
    kicker(c, "Deportes de raqueta", M, TOP - 4 * mm)
    title_block(c, ["Velocidad", "y precisión"], M - 2, TOP - 28 * mm, 58, NAVY, cs=-1.4)
    rule(M, TOP - 53 * mm)
    para(c, "Tenis, bádminton, pádel y squash: la lucha por el control del punto.", DECK(GREY, 12.6), M, TOP - 58 * mm, CW * 1.15)
    ix0 = colx(1)
    image_block(c, "racket", ix0, TOP - 90 * mm - 70 * mm, W - M - ix0, 70 * mm, "El golpe perfecto es el resultado de miles de repeticiones.")
    ib_h = 12 * mm + 7.2 * mm * 4 + 2.5 * mm
    infobox(c, M, BOT + 4 * mm + ib_h, CW, "Cuatro raquetas", [("Tenis", "pelota"), ("Bádminton", "volante"), ("Pádel", "paredes"), ("Squash", "pared frontal")])
    fr = p6_frames()
    fill(c, story, fr); report("raqueta", fr)
    footer(c, 5)
    c.showPage()



# ================= ENSAMBLADO =================
cover(); c.showPage()
editorial_indice()
team_pages(own_story(TEAM))
k = fit(lambda n: lorem_story(11, n), [p6_frames]); raqueta_page(lorem_story(11, k))
k = fit(lambda n: lorem_story(22, n), [p6_agua_frames]); agua_page(lorem_story(22, k))
combate_page()
k = fit(lambda n: lorem_story(33, n), [p8_frames]); extremos_page(lorem_story(33, k))
k = fit(lambda n: lorem_story(44, n), [p9_frames]); atletismo_page(lorem_story(44, k))
contraportada()
c.save()
print("OK ->", OUT)
