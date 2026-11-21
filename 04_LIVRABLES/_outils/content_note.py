# -*- coding: utf-8 -*-
"""Texte de la note de synthèse (français accentué)."""
from style import todo as T

HTML = u"""
<h1>Note de synthèse — Système de largage de bouée BRC-M400</h1>
<div class="lead">Équipe <b>INSATECH</b> &middot; Tunisian AeroDay V14 &middot; Challenge CAO
&middot; Porteur DJI Matrice 400 (E-Port V2) &middot; Révision C &middot; 22 novembre 2026</div>

<h2>1. Mission et architecture d'ensemble</h2>
<p>Le système assure l'emport sous le ventre du Matrice 400, le <b>largage sécurisé d'une bouée de
sauvetage de 1 kg</b> au-dessus d'une zone inondée, puis la <b>signalisation de détresse</b> de la
charge une fois au sol. Il associe un ensemble mécanique (berceau, carénage profilé, mécanisme de
libération) et une carte électronique sur mesure <b>BRC-M400</b> qui pilote le mécanisme, dialogue
avec le drone et déclenche la balise. L'énergie et la commande viennent d'un <b>port E-Port V2</b>
(13,8 / 17 / 24 V — 5 A, 120 W par port), configuré à <b>24 V</b> : aucune batterie embarquée n'est
nécessaire, ce qui allège le mécanisme et sert l'exigence de compacité.</p>

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
<li><b>Éjection active.</b> Un solénoïde pousseur 24 V, piloté en impulsion <i>peak &amp; hold</i>,
écarte franchement la bouée du carénage : la charge ne peut ni coller à l'aimant résiduel ni
rebondir dans la structure.</li>
<li><b>Confirmation par la mesure.</b> Chaque bobine est mesurée par un shunt de 10 m&#8486; et un
INA181A2. Le <b>creux de courant</b> marquant la fin de course du plongeur sert d'accusé de largage ;
la balise ne s'allume qu'<b>après</b> cette confirmation.</li>
<li><b>Verrouillage logiciel.</b> Le firmware s'abonne à la télémétrie PSDK (altitude, vitesse) et
n'autorise le largage que dans un domaine de vol défini, avec une fenêtre de validité de 10 s après
l'ordre ARMER.</li>
</ul>

<h2>3. Choix aérodynamiques</h2>
<p>Fixé sous le fuselage, le système travaille dans le vent relatif et ne doit pas dégrader les
performances de vol. Le carénage est <b>profilé</b> : maître-couple réduit au strict nécessaire pour
loger la bouée et la carte, nez arrondi et arrière effilé afin de retarder le décollement et de
limiter la traînée de culot. La carte a été dessinée pour <b>s'inscrire dans ce volume</b>
(96 &times; 66 mm, §5), et non l'inverse. Conditions de calcul retenues pour la CFD, qui servent
ensuite de chargement à la FEA : %(cfd)s</p>

<h2>4. Architecture électronique et dimensionnement</h2>
<p><b>Calcul et liaison drone.</b> Le <b>STM32U585CIU6</b> (Cortex-M33 160 MHz, 2 Mo de flash,
786 Ko de RAM, 19 &micro;A/MHz, TrustZone) s'impose parce que DJI fournit la bibliothèque PSDK
précompilée <i>armcc_cortex-m33</i> : elle tourne telle quelle, sans portage, et expose les boutons
ARMER / LARGUER / BALISE dans DJI Pilot 2.</p>
<p><b>Radio.</b> Le <b>Semtech SX1262</b> (+22 dBm, sensibilité &minus;137 dBm en SF12/BW125, 4,6 mA
en réception) opère à <b>869,525 MHz</b>, sous-bande g3. Le 2,4 GHz est écarté car c'est la bande de
la liaison de commande O4 du drone ; la 4G est écartée car elle dépend d'un réseau terrestre, le
premier à tomber lors d'une inondation. Le bilan de liaison donne <b>40 dB de marge à 15 km en
SF9</b>. Deux chemins de commande indépendants coexistent : LoRa depuis le sol et PSDK depuis le
drone.</p>
<p><b>Séparation logique / puissance.</b> Les rails sont produits <b>directement depuis VIN, jamais
en cascade</b>, pour qu'un appel de courant des actionneurs ne puisse faire chuter ni le calculateur
ni la radio :</p>
<table>
<tr><th>Rail</th><th>Circuit</th><th>Dimensionnement et rôle</th></tr>
<tr><td>+3V3 logique</td><td>LMR51430 (36 V, 3 A)</td>
    <td>0,600 &times; (1 + 100k/22,1k) = <b>3,315 V</b> ; L = 15 &micro;H ; ondulation simulée
    <b>3,3 mV</b></td></tr>
<tr><td>+3V3_RF</td><td>ferrite + 10 &micro;F / 100 nF</td>
    <td>Isole le SX1262 du bruit de commutation</td></tr>
<tr><td>+12V_GD</td><td>LDO TPS7A4101 (50 V)</td>
    <td>1,173 &times; (1 + 91k/10k) = <b>11,85 V</b> : attaque les grilles à leur RDS(on) nominal</td></tr>
<tr><td>Entrée</td><td>LM74700 + BSC028N06LS3</td>
    <td>Diode idéale : ~20 mV de chute, blocage inverse &lt; 1 &micro;s, réservoir 470 &micro;F</td></tr>
</table>
<p><b>Tenue aux perturbations.</b> La simulation d'un <b>court-circuit de 30 ms sur l'E-Port</b>
montre que le 3,3 V est maintenu grâce au blocage inverse du LM74700, alors qu'il s'effondre en
85 &micro;s avec une protection passive. Les voies de bobine sont démagnétisées par une Schottky
SS34 associée à une TVS SMAJ20A : la tension de drain plafonne à <b>48 V</b> (MOSFET 60 V) et le
courant décroît <b>4,4 fois plus vite</b> qu'avec une simple roue libre — d'où une libération de
l'aimant <b>3,2 ms</b> après l'ordre FIRE.</p>
<p><b>Bilan de puissance et séquencement.</b> Toutes charges actives, la carte appellerait
<b>4,25 A</b> pour une limite de 5 A : marge trop faible. Le firmware impose donc un séquencement —
d'abord le largage (maintien + éjection &asymp; 2 A), puis la signalisation (rampe LED + sirène
&asymp; 2,4 A) — qui maintient le courant réel <b>sous 2,5 A</b>.</p>

<h2>5. Intégration mécatronique, DFM et impression 3D</h2>
<p><b>Carte.</b> 96,1 &times; 66,1 mm, <b>4 couches</b> (signaux / plan de masse continu / plans
d'alimentation / masse), 1,6 mm, finition ENIG, vernis noir mat : 163 composants, 608 pastilles,
1414 pistes, 424 vias, <b>2,66 m</b> de cuivre. Le plan de masse de la couche 2 n'est jamais
découpé et la chaîne RF 868 MHz est routée en ligne 50 &#8486; (0,36 mm), sans via dans le couloir
d'antenne.</p>
<p><b>Interfaces imposées au châssis.</b> Quatre trous M3 aux angles, reliés à la masse pour le
blindage et la dissipation ; connecteurs de puissance XT30 regroupés sur les bords bas et droit,
face aux sorties actionneurs ; SMA en bord de carte ; connecteurs PSDK et micro-rupteurs sur le bord
haut, côté drone. %(iface)s</p>
<p><b>Gestion thermique.</b> Les sources de chaleur sont les étages de puissance (MOSFET
BSC028N06LS3, 2,8 m&#8486;) et le LDO 12 V (~60 mW). Les pertes de commutation simulées de la voie
LED restent à <b>10 mW</b>, pour une jonction proche de l'ambiante : le flux est faible et
localisé. %(therm)s</p>
<p><b>Impression 3D et jeux fonctionnels.</b> %(print)s</p>

<h2>6. Simulations et vérification</h2>
<p><b>Électronique — réalisée (ngspice).</b> Sept analyses documentées avec leurs courbes :
convertisseur 3,3 V en commutation réelle ; intégrité d'alimentation et court-circuit E-Port ; étage
LED en PWM ; coupure inductive de la sirène ; <b>modèle électromécanique du solénoïde</b> (fin de
course à 23 ms, creux de courant confirmant l'éjection à 23,6 ms) ; <b>aimant de maintien</b>
(libération 3,2 ms, démagnétisation 1,7 ms) ; bilan de liaison LoRa. La conformité du schéma est
vérifiée automatiquement : contrôle ERC sans violation et comparaison de la netlist extraite avec la
netlist de référence (<b>0 écart</b>).</p>
<p><b>Aérodynamique et structure.</b> %(sim)s</p>

<h2>7. Points ouverts assumés</h2>
<p><b>(a)</b> Référence exacte de l'aimant <i>fail-safe</i> et du solénoïde 24 V — fixe les courants
réels et la force de maintien ; la carte est dimensionnée avec marge. <b>(b)</b> Valeurs
d'adaptation RF marquées <i>TUNE</i> — nomenclature régionale Semtech E449V01A, puis réglage à
l'analyseur de réseau. <b>(c)</b> Routage : <b>30 liaisons restantes</b> sur 120 réseaux,
concentrées autour du microcontrôleur et de la radio. <b>(d)</b> Brochage UART du kit E-Port V2 — à
relever dans la documentation DJI PSDK.</p>
""" % dict(
    cfd=T(u"vitesse relative retenue, altitude, maître-couple, Cx et force de traînée issus de la CFD"),
    iface=T(u"entraxe des M3 et hauteur libre sous la carte, à figer avec le modèle du châssis"),
    therm=T(u"solution de ventilation ou de conduction retenue dans le carénage"),
    print=T(u"orientation d'impression des pièces maîtresses, matériau, épaisseurs et jeux fonctionnels retenus"),
    sim=T(u"lignes de courant, cartographie de pression et force de traînée ; contraintes de von Mises, "
          u"déplacements, zones critiques et coefficient de sécurité"),
)
