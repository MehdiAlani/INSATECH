# -*- coding: utf-8 -*-
"""Align RAPPORT_SIMULATION_ELEC.md with the Rev D (12 V pack) re-run."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "RAPPORT_SIMULATION_ELEC.md")
s = io.open(p, encoding="utf-8").read()
n = 0


def sub(a, b):
    global s, n
    assert a in s, "NOT FOUND: " + a[:70]
    s = s.replace(a, b, 1)
    n += 1


sub(u"# BRC-M400 Rev C — Rapport de simulation électronique",
    u"# BRC-M400 Rev D — Rapport de simulation électronique")
sub(u"**Oui** : −19,6 mV (0,6 %), 3,3 mV d'ondulation",
    u"**Oui** : −18,5 mV (0,56 %), 2,6 mV d'ondulation")
sub(u"| 2 | Intégrité d'alimentation | Un pic de consommation ou une coupure de l'E-Port fait-il redémarrer le MCU ? | **Non, grâce au LM74700** (un P-MOSFET passif s'effondre en 85 µs) |",
    u"| 2 | Intégrité d'alimentation | Un pic de consommation ou une coupure du pack fait-il redémarrer le MCU ? | **Non, grâce au LM74700** (sans diode idéale, le 3,3 V s'effondre en 35 µs) |")
sub(u"| 3 | Rampe LED en PWM | Le MOSFET chauffe-t-il ? | **10 mW, Tj ≈ 25 °C**, pas de dissipateur |",
    u"| 3 | Rampe LED en PWM | Le MOSFET chauffe-t-il ? | **15 mW, Tj ≈ 26 °C**, pas de dissipateur |")
sub(u"| 4 | Sirène | La diode de roue libre est-elle nécessaire ? | **Oui** : 66 V (avalanche) sans elle |",
    u"| 4 | Sirène | La diode de roue libre est-elle nécessaire ? | **Oui** : 66,2 V (avalanche) sans elle |")
sub(u"**Oui** : creux de courant en fin de course, détecté à 23,6 ms",
    u"**Oui** : creux de courant en fin de course, détecté à 23,7 ms")

sub(u"## 1. Convertisseur 24 V → 3,3 V (LMR51430, rail logique)",
    u"## 1. Convertisseur 12,6 V → 3,3 V (LMR51430, rail logique)")
sub(u"| Ondulation de la sortie (en émission) | **3,3 mV crête à crête** | — |",
    u"| Ondulation de la sortie (en émission) | **2,6 mV crête à crête** | — |")
sub(u"| Échelon 30 → 160 mA (émission LoRa) | **−19,6 mV (0,6 %)** : la tension reste dans ±1 % | — |",
    u"| Échelon 30 → 160 mA (émission LoRa) | **−18,5 mV (0,56 %)** : la tension reste dans ±1 % | — |")

sub(u"## 2. Intégrité d'alimentation et court-circuit sur l'E-Port",
    u"## 2. Intégrité d'alimentation et interruption du pack")
sub(u"- Port E-Port V2 de 24 V avec son impédance (30 mΩ + câble) et le réservoir C3 de 470 µF.",
    u"- Pack 3S à 11,1 V avec son impédance interne et le réservoir C3 de 470 µF.")
sub(u"- Rampe LED : 1,88 A en flash à 1 kHz.", u"- Rampe LED : 3,42 A en flash à 1 kHz.")
sub(u"2. De 60 à 90 ms, **court-circuit de l'entrée E-Port**.",
    u"2. De 60 à 90 ms, **interruption de l'entrée** (rebond de connecteur ou coupure BMS).")
sub(u"| Courant maximal tiré sur l'E-Port, toutes charges ensemble | **4,25 A** (limite : 5 A) | identique |",
    u"| Courant maximal tiré sur le pack, toutes charges ensemble | **5,20 A** (pack 3S 2200 mAh : < 3C) | identique |")
sub(u"| VIN minimal | 23,67 V | identique |", u"| VIN minimal | 11,00 V | identique |")
sub(u"| **Rail 3,3 V pendant le court-circuit de 30 ms** | **tient à 3,315 V** (VIN reste à 23,5 V) | **passe sous 3,0 V en 85 µs → reset du MCU** |",
    u"| **Rail 3,3 V pendant l'interruption de 30 ms** | **tient à 3,315 V** (VIN reste à 10,33 V) | **passe sous 3,0 V en 35 µs → reset du MCU** |")

sub(u"## 3. Rampe LED en PWM (UCC27511A + BSC028N06LS3, grille attaquée en 12 V)",
    u"## 3. Rampe LED 12 V en PWM (UCC27511A + BSC028N06LS3, grille attaquée en 12 V)")
sub(u"- **Rampe LED 24 V :** seuil de 20 V, résistance de 2 Ω, câblage de 1 µH.",
    u"- **Rampe LED 12 V :** seuil de 9 V, résistance de 0,8 Ω, câblage de 1 µH (45 W).")
sub(u"| Courant LED / RDS(on) | 1,88 A / **1,76 mΩ** |", u"| Courant LED / RDS(on) | 3,42 A / **1,75 mΩ** |")
sub(u"| Pertes dans le MOSFET à 20 kHz | **10 mW**, soit Tj ≈ 25 °C sans dissipateur |",
    u"| Pertes dans le MOSFET à 20 kHz | **15 mW**, soit Tj ≈ 26 °C sans dissipateur |")
sub(u"| Pic de Vds au blocage | **24,4 V avec la SS54 · 66 V sans elle (avalanche)** |",
    u"| Pic de Vds au blocage | **12,5 V avec la SS54 · 66,4 V sans elle (avalanche)** |")
sub(u"- **Sans diode de roue libre :** Vds monte à **66 V** et le MOSFET passe en avalanche, avec 0,62 mJ dissipés à chaque coupure.",
    u"- **Sans diode de roue libre :** Vds monte à **66,2 V** et le MOSFET passe en avalanche, avec 2,50 mJ dissipés à chaque coupure.")

sub(u"**Modèle :** solénoïde pousseur 24 V / 16 Ω, de course 10 mm, avec un ensemble plongeur + tige de 30 g.",
    u"**Modèle :** solénoïde pousseur 12 V / 4 Ω (36 W), de course 10 mm, avec un ensemble plongeur + tige de 30 g. La bobine est reboblinée pour 12 V à puissance constante : R et L sont divisés par 4, donc la constante de temps L/R — et la chronologie mécanique — sont conservées.")
sub(u"| Pic de courant avant le démarrage du plongeur | 1,36 A à 12,6 ms |",
    u"| Pic de courant avant le démarrage du plongeur | 2,71 A à 12,6 ms |")
sub(u"| **Creux de courant pendant la course** (force contre-électromotrice) | 0,58 A |",
    u"| **Creux de courant pendant la course** (force contre-électromotrice) | 1,16 A |")
sub(u"| **Éjection confirmée par le MCU** (minimum du creux sur l'ADC) | **23,6 ms** |",
    u"| **Éjection confirmée par le MCU** (minimum du creux sur l'ADC) | **23,7 ms** |")
sub(u"| Force : au départ / en fin de course | 1,3 N / 88 N |",
    u"| Force : au départ / en fin de course | 1,3 N / 87 N |")
sub(u"| Retour du plongeur après coupure | **22 ms avec diode + TVS**, contre 40 ms avec une diode seule |",
    u"| Retour du plongeur après coupure | **18,9 ms avec diode + TVS**, contre 39,0 ms avec une diode seule |")
sub(u"| Tension de drain au blocage | 48,2 V avec diode + TVS (sous les 60 V du MOSFET) · 24,4 V avec une diode seule |",
    u"| Tension de drain au blocage | 36,8 V avec diode + TVS (sous les 60 V du MOSFET) · 12,4 V avec une diode seule |")

sub(u"**Modèle :** bobine de 24 V / 57 Ω (10 W) et 150 mH.",
    u"**Modèle :** bobine de 12 V / 14,4 Ω (10 W) et 37,9 mH — même puissance et même constante de temps que la version 24 V.")
sub(u"| Courant nominal | 0,42 A |", u"| Courant nominal | 0,83 A |")
sub(u"| Démagnétisation à 5 % (réverrouillage) | **1,7 ms avec diode + TVS**, contre 7,5 ms avec une diode seule (4,4 fois plus rapide) |",
    u"| Démagnétisation à 5 % (réverrouillage) | **1,0 ms avec diode + TVS**, contre 7,1 ms avec une diode seule (7 fois plus rapide) |")
sub(u"| Tension de drain maximale | 47,6 V (sous les 60 V du MOSFET) |",
    u"| Tension de drain maximale | 35,8 V (sous les 60 V du MOSFET) |")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("RAPPORT_SIMULATION_ELEC.md : %d remplacements" % n)
