# -*- coding: utf-8 -*-
"""Rev D: replace section 2 (DJI interface), 8 (power budget) and 10 (simulations)."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "01_SPEC_ELECTRONIQUE.md")
s = io.open(p, encoding="utf-8").read()

SEC2 = u"""## 2. Autonomie énergétique et recharge

Le module ne reçoit **ni énergie ni ordre** du drone : il n'y a aucun connecteur entre les deux.
Ce choix est ce qui permet à la **balise de continuer à fonctionner une fois la bouée au sol**,
quand le drone est reparti — c'est précisément la fonction demandée par le cahier des charges.

### 2.1 Pack et protections

| Élément | Choix | Justification |
|---|---|---|
| Pack | **3S LiPo 2200 mAh** (9,0 – 12,6 V, 24,4 Wh) | 3 cellules donnent 12 V nominal : assez pour les actionneurs sans élévateur de puissance |
| BMS | **BQ76920** (AFE 3–5S, I²C) | Surcharge, décharge profonde, surintensité, court-circuit, température, **équilibrage** |
| Coupure | 2 MOSFET **BSC028N06LS3** tête-bêche (CHG / DSG) | La protection est **matérielle** : elle agit sans le microcontrôleur |
| Mesure | shunt **5 mΩ** + SRP/SRN | Courant pack lu par le BMS, remonté en I²C puis par radio |
| Connectique | XT30 (puissance) + JST-XH 4 points (équilibrage) | Standard des packs de modélisme |

> **Pourquoi un BMS à mesure cellule par cellule plutôt qu'un simple circuit de protection ?**
> Parce qu'il permet de **remonter l'état réel du pack au pilote avant le vol** (tension de chaque
> cellule, température, courant) : on ne décolle pas avec un pack déséquilibré ou trop froid.

### 2.2 Recharge USB-C Power Delivery

| Élément | Choix | Rôle |
|---|---|---|
| Négociation | **STUSB4500** | Sink PD **autonome** : réclame 20 V même carte éteinte, sans firmware |
| Chargeur | **BQ24610** (buck synchrone, 5–28 V) | 2,1 V × (1 + 100k/20k) = **12,6 V** ; **2 A** (1C) avec un shunt de 10 mΩ |
| Sécurité | thermistance CTN sur le pack (entrée TS) + minuterie TTC | Pas de charge hors plage de température, arrêt sur défaut |
| Durée | ≈ **70 min** pour une charge complète | 2200 mAh à 2 A |

### 2.3 LED d'état

| LED | Couleur | Source | Signification |
|---|---|---|---|
| D42 | vert | BQ24610 STAT1 | charge en cours |
| D43 | orange | BQ24610 STAT2 | charge terminée ou défaut |
| D44 | bleu | STUSB4500 POWER_OK2 | contrat USB-C PD établi |
| D45 | rouge | BQ76920 ALERT | alerte BMS (cellule, température, courant) |

---

"""

SEC8 = u"""## 8. Bilan d'énergie (pack 3S, 24,4 Wh)

| Consommateur | Courant / puissance |
|---|---|
| Veille (MCU + SX1262 en réception) | ≈ 0,1 W — **plusieurs jours d'attente** |
| Émission SX1262 à +22 dBm | 0,45 W pendant 165 ms |
| Aimant de maintien (impulsion de libération) | 0,83 A, soit 10 W |
| Solénoïde d'éjection (impulsion de 60 ms) | 2,7 A crête, soit 36 W |
| Rampe LED 12 V | 3,42 A, soit 41 W |
| Sirène 12 V | 1,0 A, soit 12 W |
| **Tout en même temps (simulé)** | **5,20 A** — moins de 3C pour le pack, sans contrainte |
| **Balise en flashs et salves (20 %)** | ≈ 11 W → **plus de 2 h d'autonomie de signalisation** |

Le largage lui-même ne coûte que quelques dizaines de millisecondes d'énergie : le
dimensionnement du pack est fixé par la **durée de signalisation**, pas par le largage.

---

"""

SEC10 = u"""## 10. Simulations (détail : `../03_SIMULATION/electronique/RAPPORT_SIMULATION_ELEC.md`)

Toutes les simulations ont été **rejouées en Rev D** avec le pack 3S. Les bobines sont rebobinées
pour 12 V à puissance constante (R et L divisés par 4), ce qui **conserve la constante de temps
L/R** et donc la chronologie mécanique.

| # | Circuit simulé | Résultat clé |
|---|---|---|
| 1 | Convertisseur 3,3 V, commutation réelle | 3,315 V ; 2,6 mV d'ondulation ; échelon d'émission LoRa : −18,5 mV (0,56 %) |
| 2 | Intégrité d'alimentation | Tout simultané : 5,20 A, VIN min 11,0 V ; **interruption de 30 ms : 3,3 V tenu** (35 µs sans diode idéale) |
| 3 | Rampe LED en PWM | 3,42 A ; RDS(on) 1,75 mΩ ; **15 mW** de pertes ; Tj ≈ 26 °C ; 66,4 V sans roue libre |
| 4 | Sirène | 1,00 A ; 12,4 V avec la SS34 contre 66,2 V sans |
| 5 | **Solénoïde d'éjection** | Fin de course à 23,1 ms ; **éjection confirmée par le creux de courant à 23,7 ms** ; drain ≤ 36,8 V |
| 6 | **Aimant de maintien** | **Libération 3,2 ms** après l'ordre FIRE ; démagnétisation 1,0 ms (contre 7,1 ms) ; drain ≤ 35,8 V |
| 7 | Bilan de liaison LoRa | 40 dB de marge à 15 km en SF9 |

---

"""

i2, i3 = s.index(u"## 2. Interface DJI Matrice 400"), s.index(u"## 3. Microcontrôleur")
s = s[:i2] + SEC2 + s[i3:]
i8, i9 = s.index(u"## 8. Bilan de puissance"), s.index(u"## 9. Points ouverts")
s = s[:i8] + SEC8 + s[i9:]
i10, isrc = s.index(u"## 10. Simulations"), s.index(u"## Sources")
s = s[:i10] + SEC10 + s[isrc:]

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("sections 2, 8 et 10 remplacees")
