# BRC-M400 Rev D — Buoy Release & Beacon Controller
## Spécification électronique — Équipe INSATECH — AeroDay V14, Challenge CAO

**Module autonome de largage de bouée et de signalisation de détresse, emporté sous DJI Matrice 400.**

> **Changement majeur en Rev D : le module n'a plus aucune liaison électrique avec le drone.**
> Il porte son énergie (pack 3S LiPo 2200 mAh + BMS) et reçoit ses ordres par LoRa. L'intégration
> mécanique se réduit à une fixation, et **la balise reste alimentée une fois la bouée au sol**.

| | |
|---|---|
| Équipe | **INSATECH** |
| Référence | BRC-M400 **Rev D** |
| Porteur | DJI Matrice 400 — **fixation mécanique seule, aucun connecteur vers le drone** |
| Énergie | **pack 3S LiPo 2200 mAh** (9,0 – 12,6 V, 24,4 Wh) + BMS BQ76920 |
| Recharge | **USB-C Power Delivery** — STUSB4500 (20 V) + chargeur BQ24610, 12,6 V / 2 A |
| Actionneurs | **électroaimant de maintien à sécurité positive** + **solénoïde d'éjection**, verrouillés par un interrupteur ARM |
| Signalisation | rampe LED haute puissance (PWM) + sirène **12 V** |
| Calcul / radio | STM32U585 (Cortex-M33) + Semtech SX1262 (LoRa 868 MHz) |
| Commande | **liaison LoRa seule** — ARMER puis LARGUER, AES-128 + anti-rejeu |
| État | 4 LED : charge, fin de charge / défaut, USB-C PD établi, alerte BMS |
| Circuit imprimé | **134 × 66 mm**, 4 couches, 1,6 mm, vernis noir mat, finition ENIG, 226 composants |
| Fichiers | `BRC-M400/` (KiCad 10) · `exports/` (PDF, BOM, STEP, rendus 3D) · `../03_SIMULATION/electronique/` |

---

## 1. Architecture

```
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
```

### Cinq principes, tous vérifiés en simulation (§10)

1. **Charge tenue sans énergie.** L'aimant de maintien est **à sécurité positive** : son aimant permanent tient la bouée, et la bobine alimentée annule le champ pour la **libérer**. Toute perte d'énergie, tout reset ou toute perte de liaison **laisse la bouée accrochée**, comme l'exige le CDC §V.1 (« intrinsèquement sûr »).
2. **Double barrière ARM / FIRE.** Pour lâcher la bouée, il faut **à la fois** l'interrupteur côté haut (ARM, qui alimente V_ACT) **et** l'étage côté bas (FIRE). Un défaut unique ne suffit donc pas : une broche du MCU qui bascule par erreur ou un MOSFET en court-circuit ne déclenche rien.
3. **Rails indépendants.** Le 3,3 V et le 12 V sont produits directement depuis VIN, jamais en cascade : un appel de courant des actionneurs ne peut pas faire chuter le MCU ni la radio.
4. **Entrée protégée par diode idéale.** Sur un rebond de connecteur ou une coupure du BMS, le condensateur réservoir reste chargé et le MCU continue de fonctionner (simulé : 30 ms sans redémarrage).
5. **Confirmation par la mesure.** Le courant de chaque bobine est mesuré. Le creux de courant qui marque la fin de course du solénoïde confirme l'éjection, et la balise ne s'allume qu'**après** cette confirmation.

---

## 2. Autonomie énergétique et recharge

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

## 3. Microcontrôleur — STM32U585CIU6

| Critère | STM32U585 |
|---|---|
| Cœur | Cortex-M33 à **160 MHz**, FPU, DSP |
| Mémoire | 2 Mo de flash, 786 Ko de RAM |
| Consommation | ≈ 19 µA/MHz |
| Sécurité | **TrustZone** ; AES, PKA et générateur aléatoire matériels |
| I²C | **BQ76920 (BMS) + STUSB4500 (USB-C PD)** sur le même bus |

**Horloge :** l'oscillateur interne MSI est recalé en boucle sur le quartz 32,768 kHz (précision ±0,25 %). Cela suffit pour l'UART à 921 600 bauds, donc pas de quartz HSE. Le quartz 32 kHz a une capacité de charge de 7 pF, d'où des condensateurs de 10 pF.

**Affectation des broches** (à valider dans STM32CubeMX) :

| Fonction | Broches |
|---|---|
| I²C BMS / PD | PA9 / PA10 (instance à confirmer sous CubeMX ; repli I²C logiciel possible) |
| Radio SX1262 | SPI1 — PA5 / PA6 / PA7 · PA4 (NSS) · PB0 (RESET) · PB1 (BUSY) · PB2 (DIO1) · PB10 (RF_RXEN) |
| Mesures ADC1 | PA0 (VIN) · PA1 (I_MAINTIEN) · PA2 (I_LED) · PA3 (I_ÉJECTION) |
| Actionneurs | **PB12 ARM** · PA8 TIM1_CH1 (PWM maintien) · PA15 TIM2_CH1 (PWM éjection) |
| Signalisation | PB14 TIM15_CH1 (PWM LED) · PB13 (sirène) |
| Divers | PB4 / PB5 (micro-rupteurs) · PB6–PB8 TIM4 (LED RGB) · PA13 / PA14 / PB3 (SWD + SWO) · PH3 (BOOT0) |

---

## 4. Radio — Semtech SX1262

- **SX1262 :** +22 dBm en émission ; sensibilité de −137 dBm en SF12 / BW 125 kHz ; 4,6 mA en réception.
- **Fréquence :** 869,525 MHz, sous-bande **g3** (500 mW PAR autorisés avec 10 % de rapport cyclique), soit une exploitation légale des +22 dBm.
- **Pourquoi pas 2,4 GHz :** c'est la bande de la liaison de commande O4 du M400, donc écartée.
- **Pourquoi pas la 4G :** elle dépend d'un réseau terrestre, le premier à tomber lors d'une inondation.

**Bilan de liaison :** marge de **40 dB à 15 km en SF9**, pour 165 ms de temps d'antenne par trame (§10).

**Protocole :**
- ARMER puis LARGUER, avec une fenêtre de validité de 10 s.
- AES-128 et compteur anti-rejeu.
- Accusé de réception et 3 retransmissions.
- **Chemin de commande unique, donc durci :** ARMER puis LARGUER, AES-128, compteur anti-rejeu, accusé de réception et 3 retransmissions.

**Front-end RF :** topologie du design de référence **Semtech E449V01A** (AN1200.40).
- **Alimentation :** DC-DC du cœur avec une inductance de 15 µH.
- **Horloge :** TCXO 32 MHz alimenté par DIO3, relié à XTA par 220 Ω + 10 pF.
- **Émission :** adaptation d'impédance, réjecteur du 2ᵉ harmonique et filtre passe-bas en π.
- **Réception :** balun.
- **Commutateur émission/réception :** AS179-92LF, commandé par DIO2 et RF_RXEN.
- **Antenne :** SMA en bord de carte.

> ⚠ Les valeurs marquées **`TUNE`** proviennent de la nomenclature régionale de Semtech, à obtenir sur demande, puis s'ajustent à l'analyseur de réseau.

---

## 5. Alimentation

### 5.1 Protection d'entrée

| Rep. | Composant | Rôle |
|---|---|---|
| J42 | XT30PW-M | Entrée pack 3S (feuille 6) |
| F1 | Fusible 10 A / 32 V | Protection du pack |
| D1 | SMAJ26A | Tension de veille 26 V, au-dessus des 24 V nominaux ; claquage sous les 38 V maximum du convertisseur |
| U1 + Q1 | **LM74700-Q1** + **BSC028N06LS3** | Diode idéale : ~20 mV de chute, blocage du courant inverse en < 1 µs |
| C1 | 100 nF entre VCAP et ANODE | Pompe de charge du LM74700 (≥ 0,1 µF selon le datasheet) |
| C3 | 470 µF / 35 V | Réservoir d'énergie : pics de courant et maintien en cas de coupure |

### 5.2 Rails

| Rail | Circuit | Dimensionnement |
|---|---|---|
| **+3V3** (logique) | **TI LMR51430XDDCR** — 36 V, 3 A, PFM à 500 kHz | 0,600 × (1 + 100k / 22,1k) = **3,315 V** ; L = 15 µH (SRN6045TA) ; 2 × 22 µF |
| **+3V3_RF** | Ferrite BLM18PG600 + 10 µF / 100 nF | Isole le SX1262 du bruit de commutation |
| **+12V_GD** (drivers de grille) | **TI TPS61040** — élévateur depuis le 3,3 V | 1,233 × (1 + 1M / 113k) = **11,96 V** ; L = 10 µH ; **indépendant de la tension pack** |

- **Alimentation des grilles en 12 V :** les MOSFET sont attaqués avec Vgs = 11,96 V, ce qui donne leur RDS(on) nominal (1,75 mΩ mesuré en simulation). Un LDO n'aurait pas pu : à 9 V de pack, il ne sortirait plus 12 V. L'élévateur garde Vgs nominal **jusqu'à la fin de la décharge**.
- **Superviseur TPS3808G33 :** sortie drain ouvert, il partage NRST avec la sonde SWD et le watchdog sans conflit. Seuil de reset : 3,07 V.

---

## 6. Étages de puissance

### 6.1 Interrupteur ARM (barrière n°1)

| Rep. | Composant | Rôle |
|---|---|---|
| Q30 | **SUD50P06-15** (P-MOSFET −60 V, 15 mΩ, DPAK) | Alimente V_ACT, le rail des actionneurs |
| R30 / R33 | 10 kΩ / 10 kΩ | Pont diviseur de grille : Vgs = −VIN / 2 = **−12 V à 24 V** (maximum ±20 V) |
| Q31, R34 / R35 | MMBT3904 + polarisation | Commande ACT_ARM depuis PB12. R35 maintient V_ACT **coupé pendant un reset** |
| C80 / C81 | 100 µF / 35 V + 10 µF | Réservoir local des bobines |

### 6.2 Voies bobines : maintien (barrière n°2) et éjection

Les deux voies sont identiques :

| Fonction | Composants |
|---|---|
| Driver de grille | **UCC27511A** : 4 A en charge, 8 A en décharge ; 4,7 Ω à l'allumage, 1 Ω à l'extinction ; rappel de grille de 10 kΩ |
| Interrupteur | **BSC028N06LS3** côté bas (60 V, 2,8 mΩ), commandable en PWM (TIM1 / TIM2) pour le mode « peak & hold » |
| **Démagnétisation rapide** | Schottky **SS34** + TVS **SMAJ20A** vers V_ACT. La tension de drain est limitée à **VIN + 0,5 + 23 V ≈ 48 V**, sous les 60 V du MOSFET. La décroissance du courant est **4,4 fois plus rapide** qu'avec une diode seule (simulé) |
| Mesure | Shunt de 10 mΩ + **INA181A2** (gain 50) : 2 A donnent 1,0 V sur l'ADC |
| Sortie | XT30PW-F |

**Électroaimant de maintien — choix du type d'aimant :**
- **Préconisé : un aimant à sécurité positive** (« fail-safe holding electromagnet », aimant permanent + bobine d'annulation), par exemple en 24 V / 10 W.
- **Avec un aimant classique** (bobine alimentée = maintien), la même carte fonctionne : le firmware inverse la logique et utilise la PWM pour réduire la puissance de maintien. Mais la bouée tomberait alors à chaque perte d'énergie, ce qui **contredit le CDC**.

**Solénoïde d'éjection :** solénoïde pousseur 24 V, alimenté par une impulsion de 60 ms. **L'éjection est confirmée** par le creux de courant qui apparaît pendant la course du plongeur (§10).

### 6.3 Signalisation de détresse

| Voie | Composants | Remarque |
|---|---|---|
| Rampe LED | UCC27511A + BSC028N06LS3, PWM à 20 kHz ; roue libre **SS54** ; shunt de 10 mΩ + INA181A2 | Permet de détecter une balise hors service |
| Sirène | UCC27511A + BSC028N06LS3 ; roue libre **SS34** | — |

- **Alimentation :** les deux voies sont alimentées en VIN, il faut donc des modèles **24 V**.
- **Déclenchement :** elles ne s'allument **qu'après** la confirmation du largage.

> **Séquencement conservé dans le firmware.** Toutes charges actives, la carte tire **5,20 A** du pack (simulé) — moins de 3C, donc sans danger pour un 2200 mAh. Le séquencement reste appliqué pour ménager les cellules et la durée de signalisation :
> 1. **Largage :** maintien + éjection ≈ 2 A.
> 2. **Signalisation :** LED + sirène ≈ 2,4 A.
>
> Le courant réel reste ainsi sous **2,5 A**.

---

## 7. Circuit imprimé

### 7.1 Empilage et règles de routage

**Empilage 4 couches, 1,6 mm :**

| Couche | Fonction |
|---|---|
| L1 | Composants, signaux, RF |
| L2 | **Plan de masse continu**, jamais découpé |
| L3 | Plans d'alimentation : +3V3 (zone MCU / RF), VIN (entrée et zone des actionneurs) |
| L4 | Masse + marquage au dos |

- **Diélectriques :** 0,2 mm (εr 4,4) entre L1 et L2.
- **Ligne RF 50 Ω :** ≈ 0,36 mm de largeur sur L1.
- **Coutures de masse :** 145 vias, aucun dans le couloir RF.

**Règles inscrites dans le projet :**

| Règle | Valeur |
|---|---|
| Isolement minimal | 0,1 mm (capacité du fabricant) |
| Perçage minimal | 0,2 mm |
| Classe **Default** | 0,15 mm d'isolement · pistes de 0,2 mm |
| Classe **POWER** | 0,15 mm d'isolement · pistes de **1,0 mm** · vias de 0,8 / 0,4 mm |
| Classe **RF50** | Pistes de **0,36 mm** |

- **Réseaux en POWER :** VIN, V_ACT, les drains des bobines, de la LED et de la sirène, et les sources sur shunt.
- **Réseaux en RF50 :** toute la chaîne 868 MHz.

> Un isolement de 0,15 mm est suffisant jusqu'à 48 V sous vernis : IPC-2221 demande 0,13 mm entre 31 et 100 V.

### 7.2 Placement

| Zone | Contenu |
|---|---|
| Bande gauche | **Bloc énergie** : USB-C, STUSB4500, chargeur BQ24610, BMS BQ76920, pack et équilibrage, LED d'état |
| Colonne suivante | Entrée pack protégée ; convertisseur 3,3 V et élévateur 12 V ; C3 |
| Haut centre | MCU et SWD ; micro-rupteurs sur le bord haut |
| Haut droit | Radio, chaîne RF en ligne dans l'ordre du signal, SMA en bord de carte |
| Bas | **Une colonne par voie de puissance**, au-dessus de son XT30 : LED, MAINTIEN, ÉJECTION (bord bas), SIRÈNE (bord droit) |

- **Dans chaque colonne :** driver → MOSFET → shunt, alignés pour que la boucle de grille soit la plus courte possible.
- **ARM :** Q30 est placé entre les voies de maintien et d'éjection.
- **Marquage :** « INSATECH » en face avant et au dos.

### 7.3 Livrables CAO

- **Modèle 3D :** `exports/BRC-M400_PCB.step`.
  > Les XT30 ne sont pas inclus : leurs modèles 3D sont au format VRML, que l'export STEP n'embarque pas. Importer un STEP de fabricant dans SolidWorks.
- **Rendus :** `exports/3d/` (dessus, isométrie, arrière, dessous).

### 7.4 État d'avancement

| Élément | État |
|---|---|
| Composants | **Placés** (163 empreintes, 534 pastilles CMS + 74 traversantes) |
| Plans | **Remplis** |
| Contrôle des règles (DRC) | **Aucune erreur** d'isolement, de court-circuit ni de perçage |
| ERC du schéma | **0 violation** ; netlist extraite identique à la référence (**0 écart**) |
| Pistes | **Routées** : 1 414 pistes, 424 vias, 2,66 m de cuivre (F.Cu 935 · In1 223 · In2 215 · B.Cu 41) |
| Reste à router | **30 liaisons**, concentrées autour du MCU et de la radio |

### 7.5 Correctif de la Rev C

Le nom de réseau `LED_G` servait à la fois pour la voie verte de la LED RGB (sortie du MCU) et pour la grille du MOSFET de la rampe LED. Cela aurait appliqué **12 V sur une broche du MCU**.
- **Correction :** les réseaux de la rampe sont renommés `LEDA_*`.
- **Prévention :** le générateur refuse désormais tout réseau partagé entre feuilles qui n'a pas été déclaré comme tel.

---

## 8. Bilan d'énergie (pack 3S, 24,4 Wh)

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

## 9. Points ouverts

| # | Sujet | Action |
|---|---|---|
| 1 | Choix précis de l'aimant à sécurité positive et du solénoïde 24 V | Déterminent les courants réels et la force de maintien |
| 2 | Valeurs RF `TUNE` | Nomenclature Semtech E449V01A, puis analyseur de réseau |
| 3 | Table de vérité de l'AS179-92LF | Datasheet Skyworks |
| 4 | Seuils BMS (surintensite, coupure basse tension) | A ecrire en NVM du BQ76920 selon le pack retenu |
| 5 | Fichier STM32CubeMX `.ioc` | Valider l'affectation ADC et timers |
| 6 | Routage | Boucles de commutation → ligne RF → boucles de grille et mesures Kelvin → signaux |

---

## 10. Simulations (détail : `../03_SIMULATION/electronique/RAPPORT_SIMULATION_ELEC.md`)

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

## Sources

- [DJI Matrice 400 specs](https://enterprise.dji.com/matrice-400/specs)
- [Semtech SX1261/2 datasheet](https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf) · [Semtech AN1200.40](https://cdn-reichelt.de/documents/datenblatt/A200/SX1262REFERENCE.pdf)
- [TI LMR51430](https://www.ti.com/lit/ds/symlink/lmr51430.pdf) · [TI LM74700-Q1](https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf) · [TI TPS61040](https://www.ti.com/lit/ds/symlink/tps61040.pdf) · [TI BQ24610](https://www.ti.com/lit/ds/symlink/bq24610.pdf) · [TI BQ76920](https://www.ti.com/lit/ds/symlink/bq76920.pdf) · [ST STUSB4500](https://www.st.com/resource/en/datasheet/stusb4500.pdf)
