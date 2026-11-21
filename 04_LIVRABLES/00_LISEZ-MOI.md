# Livrables — Équipe INSATECH

**Projet BRC-M400 — Système de largage de bouée et balise de détresse**
Tunisian AeroDay V14 · Challenge CAO · Porteur DJI Matrice 400 (E-Port V2) · Révision C

---

## Correspondance avec les livrables demandés

| # | Livrable exigé par le cahier des charges | Où | État |
|---|---|---|---|
| 1 | **Archive numérique** — assemblage 3D complet + export STEP | `03_ARCHIVE_3D/` | **à déposer (pôle mécanique)** |
| 2 | **Dossier électronique** — fichiers natifs, schéma PDF, STEP de la carte | `04_DOSSIER_ELECTRONIQUE/` | **complet** |
| 3 | **Simulations** — CFD et résistance mécanique | `05_SIMULATIONS/` | électronique **complète** · CFD/FEA **à déposer** |
| 4 | **Note de synthèse** (1 à 2 pages) | `01_NOTE_DE_SYNTHESE.pdf` | **complète**, sauf valeurs mécaniques |

**Présentation du pitch (5 min) :** `02_PRESENTATION/INSATECH_BRC-M400_presentation.pdf` — 10 diapositives.

---

## Détail des dossiers

### `01_NOTE_DE_SYNTHESE.pdf` — 2 pages
Justifie la mission, le principe de sûreté du mécanisme, les choix électroniques et le
dimensionnement, l'intégration et les simulations. Les passages **en orange** sont les valeurs
mécaniques à compléter par le pôle mécanique (aérodynamique, orientation d'impression, jeux
fonctionnels).

### `02_PRESENTATION/`
Deck PDF 16:9 pour le pitch. **La diapositive 9 contient trois emplacements** à remplir avec les
captures du carénage, de la CFD et de la FEA.

### `03_ARCHIVE_3D/` — à compléter
Assemblage SolidWorks complet avec son arborescence, **plus** l'export STEP. Voir les cotes
d'interface de la carte dans `05_SIMULATIONS/CFD_FEA/BRIEF_SIMULATIONS_ET_INTERFACE.md`.

### `04_DOSSIER_ELECTRONIQUE/` — complet

| Fichier | Contenu |
|---|---|
| `BRC-M400_KiCad/` | Projet **natif KiCad 10** : schéma hiérarchique (6 pages) + circuit imprimé routé |
| `BRC-M400_schema.pdf` | Schéma électronique complet — page 1 vue d'ensemble, pages 2 à 6 par bloc |
| `BRC-M400_PCB.step` | **Modèle 3D de la carte routée** (38 Mo : pistes, plans et composants) |
| `BRC-M400_PCB_simplifie.step` | Même carte **sans les pistes** (5 Mo) — **à utiliser pour l'assemblage CAO** |
| `BRC-M400_BOM.csv` | Nomenclature |
| `BRC-M400.net` | Netlist extraite du schéma |
| `fab/` | Gerbers et fichiers de perçage (preuve de fabricabilité) |
| `rendus_3D/` | Rendus de la carte et images du schéma |

**Caractéristiques :** 96,1 × 66,1 mm · 4 couches · 1,6 mm · ENIG · 163 composants ·
1 414 pistes · 424 vias · ERC sans violation · netlist vérifiée (0 écart).
**Réserve assumée :** 30 liaisons restent à router autour du microcontrôleur et de la radio.

### `05_SIMULATIONS/`

- `electronique/` — **complet** : rapport et 9 figures, 7 analyses ngspice (convertisseur 3,3 V,
  intégrité d'alimentation et court-circuit E-Port, étage LED PWM, coupure inductive de la sirène,
  solénoïde d'éjection, aimant de maintien, bilan de liaison LoRa).
- `CFD_FEA/` — **à compléter**. Le fichier `BRIEF_SIMULATIONS_ET_INTERFACE.md` contient les cotes
  réelles de la carte, les cas de charge chiffrés, les réglages conseillés et la **checklist exacte
  des captures exigées** par le cahier des charges.

### `_outils/`
Scripts de génération de la note de synthèse et de la présentation (python + PyMuPDF). À relancer
après avoir ajouté les captures mécaniques.

---

## Ce qui reste à faire avant le dépôt

1. **Pôle mécanique** — assemblage 3D + STEP dans `03_ARCHIVE_3D/`, rapport CFD/FEA dans
   `05_SIMULATIONS/CFD_FEA/`.
2. **Compléter** les marqueurs orange de la note de synthèse, puis relancer
   `_outils/gen_note_synthese.py`.
3. **Insérer** les trois captures mécaniques dans la diapositive 9, puis relancer
   `_outils/gen_presentation.py`.
4. *(optionnel)* Terminer les 30 liaisons de routage restantes dans KiCad.
