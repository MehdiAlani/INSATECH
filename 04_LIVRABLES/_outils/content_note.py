# -*- coding: utf-8 -*-
"""Texte de la note de synthèse (français accentué)."""
from style import todo as T

HTML = u"""
<h1>Note de synthèse — Système de largage de bouée BRC-M400</h1>
<div class="lead">Équipe <b>INSATECH</b> &middot; Tunisian AeroDay V14 &middot; Challenge CAO
&middot; Porteur DJI Matrice 400 (fixation mécanique seule) &middot; Révision D &middot; 22 novembre 2026</div>

<h2>1. Mission et architecture d'ensemble</h2>
<p>Le système assure l'emport sous le ventre du Matrice 400, le <b>largage sécurisé d'une bouée de
sauvetage de 1 kg</b> au-dessus d'une zone inondée, puis la <b>signalisation de détresse</b> de la
charge une fois au sol.</p>
<p><b>Le module est entièrement autonome : il n'a aucune liaison électrique avec le drone.</b> Il
porte son énergie (pack <b>3S LiPo 2200 mAh</b>, 24,4 Wh) et sa propre radio. Ce choix a trois
conséquences décisives : l'<b>intégration mécanique se réduit à une fixation</b>, sans connecteur
ni faisceau à faire passer vers le porteur ; le module reste <b>compatible de tout aéronef</b>, ce
que le cahier des charges demande d'un système modulaire ; et surtout <b>la balise continue de
fonctionner après le largage</b>, quand le drone est reparti — c'est précisément ce qu'on attend
d'un signal de détresse destiné à être repéré au sol.</p>

<h2>2. Mécanisme de largage : la sûreté est obtenue par construction</h2>
<p>Le point dur du cahier des charges est qu'<i>en position fermée, le mécanisme doit résister à de
fortes accélérations verticales sans libération accidentelle</i>. Nous ne traitons pas ce risque par
un verrou supplémentaire, mais par le choix même des actionneurs.</p>
<ul>
<li><b>Maintien à sécurité positive.</b> L'électroaimant de maintien est de type <i>fail-safe</i> :
un <b>aimant permanent</b> tient la bouée, et c'est <b>l'alimentation de la bobine qui annule le
champ pour libérer</b>. Toute perte d'énergie, toute coupure de liaison et tout reset du calculateur
laissent donc la charge <b>accrochée</b> : l'état sûr du système est l'état non alimenté.</li>
<li><b>Double barrière ARM / FIRE.</b> Le largage exige simultanément un interrupteur côté haut
(ARM — P-MOSFET SUD50P06-15 alimentant le rail actionneurs V_ACT) <b>et</b> l'étage côté bas de la
voie concernée (FIRE). <b>Aucun défaut unique</b> — broche de microcontrôleur qui bascule, MOSFET en
court-circuit, parasite — ne peut provoquer un largage.</li>
<li><b>Éjection active.</b> Un solénoïde pousseur 12 V, piloté en impulsion <i>peak &amp; hold</i>,
écarte franchement la bouée du carénage : la charge ne peut ni coller à l'aimant résiduel ni
rebondir dans la structure.</li>
<li><b>Confirmation par la mesure.</b> Chaque bobine est mesurée par un shunt de 10 m&#8486; et un
INA181A2. Le <b>creux de courant</b> marquant la fin de course du plongeur sert d'accusé de largage ;
la balise ne s'allume qu'<b>après</b> cette confirmation.</li>
<li><b>Protocole en deux temps.</b> L'ordre LARGUER n'est accepté qu'après une commande ARMER
distincte, dans une fenêtre de 10 s, avec chiffrement AES-128 et compteur anti-rejeu : ni un
parasite radio ni le rejeu d'une trame capturée ne peuvent déclencher un largage.</li>
</ul>

<h2>3. Choix aérodynamiques</h2>
<p>Fixé sous le fuselage, le système travaille dans le vent relatif et ne doit pas dégrader les
performances de vol. Le carénage est <b>profilé</b> : maître-couple réduit au strict nécessaire pour
loger la bouée et la carte, nez arrondi et arrière effilé afin de retarder le décollement et de
limiter la traînée de culot. La carte a été dessinée pour <b>s'inscrire dans ce volume</b>
(96 &times; 66 mm, §5), et non l'inverse. Conditions de calcul retenues pour la CFD, qui servent
ensuite de chargement à la FEA : %(cfd)s</p>

<h2>4. Architecture électronique et dimensionnement</h2>
<p><b>Énergie et recharge.</b> Le pack <b>3S LiPo 2200 mAh</b> est surveillé cellule par cellule
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
de la liaison ; sa très faible consommation est ce qui autorise une longue veille sur batterie.</p>
<p><b>Radio.</b> Le <b>Semtech SX1262</b> (+22 dBm, sensibilité &minus;137 dBm en SF12/BW125,
4,6 mA en réception) opère à <b>869,525 MHz</b>, sous-bande g3. Le 2,4 GHz est écarté car c'est la
bande de la liaison de commande du drone, qu'il ne faut pas perturber ; la 4G est écartée car elle
dépend d'un réseau terrestre, le premier à tomber lors d'une inondation. Le bilan de liaison donne
<b>40 dB de marge à 15 km en SF9</b> : la commande reste disponible bien au-delà de la portée utile
du vol.</p>
<p><b>Séparation logique / puissance.</b> Les rails sont produits <b>directement depuis VIN, jamais
en cascade</b>, pour qu'un appel de courant des actionneurs ne puisse faire chuter ni le calculateur
ni la radio :</p>
<table>
<tr><th>Rail</th><th>Circuit</th><th>Dimensionnement et rôle</th></tr>
<tr><td>+3V3 logique</td><td>LMR51430 (36 V, 3 A)</td>
    <td>0,600 &times; (1 + 100k/22,1k) = <b>3,315 V</b> ; L = 15 &micro;H ; ondulation simulée
    <b>2,6 mV</b></td></tr>
<tr><td>+3V3_RF</td><td>ferrite + 10 &micro;F / 100 nF</td>
    <td>Isole le SX1262 du bruit de commutation</td></tr>
<tr><td>+12V grilles</td><td><b>élévateur</b> TPS61040</td>
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
économique en composants comme en pertes.</p>
<p><b>Tenue aux perturbations.</b> Les voies de bobine sont démagnétisées par une Schottky SS34
associée à une TVS SMAJ20A : la tension de drain plafonne à <b>36 V</b> (MOSFET 60 V) et le courant
décroît <b>7 fois plus vite</b> qu'avec une simple roue libre — d'où une libération de l'aimant
<b>3,2 ms</b> après l'ordre FIRE. Les actionneurs sont désormais des modèles <b>12 V</b> pilotés en
<b>régulation de courant</b> (PWM + shunt + INA181A2) : le largage est donc insensible à la
décharge du pack entre 12,6 V et 9,0 V.</p>
<p><b>Bilan d'énergie.</b> Les 24,4 Wh du pack couvrent très largement la mission. La veille
(MCU + SX1262 en réception) consomme &asymp; 0,1 W, soit plusieurs jours d'attente ; le largage ne
dure que quelques dizaines de millisecondes. Le dimensionnement est en réalité fixé par la
<b>balise</b> : rampe LED et sirène 12 V appellent &asymp; 57 W en continu, d'où un fonctionnement en
<b>flashs et salves</b> (rapport cyclique 20 %%) qui porte l'autonomie de signalisation au-delà de
<b>2 heures</b>. Le séquencement largage puis balise est conservé pour ménager le pack.</p>

<h2>5. Intégration mécatronique, DFM et impression 3D</h2>
<p><b>Carte.</b> 134 &times; 66 mm, <b>4 couches</b> (signaux / plan de masse continu / plans
d'alimentation / masse), 1,6 mm, finition ENIG, vernis noir mat, <b>226 composants</b>. La bande de gauche est
entièrement dédiée à l'énergie (USB-C, chargeur, BMS, pack), physiquement séparée de la logique
et de la radio. Le plan de masse de la couche 2 n'est jamais
découpé et la chaîne RF 868 MHz est routée en ligne 50 &#8486; (0,36 mm), sans via dans le couloir
d'antenne.</p>
<p><b>Interfaces imposées au châssis.</b> Quatre trous M3 aux angles, reliés à la masse pour le
blindage et la dissipation ; XT30 des actionneurs sur le bord bas ; <b>prise USB-C de recharge sur
le bord gauche</b>, qui doit rester accessible sans démonter le carénage ; pack 3S et connecteur
d'équilibrage en bas à gauche ; SMA en bord de carte ; micro-rupteurs sur le bord haut. %(iface)s</p>
<p><b>Gestion thermique.</b> Les sources de chaleur sont les étages de puissance (MOSFET
BSC028N06LS3, 2,8 m&#8486;) et le LDO 12 V (~60 mW). Les pertes de commutation simulées de la voie
LED restent à <b>15 mW</b>, pour une jonction proche de l'ambiante : le flux est faible et
localisé. %(therm)s</p>
<p><b>Impression 3D et jeux fonctionnels.</b> %(print)s</p>

<h2>6. Simulations et vérification</h2>
<p><b>Électronique — réalisée (ngspice).</b> Sept analyses documentées avec leurs courbes :
convertisseur 3,3 V en commutation réelle ; intégrité d'alimentation et interruption du pack ; étage
LED en PWM (15 mW de pertes) ; coupure inductive de la sirène ; <b>modèle électromécanique du solénoïde</b> (fin de
course à 23 ms, creux de courant confirmant l'éjection à 23,7 ms) ; <b>aimant de maintien</b>
(libération 3,2 ms, démagnétisation 1,0 ms) ; bilan de liaison LoRa. La conformité du schéma est
vérifiée automatiquement : contrôle ERC sans violation et comparaison de la netlist extraite avec la
netlist de référence (<b>0 écart</b>).</p>
<p><b>Aérodynamique et structure.</b> %(sim)s</p>

<h2>7. Points ouverts assumés</h2>
<p><b>(a)</b> Référence exacte de l'aimant <i>fail-safe</i> et du solénoïde 12 V — fixe les courants
réels et la force de maintien ; la carte est dimensionnée avec marge. <b>(b)</b> Valeurs
d'adaptation RF marquées <i>TUNE</i> — nomenclature régionale Semtech E449V01A, puis réglage à
l'analyseur de réseau. <b>(c)</b> Référence exacte du pack 3S 2200 mAh et de son connecteur d'équilibrage.
<b>(d)</b> Seuils du BMS (surintensité, coupure basse tension) à régler en NVM selon le pack
retenu.</p>
""" % dict(
    cfd=T(u"vitesse relative retenue, altitude, maître-couple, Cx et force de traînée issus de la CFD"),
    iface=T(u"entraxe des M3 et hauteur libre sous la carte, à figer avec le modèle du châssis"),
    therm=T(u"solution de ventilation ou de conduction retenue dans le carénage"),
    print=T(u"orientation d'impression des pièces maîtresses, matériau, épaisseurs et jeux fonctionnels retenus"),
    sim=T(u"lignes de courant, cartographie de pression et force de traînée ; contraintes de von Mises, "
          u"déplacements, zones critiques et coefficient de sécurité"),
)
