# Brief — simulations CFD / FEA et interface mécanique de la carte

**Pour : le pôle mécanique d'INSATECH** · Projet BRC-M400 · AeroDay V14, Challenge CAO
**Échéance : 22 novembre 2026, 9 h** (dépôt Google Drive)

Ce document regroupe (1) les cotes réelles de la carte pour dessiner le châssis, (2) les cas de
charge à appliquer, (3) les réglages de simulation, (4) la liste exacte des captures exigées par le
cahier des charges.

---

## 1. Interface mécanique de la carte BRC-M400

Cotes extraites du fichier KiCad routé. **Repère : coin inférieur gauche du contour, X vers la
droite, Y vers le haut, vue de dessus.**

| Grandeur | Valeur |
|---|---|
| Contour | **96,1 × 66,1 mm**, angles arrondis |
| Épaisseur du circuit | 1,6 mm (4 couches, FR-4) |
| Assemblage | **composants sur la face supérieure uniquement** — le dessous est libre |
| Hauteur maximale au-dessus de la carte | **≈ 12 mm** (connecteurs XT30 et condensateur C80 8 × 10 mm) |
| Masse de la carte équipée | ≈ 75 g *(à peser / estimer sur le STEP)* |

### Trous de fixation — Ø 3,2 mm (vis M3)

| Trou | X (mm) | Y (mm) |
|---|---|---|
| H1 | 3,65 | 62,45 |
| H2 | 92,45 | 62,45 |
| H3 | 3,65 | 3,65 |
| H4 | 92,45 | 3,65 |

→ **Entraxes : 88,80 mm (X) × 58,80 mm (Y).** Les quatre trous sont reliés au plan de masse : prévoir
des **entretoises métalliques** si l'on veut utiliser le châssis comme masse et comme chemin
thermique.

### Connecteurs — à dégager dans le carénage

| Rep. | Fonction | X | Y | Orientation | Sort par |
|---|---|---|---|---|---|
| J1 | Entrée E-Port V2 (XT30 mâle) | 12,15 | 53,05 | 90° | bord **gauche** |
| J2 | UART PSDK vers le drone | 44,05 | 62,85 | 180° | bord **haut** |
| J6 | Micro-rupteurs verrou / présence | 66,05 | 62,85 | 180° | bord **haut** |
| J7 | SWD (programmation, 2×5 - 1,27 mm) | 27,55 | 61,55 | 90° | accès en **maintenance** |
| J20 | **Antenne SMA 868 MHz** | 92,85 | 51,05 | 0° | bord **droit**, en débord |
| J31 | Rampe LED (XT30 femelle) | 40,05 | 13,15 | 180° | bord **bas** |
| J33 | Électroaimant de maintien (XT30) | 56,05 | 13,15 | 180° | bord **bas** |
| J34 | Solénoïde d'éjection (XT30) | 72,05 | 13,15 | 180° | bord **bas** |
| J32 | Sirène (XT30) | 82,95 | 33,05 | −90° | bord **droit** |

**Contraintes à respecter :**

- **L'antenne SMA (J20) doit déboucher à l'air libre** et ne doit pas être entourée de métal ni de
  carbone : prévoir une fenêtre ou une zone en plastique sur au moins 20 mm autour du connecteur.
  Du carbone devant l'antenne ferait perdre l'essentiel de la portée.
- Les quatre XT30 du bord bas sortent **vers les actionneurs** : garder un dégagement d'au moins
  **25 mm** devant eux pour le rayon de courbure des câbles.
- Le connecteur SWD (J7) sert à programmer la carte : prévoir une trappe ou un capot démontable.
- Fichiers CAO : `04_DOSSIER_ELECTRONIQUE/BRC-M400_PCB_simplifie.step` (**5 Mo, à utiliser pour
  l'assemblage**) et `BRC-M400_PCB.step` (38 Mo, pistes et plans inclus, pour le rendu seulement).

### Thermique

Les sources de chaleur sont faibles et localisées : MOSFET BSC028N06LS3 (2,8 mΩ), LDO 12 V (~60 mW),
et les pertes de commutation de la voie LED simulées à **10 mW**. Les fortes puissances (rampe LED
45 W, solénoïde 36 W) sont **hors carte**, dans les actionneurs, et ne durent que le temps d'une
impulsion. Une **ventilation naturelle traversante** suffit ; l'enjeu principal du carénage est
l'étanchéité à la pluie et aux embruns, pas l'évacuation thermique.

---

## 2. Cas de charge pour la FEA

### 2.1 Hypothèses à figer

| Paramètre | Valeur proposée | À vérifier |
|---|---|---|
| Masse de la charge utile | **1 kg** | imposé par le cahier des charges |
| Facteur de charge vertical | **n = 4 g** (dimensionnement) et **6 g** (ultime) | manœuvre + rafale ; à justifier à l'oral |
| Vitesse relative de l'air | **20 m/s** (croisière) et **25 m/s** (max) | **à relever sur la fiche technique du Matrice 400** |
| Masse volumique de l'air | 1,225 kg/m³ (niveau de la mer, 15 °C) | — |
| Hauteur de chute à l'atterrissage | 0,5 m | hypothèse de dépose |

### 2.2 Efforts à appliquer

**Charge verticale** (la bouée tire sur le berceau et le verrou) :

```
F = n · m · g
n = 4 g  →  F = 4 × 1 × 9,81 = 39,2 N
n = 6 g  →  F = 6 × 1 × 9,81 = 58,9 N
```

**Effort aérodynamique** (issu de la CFD, appliqué comme champ de pression sur le carénage) :

```
q = ½ · ρ · v²
v = 20 m/s  →  q = 245 Pa
v = 25 m/s  →  q = 383 Pa
F_traînée = q · Cx · S_ref        ← S_ref = maître-couple de VOTRE géométrie
```

> Exemple d'ordre de grandeur : avec un maître-couple de 0,03 m² et Cx = 0,5 à 25 m/s,
> F_traînée ≈ 5,7 N. **Utilisez vos valeurs réelles** : le CDC demande la force de traînée calculée.

**Choc à l'atterrissage** : vitesse d'impact `v = √(2gh) = 3,13 m/s` pour 0,5 m. À traiter soit en
analyse dynamique, soit en équivalent statique en supposant une distance d'arrêt (par exemple 5 mm
d'écrasement → décélération ≈ 100 g).

### 2.3 Conditions aux limites

- **Encastrement** : les points de fixation au châssis du drone (interface supérieure).
- **Chargement** : effort vertical aux surfaces de contact berceau / bouée, **plus** le champ de
  pression de la CFD sur le carénage (le CDC demande explicitement de chaîner CFD → FEA).
- **Maillage** : raffiner sur les congés, le verrou, les perçages de fixation et tout changement
  brusque de section — ce sont les zones de concentration de contrainte.

### 2.4 Matériaux et critère d'acceptation

| Matériau | Limite élastique indicative | Usage conseillé |
|---|---|---|
| PETG imprimé | ~50 MPa, **retenir ~30 MPa** en effectif | carénage (bon compromis, tenue à l'humidité) |
| ASA imprimé | ~45 MPa | carénage exposé aux UV |
| PA12 (frittage) ou PA-CF | ~48 MPa | pièces structurelles imprimées |
| Aluminium 6061-T6 | 276 MPa | verrou, interface drone, axes |

> **Anisotropie de l'impression 3D :** la résistance entre couches vaut typiquement **40 à 60 %** de
> la résistance dans le plan des couches. Orientez les pièces pour que l'effort principal soit
> **dans le plan des couches**, et retenez un coefficient de sécurité **≥ 2** sur les pièces
> imprimées (≥ 1,5 sur les pièces métalliques).

**Critère :** σ_von Mises max < limite élastique / coefficient de sécurité, et les déformations ne
doivent pas bloquer la cinématique du mécanisme.

---

## 3. Réglages CFD conseillés

- **Domaine** : écoulement externe ; au moins 3 longueurs de corps en amont, 6 en aval, 3 sur les
  côtés, pour que les frontières ne perturbent pas le sillage.
- **Conditions** : vitesse imposée en entrée (20 puis 25 m/s), pression statique en sortie,
  parois non glissantes sur le carénage, air à 15 °C.
- **Modèle** : turbulent, k-ω SST si disponible.
- **Incidence** : au moins 0°. Un cas à 10° (vol en translation, nez piqué) renforce l'analyse.
- **Convergence** : vérifier que la force de traînée se stabilise, et le montrer.

---

## 4. Ce que le rapport doit contenir — checklist du cahier des charges

### A. Simulation aérodynamique (CFD) — *obligatoire*

- [ ] Captures des **lignes de courant** autour du carénage
- [ ] **Cartographie de la distribution des pressions**, zones de haute et basse pression mises en évidence
- [ ] **Valeur estimée de la force de traînée** face au vent relatif

### B. Simulation mécanique (Stress Analysis) — *obligatoire*

- [ ] Captures de la **distribution des contraintes** dans les pièces sollicitées
- [ ] **Cartographie des déplacements / déformations**
- [ ] **Identification des zones critiques** (contraintes les plus élevées)
- [ ] **Coefficient de sécurité** estimé pour les pièces analysées
- [ ] **Conditions de simulation** : matériaux, charges appliquées, conditions aux limites (fixations et appuis)

### C. À remonter pour la note de synthèse et la présentation

Ces trois valeurs sont attendues dans `01_NOTE_DE_SYNTHESE.pdf` (marqueurs orange « à compléter ») et
sur la diapositive 9 de la présentation :

1. **Maître-couple, Cx et force de traînée** retenus ;
2. **Orientation d'impression** des pièces maîtresses, matériau et épaisseurs ;
3. **Jeux fonctionnels** choisis (berceau/bouée, verrou, glissières).

---

## 5. Où déposer les fichiers

| Dossier | Contenu attendu |
|---|---|
| `03_ARCHIVE_3D/` | Assemblage SolidWorks complet avec son arborescence **+ export STEP** |
| `05_SIMULATIONS/CFD_FEA/` | Rapport visuel (PDF) + captures CFD et FEA |
| `02_PRESENTATION/` | Les 3 captures de la diapositive 9 (carénage, CFD, FEA) |

Une fois vos captures disponibles, elles s'insèrent dans la présentation en relançant
`_outils/gen_presentation.py` (les emplacements orange de la diapositive 9 sont prévus pour cela).
