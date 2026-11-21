# BRC-M400 Rev C — Buoy Release & Beacon Controller
## Spécification électronique — Équipe INSATECH — AeroDay V14, Challenge CAO

**Carte de commande du largage de bouée et de la signalisation de détresse, embarquée sous DJI Matrice 400.**

| | |
|---|---|
| Équipe | **INSATECH** |
| Référence | BRC-M400 **Rev C** |
| Porteur | DJI Matrice 400 — port E-Port V2 (face inférieure) |
| Actionneurs | **électroaimant de maintien à sécurité positive** + **solénoïde d'éjection**, verrouillés par un interrupteur ARM |
| Signalisation | rampe LED haute puissance (PWM) + sirène 24 V |
| Calcul / radio | STM32U585 (Cortex-M33) + Semtech SX1262 (LoRa 868 MHz) |
| Liaison drone | DJI Payload SDK V3 sur UART (bouton « LARGUER » dans DJI Pilot 2) |
| Circuit imprimé | 96 × 66 mm, 4 couches, 1,6 mm, vernis noir mat, finition ENIG |
| Fichiers | `BRC-M400/` (KiCad 10) · `exports/` (PDF, BOM, STEP, rendus 3D) · `../03_SIMULATION/electronique/` |

---

## 1. Architecture

```
 E-Port V2 VCC   ┌───────────────────────── PUISSANCE ──────────────────────────┐
 13,8-24 V, 5 A ►│ XT30 ► fusible 5 A ► TVS SMAJ26A ► diode idéale LM74700 ─► VIN │
                 │                                                                │
                 │ VIN ─► LMR51430 ─► 3,3 V ─► ferrite ─► 3,3 V RF               │
                 │ VIN ─► LDO TPS7A4101 ─► 11,85 V (drivers de grille)            │
                 │ VIN ─► ARM : P-MOSFET SUD50P06-15 ─► V_ACT ─┬► MAINTIEN (FIRE)  │
                 │                                             └► ÉJECTION (FIRE)  │
                 │ VIN ─► UCC27511A ► OptiMOS ─► RAMPE LED (PWM 20 kHz)           │
                 │ VIN ─► UCC27511A ► OptiMOS ─► SIRÈNE                           │
                 └────────────────────────────────────────────────────────────────┘
                 ┌───────────────────────── LOGIQUE ────────────────────────────┐
 UART E-Port ◄──►│ STM32U585 ◄─ SPI ─► SX1262 ─► switch AS179 ─► SMA 868 MHz      │
                 │ ADC : VIN, I_MAINTIEN, I_ÉJECTION, I_LED · SWD · LED RGB        │
                 └────────────────────────────────────────────────────────────────┘
```

### Cinq principes, tous vérifiés en simulation (§10)

1. **Charge tenue sans énergie.** L'aimant de maintien est **à sécurité positive** : son aimant permanent tient la bouée, et la bobine alimentée annule le champ pour la **libérer**. Toute perte d'énergie, tout reset ou toute perte de liaison **laisse la bouée accrochée**, comme l'exige le CDC §V.1 (« intrinsèquement sûr »).
2. **Double barrière ARM / FIRE.** Pour lâcher la bouée, il faut **à la fois** l'interrupteur côté haut (ARM, qui alimente V_ACT) **et** l'étage côté bas (FIRE). Un défaut unique ne suffit donc pas : une broche du MCU qui bascule par erreur ou un MOSFET en court-circuit ne déclenche rien.
3. **Rails indépendants.** Le 3,3 V et le 12 V sont produits directement depuis VIN, jamais en cascade : un appel de courant des actionneurs ne peut pas faire chuter le MCU ni la radio.
4. **Entrée protégée par diode idéale.** Sur un court-circuit ou une coupure de l'E-Port, le condensateur réservoir reste chargé et le MCU continue de fonctionner.
5. **Confirmation par la mesure.** Le courant de chaque bobine est mesuré. Le creux de courant qui marque la fin de course du solénoïde confirme l'éjection, et la balise ne s'allume qu'**après** cette confirmation.

---

## 2. Interface DJI Matrice 400

Le M400 dispose de **4 ports E-Port V2** en partie basse, **120 W par port**. Le kit de développement E-Port V2 (réf. CP.EN.00000644-01) les convertit en connecteurs standard :

| Sortie du kit | Caractéristique | Usage sur BRC-M400 |
|---|---|---|
| XT30 « VCC » | 13,8 / 17,02 / **24 V** @ 5 A | **Alimentation de la carte (J1)** — réglage 24 V |
| UART / PPS | TTL **3,3 V** | **Liaison PSDK V3 avec le contrôleur de vol (J2)** |

- **Connecteurs de puissance :** toutes les entrées et sorties sont en **XT30**, le standard du kit DJI. L'entrée est un XT30 mâle ; les quatre sorties (LED, maintien, éjection, sirène) sont des XT30 femelles.
- **Polarité :** sur l'empreinte KiCad, la broche 1 est « − » et la broche 2 « + ».
- **Niveaux logiques :** le MCU est en 3,3 V natif, donc aucun adaptateur de niveau n'est nécessaire.

### Liaison avec le contrôleur de vol (PSDK)

DJI publie la bibliothèque précompilée **`psdk_lib/lib/armcc_cortex-m33`** : le STM32U585 la fait tourner telle quelle, sans portage.

| Fonction PSDK | Usage |
|---|---|
| Widgets dans DJI Pilot 2 | **« ARMER »**, **« LARGUER »**, **« BALISE »**, remontée d'état (bouée présente, courants) |
| Abonnement à la télémétrie | Altitude, vitesse et position GPS → **verrouillage logiciel** : largage autorisé seulement sous une altitude et une vitesse plafond |

> Le firmware se compile sous **Keil MDK**, car la bibliothèque DJI est compilée avec Arm Compiler 6. Le brochage UART du kit E-Port V2 est à vérifier dans la documentation DJI.

---

## 3. Microcontrôleur — STM32U585CIU6

| Critère | STM32U585 |
|---|---|
| Cœur | Cortex-M33 à **160 MHz**, FPU, DSP |
| Mémoire | 2 Mo de flash, 786 Ko de RAM |
| Consommation | ≈ 19 µA/MHz |
| Sécurité | **TrustZone** ; AES, PKA et générateur aléatoire matériels |
| PSDK | **Bibliothèque DJI officielle `armcc_cortex-m33`** |

**Horloge :** l'oscillateur interne MSI est recalé en boucle sur le quartz 32,768 kHz (précision ±0,25 %). Cela suffit pour l'UART à 921 600 bauds, donc pas de quartz HSE. Le quartz 32 kHz a une capacité de charge de 7 pF, d'où des condensateurs de 10 pF.

**Affectation des broches** (à valider dans STM32CubeMX) :

| Fonction | Broches |
|---|---|
| UART PSDK | USART1 — PA9 / PA10 |
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
- **Deux chemins de commande indépendants :** LoRa depuis le sol, et PSDK depuis le drone.

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
| J1 | XT30PW-M | Entrée E-Port V2 |
| F1 | Fusible 5 A / 32 V | Calibre de l'E-Port |
| D1 | SMAJ26A | Tension de veille 26 V, au-dessus des 24 V nominaux ; claquage sous les 38 V maximum du convertisseur |
| U1 + Q1 | **LM74700-Q1** + **BSC028N06LS3** | Diode idéale : ~20 mV de chute, blocage du courant inverse en < 1 µs |
| C1 | 100 nF entre VCAP et ANODE | Pompe de charge du LM74700 (≥ 0,1 µF selon le datasheet) |
| C3 | 470 µF / 35 V | Réservoir d'énergie : pics de courant et maintien en cas de coupure |

### 5.2 Rails

| Rail | Circuit | Dimensionnement |
|---|---|---|
| **+3V3** (logique) | **TI LMR51430XDDCR** — 36 V, 3 A, PFM à 500 kHz | 0,600 × (1 + 100k / 22,1k) = **3,315 V** ; L = 15 µH (SRN6045TA) ; 2 × 22 µF |
| **+3V3_RF** | Ferrite BLM18PG600 + 10 µF / 100 nF | Isole le SX1262 du bruit de commutation |
| **+12V_GD** (drivers de grille) | **TI TPS7A4101** — LDO 50 V, 25 µA de repos | 1,173 × (1 + 91k / 10k) = **11,85 V** ; ≥ 4,7 µF en sortie (datasheet) ; ~60 mW dissipés à 24 V |

- **Alimentation des grilles en 12 V :** les MOSFET sont attaqués avec Vgs = 11,85 V, ce qui donne leur RDS(on) nominal (1,8 mΩ mesuré en simulation).
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

> **Séquencement obligatoire dans le firmware.** Si toutes les charges fonctionnent en même temps, la carte tire **4,25 A** sur l'E-Port : c'est sous la limite de 5 A, mais la marge est faible (simulé). Le firmware enchaîne donc les phases :
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
| Colonne gauche | Entrée de puissance ; convertisseur 3,3 V et LDO 12 V en dessous ; C3 |
| Haut centre | MCU et SWD ; connecteurs PSDK et micro-rupteurs sur le bord haut |
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
| Composants | **Placés** |
| Plans | **Remplis** |
| Contrôle des règles (DRC) | **Aucune erreur** d'isolement, de chevauchement d'empreintes ou de perçage |
| Pistes | **Non routées** : 235 liaisons à tracer |

### 7.5 Correctif de la Rev C

Le nom de réseau `LED_G` servait à la fois pour la voie verte de la LED RGB (sortie du MCU) et pour la grille du MOSFET de la rampe LED. Cela aurait appliqué **12 V sur une broche du MCU**.
- **Correction :** les réseaux de la rampe sont renommés `LEDA_*`.
- **Prévention :** le générateur refuse désormais tout réseau partagé entre feuilles qui n'a pas été déclaré comme tel.

---

## 8. Bilan de puissance (VIN = 24 V)

| Consommateur | Courant / puissance |
|---|---|
| Logique en attente (MCU + SX1262 en réception + LDO) | ≈ 0,1 W |
| Émission SX1262 à +22 dBm | 0,45 W pendant 165 ms |
| Aimant de maintien (impulsion de libération) | 0,42 A, soit 10 W |
| Solénoïde d'éjection (impulsion de 60 ms) | 1,5 A, soit 36 W |
| Rampe LED | 1,88 A, soit 45 W (22,5 W en flash à 50 %) |
| Sirène | 0,5 A, soit 12 W |
| **Tout en même temps (simulé)** | **4,25 A** — limite E-Port de 5 A, d'où le séquencement |
| **Séquencé (largage, puis balise)** | **≤ 2,5 A** |

---

## 9. Points ouverts

| # | Sujet | Action |
|---|---|---|
| 1 | Choix précis de l'aimant à sécurité positive et du solénoïde 24 V | Déterminent les courants réels et la force de maintien |
| 2 | Valeurs RF `TUNE` | Nomenclature Semtech E449V01A, puis analyseur de réseau |
| 3 | Table de vérité de l'AS179-92LF | Datasheet Skyworks |
| 4 | Brochage de l'UART du kit E-Port V2 | Documentation DJI PSDK |
| 5 | Fichier STM32CubeMX `.ioc` | Valider l'affectation ADC et timers |
| 6 | Routage | Boucles de commutation → ligne RF → boucles de grille et mesures Kelvin → signaux |

---

## 10. Simulations (détail : `../03_SIMULATION/electronique/RAPPORT_SIMULATION_ELEC.md`)

| # | Circuit simulé | Résultat clé |
|---|---|---|
| 1 | Convertisseur 3,3 V, commutation réelle | 3,315 V ; 3,3 mV d'ondulation ; échelon d'émission LoRa : −19,6 mV (0,6 %) |
| 2 | Intégrité d'alimentation | Tout simultané : 4,25 A ; **court-circuit E-Port de 30 ms : 3,3 V tenu (LM74700), mais effondré en 85 µs avec un P-MOSFET passif** |
| 3 | Rampe LED en PWM | RDS(on) de 1,8 mΩ ; 10 mW de pertes ; Tj ≈ 25 °C ; 66 V sans roue libre |
| 4 | Sirène | 66 V sans diode, contre 24,3 V avec la SS34 |
| 5 | **Solénoïde d'éjection (modèle électromécanique)** | Fin de course à 23 ms ; **éjection confirmée par le creux de courant à 23,6 ms** ; retour du plongeur en 22 ms (contre 40 ms avec une diode seule) ; drain ≤ 48,2 V |
| 6 | **Aimant de maintien** | **Libération 3,2 ms après l'ordre FIRE** ; démagnétisation en 1,7 ms (contre 7,5 ms) ; drain ≤ 47,6 V |
| 7 | Bilan de liaison LoRa | 40 dB de marge à 15 km en SF9 |

---

## Sources

- [DJI PSDK — Standard Hardware Port](https://developer.dji.com/doc/payload-sdk-tutorial/en/quick-start/drone-port.html) · [DJI Matrice 400 specs](https://enterprise.dji.com/matrice-400/specs) · [E-Port V2 Development Kit](https://store.dji.com/bg/product/dji-e-port-v2-development-kit) · [Payload-SDK (psdk_lib/lib)](https://github.com/dji-sdk/Payload-SDK)
- [Semtech SX1261/2 datasheet](https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf) · [Semtech AN1200.40](https://cdn-reichelt.de/documents/datenblatt/A200/SX1262REFERENCE.pdf)
- [TI LMR51430](https://www.ti.com/lit/ds/symlink/lmr51430.pdf) · [TI LM74700-Q1](https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf) · [TI TPS7A4101](https://www.ti.com/lit/ds/symlink/tps7a4101.pdf)
