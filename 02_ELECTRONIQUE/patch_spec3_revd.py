# -*- coding: utf-8 -*-
"""Rev D: sweep the remaining E-Port / PSDK / 24 V references out of the spec."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "01_SPEC_ELECTRONIQUE.md")
s = io.open(p, encoding="utf-8").read()
n = 0


def sub(a, b):
    global s, n
    assert a in s, "NOT FOUND: " + a[:70]
    s = s.replace(a, b, 1)
    n += 1


sub(u"4. **Entrée protégée par diode idéale.** Sur un court-circuit ou une coupure de l'E-Port, le condensateur réservoir reste chargé et le MCU continue de fonctionner.",
    u"4. **Entrée protégée par diode idéale.** Sur un rebond de connecteur ou une coupure du BMS, le condensateur réservoir reste chargé et le MCU continue de fonctionner (simulé : 30 ms sans redémarrage).")
sub(u"| PSDK | **Bibliothèque DJI officielle `armcc_cortex-m33`** |",
    u"| I²C | **BQ76920 (BMS) + STUSB4500 (USB-C PD)** sur le même bus |")
sub(u"| UART PSDK | USART1 — PA9 / PA10 |",
    u"| I²C BMS / PD | PA9 / PA10 (instance à confirmer sous CubeMX ; repli I²C logiciel possible) |")
sub(u"- **Deux chemins de commande indépendants :** LoRa depuis le sol, et PSDK depuis le drone.",
    u"- **Chemin de commande unique, donc durci :** ARMER puis LARGUER, AES-128, compteur anti-rejeu, accusé de réception et 3 retransmissions.")
sub(u"| J1 | XT30PW-M | Entrée E-Port V2 |", u"| J42 | XT30PW-M | Entrée pack 3S (feuille 6) |")
sub(u"| F1 | Fusible 5 A / 32 V | Calibre de l'E-Port |", u"| F1 | Fusible 10 A / 32 V | Protection du pack |")
sub(u"> **Séquencement obligatoire dans le firmware.** Si toutes les charges fonctionnent en même temps, la carte tire **4,25 A** sur l'E-Port : c'est sous la limite de 5 A, mais la marge est faible (simulé). Le firmware enchaîne donc les phases :",
    u"> **Séquencement conservé dans le firmware.** Toutes charges actives, la carte tire **5,20 A** du pack (simulé) — moins de 3C, donc sans danger pour un 2200 mAh. Le séquencement reste appliqué pour ménager les cellules et la durée de signalisation :")
sub(u"| Haut centre | MCU et SWD ; connecteurs PSDK et micro-rupteurs sur le bord haut |",
    u"| Haut centre | MCU et SWD ; micro-rupteurs sur le bord haut |")
sub(u"| Colonne gauche | Entrée de puissance ; convertisseur 3,3 V et LDO 12 V en dessous ; C3 |",
    u"| Bande gauche | **Bloc énergie** : USB-C, STUSB4500, chargeur BQ24610, BMS BQ76920, pack et équilibrage, LED d'état |\n| Colonne suivante | Entrée pack protégée ; convertisseur 3,3 V et élévateur 12 V ; C3 |")

# power rails table in section 5
sub(u"| **+12V_GD** (drivers de grille) | **TI TPS7A4101** — LDO 50 V, 25 µA de repos | 1,173 × (1 + 91k / 10k) = **11,85 V** ; ≥ 4,7 µF en sortie (datasheet) ; ~60 mW dissipés à 24 V |",
    u"| **+12V_GD** (drivers de grille) | **TI TPS61040** — élévateur depuis le 3,3 V | 1,233 × (1 + 1M / 113k) = **11,96 V** ; L = 10 µH ; **indépendant de la tension pack** |")
sub(u"- **Alimentation des grilles en 12 V :** les MOSFET sont attaqués avec Vgs = 11,85 V, ce qui donne leur RDS(on) nominal (1,8 mΩ mesuré en simulation).",
    u"- **Alimentation des grilles en 12 V :** les MOSFET sont attaqués avec Vgs = 11,96 V, ce qui donne leur RDS(on) nominal (1,75 mΩ mesuré en simulation). Un LDO n'aurait pas pu : à 9 V de pack, il ne sortirait plus 12 V. L'élévateur garde Vgs nominal **jusqu'à la fin de la décharge**.")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("spec : %d remplacements supplementaires" % n)
