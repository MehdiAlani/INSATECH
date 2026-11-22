# -*- coding: utf-8 -*-
"""Rev D updates to the pitch deck."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "gen_pptx.py")
s = io.open(p, encoding="utf-8").read()


def sub(a, b):
    global s
    assert a in s, "NOT FOUND: " + a[:80]
    s = s.replace(a, b, 1)


# ---------------------------------------------------------------- cover
sub(u'''s.text(MG, 5.05, 5.6, 0.4, [("Emport sous DJI Matrice 400 — port E-Port V2", {})],
       size=12.5, color=MUTED_D)''',
    u'''s.text(MG, 5.05, 5.6, 0.4, [("Module autonome sous DJI Matrice 400 — batterie 3S + LoRa", {})],
       size=12.5, color=MUTED_D)''')
sub(u'("22 novembre 2026   ·   Révision C", {"newpara": True, "size": 11, "color": MUTED_D})])',
    u'("22 novembre 2026   ·   Révision D", {"newpara": True, "size": 11, "color": MUTED_D})])')

# ---------------------------------------------------------------- mission figures
sub(u'''for i, (v, l) in enumerate([("1 kg", "charge utile larguée"), ("5 A", "limite du port E-Port V2"),
                            ("0", "batterie embarquée"), ("24 V", "tension d'alimentation")]):''',
    u'''for i, (v, l) in enumerate([("1 kg", "charge utile larguée"), ("3S", "LiPo 2200 mAh · 24,4 Wh"),
                            ("0", "liaison avec le drone"), ("USB-C", "recharge Power Delivery")]):''')
sub(u'''s.text(8.1, 5.52, 4.2, 0.6,
       [("Le système est alimenté et commandé par le drone : la masse larguée est la bouée seule.",
         {"size": 10.5, "color": MUTED, "line": 1.4})])''',
    u'''s.text(8.1, 5.52, 4.2, 0.75,
       [("Le module porte sa propre énergie : il se fixe sous n'importe quel aéronef, et sa balise "
         "fonctionne encore quand le drone est reparti.",
         {"size": 10.5, "color": MUTED, "line": 1.4})])''')

# ---------------------------------------------------------------- architecture
sub(u'''chain = [("DJI Matrice 400", "E-Port V2 · 24 V", NAVY),
         ("Alimentation", "LM74700 · LMR51430", AMBER_D),
         ("Calculateur", "STM32U585 · PSDK", NAVY2),
         ("Radio LoRa", "SX1262 · 868 MHz", VIOLET),
         ("Balise", "LED + sirène", RED)]''',
    u'''chain = [("Pack 3S LiPo", "2200 mAh · BMS", GREEN),
         ("Alimentation", "LM74700 · LMR51430", AMBER_D),
         ("Calculateur", "STM32U585", NAVY2),
         ("Radio LoRa", "SX1262 · 868 MHz", VIOLET),
         ("Balise", "LED + sirène", RED)]''')
sub(u'''s.chip(cols[1], y2, bw, bh, "Actionneurs", "aimant · solénoïde", fill=GREEN, size=13, sub_size=9.5)''',
    u'''s.chip(cols[0], y2, bw, bh, "Charge USB-C", "STUSB4500 · BQ24610", fill=CYAN, size=13, sub_size=9.5)
s.arrow(cols[0] + bw / 2, y2 - 0.04, cols[0] + bw / 2, top + bh + 0.04, CYAN, 1.25)
s.chip(cols[2], y2, bw, bh, "Actionneurs", "aimant · solénoïde", fill=NAVY, size=13, sub_size=9.5)''')
sub(u'''s.arrow(cols[2] + 0.5, top + bh, cols[1] + bw / 2 + 0.35, y2 - 0.04, GREEN, 1.25)
s.arrow(cols[3] + bw / 2 - 0.35, y2 - 0.04, cols[2] + bw - 0.5, top + bh, CYAN, 1.25)
s.text(cols[1] + bw + 0.1, y2 + 0.18, 2.3, 0.6,
       [("PWM · ARM · mesure de courant", {"size": 10, "color": MUTED, "align": P.CENTER}),
        ("retour d'état", {"newpara": True, "size": 10, "color": MUTED, "align": P.CENTER})])''',
    u'''s.arrow(cols[2] + bw / 2 - 0.3, top + bh, cols[2] + bw / 2 - 0.3, y2 - 0.04, NAVY, 1.25)
s.arrow(cols[3] + bw / 2, y2 - 0.04, cols[2] + bw / 2 + 0.3, top + bh, CYAN, 1.25)
s.text(cols[2] + bw + 0.1, y2 + 0.18, 2.3, 0.6,
       [("PWM · ARM · mesure de courant", {"size": 10, "color": MUTED, "align": P.CENTER}),
        ("retour d'état", {"newpara": True, "size": 10, "color": MUTED, "align": P.CENTER})])''')
sub(u'''       [("Deux chemins de commande indépendants : ", {"size": 13, "bold": True, "color": NAVY}),
        ("le bouton « LARGUER » de DJI Pilot 2 via le PSDK, et la liaison LoRa directe depuis le "
         "sol — si l'un tombe, l'autre reste.", {"size": 13, "color": TEXT})])''',
    u'''       [("Aucune liaison électrique avec le drone : ", {"size": 13, "bold": True, "color": NAVY}),
        ("le module porte son énergie et sa radio. Il se fixe sous n'importe quel aéronef, et la "
         "balise reste alimentée une fois la bouée au sol.", {"size": 13, "color": TEXT})])''')

# ---------------------------------------------------------------- rails slide
sub(u'''rails = [("+3V3 logique", "LMR51430 — 3,315 V", NAVY2),
         ("+3V3 RF", "ferrite — radio isolée", VIOLET),
         ("+12V grilles", "TPS7A4101 — 11,85 V", AMBER_D),
         ("V_ACT", "ARM — actionneurs", GREEN)]''',
    u'''rails = [("+3V3 logique", "LMR51430 — 3,315 V", NAVY2),
         ("+3V3 RF", "ferrite — radio isolée", VIOLET),
         ("+12V grilles", "élévateur TPS61040 — 11,96 V", AMBER_D),
         ("V_ACT", "ARM — actionneurs", GREEN)]''')
sub(u'''s.chip(MG, ry + 0.5, 1.35, 0.92, "VIN", "24 V", fill=NAVY, size=14, sub_size=10)''',
    u'''s.chip(MG, ry + 0.5, 1.35, 0.92, "PACK", "9 - 12,6 V", fill=NAVY, size=14, sub_size=10)''') \
    if 'ry + 0.5, 1.35, 0.92, "VIN", "24 V"' in s else None
sub(u's.chip(MG, 3.42, 1.35, 0.92, "VIN", "24 V", fill=NAVY, size=14, sub_size=10)',
    u's.chip(MG, 3.42, 1.35, 0.92, "PACK", "9 – 12,6 V", fill=NAVY, size=14, sub_size=10)')
sub(u'''       [("Séquencement imposé : ", {"size": 12.5, "bold": True, "color": NAVY}),
        ("tout allumé 4,25 A pour 5 A disponibles → largage puis balise, ", {"size": 12.5, "color": TEXT}),
        ("≤ 2,5 A", {"size": 12.5, "bold": True, "color": GREEN})])''',
    u'''       [("Un élévateur, pas un LDO : ", {"size": 12.5, "bold": True, "color": NAVY}),
        ("à 9 V de pack, un LDO 12 V ne sortirait plus 12 V. Ici ", {"size": 12.5, "color": TEXT}),
        ("Vgs reste nominal jusqu'à la fin de la décharge", {"size": 12.5, "bold": True, "color": GREEN}),
        (".", {"size": 12.5, "color": TEXT})])''')
sub(u'''       [("Court-circuit de 30 ms sur l'E-Port : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("le 3,3 V tient grâce à la diode idéale — contre un effondrement en 85 µs sans elle.",
         {"size": 11.5, "color": MUTED_D})])''',
    u'''       [("Coupure de 30 ms en entrée : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("le 3,3 V tient grâce à la diode idéale et au réservoir — contre un effondrement en 85 µs "
         "sans elles.", {"size": 11.5, "color": MUTED_D})])''')

# ---------------------------------------------------------------- board stats
sub(u'''stats = [("96 × 66", "mm · 4 couches"), ("163", "composants"), ("1 414", "pistes routées"),
         ("424", "vias"), ("0", "erreur ERC / netlist")]''',
    u'''stats = [("134 × 66", "mm · 4 couches"), ("226", "composants"), ("6", "blocs fonctionnels"),
         ("151", "réseaux"), ("0", "erreur ERC / netlist")]''')
sub(u'''       [("Pensée pour le châssis : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("contour et trous M3 aux angles, XT30 de puissance face aux actionneurs, SMA en bord de "
         "carte, plan de masse continu et ligne RF 50 Ω sans via.",
         {"size": 11.5, "color": MUTED_D})])''',
    u'''       [("Pensée pour le châssis : ", {"size": 11.5, "bold": True, "color": WHITE}),
        ("bande énergie isolée à gauche (USB-C, chargeur, BMS, pack), XT30 des actionneurs en bas, "
         "SMA en bord de carte, plan de masse continu et ligne RF 50 Ω sans via.",
         {"size": 11.5, "color": MUTED_D})])''')

# ---------------------------------------------------------------- mechanical slide note
sub(u'''        ("empreinte 96 × 66 mm, quatre M3 aux angles (entraxes 88,8 × 58,8 mm) reliés à la masse, "
         "sorties XT30 face aux actionneurs, SMA dégagée. Sources de chaleur faibles et "
         "localisées : MOSFET 2,8 mΩ et LDO ~60 mW.",''',
    u'''        ("empreinte 134 × 66 mm, quatre M3 aux angles reliés à la masse, XT30 des actionneurs en "
         "bas, SMA dégagée et surtout <b>prise USB-C accessible sans démonter le carénage</b>. "
         "Prévoir le logement du pack 3S (environ 105 × 35 × 25 mm).",''')

# ---------------------------------------------------------------- closing card
sub(u'''cards = [("Sûreté", "L'état non alimenté tient la charge, et deux barrières indépendantes commandent le largage."),''',
    u'''cards = [("Autonomie", "Aucune liaison avec le drone : la balise fonctionne encore une fois la bouée au sol."),
         ("Sûreté", "L'état non alimenté tient la charge, et deux barrières indépendantes commandent le largage."),''')
sub(u'''         ("Preuves", "Sept simulations, ERC sans violation, netlist vérifiée, carte routée sur 4 couches.")]''',
    u'''         ("Preuves", "Sept simulations, ERC sans violation, netlist vérifiée, carte 4 couches.")]''')

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("gen_pptx.py -> Rev D")
