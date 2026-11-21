# -*- coding: utf-8 -*-
"""Pitch deck INSATECH - BRC-M400 (16:9 PDF, 5 min). Run with system python (PyMuPDF)."""
import os
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import Deck, W, H, M, hx, NAVY, BLUE, ORANGE, GREY, HAIR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.normpath(os.path.join(HERE, "..", "02_PRESENTATION",
                                    "INSATECH_BRC-M400_presentation.pdf"))
R3D = os.path.join(ROOT, "02_ELECTRONIQUE", "exports", "3d")
FIG = os.path.join(ROOT, "03_SIMULATION", "electronique", "figures")
R = pymupdf.Rect

d = Deck(OUT)

# ---------------------------------------------------------------- 1. titre
pg = d.slide(dark=True)
pg.draw_rect(R(0, 0, W * 0.52, H), color=None, fill=hx("#0B1620"))
d.image(R(W * 0.50, 0, W, H), os.path.join(R3D, "BRC-M400_iso.png"), dark_panel=True)
pg.draw_rect(R(W * 0.50, 0, W * 0.535, H), color=None, fill=hx("#0B1620"))
d.html(R(M, 150, W * 0.50 - 10, 400),
       '<div style="font-size:13px;color:#6E8CA8;letter-spacing:2px">TUNISIAN AERODAY V14 &nbsp;&middot;&nbsp; CHALLENGE CAO</div>'
       '<div style="font-size:52px;font-weight:bold;color:#FFFFFF;line-height:1.05;margin-top:14px">BRC-M400</div>'
       '<div style="font-size:19px;color:#AFC4D6;margin-top:6px">Système de largage de bouée'
       '<br/>et balise de détresse</div>'
       '<div style="font-size:13.5px;color:#7E97AD;margin-top:20px">Emport sous DJI Matrice 400 — port E-Port V2</div>')
pg.draw_line(pymupdf.Point(M, 432), pymupdf.Point(M + 150, 432), color=hx("#BF5700"), width=2.4)
d.html(R(M, 446, W * 0.50 - 10, 510),
       '<div style="font-size:22px;font-weight:bold;color:#FFFFFF">Équipe INSATECH</div>'
       '<div style="font-size:12px;color:#7E97AD;margin-top:3px">22 novembre 2026 &middot; Révision C</div>')

# ---------------------------------------------------------------- 2. mission
d.slide("Larguer 1 kg en sécurité, puis rendre la bouée repérable", kicker="Le défi")
d.html(R(M, 128, 500, 430),
       '<p>Lors d\'une <b>inondation</b> ou d\'un <b>tsunami</b>, l\'intervention aérienne est souvent '
       'le seul accès rapide aux sinistrés. Le drone doit pouvoir <b>déposer une bouée</b> au plus '
       'près d\'une victime, puis repartir.</p>'
       '<p>Trois exigences commandent toute la conception :</p>'
       '<ul>'
       '<li><b>Ne jamais lâcher par accident.</b> En vol, sous forte accélération verticale, la charge '
       'reste tenue — y compris si tout tombe en panne.</li>'
       '<li><b>Larguer de façon certaine, et le savoir.</b> Le pilote doit avoir la <b>confirmation</b> '
       'que la bouée est partie.</li>'
       '<li><b>Rester repérable au sol.</b> Une balise lumineuse et sonore s\'allume après le largage.</li>'
       '</ul>')
d.panel(R(530, 128, W - M, 430), fill="#F4F7FA")
d.html(R(552, 146, W - M - 22, 420),
       '<div style="font-size:12px;color:#1565C0;letter-spacing:.5px">CONTRAINTES DIMENSIONNANTES</div>'
       '<table style="width:100%;border-collapse:collapse;margin-top:10px">'
       '<tr><td style="border:none;padding:6px 0"><span class="num">1 kg</span><br/>'
       '<span class="k">charge utile larguée</span></td>'
       '<td style="border:none;padding:6px 0"><span class="num">5 A</span><br/>'
       '<span class="k">limite du port E-Port V2 (24 V)</span></td></tr>'
       '<tr><td style="border:none;padding:6px 0"><span class="num">0</span><br/>'
       '<span class="k">batterie embarquée</span></td>'
       '<td style="border:none;padding:6px 0"><span class="num">15 km</span><br/>'
       '<span class="k">portée radio visée</span></td></tr>'
       '</table>'
       '<p style="margin-top:14px;font-size:12px;color:#5A6672">Le système est alimenté et commandé '
       'par le drone : la masse larguée est la bouée seule.</p>')

# ---------------------------------------------------------------- 3. architecture
d.slide("Architecture du système", kicker="Vue d'ensemble")
bw, bh, top = 150, 62, 170
cols = [M + i * 178 for i in range(5)]
blocks = [("DJI Matrice 400", "E-Port V2 · 24 V · UART", "#53616E"),
          ("Alimentation", "LM74700 · LMR51430", "#BF5700"),
          ("Calculateur", "STM32U585 · PSDK", "#1565C0"),
          ("Radio LoRa", "SX1262 · 868 MHz", "#6A1B9A"),
          ("Balise", "LED + sirène", "#B71C1C")]
for (t1, t2, c), x in zip(blocks, cols):
    d.chip(x, top, bw, bh, '%s<div style="font-size:10.5px;font-weight:normal;margin-top:3px">%s</div>'
           % (t1, t2), c, size=13)
for i in range(3):
    d.arrow(cols[i] + bw, top + bh / 2, cols[i + 1] - 4, top + bh / 2)
d.arrow(cols[3] + bw, top + bh / 2, cols[4] - 4, top + bh / 2)
# second row: actuators + sensors
y2 = top + 128
d.chip(cols[1], y2, bw, bh, 'Actionneurs<div style="font-size:10.5px;font-weight:normal;margin-top:3px">'
       'aimant · solénoïde</div>', "#2E7D32", size=13)
d.chip(cols[3], y2, bw, bh, 'Capteurs<div style="font-size:10.5px;font-weight:normal;margin-top:3px">'
       'verrou · présence · courants</div>', "#00695C", size=13)
d.arrow(cols[2] + 40, top + bh, cols[1] + bw / 2 + 20, y2 - 4, color=hx("#2E7D32"))
d.arrow(cols[3] + bw / 2, y2 - 4, cols[2] + bw - 36, top + bh, color=hx("#00695C"))
d.html(R(cols[1] + bw + 8, y2 + 6, cols[3] - 8, y2 + 50),
       '<div style="text-align:center;font-size:11px;color:#5A6672">PWM · ARM · mesure de courant '
       '&nbsp;&nbsp;|&nbsp;&nbsp; retour d\'état</div>')
d.panel(R(M, 420, W - M, 476), fill="#F4F7FA")
d.html(R(M + 18, 432, W - M - 18, 474),
       '<div style="font-size:12.5px;color:#19222B"><b>Deux chemins de commande indépendants :</b> '
       'le bouton « LARGUER » de DJI Pilot 2 via le PSDK, et la liaison LoRa directe depuis le sol — '
       'si l\'un tombe, l\'autre reste.</div>')

# ---------------------------------------------------------------- 4. sûreté
d.slide("L'état sûr, c'est l'état non alimenté", kicker="Sûreté par construction")
d.panel(R(M, 128, 466, 420), fill="#FFFFFF", border="#C9D2DA")
d.html(R(M + 20, 142, 446, 200),
       '<div style="font-size:15px;font-weight:bold;color:#12355B">1 — Aimant de maintien à sécurité positive</div>')
# fail-safe magnet diagram
bx, by = M + 24, 196
d.chip(bx, by, 180, 46, 'Bobine<br/><span style="font-size:10px;font-weight:normal">NON alimentée</span>',
       "#ECEFF1", tcolor="#19222B", size=12)
d.chip(bx + 212, by, 180, 46, 'Bobine<br/><span style="font-size:10px;font-weight:normal">alimentée</span>',
       "#BF5700", size=12)
d.html(R(bx, by + 56, bx + 180, by + 116),
       '<div style="text-align:center"><span class="ok" style="font-size:14px">BOUÉE TENUE</span>'
       '<div class="cap" style="margin-top:4px">l\'aimant permanent travaille seul</div></div>')
d.html(R(bx + 212, by + 56, bx + 392, by + 116),
       '<div style="text-align:center"><span class="hi" style="font-size:14px">BOUÉE LIBÉRÉE</span>'
       '<div class="cap" style="margin-top:4px">le champ de la bobine annule l\'aimant</div></div>')
d.html(R(M + 20, by + 122, 446, 414),
       '<p style="font-size:12.5px">Conséquence directe : <b>panne d\'alimentation, reset du '
       'calculateur ou perte de liaison &rarr; la bouée reste accrochée.</b></p>')
d.panel(R(494, 128, W - M, 420), fill="#FFFFFF", border="#C9D2DA")
d.html(R(514, 142, W - M - 20, 200),
       '<div style="font-size:15px;font-weight:bold;color:#12355B">2 — Double barrière ARM / FIRE</div>')
# ARM/FIRE chain
cx = 514
d.chip(cx, 196, 112, 44, 'VIN 24 V', "#53616E", size=12)
d.chip(cx + 130, 196, 112, 44, 'ARM<br/><span style="font-size:9.5px;font-weight:normal">P-MOSFET</span>',
       "#1565C0", size=12)
d.chip(cx + 260, 196, 112, 44, 'FIRE<br/><span style="font-size:9.5px;font-weight:normal">étage bas</span>',
       "#B71C1C", size=12)
d.arrow(cx + 112, 218, cx + 126, 218)
d.arrow(cx + 242, 218, cx + 256, 218)
d.html(R(514, 252, W - M - 20, 414),
       '<p style="font-size:12.5px">Le largage exige <b>les deux étages à la fois</b> : un interrupteur '
       'côté haut qui alimente le rail actionneurs, et l\'étage côté bas de la voie concernée.</p>'
       '<p style="font-size:12.5px"><b>Aucun défaut unique</b> — broche du microcontrôleur qui bascule, '
       'MOSFET en court-circuit, parasite sur une piste — <b>ne peut provoquer un largage.</b></p>'
       '<p style="font-size:12px;color:#5A6672">S\'y ajoute un verrouillage logiciel : le largage n\'est '
       'autorisé que dans un domaine d\'altitude et de vitesse lu sur la télémétrie du drone.</p>')

# ---------------------------------------------------------------- 5. séquence
d.slide("Le largage se déroule — et se prouve — en 24 ms", kicker="Séquence et confirmation")
ty = 190
pg = d.page
pg.draw_line(pymupdf.Point(M + 20, ty), pymupdf.Point(W - M - 20, ty), color=hx("#C9D2DA"), width=1.4)
steps = [(M + 20, "0 ms", "ARMER", "barrière haute fermée", "#1565C0"),
         (M + 225, "+0 ms", "FIRE", "ordre de largage", "#B71C1C"),
         (M + 430, "3,2 ms", "LIBÉRATION", "aimant relâché", "#BF5700"),
         (M + 635, "23,6 ms", "CONFIRMÉ", "creux de courant détecté", "#2E7D32")]
for x, t, lab, sub, c in steps:
    pg.draw_circle(pymupdf.Point(x, ty), 7, color=None, fill=hx(c))
    d.html(R(x - 60, ty - 72, x + 120, ty - 14),
           '<div style="font-size:19px;font-weight:bold;color:%s">%s</div>'
           '<div style="font-size:12px;color:#5A6672">%s</div>' % (c, t, lab))
    d.html(R(x - 60, ty + 16, x + 120, ty + 70),
           '<div style="font-size:11.5px;color:#19222B">%s</div>' % sub)
d.panel(R(M, 262, 520, 448), fill="#F4F7FA")
d.html(R(M + 20, 276, 500, 442),
       '<div style="font-size:12.5px;color:#1565C0;letter-spacing:.4px">LA PREUVE SANS CAPTEUR SUPPLÉMENTAIRE</div>'
       '<p style="margin-top:8px;font-size:12.5px">Pendant la course du plongeur, la force '
       'contre-électromotrice creuse le courant de la bobine. Ce <b>creux mesuré</b> prouve que le '
       'plongeur a réellement bougé.</p>'
       '<p style="font-size:12.5px">Un plongeur bloqué ne produit aucun creux : le firmware '
       '<b>signale un défaut au pilote</b> au lieu d\'allumer la balise.</p>')
d.image(R(612, 248, 842, 456), os.path.join(FIG, "07_solenoide_ejection.png"), pad=5)
d.html(R(556, 462, W - M, 498),
       '<div class="cap">Simulation électromécanique du solénoïde — le creux de courant est détecté à 23,6 ms.</div>')

# ---------------------------------------------------------------- 6. électronique
d.slide("La puissance ne peut pas faire tomber la logique", kicker="Architecture électronique")
d.html(R(M, 126, 470, 400),
       '<p style="font-size:12.5px">Les trois rails sont tirés <b>directement de VIN, jamais en '
       'cascade</b> : un appel de courant des actionneurs ne peut faire chuter ni le calculateur, '
       'ni la radio.</p>')
ry = 186
rails = [("+3V3 logique", "LMR51430 — 3,315 V", "#1565C0"),
         ("+3V3 RF", "ferrite — radio isolée", "#6A1B9A"),
         ("+12V grilles", "TPS7A4101 — 11,85 V", "#BF5700"),
         ("V_ACT", "ARM — actionneurs", "#2E7D32")]
d.chip(M, ry + 44, 96, 50, 'VIN<br/><span style="font-size:9.5px;font-weight:normal">24 V</span>',
       "#53616E", size=13)
for i, (t, s, c) in enumerate(rails):
    yy = ry + i * 42
    d.arrow(M + 96, ry + 69, M + 128, yy + 16, color=hx(c), width=1.2)
    d.chip(M + 132, yy, 150, 32, t, c, size=11.5)
    d.html(R(M + 292, yy + 4, 480, yy + 34), '<div style="font-size:11.5px;color:#19222B">%s</div>' % s)
d.panel(R(M, 376, 470, 448), fill="#FFF4EC")
d.html(R(M + 18, 388, 460, 444),
       '<div style="font-size:12.5px"><b>Séquencement imposé au firmware.</b> Tout allumé : '
       '<span class="hi">4,25 A</span> pour 5 A disponibles. Largage puis balise : '
       '<span class="ok">&le; 2,5 A</span>.</div>')
d.image(R(500, 126, W - M, 400), os.path.join(FIG, "03_integrite_alimentation.png"), pad=6)
d.panel(R(500, 410, W - M, 448), fill="#F4F7FA")
d.html(R(516, 418, W - M - 14, 446),
       '<div style="font-size:12px"><b>Court-circuit de 30 ms sur l\'E-Port :</b> le 3,3 V <span class="ok">tient</span> '
       'grâce à la diode idéale — contre un effondrement en <span class="hi">85 µs</span> sans elle.</div>')

# ---------------------------------------------------------------- 7. la carte
d.slide("La carte BRC-M400", kicker="Conception électronique")
d.image(R(M, 126, 452, 350), os.path.join(R3D, "BRC-M400_top.png"), dark_panel=True)
d.image(R(468, 126, W - M, 350), os.path.join(R3D, "BRC-M400_iso_back.png"), dark_panel=True)
stats = [("96 × 66", "mm, 4 couches"), ("163", "composants"), ("1 414", "pistes routées"),
         ("424", "vias"), ("0", "erreur ERC / netlist")]
for i, (n, lab) in enumerate(stats):
    x = M + i * 174
    d.html(R(x, 368, x + 168, 430),
           '<div class="num">%s</div><div class="k" style="margin-top:2px">%s</div>' % (n, lab))
d.panel(R(M, 430, W - M, 486), fill="#F4F7FA")
d.html(R(M + 18, 440, W - M - 18, 484),
       '<div style="font-size:12.5px"><b>Pensée pour le châssis :</b> contour et trous M3 aux angles, '
       'XT30 de puissance sur les bords bas et droit face aux actionneurs, SMA en bord de carte, '
       'connecteurs drone sur le bord haut. Plan de masse continu, ligne RF 50 Ω sans via.</div>')

# ---------------------------------------------------------------- 8. simulations
d.slide("Chaque choix est vérifié en simulation", kicker="Dimensionnement prouvé")
figs = [("08_aimant_maintien.png", "Aimant de maintien : libération <b>3,2 ms</b> après l'ordre FIRE, "
         "démagnétisation <b>4,4× plus rapide</b> grâce à la TVS."),
        ("09_bilan_liaison_lora.png", "Bilan de liaison LoRa : <b>40 dB de marge à 15 km</b> en SF9, "
         "165 ms de temps d'antenne.")]
for i, (f, cap) in enumerate(figs):
    x = M + i * 440
    d.image(R(x, 126, x + 410, 332), os.path.join(FIG, f), pad=6)
    d.html(R(x, 340, x + 410, 392), '<div class="cap">%s</div>' % cap)
d.panel(R(M, 400, W - M, 486), fill="#F4F7FA")
d.html(R(M + 18, 410, W - M - 18, 482),
       '<div style="font-size:12px;color:#1565C0;letter-spacing:.4px">SEPT ANALYSES NGSPICE + VÉRIFICATION AUTOMATIQUE DU SCHÉMA</div>'
       '<div style="font-size:12px;margin-top:6px">Convertisseur 3,3 V (ondulation 3,3 mV) · intégrité '
       'd\'alimentation et court-circuit E-Port · étage LED PWM (10 mW de pertes) · coupure inductive '
       'de la sirène · solénoïde d\'éjection · aimant de maintien · bilan de liaison. '
       'Contrôle ERC <b>sans violation</b> et netlist extraite identique à la référence (<b>0 écart</b>).</div>')

# ---------------------------------------------------------------- 9. mécanique (coéquipiers)
d.slide("Intégration mécanique, aérodynamique et structure", kicker="Pôle mécanique")
slots = [("Carénage et berceau", "vue d'ensemble de l'assemblage 3D"),
         ("CFD — lignes de courant et pressions", "force de traînée au vent relatif"),
         ("FEA — von Mises et déplacements", "zones critiques et coefficient de sécurité")]
for i, (t, s) in enumerate(slots):
    x = M + i * 294
    pg = d.page
    pg.draw_rect(R(x, 128, x + 274, 352), color=hx("#BF5700"), fill=hx("#FFFBF7"), width=1.0)
    d.html(R(x + 16, 206, x + 258, 320),
           '<div style="text-align:center;font-size:13px;font-weight:bold;color:#BF5700">%s</div>'
           '<div style="text-align:center;font-size:11px;color:#8A6244;margin-top:6px">%s</div>' % (t, s))
    d.html(R(x, 360, x + 274, 400),
           '<div class="cap" style="text-align:center">capture à insérer</div>')
d.panel(R(M, 408, W - M, 486), fill="#F4F7FA")
d.html(R(M + 18, 418, W - M - 18, 482),
       '<div style="font-size:12.5px"><b>Interface imposée par l\'électronique :</b> empreinte '
       '96 × 66 mm, quatre M3 aux angles reliés à la masse, sorties XT30 face aux actionneurs, '
       'SMA en bord de carte. Sources de chaleur faibles et localisées : MOSFET 2,8 mΩ et LDO '
       '(~60 mW), pertes de commutation simulées à 10 mW.</div>')

# ---------------------------------------------------------------- 10. conclusion
d.slide("Ce que nous apportons", kicker="En résumé")
pts = [("Sûreté", "L'état non alimenté tient la charge, et deux barrières indépendantes commandent le largage."),
       ("Certitude", "Le largage est confirmé par la signature de courant, sans capteur supplémentaire."),
       ("Robustesse", "Rails séparés et diode idéale : la puissance ne fait pas redémarrer la logique."),
       ("Preuves", "Sept simulations, ERC sans violation, netlist vérifiée, carte routée sur 4 couches.")]
for i, (t, s) in enumerate(pts):
    x = M + (i % 2) * 440
    y = 136 + (i // 2) * 128
    d.panel(R(x, y, x + 410, y + 104), fill="#F4F7FA")
    d.html(R(x + 20, y + 14, x + 392, y + 96),
           '<div style="font-size:16px;font-weight:bold;color:#12355B">%s</div>'
           '<div style="font-size:12.5px;margin-top:5px">%s</div>' % (t, s))
d.panel(R(M, 404, W - M, 486), fill="#0E1A26")
d.html(R(M + 24, 420, W - M - 24, 482),
       '<div style="font-size:17px;font-weight:bold;color:#FFFFFF">Une bouée qui ne tombe que '
       'lorsqu\'on le décide — et qui le prouve.</div>'
       '<div style="font-size:12px;color:#8FA6BC;margin-top:6px">Équipe INSATECH · BRC-M400 Rev C · merci de votre attention</div>')

doc = d.save()
for i, p in enumerate(doc):
    p.get_pixmap(dpi=72).save(os.path.join(HERE, "_slide%02d.png" % (i + 1)))
