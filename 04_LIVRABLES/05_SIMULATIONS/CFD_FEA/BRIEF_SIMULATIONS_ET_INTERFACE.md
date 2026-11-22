# Brief — simulations CFD / FEA et interface mécanique de la carte

**Pour : le pôle mécanique d'INSATECH** · Projet BRC-M400 **Rev D** · AeroDay V14, Challenge CAO
**Échéance : 22 novembre 2026, 9 h** (dépôt Google Drive)

> ### ⚠ Changement majeur en Rev D — à lire avant de modéliser
> Le module est devenu **entièrement autonome** : il n'a **plus aucune liaison électrique avec le
> drone**. Conséquences pour la mécanique :
> 1. **Plus aucun passage de câble vers le porteur** — l'interface supérieure se réduit à une
>    fixation purement mécanique.
> 2. La carte a grandi : **140 × 66 mm** (contre 96 × 66) et les entraxes des M3 ont changé.
> 3. Il faut loger un **pack 3S LiPo 2200 mAh** (~105 × 35 × 25 mm, ~180 g).
> 4. Une **prise USB-C de recharge** doit rester accessible **sans démonter le carénage**.

---

## 1. Interface mécanique de la carte BRC-M400 Rev D

Cotes extraites du fichier KiCad. **Repère : coin inférieur gauche du contour, X vers la droite,
Y vers le haut, vue de dessus.**

| Grandeur | Valeur |
|---|---|
| Contour | **140 × 66 mm**, angles arrondis R3 |
| Épaisseur du circuit | 1,6 mm (4 couches, FR-4) |
| Assemblage | **composants sur la face supérieure uniquement** — le dessous est libre |
| Hauteur maximale au-dessus de la carte | **≈ 12 mm** (connecteurs XT30, condensateur C80) |
| Masse de la carte équipée | ≈ 90 g *(à peser sur le STEP)* |

### Trous de fixation — Ø 3,2 mm (vis M3)

| Trou | X (mm) | Y (mm) |
|---|---|---|
| H3 | 3,60 | 3,60 |
| H4 | 136,40 | 3,60 |
| H1 | 3,60 | 62,40 |
| H2 | 136,40 | 62,40 |

→ **Entraxes : 132,80 mm (X) × 58,80 mm (Y).** Les quatre trous sont reliés au plan de masse :
prévoir des **entretoises métalliques** pour utiliser le châssis comme masse et chemin thermique.

### Connecteurs — à dégager dans le carénage

| Rep. | Fonction | X | Y | Sort par |
|---|---|---|---|---|
| **J40** | **USB-C de recharge** | 3,45 | 47,05 | bord **gauche** — **doit rester accessible** |
| **J42** | **Pack 3S (XT30)** | 14,05 | 3,15 | bord **bas** |
| **J41** | **Équilibrage 3S (JST-XH 4 pts)** | 36,55 | 3,15 | bord **bas** |
| J31 | Rampe LED 12 V (XT30) | 84,05 | 13,15 | bord **bas** |
| J33 | Électroaimant de maintien 12 V | 100,05 | 13,15 | bord **bas** |
| J34 | Solénoïde d'éjection 12 V | 116,05 | 13,15 | bord **bas** |
| J32 | Sirène 12 V (XT30) | 126,95 | 33,05 | bord **droit** |
| J20 | **Antenne SMA 868 MHz** | 136,85 | 51,05 | bord **droit**, en débord |
| J6 | Micro-rupteurs verrou / présence | 110,05 | 62,85 | bord **haut** |
| J7 | SWD (programmation) | 71,55 | 61,55 | accès **maintenance** |

**Contraintes à respecter :**

- **L'antenne SMA (J20) doit déboucher à l'air libre**, sans métal ni carbone à moins de 20 mm :
  du carbone devant l'antenne ferait perdre l'essentiel de la portée.
- **La prise USB-C (J40) doit être atteignable sans ouvrir le carénage** — c'est le seul moyen de
  recharger le module. Prévoir une trappe ou un passage étanche (bouchon IP).
- Garder **≥ 25 mm** de dégagement devant les XT30 du bord bas pour le rayon de courbure des câbles.
- Fichiers CAO : `04_DOSSIER_ELECTRONIQUE/BRC-M400_PCB_simplifie.step` (**léger, pour l'assemblage**)
  et `BRC-M400_PCB.step` (complet, pour le rendu).

### Logement du pack 3S

| Grandeur | Valeur indicative |
|---|---|
| Dimensions | ≈ **105 × 35 × 25 mm** *(à confirmer sur le pack réellement acheté)* |
| Masse | ≈ **180 g** |
| Fixation | sangle ou berceau mousse — **ne jamais comprimer les cellules** |
| Sécurité | prévoir un **évent** : une cellule en défaut dégaze. Ne pas enfermer hermétiquement |

> ⚠ **Sécurité LiPo :** le pack ne doit être ni percé, ni écrasé, ni placé contre une source de
> chaleur. Le logement doit le protéger des chocs à l'atterrissage, qui sont le cas de charge
> dimensionnant pour cette zone.

### Thermique

Sources de chaleur faibles et localisées : MOSFET BSC028N06LS3 (2,8 mΩ) et pertes de commutation
simulées à **15 mW**. Les fortes puissances (rampe LED 41 W, solénoïde 36 W) sont **hors carte**.
En revanche, **la charge du pack à 2 A dissipe quelques watts** dans le chargeur : prévoir un peu
de ventilation naturelle au-dessus de la bande de gauche. L'enjeu principal du carénage reste
l'étanchéité à la pluie et aux embruns.

---

## 2. Cas de charge pour la FEA

### 2.1 Hypothèses à figer

| Paramètre | Valeur proposée | À vérifier |
|---|---|---|
| Masse de la charge utile | **1 kg** | imposé par le cahier des charges |
| Masse du module (carte + pack + structure) | **à relever sur votre modèle** | le pack ajoute ~180 g |
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

**Choc à l'atterrissage** : `v = √(2gh) = 3,13 m/s` pour 0,5 m. À traiter en analyse dynamique, ou
en équivalent statique avec une distance d'arrêt supposée (5 mm d'écrasement → ≈ 100 g).
**Vérifier en particulier le logement du pack**, qui porte une masse concentrée.

### 2.3 Conditions aux limites

- **Encastrement** : les points de fixation au châssis du drone (interface supérieure).
- **Chargement** : effort vertical aux surfaces de contact berceau / bouée, **plus** le champ de
  pression issu de la CFD (le CDC demande explicitement de chaîner CFD → FEA), **plus** l'inertie
  du pack.
- **Maillage** : raffiner sur les congés, le verrou, les perçages de fixation et tout changement
  brusque de section.

### 2.4 Matériaux et critère d'acceptation

| Matériau | Limite élastique indicative | Usage conseillé |
|---|---|---|
| PETG imprimé | ~50 MPa, **retenir ~30 MPa** en effectif | carénage (tenue à l'humidité) |
| ASA imprimé | ~45 MPa | carénage exposé aux UV |
| PA12 (frittage) ou PA-CF | ~48 MPa | pièces structurelles imprimées |
| Aluminium 6061-T6 | 276 MPa | verrou, interface drone, axes |

> **Anisotropie de l'impression 3D :** la résistance entre couches vaut typiquement **40 à 60 %**
> de la résistance dans le plan. Orientez les pièces pour que l'effort principal soit **dans le plan
> des couches**, et retenez un coefficient de sécurité **≥ 2** sur les pièces imprimées
> (≥ 1,5 sur les pièces métalliques).

**Critère :** σ_von Mises max < limite élastique / coefficient de sécurité, et les déformations ne
doivent pas bloquer la cinématique du mécanisme.

---

## 3. Réglages CFD conseillés

- **Domaine** : écoulement externe ; au moins 3 longueurs de corps en amont, 6 en aval, 3 sur les
  côtés.
- **Conditions** : vitesse imposée en entrée (20 puis 25 m/s), pression statique en sortie, parois
  non glissantes, air à 15 °C.
- **Modèle** : turbulent, k-ω SST si disponible.
- **Incidence** : au moins 0°. Un cas à 10° renforce l'analyse.
- **Convergence** : montrer que la force de traînée se stabilise.

---

## 4. Checklist du cahier des charges

### A. Simulation aérodynamique (CFD) — *obligatoire*

- [ ] Captures des **lignes de courant** autour du carénage
- [ ] **Cartographie des pressions**, zones de haute et basse pression mises en évidence
- [ ] **Valeur estimée de la force de traînée**

### B. Simulation mécanique (Stress Analysis) — *obligatoire*

- [ ] **Distribution des contraintes** dans les pièces sollicitées
- [ ] **Cartographie des déplacements / déformations**
- [ ] **Zones critiques** identifiées
- [ ] **Coefficient de sécurité** estimé
- [ ] **Conditions de simulation** : matériaux, charges, conditions aux limites

### C. À remonter pour la note de synthèse et la présentation

Attendus dans `01_NOTE_DE_SYNTHESE.pdf` (marqueurs orange) et sur la **diapositive 13** :

1. **Maître-couple, Cx et force de traînée** retenus ;
2. **Orientation d'impression** des pièces maîtresses, matériau et épaisseurs ;
3. **Jeux fonctionnels** choisis (berceau/bouée, verrou, glissières).

---

## 5. Où déposer les fichiers

| Dossier | Contenu attendu |
|---|---|
| `03_ARCHIVE_3D/` | Assemblage SolidWorks complet avec son arborescence **+ export STEP** |
| `05_SIMULATIONS/CFD_FEA/` | Rapport visuel (PDF) + captures CFD et FEA |
| `02_PRESENTATION/` | Les 3 captures de la diapositive 13 |

Une fois vos captures disponibles, insérez-les dans le `.pptx` puis réexportez le PDF.
