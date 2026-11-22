# -*- coding: utf-8 -*-
"""Rev D update of 01_SPEC_ELECTRONIQUE.md (autonomous pod: 3S LiPo + BMS + USB-C PD)."""
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


# ---------------------------------------------------------------- header
sub(u"# BRC-M400 Rev C — Buoy Release & Beacon Controller",
    u"# BRC-M400 Rev D — Buoy Release & Beacon Controller")
sub(u"**Carte de commande du largage de bouée et de la signalisation de détresse, embarquée sous DJI Matrice 400.**",
    u"**Module autonome de largage de bouée et de signalisation de détresse, emporté sous DJI Matrice 400.**\n\n"
    u"> **Changement majeur en Rev D : le module n'a plus aucune liaison électrique avec le drone.**\n"
    u"> Il porte son énergie (pack 3S LiPo 2200 mAh + BMS) et reçoit ses ordres par LoRa. L'intégration\n"
    u"> mécanique se réduit à une fixation, et **la balise reste alimentée une fois la bouée au sol**.")
sub(u"| Référence | BRC-M400 **Rev C** |", u"| Référence | BRC-M400 **Rev D** |")
sub(u"| Porteur | DJI Matrice 400 — port E-Port V2 (face inférieure) |",
    u"| Porteur | DJI Matrice 400 — **fixation mécanique seule, aucun connecteur vers le drone** |\n"
    u"| Énergie | **pack 3S LiPo 2200 mAh** (9,0 – 12,6 V, 24,4 Wh) + BMS BQ76920 |\n"
    u"| Recharge | **USB-C Power Delivery** — STUSB4500 (20 V) + chargeur BQ24610, 12,6 V / 2 A |")
sub(u"| Signalisation | rampe LED haute puissance (PWM) + sirène 24 V |",
    u"| Signalisation | rampe LED haute puissance (PWM) + sirène **12 V** |")
sub(u"| Liaison drone | DJI Payload SDK V3 sur UART (bouton « LARGUER » dans DJI Pilot 2) |",
    u"| Commande | **liaison LoRa seule** — ARMER puis LARGUER, AES-128 + anti-rejeu |\n"
    u"| État | 4 LED : charge, fin de charge / défaut, USB-C PD établi, alerte BMS |")
sub(u"| Circuit imprimé | 96 × 66 mm, 4 couches, 1,6 mm, vernis noir mat, finition ENIG |",
    u"| Circuit imprimé | **134 × 66 mm**, 4 couches, 1,6 mm, vernis noir mat, finition ENIG, 226 composants |")

# ---------------------------------------------------------------- architecture block
old_arch_start = s.index(u"```\n E-Port V2 VCC")
old_arch_end = s.index(u"```", old_arch_start + 4) + 3
sub(s[old_arch_start:old_arch_end], u"""```
 PACK 3S LiPo    ┌──────────────────── ÉNERGIE ───────────────────────┐
 2200 mAh       │ XT30 + équilibrage XH ► BQ76920 (BMS) ► PACK_P            │
 9,0 – 12,6 V ►│   └► protections matérielles : OV / UV / OC / SC / T°      │
                │ PACK_P ► fusible 10 A ► TVS ► LM74700 (diode idéale) ► VIN  │
 USB-C PD ►──────┤ STUSB4500 (20 V) ► BQ24610 ► 12,6 V / 2 A ► PACK_P        │
                └───────────────────────────────────────────────────┘
                ┌──────────────────── PUISSANCE ─────────────────────┐
                │ VIN ─► LMR51430 ─► 3,3 V ─► ferrite ─► 3,3 V RF            │
                │ 3,3 V ─► TPS61040 (élévateur) ─► 12 V drivers de grille      │
                │ VIN ─► ARM : P-MOSFET ─► V_ACT ┬► MAINTIEN (FIRE)            │
                │                               └► ÉJECTION (FIRE)           │
                │ VIN ─► UCC27511A ► OptiMOS ─► RAMPE LED 12 V (PWM 20 kHz)  │
                │ VIN ─► UCC27511A ► OptiMOS ─► SIRÈNE 12 V                  │
                └───────────────────────────────────────────────────┘
                ┌───────────────────── LOGIQUE ─────────────────────┐
                │ STM32U585 ◄─ SPI ─► SX1262 ► AS179 ► SMA 868 MHz            │
                │ I²C ◄► BQ76920 + STUSB4500 (état du pack, PD)              │
                │ ADC : pack, I_MAINTIEN, I_ÉJECTION, I_LED · SWD · LED RGB     │
                └───────────────────────────────────────────────────┘
```""")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("01_SPEC_ELECTRONIQUE.md : %d remplacements (en-tete + architecture)" % n)
