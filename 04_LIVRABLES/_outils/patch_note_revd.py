# -*- coding: utf-8 -*-
"""Rev D rewrite of the note de synthese content."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "content_note.py")
s = io.open(p, encoding="utf-8").read()


def sub(a, b):
    global s
    assert a in s, "NOT FOUND: " + a[:70]
    s = s.replace(a, b, 1)


sub("&middot; Révision C &middot; 22 novembre 2026", "&middot; Révision D &middot; 22 novembre 2026")

sub(u"""<p>Le système assure l'emport sous le ventre du Matrice 400, le <b>largage sécurisé d'une bouée de
sauvetage de 1 kg</b> au-dessus d'une zone inondée, puis la <b>signalisation de détresse</b> de la
charge une fois au sol. Il associe un ensemble mécanique (berceau, carénage profilé, mécanisme de
libération) et une carte électronique sur mesure <b>BRC-M400</b> qui pilote le mécanisme, dialogue
avec le drone et déclenche la balise. L'énergie et la commande viennent d'un <b>port E-Port V2</b>
(13,8 / 17 / 24 V — 5 A, 120 W par port), configuré à <b>24 V</b> : aucune batterie embarquée n'est
nécessaire, ce qui allège le mécanisme et sert l'exigence de compacité.</p>""",
    u"""<p>Le système assure l'emport sous le ventre du Matrice 400, le <b>largage sécurisé d'une bouée de
sauvetage de 1 kg</b> au-dessus d'une zone inondée, puis la <b>signalisation de détresse</b> de la
charge une fois au sol.</p>
<p><b>Le module est entièrement autonome : il n'a aucune liaison électrique avec le drone.</b> Il
porte son énergie (pack <b>3S LiPo 2200 mAh</b>, 24,4 Wh) et sa propre radio. Ce choix a trois
conséquences décisives : l'<b>intégration mécanique se réduit à une fixation</b>, sans connecteur
ni faisceau à faire passer vers le porteur ; le module reste <b>compatible de tout aéronef</b>, ce
que le cahier des charges demande d'un système modulaire ; et surtout <b>la balise continue de
fonctionner après le largage</b>, quand le drone est reparti — c'est précisément ce qu'on attend
d'un signal de détresse destiné à être repéré au sol.</p>""")

sub(u"""<li><b>Verrouillage logiciel.</b> Le firmware s'abonne à la télémétrie PSDK (altitude, vitesse) et
n'autorise le largage que dans un domaine de vol défini, avec une fenêtre de validité de 10 s après
l'ordre ARMER.</li>""",
    u"""<li><b>Protocole en deux temps.</b> L'ordre LARGUER n'est accepté qu'après une commande ARMER
distincte, dans une fenêtre de 10 s, avec chiffrement AES-128 et compteur anti-rejeu : ni un
parasite radio ni le rejeu d'une trame capturée ne peuvent déclencher un largage.</li>""")

sub(u"""<p><b>Calcul et liaison drone.</b> Le <b>STM32U585CIU6</b> (Cortex-M33 160 MHz, 2 Mo de flash,
786 Ko de RAM, 19 &micro;A/MHz, TrustZone) s'impose parce que DJI fournit la bibliothèque PSDK
précompilée <i>armcc_cortex-m33</i> : elle tourne telle quelle, sans portage, et expose les boutons
ARMER / LARGUER / BALISE dans DJI Pilot 2.</p>""",
    u"""<p><b>Énergie et recharge.</b> Le pack <b>3S LiPo 2200 mAh</b> est surveillé cellule par cellule
par un <b>BQ76920</b> : surcharge, décharge profonde, surintensité, court-circuit, température et
équilibrage. La protection est <b>matérielle et autonome</b> — les MOSFET CHG/DSG ouvrent le pack
sans aucune intervention du microcontrôleur — et le MCU en lit l'état en I&sup2;C pour le renvoyer
par radio. La recharge se fait par <b>USB-C Power Delivery</b> : le <b>STUSB4500</b> négocie 20 V
seul, même carte éteinte, et le chargeur à découpage synchrone <b>BQ24610</b> régule
2,1 V &times; (1 + 100k/20k) = <b>12,6 V</b> à <b>2 A</b> (1C), soit une recharge complète en
environ 70 minutes. Quatre LED donnent l'état : charge, fin de charge ou défaut, PD établi, alerte
BMS.</p>
<p><b>Calcul.</b> Le <b>STM32U585CIU6</b> (Cortex-M33 160 MHz, 2 Mo de flash, 786 Ko de RAM,
19 &micro;A/MHz, TrustZone, AES et PKA matériels) assure la commande, les mesures et le chiffrement
de la liaison ; sa très faible consommation est ce qui autorise une longue veille sur batterie.</p>""")

sub(u"""<p><b>Radio.</b> Le <b>Semtech SX1262</b> (+22 dBm, sensibilité &minus;137 dBm en SF12/BW125, 4,6 mA
en réception) opère à <b>869,525 MHz</b>, sous-bande g3. Le 2,4 GHz est écarté car c'est la bande de
la liaison de commande O4 du drone ; la 4G est écartée car elle dépend d'un réseau terrestre, le
premier à tomber lors d'une inondation. Le bilan de liaison donne <b>40 dB de marge à 15 km en
SF9</b>. Deux chemins de commande indépendants coexistent : LoRa depuis le sol et PSDK depuis le
drone.</p>""",
    u"""<p><b>Radio.</b> Le <b>Semtech SX1262</b> (+22 dBm, sensibilité &minus;137 dBm en SF12/BW125,
4,6 mA en réception) opère à <b>869,525 MHz</b>, sous-bande g3. Le 2,4 GHz est écarté car c'est la
bande de la liaison de commande du drone, qu'il ne faut pas perturber ; la 4G est écartée car elle
dépend d'un réseau terrestre, le premier à tomber lors d'une inondation. Le bilan de liaison donne
<b>40 dB de marge à 15 km en SF9</b> : la commande reste disponible bien au-delà de la portée utile
du vol.</p>""")

sub(u"""<tr><td>+12V_GD</td><td>LDO TPS7A4101 (50 V)</td>
    <td>1,173 &times; (1 + 91k/10k) = <b>11,85 V</b> : attaque les grilles à leur RDS(on) nominal</td></tr>
<tr><td>Entrée</td><td>LM74700 + BSC028N06LS3</td>
    <td>Diode idéale : ~20 mV de chute, blocage inverse &lt; 1 &micro;s, réservoir 470 &micro;F</td></tr>
</table>""",
    u"""<tr><td>+12V grilles</td><td><b>élévateur</b> TPS61040</td>
    <td>1,233 &times; (1 + 1M/113k) = <b>11,96 V</b> à partir du 3,3 V</td></tr>
<tr><td>Entrée pack</td><td>LM74700 + BSC028N06LS3</td>
    <td>Diode idéale : inversion du pack impossible, réservoir 470 &micro;F</td></tr>
</table>
<p><b>Pourquoi un élévateur et non un régulateur linéaire.</b> Le pack descend à <b>9,0 V</b> en fin
de décharge. Un LDO 12 V — la solution de la révision précédente, alimentée en 24 V par le drone —
serait <b>incapable</b> de fournir 11,96 V sous 9,0 V d'entrée : les grilles seraient sous-attaquées
exactement quand la batterie est faible, donc au pire moment. En élevant depuis le 3,3 V régulé,
<b>Vgs reste nominal quel que soit l'état de charge</b>, et le RDS(on) des MOSFET avec lui. Le
courant moyen demandé est faible (Q<sub>g</sub> &times; f &asymp; 2 mA), ce qui rend ce choix
économique en composants comme en pertes.</p>""")

sub(u"""<p><b>Tenue aux perturbations.</b> La simulation d'un <b>court-circuit de 30 ms sur l'E-Port</b>
montre que le 3,3 V est maintenu grâce au blocage inverse du LM74700, alors qu'il s'effondre en
85 &micro;s avec une protection passive. Les voies de bobine sont démagnétisées par une Schottky
SS34 associée à une TVS SMAJ20A : la tension de drain plafonne à <b>48 V</b> (MOSFET 60 V) et le
courant décroît <b>4,4 fois plus vite</b> qu'avec une simple roue libre — d'où une libération de
l'aimant <b>3,2 ms</b> après l'ordre FIRE.</p>""",
    u"""<p><b>Tenue aux perturbations.</b> Les voies de bobine sont démagnétisées par une Schottky SS34
associée à une TVS SMAJ20A : la tension de drain plafonne à <b>36 V</b> (MOSFET 60 V) et le courant
décroît <b>4,4 fois plus vite</b> qu'avec une simple roue libre — d'où une libération de l'aimant
<b>3,2 ms</b> après l'ordre FIRE. Les actionneurs sont désormais des modèles <b>12 V</b> pilotés en
<b>régulation de courant</b> (PWM + shunt + INA181A2) : le largage est donc insensible à la
décharge du pack entre 12,6 V et 9,0 V.</p>""")

sub(u"""<p><b>Bilan de puissance et séquencement.</b> Toutes charges actives, la carte appellerait
<b>4,25 A</b> pour une limite de 5 A : marge trop faible. Le firmware impose donc un séquencement —
d'abord le largage (maintien + éjection &asymp; 2 A), puis la signalisation (rampe LED + sirène
&asymp; 2,4 A) — qui maintient le courant réel <b>sous 2,5 A</b>.</p>""",
    u"""<p><b>Bilan d'énergie.</b> Les 24,4 Wh du pack couvrent très largement la mission. La veille
(MCU + SX1262 en réception) consomme &asymp; 0,1 W, soit plusieurs jours d'attente ; le largage ne
dure que quelques dizaines de millisecondes. Le dimensionnement est en réalité fixé par la
<b>balise</b> : rampe LED et sirène 12 V appellent &asymp; 57 W en continu, d'où un fonctionnement en
<b>flashs et salves</b> (rapport cyclique 20 %) qui porte l'autonomie de signalisation au-delà de
<b>2 heures</b>. Le séquencement largage puis balise est conservé pour ménager le pack.</p>""")

sub(u"<p><b>Carte.</b> 96,1 &times; 66,1 mm, <b>4 couches</b>", u"<p><b>Carte.</b> 134 &times; 66 mm, <b>4 couches</b>")
sub(u"""1,6 mm, finition ENIG, vernis noir mat : 163 composants, 608 pastilles,
1414 pistes, 424 vias, <b>2,66 m</b> de cuivre.""",
    u"""1,6 mm, finition ENIG, vernis noir mat, <b>226 composants</b>. La bande de gauche est
entièrement dédiée à l'énergie (USB-C, chargeur, BMS, pack), physiquement séparée de la logique
et de la radio.""")

sub(u"""<p><b>Interfaces imposées au châssis.</b> Quatre trous M3 aux angles, reliés à la masse pour le
blindage et la dissipation ; connecteurs de puissance XT30 regroupés sur les bords bas et droit,
face aux sorties actionneurs ; SMA en bord de carte ; connecteurs PSDK et micro-rupteurs sur le bord
haut, côté drone.""",
    u"""<p><b>Interfaces imposées au châssis.</b> Quatre trous M3 aux angles, reliés à la masse pour le
blindage et la dissipation ; XT30 des actionneurs sur le bord bas ; <b>prise USB-C de recharge sur
le bord gauche</b>, qui doit rester accessible sans démonter le carénage ; pack 3S et connecteur
d'équilibrage en bas à gauche ; SMA en bord de carte ; micro-rupteurs sur le bord haut.""")

sub(u"""<p><b>(a)</b> Référence exacte de l'aimant <i>fail-safe</i> et du solénoïde 24 V""",
    u"""<p><b>(a)</b> Référence exacte de l'aimant <i>fail-safe</i> et du solénoïde 12 V""")
sub(u"""<b>(c)</b> Routage : <b>30 liaisons restantes</b> sur 120 réseaux,
concentrées autour du microcontrôleur et de la radio. <b>(d)</b> Brochage UART du kit E-Port V2 — à
relever dans la documentation DJI PSDK.</p>""",
    u"""<b>(c)</b> Référence exacte du pack 3S 2200 mAh et de son connecteur d'équilibrage.
<b>(d)</b> Seuils du BMS (surintensité, coupure basse tension) à régler en NVM selon le pack
retenu.</p>""")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("content_note.py -> Rev D")
