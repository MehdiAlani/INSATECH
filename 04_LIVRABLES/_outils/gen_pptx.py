# -*- coding: utf-8 -*-
"""Deck INSATECH - BRC-M400 (.pptx 16:9). python -m pip install python-pptx pillow"""
import os
import sys

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_kit import (AMBER, AMBER_D, CYAN, Deck, FONT_L, GREEN, HAIR, INK, MG, MUTED,  # noqa: E402
                      MUTED_D, NAVY, NAVY2, PANEL, RED, TEXT, VIOLET, W, H, WHITE)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ART = os.path.join(HERE, "art")
FIG = os.path.join(ROOT, "03_SIMULATION", "electronique", "figures")
OUT = os.path.normpath(os.path.join(HERE, "..", "02_PRESENTATION",
                                    "INSATECH_BRC-M400_presentation.pptx"))
d = Deck()
P = PP_ALIGN


def section(num, title, sub):
    s = d.add(dark=True)
    s.text(MG, 2.55, 3.0, 1.4, [(num, {})], size=96, color=AMBER, bold=True, font=FONT_L, line=1.0)
    s.rect(MG, 4.12, 1.15, 0.055, AMBER)
    s.text(MG + 2.4, 2.9, 8.6, 1.2, [(title, {})], size=38, color=WHITE, bold=True, line=1.08)
    s.text(MG + 2.4, 4.42, 8.6, 0.8, [(sub, {})], size=14, color=MUTED_D, line=1.4)
    return s


# ============================================================ 1 — couverture
s = d.add(dark=True)
s.picture_fit(os.path.join(ART, "BRC-M400_iso_cut.png"), 6.15, 1.25, 6.85, 5.1)
s.text(MG, 1.62, 6.0, 0.3, [("TUNISIAN AERODAY V14   ·   CHALLENGE CAO", {})],
       size=11, color=CYAN, bold=True, spacing=200)
s.text(MG, 2.05, 6.2, 1.5, [("BRC-M400", {})], size=76, color=WHITE, bold=True, line=1.0)
s.rect(MG, 3.42, 1.15, 0.06, AMBER)
s.text(MG, 3.72, 5.6, 1.3,
       [("Système de largage de bouée", {}),
        ("et balise de détresse", {"newpara": True})],
       size=22, color=WHITE, line=1.28)
s.text(MG, 5.05, 5.6, 0.4, [("Module autonome sous DJI Matrice 400 — batterie 3S + LoRa", {})],
       size=12.5, color=MUTED_D)
s.line(MG, 5.72, MG + 3.2, 5.72, NAVY2, 1.0)
s.text(MG, 5.92, 5.6, 0.75,
       [("Équipe INSATECH", {"size": 20, "bold": True, "color": WHITE}),
        ("22 novembre 2026   ·   Révision D", {"newpara": True, "size": 11, "color": MUTED_D})])

# ============================================================ 2 — contexte
s = d.add(dark=True)
s.kicker("Le contexte")
s.title("Quand l'eau monte, le sol devient inaccessible")
s.rule(1.78, NAVY2)
s.text(MG, 2.15, 6.5, 2.6,
       [("Lors d'une inondation ou d'un tsunami, les secours terrestres sont bloqués et les "
         "réseaux tombent les premiers.", {"size": 16, "color": WHITE, "line": 1.45}),
        ("L'aéronef devient alors le seul moyen d'atteindre une victime en quelques minutes — "
         "encore faut-il pouvoir lui déposer une bouée au plus près, puis la retrouver.",
         {"newpara": True, "size": 14, "color": MUTED_D, "line": 1.5, "space_after": 0})])
s.rect(MG, 5.05, 0.055, 1.15, AMBER)
s.text(MG + 0.3, 5.02, 6.2, 1.3,
       [("« Un largage raté, c'est une vie en moins — et un drone qui repart avec sa charge. »",
         {"size": 14.5, "italic": True, "color": WHITE, "line": 1.45})])
x = 7.9
for i, (v, l) in enumerate([("1 kg", "charge utile à déposer"),
                            ("15 km", "portée radio visée"),
                            ("24 ms", "durée du largage, confirmée")]):
    s.stat(x, 2.2 + i * 1.42, 4.6, v, l, color=AMBER, size=42, lsize=11.5)
    if i < 2:
        s.line(x, 3.52 + i * 1.42, x + 4.3, 3.52 + i * 1.42, NAVY2, 0.75)

# ============================================================ 3 — mission
s = d.add()
s.kicker("La mission")
s.title("Larguer en sécurité, puis rendre la bouée repérable")
s.accent_bar(y=1.74)
reqs = [("Ne jamais lâcher par accident",
         "En vol, sous forte accélération verticale, la charge reste tenue — y compris si tout tombe en panne."),
        ("Larguer de façon certaine, et le savoir",
         "Le pilote doit recevoir la confirmation que la bouée est réellement partie."),
        ("Rester repérable au sol",
         "Une balise lumineuse et sonore s'allume une fois la bouée larguée.")]
for i, (t, sub) in enumerate(reqs):
    y = 2.25 + i * 1.32
    s.rect(MG, y + 0.04, 0.3, 0.3, AMBER)
    s.text(MG + 0.07, y + 0.07, 0.3, 0.3, [(str(i + 1), {})], size=13, color=WHITE, bold=True)
    s.text(MG + 0.55, y, 6.3, 1.2,
           [(t, {"size": 15.5, "bold": True, "color": NAVY}),
            (sub, {"newpara": True, "size": 12, "color": MUTED, "line": 1.4})])
s.rect(7.75, 2.1, 4.85, 4.0, PANEL)
s.text(8.1, 2.42, 4.2, 0.3, [("CONTRAINTES DIMENSIONNANTES", {})], size=9.5,
       color=AMBER_D, bold=True, spacing=120)
for i, (v, l) in enumerate([("1 kg", "charge utile larguée"), ("3S", "LiPo 2200 mAh · 24,4 Wh"),
                            ("0", "liaison avec le drone"), ("USB-C", "recharge Power Delivery")]):
    s.stat(8.1 + (i % 2) * 2.25, 2.95 + (i // 2) * 1.32, 2.1, v, l, color=NAVY, size=31, lsize=9.5)
s.text(8.1, 5.52, 4.2, 0.75,
       [("Le module porte sa propre énergie : il se fixe sous n'importe quel aéronef, et sa balise "
         "fonctionne encore quand le drone est reparti.",
         {"size": 10.5, "color": MUTED, "line": 1.4})])

# ============================================================ 4 — architecture
s = d.add()
s.kicker("Vue d'ensemble")
s.title("Architecture du système")
s.accent_bar(y=1.74)
bw, bh, top = 2.05, 0.92, 2.42
cols = [MG + i * 2.47 for i in range(5)]
chain = [("Pack 3S LiPo", "2200 mAh · BMS", GREEN),
         ("Alimentation", "LM74700 · LMR51430", AMBER_D),
         ("Calculateur", "STM32U585", NAVY2),
         ("Radio LoRa", "SX1262 · 868 MHz", VIOLET),
         ("Balise", "LED + sirène", RED)]
for (t1, t2, c), x in zip(chain, cols):
    s.chip(x, top, bw, bh, t1, t2, fill=c, size=13, sub_size=9.5)
for i in range(4):
    s.arrow(cols[i] + bw + 0.04, top + bh / 2, cols[i + 1] - 0.04, top + bh / 2, MUTED, 1.25)
y2 = top + 1.72
s.chip(cols[0], y2, bw, bh, "Charge USB-C", "STUSB4500 · BQ24610", fill=CYAN, size=13, sub_size=9.5)
s.arrow(cols[0] + bw / 2, y2 - 0.04, cols[0] + bw / 2, top + bh + 0.04, CYAN, 1.25)
s.chip(cols[2], y2, bw, bh, "Actionneurs", "aimant · solénoïde", fill=NAVY, size=13, sub_size=9.5)
s.chip(cols[3], y2, bw, bh, "Capteurs", "verrou · présence · courants", fill=CYAN,
       size=13, sub_size=9.5)
s.arrow(cols[2] + bw / 2 - 0.3, top + bh, cols[2] + bw / 2 - 0.3, y2 - 0.04, NAVY, 1.25)
s.arrow(cols[3] + bw / 2, y2 - 0.04, cols[2] + bw / 2 + 0.3, top + bh, CYAN, 1.25)
s.text(cols[2] + bw + 0.1, y2 + 0.18, 2.3, 0.6,
       [("PWM · ARM · mesure de courant", {"size": 10, "color": MUTED, "align": P.CENTER}),
        ("retour d'état", {"newpara": True, "size": 10, "color": MUTED, "align": P.CENTER})])
s.rect(MG, 5.72, W - 2 * MG, 0.86, PANEL)
s.text(MG + 0.34, 5.95, W - 2 * MG - 0.7, 0.5,
       [("Aucune liaison électrique avec le drone : ", {"size": 13, "bold": True, "color": NAVY}),
        ("le module porte son énergie et sa radio. Il se fixe sous n'importe quel aéronef, et la "
         "balise reste alimentée une fois la bouée au sol.", {"size": 13, "color": TEXT})])

# ============================================================ 5 — section mécanisme
section("01", "Le mécanisme de largage",
        "Comment garantir qu'une charge de 1 kg ne tombe jamais par accident — et qu'elle tombe "
        "à coup sûr quand on le décide.")

# ============================================================ 6 — sûreté
s = d.add()
s.kicker("Sûreté par construction")
s.title("L'état sûr, c'est l'état non alimenté")
s.accent_bar(y=1.74)
s.text(MG, 2.18, 11.9, 0.45,
       [("L'électroaimant de maintien est à sécurité positive : un aimant permanent tient la bouée, "
         "et c'est l'alimentation de la bobine qui annule le champ pour libérer.",
         {"size": 14, "color": TEXT, "line": 1.4})])
# two states
for i, (lab, state, sub, col, fill) in enumerate([
        ("Bobine NON alimentée", "BOUÉE TENUE", "l'aimant permanent travaille seul", GREEN, PANEL),
        ("Bobine alimentée", "BOUÉE LIBÉRÉE", "le champ de la bobine annule l'aimant", AMBER_D, PANEL)]):
    x = MG + i * 3.1
    s.rect(x, 2.95, 2.85, 2.05, fill)
    s.rect(x, 2.95, 2.85, 0.07, col)
    s.text(x, 3.22, 2.85, 0.35, [(lab, {})], size=11, color=MUTED, align=P.CENTER)
    s.text(x, 3.72, 2.85, 0.5, [(state, {})], size=17, color=col, bold=True, align=P.CENTER)
    s.text(x + 0.2, 4.28, 2.45, 0.6, [(sub, {})], size=10.5, color=MUTED, align=P.CENTER, line=1.3)
s.rect(MG, 5.22, 5.95, 1.32, INK)
s.text(MG + 0.3, 5.46, 5.4, 0.95,
       [("Panne d'alimentation, reset du calculateur ou perte de liaison", {"size": 12.5, "color": MUTED_D}),
        ("→ la bouée reste accrochée.", {"newpara": True, "size": 15, "bold": True, "color": WHITE})])
# right: why it matters
s.rect(7.1, 2.95, 5.5, 3.59, None, line=HAIR, lw=1.0)
s.text(7.45, 3.22, 4.9, 0.35, [("POURQUOI C'EST LE BON CHOIX", {})], size=9.5,
       color=AMBER_D, bold=True, spacing=120)
pts = [("Le cahier des charges exige un mécanisme « intrinsèquement sûr » en position fermée.", None),
       ("Avec un aimant classique, bobine alimentée = maintien : la moindre coupure lâcherait la "
        "bouée en vol.", None),
       ("Ici, la seule façon de libérer est une action volontaire, alimentée et séquencée.", None)]
for i, (t, _) in enumerate(pts):
    y = 3.75 + i * 0.92
    s.rect(7.45, y + 0.06, 0.1, 0.1, AMBER)
    s.text(7.72, y - 0.04, 4.6, 0.85, [(t, {})], size=12, color=TEXT, line=1.4)

# ============================================================ 7 — double barrière
s = d.add()
s.kicker("Sûreté par construction")
s.title("Double barrière : aucun défaut unique ne peut larguer")
s.accent_bar(y=1.74)
cx, cy, cw, ch = MG, 2.5, 1.95, 1.0
s.chip(cx, cy, cw, ch, "PACK 3S", "9 – 12,6 V", fill=NAVY, size=14, sub_size=9.5)
s.arrow(cx + cw + 0.08, cy + ch / 2, cx + cw + 0.72, cy + ch / 2, MUTED, 1.4)
s.chip(cx + cw + 0.8, cy, cw, ch, "ARM", "P-MOSFET côté haut", fill=NAVY2, size=14, sub_size=9.5)
s.arrow(cx + 2 * cw + 0.88, cy + ch / 2, cx + 2 * cw + 1.52, cy + ch / 2, MUTED, 1.4)
s.chip(cx + 2 * cw + 1.6, cy, cw, ch, "FIRE", "étage côté bas", fill=RED, size=14, sub_size=9.5)
s.text(cx + cw + 0.8, cy + ch + 0.16, cw, 0.3, [("barrière n°1", {})], size=10.5,
       color=MUTED, align=P.CENTER)
s.text(cx + 2 * cw + 1.6, cy + ch + 0.16, cw, 0.3, [("barrière n°2", {})], size=10.5,
       color=MUTED, align=P.CENTER)
s.rect(MG, 4.42, 7.9, 2.1, PANEL)
s.text(MG + 0.34, 4.68, 7.3, 1.6,
       [("Le largage exige les deux étages à la fois.", {"size": 14, "bold": True, "color": NAVY}),
        ("Une broche du microcontrôleur qui bascule, un MOSFET en court-circuit ou un parasite sur "
         "une piste ne suffisent pas : il faut une commande volontaire sur les deux barrières.",
         {"newpara": True, "size": 12.5, "color": TEXT, "line": 1.45}),
        ("S'y ajoute un verrouillage logiciel : le largage n'est autorisé que dans un domaine "
         "d'altitude et de vitesse lu sur la télémétrie du drone.",
         {"newpara": True, "size": 11.5, "color": MUTED, "line": 1.4})])
s.rect(8.85, 2.5, 3.75, 4.02, INK)
s.text(9.15, 2.82, 3.2, 0.35, [("EN CAS DE DÉFAUT", {})], size=9.5, color=CYAN, bold=True, spacing=120)
for i, (f, r) in enumerate([("GPIO qui bascule", "ARM reste ouvert"),
                            ("MOSFET en court-circuit", "l'autre barrière tient"),
                            ("Reset du calculateur", "tout retombe à l'état sûr"),
                            ("Perte de liaison", "la bouée reste tenue")]):
    y = 3.35 + i * 0.78
    s.text(9.15, y, 3.2, 0.3, [(f, {})], size=11.5, color=WHITE, bold=True)
    s.text(9.15, y + 0.26, 3.2, 0.3, [("→ " + r, {})], size=10.5, color=GREEN)

# ============================================================ 8 — séquence
s = d.add()
s.kicker("Séquence et confirmation")
s.title("Le largage se déroule — et se prouve — en 24 ms")
s.accent_bar(y=1.74)
ty = 3.02
s.line(MG + 0.15, ty, W - MG - 0.15, ty, HAIR, 1.5)
steps = [("0 ms", "ARMER", "barrière haute fermée", NAVY2),
         ("+0 ms", "FIRE", "ordre de largage", RED),
         ("3,2 ms", "LIBÉRATION", "aimant relâché", AMBER_D),
         ("23,7 ms", "CONFIRMÉ", "creux de courant détecté", GREEN)]
span = (W - 2 * MG - 0.3) / 3.0
for i, (t, lab, sub, c) in enumerate(steps):
    x = MG + 0.15 + i * span
    s.rect(x - 0.085, ty - 0.085, 0.17, 0.17, c, shape=MSO_SHAPE.OVAL)
    # keep the first/last captions inside the page margins
    al = P.LEFT if i == 0 else (P.RIGHT if i == len(steps) - 1 else P.CENTER)
    bx = MG if i == 0 else (W - MG - 2.4 if i == len(steps) - 1 else x - 1.2)
    s.text(bx, ty - 1.0, 2.4, 0.4, [(t, {})], size=20, color=c, bold=True, align=al)
    s.text(bx, ty - 0.58, 2.4, 0.3, [(lab, {})], size=10.5, color=MUTED, align=al, spacing=80)
    s.text(bx, ty + 0.25, 2.4, 0.4, [(sub, {})], size=11, color=TEXT, align=al)
s.rect(MG, 3.95, 6.0, 2.55, PANEL)
s.text(MG + 0.34, 4.22, 5.4, 0.3, [("LA PREUVE, SANS CAPTEUR SUPPLÉMENTAIRE", {})],
       size=9.5, color=AMBER_D, bold=True, spacing=120)
s.text(MG + 0.34, 4.68, 5.4, 1.7,
       [("Pendant la course du plongeur, la force contre-électromotrice creuse le courant de la "
         "bobine. Ce creux mesuré prouve que le plongeur a réellement bougé.",
         {"size": 12.5, "color": TEXT, "line": 1.45}),
        ("Un plongeur bloqué ne produit aucun creux : le firmware signale un défaut au pilote au "
         "lieu d'allumer la balise.",
         {"newpara": True, "size": 12.5, "color": TEXT, "line": 1.45})])
s.rect(7.1, 3.95, 5.5, 2.55, None, line=HAIR, lw=1.0)
s.picture_fit(os.path.join(FIG, "07_solenoide_ejection.png"), 7.22, 4.05, 5.26, 2.35)

# ============================================================ 9 — section électronique
section("02", "L'architecture électronique",
        "Une carte sur mesure qui alimente, décide, communique et prouve — sans jamais laisser "
        "la puissance perturber la logique.")

# ============================================================ 10 — rails
s = d.add()
s.kicker("Séparation logique / puissance")
s.title("La puissance ne peut pas faire tomber la logique")
s.accent_bar(y=1.74)
s.text(MG, 2.18, 6.3, 0.5,
       [("Les rails sont tirés directement de VIN, jamais en cascade : un appel de courant des "
         "actionneurs ne peut faire chuter ni le calculateur, ni la radio.",
         {"size": 13, "color": TEXT, "line": 1.42})])
s.chip(MG, 3.42, 1.35, 0.92, "PACK", "9 – 12,6 V", fill=NAVY, size=14, sub_size=10)
rails = [("+3V3 logique", "LMR51430 — 3,315 V", NAVY2),
         ("+3V3 RF", "ferrite — radio isolée", VIOLET),
         ("+12V grilles", "élévateur TPS61040 — 11,96 V", AMBER_D),
         ("V_ACT", "ARM — actionneurs", GREEN)]
for i, (t, sub, c) in enumerate(rails):
    y = 2.92 + i * 0.69
    s.arrow(MG + 1.4, 3.88, MG + 1.95, y + 0.26, c, 1.1)
    s.rect(MG + 2.0, y, 1.95, 0.52, c)
    s.text(MG + 2.0, y, 1.95, 0.52, [(t, {})], size=11.5, color=WHITE, bold=True,
           align=P.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    s.text(MG + 4.1, y + 0.13, 2.6, 0.35, [(sub, {})], size=11, color=TEXT)
s.rect(MG, 5.92, 6.3, 0.72, PANEL)
s.text(MG + 0.3, 6.08, 5.8, 0.45,
       [("Un élévateur, pas un LDO : ", {"size": 12.5, "bold": True, "color": NAVY}),
        ("à 9 V de pack, un LDO 12 V ne sortirait plus 12 V. Ici ", {"size": 12.5, "color": TEXT}),
        ("Vgs reste nominal jusqu'à la fin de la décharge", {"size": 12.5, "bold": True, "color": GREEN}),
        (".", {"size": 12.5, "color": TEXT})])
s.rect(7.35, 2.1, 5.25, 3.52, None, line=HAIR, lw=1.0)
s.picture_fit(os.path.join(FIG, "03_integrite_alimentation.png"), 7.47, 2.2, 5.0, 3.32)
s.rect(7.35, 5.78, 5.25, 0.86, INK)
s.text(7.65, 5.95, 4.7, 0.6,
       [("Coupure de 30 ms en entrée : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("le 3,3 V tient grâce à la diode idéale et au réservoir — contre un effondrement en 85 µs "
         "sans elles.", {"size": 11.5, "color": MUTED_D})])

# ============================================================ 11 — la carte
s = d.add(dark=True)
s.kicker("Conception électronique", color=CYAN)
s.title("La carte BRC-M400", color=WHITE)
s.rule(1.78, NAVY2)
s.picture_fit(os.path.join(ART, "BRC-M400_top_cut.png"), MG, 2.05, 5.85, 2.95)
s.picture_fit(os.path.join(ART, "BRC-M400_iso_back_cut.png"), 6.9, 2.05, 5.7, 2.95)
stats = [("134 × 66", "mm · 4 couches"), ("226", "composants"), ("6", "blocs fonctionnels"),
         ("151", "réseaux"), ("0", "erreur ERC / netlist")]
for i, (v, l) in enumerate(stats):
    s.stat(MG + i * 2.44, 5.22, 2.3, v, l, color=AMBER, size=28, lsize=9.5)
s.rect(MG, 6.18, W - 2 * MG, 0.62, None, line=NAVY2, lw=1.0)
s.text(MG + 0.3, 6.31, W - 2 * MG - 0.6, 0.4,
       [("Pensée pour le châssis : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("bande énergie isolée à gauche (USB-C, chargeur, BMS, pack), XT30 des actionneurs en bas, "
         "SMA en bord de carte, plan de masse continu et ligne RF 50 Ω sans via.",
         {"size": 11.5, "color": MUTED_D})])

# ============================================================ 12 — simulations
s = d.add()
s.kicker("Dimensionnement prouvé")
s.title("Chaque choix est vérifié en simulation")
s.accent_bar(y=1.74)
figs = [("08_aimant_maintien.png", "Aimant de maintien",
         "libération 3,2 ms après l'ordre FIRE, démagnétisation 7× plus rapide grâce à la TVS"),
        ("09_bilan_liaison_lora.png", "Bilan de liaison LoRa",
         "40 dB de marge à 15 km en SF9, 165 ms de temps d'antenne")]
for i, (f, t, cap) in enumerate(figs):
    x = MG + i * 6.1
    s.rect(x, 2.18, 5.78, 2.72, None, line=HAIR, lw=1.0)
    s.picture_fit(os.path.join(FIG, f), x + 0.12, 2.28, 5.54, 2.52)
    s.text(x, 5.02, 5.78, 0.6,
           [(t + " — ", {"size": 12, "bold": True, "color": NAVY}),
            (cap, {"size": 12, "color": MUTED, "line": 1.35})])
s.rect(MG, 5.82, W - 2 * MG, 0.95, PANEL)
s.text(MG + 0.34, 5.98, W - 2 * MG - 0.7, 0.3,
       [("SEPT ANALYSES NGSPICE  +  VÉRIFICATION AUTOMATIQUE DU SCHÉMA", {})],
       size=9.5, color=AMBER_D, bold=True, spacing=120)
s.text(MG + 0.34, 6.28, W - 2 * MG - 0.7, 0.45,
       [("Convertisseur 3,3 V · intégrité d'alimentation · étage LED PWM · coupure inductive de la "
         "sirène · solénoïde d'éjection · aimant de maintien · bilan de liaison.   "
         "ERC sans violation et netlist identique à la référence (0 écart).",
         {"size": 11.5, "color": TEXT, "line": 1.35})])

# ============================================================ 13 — mécanique
s = d.add()
s.kicker("Pôle mécanique")
s.title("Intégration, aérodynamique et tenue structurelle")
s.accent_bar(y=1.74)
slots = [("Carénage et berceau", "assemblage 3D complet"),
         ("CFD", "lignes de courant, pressions, traînée"),
         ("FEA", "von Mises, déplacements, coefficient de sécurité")]
for i, (t, sub) in enumerate(slots):
    x = MG + i * 4.08
    s.rect(x, 2.18, 3.78, 2.95, PANEL, line=HAIR, lw=1.0)
    s.text(x, 3.25, 3.78, 0.4, [(t, {})], size=15, color=NAVY, bold=True, align=P.CENTER)
    s.text(x + 0.3, 3.75, 3.18, 0.6, [(sub, {})], size=11, color=MUTED, align=P.CENTER, line=1.35)
    s.text(x, 5.22, 3.78, 0.3, [("capture à insérer", {})], size=9.5, color=MUTED, align=P.CENTER,
           spacing=80)
s.rect(MG, 5.72, W - 2 * MG, 0.95, INK)
s.text(MG + 0.34, 5.92, W - 2 * MG - 0.7, 0.62,
       [("Interface imposée par l'électronique : ", {"size": 12, "bold": True, "color": WHITE}),
        ("empreinte 134 × 66 mm, quatre M3 aux angles reliés à la masse, XT30 des actionneurs en "
         "bas, SMA dégagée et surtout <b>prise USB-C accessible sans démonter le carénage</b>. "
         "Prévoir le logement du pack 3S (environ 105 × 35 × 25 mm).",
         {"size": 12, "color": MUTED_D, "line": 1.38})])

# ============================================================ 14 — bilan
s = d.add(dark=True)
s.kicker("En résumé", color=CYAN)
s.title("Ce que nous apportons", color=WHITE)
s.rule(1.78, NAVY2)
cards = [("Autonomie", "Aucune liaison avec le drone : la balise fonctionne encore une fois la bouée au sol."),
         ("Sûreté", "L'état non alimenté tient la charge, et deux barrières indépendantes commandent le largage."),
         ("Certitude", "Le largage est confirmé par la signature de courant, sans capteur supplémentaire."),
         ("Preuves", "Sept simulations, ERC sans violation, netlist vérifiée, carte 4 couches.")]
for i, (t, sub) in enumerate(cards):
    x = MG + (i % 2) * 6.1
    y = 2.22 + (i // 2) * 1.62
    s.rect(x, y, 5.78, 1.38, None, line=NAVY2, lw=1.0)
    s.rect(x, y, 0.055, 1.38, AMBER)
    s.text(x + 0.35, y + 0.22, 5.1, 0.35, [(t, {})], size=16, color=WHITE, bold=True)
    s.text(x + 0.35, y + 0.62, 5.1, 0.65, [(sub, {})], size=11.5, color=MUTED_D, line=1.4)
s.rect(MG, 5.72, W - 2 * MG, 1.05, AMBER)
s.text(MG + 0.4, 5.92, W - 2 * MG - 0.8, 0.7,
       [("« Une bouée qui ne tombe que lorsqu'on le décide — et qui le prouve. »",
         {"size": 18, "bold": True, "color": WHITE}),
        ("Équipe INSATECH  ·  BRC-M400 Rev D  ·  merci de votre attention",
         {"newpara": True, "size": 11, "color": WHITE})])

d.save(OUT)
